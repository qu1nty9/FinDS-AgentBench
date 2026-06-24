#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.paper_artifacts import build_paper_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build paper-ready LaTeX tables and SVG figures from pilot reference results."
    )
    parser.add_argument(
        "--reference-results-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/reference_results.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/releases/pilot_v0/paper_artifacts"),
    )
    args = parser.parse_args()

    written = build_paper_artifacts(
        reference_results_path=args.reference_results_json,
        output_dir=args.output_dir,
    )
    for key, path in sorted(written.items()):
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
