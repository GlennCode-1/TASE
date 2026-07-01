from __future__ import annotations

import numpy as np

from src.direction_a.hashing import hash_array, hash_object, parameter_hash


def test_same_array_same_hash() -> None:
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert hash_array(arr) == hash_array(arr.copy())


def test_small_floating_formatting_deterministic() -> None:
    assert hash_array([1.000000000001], decimals=10) == hash_array([1.0], decimals=10)


def test_changed_array_changed_hash() -> None:
    assert hash_array([1.0, 2.0]) != hash_array([1.0, 2.1])


def test_row_order_controlled_when_requested() -> None:
    left = np.array([[2.0, 1.0], [1.0, 2.0]])
    right = np.array([[1.0, 2.0], [2.0, 1.0]])
    assert hash_array(left, sort_rows=True) == hash_array(right, sort_rows=True)
    assert hash_array(left, sort_rows=False) != hash_array(right, sort_rows=False)


def test_parameter_hash_sorts_keys() -> None:
    assert parameter_hash({"b": 2, "a": 1}) == hash_object({"a": 1, "b": 2})
