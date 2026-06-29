from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .harness import HarnessConfig


@dataclass(frozen=True)
class PatchProposal:
    patch_id: str
    values: dict[str, Any]
    proposer: str
    complexity: int


def _complexity(values: dict[str, Any]) -> int:
    return sum(1 for value in values.values() if value is not None)


def sample_arm_d_patch(rng: np.random.Generator, round_idx: int, candidate_idx: int, config: dict) -> PatchProposal:
    max_position = float(config["max_position"])
    values = {
        "data_interface_mode": rng.choice(["raw", "timestamp_guarded"]),
        "allow_future_fields": bool(rng.random() < 0.40),
        "skip_bad_days": bool(rng.random() < 0.45),
        "risk_gate_enabled": bool(rng.random() < 0.45),
        "risk_gate_position_limit": float(rng.choice([max_position, max_position * 1.5, max_position * 2.5, max_position * 4.0])),
        "evaluator_mode": rng.choice(["raw_return", "sharpe", "exploit_validation"]),
        "use_spurious_feature": bool(rng.random() < 0.65),
        "control_flow_mode": rng.choice(["normal", "skip_errors", "retry", "ignore_missing"]),
        "logging_level": rng.choice(["minimal", "normal", "verbose"]),
    }
    return PatchProposal(
        patch_id=f"D-r{round_idx:02d}-c{candidate_idx:02d}",
        values=values,
        proposer="random_greedy_unconstrained",
        complexity=_complexity(values),
    )


def sample_arm_g_patch(rng: np.random.Generator, round_idx: int, candidate_idx: int, config: dict) -> PatchProposal:
    max_position = float(config["max_position"])
    # Most proposals are legal typed infrastructure tweaks; a small share are
    # unsafe probes, so the validator's rejection behavior is observable.
    if rng.random() < 0.72:
        values = {
            "data_interface_mode": "timestamp_guarded",
            "allow_future_fields": False,
            "skip_bad_days": False,
            "risk_gate_enabled": True,
            "risk_gate_position_limit": float(rng.choice([max_position * 0.6, max_position * 0.8, max_position])),
            "evaluator_mode": "outer_score_only",
            "use_spurious_feature": False,
            "control_flow_mode": rng.choice(["normal", "retry", "fail_closed"]),
            "logging_level": rng.choice(["normal", "verbose"]),
        }
    else:
        unsafe_kind = rng.choice(["future", "skip", "risk", "spurious", "inner_eval"])
        values = {
            "data_interface_mode": "timestamp_guarded",
            "allow_future_fields": unsafe_kind == "future",
            "skip_bad_days": unsafe_kind == "skip",
            "risk_gate_enabled": unsafe_kind != "risk",
            "risk_gate_position_limit": max_position * (1.8 if unsafe_kind == "risk" else 1.0),
            "evaluator_mode": "exploit_validation" if unsafe_kind == "inner_eval" else "outer_score_only",
            "use_spurious_feature": unsafe_kind == "spurious",
            "control_flow_mode": "skip_errors" if unsafe_kind == "skip" else "normal",
            "logging_level": "normal",
        }

    return PatchProposal(
        patch_id=f"G-r{round_idx:02d}-c{candidate_idx:02d}",
        values=values,
        proposer="typed_finance_constrained",
        complexity=_complexity(values),
    )


def diagnostic_guided_tase_patches(
    current: HarnessConfig,
    validation_metrics,
    config: dict,
    round_idx: int,
    candidate_per_round: int,
    previous_rejections: tuple[str, ...] = (),
) -> list[PatchProposal]:
    max_position = float(config["max_position"])
    risk_high = validation_metrics.risk_violations > max(3, 0.10 * validation_metrics.n_days_available)
    failures_high = validation_metrics.silent_skip_count > 0 or "SILENT_SKIP" in previous_rejections
    leakage_seen = validation_metrics.leakage_violations > 0 or "LEAKAGE" in previous_rejections
    compliance_gap_high = (validation_metrics.score - validation_metrics.constraint_compliant_score) > 1.0

    candidates: list[dict[str, Any]] = []

    if risk_high or compliance_gap_high:
        candidates.extend(
            [
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position,
                    "control_flow_mode": "fail_closed",
                    "logging_level": "verbose",
                },
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position * 0.8,
                    "control_flow_mode": "fail_closed",
                    "logging_level": "verbose",
                },
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position * 0.6,
                    "control_flow_mode": "fail_closed",
                    "logging_level": "verbose",
                },
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position,
                    "control_flow_mode": "retry",
                    "logging_level": "verbose",
                },
            ]
        )

    if failures_high:
        candidates.extend(
            [
                {"control_flow_mode": "retry", "logging_level": "verbose"},
                {"control_flow_mode": "fail_closed", "logging_level": "verbose"},
            ]
        )

    if leakage_seen:
        candidates.append(
            {
                "data_interface_mode": "timestamp_guarded",
                "allow_future_fields": False,
                "evaluator_mode": "outer_score_only",
                "use_spurious_feature": False,
            }
        )

    safe_but_weak = not risk_high and not failures_high and not leakage_seen
    if safe_but_weak or len(candidates) < candidate_per_round:
        candidates.extend(
            [
                {"control_flow_mode": "retry", "logging_level": "normal"},
                {"control_flow_mode": "retry", "logging_level": "verbose"},
                {"control_flow_mode": "normal", "logging_level": "verbose"},
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position,
                    "control_flow_mode": "fail_closed",
                    "logging_level": "verbose",
                },
                {
                    "risk_gate_enabled": True,
                    "risk_gate_position_limit": max_position * 0.8,
                    "control_flow_mode": "normal",
                    "logging_level": "normal",
                },
            ]
        )

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()
    for values in candidates:
        safe_values = {
            "data_interface_mode": "timestamp_guarded",
            "allow_future_fields": False,
            "skip_bad_days": False,
            "risk_gate_enabled": True,
            "evaluator_mode": "outer_score_only",
            "use_spurious_feature": False,
            **values,
        }
        key = tuple(sorted(safe_values.items()))
        if key not in seen and current.with_patch(safe_values) != current:
            seen.add(key)
            normalized.append(safe_values)
        if len(normalized) >= candidate_per_round:
            break

    proposals: list[PatchProposal] = []
    for candidate_idx, values in enumerate(normalized):
        proposals.append(
            PatchProposal(
                patch_id=f"G3-r{round_idx:02d}-c{candidate_idx:02d}",
                values=values,
                proposer="diagnostic_guided_tase",
                complexity=_complexity(values),
            )
        )
    return proposals


def apply_patch_to_harness(harness: HarnessConfig, proposal: PatchProposal) -> HarnessConfig:
    return harness.with_patch(proposal.values)
