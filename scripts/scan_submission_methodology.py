#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.methodology import scan_submission_methodology


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a submission for methodology risks.")
    parser.add_argument("submission_dir", type=Path)
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()

    result = scan_submission_methodology(
        args.submission_dir,
        fail_on_warnings=args.fail_on_warnings,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

