from __future__ import annotations

import yaml

from src.harness import base_harness
from src.patches import PatchProposal, apply_patch_to_harness
from src.validator import validate_tase_patch


def _config() -> dict:
    with open("configs/killtest.yaml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _proposal(values: dict) -> PatchProposal:
    return PatchProposal("test", values, "unit", len(values))


def test_validator_rejects_future_access() -> None:
    config = _config()
    candidate = apply_patch_to_harness(base_harness(config), _proposal({"allow_future_fields": True}))
    result = validate_tase_patch(candidate, _proposal({"allow_future_fields": True}), config)
    assert not result.accepted
    assert "LEAKAGE" in result.reasons


def test_validator_rejects_silent_skip() -> None:
    config = _config()
    candidate = apply_patch_to_harness(base_harness(config), _proposal({"skip_bad_days": True}))
    result = validate_tase_patch(candidate, _proposal({"skip_bad_days": True}), config)
    assert not result.accepted
    assert "SILENT_SKIP" in result.reasons


def test_validator_rejects_risk_bypass() -> None:
    config = _config()
    patch = {"risk_gate_enabled": False, "risk_gate_position_limit": config["max_position"] * 3}
    candidate = apply_patch_to_harness(base_harness(config), _proposal(patch))
    result = validate_tase_patch(candidate, _proposal(patch), config)
    assert not result.accepted
    assert "RISK_BYPASS" in result.reasons
