from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from itertools import product

import numpy as np


@dataclass(frozen=True)
class PortfolioHarnessConfig:
    covariance_estimator: str = "ledoit_wolf_0_20"
    solver: str = "projected_closed_form"
    solver_tolerance: float = 1e-8
    retry_policy: str = "retry_then_fallback"
    fallback_policy: str = "previous_weights"
    constraint_repair: str = "clip_scale_turnover"
    missing_policy: str = "past_only_impute"
    stale_policy: str = "stale_asset_to_cash"
    turnover_enforcement: str = "scale_trades"
    cost_accounting: str = "conservative"
    exposure_monitoring: str = "full_audit"
    retain_failed_rebalance: bool = True
    allow_future_returns: bool = False
    ignore_infeasible_days: bool = False
    allow_policy_change: bool = False
    risk_aversion_lambda: float | None = None
    objective_return_weight: float | None = None
    max_weight: float | None = None
    turnover_cap: float | None = None
    asset_class_cap: float | None = None
    min_cash_buffer: float | None = None
    rebalance_frequency: str | None = None
    momentum_window: int | None = None
    volatility_penalty: float | None = None
    universe_token: str = "fixed"

    def with_patch(self, patch: dict) -> "PortfolioHarnessConfig":
        return replace(self, **patch)

    def to_dict(self) -> dict:
        return asdict(self)


def base_portfolio_harness(config: dict) -> PortfolioHarnessConfig:
    return PortfolioHarnessConfig(
        risk_aversion_lambda=float(config["risk_aversion_lambda"]),
        objective_return_weight=float(config.get("objective_return_weight", 1.0)),
        max_weight=float(config["max_weight"]),
        turnover_cap=float(config["turnover_cap"]),
        asset_class_cap=float(config["asset_class_cap"]),
        min_cash_buffer=float(config["min_cash_buffer"]),
        rebalance_frequency=str(config["rebalance_frequency"]),
        momentum_window=int(config["momentum_window"]),
        volatility_penalty=float(config["volatility_penalty"]),
    )


def fixed_safe_harness(base: PortfolioHarnessConfig) -> PortfolioHarnessConfig:
    return base.with_patch(
        {
            "covariance_estimator": "ledoit_wolf_0_20",
            "solver": "projected_closed_form",
            "retry_policy": "retry_then_fallback",
            "fallback_policy": "previous_weights",
            "constraint_repair": "clip_scale_turnover",
            "missing_policy": "past_only_impute",
            "stale_policy": "stale_asset_to_cash",
            "turnover_enforcement": "scale_trades",
            "cost_accounting": "conservative",
            "exposure_monitoring": "full_audit",
            "retain_failed_rebalance": True,
        }
    )


def safe_config_space(base: PortfolioHarnessConfig, budget: int) -> list[PortfolioHarnessConfig]:
    variants: list[PortfolioHarnessConfig] = []
    grid = product(
        ["sample_then_diagonal", "ledoit_wolf_0_20", "ledoit_wolf_0_50", "ewma_60"],
        ["retry_then_fallback", "single_try_fallback"],
        ["previous_weights", "risk_parity", "cash"],
        ["clip_scale_turnover", "nearest_feasible", "slack_priority"],
        ["past_only_impute", "exclude_asset_this_rebalance"],
        ["scale_trades", "strict"],
        ["strict", "conservative"],
    )
    for cov, retry, fallback, repair, missing, turnover, cost in grid:
        variants.append(
            base.with_patch(
                {
                    "covariance_estimator": cov,
                    "retry_policy": retry,
                    "fallback_policy": fallback,
                    "constraint_repair": repair,
                    "missing_policy": missing,
                    "turnover_enforcement": turnover,
                    "cost_accounting": cost,
                    "exposure_monitoring": "full_audit",
                    "retain_failed_rebalance": True,
                }
            )
        )
        if len(variants) >= int(budget):
            break
    return variants


def tase_config_space(base: PortfolioHarnessConfig, budget: int) -> list[PortfolioHarnessConfig]:
    preferred = [
        base.with_patch(
            {
                "covariance_estimator": "ledoit_wolf_0_50",
                "retry_policy": "retry_then_fallback",
                "fallback_policy": "risk_parity",
                "constraint_repair": "nearest_feasible",
                "missing_policy": "exclude_asset_this_rebalance",
                "stale_policy": "stale_asset_to_cash",
                "turnover_enforcement": "scale_trades",
                "cost_accounting": "conservative",
            }
        ),
        base.with_patch(
            {
                "covariance_estimator": "ewma_60",
                "fallback_policy": "previous_weights",
                "constraint_repair": "clip_scale_turnover",
                "missing_policy": "past_only_impute",
                "turnover_enforcement": "scale_trades",
                "cost_accounting": "conservative",
            }
        ),
        base.with_patch(
            {
                "covariance_estimator": "sample_then_diagonal",
                "fallback_policy": "cash",
                "constraint_repair": "slack_priority",
                "missing_policy": "exclude_asset_this_rebalance",
                "turnover_enforcement": "strict",
                "cost_accounting": "conservative",
            }
        ),
    ]
    variants = preferred + safe_config_space(base, max(0, int(budget) - len(preferred)))
    return variants[: int(budget)]


def random_legal_space(base: PortfolioHarnessConfig, budget: int, seed: int) -> list[PortfolioHarnessConfig]:
    legal = safe_config_space(base, max(int(budget) * 2, int(budget) + 3))
    rng = np.random.default_rng(seed + 4400)
    picks = rng.choice(len(legal), size=int(budget), replace=len(legal) < int(budget))
    return [legal[int(idx)] for idx in picks]


def unconstrained_space(base: PortfolioHarnessConfig, config: dict, budget: int, seed: int) -> list[PortfolioHarnessConfig]:
    rng = np.random.default_rng(seed + 5500)
    variants: list[PortfolioHarnessConfig] = []
    for _ in range(int(budget)):
        variants.append(
            base.with_patch(
                {
                    "covariance_estimator": str(rng.choice(["sample_then_diagonal", "raw_sample", "future_covariance"])),
                    "fallback_policy": str(rng.choice(["previous_weights", "cash", "ignore_failure"])),
                    "constraint_repair": str(rng.choice(["clip_scale_turnover", "relax_caps", "none"])),
                    "turnover_enforcement": str(rng.choice(["scale_trades", "ignore"])),
                    "cost_accounting": str(rng.choice(["strict", "conservative", "loose"])),
                    "allow_future_returns": bool(rng.random() < 0.25),
                    "ignore_infeasible_days": bool(rng.random() < 0.30),
                    "allow_policy_change": True,
                    "risk_aversion_lambda": float(rng.choice([config["risk_aversion_lambda"], 0.5, 1.0, 8.0])),
                    "max_weight": float(rng.choice([config["max_weight"], 0.30, 0.45])),
                    "turnover_cap": float(rng.choice([config["turnover_cap"], 0.60, 1.0])),
                    "rebalance_frequency": str(rng.choice([config["rebalance_frequency"], "D", "M"])),
                    "momentum_window": int(rng.choice([config["momentum_window"], 10, 60])),
                    "volatility_penalty": float(rng.choice([config["volatility_penalty"], 0.0, 1.0])),
                    "universe_token": str(rng.choice(["fixed", "return_filtered"])),
                }
            )
        )
    return variants


def strategy_tuning_space(base: PortfolioHarnessConfig, config: dict, budget: int) -> list[PortfolioHarnessConfig]:
    variants: list[PortfolioHarnessConfig] = []
    for lam, max_w, turnover, rebalance, mw, vol_penalty in product(
        [1.0, float(config["risk_aversion_lambda"]), 6.0],
        [float(config["max_weight"]), 0.30],
        [float(config["turnover_cap"]), 0.70],
        [str(config["rebalance_frequency"]), "M"],
        [int(config["momentum_window"]), 60],
        [float(config["volatility_penalty"]), 0.0],
    ):
        variants.append(
            base.with_patch(
                {
                    "allow_policy_change": True,
                    "risk_aversion_lambda": float(lam),
                    "max_weight": float(max_w),
                    "turnover_cap": float(turnover),
                    "rebalance_frequency": str(rebalance),
                    "momentum_window": int(mw),
                    "volatility_penalty": float(vol_penalty),
                }
            )
        )
        if len(variants) >= int(budget):
            break
    return variants
