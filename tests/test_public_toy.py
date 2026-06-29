from __future__ import annotations

import pandas as pd
import yaml

from src.features import assign_time_blocks, build_lagged_features, feature_lag_audit
from src.public_data import PublicDataBundle, make_offline_fixture_ohlcv, process_public_ohlcv
from src.public_experiment import SEARCH_ARMS, run_public_toy
from src.public_pbo import deflated_sharpe_ratio, summarize_pbo
from src.public_task import (
    base_public_harness,
    compute_target_weights,
    future_return_independence_placebo,
    w_t_invariance_test,
)


def _config() -> dict:
    with open("configs/public_toy.yaml", "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["universe"] = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "VNQ", "XLF"]
    config["start_date"] = "2020-01-01"
    config["end_date"] = "2020-12-31"
    config["min_assets"] = 10
    config["allow_synthetic_fallback"] = True
    config["selection_blocks"] = 4
    config["validation_window_blocks"] = 1
    config["oos_window_blocks"] = 1
    config["final_confirmation_months"] = 2
    config["n_seeds"] = 1
    config["quick_n_seeds"] = 1
    config["search_budget"] = 4
    config["quick_search_budget"] = 2
    config["candidate_per_round"] = 2
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


def _features(config: dict | None = None) -> pd.DataFrame:
    cfg = config or _config()
    return build_lagged_features(
        _bundle(cfg).prices,
        cfg["momentum_window"],
        cfg["volatility_window"],
        cfg["volatility_penalty"],
    )


_CACHED_OUTPUT = None


def _quick_output():
    global _CACHED_OUTPUT
    if _CACHED_OUTPUT is None:
        cfg = _config()
        _CACHED_OUTPUT = (cfg, run_public_toy(_bundle(cfg), cfg, quick=True))
    return _CACHED_OUTPUT


def test_public_data_no_future_features() -> None:
    features = _features()
    assert feature_lag_audit(features)
    assert "future_return_1d" in features.columns
    assert "future_return_1d" not in features.attrs.get("used_features", ("momentum_20", "volatility_20", "score"))


def test_train_val_test_time_order() -> None:
    cfg = _config()
    blocked = assign_time_blocks(_features(cfg), cfg["selection_blocks"], cfg["final_confirmation_months"])
    for block in range(cfg["selection_blocks"] - 1):
        left = blocked[blocked["block"] == block]["date"].max()
        right = blocked[blocked["block"] == block + 1]["date"].min()
        assert left < right
    assert blocked[blocked["is_final_confirmation"]]["date"].min() > blocked[~blocked["is_final_confirmation"]]["date"].max()


def test_feature_lag_audit() -> None:
    features = _features()
    features.attrs["used_features"] = ("momentum_20", "volatility_20", "score")
    assert feature_lag_audit(features)
    features.attrs["used_features"] = ("momentum_20", "future_return_1d")
    assert not feature_lag_audit(features)


def test_w_t_invariance_gate_rejects_strategy_change() -> None:
    cfg = _config()
    features = _features(cfg)
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    changed = compute_target_weights(features, base.with_patch({"top_k": 2, "allow_weight_change": True}), cfg)
    assert not w_t_invariance_test(reference, changed)


def test_rebalance_frequency_not_allowed_in_tase_patch() -> None:
    cfg = _config()
    features = _features(cfg)
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    changed = compute_target_weights(features, base.with_patch({"rebalance": "M", "allow_weight_change": True}), cfg)
    assert not w_t_invariance_test(reference, changed)


def test_volatility_targeting_not_allowed_in_tase_patch() -> None:
    cfg = _config()
    features = _features(cfg)
    base = base_public_harness(cfg)
    reference = compute_target_weights(features, base, cfg)
    changed = compute_target_weights(features, base.with_patch({"volatility_penalty": 0.9, "allow_weight_change": True}), cfg)
    assert not w_t_invariance_test(reference, changed)


def test_same_budget_for_search_arms() -> None:
    cfg, output = _quick_output()
    log = output.candidate_log
    counts = log.groupby(["arm", "seed", "split_id"])["candidate_id"].nunique()
    assert set(log["arm"]) == set(SEARCH_ARMS)
    assert set(counts.unique()) == {cfg["quick_search_budget"]}


def test_dsr_uses_true_candidate_count() -> None:
    rows = pd.DataFrame(
        {
            "arm": ["A", "A", "A"],
            "split_id": [0, 0, 0],
            "candidate_id": ["a", "b", "c"],
            "is_score": [1.0, 0.5, 0.2],
            "oos_score": [0.1, 0.4, 0.3],
            "dsr": [deflated_sharpe_ratio(1.0, 3, 40), 0.0, 0.0],
        }
    )
    summary = summarize_pbo(rows)
    assert int(summary.iloc[0]["true_candidate_count"]) == 3


def test_pbo_runs_on_multiple_splits() -> None:
    _, output = _quick_output()
    assert output.candidate_log["split_id"].nunique() >= 2
    assert "pbo_estimate" in output.summary.columns


def test_locked_test_not_used_for_selection() -> None:
    _, output = _quick_output()
    assert output.candidate_log["selection_score"].notna().all()
    assert "final" not in " ".join(output.candidate_log.columns).lower()


def test_future_return_independence_placebo_rejects_future_use() -> None:
    cfg = _config()
    features = _features(cfg)
    base = base_public_harness(cfg)
    assert future_return_independence_placebo(features, base, cfg)
    assert not future_return_independence_placebo(features, base.with_patch({"allow_future_features": True}), cfg)
