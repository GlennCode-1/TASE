from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
from typing import Any

import pandas as pd

from .hashing import hash_object


REQUIRED_OPERATOR_FAMILIES = [
    "cross_sectional_momentum",
    "time_series_momentum",
    "short_term_reversal",
    "medium_term_reversal",
    "volatility",
    "low_volatility",
    "volatility_scaled_momentum",
    "volume_liquidity",
    "moving_average_crossover",
    "breakout",
    "residual_momentum",
    "sector_neutral_momentum",
    "rank_combination",
    "two_factor_combination",
    "risk_adjusted_variant",
]

BASE_GRID = {
    "lookback_window": [5, 20, 60, 120],
    "holding_period": [1, 5, 20],
    "rank_method": ["raw", "winsorized"],
    "sector_neutralization": [False],
    "volatility_scaling": [False, True],
}

FAMILY_OVERRIDES = {
    "volume_liquidity": {"requires_volume": True},
    "sector_neutral_momentum": {"requires_sector_label": True, "sector_neutralization": [True]},
    "rank_combination": {"combination_mode": ["momentum_lowvol", "momentum_liquidity"]},
    "two_factor_combination": {"combination_mode": ["momentum_value_proxy", "momentum_volatility"]},
    "moving_average_crossover": {"fast_window": [5, 20], "slow_window": [60, 120]},
    "breakout": {"breakout_window": [20, 60]},
}


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    operator_family: str
    parameter_json: str
    requires_sector_label: bool
    requires_volume: bool
    requires_returns: bool
    uses_future_data: bool
    expected_holding_period: int
    status: str
    notes: str


def operator_library_spec() -> pd.DataFrame:
    rows = []
    for family in REQUIRED_OPERATOR_FAMILIES:
        overrides = FAMILY_OVERRIDES.get(family, {})
        rows.append(
            {
                "operator_family": family,
                "status": "included",
                "requires_sector_label": bool(overrides.get("requires_sector_label", family == "sector_neutral_momentum")),
                "requires_volume": bool(overrides.get("requires_volume", family == "volume_liquidity")),
                "requires_returns": True,
                "allowed_parameter_keys": ",".join(sorted(set(BASE_GRID) | set(overrides))),
                "frozen_in_b0": True,
                "notes": "pre-registered B0 design only; no PnL computed",
            }
        )
    return pd.DataFrame(rows)


def _family_grid(family: str) -> dict[str, list[Any]]:
    grid = {key: list(value) for key, value in BASE_GRID.items()}
    overrides = FAMILY_OVERRIDES.get(family, {})
    for key, value in overrides.items():
        if key.startswith("requires_"):
            continue
        grid[key] = list(value)
    if family == "sector_neutral_momentum":
        grid["sector_neutralization"] = [True]
    return grid


def _candidate_id(operator_family: str, parameters: dict[str, Any], universe_role: str) -> str:
    payload = {
        "operator_family": operator_family,
        "parameters": parameters,
        "universe_role": universe_role,
        "holding_period": parameters["holding_period"],
    }
    return hash_object(payload)[:16]


def build_candidate_library(universe_role: str = "approximate_pit_us_stock_universe") -> pd.DataFrame:
    rows: list[CandidateSpec] = []
    for family in REQUIRED_OPERATOR_FAMILIES:
        grid = _family_grid(family)
        keys = sorted(grid)
        for values in itertools.product(*(grid[key] for key in keys)):
            params = dict(zip(keys, values))
            params["cost_model"] = "fixed_not_tunable"
            overrides = FAMILY_OVERRIDES.get(family, {})
            requires_sector = bool(overrides.get("requires_sector_label", params.get("sector_neutralization", False)))
            requires_volume = bool(overrides.get("requires_volume", False))
            rows.append(
                CandidateSpec(
                    candidate_id=_candidate_id(family, params, universe_role),
                    operator_family=family,
                    parameter_json=json.dumps(params, sort_keys=True, separators=(",", ":")),
                    requires_sector_label=requires_sector,
                    requires_volume=requires_volume,
                    requires_returns=True,
                    uses_future_data=False,
                    expected_holding_period=int(params["holding_period"]),
                    status="pre_registered_design",
                    notes="B0 library definition only; candidate signal/PnL to be precomputed in B1",
                )
            )
    return pd.DataFrame([row.__dict__ for row in rows]).drop_duplicates("candidate_id").reset_index(drop=True)


def candidate_count_status(count: int, target_min: int = 1000, target_max: int = 2000) -> str:
    if count < target_min:
        return "BELOW_TARGET_NEEDS_PRE_REGISTERED_EXPANSION"
    if count > target_max:
        return "ABOVE_TARGET_NEEDS_PRE_REGISTERED_SHRINK"
    return "PASS_WITHIN_TARGET"
