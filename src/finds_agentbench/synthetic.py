from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class LeakageAuditPaths:
    public_panel: Path
    flawed_workflow: Path
    answer_key: Path


@dataclass(frozen=True)
class SyntheticMarketPaths:
    train_public: Path
    private_holdout_features: Path
    sample_submission: Path
    metadata: Path
    answer_key: Path


def business_dates(start: date, periods: int) -> list[date]:
    """Return the first `periods` weekdays at or after `start`."""
    values: list[date] = []
    current = start
    while len(values) < periods:
        if current.weekday() < 5:
            values.append(current)
        current += timedelta(days=1)
    return values


def split_for_date(value: date) -> str:
    if value <= date(2020, 12, 31):
        return "train"
    if value <= date(2021, 6, 30):
        return "public_validation"
    return "private_temporal_holdout"


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def generate_leakage_audit_rows(
    *,
    seed: int = 7,
    n_assets: int = 8,
    n_periods: int = 520,
) -> list[dict[str, str]]:
    """Generate a synthetic financial panel with controlled leakage traps.

    The legitimate signal is useful but noisy. The future leak is intentionally
    target-derived and should be removed by a correct audit.
    """
    rng = random.Random(seed)
    dates = business_dates(date(2020, 1, 2), n_periods)
    rows: list[dict[str, str]] = []

    latent_by_asset = {f"asset_{idx:02d}": rng.gauss(0, 0.4) for idx in range(n_assets)}
    asset_bias = {asset: rng.gauss(0, 0.25) for asset in latent_by_asset}

    for current_date in dates:
        regime = -0.35 if date(2020, 3, 2) <= current_date <= date(2020, 5, 29) else 0.15
        for asset_id in sorted(latent_by_asset):
            previous_latent = latent_by_asset[asset_id]
            latent = 0.82 * previous_latent + rng.gauss(0, 0.45)
            latent_by_asset[asset_id] = latent

            lagged_signal = previous_latent + rng.gauss(0, 0.25)
            noise_feature = rng.gauss(0, 1.0)
            probability = sigmoid(1.15 * lagged_signal + 0.55 * regime + asset_bias[asset_id])
            target = 1 if rng.random() < probability else 0

            future_return_proxy = (2 * target - 1) + rng.gauss(0, 0.08)
            rows.append(
                {
                    "row_id": f"{current_date.isoformat()}_{asset_id}",
                    "date": current_date.isoformat(),
                    "asset_id": asset_id,
                    "split": split_for_date(current_date),
                    "feature_lagged_signal": f"{lagged_signal:.8f}",
                    "feature_noise": f"{noise_feature:.8f}",
                    "feature_future_return_leak": f"{future_return_proxy:.8f}",
                    "target": str(target),
                }
            )

    return rows


def write_leakage_audit_task(
    *,
    output_dir: str | Path = "data/raw/leakage_audit_temporal_split_v0",
    private_dir: str | Path = "data/private/leakage_audit_temporal_split_v0",
    seed: int = 7,
) -> LeakageAuditPaths:
    output_path = Path(output_dir)
    private_path = Path(private_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    rows = generate_leakage_audit_rows(seed=seed)
    public_panel = output_path / "panel.csv"
    flawed_workflow = output_path / "flawed_workflow.json"
    answer_key = private_path / "answer_key.json"

    fieldnames = [
        "row_id",
        "date",
        "asset_id",
        "split",
        "feature_lagged_signal",
        "feature_noise",
        "feature_future_return_leak",
        "target",
    ]
    with public_panel.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    flawed_metadata = {
        "task_id": "leakage_audit_temporal_split_v0",
        "seed": seed,
        "flawed_workflow": {
            "split_strategy": "random_row_split",
            "preprocessing": "standard_scaler_fit_on_full_dataset",
            "features": [
                "feature_lagged_signal",
                "feature_noise",
                "feature_future_return_leak",
            ],
            "target": "target",
        },
        "intended_fix": {
            "split_strategy": "chronological_split_using_split_column",
            "preprocessing": "fit_transform_train_only_then_transform_validation",
            "drop_features": ["feature_future_return_leak"],
        },
    }
    flawed_workflow.write_text(json.dumps(flawed_metadata, indent=2) + "\n", encoding="utf-8")

    answer = {
        "task_id": "leakage_audit_temporal_split_v0",
        "required_findings": [
            {
                "id": "future_feature_leak",
                "description": "feature_future_return_leak is target-derived future information.",
                "required_terms": ["feature_future_return_leak"],
                "support_terms_any": ["future", "leak", "target-derived", "unavailable"],
            },
            {
                "id": "random_temporal_split",
                "description": "Random row split is invalid for temporal financial data.",
                "required_terms": ["random"],
                "support_terms_any": ["temporal", "chronological", "time"],
            },
            {
                "id": "full_dataset_preprocessing",
                "description": "Preprocessing fit on the full dataset leaks validation information.",
                "required_terms": ["full dataset"],
                "support_terms_any": ["scaler", "preprocessing", "fit"],
            },
        ],
        "expected_metric_direction": {
            "metric_any_of": ["auc", "accuracy", "balanced_accuracy"],
            "flawed_should_exceed_corrected_by_at_least": 0.05,
        },
    }
    answer_key.write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")

    return LeakageAuditPaths(
        public_panel=public_panel,
        flawed_workflow=flawed_workflow,
        answer_key=answer_key,
    )


def predictive_split_for_date(value: date) -> str:
    if value <= date(2020, 12, 31):
        return "train"
    if value <= date(2021, 6, 30):
        return "public_validation"
    return "private_temporal_holdout"


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = mean(values)
    variance = sum((value - center) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def generate_synthetic_market_rows(
    *,
    seed: int = 11,
    n_assets: int = 10,
    n_periods: int = 760,
) -> list[dict[str, str]]:
    """Generate a point-in-time synthetic market direction task."""
    rng = random.Random(seed)
    dates = business_dates(date(2019, 1, 2), n_periods)
    returns_by_asset: dict[str, list[float]] = {}

    for asset_idx in range(n_assets):
        asset_id = f"asset_{asset_idx:02d}"
        latent = rng.gauss(0, 0.2)
        asset_bias = rng.gauss(0, 0.0005)
        asset_returns: list[float] = []

        for current_date in dates:
            shock_regime = -0.006 if date(2020, 3, 2) <= current_date <= date(2020, 5, 29) else 0.001
            latent = 0.88 * latent + rng.gauss(0, 0.35)
            expected_return = asset_bias + 0.0035 * latent + shock_regime
            realized_return = expected_return + rng.gauss(0, 0.018)
            asset_returns.append(realized_return)

        returns_by_asset[asset_id] = asset_returns

    rows: list[dict[str, str]] = []
    for asset_id, asset_returns in sorted(returns_by_asset.items()):
        for idx in range(20, len(dates) - 1):
            current_date = dates[idx]
            ret_1d = asset_returns[idx]
            ret_5d = sum(asset_returns[idx - 4 : idx + 1])
            momentum_20d = sum(asset_returns[idx - 19 : idx + 1])
            volatility_10d = std(asset_returns[idx - 9 : idx + 1])
            market_regime_proxy = -1.0 if date(2020, 3, 2) <= current_date <= date(2020, 5, 29) else 1.0
            next_return = asset_returns[idx + 1]
            target = 1 if next_return > 0 else 0
            split = predictive_split_for_date(current_date)

            rows.append(
                {
                    "row_id": f"{current_date.isoformat()}_{asset_id}",
                    "date": current_date.isoformat(),
                    "asset_id": asset_id,
                    "split": split,
                    "ret_1d": f"{ret_1d:.8f}",
                    "ret_5d": f"{ret_5d:.8f}",
                    "momentum_20d": f"{momentum_20d:.8f}",
                    "volatility_10d": f"{volatility_10d:.8f}",
                    "market_regime_proxy": f"{market_regime_proxy:.1f}",
                    "next_day_positive_return": str(target),
                    "next_day_return": f"{next_return:.8f}",
                }
            )

    return rows


def write_synthetic_market_direction_task(
    *,
    output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    seed: int = 11,
) -> SyntheticMarketPaths:
    output_path = Path(output_dir)
    private_path = Path(private_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    rows = generate_synthetic_market_rows(seed=seed)
    train_public = output_path / "train_public.csv"
    holdout_features = output_path / "private_holdout_features.csv"
    sample_submission = output_path / "sample_submission.csv"
    metadata = output_path / "metadata.json"
    answer_key = private_path / "answer_key.csv"

    feature_fields = [
        "row_id",
        "date",
        "asset_id",
        "split",
        "ret_1d",
        "ret_5d",
        "momentum_20d",
        "volatility_10d",
        "market_regime_proxy",
    ]
    public_fields = feature_fields + ["next_day_positive_return", "next_day_return"]
    answer_fields = ["row_id", "date", "asset_id", "next_day_positive_return", "next_day_return"]

    public_rows = [row for row in rows if row["split"] != "private_temporal_holdout"]
    holdout_rows = [row for row in rows if row["split"] == "private_temporal_holdout"]

    with train_public.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=public_fields)
        writer.writeheader()
        writer.writerows(public_rows)

    with holdout_features.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=feature_fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in feature_fields} for row in holdout_rows)

    with sample_submission.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "prediction", "probability"])
        writer.writeheader()
        for row in holdout_rows:
            writer.writerow({"row_id": row["row_id"], "prediction": "0", "probability": "0.5"})

    with answer_key.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=answer_fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in answer_fields} for row in holdout_rows)

    metadata.write_text(
        json.dumps(
            {
                "task_id": "synthetic_market_direction_v0",
                "seed": seed,
                "splits": {
                    "train": {"start": "2019-01-30", "end": "2020-12-31"},
                    "public_validation": {"start": "2021-01-01", "end": "2021-06-30"},
                    "private_temporal_holdout": {"start": "2021-07-01", "end": "2021-11-29"},
                },
                "target": "next_day_positive_return",
                "forbidden_private_columns": [
                    "next_day_positive_return",
                    "next_day_return",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return SyntheticMarketPaths(
        train_public=train_public,
        private_holdout_features=holdout_features,
        sample_submission=sample_submission,
        metadata=metadata,
        answer_key=answer_key,
    )

