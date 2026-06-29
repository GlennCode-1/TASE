from __future__ import annotations

import pandas as pd

from .data_generator import generate_synthetic_data
from .evolution import ArmRunResult, run_evolution_for_seed, run_stage2_for_seed, run_stage3_for_seed


def _result_row(result: ArmRunResult) -> dict:
    validation = result.validation_metrics
    test = result.test_metrics
    return {
        "arm": result.arm,
        "seed": result.seed,
        "validation_score": validation.score,
        "locked_test_score": test.score,
        "validation_test_gap": validation.score - test.score,
        "constraint_compliant_score": test.constraint_compliant_score,
        "validation_constraint_compliant_score": validation.constraint_compliant_score,
        "leakage_violations": test.leakage_violations,
        "silent_skip_count": test.silent_skip_count,
        "risk_violations": test.risk_violations,
        "unsafe_accepted_patch_rate": result.unsafe_accepted_patch_rate,
        "accepted_patch_count": result.accepted_patch_count,
        "useful_patch_count": result.useful_patch_count,
        "rejected_patch_count": result.rejected_patch_count,
        "final_harness_config": result.final_harness.to_json(),
        "outer_evaluator_version": test.evaluator_version,
    }


def _summary(results_by_seed: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "validation_score",
        "locked_test_score",
        "validation_test_gap",
        "constraint_compliant_score",
        "leakage_violations",
        "silent_skip_count",
        "risk_violations",
        "unsafe_accepted_patch_rate",
        "accepted_patch_count",
        "useful_patch_count",
        "rejected_patch_count",
    ]
    grouped = results_by_seed.groupby("arm", sort=False)[metrics].agg(["mean", "std"])
    grouped.columns = [f"{metric}_{stat}" for metric, stat in grouped.columns]
    return grouped.reset_index()


def _add_stage2_comparisons(results_by_seed: pd.DataFrame) -> pd.DataFrame:
    df = results_by_seed.copy()
    comparison_cols = [
        "beats_constrained_fixed",
        "beats_random_legal_patch",
        "delta_vs_constrained_fixed_locked_test",
        "delta_vs_random_legal_patch_locked_test",
        "delta_vs_constrained_fixed_compliant_score",
        "delta_vs_random_legal_patch_compliant_score",
    ]
    for col in comparison_cols:
        df[col] = False if col.startswith("beats_") else 0.0

    for seed, group in df.groupby("seed"):
        by_arm = group.set_index("arm")
        if "TASE Finance-Constrained" not in by_arm.index:
            continue
        tase = by_arm.loc["TASE Finance-Constrained"]
        fixed = by_arm.loc["Constrained Fixed"] if "Constrained Fixed" in by_arm.index else None
        random = by_arm.loc["Random Legal Patch"] if "Random Legal Patch" in by_arm.index else None
        tase_mask = (df["seed"] == seed) & (df["arm"] == "TASE Finance-Constrained")

        if fixed is not None:
            delta_locked = float(tase["locked_test_score"] - fixed["locked_test_score"])
            delta_compliant = float(tase["constraint_compliant_score"] - fixed["constraint_compliant_score"])
            df.loc[tase_mask, "delta_vs_constrained_fixed_locked_test"] = delta_locked
            df.loc[tase_mask, "delta_vs_constrained_fixed_compliant_score"] = delta_compliant
            df.loc[tase_mask, "beats_constrained_fixed"] = bool(delta_compliant > 0.0)

        if random is not None:
            delta_locked = float(tase["locked_test_score"] - random["locked_test_score"])
            delta_compliant = float(tase["constraint_compliant_score"] - random["constraint_compliant_score"])
            df.loc[tase_mask, "delta_vs_random_legal_patch_locked_test"] = delta_locked
            df.loc[tase_mask, "delta_vs_random_legal_patch_compliant_score"] = delta_compliant
            df.loc[tase_mask, "beats_random_legal_patch"] = bool(delta_compliant > 0.0)

    return df


def run_killtest(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows: list[dict] = []
    patch_rows: list[dict] = []

    for seed in range(int(config["n_seeds"])):
        bundle = generate_synthetic_data(config, seed)
        for result in run_evolution_for_seed(bundle, seed, config):
            result_rows.append(_result_row(result))
            patch_rows.extend(result.patch_log)

    results_by_seed = pd.DataFrame(result_rows)
    patch_log = pd.DataFrame(patch_rows)
    summary = _summary(results_by_seed)
    return results_by_seed, patch_log, summary


def run_stage2_controls(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows: list[dict] = []
    patch_rows: list[dict] = []

    for seed in range(int(config["n_seeds"])):
        bundle = generate_synthetic_data(config, seed)
        for result in run_stage2_for_seed(bundle, seed, config):
            result_rows.append(_result_row(result))
            patch_rows.extend(result.patch_log)

    results_by_seed = _add_stage2_comparisons(pd.DataFrame(result_rows))
    patch_log = pd.DataFrame(patch_rows)
    summary = _summary(results_by_seed)
    return results_by_seed, patch_log, summary


def _violation_load(row: pd.Series) -> float:
    return (
        float(row["leakage_violations_mean"])
        + float(row["silent_skip_count_mean"]) / 20.0
        + float(row["risk_violations_mean"]) / 20.0
    )


def _add_stage3_summary_columns(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    by_arm = out.set_index("arm")
    tase = by_arm.loc["TASE Finance-Constrained"]
    fixed = by_arm.loc["Constrained Fixed"]
    random = by_arm.loc["Random Legal Patch"]

    tase_delta_fixed_locked = float(tase["locked_test_score_mean"] - fixed["locked_test_score_mean"])
    tase_delta_fixed_compliant = float(
        tase["constraint_compliant_score_mean"] - fixed["constraint_compliant_score_mean"]
    )
    tase_delta_random_locked = float(tase["locked_test_score_mean"] - random["locked_test_score_mean"])
    tase_delta_random_compliant = float(
        tase["constraint_compliant_score_mean"] - random["constraint_compliant_score_mean"]
    )
    tase_accepted = float(tase["accepted_patch_count_mean"])
    tase_useful = float(tase["useful_patch_count_mean"])
    tase_rejected = float(tase["rejected_patch_count_mean"])

    tase_viol = _violation_load(tase)
    fixed_viol = _violation_load(fixed)
    random_viol = _violation_load(random)
    h3 = (
        (tase_delta_fixed_locked > 0.0 or tase_delta_fixed_compliant > 0.0)
        and tase_viol <= fixed_viol + 1e-12
        and tase_accepted > 0.6
    )
    h4 = (
        tase_delta_random_locked > 0.0
        and tase_delta_random_compliant > 0.0
        and tase_viol <= random_viol + 1.0
    )

    out["tase_accepted_patch_count_mean"] = tase_accepted
    out["tase_useful_patch_count_mean"] = tase_useful
    out["tase_rejected_patch_count_mean"] = tase_rejected
    out["tase_delta_vs_constrained_fixed_locked_test"] = tase_delta_fixed_locked
    out["tase_delta_vs_constrained_fixed_compliant_score"] = tase_delta_fixed_compliant
    out["tase_delta_vs_random_legal_locked_test"] = tase_delta_random_locked
    out["tase_delta_vs_random_legal_compliant_score"] = tase_delta_random_compliant
    out["h3_supported"] = h3
    out["h4_supported"] = h4
    return out


def run_stage3_proposer(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows: list[dict] = []
    patch_rows: list[dict] = []

    for seed in range(int(config["n_seeds"])):
        bundle = generate_synthetic_data(config, seed)
        for result in run_stage3_for_seed(bundle, seed, config):
            result_rows.append(_result_row(result))
            patch_rows.extend(result.patch_log)

    results_by_seed = _add_stage2_comparisons(pd.DataFrame(result_rows))
    patch_log = pd.DataFrame(patch_rows)
    summary = _add_stage3_summary_columns(_summary(results_by_seed))
    return results_by_seed, patch_log, summary
