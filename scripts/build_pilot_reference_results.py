#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.benchmark_manifest import (
    BENCHMARK_ID,
    BENCHMARK_VERSION,
    RELEASE_STAGE,
    command_for_protocol,
)
from finds_agentbench.reference_results import load_csv_rows, write_reference_results_snapshot
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the pilot reference-results snapshot from repeated-run summary CSVs."
    )
    parser.add_argument("--baseline-summary-csv", type=Path, required=True)
    parser.add_argument("--agent-summary-csv", type=Path, required=True)
    parser.add_argument("--protocol-summary-csv", type=Path, required=True)
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/reference_results.md"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/reference_results.json"),
    )
    parser.add_argument(
        "--treasury-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument(
        "--expected-run-count",
        type=int,
        default=3,
    )
    args = parser.parse_args()

    markdown_path, json_path = write_reference_results_snapshot(
        output_markdown_path=args.output_markdown,
        output_json_path=args.output_json,
        benchmark_id=BENCHMARK_ID,
        benchmark_version=BENCHMARK_VERSION,
        release_stage=RELEASE_STAGE,
        treasury_snapshot_date=args.treasury_snapshot_date,
        baseline_rows=load_csv_rows(args.baseline_summary_csv),
        agent_rows=load_csv_rows(args.agent_summary_csv),
        protocol_rows=load_csv_rows(args.protocol_summary_csv),
        baseline_command=command_for_protocol("pilot_baseline_suite"),
        agent_command=command_for_protocol("pilot_agent_suite"),
        protocol_command=command_for_protocol("pilot_protocol"),
        expected_run_count=args.expected_run_count,
    )

    print(f"reference_results_markdown: {markdown_path}")
    print(f"reference_results_json: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
