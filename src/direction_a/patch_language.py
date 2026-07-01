from __future__ import annotations

from .schemas import FORBIDDEN_FIELDS, PatchType, TargetStage, WorkflowPatch, validate_patch

FROZEN_METHOD_CONSTRAINTS = [
    "fixed candidate strategy library",
    "fixed operator library",
    "fixed parameter grid",
    "fixed candidate budget",
    "fixed transaction cost",
    "fixed locked-test window and final metric",
    "candidate signal/PnL/turnover/cost-PnL invariance by hash",
    "archive completeness and no hidden candidate drops",
    "locked-test inaccessible during B0 and workflow selection",
]

__all__ = [
    "FORBIDDEN_FIELDS",
    "FROZEN_METHOD_CONSTRAINTS",
    "PatchType",
    "TargetStage",
    "WorkflowPatch",
    "validate_patch",
]
