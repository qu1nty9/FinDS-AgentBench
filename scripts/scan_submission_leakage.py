#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.leakage import scan_submission_for_leakage


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a submission for forbidden leakage terms.")
    parser.add_argument("submission_dir", type=Path)
    parser.add_argument(
        "--forbidden-term",
        action="append",
        default=None,
        help="Additional or replacement forbidden term. Can be passed multiple times.",
    )
    args = parser.parse_args()

    result = scan_submission_for_leakage(
        args.submission_dir,
        forbidden_terms=args.forbidden_term,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

