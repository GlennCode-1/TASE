from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def write_dense_matrix(path: Path, array: np.ndarray, metadata: dict[str, Any]) -> Path:
    if path.suffix.lower() == ".csv":
        raise ValueError("B1 forbids giant CSV for dense matrices")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, array)
    meta_path = path.with_suffix(path.suffix + ".metadata.json")
    meta = dict(metadata)
    meta["shape"] = list(array.shape)
    meta["dtype"] = str(array.dtype)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    return path


def matrix_exists(path: str | Path) -> bool:
    return Path(path).exists()
