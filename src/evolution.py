from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .data_generator import DataBundle
from .evaluator import (
    EvaluationMetrics,
    evaluate_harness,
    financial_meta_fitness,
    selection_score_for_arm_d,
)
from .harness import HarnessConfig, base_harness
from .patches import (
    PatchProposal,
    apply_patch_to_harness,
    diagnostic_guided_tase_patches,
    sample_arm_d_patch,
    sample_arm_g_patch,
)
from .validator import validate_tase_patch


@dataclass(frozen=True)
class ArmRunResult:
    arm: str
    seed: int
    final_harness: HarnessConfig
    validation_metrics: EvaluationMetrics
    test_metrics: EvaluationMetrics
    accepted_patch_count: int
    useful_patch_count: int
    rejected_patch_count: int
    unsafe_accepted_patch_rate: float
    patch_log: list[dict]


def _unsafe_flag(harness: HarnessConfig, config: dict) -> bool:
    return (
        harness.allow_future_fields
        or harness.skip_bad_days
        or not harness.risk_gate_enabled
        or harness.risk_gate_position_limit > float(config["max_position"])
        or harness.use_spurious_feature
        or harness.control_flow_mode in {"skip_errors", "ignore_missing"}
        or harness.evaluator_mode != "outer_score_only"
    )


def _effective_complexity(harness: HarnessConfig, config: dict) -> int:
    base = base_harness(config).to_dict()
    current = harness.to_dict()
    ignored = {"logging_level"}
    return sum(1 for key, value in current.items() if key not in ignored and value != base[key])


def _is_useful_transition(before: EvaluationMetrics, after: EvaluationMetrics) -> bool:
    return (
        after.constraint_compliant_score >= before.constraint_compliant_score - 1e-12
        and after.leakage_violations <= before.leakage_violations
        and after.silent_skip_count <= before.silent_skip_count
        and after.risk_violations <= before.risk_violations
    )


def _run_arm_d(bundle: DataBundle, seed: int, config: dict) -> ArmRunResult:
    rng = np.random.default_rng(seed + 10_000)
    current = base_harness(config)
    current_complexity = 0
    current_validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    current_selection_score = selection_score_for_arm_d(current_validation, current)
    patch_log: list[dict] = []
    accepted = 0
    unsafe_accepted = 0

    for round_idx in range(int(config["patch_budget"])):
        best_tuple = (current_selection_score, current, current_validation, current_complexity, None)
        for candidate_idx in range(int(config["candidate_per_round"])):
            proposal = sample_arm_d_patch(rng, round_idx, candidate_idx, config)
            candidate = apply_patch_to_harness(current, proposal)
            candidate_complexity = _effective_complexity(candidate, config)
            metrics = evaluate_harness(bundle, "validation", candidate, config, candidate_complexity)
            selection_score = selection_score_for_arm_d(metrics, candidate)
            patch_log.append(
                {
                    "arm": "Generic Unconstrained",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id,
                    "status": "CANDIDATE",
                    "selection_split": "validation",
                    "selection_score": selection_score,
                    "outer_validation_score": metrics.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                }
            )
            if selection_score > best_tuple[0]:
                best_tuple = (selection_score, candidate, metrics, candidate_complexity, proposal)

        if best_tuple[4] is not None:
            current_selection_score, current, current_validation, current_complexity, proposal = best_tuple
            accepted += 1
            unsafe_accepted += int(_unsafe_flag(current, config))
            patch_log.append(
                {
                    "arm": "Generic Unconstrained",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id,
                    "status": "ACCEPTED",
                    "selection_split": "validation",
                    "selection_score": current_selection_score,
                    "outer_validation_score": current_validation.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                }
            )

    final_validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    final_test = evaluate_harness(bundle, "test", current, config, current_complexity)
    unsafe_rate = unsafe_accepted / accepted if accepted else 0.0
    return ArmRunResult(
        arm="Generic Unconstrained",
        seed=seed,
        final_harness=current,
        validation_metrics=final_validation,
        test_metrics=final_test,
        accepted_patch_count=accepted,
        useful_patch_count=0,
        rejected_patch_count=0,
        unsafe_accepted_patch_rate=unsafe_rate,
        patch_log=patch_log,
    )


def _run_arm_g(bundle: DataBundle, seed: int, config: dict, proposer_mode: str = "random_greedy") -> ArmRunResult:
    rng = np.random.default_rng(seed + 20_000)
    current = base_harness(config)
    current_complexity = 0
    current_validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    current_selection_score = financial_meta_fitness(current_validation)
    patch_log: list[dict] = []
    accepted = 0
    rejected = 0
    unsafe_accepted = 0
    useful_accepted = 0
    previous_rejections: list[str] = []

    for round_idx in range(int(config["patch_budget"])):
        best_tuple = (current_selection_score, current, current_validation, current_complexity, None)
        if proposer_mode == "diagnostic":
            proposals = diagnostic_guided_tase_patches(
                current=current,
                validation_metrics=current_validation,
                config=config,
                round_idx=round_idx,
                candidate_per_round=int(config["candidate_per_round"]),
                previous_rejections=tuple(previous_rejections),
            )
        else:
            proposals = [
                sample_arm_g_patch(rng, round_idx, candidate_idx, config)
                for candidate_idx in range(int(config["candidate_per_round"]))
            ]

        for proposal in proposals:
            candidate = apply_patch_to_harness(current, proposal)
            validation = validate_tase_patch(candidate, proposal, config)
            if not validation.accepted:
                rejected += 1
                previous_rejections.extend(validation.reasons)
                patch_log.append(
                    {
                        "arm": "TASE Finance-Constrained",
                        "seed": seed,
                        "round": round_idx,
                        "patch_id": proposal.patch_id,
                        "status": "REJECTED",
                        "selection_split": "validation",
                        "selection_score": np.nan,
                        "outer_validation_score": np.nan,
                        "reject_reasons": "|".join(validation.reasons),
                        "patch_values": str(proposal.values),
                    }
                )
                continue

            candidate_complexity = _effective_complexity(candidate, config)
            metrics = evaluate_harness(bundle, "validation", candidate, config, candidate_complexity)
            selection_score = financial_meta_fitness(metrics)
            patch_log.append(
                {
                    "arm": "TASE Finance-Constrained",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id,
                    "status": "CANDIDATE",
                    "selection_split": "validation",
                    "selection_score": selection_score,
                    "outer_validation_score": metrics.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                }
            )
            improves_selection = selection_score > best_tuple[0]
            neutral_useful = (
                proposer_mode == "diagnostic"
                and selection_score >= best_tuple[0] - 1e-12
                and _is_useful_transition(current_validation, metrics)
            )
            if improves_selection or neutral_useful:
                best_tuple = (selection_score, candidate, metrics, candidate_complexity, proposal)

        if best_tuple[4] is not None:
            previous_validation = current_validation
            current_selection_score, current, current_validation, current_complexity, proposal = best_tuple
            accepted += 1
            unsafe_accepted += int(_unsafe_flag(current, config))
            useful_accepted += int(_is_useful_transition(previous_validation, current_validation))
            patch_log.append(
                {
                    "arm": "TASE Finance-Constrained",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id,
                    "status": "ACCEPTED",
                    "selection_split": "validation",
                    "selection_score": current_selection_score,
                    "outer_validation_score": current_validation.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                    "proposer_mode": proposer_mode,
                    "useful_patch": _is_useful_transition(previous_validation, current_validation),
                }
            )

    final_validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    final_test = evaluate_harness(bundle, "test", current, config, current_complexity)
    unsafe_rate = unsafe_accepted / accepted if accepted else 0.0
    return ArmRunResult(
        arm="TASE Finance-Constrained",
        seed=seed,
        final_harness=current,
        validation_metrics=final_validation,
        test_metrics=final_test,
        accepted_patch_count=accepted,
        useful_patch_count=useful_accepted,
        rejected_patch_count=rejected,
        unsafe_accepted_patch_rate=unsafe_rate,
        patch_log=patch_log,
    )


def constrained_fixed_harness(config: dict) -> HarnessConfig:
    return HarnessConfig(
        data_interface_mode="timestamp_guarded",
        allow_future_fields=False,
        skip_bad_days=False,
        risk_gate_enabled=True,
        risk_gate_position_limit=float(config["max_position"]),
        evaluator_mode="outer_score_only",
        use_spurious_feature=False,
        control_flow_mode="fail_closed",
        logging_level="verbose",
    )


def _run_arm_e(bundle: DataBundle, seed: int, config: dict) -> ArmRunResult:
    current = constrained_fixed_harness(config)
    current_complexity = _effective_complexity(current, config)
    validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    test = evaluate_harness(bundle, "test", current, config, current_complexity)
    return ArmRunResult(
        arm="Constrained Fixed",
        seed=seed,
        final_harness=current,
        validation_metrics=validation,
        test_metrics=test,
        accepted_patch_count=0,
        useful_patch_count=0,
        rejected_patch_count=0,
        unsafe_accepted_patch_rate=0.0,
        patch_log=[
            {
                "arm": "Constrained Fixed",
                "seed": seed,
                "round": -1,
                "patch_id": "fixed-constrained",
                "status": "FIXED",
                "selection_split": "none",
                "selection_score": np.nan,
                "outer_validation_score": validation.score,
                "reject_reasons": "",
                "patch_values": current.to_json(),
            }
        ],
    )


def _run_arm_f(bundle: DataBundle, seed: int, config: dict) -> ArmRunResult:
    rng = np.random.default_rng(seed + 30_000)
    current = base_harness(config)
    current_complexity = 0
    rejected = 0
    accepted = 0
    unsafe_accepted = 0
    patch_log: list[dict] = []

    for round_idx in range(int(config["patch_budget"])):
        legal_candidates: list[tuple[PatchProposal, HarnessConfig, EvaluationMetrics, int]] = []
        for candidate_idx in range(int(config["candidate_per_round"])):
            proposal = sample_arm_g_patch(rng, round_idx, candidate_idx, config)
            candidate = apply_patch_to_harness(current, proposal)
            validation = validate_tase_patch(candidate, proposal, config)
            if not validation.accepted:
                rejected += 1
                patch_log.append(
                    {
                        "arm": "Random Legal Patch",
                        "seed": seed,
                        "round": round_idx,
                        "patch_id": proposal.patch_id.replace("G-", "F-"),
                        "status": "REJECTED",
                        "selection_split": "none",
                        "selection_score": np.nan,
                        "outer_validation_score": np.nan,
                        "reject_reasons": "|".join(validation.reasons),
                        "patch_values": str(proposal.values),
                    }
                )
                continue

            candidate_complexity = _effective_complexity(candidate, config)
            metrics = evaluate_harness(bundle, "validation", candidate, config, candidate_complexity)
            legal_candidates.append((proposal, candidate, metrics, candidate_complexity))
            patch_log.append(
                {
                    "arm": "Random Legal Patch",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id.replace("G-", "F-"),
                    "status": "LEGAL_CANDIDATE",
                    "selection_split": "none",
                    "selection_score": np.nan,
                    "outer_validation_score": metrics.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                }
            )

        if legal_candidates:
            idx = int(rng.integers(0, len(legal_candidates)))
            proposal, current, validation_metrics, current_complexity = legal_candidates[idx]
            accepted += 1
            unsafe_accepted += int(_unsafe_flag(current, config))
            patch_log.append(
                {
                    "arm": "Random Legal Patch",
                    "seed": seed,
                    "round": round_idx,
                    "patch_id": proposal.patch_id.replace("G-", "F-"),
                    "status": "ACCEPTED_RANDOM",
                    "selection_split": "none",
                    "selection_score": np.nan,
                    "outer_validation_score": validation_metrics.score,
                    "reject_reasons": "",
                    "patch_values": str(proposal.values),
                }
            )

    final_validation = evaluate_harness(bundle, "validation", current, config, current_complexity)
    final_test = evaluate_harness(bundle, "test", current, config, current_complexity)
    unsafe_rate = unsafe_accepted / accepted if accepted else 0.0
    return ArmRunResult(
        arm="Random Legal Patch",
        seed=seed,
        final_harness=current,
        validation_metrics=final_validation,
        test_metrics=final_test,
        accepted_patch_count=accepted,
        useful_patch_count=0,
        rejected_patch_count=rejected,
        unsafe_accepted_patch_rate=unsafe_rate,
        patch_log=patch_log,
    )


def run_evolution_for_seed(bundle: DataBundle, seed: int, config: dict) -> list[ArmRunResult]:
    return [_run_arm_d(bundle, seed, config), _run_arm_g(bundle, seed, config)]


def run_stage2_for_seed(bundle: DataBundle, seed: int, config: dict) -> list[ArmRunResult]:
    return [
        _run_arm_d(bundle, seed, config),
        _run_arm_e(bundle, seed, config),
        _run_arm_f(bundle, seed, config),
        _run_arm_g(bundle, seed, config),
    ]


def run_stage3_for_seed(bundle: DataBundle, seed: int, config: dict) -> list[ArmRunResult]:
    return [
        _run_arm_d(bundle, seed, config),
        _run_arm_e(bundle, seed, config),
        _run_arm_f(bundle, seed, config),
        _run_arm_g(bundle, seed, config, proposer_mode="diagnostic"),
    ]
