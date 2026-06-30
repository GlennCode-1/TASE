from __future__ import annotations

import numpy as np
import pandas as pd

from .features import build_lagged_features, feature_lag_audit


DEFAULT_ASSET_CLASS = {
    "SPY": "us_equity", "QQQ": "us_equity", "IWM": "us_equity", "DIA": "us_equity", "VTI": "us_equity",
    "EFA": "intl_equity", "EEM": "intl_equity", "EWJ": "intl_equity", "EWU": "intl_equity", "EWG": "intl_equity", "FXI": "intl_equity",
    "TLT": "rates", "IEF": "rates", "SHY": "rates", "AGG": "rates", "TIP": "rates", "LQD": "credit", "HYG": "credit",
    "GLD": "commodity", "SLV": "commodity", "DBC": "commodity", "USO": "commodity",
    "VNQ": "real_estate", "IYR": "real_estate", "XLRE": "real_estate",
    "XLF": "sector", "XLK": "sector", "XLE": "sector", "XLI": "sector", "XLU": "sector", "XLP": "sector", "XLY": "sector", "XLV": "sector", "XLB": "sector",
    "MTUM": "factor", "QUAL": "factor", "USMV": "factor", "VLUE": "factor", "VUG": "factor", "VTV": "factor", "SIZE": "factor", "SPLV": "factor", "IVE": "factor", "IVW": "factor",
}


def build_portfolio_features(prices: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = build_lagged_features(
        prices,
        int(config["momentum_window"]),
        int(config["volatility_window"]),
        float(config["volatility_penalty"]),
    )
    features.attrs["used_features"] = ("momentum_20", "volatility_20", "score")
    if not feature_lag_audit(features):
        raise RuntimeError("portfolio feature lag audit failed")
    features["asset_class"] = features["ticker"].map(lambda x: DEFAULT_ASSET_CLASS.get(str(x), "other"))
    dates = pd.DatetimeIndex(sorted(features["date"].unique()))
    date_rank = {date: idx for idx, date in enumerate(dates)}
    n = max(1, len(dates) - 1)
    pct = features["date"].map(lambda x: date_rank[pd.Timestamp(x)] / n)
    stress = config.get("stress_scenarios", {}) or {}
    features["stress_covariance_near_singular"] = bool(stress.get("covariance_near_singular", True)) & pct.between(0.30, 0.38)
    features["stress_missing_returns_block"] = bool(stress.get("missing_returns_block", True)) & pct.between(0.42, 0.46)
    features["stress_stale_price"] = bool(stress.get("stale_price_flags", True)) & pct.between(0.50, 0.54)
    features["stress_infeasible_constraints"] = bool(stress.get("optimizer_infeasible_constraints", True)) & pct.between(0.58, 0.62)
    features["stress_high_turnover"] = bool(stress.get("high_turnover_pressure", True)) & pct.between(0.66, 0.70)
    features["stress_cost_spike"] = bool(stress.get("transaction_cost_spike", True)) & pct.between(0.72, 0.76)
    vol_rank = features.groupby("date")["volatility_20"].transform("mean").rank(pct=True)
    features["stress_extreme_volatility"] = bool(stress.get("extreme_volatility_regime", True)) & (vol_rank > 0.80)
    features["stress_concentration_shock"] = bool(stress.get("concentration_shock", True)) & pct.between(0.80, 0.86)
    return features.reset_index(drop=True)


def portfolio_feature_matrices(features: pd.DataFrame) -> dict[str, object]:
    data = features.sort_values(["date", "ticker"]).copy()
    dates = pd.DatetimeIndex(sorted(data["date"].unique()))
    tickers = list(sorted(data["ticker"].unique()))

    def matrix(col: str, fill: float = 0.0) -> np.ndarray:
        return (
            data.pivot(index="date", columns="ticker", values=col)
            .reindex(index=dates, columns=tickers)
            .fillna(fill)
            .to_numpy(dtype=float)
        )

    per_date = data.drop_duplicates("date").set_index("date").reindex(dates)
    asset_classes = [str(data[data["ticker"] == ticker]["asset_class"].iloc[0]) for ticker in tickers]
    return {
        "dates": dates,
        "tickers": tickers,
        "asset_classes": asset_classes,
        "return_1d": matrix("return_1d"),
        "score": matrix("score"),
        "future_return_1d": matrix("future_return_1d"),
        "volatility_20": matrix("volatility_20"),
        "stress_covariance_near_singular": per_date["stress_covariance_near_singular"].fillna(False).to_numpy(dtype=bool),
        "stress_missing_returns_block": per_date["stress_missing_returns_block"].fillna(False).to_numpy(dtype=bool),
        "stress_stale_price": per_date["stress_stale_price"].fillna(False).to_numpy(dtype=bool),
        "stress_infeasible_constraints": per_date["stress_infeasible_constraints"].fillna(False).to_numpy(dtype=bool),
        "stress_high_turnover": per_date["stress_high_turnover"].fillna(False).to_numpy(dtype=bool),
        "stress_cost_spike": per_date["stress_cost_spike"].fillna(False).to_numpy(dtype=bool),
        "stress_extreme_volatility": per_date["stress_extreme_volatility"].fillna(False).to_numpy(dtype=bool),
        "stress_concentration_shock": per_date["stress_concentration_shock"].fillna(False).to_numpy(dtype=bool),
        "block": per_date["block"].fillna(0).to_numpy(dtype=int) if "block" in per_date.columns else np.zeros(len(dates), dtype=int),
        "is_final_confirmation": per_date["is_final_confirmation"].fillna(False).to_numpy(dtype=bool) if "is_final_confirmation" in per_date.columns else np.zeros(len(dates), dtype=bool),
    }
