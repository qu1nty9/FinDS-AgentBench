#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.manual_audit import build_manual_audit_workflow_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FinDS-AgentBench manual-audit workflow artifacts.")
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path("audits/pilot_v0/reviews"),
        help="Directory for reviewer packet CSV files.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("audits/pilot_v0/reports"),
        help="Directory for agreement reports.",
    )
    args = parser.parse_args()

    result = build_manual_audit_workflow_artifacts(
        reviews_dir=args.reviews_dir,
        reports_dir=args.reports_dir,
    )
    print(f"reviews_readme: {result['reviews_readme_path']}")
    print(f"independent_reviewer_handoff: {result['independent_reviewer_handoff_path']}")
    print(f"reviewer_1_seed: {result['reviewer_1_seed_path']}")
    print(f"reviewer_2_template: {result['reviewer_2_template_path']}")
    print(f"reviewer_2_shadow: {result['reviewer_2_shadow_path']}")
    print(f"agreement_json: {result['agreement_json_path']}")
    print(f"agreement_markdown: {result['agreement_markdown_path']}")
    print(f"adjudication_json: {result['adjudication_json_path']}")
    print(f"adjudication_markdown: {result['adjudication_markdown_path']}")
    print(f"reviewer_readiness_json: {result['reviewer_readiness_json_path']}")
    print(f"reviewer_readiness_markdown: {result['reviewer_readiness_markdown_path']}")
    print(
        "independent_reviewer_packet_validation_json: "
        f"{result['independent_reviewer_packet_validation_json_path']}"
    )
    print(
        "independent_reviewer_packet_validation_markdown: "
        f"{result['independent_reviewer_packet_validation_markdown_path']}"
    )
    print(f"official_agreement_status: {result['agreement_summary']['status']}")
    print(f"exploratory_agreement_status: {result['agreement_summary']['exploratory_status']}")
    print(f"reviewer_readiness_status: {result['reviewer_readiness']['status']}")
    print(
        "independent_reviewer_packet_validation_status: "
        f"{result['independent_reviewer_packet_validation']['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
