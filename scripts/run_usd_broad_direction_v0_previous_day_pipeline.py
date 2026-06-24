#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.pipelines import run_usd_broad_direction_v0_previous_day_pipeline
from finds_agentbench.usd_broad import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the usd_broad_direction_v0 previous-day rule baseline end to end."
    )
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--run-label", default=None)
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
        "--run-dir",
        type=Path,
        default=Path("runs/usd_broad_direction_v0/previous_day_direction_baseline"),
    )
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    parser.add_argument("--report-csv", type=Path, default=Path("reports/generated/run_results.csv"))
    parser.add_argument(
        "--report-markdown",
        type=Path,
        default=Path("reports/generated/run_results.md"),
    )
    parser.add_argument("--summary-csv", type=Path, default=Path("reports/generated/run_summary.csv"))
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
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument("--execute-notebook", action="store_true")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    exit_code = 0
    last_result = None
    for repeat_offset in range(args.repeat):
        current_seed = args.seed + repeat_offset
        run_label = args.run_label
        if args.repeat > 1:
            prefix = args.run_label or "repeat"
            run_label = f"{prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"

        data_output_dir = args.data_output_dir / run_label if run_label else args.data_output_dir
        private_dir = args.private_dir / run_label if run_label else args.private_dir

        result = run_usd_broad_direction_v0_previous_day_pipeline(
            seed=current_seed,
            task_path=args.task,
            data_output_dir=data_output_dir,
            private_dir=private_dir,
            run_dir=args.run_dir,
            run_label=run_label,
            repeat_index=repeat_offset + 1,
            repeat_count=args.repeat,
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
        last_result = result
        print(f"[{repeat_offset + 1}/{args.repeat}] status: {result.status}")
        print(f"[{repeat_offset + 1}/{args.repeat}] run_dir: {result.run_dir}")
        print(f"[{repeat_offset + 1}/{args.repeat}] score: {result.score_path}")
        print(f"[{repeat_offset + 1}/{args.repeat}] validation: {result.validation_path}")
        print(f"[{repeat_offset + 1}/{args.repeat}] manifest: {result.manifest_path}")
        if result.status != "completed":
            exit_code = 1

    if last_result is not None:
        print(f"report_csv: {last_result.report_csv_path}")
        print(f"report_markdown: {last_result.report_markdown_path}")
        print(f"summary_csv: {last_result.summary_csv_path}")
        print(f"summary_markdown: {last_result.summary_markdown_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
