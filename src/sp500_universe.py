from __future__ import annotations

from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def _path(root: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root / path


def _to_yfinance_symbol(symbol: str) -> str:
    return str(symbol).strip().replace(".", "-")


def fetch_current_sp500_constituents(config: dict) -> pd.DataFrame:
    url = str(config.get("constituents_url", WIKIPEDIA_SP500_URL))
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 TASE research diagnostic"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    tables = pd.read_html(StringIO(html))
    if not tables:
        raise RuntimeError("could not read S&P 500 constituents table")
    table = tables[0].copy()
    rename = {
        "Symbol": "ticker",
        "Security": "company_name",
        "GICS Sector": "sector",
        "GICS Sub-Industry": "sub_industry",
        "Headquarters Location": "headquarters",
        "Date added": "date_added",
        "CIK": "cik",
        "Founded": "founded",
    }
    table = table.rename(columns=rename)
    required = ["ticker", "company_name", "sector"]
    missing = [col for col in required if col not in table.columns]
    if missing:
        raise RuntimeError(f"S&P 500 table missing columns: {missing}")
    keep = [col for col in ["ticker", "company_name", "sector", "sub_industry", "headquarters", "date_added", "cik", "founded"] if col in table.columns]
    out = table[keep].copy()
    out["ticker"] = out["ticker"].astype(str).str.strip()
    out["yfinance_ticker"] = out["ticker"].map(_to_yfinance_symbol)
    out["retrieved_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
    out["source_url"] = url
    return out.sort_values("ticker").reset_index(drop=True)


def load_or_fetch_sp500_constituents(config: dict, root: Path, refresh: bool = False) -> pd.DataFrame:
    path = _path(root, str(config["constituents_path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        return pd.read_csv(path)
    constituents = fetch_current_sp500_constituents(config)
    constituents.to_csv(path, index=False)
    return constituents
