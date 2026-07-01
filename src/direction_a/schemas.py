from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


FORBIDDEN_FIELDS = {
    "locked_test_window",
    "locked_test_metric",
    "future_return",
    "transaction_cost_override",
    "final_metric_after_validation",
    "operator_library_extension",
    "parameter_grid_extension",
    "candidate_budget_increase",
    "raw_signal_override",
    "pnl_curve_override",
    "hidden_candidate_drop",
    "python_code",
    "arbitrary_code",
}


class PatchType(str, Enum):
    ValidationSchedulePatch = "ValidationSchedulePatch"
    PruningRulePatch = "PruningRulePatch"
    PenaltyUsagePatch = "PenaltyUsagePatch"
    CriticLoopPatch = "CriticLoopPatch"
    EnsembleRulePatch = "EnsembleRulePatch"
    ArchivePolicyPatch = "ArchivePolicyPatch"
    RetestRollbackPatch = "RetestRollbackPatch"


class TargetStage(str, Enum):
    validation = "validation"
    candidate_filtering = "candidate_filtering"
    scoring = "scoring"
    review = "review"
    ensemble = "ensemble"
    archive = "archive"
    diagnostics = "diagnostics"


class ValidationScheme(str, Enum):
    simple_walk_forward = "simple_walk_forward"
    expanding_walk_forward = "expanding_walk_forward"
    CSCV_10 = "CSCV_10"
    CSCV_20 = "CSCV_20"
    regime_split_validation = "regime_split_validation"


class ValidationAggregation(str, Enum):
    mean_rank = "mean_rank"
    median_rank = "median_rank"
    worst_decile_rank = "worst_decile_rank"
    stability_weighted_rank = "stability_weighted_rank"


class PruningMetric(str, Enum):
    validation_sharpe = "validation_sharpe"
    pbo_adjusted_sharpe = "pbo_adjusted_sharpe"
    degradation_adjusted_return = "degradation_adjusted_return"
    turnover_adjusted_return = "turnover_adjusted_return"
    cvar_adjusted_score = "cvar_adjusted_score"


class PruningThreshold(str, Enum):
    pre_registered_low = "pre_registered_low"
    pre_registered_medium = "pre_registered_medium"
    pre_registered_high = "pre_registered_high"


class PenaltyType(str, Enum):
    PBO = "PBO"
    turnover = "turnover"
    drawdown = "drawdown"
    CVaR = "CVaR"
    transaction_cost = "transaction_cost"
    candidate_instability = "candidate_instability"
    ensemble_concentration = "ensemble_concentration"


class PenaltyWeight(str, Enum):
    pre_registered_low = "pre_registered_low"
    pre_registered_medium = "pre_registered_medium"
    pre_registered_high = "pre_registered_high"


class ReviewerType(str, Enum):
    leakage_reviewer = "leakage_reviewer"
    turnover_reviewer = "turnover_reviewer"
    drawdown_reviewer = "drawdown_reviewer"
    regime_stability_reviewer = "regime_stability_reviewer"
    diversity_reviewer = "diversity_reviewer"
    archive_consistency_reviewer = "archive_consistency_reviewer"


class ReviewerDecisionRule(str, Enum):
    veto_if_fail = "veto_if_fail"
    require_two_passes = "require_two_passes"
    downgrade_score = "downgrade_score"
    retest_candidate = "retest_candidate"


class EnsembleRule(str, Enum):
    top_k_by_reliability = "top_k_by_reliability"
    diversity_constrained_top_k = "diversity_constrained_top_k"
    cluster_representative_selection = "cluster_representative_selection"


class EnsembleWeightScheme(str, Enum):
    equal_weight = "equal_weight"
    inverse_turnover = "inverse_turnover"
    reliability_weighted = "reliability_weighted"
    capped_reliability_weighted = "capped_reliability_weighted"


class ArchiveRetrievalPolicy(str, Enum):
    accepted_only = "accepted_only"
    accepted_and_rejected_diagnostics = "accepted_and_rejected_diagnostics"
    failure_pattern_retrieval = "failure_pattern_retrieval"
    lineage_nearest_neighbors = "lineage_nearest_neighbors"


class RetestTrigger(str, Enum):
    high_pbo_warning = "high_pbo_warning"
    degradation_warning = "degradation_warning"
    leakage_reviewer_uncertain = "leakage_reviewer_uncertain"
    regime_instability_warning = "regime_instability_warning"


class RetestAction(str, Enum):
    retest_on_prior_validation_fold = "retest_on_prior_validation_fold"
    rollback_last_patch = "rollback_last_patch"
    quarantine_candidate = "quarantine_candidate"
    require_archive_consistency_review = "require_archive_consistency_review"


class StrictParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidationScheduleParameters(StrictParams):
    scheme: ValidationScheme
    aggregation: ValidationAggregation


class PruningRuleParameters(StrictParams):
    metric: PruningMetric
    threshold: PruningThreshold
    min_folds_survived: Literal[3, 4, 5]


class PenaltyUsageParameters(StrictParams):
    penalty_type: PenaltyType
    weight: PenaltyWeight


class CriticLoopParameters(StrictParams):
    reviewer_type: ReviewerType
    decision_rule: ReviewerDecisionRule


class EnsembleRuleParameters(StrictParams):
    rule: EnsembleRule
    k: Literal[5, 10, 20]
    weight_scheme: EnsembleWeightScheme


class ArchivePolicyParameters(StrictParams):
    retrieval_policy: ArchiveRetrievalPolicy
    include_rejected_diagnostics: bool = True


class RetestRollbackParameters(StrictParams):
    trigger: RetestTrigger
    action: RetestAction


PARAMETER_MODELS = {
    PatchType.ValidationSchedulePatch: ValidationScheduleParameters,
    PatchType.PruningRulePatch: PruningRuleParameters,
    PatchType.PenaltyUsagePatch: PenaltyUsageParameters,
    PatchType.CriticLoopPatch: CriticLoopParameters,
    PatchType.EnsembleRulePatch: EnsembleRuleParameters,
    PatchType.ArchivePolicyPatch: ArchivePolicyParameters,
    PatchType.RetestRollbackPatch: RetestRollbackParameters,
}

ALLOWED_OPERATIONS = {
    PatchType.ValidationSchedulePatch: {"set_validation_scheme"},
    PatchType.PruningRulePatch: {"set_pruning_rule"},
    PatchType.PenaltyUsagePatch: {"enable_penalty", "disable_penalty"},
    PatchType.CriticLoopPatch: {"add_reviewer", "remove_reviewer"},
    PatchType.EnsembleRulePatch: {"set_ensemble_rule"},
    PatchType.ArchivePolicyPatch: {"set_archive_retrieval"},
    PatchType.RetestRollbackPatch: {"set_retest_rule", "set_rollback_rule"},
}


def find_forbidden_fields(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key) in FORBIDDEN_FIELDS:
                found.append(str(key))
            found.extend(find_forbidden_fields(value))
    elif isinstance(obj, list):
        for value in obj:
            found.extend(find_forbidden_fields(value))
    return found


class WorkflowPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patch_id: str = Field(min_length=1)
    patch_type: PatchType
    target_stage: TargetStage
    operation: str
    parameters: dict[str, Any]
    preconditions: list[str] = []
    expected_effect: str
    safety_tags: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden_fields(cls, data: Any) -> Any:
        forbidden = sorted(set(find_forbidden_fields(data)))
        if forbidden:
            raise ValueError(f"forbidden workflow patch fields: {', '.join(forbidden)}")
        return data

    @field_validator("parameters")
    @classmethod
    def reject_nested_freeform_parameters(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                raise ValueError(f"parameter {key} must be an enum, bool, or pre-registered scalar, not nested free-form data")
        return value

    @model_validator(mode="after")
    def validate_typed_parameters(self) -> "WorkflowPatch":
        if self.operation not in ALLOWED_OPERATIONS[self.patch_type]:
            raise ValueError(f"operation {self.operation} is not allowed for {self.patch_type.value}")
        model = PARAMETER_MODELS[self.patch_type]
        try:
            model.model_validate(self.parameters)
        except ValidationError as exc:
            raise ValueError(f"invalid typed parameters for {self.patch_type.value}: {exc}") from exc
        return self

    def typed_parameters(self) -> StrictParams:
        return PARAMETER_MODELS[self.patch_type].model_validate(self.parameters)


def validate_patch(payload: dict[str, Any]) -> WorkflowPatch:
    return WorkflowPatch.model_validate(payload)
