#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.pipelines import (
    DEFAULT_USD_BROAD_SUITE_RUNS_ROOT,
    run_usd_broad_direction_v0_baseline_suite,
)
from finds_agentbench.usd_broad import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run repeated baseline experiments for usd_broad_direction_v0."
    )
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Number of repeated seeds per baseline. Seeds are seed + repeat_index.",
    )
    parser.add_argument("--run-label-prefix", default="pilot")
    parser.add_argument(
        "--task",
        type=Path,
        default=Path("tasks/pilot/usd_broad_direction_v0.yaml"),
    )
    parser.add_argument(
        "--data-output-dir",
        type=Path,
        default=Path("data/raw/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("data/private/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path(DEFAULT_USD_BROAD_SUITE_RUNS_ROOT),
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        default=Path("reports/generated/run_results.csv"),
    )
    parser.add_argument(
        "--report-markdown",
        type=Path,
        default=Path("reports/generated/run_results.md"),
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("reports/generated/run_summary.csv"),
    )
    parser.add_argument(
        "--summary-markdown",
        type=Path,
        default=Path("reports/generated/run_summary.md"),
    )
    parser.add_argument(
        "--snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--execute-notebook", action="store_true")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    result = run_usd_broad_direction_v0_baseline_suite(
        seed=args.seed,
        repeat=args.repeat,
        run_label_prefix=args.run_label_prefix,
        task_path=args.task,
        data_output_dir=args.data_output_dir,
        private_dir=args.private_dir,
        runs_root=args.runs_root,
        report_csv_path=args.report_csv,
        report_markdown_path=args.report_markdown,
        summary_csv_path=args.summary_csv,
        summary_markdown_path=args.summary_markdown,
        execute_notebook=args.execute_notebook,
        command=" ".join(sys.argv),
        snapshot_date=args.snapshot_date,
        api_key=args.api_key,
    )

    for index, pipeline_result in enumerate(result.results, start=1):
        total = len(result.results)
        print(f"[{index}/{total}] status: {pipeline_result.status}")
        print(f"[{index}/{total}] run_dir: {pipeline_result.run_dir}")
        print(f"[{index}/{total}] manifest: {pipeline_result.manifest_path}")

    print(f"status: {result.status}")
    print(f"report_csv: {result.report_csv_path}")
    print(f"report_markdown: {result.report_markdown_path}")
    print(f"summary_csv: {result.summary_csv_path}")
    print(f"summary_markdown: {result.summary_markdown_path}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
