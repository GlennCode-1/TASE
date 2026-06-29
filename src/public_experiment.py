from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

from .features import assign_time_blocks, build_lagged_features, feature_lag_audit
from .public_data import PublicDataBundle
from .public_pbo import deflated_sharpe_ratio, summarize_pbo
from .public_task import (
    PublicHarnessConfig,
    base_public_harness,
    compute_target_weights,
    evaluate_public_config,
    future_return_independence_placebo,
    w_t_invariance_test,
)


SEARCH_ARMS = [
    "MetaHarness Unconstrained",
    "Constrained Safe Search",
    "Random Legal Patch",
    "TASE Typed Harness",
    "Lightweight Strategy Evolution",
    "SHARP-style Policy Baseline",
]
PASSIVE_ARMS = ["Equal Weight Buy Hold", "60/40 Proxy"]


@dataclass(frozen=True)
class PublicRunOutput:
    results_by_split: pd.DataFrame
    candidate_log: pd.DataFrame
    summary: pd.DataFrame


def _block_splits(n_blocks: int, validation_blocks: int, oos_blocks: int) -> list[tuple[list[int], list[int]]]:
    splits: list[tuple[list[int], list[int]]] = []
    width = int(validation_blocks) + int(oos_blocks)
    for start in range(0, int(n_blocks) - width + 1):
        is_blocks = list(range(start, start + int(validation_blocks)))
        oos = list(range(start + int(validation_blocks), start + width))
        splits.append((is_blocks, oos))
    return splits


def _safe_configs(base: PublicHarnessConfig, config: dict, budget: int) -> list[PublicHarnessConfig]:
    variants = []
    grid = product(
        ["strict", "ffill_one"],
        ["fail_closed", "retry"],
        ["normal", "verbose"],
        [0.0, 0.02],
        ["strict", "settlement_lag"],
    )
    for missing, flow, logging, floor, accounting in grid:
        variants.append(
            base.with_patch(
                {
                    "missing_policy": missing,
                    "control_flow": flow,
                    "logging": logging,
                    "risk_floor": floor,
                    "execution_accounting": accounting,
                }
            )
        )
        if len(variants) >= budget:
            break
    return variants


def _tase_configs(base: PublicHarnessConfig, config: dict, budget: int) -> list[PublicHarnessConfig]:
    candidates = _safe_configs(base, config, budget)
    extra = [
        {"data_sanitizer": "timestamp_guarded", "audit_strictness": "strict", "failed_run_retention": "keep"},
        {"cost_accounting": "strict", "logging": "verbose"},
        {"missing_policy": "strict", "control_flow": "fail_closed", "logging": "verbose"},
    ]
    for patch in extra:
        if len(candidates) >= budget:
            break
        candidates.append(base.with_patch(patch))
    return candidates[:budget]


def _unconstrained_configs(base: PublicHarnessConfig, config: dict, budget: int, seed: int) -> list[PublicHarnessConfig]:
    rng = np.random.default_rng(seed + 700)
    variants = []
    for _ in range(budget):
        variants.append(
            base.with_patch(
                {
                    "missing_policy": str(rng.choice(["strict", "drop_missing", "ffill_one"])),
                    "data_sanitizer": str(rng.choice(["timestamp_guarded", "raw"])),
                    "control_flow": str(rng.choice(["fail_closed", "retry", "skip_errors"])),
                    "cost_accounting": str(rng.choice(["strict", "loose"])),
                    "allow_future_features": bool(rng.random() < 0.20),
                    "allow_weight_change": bool(rng.random() < 0.45),
                    "top_k": int(rng.choice([2, 3, int(config["top_k"]), 6])),
                    "rebalance": str(rng.choice([str(config["rebalance"]), "D", "M"])),
                }
            )
        )
    return variants


def _random_legal_configs(base: PublicHarnessConfig, config: dict, budget: int, seed: int) -> list[PublicHarnessConfig]:
    rng = np.random.default_rng(seed + 900)
    legal = _tase_configs(base, config, max(budget * 2, budget + 1))
    picks = rng.choice(len(legal), size=budget, replace=len(legal) < budget)
    return [legal[int(idx)] for idx in picks]


def _strategy_configs(base: PublicHarnessConfig, config: dict, budget: int) -> list[PublicHarnessConfig]:
    variants = []
    for mw, penalty, top_k, threshold, rebalance in product(
        [10, 20, 60], [0.0, 0.25, 0.5], [3, 4, 6], [-999.0, 0.0], [str(config["rebalance"]), "M"]
    ):
        variants.append(
            base.with_patch(
                {
                    "allow_weight_change": True,
                    "momentum_window": int(mw),
                    "volatility_penalty": float(penalty),
                    "top_k": int(top_k),
                    "threshold": float(threshold),
                    "rebalance": str(rebalance),
                }
            )
        )
        if len(variants) >= budget:
            break
    return variants


def _policy_configs(base: PublicHarnessConfig, config: dict, budget: int) -> list[PublicHarnessConfig]:
    variants = []
    for rule, floor, flow in product(["none", "risk_off_on_high_vol"], [0.0, 0.02], ["fail_closed", "retry"]):
        variants.append(base.with_patch({"policy_risk_rule": rule, "risk_floor": floor, "control_flow": flow}))
        if len(variants) >= budget:
            break
    while len(variants) < budget:
        variants.append(variants[-1])
    return variants[:budget]


def _candidates_for_arm(arm: str, base: PublicHarnessConfig, config: dict, budget: int, seed: int) -> list[PublicHarnessConfig]:
    if arm == "MetaHarness Unconstrained":
        return _unconstrained_configs(base, config, budget, seed)
    if arm == "Constrained Safe Search":
        return _safe_configs(base, config, budget)
    if arm == "Random Legal Patch":
        return _random_legal_configs(base, config, budget, seed)
    if arm == "TASE Typed Harness":
        return _tase_configs(base, config, budget)
    if arm == "Lightweight Strategy Evolution":
        return _strategy_configs(base, config, budget)
    if arm == "SHARP-style Policy Baseline":
        return _policy_configs(base, config, budget)
    raise KeyError(arm)


def _harness_key(harness: PublicHarnessConfig) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(harness.to_dict().items()))


def _selection_objective(evaluation, harness: PublicHarnessConfig, n_trials: int) -> float:
    dsr = deflated_sharpe_ratio(evaluation.sharpe, n_trials, evaluation.n_days)
    return dsr - 0.5 * evaluation.constraint_violations - max(0.0, evaluation.turnover - 0.35)


def _passive_weights(features: pd.DataFrame, arm: str) -> pd.DataFrame:
    dates = sorted(features["date"].unique())
    tickers = sorted(features["ticker"].unique())
    rows = []
    for date in dates:
        if arm == "60/40 Proxy":
            weights = {ticker: 0.0 for ticker in tickers}
            if "SPY" in weights:
                weights["SPY"] = 0.6
            bond = "IEF" if "IEF" in weights else "TLT" if "TLT" in weights else tickers[0]
            weights[bond] = weights.get(bond, 0.0) + 0.4
        else:
            weights = {ticker: 1.0 / len(tickers) for ticker in tickers}
        rows.extend({"date": date, "ticker": ticker, "target_weight": weight} for ticker, weight in weights.items())
    return pd.DataFrame(rows)


def _evaluate_passive(features: pd.DataFrame, arm: str, config: dict, dates) -> dict:
    harness = base_public_harness(config)
    data = features[features["date"].isin(dates)].copy()
    reference = _passive_weights(data, arm)
    evaluation = evaluate_public_config(data, harness, config, allowed_dates=dates, reference_weights=reference)
    return evaluation.to_dict()


def run_public_toy(bundle: PublicDataBundle, config: dict, quick: bool = False) -> PublicRunOutput:
    cfg = dict(config)
    if quick:
        cfg["n_seeds"] = int(cfg.get("quick_n_seeds", 1))
        cfg["search_budget"] = int(cfg.get("quick_search_budget", 8))
    features = build_lagged_features(
        bundle.prices,
        int(cfg["momentum_window"]),
        int(cfg["volatility_window"]),
        float(cfg["volatility_penalty"]),
    )
    if quick:
        quick_start = pd.Timestamp(features["date"].max()) - pd.DateOffset(years=3)
        features = features[features["date"] >= quick_start].copy()
    features.attrs["used_features"] = ("momentum_20", "volatility_20", "score")
    if not feature_lag_audit(features):
        raise RuntimeError("feature lag audit failed")
    features = assign_time_blocks(features, int(cfg["selection_blocks"]), int(cfg["final_confirmation_months"]))
    cfg["effective_start_date"] = str(pd.Timestamp(features["date"].min()).date())
    cfg["effective_end_date"] = str(pd.Timestamp(features["date"].max()).date())
    base = base_public_harness(cfg)
    reference_weights = compute_target_weights(features, base, cfg)
    splits = _block_splits(int(cfg["selection_blocks"]), int(cfg["validation_window_blocks"]), int(cfg["oos_window_blocks"]))
    budget = int(cfg["search_budget"])
    candidate_rows: list[dict] = []
    result_rows: list[dict] = []
    weight_cache: dict[tuple[tuple[str, object], ...], pd.DataFrame] = {}
    eval_cache: dict[tuple[tuple[tuple[str, object], ...], tuple[int, ...]], object] = {}
    pi_cache: dict[tuple[tuple[str, object], ...], bool] = {}

    def weights_for(harness: PublicHarnessConfig) -> pd.DataFrame:
        key = _harness_key(harness)
        if key not in weight_cache:
            weight_cache[key] = compute_target_weights(features, harness, cfg)
        return weight_cache[key]

    def dates_key(dates: set[pd.Timestamp]) -> tuple[int, ...]:
        return tuple(sorted(pd.DatetimeIndex(pd.to_datetime(list(dates))).asi8.tolist()))

    def pi_pass_for(harness: PublicHarnessConfig) -> bool:
        key = _harness_key(harness)
        if key not in pi_cache:
            pi_cache[key] = w_t_invariance_test(reference_weights, weights_for(harness))
            pi_cache[key] = pi_cache[key] and future_return_independence_placebo(features, harness, cfg)
        return pi_cache[key]

    def eval_for(harness: PublicHarnessConfig, dates: set[pd.Timestamp]):
        h_key = _harness_key(harness)
        e_key = (h_key, dates_key(dates))
        if e_key not in eval_cache:
            eval_cache[e_key] = evaluate_public_config(
                features, harness, cfg, dates, reference_weights, target_weights=weights_for(harness)
            )
        return eval_cache[e_key]

    for seed in range(int(cfg["n_seeds"])):
        for split_id, (is_blocks, oos_blocks) in enumerate(splits):
            is_dates = set(features.loc[features["block"].isin(is_blocks), "date"])
            oos_dates = set(features.loc[features["block"].isin(oos_blocks), "date"])
            for arm in SEARCH_ARMS:
                candidates = _candidates_for_arm(arm, base, cfg, budget, seed)
                scored = []
                for idx, harness in enumerate(candidates):
                    candidate_weights = weights_for(harness)
                    pi_pass = True
                    if arm in {"Constrained Safe Search", "Random Legal Patch", "TASE Typed Harness"}:
                        pi_pass = pi_pass_for(harness)
                    is_eval = eval_for(harness, is_dates)
                    oos_eval = eval_for(harness, oos_dates)
                    if arm == "Random Legal Patch":
                        selection = float(idx == 0)
                    else:
                        selection = _selection_objective(is_eval, harness, budget)
                    row = {
                        "arm": arm,
                        "seed": seed,
                        "split_id": split_id,
                        "candidate_id": f"{arm}-{seed}-{idx}",
                        "selection_score": selection,
                        "is_score": is_eval.sharpe,
                        "oos_score": oos_eval.sharpe,
                        "dsr": deflated_sharpe_ratio(is_eval.sharpe, budget, is_eval.n_days),
                        "leakage_audit_pass": is_eval.leakage_violations == 0,
                        "pi_invariance_pass": pi_pass,
                        "constraint_violations": is_eval.constraint_violations + int(not pi_pass),
                        "candidate_values": harness.to_dict(),
                        **{f"is_{key}": value for key, value in is_eval.to_dict().items()},
                        **{f"oos_{key}": value for key, value in oos_eval.to_dict().items()},
                    }
                    candidate_rows.append(row)
                    scored.append(row)
                if arm == "Random Legal Patch":
                    chosen = scored[0]
                else:
                    chosen = sorted(scored, key=lambda row: row["selection_score"], reverse=True)[0]
                result_rows.append(chosen | {"chosen": True})

            for arm in PASSIVE_ARMS:
                passive = _evaluate_passive(features, arm, cfg, oos_dates)
                result_rows.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "split_id": split_id,
                        "candidate_id": f"{arm}-{seed}-{split_id}",
                        "selection_score": np.nan,
                        "is_score": np.nan,
                        "oos_score": passive["sharpe"],
                        "dsr": deflated_sharpe_ratio(passive["sharpe"], 1, passive["n_days"]),
                        "leakage_audit_pass": True,
                        "pi_invariance_pass": True,
                        "constraint_violations": 0,
                        "chosen": True,
                        **{f"oos_{key}": value for key, value in passive.items()},
                    }
                )

    candidate_log = pd.DataFrame(candidate_rows)
    results = pd.DataFrame(result_rows)
    pbo = summarize_pbo(candidate_log)
    chosen_summary = (
        results.groupby("arm", sort=False)
        .agg(
            locked_sharpe=("oos_sharpe", "mean"),
            locked_cumulative_return=("oos_cumulative_return", "mean"),
            locked_max_drawdown=("oos_max_drawdown", "mean"),
            turnover=("oos_turnover", "mean"),
            leakage_audit_pass_rate=("leakage_audit_pass", "mean"),
            pi_invariance_pass_rate=("pi_invariance_pass", "mean"),
            constraint_violation_count=("constraint_violations", "mean"),
        )
        .reset_index()
    )
    summary = chosen_summary.merge(pbo, on="arm", how="left")
    summary["true_candidate_count"] = summary["true_candidate_count"].fillna(1).astype(int)
    summary["pbo_estimate"] = summary["pbo_estimate"].fillna(0.0)
    summary["is_oos_rank_correlation"] = summary["is_oos_rank_correlation"].fillna(0.0)
    summary["validation_to_oos_degradation"] = summary["validation_to_oos_degradation"].fillna(0.0)
    summary["deflated_sharpe_ratio"] = summary["deflated_sharpe_ratio"].fillna(summary["locked_sharpe"])
    summary["spa_like_pvalue"] = summary["spa_like_pvalue"].fillna(1.0)
    summary.attrs["effective_start_date"] = cfg["effective_start_date"]
    summary.attrs["effective_end_date"] = cfg["effective_end_date"]
    summary.attrs["run_mode"] = "quick" if quick else "full"
    return PublicRunOutput(results_by_split=results, candidate_log=candidate_log, summary=summary)
