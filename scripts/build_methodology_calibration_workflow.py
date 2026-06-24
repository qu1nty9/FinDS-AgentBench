#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.methodology_calibration import (
    DEFAULT_METHODOLOGY_CALIBRATION_CONFIG_PATH,
    DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH,
    DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_JSON_PATH,
    DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_MARKDOWN_PATH,
    build_methodology_calibration_workflow,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the methodology calibration summary and review packet."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_METHODOLOGY_CALIBRATION_CONFIG_PATH)
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks/pilot"))
    parser.add_argument(
        "--review-packet",
        type=Path,
        default=DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH,
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_JSON_PATH,
    )
    parser.add_argument(
        "--summary-markdown",
        type=Path,
        default=DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_MARKDOWN_PATH,
    )
    parser.add_argument(
        "--clean-controls-per-group",
        type=int,
        default=1,
        help="Number of clean-control submissions to sample per (task_id, run_type) group.",
    )
    args = parser.parse_args()

    result = build_methodology_calibration_workflow(
        config_path=args.config,
        tasks_root=args.tasks_root,
        review_packet_path=args.review_packet,
        summary_json_path=args.summary_json,
        summary_markdown_path=args.summary_markdown,
        clean_control_per_group=args.clean_controls_per_group,
    )
    print(f"summary_json: {result['summary_json_path']}")
    print(f"summary_markdown: {result['summary_markdown_path']}")
    print(f"review_packet: {result['review_packet_path']}")
    print(f"entry_count: {result['summary']['counts']['entry_count']}")
    print(f"finding_count: {result['summary']['counts']['finding_count']}")
    print(f"clean_control_rows: {result['summary']['review_packet']['clean_control_row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
