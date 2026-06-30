from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .portfolio_harness_patches import PortfolioHarnessConfig


@dataclass(frozen=True)
class PortfolioEvaluation:
    cumulative_return: float
    annualized_return: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    drawdown_duration: float
    cvar_95: float
    downside_deviation: float
    realized_volatility: float
    turnover: float
    transaction_cost_paid: float
    turnover_adjusted_net_return: float
    constraint_violation_severity: float
    infeasible_optimization_events: int
    optimizer_recovery_success_rate: float
    failed_rebalance_retention_rate: float
    cash_ratio_due_to_infeasibility: float
    exposure_drift: float
    herfindahl_index: float
    diversification_ratio: float
    asset_class_cap_violation_severity: float
    high_vol_return: float
    normal_vol_return: float
    stress_recovery_return: float
    n_days: int

    def to_dict(self) -> dict:
        return asdict(self)


def _drawdown_duration(drawdown: np.ndarray) -> float:
    durations = []
    current = 0
    for value in drawdown:
        if value < 0.0:
            current += 1
        else:
            if current:
                durations.append(current)
            current = 0
    if current:
        durations.append(current)
    return float(max(durations) if durations else 0)


def evaluate_portfolio_weights(
    returns: np.ndarray,
    weights: np.ndarray,
    mask: np.ndarray,
    stress_mask: np.ndarray,
    high_vol_mask: np.ndarray,
    events,
    asset_classes: list[str],
    harness: PortfolioHarnessConfig,
    config: dict,
) -> PortfolioEvaluation:
    if not bool(mask.any()):
        return PortfolioEvaluation(
            cumulative_return=0.0,
            annualized_return=0.0,
            sharpe=0.0,
            sortino=0.0,
            calmar=0.0,
            max_drawdown=0.0,
            drawdown_duration=0.0,
            cvar_95=0.0,
            downside_deviation=0.0,
            realized_volatility=0.0,
            turnover=0.0,
            transaction_cost_paid=0.0,
            turnover_adjusted_net_return=0.0,
            constraint_violation_severity=0.0,
            infeasible_optimization_events=0,
            optimizer_recovery_success_rate=0.0,
            failed_rebalance_retention_rate=0.0,
            cash_ratio_due_to_infeasibility=0.0,
            exposure_drift=0.0,
            herfindahl_index=0.0,
            diversification_ratio=0.0,
            asset_class_cap_violation_severity=0.0,
            high_vol_return=0.0,
            normal_vol_return=0.0,
            stress_recovery_return=0.0,
            n_days=0,
        )
    w = weights[mask]
    r = returns[mask]
    shifted = np.vstack([np.zeros((1, w.shape[1])), w[:-1]])
    turnover_vec = np.concatenate([[np.abs(w[0]).sum()], np.abs(np.diff(w, axis=0)).sum(axis=1)])
    cost_multiplier = np.where(stress_mask[mask], 2.5, 1.0)
    costs = turnover_vec * (float(config["transaction_cost_bps"]) / 10000.0) * cost_multiplier
    gross = (shifted * r).sum(axis=1)
    net = gross - costs
    equity = np.cumprod(1.0 + net)
    cumulative = float(equity[-1] - 1.0)
    annual = float(equity[-1] ** (252.0 / max(1, len(net))) - 1.0)
    std = float(net.std(ddof=0))
    sharpe = 0.0 if std == 0.0 else float(net.mean() / std * np.sqrt(252.0))
    downside = net[net < 0.0]
    downside_dev = 0.0 if downside.size == 0 else float(np.sqrt(np.mean(np.square(downside))) * np.sqrt(252.0))
    sortino = 0.0 if downside_dev == 0.0 else float(net.mean() * 252.0 / downside_dev)
    drawdown = equity / np.maximum.accumulate(equity) - 1.0
    max_dd = float(drawdown.min())
    calmar = 0.0 if max_dd == 0.0 else annual / abs(max_dd)
    q = np.quantile(net, 0.05) if len(net) else 0.0
    cvar = float(net[net <= q].mean()) if np.any(net <= q) else 0.0
    max_weight = float(harness.max_weight if harness.max_weight is not None else config["max_weight"])
    asset_cap = float(harness.asset_class_cap if harness.asset_class_cap is not None else config["asset_class_cap"])
    turnover_cap = float(harness.turnover_cap if harness.turnover_cap is not None else config["turnover_cap"])
    max_weight_violation = np.maximum(w - max_weight, 0.0).sum(axis=1)
    turnover_violation = np.maximum(turnover_vec - turnover_cap, 0.0)
    class_violation_arr = np.zeros(w.shape[0], dtype=float)
    for cls in sorted(set(asset_classes)):
        idx = np.asarray([i for i, value in enumerate(asset_classes) if value == cls], dtype=int)
        if idx.size:
            exposure = w[:, idx].sum(axis=1)
            class_violation_arr += np.maximum(exposure - asset_cap, 0.0)
    severity = float(max_weight_violation.mean() + turnover_violation.mean() + class_violation_arr.mean())
    event_count = len(events) if events is not None else 0
    failed = 0
    success = 0
    if events is not None and event_count:
        failed = int((~events["success"].astype(bool)).sum()) if "success" in events.columns else 0
        success = int(events["success"].astype(bool).sum()) if "success" in events.columns else event_count
    recovery = 1.0 if event_count == 0 else float(success / event_count)
    failed_retention = 1.0 if failed == 0 else float(bool(harness.retain_failed_rebalance))
    cash_ratio = float(np.maximum(0.0, 1.0 - w.sum(axis=1)).mean())
    exposure_drift = float(np.abs(w.sum(axis=1) - (1.0 - float(config["min_cash_buffer"]))).mean())
    herf = float(np.square(w).sum(axis=1).mean())
    asset_vol = np.std(r, axis=0, ddof=0)
    port_vol = std
    div_ratio = 0.0 if port_vol == 0.0 else float(np.mean((w * asset_vol).sum(axis=1)) / port_vol)
    high_mask = high_vol_mask[mask]
    high_ret = float(net[high_mask].mean()) if np.any(high_mask) else 0.0
    normal_ret = float(net[~high_mask].mean()) if np.any(~high_mask) else 0.0
    stress_ret = float(net[stress_mask[mask]].mean()) if np.any(stress_mask[mask]) else 0.0
    return PortfolioEvaluation(
        cumulative_return=cumulative,
        annualized_return=annual,
        sharpe=sharpe,
        sortino=float(sortino),
        calmar=float(calmar),
        max_drawdown=max_dd,
        drawdown_duration=_drawdown_duration(drawdown),
        cvar_95=cvar,
        downside_deviation=downside_dev,
        realized_volatility=std * float(np.sqrt(252.0)),
        turnover=float(turnover_vec.mean()),
        transaction_cost_paid=float(costs.sum()),
        turnover_adjusted_net_return=float(cumulative - costs.sum()),
        constraint_violation_severity=severity,
        infeasible_optimization_events=failed,
        optimizer_recovery_success_rate=recovery,
        failed_rebalance_retention_rate=failed_retention,
        cash_ratio_due_to_infeasibility=cash_ratio,
        exposure_drift=exposure_drift,
        herfindahl_index=herf,
        diversification_ratio=div_ratio,
        asset_class_cap_violation_severity=float(class_violation_arr.mean()),
        high_vol_return=high_ret,
        normal_vol_return=normal_ret,
        stress_recovery_return=stress_ret,
        n_days=int(len(net)),
    )
