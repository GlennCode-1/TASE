from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import numpy as np
import pandas as pd


OHLCV_COLUMNS = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]


@dataclass(frozen=True)
class PublicDataBundle:
    prices: pd.DataFrame
    universe: tuple[str, ...]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    missing_log: pd.DataFrame


def _path(root: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root / path


def _normalize_ohlcv(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    cols = {str(col).lower().replace(" ", "_"): col for col in frame.columns}
    date_col = cols.get("date") or frame.index.name or frame.index
    if "date" in cols:
        dates = pd.to_datetime(frame[cols["date"]])
    else:
        dates = pd.to_datetime(frame.index)

    out = pd.DataFrame(
        {
            "date": dates,
            "ticker": ticker,
            "open": pd.to_numeric(frame[cols.get("open", "Open")], errors="coerce"),
            "high": pd.to_numeric(frame[cols.get("high", "High")], errors="coerce"),
            "low": pd.to_numeric(frame[cols.get("low", "Low")], errors="coerce"),
            "close": pd.to_numeric(frame[cols.get("close", "Close")], errors="coerce"),
            "adj_close": pd.to_numeric(
                frame[cols.get("adj_close", cols.get("adj_close", cols.get("close", "Close")))], errors="coerce"
            ),
            "volume": pd.to_numeric(frame[cols.get("volume", "Volume")], errors="coerce"),
        }
    )
    return out[OHLCV_COLUMNS]


def _download_yfinance(universe: list[str], start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("yfinance is not installed") from exc

    frames: list[pd.DataFrame] = []
    for ticker in universe:
        data = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
        if data.empty:
            continue
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        frames.append(_normalize_ohlcv(data, ticker))
    if not frames:
        raise RuntimeError("yfinance returned no usable ETF data")
    return pd.concat(frames, ignore_index=True)


def _download_stooq(universe: list[str], start: str, end: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    start_compact = pd.Timestamp(start).strftime("%Y%m%d")
    end_compact = pd.Timestamp(end).strftime("%Y%m%d")
    for ticker in universe:
        symbol = ticker.lower() + ".us"
        url = f"https://stooq.com/q/d/l/?s={symbol}&d1={start_compact}&d2={end_compact}&i=d"
        try:
            with urlopen(url, timeout=20) as response:
                frame = pd.read_csv(response)
        except (OSError, URLError):
            continue
        if frame.empty or "Date" not in frame.columns:
            continue
        normalized = _normalize_ohlcv(frame.rename(columns={"Date": "date"}), ticker)
        normalized["adj_close"] = normalized["close"]
        frames.append(normalized)
    if not frames:
        raise RuntimeError("stooq returned no usable ETF data")
    return pd.concat(frames, ignore_index=True)


def download_public_ohlcv(config: dict) -> pd.DataFrame:
    universe = list(config["universe"])
    start = str(config["start_date"])
    end = str(config["end_date"])
    source = str(config.get("download_source", "yfinance"))
    if source == "stooq":
        return _download_stooq(universe, start, end)
    try:
        return _download_yfinance(universe, start, end)
    except Exception:
        return _download_stooq(universe, start, end)


def make_offline_fixture_ohlcv(config: dict) -> pd.DataFrame:
    if not bool(config.get("allow_synthetic_fallback", False)):
        raise RuntimeError("offline fixture fallback is disabled in config")
    rng = np.random.default_rng(20260629)
    universe = list(config["universe"])
    dates = pd.bdate_range(config["start_date"], config["end_date"])
    rows: list[dict] = []
    for idx, ticker in enumerate(universe):
        price = 80.0 + idx * 3.0
        drift = 0.00010 + 0.00002 * (idx % 5)
        vol = 0.010 + 0.002 * (idx % 4)
        for date in dates:
            shock = rng.normal(drift, vol)
            price = max(5.0, price * (1.0 + shock))
            rows.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "open": price * (1.0 + rng.normal(0.0, 0.001)),
                    "high": price * 1.003,
                    "low": price * 0.997,
                    "close": price,
                    "adj_close": price,
                    "volume": int(1_000_000 + 10_000 * idx),
                }
            )
    return pd.DataFrame(rows, columns=OHLCV_COLUMNS)


def load_or_download_public_data(config: dict, root: Path, quick: bool = False) -> PublicDataBundle:
    raw_path = _path(root, str(config["raw_data_path"]))
    processed_path = _path(root, str(config["processed_data_path"]))
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.parent.mkdir(parents=True, exist_ok=True)

    if processed_path.exists():
        processed = pd.read_csv(processed_path, parse_dates=["date"])
    else:
        if raw_path.exists():
            raw = pd.read_csv(raw_path, parse_dates=["date"])
        elif quick and bool(config.get("allow_synthetic_fallback", False)):
            raw = make_offline_fixture_ohlcv(config)
            raw.to_csv(raw_path, index=False)
        else:
            raw = download_public_ohlcv(config)
            raw.to_csv(raw_path, index=False)
        processed, _ = process_public_ohlcv(raw, config)
        processed.to_csv(processed_path, index=False)

    processed, missing_log = process_public_ohlcv(processed, config)
    if len(processed["ticker"].unique()) < int(config["min_assets"]):
        raise RuntimeError("fewer than min_assets have usable aligned data")
    return PublicDataBundle(
        prices=processed,
        universe=tuple(sorted(processed["ticker"].unique())),
        start_date=pd.Timestamp(processed["date"].min()),
        end_date=pd.Timestamp(processed["date"].max()),
        missing_log=missing_log,
    )


def process_public_ohlcv(raw: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = raw.copy()
    data["date"] = pd.to_datetime(data["date"])
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.sort_values(["ticker", "date"])
    missing_rows = data[data["adj_close"].isna()].copy()
    data = data.dropna(subset=["adj_close"])

    counts = data.groupby("ticker")["date"].nunique().sort_values(ascending=False)
    min_assets = int(config["min_assets"])
    keep = [ticker for ticker in config["universe"] if ticker in counts.index]
    if len(keep) < min_assets:
        raise RuntimeError(f"only {len(keep)} tickers downloaded; need at least {min_assets}")
    data = data[data["ticker"].isin(keep)].copy()

    common_dates = None
    for _, group in data.groupby("ticker"):
        dates = set(pd.to_datetime(group["date"]))
        common_dates = dates if common_dates is None else common_dates.intersection(dates)
    if not common_dates:
        raise RuntimeError("no common trading dates across ETF universe")
    data = data[data["date"].isin(common_dates)].copy()
    data = data.sort_values(["date", "ticker"]).reset_index(drop=True)

    full_index = pd.MultiIndex.from_product(
        [sorted(common_dates), sorted(data["ticker"].unique())], names=["date", "ticker"]
    )
    observed_index = pd.MultiIndex.from_frame(data[["date", "ticker"]])
    missing_pairs = full_index.difference(observed_index)
    missing_log = pd.DataFrame(list(missing_pairs), columns=["date", "ticker"])
    if not missing_rows.empty:
        missing_log = pd.concat([missing_log, missing_rows[["date", "ticker"]]], ignore_index=True)
    return data[OHLCV_COLUMNS], missing_log.sort_values(["date", "ticker"]).reset_index(drop=True)
