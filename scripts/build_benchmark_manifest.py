#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.benchmark_manifest import build_benchmark_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the canonical FinDS-AgentBench pilot release manifest."
    )
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks/pilot"))
    parser.add_argument("--cards-root", type=Path, default=Path("docs/cards"))
    parser.add_argument("--data-manifests-root", type=Path, default=Path("docs/data_manifests/pilot_v0"))
    parser.add_argument("--output-root", type=Path, default=Path("docs/releases/pilot_v0"))
    args = parser.parse_args()

    result = build_benchmark_manifest(
        tasks_root=args.tasks_root,
        cards_root=args.cards_root,
        data_manifests_root=args.data_manifests_root,
        output_root=args.output_root,
    )

    print(f"manifest: {result.manifest_path}")
    print(f"readme: {result.readme_path}")
    print(f"cards_index: {result.cards_index_path}")
    print(f"data_manifests_index: {result.data_manifests_readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
