#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.pipelines import (
    DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    run_pilot_baseline_suite,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all implemented pilot baseline experiments with repeated seeds."
    )
    parser.add_argument("--market-seed", type=int, default=11)
    parser.add_argument("--event-seed", type=int, default=23)
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Number of repeated seeds per baseline. Seeds are seed + repeat_index.",
    )
    parser.add_argument("--run-label-prefix", default="pilot")
    parser.add_argument(
        "--market-task",
        type=Path,
        default=Path("tasks/pilot/synthetic_market_direction_v0.yaml"),
    )
    parser.add_argument(
        "--event-task",
        type=Path,
        default=Path("tasks/pilot/synthetic_event_response_v0.yaml"),
    )
    parser.add_argument(
        "--market-data-output-dir",
        type=Path,
        default=Path("data/raw/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--market-private-dir",
        type=Path,
        default=Path("data/private/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--event-data-output-dir",
        type=Path,
        default=Path("data/raw/synthetic_event_response_v0"),
    )
    parser.add_argument(
        "--event-private-dir",
        type=Path,
        default=Path("data/private/synthetic_event_response_v0"),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path(DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT),
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
    parser.add_argument("--execute-notebook", action="store_true")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    result = run_pilot_baseline_suite(
        market_seed=args.market_seed,
        event_seed=args.event_seed,
        repeat=args.repeat,
        run_label_prefix=args.run_label_prefix,
        market_task_path=args.market_task,
        event_task_path=args.event_task,
        market_data_output_dir=args.market_data_output_dir,
        market_private_dir=args.market_private_dir,
        event_data_output_dir=args.event_data_output_dir,
        event_private_dir=args.event_private_dir,
        runs_root=args.runs_root,
        report_csv_path=args.report_csv,
        report_markdown_path=args.report_markdown,
        summary_csv_path=args.summary_csv,
        summary_markdown_path=args.summary_markdown,
        execute_notebook=args.execute_notebook,
        command=" ".join(sys.argv),
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
