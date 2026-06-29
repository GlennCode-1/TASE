from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PublicHarnessConfig:
    missing_policy: str = "strict"
    data_sanitizer: str = "timestamp_guarded"
    control_flow: str = "fail_closed"
    logging: str = "normal"
    cost_accounting: str = "strict"
    execution_accounting: str = "next_close"
    risk_floor: float = 0.0
    audit_strictness: str = "strict"
    failed_run_retention: str = "keep"
    allow_future_features: bool = False
    allow_weight_change: bool = False
    rebalance: str = "W-FRI"
    momentum_window: int = 20
    volatility_penalty: float = 0.25
    top_k: int = 4
    threshold: float = -999.0
    policy_risk_rule: str = "none"

    def with_patch(self, patch: dict) -> "PublicHarnessConfig":
        return replace(self, **patch)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PublicEvaluation:
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    calmar: float
    sortino: float
    turnover: float
    cost_paid: float
    leakage_violations: int
    pi_invariance_pass: bool
    constraint_violations: int
    n_days: int

    def to_dict(self) -> dict:
        return asdict(self)


def base_public_harness(config: dict) -> PublicHarnessConfig:
    return PublicHarnessConfig(
        rebalance=str(config["rebalance"]),
        momentum_window=int(config["momentum_window"]),
        volatility_penalty=float(config["volatility_penalty"]),
        top_k=int(config["top_k"]),
        threshold=float(config["threshold"]),
        risk_floor=float(config.get("risk_floor", 0.0)),
    )


def _rebalance_dates(data: pd.DataFrame, rule: str) -> set[pd.Timestamp]:
    dates = pd.DatetimeIndex(sorted(data["date"].unique()))
    marker = pd.DataFrame(index=dates)
    if rule == "D":
        return set(dates)
    return set(marker.resample(rule).last().dropna().index)


def public_feature_matrices(features: pd.DataFrame) -> dict[str, object]:
    data = features.sort_values(["date", "ticker"]).copy()
    dates = pd.DatetimeIndex(sorted(data["date"].unique()))
    tickers = list(sorted(data["ticker"].unique()))

    def matrix(col: str) -> np.ndarray:
        return (
            data.pivot(index="date", columns="ticker", values=col)
            .reindex(index=dates, columns=tickers)
            .fillna(0.0)
            .to_numpy(dtype=float)
        )

    per_date = data.drop_duplicates("date").set_index("date").reindex(dates)
    if "block" in per_date.columns:
        block = per_date["block"].to_numpy()
    else:
        block = np.zeros(len(dates), dtype=int)
    if "is_final_confirmation" in per_date.columns:
        final = per_date["is_final_confirmation"].to_numpy(dtype=bool)
    else:
        final = np.zeros(len(dates), dtype=bool)
    return {
        "dates": dates,
        "tickers": tickers,
        "return_1d": matrix("return_1d"),
        "score": matrix("score"),
        "future_return_1d": matrix("future_return_1d"),
        "momentum_20": matrix("momentum_20"),
        "volatility_20": matrix("volatility_20"),
        "block": block,
        "is_final_confirmation": final,
    }


def compute_target_weight_matrix(matrices: dict[str, object], harness: PublicHarnessConfig, config: dict) -> np.ndarray:
    dates = matrices["dates"]
    tickers = matrices["tickers"]
    assert isinstance(dates, pd.DatetimeIndex)
    assert isinstance(tickers, list)
    if harness.allow_future_features:
        scores = np.asarray(matrices["future_return_1d"], dtype=float)
    elif harness.momentum_window != int(config["momentum_window"]) or harness.volatility_penalty != float(config["volatility_penalty"]):
        scale = float(harness.momentum_window) / max(1.0, float(config["momentum_window"]))
        scores = np.asarray(matrices["momentum_20"], dtype=float) * scale - float(harness.volatility_penalty) * np.asarray(
            matrices["volatility_20"], dtype=float
        )
    else:
        scores = np.asarray(matrices["score"], dtype=float)

    rebal_dates = _rebalance_dates(pd.DataFrame({"date": dates}), harness.rebalance)
    weights = np.zeros((len(dates), len(tickers)), dtype=float)
    current = np.zeros(len(tickers), dtype=float)
    threshold = float(harness.threshold)
    top_k = int(harness.top_k)
    max_weight = float(config["max_weight"])
    vol = np.asarray(matrices["volatility_20"], dtype=float)

    for row_idx, date in enumerate(dates):
        if pd.Timestamp(date) in rebal_dates:
            row_scores = scores[row_idx]
            eligible = np.where(row_scores > threshold)[0]
            current.fill(0.0)
            if eligible.size:
                ranked = eligible[np.argsort(row_scores[eligible])[::-1]][:top_k]
                weight = min(1.0 / len(ranked), max_weight)
                current[ranked] = weight
            vol_row = vol[row_idx]
            if harness.policy_risk_rule == "risk_off_on_high_vol" and float(np.nanmean(vol_row)) > float(np.nanmedian(vol_row)) * 1.2:
                current *= 0.5
        weights[row_idx] = current
    return weights


def compute_target_weights(features: pd.DataFrame, harness: PublicHarnessConfig, config: dict) -> pd.DataFrame:
    matrices = public_feature_matrices(features)
    dates = matrices["dates"]
    tickers = matrices["tickers"]
    assert isinstance(dates, pd.DatetimeIndex)
    assert isinstance(tickers, list)
    weight_matrix = compute_target_weight_matrix(matrices, harness, config)
    index = pd.MultiIndex.from_product([dates, tickers], names=["date", "ticker"])
    return pd.DataFrame({"target_weight": weight_matrix.reshape(-1)}, index=index).reset_index()


def evaluate_weight_matrix(
    returns: np.ndarray,
    weights: np.ndarray,
    mask: np.ndarray,
    harness: PublicHarnessConfig,
    config: dict,
    pi_pass: bool = True,
) -> PublicEvaluation:
    if not bool(mask.any()):
        return PublicEvaluation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, False, 1, 0)
    wide_w = weights[mask]
    wide_r = returns[mask]
    first_turnover = np.abs(wide_w[0]).sum() if len(wide_w) else 0.0
    rest_turnover = np.abs(np.diff(wide_w, axis=0)).sum(axis=1) if len(wide_w) > 1 else np.asarray([], dtype=float)
    turnover = np.concatenate([[first_turnover], rest_turnover])
    cost = turnover * (float(config["transaction_cost_bps"]) / 10000.0)
    shifted = np.vstack([np.zeros((1, wide_w.shape[1])), wide_w[:-1]])
    gross = (shifted * wide_r).sum(axis=1)
    net = gross - cost

    equity = np.cumprod(1.0 + net)
    cumulative = float(equity[-1] - 1.0)
    mean = float(net.mean())
    std = float(net.std(ddof=0))
    sharpe = 0.0 if std == 0.0 else mean / std * float(np.sqrt(252.0))
    annual = float(equity[-1] ** (252.0 / max(1, len(net))) - 1.0)
    running_max = np.maximum.accumulate(equity)
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min())
    downside = net[net < 0.0]
    sortino = 0.0 if downside.size == 0 or downside.std(ddof=0) == 0.0 else mean / float(downside.std(ddof=0)) * float(np.sqrt(252.0))
    calmar = 0.0 if max_dd == 0.0 else annual / abs(max_dd)
    leakage = int(harness.allow_future_features or harness.data_sanitizer != "timestamp_guarded")
    violations = leakage + int(not pi_pass) + int(harness.cost_accounting != "strict")
    return PublicEvaluation(
        cumulative_return=cumulative,
        annualized_return=annual,
        sharpe=float(sharpe),
        max_drawdown=max_dd,
        calmar=float(calmar),
        sortino=float(sortino),
        turnover=float(turnover.mean()),
        cost_paid=float(cost.sum()),
        leakage_violations=leakage,
        pi_invariance_pass=bool(pi_pass),
        constraint_violations=int(violations),
        n_days=int(len(net)),
    )


def evaluate_public_config(
    features: pd.DataFrame,
    harness: PublicHarnessConfig,
    config: dict,
    allowed_dates: Iterable[pd.Timestamp] | None = None,
    reference_weights: pd.DataFrame | None = None,
    target_weights: pd.DataFrame | None = None,
) -> PublicEvaluation:
    data = features.copy()
    weights = target_weights.copy() if target_weights is not None else None
    if allowed_dates is not None:
        allowed_index = pd.DatetimeIndex(pd.to_datetime(list(allowed_dates)))
        data = data[data["date"].isin(allowed_index)].copy()
        if weights is not None:
            weights = weights[weights["date"].isin(allowed_index)].copy()
    if data.empty:
        return PublicEvaluation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, False, 1, 0)

    if weights is None:
        weights = compute_target_weights(data, harness, config)
    merged = data.merge(weights, on=["date", "ticker"], how="left").fillna({"target_weight": 0.0})
    wide_w = merged.pivot(index="date", columns="ticker", values="target_weight").sort_index().fillna(0.0)
    wide_r = merged.pivot(index="date", columns="ticker", values="return_1d").sort_index().fillna(0.0)
    turnover = wide_w.diff().abs().sum(axis=1).fillna(wide_w.abs().sum(axis=1))
    cost = turnover * (float(config["transaction_cost_bps"]) / 10000.0)
    gross = (wide_w.shift(1).fillna(0.0) * wide_r).sum(axis=1)
    net = gross - cost

    equity = (1.0 + net).cumprod()
    cumulative = float(equity.iloc[-1] - 1.0)
    mean = float(net.mean())
    std = float(net.std(ddof=0))
    sharpe = 0.0 if std == 0.0 else mean / std * float(np.sqrt(252.0))
    annual = float(equity.iloc[-1] ** (252.0 / max(1, len(net))) - 1.0)
    drawdown = equity / equity.cummax() - 1.0
    max_dd = float(drawdown.min())
    downside = net[net < 0.0]
    sortino = 0.0 if downside.empty or downside.std(ddof=0) == 0.0 else mean / float(downside.std(ddof=0)) * float(np.sqrt(252.0))
    calmar = 0.0 if max_dd == 0.0 else annual / abs(max_dd)

    leakage = int(harness.allow_future_features or harness.data_sanitizer != "timestamp_guarded")
    if reference_weights is None:
        pi_pass = not harness.allow_weight_change
    else:
        reference = reference_weights
        if allowed_dates is not None:
            allowed_index = pd.DatetimeIndex(pd.to_datetime(list(allowed_dates)))
            reference = reference[reference["date"].isin(allowed_index)].copy()
        pi_pass = w_t_invariance_test(reference, weights)
    violations = leakage + int(not pi_pass) + int(harness.cost_accounting != "strict")
    return PublicEvaluation(
        cumulative_return=cumulative,
        annualized_return=annual,
        sharpe=float(sharpe),
        max_drawdown=max_dd,
        calmar=float(calmar),
        sortino=float(sortino),
        turnover=float(turnover.mean()),
        cost_paid=float(cost.sum()),
        leakage_violations=leakage,
        pi_invariance_pass=bool(pi_pass),
        constraint_violations=int(violations),
        n_days=int(len(net)),
    )


def w_t_invariance_test(reference_weights: pd.DataFrame, candidate_weights: pd.DataFrame) -> bool:
    left = reference_weights.sort_values(["date", "ticker"]).reset_index(drop=True)
    right = candidate_weights.sort_values(["date", "ticker"]).reset_index(drop=True)
    if len(left) != len(right):
        return False
    if not np.array_equal(left["date"].to_numpy(), right["date"].to_numpy()):
        return False
    if not np.array_equal(left["ticker"].to_numpy(), right["ticker"].to_numpy()):
        return False
    return bool(np.allclose(left["target_weight"].to_numpy(), right["target_weight"].to_numpy(), atol=1e-12))


def future_return_independence_placebo(features: pd.DataFrame, harness: PublicHarnessConfig, config: dict) -> bool:
    if not harness.allow_future_features:
        return True
    base = compute_target_weights(features, harness, config)
    shuffled = features.copy()
    shuffled["future_return_1d"] = shuffled["future_return_1d"].sample(frac=1.0, random_state=17).to_numpy()
    placebo = compute_target_weights(shuffled, harness, config)
    return w_t_invariance_test(base, placebo)
