#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def probability_from_momentum(momentum_20d: float, volatility_10d: float) -> float:
    scaled = momentum_20d / max(volatility_10d, 1e-6)
    probability = 0.5 + max(min(0.04 * scaled, 0.2), -0.2)
    return min(max(probability, 0.05), 0.95)


def write_submission(features_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with features_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["row_id", "prediction", "probability"])
            writer.writeheader()
            for row in reader:
                probability = probability_from_momentum(
                    float(row["momentum_20d"]),
                    float(row["volatility_10d"]),
                )
                writer.writerow(
                    {
                        "row_id": row["row_id"],
                        "prediction": "1" if probability >= 0.5 else "0",
                        "probability": f"{probability:.8f}",
                    }
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write momentum baseline predictions.")
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/raw/synthetic_market_direction_v0/private_holdout_features.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/synthetic_market_direction_v0/momentum_baseline/predictions.csv"),
    )
    args = parser.parse_args()

    write_submission(args.features, args.output)
    print(f"Wrote predictions: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

