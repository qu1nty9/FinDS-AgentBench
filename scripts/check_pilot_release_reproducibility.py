#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.release_reproducibility import (
    build_release_repro_paths,
    run_release_reproducibility_check,
    write_release_reproducibility_forensics,
)
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the pilot release twice on isolated roots and compare deterministic outputs."
    )
    parser.add_argument("--work-root", type=Path, default=Path("tmp/pilot_release_repro_check"))
    parser.add_argument("--forensics-output-dir", type=Path, default=None)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--market-seed", type=int, default=11)
    parser.add_argument("--event-seed", type=int, default=23)
    parser.add_argument("--treasury-seed", type=int, default=29)
    parser.add_argument("--curve-seed", type=int, default=31)
    parser.add_argument("--curve3mo-seed", type=int, default=33)
    parser.add_argument("--front-end-seed", type=int, default=31)
    parser.add_argument("--usd-seed", type=int, default=37)
    parser.add_argument(
        "--treasury-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument(
        "--curve-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument(
        "--curve3mo-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument(
        "--front-end-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument(
        "--usd-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    forensics_output_dir = args.forensics_output_dir or (args.work_root / "forensics")
    first_paths = build_release_repro_paths(args.work_root / "first")
    second_paths = build_release_repro_paths(args.work_root / "second")

    try:
        result = run_release_reproducibility_check(
            work_root=args.work_root,
            repeat=args.repeat,
            market_seed=args.market_seed,
            event_seed=args.event_seed,
            treasury_seed=args.treasury_seed,
            curve_seed=args.curve_seed,
            curve3mo_seed=args.curve3mo_seed,
            front_end_seed=args.front_end_seed,
            usd_seed=args.usd_seed,
            treasury_snapshot_date=args.treasury_snapshot_date,
            curve_snapshot_date=args.curve_snapshot_date,
            curve3mo_snapshot_date=args.curve3mo_snapshot_date,
            front_end_snapshot_date=args.front_end_snapshot_date,
            usd_snapshot_date=args.usd_snapshot_date,
        )
    except Exception as exc:
        forensics = write_release_reproducibility_forensics(
            first_paths=first_paths,
            second_paths=second_paths,
            output_dir=forensics_output_dir,
            failure_message=str(exc),
        )
        print("status: failed", file=sys.stderr)
        print(f"failure: {exc}", file=sys.stderr)
        print(f"forensics_summary_json: {forensics.summary_json_path}", file=sys.stderr)
        print(f"forensics_summary_markdown: {forensics.summary_markdown_path}", file=sys.stderr)
        raise

    forensics = write_release_reproducibility_forensics(
        first_paths=first_paths,
        second_paths=second_paths,
        output_dir=forensics_output_dir,
    )
    print("status: reproducible")
    print(f"first_root: {result.first_root}")
    print(f"second_root: {result.second_root}")
    print(f"compared_artifact_count: {result.compared_artifact_count}")
    print(f"forensics_summary_json: {forensics.summary_json_path}")
    print(f"forensics_summary_markdown: {forensics.summary_markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
