#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.submission_package import (
    DEFAULT_ARCHIVE_MANIFEST_PATH,
    DEFAULT_EVIDENCE_LEDGER_PATH,
    DEFAULT_FORMATTING_CHECK_PATH,
    DEFAULT_PUBLICATION_GATE_PATH,
    DEFAULT_RELEASE_MANIFEST_PATH,
    DEFAULT_SUBMISSION_PACKAGE_JSON_PATH,
    DEFAULT_SUBMISSION_PACKAGE_MARKDOWN_PATH,
    DEFAULT_SUBMISSION_READINESS_PATH,
    build_submission_package_artifacts,
    stale_submission_package_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the FinDS-AgentBench workshop submission package manifest."
    )
    parser.add_argument("--release-manifest", type=Path, default=DEFAULT_RELEASE_MANIFEST_PATH)
    parser.add_argument("--archive-manifest", type=Path, default=DEFAULT_ARCHIVE_MANIFEST_PATH)
    parser.add_argument("--submission-readiness", type=Path, default=DEFAULT_SUBMISSION_READINESS_PATH)
    parser.add_argument("--evidence-ledger", type=Path, default=DEFAULT_EVIDENCE_LEDGER_PATH)
    parser.add_argument("--publication-gate", type=Path, default=DEFAULT_PUBLICATION_GATE_PATH)
    parser.add_argument("--formatting-check", type=Path, default=DEFAULT_FORMATTING_CHECK_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_SUBMISSION_PACKAGE_JSON_PATH)
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=DEFAULT_SUBMISSION_PACKAGE_MARKDOWN_PATH,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return non-zero if the generated submission-package artifacts are stale.",
    )
    args = parser.parse_args()

    if args.check:
        stale_paths = stale_submission_package_artifacts(
            release_manifest_path=args.release_manifest,
            archive_manifest_path=args.archive_manifest,
            submission_readiness_path=args.submission_readiness,
            evidence_ledger_path=args.evidence_ledger,
            publication_gate_path=args.publication_gate,
            formatting_check_path=args.formatting_check,
            output_json_path=args.output_json,
            output_markdown_path=args.output_markdown,
        )
        if stale_paths:
            for path in stale_paths:
                print(f"stale_submission_package_artifact: {path}", file=sys.stderr)
            return 1
        print("submission_package_manifest: current")
        return 0

    result = build_submission_package_artifacts(
        release_manifest_path=args.release_manifest,
        archive_manifest_path=args.archive_manifest,
        submission_readiness_path=args.submission_readiness,
        evidence_ledger_path=args.evidence_ledger,
        publication_gate_path=args.publication_gate,
        formatting_check_path=args.formatting_check,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
    )
    print(f"submission_package_json: {result.json_path}")
    print(f"submission_package_markdown: {result.markdown_path}")
    print(f"submission_package_status: {result.manifest['status']}")
    print(
        "missing_required_artifacts: "
        f"{result.manifest['missing_required_artifact_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
