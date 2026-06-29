from __future__ import annotations

import yaml

from src.data_generator import generate_synthetic_data
from src.evaluator import OUTER_EVALUATOR_VERSION, evaluate_harness
from src.experiments import run_killtest
from src.harness import base_harness


def _config() -> dict:
    with open("configs/killtest.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["n_assets"] = 8
    config["train_days"] = 40
    config["val_days"] = 20
    config["test_days"] = 20
    config["n_seeds"] = 1
    config["patch_budget"] = 4
    config["candidate_per_round"] = 3
    return config


def test_locked_test_not_used_in_selection() -> None:
    config = _config()
    _, patch_log, _ = run_killtest(config)
    assert set(patch_log["selection_split"].dropna()) == {"validation"}
    accepted = patch_log[patch_log["status"] == "ACCEPTED"]
    assert not accepted.empty
    assert not accepted["selection_score"].isna().any()


def test_outer_evaluator_same_for_both_arms() -> None:
    config = _config()
    results, _, _ = run_killtest(config)
    versions = set(results["outer_evaluator_version"])
    assert versions == {OUTER_EVALUATOR_VERSION}
    assert set(results["arm"]) == {"Generic Unconstrained", "TASE Finance-Constrained"}


def test_outer_evaluator_is_deterministic() -> None:
    config = _config()
    bundle = generate_synthetic_data(config, seed=2)
    harness = base_harness(config)
    first = evaluate_harness(bundle, "validation", harness, config)
    second = evaluate_harness(bundle, "validation", harness, config)
    assert first == second
