#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.pipelines import (
    DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    run_pilot_baseline_suite,
)
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all implemented pilot baseline experiments with repeated seeds."
    )
    parser.add_argument("--market-seed", type=int, default=11)
    parser.add_argument("--event-seed", type=int, default=23)
    parser.add_argument("--treasury-seed", type=int, default=29)
    parser.add_argument("--curve-seed", type=int, default=31)
    parser.add_argument("--curve3mo-seed", type=int, default=33)
    parser.add_argument("--front-end-seed", type=int, default=31)
    parser.add_argument("--usd-seed", type=int, default=37)
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
        "--treasury-task",
        type=Path,
        default=Path("tasks/pilot/yield_direction_treasury10y_v0.yaml"),
    )
    parser.add_argument(
        "--curve-task",
        type=Path,
        default=Path("tasks/pilot/yield_curve_10y2y_steepening_v0.yaml"),
    )
    parser.add_argument(
        "--curve3mo-task",
        type=Path,
        default=Path("tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml"),
    )
    parser.add_argument(
        "--front-end-task",
        type=Path,
        default=Path("tasks/pilot/front_end_spread_widening_v0.yaml"),
    )
    parser.add_argument(
        "--usd-task",
        type=Path,
        default=Path("tasks/pilot/usd_broad_direction_v0.yaml"),
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
        "--treasury-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_direction_treasury10y_v0"),
    )
    parser.add_argument(
        "--treasury-private-dir",
        type=Path,
        default=Path("data/private/yield_direction_treasury10y_v0"),
    )
    parser.add_argument(
        "--curve-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_curve_10y2y_steepening_v0"),
    )
    parser.add_argument(
        "--curve-private-dir",
        type=Path,
        default=Path("data/private/yield_curve_10y2y_steepening_v0"),
    )
    parser.add_argument(
        "--curve3mo-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_curve_10y3mo_steepening_v0"),
    )
    parser.add_argument(
        "--curve3mo-private-dir",
        type=Path,
        default=Path("data/private/yield_curve_10y3mo_steepening_v0"),
    )
    parser.add_argument(
        "--front-end-data-output-dir",
        type=Path,
        default=Path("data/raw/front_end_spread_widening_v0"),
    )
    parser.add_argument(
        "--front-end-private-dir",
        type=Path,
        default=Path("data/private/front_end_spread_widening_v0"),
    )
    parser.add_argument(
        "--usd-data-output-dir",
        type=Path,
        default=Path("data/raw/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--usd-private-dir",
        type=Path,
        default=Path("data/private/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path(DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT),
    )
    parser.add_argument("--clean-existing-runs", action="store_true")
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
        "--treasury-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--treasury-api-key", default=None)
    parser.add_argument(
        "--curve-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--curve-api-key", default=None)
    parser.add_argument(
        "--curve3mo-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--curve3mo-api-key", default=None)
    parser.add_argument(
        "--front-end-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--front-end-api-key", default=None)
    parser.add_argument(
        "--usd-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--usd-api-key", default=None)
    parser.add_argument("--execute-notebook", action="store_true")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    result = run_pilot_baseline_suite(
        market_seed=args.market_seed,
        event_seed=args.event_seed,
        treasury_seed=args.treasury_seed,
        curve_seed=args.curve_seed,
        curve3mo_seed=args.curve3mo_seed,
        front_end_seed=args.front_end_seed,
        usd_seed=args.usd_seed,
        repeat=args.repeat,
        run_label_prefix=args.run_label_prefix,
        market_task_path=args.market_task,
        event_task_path=args.event_task,
        treasury_task_path=args.treasury_task,
        curve_task_path=args.curve_task,
        curve3mo_task_path=args.curve3mo_task,
        front_end_task_path=args.front_end_task,
        usd_task_path=args.usd_task,
        market_data_output_dir=args.market_data_output_dir,
        market_private_dir=args.market_private_dir,
        event_data_output_dir=args.event_data_output_dir,
        event_private_dir=args.event_private_dir,
        treasury_data_output_dir=args.treasury_data_output_dir,
        treasury_private_dir=args.treasury_private_dir,
        curve_data_output_dir=args.curve_data_output_dir,
        curve_private_dir=args.curve_private_dir,
        curve3mo_data_output_dir=args.curve3mo_data_output_dir,
        curve3mo_private_dir=args.curve3mo_private_dir,
        front_end_data_output_dir=args.front_end_data_output_dir,
        front_end_private_dir=args.front_end_private_dir,
        usd_data_output_dir=args.usd_data_output_dir,
        usd_private_dir=args.usd_private_dir,
        runs_root=args.runs_root,
        clean_existing_runs=args.clean_existing_runs,
        report_csv_path=args.report_csv,
        report_markdown_path=args.report_markdown,
        summary_csv_path=args.summary_csv,
        summary_markdown_path=args.summary_markdown,
        execute_notebook=args.execute_notebook,
        command=" ".join(sys.argv),
        treasury_snapshot_date=args.treasury_snapshot_date,
        treasury_api_key=args.treasury_api_key,
        curve_snapshot_date=args.curve_snapshot_date,
        curve_api_key=args.curve_api_key,
        curve3mo_snapshot_date=args.curve3mo_snapshot_date,
        curve3mo_api_key=args.curve3mo_api_key,
        front_end_snapshot_date=args.front_end_snapshot_date,
        front_end_api_key=args.front_end_api_key,
        usd_snapshot_date=args.usd_snapshot_date,
        usd_api_key=args.usd_api_key,
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
