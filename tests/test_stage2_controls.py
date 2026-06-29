from __future__ import annotations

import yaml

from src.experiments import run_stage2_controls


def _config() -> dict:
    with open("configs/killtest_stage2.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["n_assets"] = 8
    config["train_days"] = 40
    config["val_days"] = 20
    config["test_days"] = 20
    config["n_seeds"] = 2
    config["patch_budget"] = 4
    config["candidate_per_round"] = 3
    return config


def test_stage2_runs_four_arms() -> None:
    results, patch_log, summary = run_stage2_controls(_config())
    assert set(results["arm"]) == {
        "Generic Unconstrained",
        "Constrained Fixed",
        "Random Legal Patch",
        "TASE Finance-Constrained",
    }
    assert set(summary["arm"]) == set(results["arm"])
    assert not patch_log.empty


def test_stage2_random_legal_does_not_select_by_validation_score() -> None:
    _, patch_log, _ = run_stage2_controls(_config())
    random_log = patch_log[patch_log["arm"] == "Random Legal Patch"]
    assert not random_log.empty
    assert set(random_log["selection_split"]) == {"none"}
    accepted = random_log[random_log["status"] == "ACCEPTED_RANDOM"]
    assert not accepted.empty
    assert accepted["selection_score"].isna().all()


def test_stage2_result_has_control_delta_columns() -> None:
    results, _, _ = run_stage2_controls(_config())
    required = {
        "beats_constrained_fixed",
        "beats_random_legal_patch",
        "delta_vs_constrained_fixed_locked_test",
        "delta_vs_random_legal_patch_locked_test",
        "delta_vs_constrained_fixed_compliant_score",
        "delta_vs_random_legal_patch_compliant_score",
    }
    assert required.issubset(results.columns)
    tase = results[results["arm"] == "TASE Finance-Constrained"]
    assert len(tase) == 2
