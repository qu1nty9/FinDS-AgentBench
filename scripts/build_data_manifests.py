#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.data_manifest import build_data_manifests


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build public data manifests and checksums for benchmark tasks."
    )
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks/pilot"))
    parser.add_argument("--output-root", type=Path, default=Path("docs/data_manifests/pilot_v0"))
    parser.add_argument("--workspace-root", type=Path, default=Path("."))
    args = parser.parse_args()

    result = build_data_manifests(
        tasks_root=args.tasks_root,
        output_root=args.output_root,
        workspace_root=args.workspace_root,
    )

    print(f"manifests: {len(result.manifest_paths)}")
    print(f"index_json: {result.index_json_path}")
    print(f"index_csv: {result.index_csv_path}")
    print(f"readme: {result.readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
