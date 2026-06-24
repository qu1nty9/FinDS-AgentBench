#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.treasury import (
    DEFAULT_OBSERVATION_END,
    DEFAULT_OBSERVATION_START,
    DEFAULT_REALTIME_SNAPSHOT_DATE,
    write_yield_direction_task,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and build the yield_direction_treasury10y_v0 task data."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/yield_direction_treasury10y_v0"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("data/private/yield_direction_treasury10y_v0"),
    )
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument("--observation-start", type=str, default=DEFAULT_OBSERVATION_START)
    parser.add_argument("--observation-end", type=str, default=DEFAULT_OBSERVATION_END)
    parser.add_argument(
        "--snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
        help="Vintage freeze date for ALFRED/FRED realtime retrieval.",
    )
    args = parser.parse_args()

    paths = write_yield_direction_task(
        output_dir=args.output_dir,
        private_dir=args.private_dir,
        api_key=args.api_key,
        observation_start=args.observation_start,
        observation_end=args.observation_end,
        snapshot_date=args.snapshot_date,
    )
    print(f"train_public: {paths.train_public}")
    print(f"private_holdout_features: {paths.private_holdout_features}")
    print(f"sample_submission: {paths.sample_submission}")
    print(f"metadata: {paths.metadata}")
    print(f"answer_key: {paths.answer_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
