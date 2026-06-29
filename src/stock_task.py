from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd

from .features import build_lagged_features, feature_lag_audit


@dataclass(frozen=True)
class StockHarnessConfig:
    missing_policy: str = "strict_fail_closed"
    stale_policy: str = "none"
    bad_tick_policy: str = "none"
    corporate_action_policy: str = "none"
    failed_day_policy: str = "fail_closed"
    cost_accounting: str = "strict_cost_accounting"
    audit_level: str = "strict_feature_lag_audit"
    trace_level: str = "normal"
    cash_buffer: float = 0.0
    allow_future_features: bool = False
    allow_strategy_change: bool = False
    use_future_exclusion: bool = False
    rebalance: str = "W-FRI"
    momentum_window: int = 20
    volatility_window: int = 20
    volatility_penalty: float = 0.5
    top_k: int = 30
    threshold: float = -999.0
    policy_risk_rule: str = "none"

    def with_patch(self, patch: dict) -> "StockHarnessConfig":
        return replace(self, **patch)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class StockEvaluation:
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    turnover: float
    hit_rate: float
    active_asset_count: float
    cash_ratio: float
    cost_paid: float
    leakage_violations: int
    strategy_boundary_violations: int
    availability_audit_pass: bool
    constraint_violations: int
    n_days: int

    def to_dict(self) -> dict:
        return asdict(self)


def base_stock_harness(config: dict) -> StockHarnessConfig:
    return StockHarnessConfig(
        rebalance=str(config["rebalance"]),
        momentum_window=int(config["momentum_window"]),
        volatility_window=int(config["volatility_window"]),
        volatility_penalty=float(config["volatility_penalty"]),
        top_k=int(config["top_k"]),
        threshold=float(config.get("threshold", -999.0)),
    )


def build_stock_features(prices: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = build_lagged_features(
        prices,
        int(config["momentum_window"]),
        int(config["volatility_window"]),
        float(config["volatility_penalty"]),
    )
    data = prices.sort_values(["ticker", "date"]).copy()
    data["raw_return_1d"] = data.groupby("ticker")["adj_close"].pct_change()
    data["is_missing_adj_close"] = data["adj_close"].isna()
    data["is_stale_price"] = data.groupby("ticker")["adj_close"].transform(lambda s: s.diff().abs().eq(0).rolling(5, min_periods=1).sum() >= 5)
    data["is_bad_tick"] = data["raw_return_1d"].abs() > float(config.get("bad_tick_abs_return", 0.50))
    ratio = data["close"] / data["adj_close"].replace(0, np.nan)
    data["is_corporate_action_anomaly"] = ratio.groupby(data["ticker"]).pct_change().abs() > float(
        config.get("corporate_action_ratio_jump", 0.50)
    )
    flags = data[["date", "ticker", "is_stale_price", "is_bad_tick", "is_corporate_action_anomaly"]]
    out = features.merge(flags, on=["date", "ticker"], how="left").fillna(
        {"is_stale_price": False, "is_bad_tick": False, "is_corporate_action_anomaly": False}
    )
    out.attrs["used_features"] = ("momentum_20", "volatility_20", "score")
    if not feature_lag_audit(out):
        raise RuntimeError("stock feature lag audit failed")
    return out


def stock_feature_matrices(features: pd.DataFrame) -> dict[str, object]:
    data = features.sort_values(["date", "ticker"]).copy()
    dates = pd.DatetimeIndex(sorted(data["date"].unique()))
    tickers = list(sorted(data["ticker"].unique()))

    def matrix(col: str, fill=0.0):
        return (
            data.pivot(index="date", columns="ticker", values=col)
            .reindex(index=dates, columns=tickers)
            .fillna(fill)
            .to_numpy(dtype=float)
        )

    per_date = data.drop_duplicates("date").set_index("date").reindex(dates)
    block = per_date["block"].to_numpy() if "block" in per_date.columns else np.zeros(len(dates), dtype=int)
    final = per_date["is_final_confirmation"].to_numpy(dtype=bool) if "is_final_confirmation" in per_date.columns else np.zeros(len(dates), dtype=bool)
    return {
        "dates": dates,
        "tickers": tickers,
        "return_1d": matrix("return_1d"),
        "score": matrix("score"),
        "future_return_1d": matrix("future_return_1d"),
        "momentum_20": matrix("momentum_20"),
        "volatility_20": matrix("volatility_20"),
        "is_stale_price": matrix("is_stale_price", False).astype(bool),
        "is_bad_tick": matrix("is_bad_tick", False).astype(bool),
        "is_corporate_action_anomaly": matrix("is_corporate_action_anomaly", False).astype(bool),
        "block": block,
        "is_final_confirmation": final,
    }


def _rebalance_dates(dates: pd.DatetimeIndex, rule: str) -> set[pd.Timestamp]:
    if rule == "D":
        return set(pd.Timestamp(d) for d in dates)
    marker = pd.DataFrame(index=dates)
    return set(marker.resample(rule).last().dropna().index)


def raw_score_matrix(matrices: dict[str, object], harness: StockHarnessConfig, config: dict) -> np.ndarray:
    if harness.allow_future_features:
        return np.asarray(matrices["future_return_1d"], dtype=float)
    if (
        harness.momentum_window != int(config["momentum_window"])
        or harness.volatility_window != int(config["volatility_window"])
        or harness.volatility_penalty != float(config["volatility_penalty"])
    ):
        scale = float(harness.momentum_window) / max(1.0, float(config["momentum_window"]))
        return np.asarray(matrices["momentum_20"], dtype=float) * scale - float(harness.volatility_penalty) * np.asarray(
            matrices["volatility_20"], dtype=float
        )
    return np.asarray(matrices["score"], dtype=float)


def invalid_asset_mask(matrices: dict[str, object], harness: StockHarnessConfig, config: dict) -> tuple[np.ndarray, list[dict]]:
    dates = matrices["dates"]
    tickers = matrices["tickers"]
    assert isinstance(dates, pd.DatetimeIndex)
    assert isinstance(tickers, list)
    stale = np.asarray(matrices["is_stale_price"], dtype=bool)
    bad = np.asarray(matrices["is_bad_tick"], dtype=bool)
    corporate = np.asarray(matrices["is_corporate_action_anomaly"], dtype=bool)
    future = np.asarray(matrices["future_return_1d"], dtype=float) < 0.0
    invalid = np.zeros_like(stale, dtype=bool)
    reasons: list[dict] = []

    def add(mask: np.ndarray, reason: str) -> None:
        nonlocal invalid, reasons
        selected = np.asarray(mask, dtype=bool)
        invalid |= selected
        rows, cols = np.where(selected)
        for r, c in zip(rows, cols):
            reasons.append({"date": dates[int(r)], "ticker": tickers[int(c)], "reason": reason})

    if harness.stale_policy == "stale_price_to_cash":
        add(stale, "stale")
    if harness.bad_tick_policy == "bad_tick_filter_with_past_only_threshold":
        add(bad, "bad_tick")
    if harness.corporate_action_policy == "corporate_action_sanity_check":
        add(corporate, "corporate_action_anomaly")
    if harness.missing_policy in {"asset_cash_if_missing", "asset_exclude_if_missing_ratio_high", "past_only_safe_impute"}:
        add(stale | bad | corporate, "availability_or_sanity")
    if harness.use_future_exclusion:
        add(future, "future_return_filter")
    return invalid, reasons


def compute_stock_weight_matrix(matrices: dict[str, object], harness: StockHarnessConfig, config: dict) -> tuple[np.ndarray, pd.DataFrame]:
    dates = matrices["dates"]
    tickers = matrices["tickers"]
    assert isinstance(dates, pd.DatetimeIndex)
    assert isinstance(tickers, list)
    scores = raw_score_matrix(matrices, harness, config)
    invalid, reason_rows = invalid_asset_mask(matrices, harness, config)
    rebal_dates = _rebalance_dates(dates, harness.rebalance)
    weights = np.zeros_like(scores, dtype=float)
    current = np.zeros(scores.shape[1], dtype=float)
    max_weight = float(config.get("max_weight", 1.0 / max(1, int(config["top_k"]))))
    for row_idx, date in enumerate(dates):
        current[invalid[row_idx]] = 0.0
        if pd.Timestamp(date) in rebal_dates:
            current.fill(0.0)
            row_scores = scores[row_idx].copy()
            row_scores[invalid[row_idx]] = -np.inf
            eligible = np.where(row_scores > float(harness.threshold))[0]
            if eligible.size:
                chosen = eligible[np.argsort(row_scores[eligible])[::-1]][: int(harness.top_k)]
                if chosen.size:
                    weight = min(1.0 / chosen.size, max_weight)
                    current[chosen] = weight
            if harness.cash_buffer > 0:
                current *= max(0.0, 1.0 - float(harness.cash_buffer))
        weights[row_idx] = current
    return weights, pd.DataFrame(reason_rows)


def clean_panel_score_invariance(matrices: dict[str, object], harness: StockHarnessConfig, config: dict) -> bool:
    base = base_stock_harness(config)
    strategy_fields = ("rebalance", "momentum_window", "volatility_window", "volatility_penalty", "top_k", "threshold", "policy_risk_rule")
    for field in strategy_fields:
        if getattr(harness, field) != getattr(base, field):
            return False
    base_scores = raw_score_matrix(matrices, base, config)
    candidate_scores = raw_score_matrix(matrices, harness, config)
    clean = ~(
        np.asarray(matrices["is_stale_price"], dtype=bool)
        | np.asarray(matrices["is_bad_tick"], dtype=bool)
        | np.asarray(matrices["is_corporate_action_anomaly"], dtype=bool)
    )
    if not np.allclose(base_scores[clean], candidate_scores[clean], atol=1e-12, equal_nan=True):
        return False
    for row_idx in range(base_scores.shape[0]):
        cols = np.where(clean[row_idx])[0]
        if cols.size <= 1:
            continue
        if not np.array_equal(np.argsort(base_scores[row_idx, cols]), np.argsort(candidate_scores[row_idx, cols])):
            return False
    return True


def future_return_exclusion_placebo(matrices: dict[str, object], harness: StockHarnessConfig, config: dict) -> bool:
    base_invalid, _ = invalid_asset_mask(matrices, harness, config)
    altered = dict(matrices)
    future = np.asarray(matrices["future_return_1d"], dtype=float).copy().reshape(-1)
    rng = np.random.default_rng(17)
    rng.shuffle(future)
    altered["future_return_1d"] = future.reshape(np.asarray(matrices["future_return_1d"]).shape)
    placebo_invalid, _ = invalid_asset_mask(altered, harness, config)
    return bool(np.array_equal(base_invalid, placebo_invalid))


def evaluate_stock_weight_matrix(
    returns: np.ndarray,
    weights: np.ndarray,
    mask: np.ndarray,
    harness: StockHarnessConfig,
    config: dict,
    strategy_pass: bool,
    availability_pass: bool,
) -> StockEvaluation:
    if not bool(mask.any()):
        return StockEvaluation(0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, False, 3, 0)
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
    sharpe = 0.0 if std == 0 else mean / std * float(np.sqrt(252.0))
    annual = float(equity[-1] ** (252.0 / max(1, len(net))) - 1.0)
    drawdown = equity / np.maximum.accumulate(equity) - 1.0
    leakage = int(harness.allow_future_features or harness.use_future_exclusion)
    strategy_violation = int(not strategy_pass or harness.allow_strategy_change)
    cost_violation = int(harness.cost_accounting not in {"strict_cost_accounting", "conservative_cost_accounting"})
    availability_violation = int(not availability_pass)
    violations = leakage + strategy_violation + cost_violation + availability_violation
    active_counts = (wide_w > 0).sum(axis=1)
    return StockEvaluation(
        cumulative_return=cumulative,
        annualized_return=annual,
        sharpe=float(sharpe),
        max_drawdown=float(drawdown.min()),
        turnover=float(turnover.mean()),
        hit_rate=float((net > 0).mean()),
        active_asset_count=float(active_counts.mean()),
        cash_ratio=float(1.0 - wide_w.sum(axis=1).mean()),
        cost_paid=float(cost.sum()),
        leakage_violations=leakage,
        strategy_boundary_violations=strategy_violation,
        availability_audit_pass=bool(availability_pass),
        constraint_violations=int(violations),
        n_days=int(len(net)),
    )
