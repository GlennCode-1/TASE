from __future__ import annotations

import numpy as np
import pandas as pd

from .universe_builder import SmokeUniverse


def make_deterministic_mock_price_panel(universe: SmokeUniverse, start: str, end: str, seed: int = 20260701) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="B")
    rows = []
    for asset_idx, ticker in enumerate(universe.tickers):
        base = 50.0 + asset_idx * 3.0
        trend = 0.00015 * (asset_idx % 5 - 2)
        seasonal = 0.01 * np.sin(np.arange(len(dates)) / (7.0 + asset_idx % 4))
        deterministic_noise = 0.002 * np.cos(np.arange(len(dates)) * (asset_idx + 1) / 19.0)
        returns = trend + seasonal / 100.0 + deterministic_noise
        close = base * np.cumprod(1.0 + returns)
        volume = 1_000_000 + asset_idx * 25_000 + (np.arange(len(dates)) % 21) * 1000
        for date, price, vol in zip(dates, close, volume):
            rows.append({"date": date, "ticker": ticker, "close": float(price), "volume": float(vol), "sector": universe.sectors[ticker]})
    return pd.DataFrame(rows)


def price_panel_to_matrices(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = panel.pivot(index="date", columns="ticker", values="close").sort_index()
    volumes = panel.pivot(index="date", columns="ticker", values="volume").reindex_like(prices)
    return prices, volumes
