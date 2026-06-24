#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.curve_10y3mo import write_curve_extra_trees_submission_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write extra trees artifacts for yield_curve_10y3mo_steepening_v0."
    )
    parser.add_argument(
        "--train-public",
        type=Path,
        default=Path("data/raw/yield_curve_10y3mo_steepening_v0/train_public.csv"),
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/raw/yield_curve_10y3mo_steepening_v0/private_holdout_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/yield_curve_10y3mo_steepening_v0/extra_trees_baseline"),
    )
    parser.add_argument("--random-state", type=int, default=41)
    args = parser.parse_args()

    metadata = write_curve_extra_trees_submission_artifacts(
        train_public_path=args.train_public,
        holdout_features_path=args.features,
        output_dir=args.output_dir,
        random_state=args.random_state,
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
