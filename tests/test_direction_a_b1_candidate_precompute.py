from __future__ import annotations

import pandas as pd

from src.direction_a.candidate_operators import IMPLEMENTED_OPERATOR_FAMILIES, compute_candidate_pnl, compute_signal, parse_parameters, signal_to_positions
from src.direction_a.candidate_precompute import select_smoke_candidates
from src.direction_a.price_loader import make_deterministic_mock_price_panel, price_panel_to_matrices
from src.direction_a.universe_builder import build_smoke_universe


def test_representative_operators_are_implemented() -> None:
    required = {"cross_sectional_momentum", "short_term_reversal", "volatility", "volume_liquidity", "moving_average_crossover", "breakout", "low_volatility"}
    assert required.issubset(IMPLEMENTED_OPERATOR_FAMILIES)


def test_signal_position_turnover_shapes_and_past_only() -> None:
    library = pd.read_csv("outputs/direction_a_b0/candidate_library_spec.csv")
    candidates = select_smoke_candidates(library, 60)
    universe = build_smoke_universe(8)
    panel = make_deterministic_mock_price_panel(universe, "2018-01-01", "2018-06-30")
    prices, volumes = price_panel_to_matrices(panel)
    row = candidates.iloc[0]
    signal = compute_signal(row["operator_family"], parse_parameters(row["parameter_json"]), prices, volumes)
    positions = signal_to_positions(signal)
    pnl = compute_candidate_pnl(positions, prices, 5)
    assert signal.shape == prices.shape
    assert positions.shape == prices.shape
    assert (pnl["turnover"] >= 0).all()
    assert pnl["cost_adjusted_pnl"].shape[0] == prices.shape[0]
    assert not candidates["uses_future_data"].any()
