#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.pipelines import run_synthetic_market_momentum_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the synthetic_market_direction_v0 momentum baseline end to end."
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--task",
        type=Path,
        default=Path("tasks/pilot/synthetic_market_direction_v0.yaml"),
    )
    parser.add_argument(
        "--data-output-dir",
        type=Path,
        default=Path("data/raw/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("data/private/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("runs/synthetic_market_direction_v0/momentum_baseline"),
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
    parser.add_argument("--execute-notebook", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_market_momentum_pipeline(
        seed=args.seed,
        task_path=args.task,
        data_output_dir=args.data_output_dir,
        private_dir=args.private_dir,
        run_dir=args.run_dir,
        report_csv_path=args.report_csv,
        report_markdown_path=args.report_markdown,
        execute_notebook=args.execute_notebook,
        command=" ".join(sys.argv),
    )
    print(f"status: {result.status}")
    print(f"run_dir: {result.run_dir}")
    print(f"score: {result.score_path}")
    print(f"validation: {result.validation_path}")
    print(f"manifest: {result.manifest_path}")
    print(f"report_csv: {result.report_csv_path}")
    print(f"report_markdown: {result.report_markdown_path}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

