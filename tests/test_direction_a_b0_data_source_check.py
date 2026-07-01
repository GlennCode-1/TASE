from __future__ import annotations

import pandas as pd

from src.direction_a.data_source_check import b0_data_status, build_data_source_feasibility, validate_source_roles


def _cfg() -> dict:
    return {"start_date": "2007-01-01", "end_date": "2024-12-31"}


def test_missing_true_pit_source_triggers_warning_status() -> None:
    feasibility = build_data_source_feasibility(_cfg())
    public_true = feasibility[(feasibility["requires_auth"] == False) & (feasibility["is_point_in_time"] == True)]
    assert public_true.empty
    assert b0_data_status(feasibility) == "NEEDS_USER_INPUT"


def test_current_constituents_cannot_be_marked_true_pit() -> None:
    feasibility = build_data_source_feasibility(_cfg())
    current = feasibility[feasibility["source_name"].str.contains("Current", case=False)].iloc[0]
    assert bool(current["is_point_in_time"]) is False
    assert current["recommended_role"] == "not_main_evidence"
    assert validate_source_roles(feasibility) == []


def test_etf_universe_marked_sanity_tier() -> None:
    feasibility = build_data_source_feasibility(_cfg())
    etf = feasibility[feasibility["source_name"].str.contains("ETF", case=False)].iloc[0]
    assert etf["recommended_role"] == "sanity_universe_only"


def test_fallback_universe_marked_diagnostic_not_unbiased_main() -> None:
    feasibility = build_data_source_feasibility(_cfg())
    fallback = feasibility[feasibility["recommended_role"] == "liquid_us_universe_diagnostic"].iloc[0]
    assert bool(fallback["is_point_in_time"]) is False
    assert fallback["survivorship_bias_risk"] == "high"
