#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.publication_gate import (
    DEFAULT_FORMATTING_CHECK_PATH,
    DEFAULT_PUBLICATION_GATE_JSON_PATH,
    DEFAULT_PUBLICATION_GATE_MARKDOWN_PATH,
    DEFAULT_RELEASE_MANIFEST_PATH,
    DEFAULT_SUBMISSION_READINESS_PATH,
    build_publication_gate_artifacts,
    stale_publication_gate_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the FinDS-AgentBench pilot publication-gate manifest."
    )
    parser.add_argument("--release-manifest", type=Path, default=DEFAULT_RELEASE_MANIFEST_PATH)
    parser.add_argument("--submission-readiness", type=Path, default=DEFAULT_SUBMISSION_READINESS_PATH)
    parser.add_argument("--formatting-check", type=Path, default=DEFAULT_FORMATTING_CHECK_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_PUBLICATION_GATE_JSON_PATH)
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_PUBLICATION_GATE_MARKDOWN_PATH)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return non-zero if the generated publication-gate artifacts are stale.",
    )
    args = parser.parse_args()

    if args.check:
        stale_paths = stale_publication_gate_artifacts(
            release_manifest_path=args.release_manifest,
            submission_readiness_path=args.submission_readiness,
            formatting_check_path=args.formatting_check,
            output_json_path=args.output_json,
            output_markdown_path=args.output_markdown,
        )
        if stale_paths:
            for path in stale_paths:
                print(f"stale_publication_gate_artifact: {path}", file=sys.stderr)
            return 1
        print("publication_gate_manifest: current")
        return 0

    result = build_publication_gate_artifacts(
        release_manifest_path=args.release_manifest,
        submission_readiness_path=args.submission_readiness,
        formatting_check_path=args.formatting_check,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
    )
    print(f"publication_gate_json: {result.json_path}")
    print(f"publication_gate_markdown: {result.markdown_path}")
    print(f"publication_gate_status: {result.manifest['status']}")
    print(
        "blocking_evidence_gates: "
        f"{result.manifest['blocking_evidence_gate_count']}/{result.manifest['evidence_gate_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
