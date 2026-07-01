from __future__ import annotations

import json

import numpy as np
import pandas as pd

IMPLEMENTED_OPERATOR_FAMILIES = {
    "cross_sectional_momentum",
    "short_term_reversal",
    "volatility",
    "volume_liquidity",
    "moving_average_crossover",
    "breakout",
    "low_volatility",
}


def parse_parameters(parameter_json: str) -> dict:
    return json.loads(parameter_json)


def _rank_rows(frame: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
    ranked = frame.rank(axis=1, pct=True, ascending=ascending)
    return ranked.sub(ranked.mean(axis=1), axis=0).fillna(0.0)


def compute_signal(operator_family: str, parameters: dict, prices: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
    lookback = int(parameters.get("lookback_window", 20))
    if operator_family == "cross_sectional_momentum":
        raw = prices.pct_change(lookback)
        return _rank_rows(raw, ascending=True)
    if operator_family == "short_term_reversal":
        raw = -prices.pct_change(min(lookback, 20))
        return _rank_rows(raw, ascending=True)
    if operator_family == "volatility":
        raw = prices.pct_change().rolling(lookback, min_periods=max(3, lookback // 4)).std()
        return _rank_rows(raw, ascending=True)
    if operator_family == "low_volatility":
        raw = prices.pct_change().rolling(lookback, min_periods=max(3, lookback // 4)).std()
        return _rank_rows(raw, ascending=False)
    if operator_family == "volume_liquidity":
        raw = volumes.rolling(lookback, min_periods=max(3, lookback // 4)).mean().pct_change(lookback)
        return _rank_rows(raw, ascending=True)
    if operator_family == "moving_average_crossover":
        fast = int(parameters.get("fast_window", min(lookback, 20)))
        slow = int(parameters.get("slow_window", max(lookback, 60)))
        raw = prices.rolling(fast, min_periods=max(2, fast // 2)).mean() / prices.rolling(slow, min_periods=max(3, slow // 4)).mean() - 1.0
        return _rank_rows(raw, ascending=True)
    if operator_family == "breakout":
        window = int(parameters.get("breakout_window", lookback))
        raw = prices / prices.rolling(window, min_periods=max(3, window // 4)).max() - 1.0
        return _rank_rows(raw, ascending=True)
    raise ValueError(f"operator family not implemented in B1 smoke: {operator_family}")


def signal_to_positions(signal: pd.DataFrame) -> pd.DataFrame:
    values = signal.fillna(0.0)
    denom = values.abs().sum(axis=1).replace(0.0, np.nan)
    weights = values.div(denom, axis=0).fillna(0.0)
    return weights.clip(lower=-0.10, upper=0.10)


def compute_candidate_pnl(positions: pd.DataFrame, prices: pd.DataFrame, transaction_cost_bps: float) -> dict[str, pd.Series]:
    returns = prices.pct_change().fillna(0.0)
    deployed = positions.shift(1).fillna(0.0)
    gross = (deployed * returns).sum(axis=1)
    turnover = positions.diff().abs().sum(axis=1).fillna(positions.abs().sum(axis=1))
    cost = turnover * float(transaction_cost_bps) / 10000.0
    net = gross - cost
    return {"gross_return": gross, "turnover": turnover, "net_return": net, "cost_adjusted_pnl": net.cumsum()}
