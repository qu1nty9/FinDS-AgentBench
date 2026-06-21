#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.synthetic import write_synthetic_event_response_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic_event_response_v0 data.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/synthetic_event_response_v0"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("data/private/synthetic_event_response_v0"),
    )
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()

    paths = write_synthetic_event_response_task(
        output_dir=args.output_dir,
        private_dir=args.private_dir,
        seed=args.seed,
    )
    print(f"Wrote train/public data: {paths.train_public}")
    print(f"Wrote private holdout features: {paths.private_holdout_features}")
    print(f"Wrote sample submission: {paths.sample_submission}")
    print(f"Wrote metadata: {paths.metadata}")
    print(f"Wrote private answer key: {paths.answer_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
