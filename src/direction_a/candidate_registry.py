from __future__ import annotations

import pandas as pd

REGISTRY_COLUMNS = [
    "candidate_id",
    "operator_family",
    "parameter_hash",
    "signal_hash",
    "pnl_hash",
    "turnover_hash",
    "cost_pnl_hash",
    "matrix_path_signal",
    "matrix_path_pnl",
    "matrix_path_turnover",
    "matrix_path_cost_pnl",
    "created_at",
    "data_window_start",
    "data_window_end",
    "universe_id",
    "status",
]


def registry_schema() -> pd.DataFrame:
    descriptions = {
        "candidate_id": "deterministic sha256 id for operator family + sorted parameters + universe role",
        "operator_family": "pre-registered operator family",
        "parameter_hash": "sha256 hash of sorted parameter JSON",
        "signal_hash": "sha256 hash of rounded signal matrix slice",
        "pnl_hash": "sha256 hash of rounded gross return/PnL series",
        "turnover_hash": "sha256 hash of rounded turnover series",
        "cost_pnl_hash": "sha256 hash of rounded cost-adjusted PnL series",
        "matrix_path_signal": "relative path to signal matrix shard",
        "matrix_path_pnl": "relative path to gross/net PnL matrix shard",
        "matrix_path_turnover": "relative path to turnover matrix shard",
        "matrix_path_cost_pnl": "relative path to cost-adjusted PnL matrix shard",
        "created_at": "UTC creation timestamp for precompute artifact",
        "data_window_start": "data window start used for precompute",
        "data_window_end": "data window end used for precompute",
        "universe_id": "versioned universe identifier",
        "status": "precomputed, quarantined, invalid, or missing",
    }
    return pd.DataFrame({"field": REGISTRY_COLUMNS, "description": [descriptions[col] for col in REGISTRY_COLUMNS]})
