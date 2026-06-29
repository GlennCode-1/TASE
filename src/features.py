from __future__ import annotations

import pandas as pd


SAFE_FEATURES = ("momentum_20", "volatility_20", "score")


def build_lagged_features(prices: pd.DataFrame, momentum_window: int, volatility_window: int, volatility_penalty: float) -> pd.DataFrame:
    data = prices.sort_values(["ticker", "date"]).copy()
    grouped = data.groupby("ticker", group_keys=False)
    data["return_1d"] = grouped["adj_close"].pct_change()
    data["future_return_1d"] = grouped["return_1d"].shift(-1)
    data["momentum_20"] = grouped["adj_close"].pct_change(momentum_window).shift(1)
    data["volatility_20"] = grouped["return_1d"].rolling(volatility_window).std().reset_index(level=0, drop=True).shift(1)
    data["score"] = data["momentum_20"] - float(volatility_penalty) * data["volatility_20"]
    return data.dropna(subset=["return_1d", "momentum_20", "volatility_20", "score"]).reset_index(drop=True)


def feature_lag_audit(features: pd.DataFrame) -> bool:
    required = set(SAFE_FEATURES)
    if not required.issubset(features.columns):
        return False
    unsafe_feature_names = {"future_return_1d", "next_return", "lead_return"}
    used = set(features.attrs.get("used_features", SAFE_FEATURES))
    return not bool(unsafe_feature_names.intersection(used))


def assign_time_blocks(features: pd.DataFrame, n_blocks: int, final_confirmation_months: int) -> pd.DataFrame:
    data = features.sort_values(["date", "ticker"]).copy()
    final_start = data["date"].max() - pd.DateOffset(months=int(final_confirmation_months))
    data["is_final_confirmation"] = data["date"] > final_start
    trainable_dates = sorted(data.loc[~data["is_final_confirmation"], "date"].unique())
    if len(trainable_dates) < int(n_blocks):
        raise ValueError("not enough dates for requested public toy blocks")
    block_lookup: dict[pd.Timestamp, int] = {}
    for idx, date in enumerate(trainable_dates):
        block_lookup[pd.Timestamp(date)] = min(int(n_blocks) - 1, idx * int(n_blocks) // len(trainable_dates))
    data["block"] = data["date"].map(lambda value: block_lookup.get(pd.Timestamp(value), int(n_blocks)))
    return data
