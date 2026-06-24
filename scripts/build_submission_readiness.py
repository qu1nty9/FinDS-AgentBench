#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.submission_readiness import build_submission_readiness_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FinDS-AgentBench submission-readiness gate artifacts.")
    parser.add_argument("--manifest", type=Path, default=Path("docs/releases/pilot_v0/manifest.json"))
    parser.add_argument(
        "--methodology-summary",
        type=Path,
        default=Path("audits/methodology_calibration/reports/summary.json"),
    )
    parser.add_argument(
        "--methodology-review-packet",
        type=Path,
        default=Path("audits/methodology_calibration/reviews/calibration_review_packet.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/submission_readiness.json"),
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/submission_readiness.md"),
    )
    parser.add_argument(
        "--evidence-ledger-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/submission_evidence_ledger.json"),
    )
    parser.add_argument(
        "--evidence-ledger-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/submission_evidence_ledger.md"),
    )
    args = parser.parse_args()

    result = build_submission_readiness_artifacts(
        manifest_path=args.manifest,
        methodology_calibration_summary_path=args.methodology_summary,
        methodology_calibration_review_packet_path=args.methodology_review_packet,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
        evidence_ledger_json_path=args.evidence_ledger_json,
        evidence_ledger_markdown_path=args.evidence_ledger_markdown,
    )
    print(f"submission_readiness_json: {result['json_path']}")
    print(f"submission_readiness_markdown: {result['markdown_path']}")
    print(f"submission_evidence_ledger_json: {result['evidence_ledger_json_path']}")
    print(f"submission_evidence_ledger_markdown: {result['evidence_ledger_markdown_path']}")
    print(f"submission_readiness_status: {result['report']['status']}")
    print(f"submission_evidence_ledger_status: {result['evidence_ledger']['status']}")
    print(f"ready_gates: {result['report']['ready_gate_count']}/{result['report']['gate_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
