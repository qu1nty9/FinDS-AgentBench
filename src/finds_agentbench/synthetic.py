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

