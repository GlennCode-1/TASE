from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.direction_a.hashing import hash_array
from src.direction_a.matrix_store import matrix_exists, write_dense_matrix


def test_no_giant_csv_for_dense_matrices(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_dense_matrix(tmp_path / "matrix.csv", np.zeros((2, 2)), {})


def test_npy_and_metadata_created(tmp_path: Path) -> None:
    path = write_dense_matrix(tmp_path / "matrix.npy", np.ones((2, 3)), {"name": "smoke"})
    assert path.exists()
    assert Path(str(path) + ".metadata.json").exists()


def test_hash_contract_changed_matrix_changes_hash() -> None:
    assert hash_array(np.array([1.0, 2.0])) != hash_array(np.array([1.0, 2.1]))


def test_registry_contains_required_fields_if_generated() -> None:
    path = Path("outputs/direction_a_b1/registry/candidate_registry_smoke.csv")
    if not path.exists():
        return
    registry = pd.read_csv(path)
    required = {"candidate_id", "signal_hash", "pnl_hash", "turnover_hash", "cost_pnl_hash", "matrix_path_signal"}
    assert required.issubset(registry.columns)
    assert registry[["signal_hash", "pnl_hash", "turnover_hash", "cost_pnl_hash"]].notna().all().all()
    assert all(matrix_exists(path) for path in registry["matrix_path_signal"].head(5))
