from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


FUTURE_FIELDS = ("future_ret_1d", "next_day_direction")


@dataclass(frozen=True)
class DataBundle:
    data: pd.DataFrame
    split_days: dict[str, set[int]]
    future_fields: tuple[str, ...] = FUTURE_FIELDS

    def split(self, name: str) -> pd.DataFrame:
        if name not in self.split_days:
            raise KeyError(f"unknown split: {name}")
        return self.data[self.data["split"] == name].copy()

    def available_feature_columns(self, split: str | None = None) -> list[str]:
        cols = [
            "signal",
            "regime_b",
            "volatility",
            "risk_flag",
            "spurious_feature",
            "missing_data",
            "high_vol_day",
            "crash_day",
        ]
        return [col for col in cols if col not in self.future_fields]

    def is_feature_available_at_decision_time(self, field: str) -> bool:
        return field not in self.future_fields


def _split_for_day(day: int, train_days: int, val_days: int) -> str:
    if day < train_days:
        return "train"
    if day < train_days + val_days:
        return "validation"
    return "test"


def _build_split_days(train_days: int, val_days: int, test_days: int) -> dict[str, set[int]]:
    train = set(range(train_days))
    val = set(range(train_days, train_days + val_days))
    test = set(range(train_days + val_days, train_days + val_days + test_days))
    return {"train": train, "validation": val, "test": test}


def generate_synthetic_data(config: dict, seed: int) -> DataBundle:
    rng = np.random.default_rng(seed)
    n_assets = int(config["n_assets"])
    train_days = int(config["train_days"])
    val_days = int(config["val_days"])
    test_days = int(config["test_days"])
    total_days = train_days + val_days + test_days

    rows: list[dict] = []
    asset_quality = rng.normal(0.0, 0.35, size=n_assets)
    market_noise = rng.normal(0.0, 0.006, size=total_days)

    for day in range(total_days):
        split = _split_for_day(day, train_days, val_days)
        day_in_split = (
            day
            if split == "train"
            else day - train_days
            if split == "validation"
            else day - train_days - val_days
        )

        if split == "test":
            regime_b = rng.random() < 0.78
            high_vol_day = rng.random() < 0.24
            crash_day = rng.random() < 0.12
            missing_data = rng.random() < 0.10
        elif split == "validation":
            regime_b = rng.random() < 0.16
            high_vol_day = rng.random() < 0.12
            crash_day = rng.random() < 0.05
            missing_data = rng.random() < 0.07
        else:
            regime_b = rng.random() < 0.10
            high_vol_day = rng.random() < 0.10
            crash_day = rng.random() < 0.04
            missing_data = rng.random() < 0.06

        volatility = 0.010 + (0.014 if high_vol_day else 0.0) + (0.010 if regime_b else 0.0)
        risk_flag = high_vol_day or crash_day or missing_data
        validation_wave = np.sin(day_in_split / 7.0) + 0.4 * np.cos(day_in_split / 17.0)

        for asset in range(n_assets):
            signal = rng.normal(asset_quality[asset], 1.0)
            spurious_feature = validation_wave + rng.normal(0.0, 0.35)
            if asset % 2:
                spurious_feature *= -1.0

            stable_alpha = 0.0012 * signal
            if split == "validation":
                spurious_alpha = 0.0060 * spurious_feature
            elif split == "test":
                spurious_alpha = -0.0055 * spurious_feature
            else:
                spurious_alpha = 0.0005 * spurious_feature

            regime_drag = -0.0007 if regime_b else 0.0002
            crash_drag = -0.030 if crash_day else 0.0
            if crash_day:
                # On crash days the ordinary signal is deliberately misleading.
                stable_alpha = -abs(stable_alpha) - 0.001

            ret = (
                stable_alpha
                + spurious_alpha
                + regime_drag
                + crash_drag
                + market_noise[day]
                + rng.normal(0.0, volatility)
            )

            future_ret = ret if split != "test" else np.nan
            next_dir = np.sign(ret) if split != "test" else np.nan

            rows.append(
                {
                    "day": day,
                    "asset": asset,
                    "split": split,
                    "return_1d": ret,
                    "signal": signal,
                    "regime_b": float(regime_b),
                    "volatility": volatility,
                    "risk_flag": bool(risk_flag),
                    "spurious_feature": spurious_feature,
                    "future_ret_1d": future_ret,
                    "next_day_direction": next_dir,
                    "missing_data": bool(missing_data),
                    "high_vol_day": bool(high_vol_day),
                    "crash_day": bool(crash_day),
                }
            )

    data = pd.DataFrame(rows)
    split_days = _build_split_days(train_days, val_days, test_days)
    return DataBundle(data=data, split_days=split_days)


def assert_no_split_overlap(split_days: dict[str, Iterable[int]]) -> None:
    names = list(split_days)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            overlap = set(split_days[left]).intersection(split_days[right])
            if overlap:
                raise AssertionError(f"{left} overlaps {right}: {sorted(overlap)[:5]}")
