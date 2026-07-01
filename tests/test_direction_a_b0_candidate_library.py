from __future__ import annotations

import json

from src.direction_a.candidate_library import REQUIRED_OPERATOR_FAMILIES, build_candidate_library, candidate_count_status, operator_library_spec


def test_candidate_ids_deterministic() -> None:
    a = build_candidate_library()
    b = build_candidate_library()
    assert list(a["candidate_id"].head(50)) == list(b["candidate_id"].head(50))


def test_operator_library_frozen_and_complete() -> None:
    operators = operator_library_spec()
    assert set(REQUIRED_OPERATOR_FAMILIES).issubset(set(operators["operator_family"]))
    assert operators["frozen_in_b0"].all()


def test_parameter_grid_deterministic() -> None:
    candidates = build_candidate_library()
    first = json.loads(candidates.iloc[0]["parameter_json"])
    assert first["cost_model"] == "fixed_not_tunable"
    assert "holding_period" in first


def test_candidate_count_within_target() -> None:
    candidates = build_candidate_library()
    assert candidate_count_status(len(candidates), 1000, 2000) == "PASS_WITHIN_TARGET"


def test_no_candidate_uses_future_data_by_default() -> None:
    candidates = build_candidate_library()
    assert not candidates["uses_future_data"].any()
