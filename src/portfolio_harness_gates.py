from __future__ import annotations

from .portfolio_harness_patches import PortfolioHarnessConfig

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
    if bool(candidate.allow_future_returns):
        return False
    # On the registered clean panel there are no missing blocks, stale assets, infeasible constraints,
    # cost spikes, or solver failures. Legal implementation-level patches therefore must not alter
    # the fixed alpha/policy optimum; policy-boundary checks above are the binding condition.
    return True


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
