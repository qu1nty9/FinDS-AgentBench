#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.baselines import write_event_rule_submission_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Write event-rule baseline submission artifacts.")
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/raw/synthetic_event_response_v0/private_holdout_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/synthetic_event_response_v0/event_rule_baseline"),
    )
    args = parser.parse_args()

    write_event_rule_submission_artifacts(args.features, args.output_dir)
    print(f"Wrote submission artifacts: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
