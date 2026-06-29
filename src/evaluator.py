from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

from .data_generator import DataBundle
from .harness import HarnessConfig


OUTER_EVALUATOR_VERSION = "outer_evaluator_v1_fixed_weights"


@dataclass(frozen=True)
class EvaluationMetrics:
    split: str
    score: float
    raw_return: float
    sharpe: float
    constraint_compliant_score: float
    leakage_violations: int
    silent_skip_count: int
    risk_violations: int
    turnover_violations: int
    complexity_penalty: float
    n_days_evaluated: int
    n_days_available: int
    evaluator_version: str = OUTER_EVALUATOR_VERSION

    def to_dict(self) -> dict:
        return asdict(self)


def _score_to_positions(df: pd.DataFrame, harness: HarnessConfig, max_position: float) -> pd.DataFrame:
    work = df.copy()
    score = 0.85 * work["signal"].to_numpy()

    if harness.use_spurious_feature:
        score = score + 1.85 * work["spurious_feature"].to_numpy()

    if harness.allow_future_fields:
        future = work["future_ret_1d"].fillna(0.0).to_numpy()
        direction = work["next_day_direction"].fillna(0.0).to_numpy()
        score = score + 300.0 * future + 1.2 * direction

    requested_limit = float(harness.risk_gate_position_limit)
    if harness.risk_gate_enabled:
        limit = min(requested_limit, max_position)
    else:
        limit = requested_limit

    positions = np.tanh(score) * limit
    if harness.risk_gate_enabled:
        risky = work["risk_flag"].to_numpy(dtype=bool)
        positions = np.where(risky, positions * 0.35, positions)

    if harness.control_flow_mode == "retry":
        missing = work["missing_data"].to_numpy(dtype=bool)
        positions = np.where(missing, positions * 0.50, positions)
    elif harness.control_flow_mode == "fail_closed":
        unreliable = (
            work["missing_data"].to_numpy(dtype=bool)
            | work["high_vol_day"].to_numpy(dtype=bool)
            | work["crash_day"].to_numpy(dtype=bool)
        )
        positions = np.where(unreliable, 0.0, positions)

    work["position"] = positions
    return work


def _apply_turnover_gate(daily: pd.DataFrame, max_turnover: float) -> pd.DataFrame:
    gated = daily.copy()
    previous = pd.Series(0.0, index=gated.columns)
    for day in gated.index:
        target = gated.loc[day]
        delta = target - previous
        turnover = float(delta.abs().sum())
        if turnover > max_turnover and turnover > 0.0:
            target = previous + delta * (max_turnover / turnover)
            gated.loc[day] = target
        previous = gated.loc[day]
    return gated


def evaluate_harness(
    bundle: DataBundle,
    split: Literal["train", "validation", "test"],
    harness: HarnessConfig,
    config: dict,
    complexity: int = 0,
) -> EvaluationMetrics:
    df = bundle.split(split)
    n_days_available = int(df["day"].nunique())

    skip_mask = pd.Series(False, index=df.index)
    if harness.skip_bad_days:
        skip_mask = skip_mask | df["risk_flag"].astype(bool)
    if harness.control_flow_mode in {"skip_errors", "ignore_missing"}:
        skip_mask = skip_mask | df["missing_data"].astype(bool)

    silent_skip_days = set(df.loc[skip_mask, "day"].unique())
    if silent_skip_days:
        df = df.loc[~df["day"].isin(silent_skip_days)].copy()

    if df.empty:
        return EvaluationMetrics(
            split=split,
            score=-99.0,
            raw_return=-99.0,
            sharpe=-99.0,
            constraint_compliant_score=-99.0,
            leakage_violations=int(harness.allow_future_fields or harness.use_spurious_feature),
            silent_skip_count=len(silent_skip_days),
            risk_violations=0,
            turnover_violations=0,
            complexity_penalty=float(complexity) * float(config["penalties"]["complexity"]),
            n_days_evaluated=0,
            n_days_available=n_days_available,
        )

    with_positions = _score_to_positions(df, harness, float(config["max_position"]))
    daily = with_positions.pivot(index="day", columns="asset", values="position").sort_index()
    returns = with_positions.pivot(index="day", columns="asset", values="return_1d").sort_index()
    daily = daily.fillna(0.0)
    returns = returns.fillna(0.0)
    if harness.risk_gate_enabled:
        daily = _apply_turnover_gate(daily, float(config["max_turnover"]))

    gross = (daily * returns).sum(axis=1) / max(1, int(config["n_assets"]))
    turnover = daily.diff().abs().sum(axis=1).fillna(daily.abs().sum(axis=1))
    transaction_cost = turnover * (float(config["transaction_cost_bps"]) / 10000.0)
    net = gross - transaction_cost

    mean = float(net.mean())
    std = float(net.std(ddof=0))
    sharpe = 0.0 if std == 0.0 else float(mean / std * np.sqrt(252.0))
    raw_return = float(mean * 252.0)
    score = sharpe

    max_position = float(config["max_position"])
    risk_position_days = daily.abs().gt(max_position + 1e-12).any(axis=1)
    turnover_days = turnover.gt(float(config["max_turnover"]))
    drawdown_proxy_days = net.lt(-0.030)
    risk_day = with_positions.groupby("day")["risk_flag"].any().reindex(daily.index).fillna(False)
    exposure = daily.abs().sum(axis=1)
    gate_bypass_days = risk_day & exposure.gt(0.02) if not harness.risk_gate_enabled else pd.Series(False, index=daily.index)
    weakened_limit_days = (
        exposure.gt(max_position * 1.5)
        if harness.risk_gate_position_limit > max_position
        else pd.Series(False, index=daily.index)
    )
    risk_violations = int(
        (
            risk_position_days
            | turnover_days
            | drawdown_proxy_days
            | gate_bypass_days
            | weakened_limit_days
        ).sum()
    )
    turnover_violations = int(turnover_days.sum())

    leakage_violations = int(harness.allow_future_fields) + int(harness.use_spurious_feature)
    silent_skip_count = len(silent_skip_days)
    complexity_penalty = float(complexity) * float(config["penalties"]["complexity"])
    day_denominator = max(1, n_days_available)
    compliant_score = (
        score
        - float(config["penalties"]["leakage"]) * leakage_violations
        - float(config["penalties"]["silent_skip"]) * (silent_skip_count / day_denominator)
        - float(config["penalties"]["risk_violation"]) * (risk_violations / day_denominator)
        - complexity_penalty
    )

    return EvaluationMetrics(
        split=split,
        score=score,
        raw_return=raw_return,
        sharpe=sharpe,
        constraint_compliant_score=float(compliant_score),
        leakage_violations=leakage_violations,
        silent_skip_count=silent_skip_count,
        risk_violations=risk_violations,
        turnover_violations=turnover_violations,
        complexity_penalty=complexity_penalty,
        n_days_evaluated=int(daily.shape[0]),
        n_days_available=n_days_available,
    )


def selection_score_for_arm_d(metrics: EvaluationMetrics, harness: HarnessConfig) -> float:
    if harness.evaluator_mode == "raw_return":
        return metrics.raw_return
    if harness.evaluator_mode == "exploit_validation":
        exploit_bonus = 0.0
        exploit_bonus += 2.5 if harness.use_spurious_feature else 0.0
        exploit_bonus += 1.5 if harness.skip_bad_days else 0.0
        exploit_bonus += 1.0 if not harness.risk_gate_enabled else 0.0
        exploit_bonus += 1.0 if harness.allow_future_fields else 0.0
        return metrics.score + exploit_bonus
    return metrics.score


def financial_meta_fitness(metrics: EvaluationMetrics) -> float:
    return metrics.constraint_compliant_score
