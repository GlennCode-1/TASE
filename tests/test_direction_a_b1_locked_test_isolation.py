from __future__ import annotations

from pathlib import Path

import pytest

from src.direction_a.locked_test_store import LockedTestAccessPolicy
from src.direction_a.split_manager import build_split_spec, locked_test_mask, train_validation_mask


def test_locked_test_path_marked_inaccessible_before_final(tmp_path: Path) -> None:
    tv = tmp_path / "train_validation"
    locked = tmp_path / "locked_test"
    tv.mkdir(); locked.mkdir()
    policy = LockedTestAccessPolicy(tv, locked, allow_locked_read=False)
    with pytest.raises(PermissionError):
        policy.assert_can_read(locked / "secret.npy")


def test_train_validation_path_can_be_read(tmp_path: Path) -> None:
    tv = tmp_path / "train_validation"
    locked = tmp_path / "locked_test"
    tv.mkdir(); locked.mkdir()
    LockedTestAccessPolicy(tv, locked, allow_locked_read=False).assert_can_read(tv / "matrix.npy")


def test_split_masks_separate_locked_test() -> None:
    spec = build_split_spec("2018-01-01", "2020-12-31", "2020-01-01", "2020-12-31")
    dates = ["2019-12-31", "2020-01-02"]
    assert list(train_validation_mask(dates, spec)) == [True, False]
    assert list(locked_test_mask(dates, spec)) == [False, True]
