from __future__ import annotations

import inspect

import yaml

from src.evaluator import EvaluationMetrics, OUTER_EVALUATOR_VERSION
from src.experiments import run_stage2_controls, run_stage3_proposer
from src.harness import base_harness
from src.patches import diagnostic_guided_tase_patches


def _config() -> dict:
    with open("configs/killtest_stage3.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["n_assets"] = 8
    config["train_days"] = 40
    config["val_days"] = 20
    config["test_days"] = 20
    config["n_seeds"] = 1
    config["patch_budget"] = 5
    config["candidate_per_round"] = 4
    return config


def _metrics(**overrides) -> EvaluationMetrics:
    values = {
        "split": "validation",
        "score": -10.0,
        "raw_return": -0.1,
        "sharpe": -10.0,
        "constraint_compliant_score": -13.0,
        "leakage_violations": 0,
        "silent_skip_count": 0,
        "risk_violations": 10,
        "turnover_violations": 0,
        "complexity_penalty": 0.0,
        "n_days_evaluated": 20,
        "n_days_available": 20,
    }
    values.update(overrides)
    return EvaluationMetrics(**values)


def test_diagnostic_proposer_uses_validation_only() -> None:
    signature = inspect.signature(diagnostic_guided_tase_patches)
    assert "validation_metrics" in signature.parameters
    assert "locked" not in "".join(signature.parameters)


def test_diagnostic_proposer_never_uses_locked_test() -> None:
    _, patch_log, _ = run_stage3_proposer(_config())
    tase_log = patch_log[patch_log["arm"] == "TASE Finance-Constrained"]
    assert not tase_log.empty
    assert set(tase_log["selection_split"]) == {"validation"}


def test_diagnostic_proposer_proposes_risk_tightening_when_risk_violations_high() -> None:
    config = _config()
    proposals = diagnostic_guided_tase_patches(
        current=base_harness(config),
        validation_metrics=_metrics(risk_violations=18),
        config=config,
        round_idx=0,
        candidate_per_round=4,
    )
    assert any(p.values.get("risk_gate_position_limit", config["max_position"]) < config["max_position"] for p in proposals)
    assert all(not p.values.get("allow_future_fields", False) for p in proposals)


def test_diagnostic_proposer_proposes_fail_closed_when_failures_high() -> None:
    config = _config()
    proposals = diagnostic_guided_tase_patches(
        current=base_harness(config),
        validation_metrics=_metrics(silent_skip_count=4, risk_violations=0),
        config=config,
        round_idx=0,
        candidate_per_round=4,
        previous_rejections=("SILENT_SKIP",),
    )
    assert any(p.values.get("control_flow_mode") == "fail_closed" for p in proposals)


def test_tase_stage3_accepts_more_legal_patches_than_stage2_smoke() -> None:
    config = _config()
    stage2_results, _, _ = run_stage2_controls(config)
    stage3_results, _, _ = run_stage3_proposer(config)
    stage2_tase = stage2_results[stage2_results["arm"] == "TASE Finance-Constrained"]["accepted_patch_count"].mean()
    stage3_tase = stage3_results[stage3_results["arm"] == "TASE Finance-Constrained"]["accepted_patch_count"].mean()
    assert stage3_tase > stage2_tase


def test_stage3_same_outer_evaluator_for_all_groups() -> None:
    results, _, _ = run_stage3_proposer(_config())
    assert set(results["outer_evaluator_version"]) == {OUTER_EVALUATOR_VERSION}
    assert set(results["arm"]) == {
        "Generic Unconstrained",
        "Constrained Fixed",
        "Random Legal Patch",
        "TASE Finance-Constrained",
    }
