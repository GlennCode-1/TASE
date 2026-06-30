from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .features import assign_time_blocks
from .public_data import PublicDataBundle
from .portfolio_harness_gates import clean_panel_w_star_invariance, legal_harness_gate, policy_specification_frozen
from .portfolio_harness_patches import (
    PortfolioHarnessConfig,
    base_portfolio_harness,
    fixed_safe_harness,
    random_legal_space,
    safe_config_space,
    strategy_tuning_space,
    tase_config_space,
    unconstrained_space,
)
from .portfolio_metrics import PortfolioEvaluation, evaluate_portfolio_weights
from .portfolio_optimizer import compute_portfolio_weight_matrix
from .portfolio_task import build_portfolio_features, portfolio_feature_matrices

SEARCH_ARMS = [
    "Fixed Safe Portfolio Harness",
    "Same-Budget Safe Configuration Search",
    "Random Legal Harness Patch",
    "TASE Typed Portfolio Harness Reconstruction",
    "Unconstrained Portfolio Harness Search",
    "Portfolio Strategy Tuning Baseline",
]
PASSIVE_ARMS = ["Equal Weight ETF Portfolio", "Risk Parity Fixed Portfolio", "60/40 Portfolio"]
LEGAL_COMPARISON_ARMS = [
    "Fixed Safe Portfolio Harness",
    "Same-Budget Safe Configuration Search",
    "Random Legal Harness Patch",
    "TASE Typed Portfolio Harness Reconstruction",
]


@dataclass(frozen=True)
class PortfolioRunOutput:
    results_by_split: pd.DataFrame
    candidate_log: pd.DataFrame
    summary: pd.DataFrame
    invalid_high_score_log: pd.DataFrame
    paired_bootstrap: pd.DataFrame


def _block_splits(n_blocks: int, validation_blocks: int, oos_blocks: int) -> list[tuple[list[int], list[int]]]:
    width = int(validation_blocks) + int(oos_blocks)
    return [
        (list(range(start, start + int(validation_blocks))), list(range(start + int(validation_blocks), start + width)))
        for start in range(0, int(n_blocks) - width + 1)
    ]


def _harness_key(harness: PortfolioHarnessConfig) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(harness.to_dict().items()))


def _candidates_for_arm(arm: str, base: PortfolioHarnessConfig, config: dict, budget: int, seed: int) -> list[PortfolioHarnessConfig]:
    if arm == "Fixed Safe Portfolio Harness":
        return [fixed_safe_harness(base)]
    if arm == "Same-Budget Safe Configuration Search":
        return safe_config_space(base, budget)
    if arm == "Random Legal Harness Patch":
        return random_legal_space(base, budget, seed)
    if arm == "TASE Typed Portfolio Harness Reconstruction":
        return tase_config_space(base, budget)
    if arm == "Unconstrained Portfolio Harness Search":
        return unconstrained_space(base, config, budget, seed)
    if arm == "Portfolio Strategy Tuning Baseline":
        return strategy_tuning_space(base, config, budget)
    raise KeyError(arm)




def _empty_eval() -> PortfolioEvaluation:
    return PortfolioEvaluation(
        cumulative_return=0.0, annualized_return=0.0, sharpe=0.0, sortino=0.0, calmar=0.0,
        max_drawdown=0.0, drawdown_duration=0.0, cvar_95=0.0, downside_deviation=0.0,
        realized_volatility=0.0, turnover=0.0, transaction_cost_paid=0.0, turnover_adjusted_net_return=0.0,
        constraint_violation_severity=0.0, infeasible_optimization_events=0, optimizer_recovery_success_rate=0.0,
        failed_rebalance_retention_rate=0.0, cash_ratio_due_to_infeasibility=0.0, exposure_drift=0.0,
        herfindahl_index=0.0, diversification_ratio=0.0, asset_class_cap_violation_severity=0.0,
        high_vol_return=0.0, normal_vol_return=0.0, stress_recovery_return=0.0, n_days=0,
    )


def _invalid_candidate_score(gate_reason: str) -> float:
    reason = str(gate_reason)
    return float(
        1.0
        + 2.0 * int("POLICY_SPECIFICATION_CHANGED" in reason)
        + 2.0 * int("FUTURE_RETURN_LEAKAGE" in reason)
        + 1.0 * int("CLEAN_PANEL_W_STAR_CHANGED" in reason)
        + 0.5 * int("LOOSE_COST_ACCOUNTING" in reason)
    )

def _selection_objective(eval_obj, valid: bool) -> float:
    score = (
        -2.0 * float(eval_obj.cvar_95)
        -1.0 * abs(float(eval_obj.max_drawdown))
        -0.25 * float(eval_obj.drawdown_duration) / max(1.0, float(eval_obj.n_days))
        -0.60 * float(eval_obj.turnover)
        -1.50 * float(eval_obj.constraint_violation_severity)
        +0.30 * float(eval_obj.optimizer_recovery_success_rate)
        +0.15 * float(eval_obj.turnover_adjusted_net_return)
    )
    return score if valid else -1e9


def _passive_weights(matrices: dict[str, object], arm: str, config: dict) -> np.ndarray:
    returns = np.asarray(matrices["return_1d"], dtype=float)
    n_dates, n_assets = returns.shape
    weights = np.zeros((n_dates, n_assets), dtype=float)
    tickers = list(matrices["tickers"])
    if arm == "60/40 Portfolio":
        equity = tickers.index("SPY") if "SPY" in tickers else 0
        bond = tickers.index("IEF") if "IEF" in tickers else tickers.index("TLT") if "TLT" in tickers else min(1, n_assets - 1)
        weights[:, equity] = 0.6
        weights[:, bond] += 0.4
    elif arm == "Risk Parity Fixed Portfolio":
        vol = np.nanstd(returns, axis=0)
        inv = 1.0 / np.maximum(vol, 1e-6)
        weights[:, :] = inv / inv.sum() * (1.0 - float(config["min_cash_buffer"]))
    else:
        weights[:, :] = (1.0 - float(config["min_cash_buffer"])) / n_assets
    return weights


def paired_block_bootstrap(results: pd.DataFrame, block_size: int = 5, n_bootstrap: int = 200, seed: int = 20260629) -> pd.DataFrame:
    rows: list[dict] = []
    rng = np.random.default_rng(seed)
    comparisons = [
        ("TASE Typed Portfolio Harness Reconstruction", "Fixed Safe Portfolio Harness"),
        ("TASE Typed Portfolio Harness Reconstruction", "Same-Budget Safe Configuration Search"),
        ("TASE Typed Portfolio Harness Reconstruction", "Random Legal Harness Patch"),
        ("TASE Typed Portfolio Harness Reconstruction", "Risk Parity Fixed Portfolio"),
        ("TASE Typed Portfolio Harness Reconstruction", "Equal Weight ETF Portfolio"),
    ]
    metrics = [
        "oos_cvar_95",
        "oos_drawdown_duration",
        "oos_turnover",
        "oos_transaction_cost_paid",
        "oos_constraint_violation_severity",
        "oos_optimizer_recovery_success_rate",
        "oos_turnover_adjusted_net_return",
        "oos_cumulative_return",
        "oos_sharpe",
    ]
    metric_names = {
        "oos_cvar_95": "cvar_95",
        "oos_drawdown_duration": "drawdown_duration",
        "oos_turnover": "turnover",
        "oos_transaction_cost_paid": "transaction_cost_paid",
        "oos_constraint_violation_severity": "constraint_violation_severity",
        "oos_optimizer_recovery_success_rate": "optimizer_recovery_success_rate",
        "oos_turnover_adjusted_net_return": "turnover_adjusted_net_return",
        "oos_cumulative_return": "locked_cumulative_return",
        "oos_sharpe": "locked_sharpe",
    }
    keys = ["seed", "split_id"]
    for left, right in comparisons:
        l = results[results["arm"] == left][keys + metrics]
        r = results[results["arm"] == right][keys + metrics]
        merged = l.merge(r, on=keys, suffixes=("_left", "_right"))
        if merged.empty:
            continue
        for metric in metrics:
            pair = merged.dropna(subset=[f"{metric}_left", f"{metric}_right"])
            if pair.empty:
                continue
            diff = (pair[f"{metric}_left"] - pair[f"{metric}_right"]).to_numpy(dtype=float)
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
                    "metric": metric_names[metric],
                    "mean_diff": float(diff.mean()),
                    "ci_low": float(np.quantile(means, 0.025)),
                    "ci_high": float(np.quantile(means, 0.975)),
                    "n_pairs": int(len(diff)),
                    "block_size": int(block_size),
                }
            )
    return pd.DataFrame(rows)


def finalize_portfolio_harness_output(results: pd.DataFrame, candidate_log: pd.DataFrame, config: dict) -> PortfolioRunOutput:
    summary = (
        results.groupby("arm", sort=False)
        .agg(
            locked_cvar_95=("oos_cvar_95", "mean"),
            locked_downside_deviation=("oos_downside_deviation", "mean"),
            locked_sortino=("oos_sortino", "mean"),
            locked_calmar=("oos_calmar", "mean"),
            locked_max_drawdown=("oos_max_drawdown", "mean"),
            locked_drawdown_duration=("oos_drawdown_duration", "mean"),
            realized_volatility=("oos_realized_volatility", "mean"),
            turnover=("oos_turnover", "mean"),
            transaction_cost_paid=("oos_transaction_cost_paid", "mean"),
            turnover_adjusted_net_return=("oos_turnover_adjusted_net_return", "mean"),
            constraint_violation_severity=("oos_constraint_violation_severity", "mean"),
            infeasible_optimization_events=("oos_infeasible_optimization_events", "mean"),
            optimizer_recovery_success_rate=("oos_optimizer_recovery_success_rate", "mean"),
            failed_rebalance_retention_rate=("oos_failed_rebalance_retention_rate", "mean"),
            cash_ratio_due_to_infeasibility=("oos_cash_ratio_due_to_infeasibility", "mean"),
            exposure_drift=("oos_exposure_drift", "mean"),
            herfindahl_index=("oos_herfindahl_index", "mean"),
            diversification_ratio=("oos_diversification_ratio", "mean"),
            asset_class_cap_violation_severity=("oos_asset_class_cap_violation_severity", "mean"),
            high_vol_return=("oos_high_vol_return", "mean"),
            normal_vol_return=("oos_normal_vol_return", "mean"),
            stress_recovery_return=("oos_stress_recovery_return", "mean"),
            locked_cumulative_return=("oos_cumulative_return", "mean"),
            locked_annualized_return=("oos_annualized_return", "mean"),
            locked_sharpe=("oos_sharpe", "mean"),
            valid_selected_cells=("selection_status", lambda s: int((s == "VALID_SELECTED").sum())),
            no_valid_candidate_cells=("selection_status", lambda s: int((s == "NO_VALID_CANDIDATE").sum())),
        )
        .reset_index()
    )
    true_counts = candidate_log.groupby("arm")["candidate_id"].nunique().rename("true_candidate_count")
    valid_counts = candidate_log[candidate_log["valid_for_selection"]].groupby("arm")["candidate_id"].nunique().rename("valid_candidate_count")
    summary = summary.merge(true_counts, on="arm", how="left").merge(valid_counts, on="arm", how="left")
    summary["true_candidate_count"] = summary["true_candidate_count"].fillna(1).astype(int)
    summary["valid_candidate_count"] = summary["valid_candidate_count"].fillna(0).astype(int)
    invalid = candidate_log[~candidate_log["valid_for_selection"].astype(bool)].copy()
    if invalid.empty:
        invalid_log = pd.DataFrame(columns=["arm", "seed", "split_id", "candidate_id", "reason", "validation_score", "locked_score_if_computed", "why_not_selected"])
    else:
        invalid_log = pd.DataFrame(
            {
                "arm": invalid["arm"],
                "seed": invalid["seed"],
                "split_id": invalid["split_id"],
                "candidate_id": invalid["candidate_id"],
                "reason": invalid["gate_reason"],
                "validation_score": invalid["is_score"],
                "locked_score_if_computed": invalid["oos_score"],
                "why_not_selected": "FAILED_HARD_GATE",
            }
        ).sort_values("validation_score", ascending=False)
    bootstrap_samples = int(config.get("bootstrap_iterations", config.get("bootstrap_samples", 200)))
    block_size = int(config.get("block_size", config.get("bootstrap_block_size", 5)))
    paired = paired_block_bootstrap(results, block_size, bootstrap_samples)
    return PortfolioRunOutput(results, candidate_log, summary, invalid_log, paired)


def run_portfolio_harness(bundle: PublicDataBundle, config: dict, quick: bool = False) -> PortfolioRunOutput:
    cfg = dict(config)
    if quick:
        cfg["n_seeds"] = int(cfg.get("quick_n_seeds", 1))
        cfg["search_budget"] = int(cfg.get("quick_search_budget", 12))
    features = build_portfolio_features(bundle.prices, cfg)
    if quick:
        quick_start = pd.Timestamp(features["date"].max()) - pd.DateOffset(years=4)
        features = features[features["date"] >= quick_start].copy()
    features = assign_time_blocks(features, int(cfg["selection_blocks"]), int(cfg["final_confirmation_months"]))
    cfg["effective_start_date"] = str(pd.Timestamp(features["date"].min()).date())
    cfg["effective_end_date"] = str(pd.Timestamp(features["date"].max()).date())
    matrices = portfolio_feature_matrices(features)
    returns = np.asarray(matrices["return_1d"], dtype=float)
    blocks = np.asarray(matrices["block"], dtype=int)
    stress_mask = (
        np.asarray(matrices["stress_covariance_near_singular"], dtype=bool)
        | np.asarray(matrices["stress_missing_returns_block"], dtype=bool)
        | np.asarray(matrices["stress_stale_price"], dtype=bool)
        | np.asarray(matrices["stress_infeasible_constraints"], dtype=bool)
        | np.asarray(matrices["stress_high_turnover"], dtype=bool)
        | np.asarray(matrices["stress_cost_spike"], dtype=bool)
        | np.asarray(matrices["stress_concentration_shock"], dtype=bool)
    )
    high_vol_mask = np.asarray(matrices["stress_extreme_volatility"], dtype=bool)
    asset_classes = list(matrices["asset_classes"])
    base = base_portfolio_harness(cfg)
    fixed_base = fixed_safe_harness(base)
    budget = int(cfg["search_budget"])
    splits = _block_splits(int(cfg["selection_blocks"]), int(cfg["validation_window_blocks"]), int(cfg["oos_window_blocks"]))
    weight_cache: dict[tuple[tuple[str, object], ...], tuple[np.ndarray, pd.DataFrame]] = {}
    gate_cache: dict[tuple[tuple[str, object], ...], tuple[bool, str]] = {}
    eval_cache: dict[tuple[tuple[tuple[str, object], ...], tuple[int, ...]], object] = {}
    candidate_rows: list[dict] = []
    result_rows: list[dict] = []

    def weights_for(harness: PortfolioHarnessConfig) -> tuple[np.ndarray, pd.DataFrame]:
        key = _harness_key(harness)
        if key not in weight_cache:
            weight_cache[key] = compute_portfolio_weight_matrix(matrices, harness, cfg, clean_panel=False)
        return weight_cache[key]

    def gate_for(harness: PortfolioHarnessConfig) -> tuple[bool, str]:
        key = _harness_key(harness)
        if key not in gate_cache:
            gate_cache[key] = legal_harness_gate(fixed_base, harness, matrices, cfg)
        return gate_cache[key]

    def eval_for(harness: PortfolioHarnessConfig, block_ids: list[int]):
        key = (_harness_key(harness), tuple(block_ids))
        if key not in eval_cache:
            mask = np.isin(blocks, block_ids)
            weights, events = weights_for(harness)
            eval_cache[key] = evaluate_portfolio_weights(
                returns, weights, mask, stress_mask, high_vol_mask, events, asset_classes, harness, cfg
            )
        return eval_cache[key]

    seed_values = [int(seed) for seed in cfg.get("seed_ids", range(int(cfg["n_seeds"]))) ]
    for seed in seed_values:
        for split_id, (is_blocks, oos_blocks) in enumerate(splits):
            for arm in SEARCH_ARMS:
                candidates = _candidates_for_arm(arm, fixed_base, cfg, budget, seed)
                scored = []
                for idx, harness in enumerate(candidates):
                    gate_pass, gate_reason = gate_for(harness)
                    if arm == "Fixed Safe Portfolio Harness":
                        selectable = gate_pass
                    elif arm in LEGAL_COMPARISON_ARMS:
                        selectable = gate_pass
                    elif arm == "Unconstrained Portfolio Harness Search":
                        selectable = gate_pass
                    else:
                        selectable = False
                    skip_illegal_eval = not gate_pass and arm != "Portfolio Strategy Tuning Baseline"
                    if skip_illegal_eval:
                        is_eval = _empty_eval()
                        oos_eval = _empty_eval()
                        invalid_proxy = _invalid_candidate_score(gate_reason)
                        is_score = invalid_proxy
                        oos_score = np.nan
                        selection = -1e9
                    else:
                        is_eval = eval_for(harness, is_blocks)
                        oos_eval = eval_for(harness, oos_blocks)
                        is_score = is_eval.turnover_adjusted_net_return
                        oos_score = oos_eval.turnover_adjusted_net_return
                        selection = _selection_objective(is_eval, selectable)
                    if arm == "Random Legal Harness Patch":
                        selection = float(idx == 0) if selectable else -1e9
                    if arm == "Portfolio Strategy Tuning Baseline":
                        selection = _selection_objective(is_eval, True)
                    row = {
                        "arm": arm,
                        "seed": seed,
                        "split_id": split_id,
                        "candidate_id": f"{arm}-{seed}-{idx}",
                        "selection_score": selection,
                        "is_score": is_score,
                        "oos_score": oos_score,
                        "valid_for_selection": selectable,
                        "selection_status": "VALID_CANDIDATE" if selectable else "INVALID_CANDIDATE",
                        "gate_pass": gate_pass,
                        "gate_reason": gate_reason,
                        "clean_panel_w_star_invariance": "CLEAN_PANEL_W_STAR_CHANGED" not in gate_reason,
                        "policy_specification_frozen": "POLICY_SPECIFICATION_CHANGED" not in gate_reason,
                        "leakage_audit_pass": not bool(harness.allow_future_returns),
                        "candidate_values": harness.to_dict(),
                        **{f"is_{k}": v for k, v in is_eval.to_dict().items()},
                        **{f"oos_{k}": v for k, v in oos_eval.to_dict().items()},
                    }
                    candidate_rows.append(row)
                    scored.append(row)
                if arm == "Portfolio Strategy Tuning Baseline":
                    chosen = sorted(scored, key=lambda row: row["selection_score"], reverse=True)[0]
                    result_rows.append(chosen | {"chosen": True, "selection_status": "STRATEGY_SELECTED"})
                else:
                    valid_scored = [row for row in scored if row["valid_for_selection"]]
                    if valid_scored:
                        chosen = sorted(valid_scored, key=lambda row: row["selection_score"], reverse=True)[0]
                        result_rows.append(chosen | {"chosen": True, "selection_status": "VALID_SELECTED"})
                    else:
                        null_row = {"arm": arm, "seed": seed, "split_id": split_id, "candidate_id": pd.NA, "selection_score": np.nan, "is_score": np.nan, "oos_score": np.nan, "valid_for_selection": False, "selection_status": "NO_VALID_CANDIDATE", "chosen": False, "gate_pass": False, "gate_reason": "NO_VALID_CANDIDATE"}
                        for prefix in ["is", "oos"]:
                            for key in evaluate_portfolio_weights(returns, np.zeros_like(returns), np.zeros(len(returns), dtype=bool), stress_mask, high_vol_mask, pd.DataFrame(), asset_classes, fixed_base, cfg).to_dict():
                                null_row[f"{prefix}_{key}"] = np.nan
                        result_rows.append(null_row)
            for arm in PASSIVE_ARMS:
                weights = _passive_weights(matrices, arm, cfg)
                mask = np.isin(blocks, oos_blocks)
                eval_obj = evaluate_portfolio_weights(returns, weights, mask, stress_mask, high_vol_mask, pd.DataFrame(), asset_classes, fixed_base, cfg)
                result_rows.append({"arm": arm, "seed": seed, "split_id": split_id, "candidate_id": f"{arm}-{seed}-{split_id}", "selection_status": "PASSIVE", "valid_for_selection": True, "chosen": True, "selection_score": np.nan, "is_score": np.nan, "oos_score": eval_obj.turnover_adjusted_net_return, "gate_pass": True, "gate_reason": "PASSIVE", **{f"oos_{k}": v for k, v in eval_obj.to_dict().items()}})
    candidate_log = pd.DataFrame(candidate_rows)
    results = pd.DataFrame(result_rows)
    return finalize_portfolio_harness_output(results, candidate_log, cfg)
