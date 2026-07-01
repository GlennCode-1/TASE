from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SmokeUniverse:
    tickers: tuple[str, ...]
    sectors: dict[str, str]
    universe_id: str
    role: str


SECTOR_CYCLE = ("technology", "healthcare", "financials", "industrials", "consumer", "energy")


def build_smoke_universe(max_assets: int = 30, role: str = "deterministic_mock_diagnostic") -> SmokeUniverse:
    n = min(int(max_assets), 30)
    tickers = tuple(f"B1A{i:02d}" for i in range(n))
    sectors = {ticker: SECTOR_CYCLE[i % len(SECTOR_CYCLE)] for i, ticker in enumerate(tickers)}
    return SmokeUniverse(tickers=tickers, sectors=sectors, universe_id=f"b1_mock_{n}_assets", role=role)
