from __future__ import annotations

from src.direction_a.data_audit import build_source_audit, main_data_path_decision, validate_audit


def _audit():
    return build_source_audit({"start_date": "2007-01-01", "end_date": "2024-12-31"})


def test_current_constituents_cannot_be_true_pit() -> None:
    current = _audit()[lambda df: df["source_name"].str.contains("Current", case=False)].iloc[0]
    assert bool(current["is_true_pit"]) is False
    assert current["decision"] == "REJECT"


def test_etf_tier_cannot_be_main_pit_evidence() -> None:
    etf = _audit()[lambda df: df["source_name"].str.contains("ETF", case=False)].iloc[0]
    assert etf["decision"] == "ACCEPT_SANITY_ONLY"


def test_missing_license_triggers_warning() -> None:
    warnings = validate_audit(_audit())
    assert any("license" in warning for warning in warnings)


def test_auth_required_cannot_be_default_public_path() -> None:
    audit = _audit()
    assert audit[(audit["requires_auth"] == True) & audit["decision"].eq("ACCEPT_MAIN_CANDIDATE")].empty


def test_fallback_diagnostic_marks_claim_downgrade() -> None:
    status, text = main_data_path_decision(_audit())
    assert status == "PASS_WITH_DIAGNOSTIC_FALLBACK"
    assert "downgraded" in text
