from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd


def _normalize(obj: Any, decimals: int) -> Any:
    if isinstance(obj, float):
        return round(obj, decimals)
    if isinstance(obj, (np.floating,)):
        return round(float(obj), decimals)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, dict):
        return {str(key): _normalize(obj[key], decimals) for key in sorted(obj)}
    if isinstance(obj, (list, tuple)):
        return [_normalize(value, decimals) for value in obj]
    if obj is pd.NA:
        return None
    return obj


def deterministic_json(obj: Any, decimals: int = 10) -> str:
    return json.dumps(_normalize(obj, decimals), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_object(obj: Any, decimals: int = 10) -> str:
    return sha256_text(deterministic_json(obj, decimals=decimals))


def hash_array(array: Any, decimals: int = 10, sort_rows: bool = False) -> str:
    arr = np.asarray(array)
    if np.issubdtype(arr.dtype, np.number):
        arr = np.round(arr.astype(float), decimals)
    if sort_rows:
        if arr.ndim == 1:
            arr = np.sort(arr)
        elif arr.ndim == 2:
            order = np.lexsort(tuple(arr[:, col] for col in range(arr.shape[1] - 1, -1, -1)))
            arr = arr[order]
        else:
            raise ValueError("sort_rows only supports 1D or 2D arrays")
    return hash_object(arr.tolist(), decimals=decimals)


def parameter_hash(parameters: dict[str, Any], decimals: int = 10) -> str:
    return hash_object(parameters, decimals=decimals)
