#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.statistical_artifacts import build_statistical_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build uncertainty and paired-comparison artifacts from pilot protocol run results."
    )
    parser.add_argument(
        "--protocol-results-csv",
        type=Path,
        default=Path("reports/release_runs/pilot_protocol_run_results.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/releases/pilot_v0/statistical_artifacts"),
    )
    args = parser.parse_args()

    written = build_statistical_artifacts(
        protocol_results_csv_path=args.protocol_results_csv,
        output_dir=args.output_dir,
    )
    for key, path in sorted(written.items()):
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
