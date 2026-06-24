#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.usd_relative import write_usd_relative_logistic_submission_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write logistic regression artifacts for usd_afe_vs_eme_relative_direction_v0."
    )
    parser.add_argument(
        "--train-public",
        type=Path,
        default=Path("data/raw/usd_afe_vs_eme_relative_direction_v0/train_public.csv"),
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/raw/usd_afe_vs_eme_relative_direction_v0/private_holdout_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/usd_afe_vs_eme_relative_direction_v0/logistic_regression_baseline"),
    )
    parser.add_argument("--random-state", type=int, default=29)
    args = parser.parse_args()

    metadata = write_usd_relative_logistic_submission_artifacts(
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
