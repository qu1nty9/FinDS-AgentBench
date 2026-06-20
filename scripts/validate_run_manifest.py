#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.runs import load_run_manifest, validate_run_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a FinDS-AgentBench run manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = load_run_manifest(args.manifest)
    result = validate_run_manifest(manifest)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

