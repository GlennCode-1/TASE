from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

from .features import assign_time_blocks
from .sp500_data import StockDataBundle
from .stock_task import (
    StockHarnessConfig,
    base_stock_harness,
    build_stock_features,
    clean_panel_score_invariance,
    compute_stock_weight_matrix,
    evaluate_stock_weight_matrix,
    future_return_exclusion_placebo,
    stock_feature_matrices,
)

CORE_ARMS = ["Unconstrained Search", "Constrained Safe Search", "Random Legal Patch", "TASE Typed Harness"]
OPTIONAL_ARMS = ["Lightweight Strategy Tuning"]


@dataclass(frozen=True)
class StockRunOutput:
    results_by_split: pd.DataFrame
    candidate_log: pd.DataFrame
    summary: pd.DataFrame
    paired_bootstrap: pd.DataFrame
    exclusion_log: pd.DataFrame


def block_splits(n_blocks: int, validation_blocks: int, oos_blocks: int) -> list[tuple[list[int], list[int]]]:
    width = int(validation_blocks) + int(oos_blocks)
    return [
        (list(range(start, start + int(validation_blocks))), list(range(start + int(validation_blocks), start + width)))
        for start in range(0, int(n_blocks) - width + 1)
    ]


def _safe_configs(base: StockHarnessConfig, budget: int) -> list[StockHarnessConfig]:
    variants = []
    grid = product(
        ["strict_fail_closed", "past_only_safe_impute", "asset_cash_if_missing", "asset_exclude_if_missing_ratio_high"],
        ["none", "stale_price_to_cash"],
        ["none", "bad_tick_filter_with_past_only_threshold"],
        ["none", "corporate_action_sanity_check"],
        ["fail_closed", "retry_then_fail_closed", "retain_failed_day_as_cash"],
        ["strict_cost_accounting", "conservative_cost_accounting"],
        ["normal", "full_decision_trace"],
        [0.0, 0.02],
    )
    for missing, stale, bad, corporate, failed, cost, trace, buffer in grid:
        variants.append(
            base.with_patch(
                {
                    "missing_policy": missing,
                    "stale_policy": stale,
                    "bad_tick_policy": bad,
                    "corporate_action_policy": corporate,
                    "failed_day_policy": failed,
                    "cost_accounting": cost,
                    "trace_level": trace,
                    "cash_buffer": buffer,
                }
            )
        )
        if len(variants) >= budget:
            break
    return variants


def _tase_configs(base: StockHarnessConfig, budget: int) -> list[StockHarnessConfig]:
    candidates = _safe_configs(base, budget)
    preferred = [
        {"missing_policy": "asset_cash_if_missing", "stale_policy": "stale_price_to_cash", "trace_level": "full_decision_trace"},
        {"bad_tick_policy": "bad_tick_filter_with_past_only_threshold", "corporate_action_policy": "corporate_action_sanity_check"},
        {"failed_day_policy": "retain_failed_day_as_cash", "cash_buffer": 0.02},
    ]
    for patch in preferred:
        if len(candidates) >= budget:
            break
        candidates.append(base.with_patch(patch))
    return candidates[:budget]


def _random_legal_configs(base: StockHarnessConfig, budget: int, seed: int) -> list[StockHarnessConfig]:
    rng = np.random.default_rng(seed + 202)
    legal = _tase_configs(base, max(budget * 2, budget + 1))
    picks = rng.choice(len(legal), size=budget, replace=len(legal) < budget)
    return [legal[int(idx)] for idx in picks]


def _unconstrained_configs(base: StockHarnessConfig, config: dict, budget: int, seed: int) -> list[StockHarnessConfig]:
    rng = np.random.default_rng(seed + 404)
    variants = []
    for _ in range(budget):
        variants.append(
            base.with_patch(
                {
                    "missing_policy": str(rng.choice(["strict_fail_closed", "drop_failed_assets", "asset_cash_if_missing"])),
                    "stale_policy": str(rng.choice(["none", "stale_price_to_cash"])),
                    "bad_tick_policy": str(rng.choice(["none", "bad_tick_filter_with_past_only_threshold"])),
                    "corporate_action_policy": str(rng.choice(["none", "corporate_action_sanity_check"])),
                    "allow_future_features": bool(rng.random() < 0.25),
                    "allow_strategy_change": bool(rng.random() < 0.35),
                    "use_future_exclusion": bool(rng.random() < 0.20),
                    "cost_accounting": str(rng.choice(["strict_cost_accounting", "loose_cost_accounting"])),
                    "top_k": int(rng.choice([10, int(config["top_k"]), 50])),
                    "rebalance": str(rng.choice([str(config["rebalance"]), "D", "M"])),
                    "volatility_penalty": float(rng.choice([0.0, float(config["volatility_penalty"]), 1.0])),
                }
            )
        )
    return variants


def _strategy_configs(base: StockHarnessConfig, config: dict, budget: int) -> list[StockHarnessConfig]:
    variants = []
    for top_k, mw, penalty, rebalance in product([20, 30, 50], [10, 20, 60], [0.0, 0.5, 1.0], [str(config["rebalance"]), "M"]):
        variants.append(
            base.with_patch(
                {
                    "allow_strategy_change": True,
                    "top_k": int(top_k),
                    "momentum_window": int(mw),
                    "volatility_penalty": float(penalty),
                    "rebalance": str(rebalance),
                }
            )
        )
        if len(variants) >= budget:
            break
    return variants


def candidates_for_arm(arm: str, base: StockHarnessConfig, config: dict, budget: int, seed: int) -> list[StockHarnessConfig]:
    if arm == "Unconstrained Search":
        return _unconstrained_configs(base, config, budget, seed)
    if arm == "Constrained Safe Search":
        return _safe_configs(base, budget)
    if arm == "Random Legal Patch":
        return _random_legal_configs(base, budget, seed)
    if arm == "TASE Typed Harness":
        return _tase_configs(base, budget)
    if arm == "Lightweight Strategy Tuning":
        return _strategy_configs(base, config, budget)
    raise KeyError(arm)


def _harness_key(harness: StockHarnessConfig) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(harness.to_dict().items()))


def _objective(eval_obj, valid: bool) -> float:
    if not valid:
        return -1e9
    return float(eval_obj.sharpe - 0.25 * eval_obj.constraint_violations - max(0.0, eval_obj.turnover - 0.50))


def paired_block_bootstrap(results: pd.DataFrame, block_size: int = 5, n_bootstrap: int = 200, seed: int = 20260629) -> pd.DataFrame:
    rows: list[dict] = []
    rng = np.random.default_rng(seed)
    keys = ["seed", "split_id"]
    for left, right in [("TASE Typed Harness", "Constrained Safe Search"), ("TASE Typed Harness", "Random Legal Patch")]:
        l = results[results["arm"] == left][keys + ["oos_sharpe", "oos_cumulative_return"]]
        r = results[results["arm"] == right][keys + ["oos_sharpe", "oos_cumulative_return"]]
        merged = l.merge(r, on=keys, suffixes=("_left", "_right"))
        if merged.empty:
            continue
        for metric in ["oos_sharpe", "oos_cumulative_return"]:
            diff = (merged[f"{metric}_left"] - merged[f"{metric}_right"]).to_numpy(dtype=float)
            means = []
            for _ in range(int(n_bootstrap)):
                sample = []
                while len(sample) < len(diff):
                    start = int(rng.integers(0, len(diff)))
                    for offset in range(int(block_size)):
                        sample.append(diff[(start + offset) % len(diff)])
                        if len(sample) >= len(diff):
                            break
                means.append(float(np.mean(sample)))
            rows.append(
                {
                    "comparison": f"{left} - {right}",
                    "metric": metric,
                    "mean_diff": float(diff.mean()),
                    "ci_low": float(np.quantile(means, 0.025)),
                    "ci_high": float(np.quantile(means, 0.975)),
                    "n_pairs": int(len(diff)),
                    "block_size": int(block_size),
                }
            )
    return pd.DataFrame(rows)


def run_sp500_short(bundle: StockDataBundle, config: dict, quick: bool = False) -> StockRunOutput:
    cfg = dict(config)
    if quick:
        cfg["n_seeds"] = int(cfg.get("quick_n_seeds", 1))
        cfg["search_budget"] = int(cfg.get("quick_search_budget", 8))
    features = build_stock_features(bundle.prices, cfg)
    features = assign_time_blocks(features, int(cfg["selection_blocks"]), int(cfg["final_confirmation_months"]))
    cfg["effective_start_date"] = str(pd.Timestamp(features["date"].min()).date())
    cfg["effective_end_date"] = str(pd.Timestamp(features["date"].max()).date())
    matrices = stock_feature_matrices(features)
    returns = np.asarray(matrices["return_1d"], dtype=float)
    dates = pd.DatetimeIndex(matrices["dates"])
    blocks = np.asarray(matrices["block"])
    base = base_stock_harness(cfg)
    splits = block_splits(int(cfg["selection_blocks"]), int(cfg["validation_window_blocks"]), int(cfg["oos_window_blocks"]))
    budget = int(cfg["search_budget"])
    arms = CORE_ARMS + (["Lightweight Strategy Tuning"] if bool(cfg.get("include_strategy_baseline", True)) else [])
    weight_cache: dict[tuple[tuple[str, object], ...], tuple[np.ndarray, pd.DataFrame]] = {}
    audit_cache: dict[tuple[tuple[str, object], ...], tuple[bool, bool]] = {}
    eval_cache = {}
    candidate_rows: list[dict] = []
    result_rows: list[dict] = []
    exclusion_frames: list[pd.DataFrame] = []

    def weights_for(harness: StockHarnessConfig) -> tuple[np.ndarray, pd.DataFrame]:
        key = _harness_key(harness)
        if key not in weight_cache:
            weight_cache[key] = compute_stock_weight_matrix(matrices, harness, cfg)
        return weight_cache[key]

    def audits_for(harness: StockHarnessConfig) -> tuple[bool, bool]:
        key = _harness_key(harness)
        if key not in audit_cache:
            audit_cache[key] = (
                clean_panel_score_invariance(matrices, harness, cfg),
                future_return_exclusion_placebo(matrices, harness, cfg),
            )
        return audit_cache[key]

    def eval_for(harness: StockHarnessConfig, block_ids: list[int]):
        key = (_harness_key(harness), tuple(block_ids))
        if key not in eval_cache:
            mask = np.isin(blocks, block_ids)
            weights, _ = weights_for(harness)
            strategy_pass, availability_pass = audits_for(harness)
            eval_cache[key] = evaluate_stock_weight_matrix(returns, weights, mask, harness, cfg, strategy_pass, availability_pass)
        return eval_cache[key]

    for seed in range(int(cfg["n_seeds"])):
        for split_id, (is_blocks, oos_blocks) in enumerate(splits):
            for arm in arms:
                candidates = candidates_for_arm(arm, base, cfg, budget, seed)
                scored = []
                for idx, harness in enumerate(candidates):
                    is_eval = eval_for(harness, is_blocks)
                    oos_eval = eval_for(harness, oos_blocks)
                    strategy_pass, availability_pass = audits_for(harness)
                    leakage_pass = is_eval.leakage_violations == 0
                    hard_gate_pass = bool(leakage_pass and strategy_pass and availability_pass)
                    if arm == "Unconstrained Search":
                        selectable = hard_gate_pass
                    elif arm == "Lightweight Strategy Tuning":
                        selectable = leakage_pass and availability_pass
                    else:
                        selectable = hard_gate_pass
                    selection = _objective(is_eval, selectable)
                    if arm == "Random Legal Patch":
                        selection = float(idx == 0) if selectable else -1e9
                    weights, exclusion = weights_for(harness)
                    if not exclusion.empty:
                        sample = exclusion.head(200).copy()
                        sample["arm"] = arm
                        sample["seed"] = seed
                        sample["split_id"] = split_id
                        sample["candidate_id"] = f"{arm}-{seed}-{idx}"
                        exclusion_frames.append(sample)
                    row = {
                        "arm": arm,
                        "seed": seed,
                        "split_id": split_id,
                        "candidate_id": f"{arm}-{seed}-{idx}",
                        "selection_score": selection,
                        "is_score": is_eval.sharpe,
                        "oos_score": oos_eval.sharpe,
                        "valid_for_selection": selectable,
                        "leakage_audit_pass": leakage_pass,
                        "strategy_boundary_pass": strategy_pass,
                        "availability_audit_pass": availability_pass,
                        "constraint_violations": is_eval.constraint_violations,
                        "candidate_values": harness.to_dict(),
                        **{f"is_{key}": value for key, value in is_eval.to_dict().items()},
                        **{f"oos_{key}": value for key, value in oos_eval.to_dict().items()},
                    }
                    candidate_rows.append(row)
                    scored.append(row)
                valid_scored = [row for row in scored if row["valid_for_selection"]]
                if valid_scored:
                    chosen = sorted(valid_scored, key=lambda row: row["selection_score"], reverse=True)[0]
                else:
                    chosen = sorted(scored, key=lambda row: row["selection_score"], reverse=True)[0]
                result_rows.append(chosen | {"chosen": True})
    candidate_log = pd.DataFrame(candidate_rows)
    results = pd.DataFrame(result_rows)
    chosen_summary = (
        results.groupby("arm", sort=False)
        .agg(
            locked_sharpe=("oos_sharpe", "mean"),
            locked_cumulative_return=("oos_cumulative_return", "mean"),
            locked_max_drawdown=("oos_max_drawdown", "mean"),
            validation_to_locked_degradation=("is_score", lambda s: float(s.mean())),
            turnover=("oos_turnover", "mean"),
            hit_rate=("oos_hit_rate", "mean"),
            active_asset_count=("oos_active_asset_count", "mean"),
            cash_ratio=("oos_cash_ratio", "mean"),
            leakage_violation_count=("is_leakage_violations", "mean"),
            strategy_boundary_violation_count=("is_strategy_boundary_violations", "mean"),
            availability_audit_pass_rate=("availability_audit_pass", "mean"),
            constraint_violation_count=("constraint_violations", "mean"),
            valid_selection_rate=("valid_for_selection", "mean"),
        )
        .reset_index()
    )
    locked_mean = results.groupby("arm")["oos_score"].mean().to_dict()
    chosen_summary["validation_to_locked_degradation"] = chosen_summary.apply(
        lambda row: float(row["validation_to_locked_degradation"] - locked_mean.get(row["arm"], 0.0)), axis=1
    )
    true_counts = candidate_log.groupby("arm")["candidate_id"].nunique().rename("true_candidate_count")
    valid_counts = candidate_log[candidate_log["valid_for_selection"]].groupby("arm")["candidate_id"].nunique().rename("valid_candidate_count")
    summary = chosen_summary.merge(true_counts, on="arm", how="left").merge(valid_counts, on="arm", how="left")
    summary["valid_candidate_count"] = summary["valid_candidate_count"].fillna(0).astype(int)
    summary.attrs["effective_start_date"] = cfg["effective_start_date"]
    summary.attrs["effective_end_date"] = cfg["effective_end_date"]
    summary.attrs["run_mode"] = "quick" if quick else "full"
    paired = paired_block_bootstrap(
        results,
        int(cfg.get("bootstrap_block_size", 5)),
        int(cfg.get("bootstrap_samples", 200)),
    )
    exclusion_log = pd.concat(exclusion_frames, ignore_index=True) if exclusion_frames else pd.DataFrame(columns=["date", "ticker", "reason"])
    return StockRunOutput(results, candidate_log, summary, paired, exclusion_log)
