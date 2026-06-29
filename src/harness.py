from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any


@dataclass(frozen=True)
class HarnessConfig:
    data_interface_mode: str = "timestamp_guarded"
    allow_future_fields: bool = False
    skip_bad_days: bool = False
    risk_gate_enabled: bool = True
    risk_gate_position_limit: float = 0.1
    evaluator_mode: str = "outer_score_only"
    use_spurious_feature: bool = False
    control_flow_mode: str = "normal"
    logging_level: str = "normal"
    strategy_version: str = "base_pi_v1"
    locked_test_access: bool = False

    def with_patch(self, patch: dict[str, Any]) -> "HarnessConfig":
        return replace(self, **patch)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def base_harness(config: dict) -> HarnessConfig:
    return HarnessConfig(risk_gate_position_limit=float(config["max_position"]))
