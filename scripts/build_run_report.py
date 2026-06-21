#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.reports import (
    aggregate_result_rows,
    load_result_rows,
    write_results_csv,
    write_results_markdown,
    write_summary_csv,
    write_summary_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build CSV and Markdown reports from FinDS-AgentBench run manifests."
    )
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("reports/generated/run_results.csv"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/generated/run_results.md"),
    )
    parser.add_argument(
        "--summary-csv-output",
        type=Path,
        default=Path("reports/generated/run_summary.csv"),
    )
    parser.add_argument(
        "--summary-markdown-output",
        type=Path,
        default=Path("reports/generated/run_summary.md"),
    )
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--markdown-column",
        action="append",
        default=None,
        help="Markdown column to include. Can be passed multiple times.",
    )
    args = parser.parse_args()

    rows = load_result_rows(args.runs_root, strict=args.strict)
    write_results_csv(rows, args.csv_output)
    write_results_markdown(rows, args.markdown_output, columns=args.markdown_column)
    print(f"Wrote {len(rows)} rows to {args.csv_output}")
    print(f"Wrote Markdown report to {args.markdown_output}")
    if not args.no_summary:
        summary_rows = aggregate_result_rows(rows)
        write_summary_csv(summary_rows, args.summary_csv_output)
        write_summary_markdown(summary_rows, args.summary_markdown_output)
        print(f"Wrote {len(summary_rows)} summary rows to {args.summary_csv_output}")
        print(f"Wrote summary Markdown report to {args.summary_markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
