from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .public_data import OHLCV_COLUMNS, _normalize_ohlcv
from .sp500_universe import load_or_fetch_sp500_constituents


@dataclass(frozen=True)
class StockDataBundle:
    prices: pd.DataFrame
    universe: tuple[str, ...]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    missing_log: pd.DataFrame
    constituents: pd.DataFrame


def _path(root: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root / path


def download_sp500_ohlcv(tickers: list[str], config: dict, batch_size: int = 80) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("yfinance is not installed") from exc
    frames: list[pd.DataFrame] = []
    for start in range(0, len(tickers), batch_size):
        batch = tickers[start : start + batch_size]
        data = yf.download(
            batch,
            start=str(config["start_date"]),
            end=str(config["end_date"]),
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        if data.empty:
            continue
        if isinstance(data.columns, pd.MultiIndex):
            first_level = set(map(str, data.columns.get_level_values(0)))
            second_level = set(map(str, data.columns.get_level_values(1)))
            for ticker in batch:
                frame = None
                if ticker in first_level:
                    frame = data[ticker].dropna(how="all")
                elif ticker in second_level:
                    frame = data.xs(ticker, level=1, axis=1).dropna(how="all")
                if frame is not None and not frame.empty:
                    frames.append(_normalize_ohlcv(frame, ticker))
        else:
            if len(batch) == 1:
                frames.append(_normalize_ohlcv(data, batch[0]))
    if not frames:
        raise RuntimeError("yfinance returned no usable S&P 500 stock data")
    return pd.concat(frames, ignore_index=True)


def make_offline_stock_fixture(config: dict, n_assets: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = int(n_assets or max(int(config.get("quick_min_assets", 40)), 45))
    dates = pd.bdate_range(config["start_date"], config["end_date"])
    rows: list[dict] = []
    constituents = []
    rng = np.random.default_rng(20260629)
    for idx in range(n):
        ticker = f"T{idx:03d}"
        constituents.append(
            {
                "ticker": ticker,
                "yfinance_ticker": ticker,
                "company_name": f"Test Company {idx}",
                "sector": "Synthetic",
                "sub_industry": "Synthetic",
                "retrieved_at": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
                "source_url": "offline_fixture",
            }
        )
        price = 50.0 + idx
        for day_idx, date in enumerate(dates):
            if idx % 13 == 0 and day_idx % 29 == 0:
                continue
            if idx % 17 == 0 and day_idx < 35:
                continue
            shock = rng.normal(0.0002 + 0.00001 * (idx % 7), 0.018 + 0.002 * (idx % 5))
            if idx % 19 == 0 and day_idx == len(dates) // 2:
                shock = 0.70
            price = max(1.0, price * (1.0 + shock))
            close = price
            adj = close
            if idx % 23 == 0 and day_idx > len(dates) // 2:
                adj = close * 0.5
            rows.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "open": close * (1.0 + rng.normal(0, 0.001)),
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "adj_close": adj,
                    "volume": int(500_000 + 1000 * idx),
                }
            )
    return pd.DataFrame(rows, columns=OHLCV_COLUMNS), pd.DataFrame(constituents)


def _finalize_missing_log(missing_log: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = ["date", "event_start_date", "event_end_date", "ticker", "event_type", "reason", "date_status", "missing_ratio"]
    if missing_log.empty:
        return pd.DataFrame(columns=columns)
    out = missing_log.copy()
    if "missing_ratio" not in out.columns:
        out["missing_ratio"] = np.nan
    out["date"] = pd.to_datetime(out.get("date"), errors="coerce")
    known = out["date"].notna()
    out["event_start_date"] = pd.NaT
    out["event_end_date"] = pd.NaT
    out.loc[known, "event_start_date"] = out.loc[known, "date"]
    out.loc[known, "event_end_date"] = out.loc[known, "date"]
    out.loc[~known, "event_start_date"] = pd.Timestamp(config["start_date"])
    out.loc[~known, "event_end_date"] = pd.Timestamp(config["end_date"])
    out["event_type"] = out["reason"].astype(str)
    out["date_status"] = np.where(known, "KNOWN", "UNKNOWN")
    return out.reindex(columns=columns)


def process_sp500_ohlcv(raw: pd.DataFrame, constituents: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = raw.copy()
    data["date"] = pd.to_datetime(data["date"])
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.sort_values(["ticker", "date"])
    requested = list(constituents["yfinance_ticker"].astype(str))
    present = set(data["ticker"].astype(str).unique())
    missing_rows = data[data["adj_close"].isna()][["date", "ticker"]].copy()
    missing_rows["reason"] = "missing_adjusted_close"
    data = data.dropna(subset=["adj_close"])
    counts = data.groupby("ticker")["date"].nunique()
    max_count = int(counts.max()) if not counts.empty else 0
    required_count = int(np.floor(max_count * float(config.get("min_history_coverage", 0.90)))) if max_count else 0
    max_missing_ratio = float(config.get("max_missing_ratio", 0.10))
    keep: list[str] = []
    log_rows: list[dict] = []
    for ticker in requested:
        if ticker not in present:
            log_rows.append({"date": pd.NaT, "ticker": ticker, "reason": "download_failed", "missing_ratio": 1.0})
            continue
        count = int(counts.get(ticker, 0))
        missing_ratio = 1.0 - (count / max(1, max_count))
        if count < required_count:
            log_rows.append({"date": pd.NaT, "ticker": ticker, "reason": "insufficient_history", "missing_ratio": missing_ratio})
            continue
        if missing_ratio > max_missing_ratio:
            log_rows.append({"date": pd.NaT, "ticker": ticker, "reason": "missing_ratio_high", "missing_ratio": missing_ratio})
            continue
        keep.append(ticker)
        if missing_ratio > 0:
            log_rows.append({"date": pd.NaT, "ticker": ticker, "reason": "some_missing_days", "missing_ratio": missing_ratio})
    if len(keep) < int(config["min_assets"]):
        raise RuntimeError(f"only {len(keep)} stocks retained; need at least {config['min_assets']}")
    data = data[data["ticker"].isin(keep)].copy()
    returns = data.groupby("ticker")["adj_close"].pct_change()
    bad = data[returns.abs() > float(config.get("bad_tick_abs_return", 0.50))][["date", "ticker"]].copy()
    bad["reason"] = "bad_tick_extreme_return"
    ratio = data["close"] / data["adj_close"].replace(0, np.nan)
    ratio_jump = ratio.groupby(data["ticker"]).pct_change().abs()
    corporate = data[ratio_jump > float(config.get("corporate_action_ratio_jump", 0.50))][["date", "ticker"]].copy()
    corporate["reason"] = "corporate_action_anomaly"
    logs = [pd.DataFrame(log_rows), missing_rows, bad, corporate]
    missing_log = pd.concat([frame for frame in logs if not frame.empty], ignore_index=True)
    missing_log = _finalize_missing_log(missing_log, config)
    return data[OHLCV_COLUMNS].sort_values(["date", "ticker"]).reset_index(drop=True), missing_log.sort_values(["ticker", "date"], na_position="first").reset_index(drop=True)


def load_or_download_sp500_data(config: dict, root: Path, quick: bool = False, refresh_constituents: bool = False) -> StockDataBundle:
    run_config = dict(config)
    constituents = load_or_fetch_sp500_constituents(run_config, root, refresh=refresh_constituents)
    if quick and int(run_config.get("quick_max_assets", 0)) > 0:
        constituents = constituents.head(int(run_config["quick_max_assets"])).copy()
        run_config["min_assets"] = int(run_config.get("quick_min_assets", min(40, len(constituents))))
    raw_path = _path(root, str(run_config["raw_data_path"]))
    processed_path = _path(root, str(run_config["processed_data_path"]))
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists():
        raw = pd.read_csv(raw_path, parse_dates=["date"])
        raw_ticker_count = int(raw["ticker"].nunique()) if "ticker" in raw.columns else 0
        if not quick and raw_ticker_count < int(run_config["min_assets"]):
            tickers = list(constituents["yfinance_ticker"].astype(str))
            raw = download_sp500_ohlcv(tickers, run_config)
            raw.to_csv(raw_path, index=False)
        processed, missing_log = process_sp500_ohlcv(raw, constituents, run_config)
        processed.to_csv(processed_path, index=False)
    elif quick and bool(run_config.get("allow_synthetic_fallback", False)):
        raw, fixture_constituents = make_offline_stock_fixture(run_config)
        constituents = fixture_constituents
        constituents.to_csv(_path(root, str(run_config["constituents_path"])), index=False)
        raw.to_csv(raw_path, index=False)
        processed, missing_log = process_sp500_ohlcv(raw, constituents, run_config)
        processed.to_csv(processed_path, index=False)
    else:
        tickers = list(constituents["yfinance_ticker"].astype(str))
        raw = download_sp500_ohlcv(tickers, run_config)
        raw.to_csv(raw_path, index=False)
        processed, missing_log = process_sp500_ohlcv(raw, constituents, run_config)
        processed.to_csv(processed_path, index=False)
    universe = tuple(sorted(processed["ticker"].unique()))
    if len(universe) < int(run_config["min_assets"]):
        raise RuntimeError(f"fewer than min_assets retained: {len(universe)}")
    return StockDataBundle(
        prices=processed,
        universe=universe,
        start_date=pd.Timestamp(processed["date"].min()),
        end_date=pd.Timestamp(processed["date"].max()),
        missing_log=missing_log,
        constituents=constituents,
    )
