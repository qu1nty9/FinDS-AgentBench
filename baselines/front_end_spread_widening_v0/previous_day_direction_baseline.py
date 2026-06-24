#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.front_end import write_front_end_previous_day_direction_submission_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write previous-day direction rule artifacts for front_end_spread_widening_v0."
    )
    parser.add_argument(
        "--train-public",
        type=Path,
        default=Path("data/raw/front_end_spread_widening_v0/train_public.csv"),
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/raw/front_end_spread_widening_v0/private_holdout_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/front_end_spread_widening_v0/previous_day_direction_baseline"),
    )
    args = parser.parse_args()

    metadata = write_front_end_previous_day_direction_submission_artifacts(
        train_public_path=args.train_public,
        holdout_features_path=args.features,
        output_dir=args.output_dir,
    )
    print(f"Wrote submission artifacts: {args.output_dir}")
    print(f"Selected threshold: {metadata['selected_threshold']}")
    print(
        "Public validation balanced accuracy: "
        f"{metadata['public_validation_balanced_accuracy']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
