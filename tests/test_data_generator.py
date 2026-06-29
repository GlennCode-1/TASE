from __future__ import annotations

import yaml

from src.data_generator import assert_no_split_overlap, generate_synthetic_data


def _config() -> dict:
    with open("configs/killtest.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["n_assets"] = 5
    config["train_days"] = 20
    config["val_days"] = 8
    config["test_days"] = 7
    config["n_seeds"] = 1
    return config


def test_data_split_no_overlap() -> None:
    bundle = generate_synthetic_data(_config(), seed=0)
    assert_no_split_overlap(bundle.split_days)
    assert bundle.split("train")["day"].nunique() == 20
    assert bundle.split("validation")["day"].nunique() == 8
    assert bundle.split("test")["day"].nunique() == 7


def test_future_field_unavailable_before_time() -> None:
    bundle = generate_synthetic_data(_config(), seed=1)
    assert not bundle.is_feature_available_at_decision_time("future_ret_1d")
    assert not bundle.is_feature_available_at_decision_time("next_day_direction")
    assert bundle.is_feature_available_at_decision_time("signal")
    assert "future_ret_1d" not in bundle.available_feature_columns("validation")
