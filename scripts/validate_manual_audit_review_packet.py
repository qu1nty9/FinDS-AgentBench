#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.manual_audit import (
    DEFAULT_INDEPENDENT_REVIEWER_PACKET_VALIDATION_JSON_PATH,
    DEFAULT_INDEPENDENT_REVIEWER_PACKET_VALIDATION_MARKDOWN_PATH,
    build_independent_reviewer_packet_validation_report,
    write_independent_reviewer_packet_validation_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an independent manual-audit reviewer packet."
    )
    parser.add_argument(
        "--packet",
        type=Path,
        required=True,
        help="Completed reviewer packet CSV copied from reviewer_2_blank_template.csv.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_INDEPENDENT_REVIEWER_PACKET_VALIDATION_JSON_PATH,
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=DEFAULT_INDEPENDENT_REVIEWER_PACKET_VALIDATION_MARKDOWN_PATH,
    )
    args = parser.parse_args()

    report = build_independent_reviewer_packet_validation_report(packet_path=args.packet)
    outputs = write_independent_reviewer_packet_validation_artifacts(
        report=report,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
    )
    print(f"validation_json: {outputs['json_path']}")
    print(f"validation_markdown: {outputs['markdown_path']}")
    print(f"validation_status: {report['status']}")
    print(f"ready_for_independent_agreement: {report['ready_for_independent_agreement']}")
    print(f"error_count: {report['error_count']}")
    return 0 if report["ready_for_independent_agreement"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
