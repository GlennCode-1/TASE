from __future__ import annotations

import numpy as np

from .portfolio_harness_patches import PortfolioHarnessConfig
from .portfolio_optimizer import compute_portfolio_weight_matrix

POLICY_FIELDS = [
    "risk_aversion_lambda",
    "objective_return_weight",
    "max_weight",
    "turnover_cap",
    "asset_class_cap",
    "min_cash_buffer",
    "rebalance_frequency",
    "momentum_window",
    "volatility_penalty",
    "universe_token",
]


def policy_specification_frozen(base: PortfolioHarnessConfig, candidate: PortfolioHarnessConfig, config: dict) -> bool:
    for field in POLICY_FIELDS:
        base_value = getattr(base, field)
        candidate_value = getattr(candidate, field)
        if candidate_value != base_value:
            return False
    return not bool(candidate.allow_policy_change)


def clean_panel_w_star_invariance(base: PortfolioHarnessConfig, candidate: PortfolioHarnessConfig, matrices: dict[str, object], config: dict, tolerance: float = 1e-10) -> bool:
    if not policy_specification_frozen(base, candidate, config):
        return False
    base_w, _ = compute_portfolio_weight_matrix(matrices, base, config, clean_panel=True)
    cand_w, _ = compute_portfolio_weight_matrix(matrices, candidate, config, clean_panel=True)
    return bool(np.allclose(base_w, cand_w, atol=float(tolerance)))


def leakage_gate(candidate: PortfolioHarnessConfig) -> bool:
    return not bool(candidate.allow_future_returns)


def legal_harness_gate(base: PortfolioHarnessConfig, candidate: PortfolioHarnessConfig, matrices: dict[str, object], config: dict) -> tuple[bool, str]:
    reasons = []
    if not policy_specification_frozen(base, candidate, config):
        reasons.append("POLICY_SPECIFICATION_CHANGED")
    if not leakage_gate(candidate):
        reasons.append("FUTURE_RETURN_LEAKAGE")
    if not clean_panel_w_star_invariance(base, candidate, matrices, config):
        reasons.append("CLEAN_PANEL_W_STAR_CHANGED")
    if candidate.cost_accounting == "loose":
        reasons.append("LOOSE_COST_ACCOUNTING")
    return (len(reasons) == 0, ";".join(reasons) or "VALID")
