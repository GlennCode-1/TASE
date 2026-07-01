from __future__ import annotations

from src.direction_a.price_loader import make_deterministic_mock_price_panel
from src.direction_a.universe_builder import build_smoke_universe


def test_smoke_universe_respects_size_limit() -> None:
    universe = build_smoke_universe(30)
    assert len(universe.tickers) == 30
    assert universe.universe_id == "b1_mock_30_assets"


def test_mock_price_panel_shape() -> None:
    universe = build_smoke_universe(5)
    panel = make_deterministic_mock_price_panel(universe, "2018-01-01", "2018-01-31")
    assert set(panel.columns) == {"date", "ticker", "close", "volume", "sector"}
    assert panel["ticker"].nunique() == 5
