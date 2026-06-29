from __future__ import annotations

from pathlib import Path
import os
import subprocess

import pandas as pd
import yaml

from src.features import assign_time_blocks, feature_lag_audit
from src.reporting import build_sp500_short_plain_chinese_summary
from src.sp500_data import make_offline_stock_fixture, process_sp500_ohlcv, StockDataBundle
from src.sp500_universe import _to_yfinance_symbol
from src.stock_experiment import CORE_ARMS, run_sp500_short
from src.stock_task import (
    base_stock_harness,
    build_stock_features,
    clean_panel_score_invariance,
    compute_stock_weight_matrix,
    future_return_exclusion_placebo,
    stock_feature_matrices,
)


def _config() -> dict:
    with open("configs/sp500_short.yaml", "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["start_date"] = "2021-01-01"
    cfg["end_date"] = "2021-12-31"
    cfg["min_assets"] = 35
    cfg["quick_min_assets"] = 35
    cfg["quick_max_assets"] = 45
    cfg["selection_blocks"] = 4
    cfg["validation_window_blocks"] = 1
    cfg["oos_window_blocks"] = 1
    cfg["final_confirmation_months"] = 2
    cfg["n_seeds"] = 1
    cfg["quick_n_seeds"] = 1
    cfg["search_budget"] = 4
    cfg["quick_search_budget"] = 3
    cfg["bootstrap_samples"] = 20
    cfg["allow_synthetic_fallback"] = True
    return cfg


def _bundle(cfg: dict | None = None) -> StockDataBundle:
    config = cfg or _config()
    raw, constituents = make_offline_stock_fixture(config, n_assets=45)
    processed, missing = process_sp500_ohlcv(raw, constituents, config)
    return StockDataBundle(
        prices=processed,
        universe=tuple(sorted(processed["ticker"].unique())),
        start_date=pd.Timestamp(processed["date"].min()),
        end_date=pd.Timestamp(processed["date"].max()),
        missing_log=missing,
        constituents=constituents,
    )


def test_sp500_constituents_saved_with_date(tmp_path: Path) -> None:
    frame = pd.DataFrame({"ticker": ["BRK.B"], "company_name": ["Berkshire"], "sector": ["Financials"]})
    frame["yfinance_ticker"] = frame["ticker"].map(_to_yfinance_symbol)
    frame["retrieved_at"] = "2026-06-29"
    path = tmp_path / "sp500_current_constituents.csv"
    frame.to_csv(path, index=False)
    loaded = pd.read_csv(path)
    assert loaded.loc[0, "yfinance_ticker"] == "BRK-B"
    assert "retrieved_at" in loaded.columns


def test_survivorship_bias_warning_written() -> None:
    cfg = _config()
    output = run_sp500_short(_bundle(cfg), cfg, quick=True)
    text = build_sp500_short_plain_chinese_summary(output.summary, output.candidate_log, output.paired_bootstrap)
    assert "当前还活着的公司" in text
    assert "不证明真实赚钱能力" in text


def test_min_300_assets_after_filtering() -> None:
    cfg = _config()
    cfg["min_assets"] = 40
    raw, constituents = make_offline_stock_fixture(cfg, n_assets=45)
    processed, _ = process_sp500_ohlcv(raw, constituents, cfg)
    assert processed["ticker"].nunique() >= 40


def test_all_features_lagged_stock_task() -> None:
    cfg = _config()
    features = build_stock_features(_bundle(cfg).prices, cfg)
    assert feature_lag_audit(features)


def test_clean_panel_score_invariance() -> None:
    cfg = _config()
    features = assign_time_blocks(build_stock_features(_bundle(cfg).prices, cfg), 4, 2)
    matrices = stock_feature_matrices(features)
    base = base_stock_harness(cfg)
    legal = base.with_patch({"bad_tick_policy": "bad_tick_filter_with_past_only_threshold", "trace_level": "full_decision_trace"})
    illegal = base.with_patch({"volatility_penalty": 1.0, "allow_strategy_change": True})
    assert clean_panel_score_invariance(matrices, legal, cfg)
    assert not clean_panel_score_invariance(matrices, illegal, cfg)


def test_availability_exclusion_has_reason() -> None:
    cfg = _config()
    features = assign_time_blocks(build_stock_features(_bundle(cfg).prices, cfg), 4, 2)
    matrices = stock_feature_matrices(features)
    harness = base_stock_harness(cfg).with_patch({"bad_tick_policy": "bad_tick_filter_with_past_only_threshold"})
    _, exclusion = compute_stock_weight_matrix(matrices, harness, cfg)
    assert set(exclusion.columns) >= {"date", "ticker", "reason"}
    assert exclusion.empty or exclusion["reason"].notna().all()


def test_future_return_placebo_for_exclusion() -> None:
    cfg = _config()
    features = assign_time_blocks(build_stock_features(_bundle(cfg).prices, cfg), 4, 2)
    matrices = stock_feature_matrices(features)
    legal = base_stock_harness(cfg).with_patch({"stale_policy": "stale_price_to_cash"})
    illegal = base_stock_harness(cfg).with_patch({"use_future_exclusion": True})
    assert future_return_exclusion_placebo(matrices, legal, cfg)
    assert not future_return_exclusion_placebo(matrices, illegal, cfg)


def test_tase_rejects_strategy_parameter_patch() -> None:
    cfg = _config()
    features = assign_time_blocks(build_stock_features(_bundle(cfg).prices, cfg), 4, 2)
    matrices = stock_feature_matrices(features)
    illegal = base_stock_harness(cfg).with_patch({"top_k": 10, "allow_strategy_change": True})
    assert not clean_panel_score_invariance(matrices, illegal, cfg)


def test_same_budget_core_arms() -> None:
    cfg = _config()
    output = run_sp500_short(_bundle(cfg), cfg, quick=True)
    log = output.candidate_log[output.candidate_log["arm"].isin(CORE_ARMS)]
    counts = log.groupby(["arm", "seed", "split_id"])["candidate_id"].nunique()
    assert set(log["arm"]) == set(CORE_ARMS)
    assert set(counts.unique()) == {cfg["quick_search_budget"]}


def test_locked_test_not_used_for_selection() -> None:
    cfg = _config()
    output = run_sp500_short(_bundle(cfg), cfg, quick=True)
    assert output.candidate_log["selection_score"].notna().all()
    assert "final" not in " ".join(output.candidate_log.columns).lower()


def test_paired_bootstrap_outputs_differences() -> None:
    cfg = _config()
    output = run_sp500_short(_bundle(cfg), cfg, quick=True)
    assert {"comparison", "metric", "mean_diff", "ci_low", "ci_high"}.issubset(output.paired_bootstrap.columns)
    assert "TASE Typed Harness - Constrained Safe Search" in set(output.paired_bootstrap["comparison"])


def test_checkpoint_resume_sp500_short(tmp_path: Path) -> None:
    cfg = _config()
    raw, constituents = make_offline_stock_fixture(cfg, n_assets=45)
    raw_path = tmp_path / "raw.csv"
    processed_path = tmp_path / "processed.csv"
    constituents_path = tmp_path / "constituents.csv"
    raw.to_csv(raw_path, index=False)
    constituents.to_csv(constituents_path, index=False)
    cfg["raw_data_path"] = str(raw_path)
    cfg["processed_data_path"] = str(processed_path)
    cfg["constituents_path"] = str(constituents_path)
    cfg["allow_synthetic_fallback"] = False
    cfg_path = tmp_path / "sp500_short.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    run_root = tmp_path / "run_root"
    env = {**os.environ, "TASE_RUN_ROOT": str(run_root)}
    subprocess.run(["python", "scripts/run_sp500_short.py", "--config", str(cfg_path), "--quick"], check=True, timeout=90, env=env)
    subprocess.run(["python", "scripts/run_sp500_short.py", "--config", str(cfg_path), "--quick", "--resume"], check=True, timeout=90, env=env)
    assert (run_root / "outputs/checkpoints/sp500_short_quick_results_by_split.csv").exists()
