from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SplitSpec:
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    locked_test_start: str
    locked_test_end: str
    locked_test_inaccessible_before_final: bool = True
    future_nested_expanding_walkforward_placeholder: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def build_split_spec(date_start: str, date_end: str, locked_start: str, locked_end: str) -> SplitSpec:
    start = pd.Timestamp(date_start)
    locked = pd.Timestamp(locked_start)
    validation_start = max(start, locked - pd.DateOffset(years=1))
    train_end = validation_start - pd.offsets.BDay(1)
    validation_end = locked - pd.offsets.BDay(1)
    return SplitSpec(
        train_start=str(start.date()),
        train_end=str(pd.Timestamp(train_end).date()),
        validation_start=str(pd.Timestamp(validation_start).date()),
        validation_end=str(pd.Timestamp(validation_end).date()),
        locked_test_start=str(pd.Timestamp(locked_start).date()),
        locked_test_end=str(pd.Timestamp(locked_end).date()),
    )


def write_split_spec(spec: SplitSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")


def train_validation_mask(dates, spec: SplitSpec):
    dates = pd.to_datetime(dates)
    return (dates >= pd.Timestamp(spec.train_start)) & (dates <= pd.Timestamp(spec.validation_end))


def locked_test_mask(dates, spec: SplitSpec):
    dates = pd.to_datetime(dates)
    return (dates >= pd.Timestamp(spec.locked_test_start)) & (dates <= pd.Timestamp(spec.locked_test_end))
