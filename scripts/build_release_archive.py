#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.release_archive import (
    DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    DEFAULT_RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH,
    DEFAULT_RELEASE_ARCHIVE_OUTPUT_DIR,
    DEFAULT_RELEASE_MANIFEST_PATH,
    DEFAULT_SUBMISSION_READINESS_PATH,
    build_release_archive,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic FinDS-AgentBench pilot release archive and checksums."
    )
    parser.add_argument("--workspace-root", type=Path, default=Path("."))
    parser.add_argument("--release-manifest", type=Path, default=DEFAULT_RELEASE_MANIFEST_PATH)
    parser.add_argument(
        "--submission-readiness",
        type=Path,
        default=DEFAULT_SUBMISSION_READINESS_PATH,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RELEASE_ARCHIVE_OUTPUT_DIR)
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    )
    parser.add_argument(
        "--manifest-markdown",
        type=Path,
        default=DEFAULT_RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH,
    )
    parser.add_argument(
        "--include-path",
        type=Path,
        action="append",
        dest="include_paths",
        help="Override the default archive include set. May be provided multiple times.",
    )
    args = parser.parse_args()

    result = build_release_archive(
        workspace_root=args.workspace_root,
        release_manifest_path=args.release_manifest,
        submission_readiness_path=args.submission_readiness,
        output_dir=args.output_dir,
        manifest_json_path=args.manifest_json,
        manifest_markdown_path=args.manifest_markdown,
        include_paths=args.include_paths if args.include_paths else None,
    )
    print(f"archive: {result.archive_path}")
    print(f"archive_sha256: {result.manifest['archive_sha256']}")
    print(f"manifest_json: {result.manifest_json_path}")
    print(f"manifest_markdown: {result.manifest_markdown_path}")
    print(f"archive_status: {result.manifest['archive_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
