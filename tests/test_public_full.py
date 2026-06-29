from __future__ import annotations

from pathlib import Path
import os
import subprocess

import pandas as pd
import pytest
import yaml

from src.features import build_lagged_features, feature_lag_audit
from src.public_data import PublicDataBundle, make_offline_fixture_ohlcv, process_public_ohlcv
from src.public_experiment import SEARCH_ARMS, run_public_toy
from src.public_task import base_public_harness, compute_target_weights, w_t_invariance_test


def _config() -> dict:
    with open("configs/public_full.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["universe"] = [
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "VTI",
        "EFA",
        "EEM",
        "TLT",
        "IEF",
        "SHY",
        "GLD",
        "SLV",
        "VNQ",
        "XLF",
        "XLK",
        "XLE",
        "XLI",
        "XLU",
        "XLP",
        "XLY",
        "XLV",
        "XLB",
        "VUG",
        "VTV",
        "SMH",
        "XBI",
        "LQD",
        "HYG",
        "TIP",
        "AGG",
    ]
    config["start_date"] = "2020-01-01"
    config["end_date"] = "2020-12-31"
    config["min_assets"] = 20
    config["min_history_coverage"] = 0.90
    config["allow_synthetic_fallback"] = True
    config["selection_blocks"] = 4
    config["validation_window_blocks"] = 1
    config["oos_window_blocks"] = 1
    config["final_confirmation_months"] = 2
    config["n_seeds"] = 1
    config["quick_n_seeds"] = 1
    config["search_budget"] = 4
    config["quick_search_budget"] = 3
    config["bootstrap_samples"] = 20
    return config


def _bundle(config: dict | None = None) -> PublicDataBundle:
    cfg = config or _config()
    raw = make_offline_fixture_ohlcv(cfg)
    processed, missing_log = process_public_ohlcv(raw, cfg)
    return PublicDataBundle(
        prices=processed,
        universe=tuple(sorted(processed["ticker"].unique())),
        start_date=pd.Timestamp(processed["date"].min()),
        end_date=pd.Timestamp(processed["date"].max()),
        missing_log=missing_log,
    )


def test_public_full_universe_filtering() -> None:
    cfg = _config()
    raw = make_offline_fixture_ohlcv(cfg)
    sparse = raw[~((raw["ticker"] == "AGG") & (raw["date"] < "2020-10-01"))]
    processed, missing_log = process_public_ohlcv(sparse, cfg)
    assert "AGG" not in set(processed["ticker"])
    assert "insufficient_history" in set(missing_log["reason"])


def test_min_assets_after_filtering() -> None:
    cfg = _config()
    processed, _ = process_public_ohlcv(make_offline_fixture_ohlcv(cfg), cfg)
    assert processed["ticker"].nunique() >= cfg["min_assets"]


def test_no_synthetic_fallback() -> None:
    with open("configs/public_full.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    assert config["allow_synthetic_fallback"] is False


def test_all_features_lagged() -> None:
    cfg = _config()
    features = build_lagged_features(_bundle(cfg).prices, cfg["momentum_window"], cfg["volatility_window"], cfg["volatility_penalty"])
    features.attrs["used_features"] = ("momentum_20", "volatility_20", "score")
    assert feature_lag_audit(features)


def test_pi_invariance_for_tase_patches() -> None:
    cfg = _config()
    features = build_lagged_features(_bundle(cfg).prices, cfg["momentum_window"], cfg["volatility_window"], cfg["volatility_penalty"])
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    legal = compute_target_weights(features, base.with_patch({"logging": "verbose", "control_flow": "retry"}), cfg)
    assert w_t_invariance_test(reference, legal)


def test_tase_rejects_rebalance_frequency_patch() -> None:
    cfg = _config()
    features = build_lagged_features(_bundle(cfg).prices, cfg["momentum_window"], cfg["volatility_window"], cfg["volatility_penalty"])
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    changed = compute_target_weights(features, base.with_patch({"rebalance": "M", "allow_weight_change": True}), cfg)
    assert not w_t_invariance_test(reference, changed)


def test_tase_rejects_volatility_targeting_patch() -> None:
    cfg = _config()
    features = build_lagged_features(_bundle(cfg).prices, cfg["momentum_window"], cfg["volatility_window"], cfg["volatility_penalty"])
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    changed = compute_target_weights(features, base.with_patch({"volatility_penalty": 0.8, "allow_weight_change": True}), cfg)
    assert not w_t_invariance_test(reference, changed)


def test_public_full_same_budget_for_search_arms() -> None:
    cfg = _config()
    output = run_public_toy(_bundle(cfg), cfg, quick=True)
    counts = output.candidate_log.groupby(["arm", "seed", "split_id"])["candidate_id"].nunique()
    assert set(output.candidate_log["arm"]) == set(SEARCH_ARMS)
    assert set(counts.unique()) == {cfg["quick_search_budget"]}


def test_public_full_pbo_has_multiple_splits() -> None:
    cfg = _config()
    output = run_public_toy(_bundle(cfg), cfg, quick=True)
    assert output.candidate_log["split_id"].nunique() >= 2
    assert "pbo_estimate" in output.summary.columns


def test_checkpoint_resume(tmp_path: Path) -> None:
    cfg = _config()
    cfg["raw_data_path"] = str(tmp_path / "raw.csv")
    cfg["processed_data_path"] = str(tmp_path / "processed.csv")
    cfg_path = tmp_path / "public_full_test.yaml"
    raw = make_offline_fixture_ohlcv(cfg)
    raw.to_csv(cfg["raw_data_path"], index=False)
    cfg["allow_synthetic_fallback"] = False
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    run_root = tmp_path / "run_root"
    env = {**os.environ, "TASE_RUN_ROOT": str(run_root)}
    subprocess.run(
        ["python", "scripts/run_public_full.py", "--config", str(cfg_path), "--quick"],
        check=True,
        timeout=60,
        env=env,
    )
    subprocess.run(
        ["python", "scripts/run_public_full.py", "--config", str(cfg_path), "--quick", "--resume"],
        check=True,
        timeout=60,
        env=env,
    )
    assert (run_root / "outputs/checkpoints/public_full_quick_results_by_split.csv").exists()


def test_locked_test_not_used_for_selection_public_full() -> None:
    cfg = _config()
    output = run_public_toy(_bundle(cfg), cfg, quick=True)
    assert output.candidate_log["selection_score"].notna().all()
    assert "final" not in " ".join(output.candidate_log.columns).lower()
