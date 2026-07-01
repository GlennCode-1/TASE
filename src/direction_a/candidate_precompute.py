from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .candidate_operators import IMPLEMENTED_OPERATOR_FAMILIES, compute_candidate_pnl, compute_signal, parse_parameters, signal_to_positions
from .hashing import hash_array, parameter_hash
from .locked_test_store import LockedTestAccessPolicy, write_access_report
from .matrix_store import write_dense_matrix
from .price_loader import price_panel_to_matrices
from .split_manager import SplitSpec, locked_test_mask, train_validation_mask

REGISTRY_COLUMNS = [
    "candidate_id", "operator_family", "parameter_hash", "signal_hash", "pnl_hash", "turnover_hash", "cost_pnl_hash",
    "matrix_path_signal", "matrix_path_pnl", "matrix_path_turnover", "matrix_path_cost_pnl", "created_at",
    "data_window_start", "data_window_end", "universe_id", "status", "uses_future_data", "notes",
]


def select_smoke_candidates(candidate_library: pd.DataFrame, max_candidates: int = 60) -> pd.DataFrame:
    frames = []
    per_family = max(1, int(max_candidates) // len(IMPLEMENTED_OPERATOR_FAMILIES))
    for family in sorted(IMPLEMENTED_OPERATOR_FAMILIES):
        family_rows = candidate_library[candidate_library["operator_family"].eq(family)].head(per_family)
        if family_rows.empty:
            raise ValueError(f"missing B1 smoke family in candidate library: {family}")
        frames.append(family_rows)
    selected = pd.concat(frames, ignore_index=True).head(max_candidates)
    if selected["operator_family"].nunique() < len(IMPLEMENTED_OPERATOR_FAMILIES):
        raise ValueError("smoke candidate subset does not cover all required representative operators")
    return selected.reset_index(drop=True)


def precompute_smoke(panel: pd.DataFrame, candidates: pd.DataFrame, split: SplitSpec, output_dir: Path, universe_id: str, transaction_cost_bps: float, decimals: int = 10) -> tuple[pd.DataFrame, dict[str, object]]:
    prices, volumes = price_panel_to_matrices(panel)
    tv_mask = np.asarray(train_validation_mask(prices.index, split), dtype=bool)
    lock_mask = np.asarray(locked_test_mask(prices.index, split), dtype=bool)
    tv_dir = output_dir / "train_validation"
    lock_dir = output_dir / "locked_test"
    registry_rows = []
    signal_tv = []
    position_tv = []
    gross_tv = []
    net_tv = []
    turnover_tv = []
    cost_pnl_tv = []
    locked_signal = []
    locked_net = []
    diagnostic_rows = []
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    for _, row in candidates.iterrows():
        params = parse_parameters(row["parameter_json"])
        signal = compute_signal(row["operator_family"], params, prices, volumes)
        positions = signal_to_positions(signal)
        pnl = compute_candidate_pnl(positions, prices, transaction_cost_bps)
        tv_signal = signal.to_numpy()[tv_mask]
        tv_pos = positions.to_numpy()[tv_mask]
        tv_gross = pnl["gross_return"].to_numpy()[tv_mask]
        tv_net = pnl["net_return"].to_numpy()[tv_mask]
        tv_turn = pnl["turnover"].to_numpy()[tv_mask]
        tv_cost_pnl = pnl["cost_adjusted_pnl"].to_numpy()[tv_mask]
        signal_tv.append(tv_signal)
        position_tv.append(tv_pos)
        gross_tv.append(tv_gross)
        net_tv.append(tv_net)
        turnover_tv.append(tv_turn)
        cost_pnl_tv.append(tv_cost_pnl)
        locked_signal.append(signal.to_numpy()[lock_mask])
        locked_net.append(pnl["net_return"].to_numpy()[lock_mask])
        diagnostic_rows.append([float(np.nanmean(tv_net)), float(np.nanstd(tv_net)), float(np.nanmean(tv_turn))])

    matrices = {
        "signal_matrix": np.asarray(signal_tv),
        "position_matrix": np.asarray(position_tv),
        "gross_return_matrix": np.asarray(gross_tv),
        "net_return_matrix": np.asarray(net_tv),
        "turnover_matrix": np.asarray(turnover_tv),
        "cost_adjusted_pnl_matrix": np.asarray(cost_pnl_tv),
        "diagnostic_matrix": np.asarray(diagnostic_rows),
    }
    matrix_paths = {}
    for name, array in matrices.items():
        matrix_paths[name] = write_dense_matrix(output_dir / f"{name}.npy", array, {"matrix_name": name, "split": "train_validation", "universe_id": universe_id})
    locked_paths = [
        write_dense_matrix(lock_dir / "locked_signal_matrix.npy", np.asarray(locked_signal), {"matrix_name": "locked_signal_matrix", "split": "locked_test", "universe_id": universe_id}),
        write_dense_matrix(lock_dir / "locked_net_return_matrix.npy", np.asarray(locked_net), {"matrix_name": "locked_net_return_matrix", "split": "locked_test", "universe_id": universe_id}),
    ]
    policy = LockedTestAccessPolicy(tv_dir, lock_dir, allow_locked_read=False)
    write_access_report(output_dir.parent / "locked_test_access_report.md", policy, locked_paths)

    def rel(path: Path) -> str:
        return str(path.relative_to(output_dir.parents[2]))

    for idx, (_, row) in enumerate(candidates.iterrows()):
        params = parse_parameters(row["parameter_json"])
        registry_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "operator_family": row["operator_family"],
                "parameter_hash": parameter_hash(params, decimals=decimals),
                "signal_hash": hash_array(matrices["signal_matrix"][idx], decimals=decimals),
                "pnl_hash": hash_array(matrices["net_return_matrix"][idx], decimals=decimals),
                "turnover_hash": hash_array(matrices["turnover_matrix"][idx], decimals=decimals),
                "cost_pnl_hash": hash_array(matrices["cost_adjusted_pnl_matrix"][idx], decimals=decimals),
                "matrix_path_signal": rel(matrix_paths["signal_matrix"]),
                "matrix_path_pnl": rel(matrix_paths["net_return_matrix"]),
                "matrix_path_turnover": rel(matrix_paths["turnover_matrix"]),
                "matrix_path_cost_pnl": rel(matrix_paths["cost_adjusted_pnl_matrix"]),
                "created_at": created_at,
                "data_window_start": split.train_start,
                "data_window_end": split.validation_end,
                "universe_id": universe_id,
                "status": "smoke_precomputed",
                "uses_future_data": False,
                "notes": f"train_validation artifact in shared matrix row {idx}; locked-test artifacts physically separated and not used for diagnostics",
            }
        )
    registry = pd.DataFrame(registry_rows, columns=REGISTRY_COLUMNS)
    summary = {
        "candidate_count": int(len(candidates)),
        "asset_count": int(prices.shape[1]),
        "train_validation_days": int(tv_mask.sum()),
        "locked_test_days": int(lock_mask.sum()),
        "matrices": sorted(matrices),
        "locked_read_allowed_before_final": False,
    }
    return registry, summary
