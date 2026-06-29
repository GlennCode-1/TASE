from __future__ import annotations

import math

import numpy as np
import pandas as pd


def deflated_sharpe_ratio(sharpe: float, n_trials: int, n_obs: int) -> float:
    if n_obs <= 2:
        return 0.0
    expected_max = math.sqrt(2.0 * math.log(max(2, int(n_trials)))) / math.sqrt(max(1, n_obs))
    return float((sharpe - expected_max) * math.sqrt(max(1, n_obs - 1)))


def spa_like_pvalue(best_oos_score: float, candidate_oos_scores: list[float]) -> float:
    if not candidate_oos_scores:
        return 1.0
    scores = np.asarray(candidate_oos_scores, dtype=float)
    return float((np.sum(scores >= best_oos_score) + 1.0) / (len(scores) + 1.0))


def summarize_pbo(candidate_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for arm, group in candidate_log.groupby("arm", sort=False):
        split_rows = []
        for split_id, split_group in group.groupby("split_id"):
            if split_group.empty:
                continue
            best = split_group.sort_values("is_score", ascending=False).iloc[0]
            oos_rank = split_group["oos_score"].rank(ascending=False, method="average")
            best_rank = float(oos_rank.loc[best.name])
            bottom_half = best_rank > (len(split_group) + 1.0) / 2.0
            corr = split_group[["is_score", "oos_score"]].corr(method="spearman").iloc[0, 1]
            split_rows.append(
                {
                    "split_id": split_id,
                    "best_is_score": float(best["is_score"]),
                    "best_oos_score": float(best["oos_score"]),
                    "degradation": float(best["is_score"] - best["oos_score"]),
                    "bottom_half": bool(bottom_half),
                    "rank_corr": 0.0 if pd.isna(corr) else float(corr),
                    "best_dsr": float(best["dsr"]),
                    "best_spa_pvalue": spa_like_pvalue(float(best["oos_score"]), split_group["oos_score"].tolist()),
                    "candidate_count": int(split_group["candidate_id"].nunique()),
                }
            )
        frame = pd.DataFrame(split_rows)
        if frame.empty:
            continue
        rows.append(
            {
                "arm": arm,
                "pbo_estimate": float(frame["bottom_half"].mean()),
                "is_oos_rank_correlation": float(frame["rank_corr"].mean()),
                "validation_to_oos_degradation": float(frame["degradation"].mean()),
                "deflated_sharpe_ratio": float(frame["best_dsr"].mean()),
                "spa_like_pvalue": float(frame["best_spa_pvalue"].mean()),
                "true_candidate_count": int(group["candidate_id"].nunique()),
                "mean_split_candidate_count": float(frame["candidate_count"].mean()),
            }
        )
    return pd.DataFrame(rows)
