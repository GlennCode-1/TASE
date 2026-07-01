from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.direction_a.schemas import WorkflowPatch, validate_patch


def test_valid_validation_schedule_patch_passes() -> None:
    patch = validate_patch(
        {
            "patch_id": "p1",
            "patch_type": "ValidationSchedulePatch",
            "target_stage": "validation",
            "operation": "set_validation_scheme",
            "parameters": {"scheme": "CSCV_10", "aggregation": "median_rank"},
            "expected_effect": "reduce validation overfit",
            "safety_tags": ["locked_test_isolated"],
        }
    )
    assert patch.patch_type.value == "ValidationSchedulePatch"


@pytest.mark.parametrize("field", ["locked_test_metric", "python_code"])
def test_forbidden_fields_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        WorkflowPatch.model_validate(
            {
                "patch_id": "bad",
                "patch_type": "ValidationSchedulePatch",
                "target_stage": "validation",
                "operation": "set_validation_scheme",
                "parameters": {"scheme": "CSCV_10", "aggregation": "median_rank", field: "bad"},
                "expected_effect": "bad",
            }
        )


def test_unknown_patch_type_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_patch(
            {
                "patch_id": "bad",
                "patch_type": "AlphaFormulaPatch",
                "target_stage": "validation",
                "operation": "set_validation_scheme",
                "parameters": {"scheme": "CSCV_10", "aggregation": "median_rank"},
                "expected_effect": "bad",
            }
        )


def test_arbitrary_nested_dict_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_patch(
            {
                "patch_id": "bad",
                "patch_type": "PruningRulePatch",
                "target_stage": "candidate_filtering",
                "operation": "set_pruning_rule",
                "parameters": {"metric": "pbo_adjusted_sharpe", "threshold": {"free": 0.1}, "min_folds_survived": 4},
                "expected_effect": "bad",
            }
        )


def test_patch_parameters_constrained_by_enum() -> None:
    with pytest.raises(ValidationError):
        validate_patch(
            {
                "patch_id": "bad",
                "patch_type": "PenaltyUsagePatch",
                "target_stage": "scoring",
                "operation": "enable_penalty",
                "parameters": {"penalty_type": "PBO", "weight": "picked_after_validation"},
                "expected_effect": "bad",
            }
        )
