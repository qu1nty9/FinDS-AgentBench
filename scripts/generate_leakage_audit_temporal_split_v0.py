#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.synthetic import write_leakage_audit_task


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for leakage_audit_temporal_split_v0."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/leakage_audit_temporal_split_v0"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("data/private/leakage_audit_temporal_split_v0"),
    )
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    paths = write_leakage_audit_task(
        output_dir=args.output_dir,
        private_dir=args.private_dir,
        seed=args.seed,
    )
    print(f"Wrote public panel: {paths.public_panel}")
    print(f"Wrote flawed workflow: {paths.flawed_workflow}")
    print(f"Wrote private answer key: {paths.answer_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

