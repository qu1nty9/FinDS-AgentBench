#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.pipelines import run_synthetic_market_agent_command


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an external agent command on synthetic_market_direction_v0."
    )
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--agent-version", default="unknown")
    parser.add_argument(
        "--agent-command",
        required=True,
        help="Command string parsed with shlex. Use FINDS_* env vars inside the agent.",
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--run-label", default=None)
    parser.add_argument("--repeat-index", type=int, default=None)
    parser.add_argument("--repeat-count", type=int, default=None)
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
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--runs-root", type=Path, default=None)
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
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--cwd", type=Path, default=None)
    args = parser.parse_args()

    result = run_synthetic_market_agent_command(
        agent_id=args.agent_id,
        agent_version=args.agent_version,
        agent_command=args.agent_command,
        seed=args.seed,
        task_path=args.task,
        data_output_dir=args.data_output_dir,
        private_dir=args.private_dir,
        run_dir=args.run_dir,
        run_label=args.run_label,
        repeat_index=args.repeat_index,
        repeat_count=args.repeat_count,
        runs_root=args.runs_root,
        report_csv_path=args.report_csv,
        report_markdown_path=args.report_markdown,
        summary_csv_path=args.summary_csv,
        summary_markdown_path=args.summary_markdown,
        execute_notebook=args.execute_notebook,
        command_timeout_seconds=args.timeout_seconds,
        cwd=args.cwd,
    )

    print(f"status: {result.status}")
    print(f"run_dir: {result.run_dir}")
    print(f"score: {result.score_path}")
    print(f"validation: {result.validation_path}")
    print(f"manifest: {result.manifest_path}")
    print(f"report_csv: {result.report_csv_path}")
    print(f"report_markdown: {result.report_markdown_path}")
    print(f"summary_csv: {result.summary_csv_path}")
    print(f"summary_markdown: {result.summary_markdown_path}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
