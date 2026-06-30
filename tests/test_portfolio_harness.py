from __future__ import annotations

from pathlib import Path
import os
import subprocess

import pandas as pd
import yaml

from src.features import assign_time_blocks
from src.public_data import PublicDataBundle, make_offline_fixture_ohlcv, process_public_ohlcv
from src.portfolio_experiment import run_portfolio_harness
from src.portfolio_harness_gates import clean_panel_w_star_invariance, legal_harness_gate, policy_specification_frozen
from src.portfolio_harness_patches import base_portfolio_harness, fixed_safe_harness
from src.portfolio_metrics import evaluate_portfolio_weights
from src.portfolio_optimizer import compute_portfolio_weight_matrix, repair_weights
from src.portfolio_task import build_portfolio_features, portfolio_feature_matrices


def _config() -> dict:
    with open("configs/portfolio_harness.yaml", "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["universe"] = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "VNQ", "XLF", "XLK", "XLE"]
    cfg["start_date"] = "2020-01-01"
    cfg["end_date"] = "2021-12-31"
    cfg["min_assets"] = 10
    cfg["allow_synthetic_fallback"] = True
    cfg["selection_blocks"] = 4
    cfg["validation_window_blocks"] = 1
    cfg["oos_window_blocks"] = 1
    cfg["final_confirmation_months"] = 2
    cfg["n_seeds"] = 1
    cfg["quick_n_seeds"] = 1
    cfg["search_budget"] = 4
    cfg["quick_search_budget"] = 3
    cfg["bootstrap_samples"] = 20
    return cfg


def _bundle(cfg: dict | None = None) -> PublicDataBundle:
    config = cfg or _config()
    raw = make_offline_fixture_ohlcv(config)
    processed, missing = process_public_ohlcv(raw, config)
    return PublicDataBundle(processed, tuple(sorted(processed["ticker"].unique())), pd.Timestamp(processed["date"].min()), pd.Timestamp(processed["date"].max()), missing)


def _matrices(cfg: dict | None = None):
    config = cfg or _config()
    features = build_portfolio_features(_bundle(config).prices, config)
    features = assign_time_blocks(features, config["selection_blocks"], config["final_confirmation_months"])
    return portfolio_feature_matrices(features)


def test_alpha_frozen_in_portfolio_task() -> None:
    cfg = _config()
    features = build_portfolio_features(_bundle(cfg).prices, cfg)
    assert features.attrs["used_features"] == ("momentum_20", "volatility_20", "score")
    assert "future_return_1d" not in features.attrs["used_features"]


def test_policy_specification_frozen() -> None:
    cfg = _config()
    base = fixed_safe_harness(base_portfolio_harness(cfg))
    legal = base.with_patch({"fallback_policy": "risk_parity"})
    illegal = base.with_patch({"risk_aversion_lambda": 1.0, "allow_policy_change": True})
    assert policy_specification_frozen(base, legal, cfg)
    assert not policy_specification_frozen(base, illegal, cfg)


def test_clean_panel_w_star_invariance_passes_for_solver_fallback_patch() -> None:
    cfg = _config()
    matrices = _matrices(cfg)
    base = fixed_safe_harness(base_portfolio_harness(cfg))
    legal = base.with_patch({"fallback_policy": "risk_parity", "retry_policy": "single_try_fallback"})
    assert clean_panel_w_star_invariance(base, legal, matrices, cfg)


def test_clean_panel_w_star_invariance_rejects_lambda_change() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    assert not clean_panel_w_star_invariance(base, base.with_patch({"risk_aversion_lambda": 0.5, "allow_policy_change": True}), matrices, cfg)


def test_clean_panel_w_star_invariance_rejects_max_weight_change() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    assert not clean_panel_w_star_invariance(base, base.with_patch({"max_weight": 0.5, "allow_policy_change": True}), matrices, cfg)


def test_clean_panel_w_star_invariance_rejects_rebalance_change() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    assert not clean_panel_w_star_invariance(base, base.with_patch({"rebalance_frequency": "M", "allow_policy_change": True}), matrices, cfg)


def test_clean_panel_w_star_invariance_rejects_alpha_change() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    assert not clean_panel_w_star_invariance(base, base.with_patch({"momentum_window": 60, "allow_policy_change": True}), matrices, cfg)


def test_constraint_repair_keeps_fixed_caps() -> None:
    cfg = _config()
    base = fixed_safe_harness(base_portfolio_harness(cfg))
    raw = pd.Series([0.8, 0.4, 0.3]).to_numpy()
    prev = pd.Series([0.1, 0.1, 0.1]).to_numpy()
    weights, turnover = repair_weights(raw, prev, ["a", "a", "b"], base, cfg)
    assert weights.max() <= cfg["max_weight"] + 1e-12
    assert turnover <= cfg["turnover_cap"] + 1e-12


def test_missing_handling_uses_past_only() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    legal = base.with_patch({"missing_policy": "past_only_impute"})
    ok, reason = legal_harness_gate(base, legal, matrices, cfg)
    assert ok, reason
    assert not legal.allow_future_returns


def test_unconstrained_invalid_policy_change_logged() -> None:
    cfg = _config()
    output = run_portfolio_harness(_bundle(cfg), cfg, quick=True)
    invalid = output.invalid_high_score_log
    assert not invalid.empty
    assert invalid["reason"].str.contains("POLICY_SPECIFICATION_CHANGED|FUTURE_RETURN_LEAKAGE|CLEAN_PANEL_W_STAR_CHANGED").any()


def test_tase_cannot_change_objective_weights() -> None:
    cfg = _config(); matrices = _matrices(cfg); base = fixed_safe_harness(base_portfolio_harness(cfg))
    illegal = base.with_patch({"objective_return_weight": 2.0, "allow_policy_change": True})
    ok, reason = legal_harness_gate(base, illegal, matrices, cfg)
    assert not ok
    assert "POLICY_SPECIFICATION_CHANGED" in reason


def test_paired_bootstrap_for_cvar_and_turnover() -> None:
    cfg = _config(); output = run_portfolio_harness(_bundle(cfg), cfg, quick=True)
    assert {"comparison", "metric", "mean_diff", "ci_low", "ci_high"}.issubset(output.paired_bootstrap.columns)
    assert {"cvar_95", "turnover"}.issubset(set(output.paired_bootstrap["metric"]))


def test_portfolio_harness_outputs_risk_metrics() -> None:
    cfg = _config(); output = run_portfolio_harness(_bundle(cfg), cfg, quick=True)
    needed = {"locked_cvar_95", "locked_drawdown_duration", "turnover", "transaction_cost_paid", "constraint_violation_severity", "optimizer_recovery_success_rate"}
    assert needed.issubset(output.summary.columns)


def test_no_locked_test_selection() -> None:
    cfg = _config(); output = run_portfolio_harness(_bundle(cfg), cfg, quick=True)
    assert output.candidate_log["selection_score"].notna().all()
    assert "locked" not in " ".join([c for c in output.candidate_log.columns if c.startswith("is_")]).lower()


def test_portfolio_harness_script_smoke(tmp_path: Path) -> None:
    cfg = _config()
    raw = make_offline_fixture_ohlcv(cfg)
    raw_path = tmp_path / "raw.csv"
    processed_path = tmp_path / "processed.csv"
    raw.to_csv(raw_path, index=False)
    cfg["raw_data_path"] = str(raw_path)
    cfg["processed_data_path"] = str(processed_path)
    cfg["allow_synthetic_fallback"] = False
    cfg_path = tmp_path / "portfolio_harness.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    run_root = tmp_path / "run"
    env = {**os.environ, "TASE_RUN_ROOT": str(run_root)}
    subprocess.run(["python", "scripts/run_portfolio_harness.py", "--config", str(cfg_path), "--quick"], check=True, timeout=120, env=env)
    assert (run_root / "outputs/portfolio_harness_summary_metrics.csv").exists()
    assert (run_root / "reports/plain_chinese_summary_portfolio_harness.md").exists()
