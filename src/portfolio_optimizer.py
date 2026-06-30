from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio_harness_patches import PortfolioHarnessConfig


def rebalance_dates(dates: pd.DatetimeIndex, rule: str) -> set[pd.Timestamp]:
    if str(rule) == "D":
        return set(pd.Timestamp(d) for d in dates)
    marker = pd.DataFrame(index=pd.DatetimeIndex(dates))
    return set(pd.Timestamp(d) for d in marker.resample(str(rule)).last().dropna().index)


def _covariance(window: np.ndarray, estimator: str) -> np.ndarray:
    if window.shape[0] < 2:
        return np.eye(window.shape[1]) * 1e-4
    clean = np.nan_to_num(window, nan=0.0, posinf=0.0, neginf=0.0)
    cov = np.cov(clean, rowvar=False)
    if cov.ndim == 0:
        cov = np.asarray([[float(cov)]])
    diag = np.diag(np.diag(cov))
    if estimator == "ledoit_wolf_0_50":
        cov = 0.5 * cov + 0.5 * diag
    elif estimator == "ledoit_wolf_0_20":
        cov = 0.8 * cov + 0.2 * diag
    elif estimator == "ewma_60":
        decay = 0.5 ** (1.0 / 60.0)
        weights = decay ** np.arange(clean.shape[0] - 1, -1, -1)
        weights = weights / weights.sum()
        demeaned = clean - np.average(clean, axis=0, weights=weights)
        cov = (demeaned * weights[:, None]).T @ demeaned
    elif estimator == "raw_sample":
        cov = cov
    elif estimator == "future_covariance":
        cov = cov * 0.5
    else:
        cov = cov + np.eye(cov.shape[0]) * 1e-6
    return np.nan_to_num(cov, nan=0.0, posinf=0.0, neginf=0.0)


def _risk_parity(cov: np.ndarray, max_weight: float, investable: float) -> np.ndarray:
    diag = np.maximum(np.diag(cov), 1e-8)
    inv = 1.0 / np.sqrt(diag)
    weights = inv / inv.sum() * investable
    return np.minimum(weights, max_weight)


def _cap_asset_class(weights: np.ndarray, asset_classes: list[str], cap: float) -> np.ndarray:
    out = weights.copy()
    for cls in sorted(set(asset_classes)):
        idx = np.asarray([i for i, value in enumerate(asset_classes) if value == cls], dtype=int)
        total = float(out[idx].sum()) if idx.size else 0.0
        if total > cap and total > 0.0:
            out[idx] *= cap / total
    return out


def repair_weights(raw: np.ndarray, prev: np.ndarray, asset_classes: list[str], harness: PortfolioHarnessConfig, config: dict) -> tuple[np.ndarray, float]:
    max_weight = float(harness.max_weight if harness.max_weight is not None else config["max_weight"])
    asset_cap = float(harness.asset_class_cap if harness.asset_class_cap is not None else config["asset_class_cap"])
    turnover_cap = float(harness.turnover_cap if harness.turnover_cap is not None else config["turnover_cap"])
    cash = float(harness.min_cash_buffer if harness.min_cash_buffer is not None else config["min_cash_buffer"])
    investable = max(0.0, 1.0 - cash)
    w = np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0)
    w = np.maximum(w, 0.0)
    if str(harness.constraint_repair) in {"clip_scale_turnover", "nearest_feasible", "slack_priority"}:
        w = np.minimum(w, max_weight)
        w = _cap_asset_class(w, asset_classes, asset_cap)
        total = float(w.sum())
        if total > investable and total > 0.0:
            w *= investable / total
    delta = w - prev
    turnover = float(np.abs(delta).sum())
    if str(harness.turnover_enforcement) in {"scale_trades", "strict"} and turnover > turnover_cap and turnover > 0.0:
        if str(harness.turnover_enforcement) == "strict":
            w = prev.copy()
        else:
            w = prev + delta * (turnover_cap / turnover)
    return w, float(np.abs(w - prev).sum())


def solve_target_weights(alpha: np.ndarray, cov: np.ndarray, prev: np.ndarray, asset_classes: list[str], harness: PortfolioHarnessConfig, config: dict) -> tuple[np.ndarray, bool, str]:
    lam = float(harness.risk_aversion_lambda if harness.risk_aversion_lambda is not None else config["risk_aversion_lambda"])
    ret_weight = float(harness.objective_return_weight if harness.objective_return_weight is not None else config.get("objective_return_weight", 1.0))
    max_weight = float(harness.max_weight if harness.max_weight is not None else config["max_weight"])
    investable = max(0.0, 1.0 - float(harness.min_cash_buffer if harness.min_cash_buffer is not None else config["min_cash_buffer"]))
    try:
        ridge = cov + np.eye(cov.shape[0]) * 1e-5
        raw = np.linalg.pinv(ridge) @ (alpha * ret_weight) / max(lam, 1e-8)
        raw = np.maximum(raw, 0.0)
        if raw.sum() <= 0.0:
            raw = np.ones_like(alpha) / len(alpha) * investable
        else:
            raw = raw / raw.sum() * investable
        raw = np.minimum(raw, max_weight)
        weights, _ = repair_weights(raw, prev, asset_classes, harness, config)
        return weights, True, "ok"
    except np.linalg.LinAlgError:
        return fallback_weights(prev, cov, asset_classes, harness, config), False, "solver_failure"


def fallback_weights(prev: np.ndarray, cov: np.ndarray, asset_classes: list[str], harness: PortfolioHarnessConfig, config: dict) -> np.ndarray:
    investable = max(0.0, 1.0 - float(harness.min_cash_buffer if harness.min_cash_buffer is not None else config["min_cash_buffer"]))
    max_weight = float(harness.max_weight if harness.max_weight is not None else config["max_weight"])
    if harness.fallback_policy == "cash":
        return np.zeros_like(prev)
    if harness.fallback_policy == "risk_parity":
        raw = _risk_parity(cov, max_weight, investable)
        repaired, _ = repair_weights(raw, prev, asset_classes, harness, config)
        return repaired
    if harness.fallback_policy == "ignore_failure":
        return np.ones_like(prev) / len(prev) * investable
    return prev.copy()


def compute_portfolio_weight_matrix(matrices: dict[str, object], harness: PortfolioHarnessConfig, config: dict, clean_panel: bool = False) -> tuple[np.ndarray, pd.DataFrame]:
    dates = matrices["dates"]
    tickers = matrices["tickers"]
    asset_classes = list(matrices["asset_classes"])
    returns = np.asarray(matrices["return_1d"], dtype=float)
    scores = np.asarray(matrices["future_return_1d" if harness.allow_future_returns else "score"], dtype=float)
    if harness.momentum_window != int(config["momentum_window"]) or harness.volatility_penalty != float(config["volatility_penalty"]):
        scores = scores * (float(harness.momentum_window or config["momentum_window"]) / float(config["momentum_window"])) - 0.01 * float(harness.volatility_penalty or config["volatility_penalty"])
    rule = str(harness.rebalance_frequency or config["rebalance_frequency"])
    rebal = rebalance_dates(pd.DatetimeIndex(dates), rule)
    lookback = int(config.get("covariance_lookback", 60))
    weights = np.zeros_like(returns)
    prev = np.zeros(returns.shape[1], dtype=float)
    events: list[dict] = []
    for idx, date in enumerate(pd.DatetimeIndex(dates)):
        if date in rebal:
            start = max(0, idx - lookback)
            window = returns[start:idx]
            alpha = scores[idx].copy()
            if not clean_panel:
                if bool(matrices["stress_missing_returns_block"][idx]) and harness.missing_policy == "exclude_asset_this_rebalance":
                    alpha[: max(1, len(alpha) // 8)] = -999.0
                if bool(matrices["stress_stale_price"][idx]) and harness.stale_policy == "stale_asset_to_cash":
                    alpha[-max(1, len(alpha) // 10):] = -999.0
                if bool(matrices["stress_high_turnover"][idx]):
                    alpha = alpha[::-1]
            estimator = "ledoit_wolf_0_20" if clean_panel else str(harness.covariance_estimator)
            cov = _covariance(window, estimator)
            if not clean_panel and bool(matrices["stress_covariance_near_singular"][idx]):
                cov = cov * 0.0 + np.eye(cov.shape[0]) * 1e-10
            condition = float(np.linalg.cond(cov + np.eye(cov.shape[0]) * 1e-12))
            forced_fail = (not clean_panel and bool(matrices["stress_infeasible_constraints"][idx]) and harness.fallback_policy in {"cash", "risk_parity"})
            if condition > float(config.get("covariance_condition_threshold", 1e6)) and harness.covariance_estimator in {"raw_sample", "sample_then_diagonal"}:
                cov = np.diag(np.maximum(np.diag(cov), 1e-8))
            if forced_fail:
                candidate = fallback_weights(prev, cov, asset_classes, harness, config)
                success = False
                reason = "forced_infeasible_stress"
            else:
                candidate, success, reason = solve_target_weights(alpha, cov, prev, asset_classes, harness, config)
            weights[idx] = candidate
            prev = candidate
            events.append({"date": date, "success": success, "reason": reason, "condition_number": condition})
        else:
            weights[idx] = prev
    return weights, pd.DataFrame(events)
