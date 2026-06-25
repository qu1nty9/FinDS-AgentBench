#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finds_agentbench.release_archive import (
    DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    verify_release_archive,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a FinDS-AgentBench release archive against its checksum manifest."
    )
    parser.add_argument("--workspace-root", type=Path, default=Path("."))
    parser.add_argument(
        "--archive-manifest",
        type=Path,
        default=DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    )
    parser.add_argument("--json", action="store_true", help="Print the full verification report as JSON.")
    args = parser.parse_args()

    result = verify_release_archive(
        workspace_root=args.workspace_root,
        archive_manifest_path=args.archive_manifest,
    )
    if args.json:
        print(json.dumps(result.report, indent=2, sort_keys=True))
    else:
        print(f"status: {result.status}")
        print(f"archive_path: {result.report['archive_path']}")
        print(f"archive_sha256_match: {result.report.get('archive_sha256_match', False)}")
        print(f"archive_file_count: {result.report.get('archive_file_count', 0)}")
        print(f"error_count: {result.report['error_count']}")
        for error in result.report["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if result.status == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
