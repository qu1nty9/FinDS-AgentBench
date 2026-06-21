#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.artifacts import validate_submission_artifacts
from finds_agentbench.io import load_yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate FinDS-AgentBench submission artifacts.")
    parser.add_argument("task", type=Path, help="Path to task YAML file.")
    parser.add_argument("submission_dir", type=Path, help="Path to submission directory.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--skip-notebook-execution", action="store_true")
    parser.add_argument("--executed-output", type=Path, default=None)
    parser.add_argument("--scan-leakage", action="store_true")
    parser.add_argument("--scan-methodology", action="store_true")
    parser.add_argument("--methodology-fail-on-warnings", action="store_true")
    parser.add_argument(
        "--forbidden-term",
        action="append",
        default=None,
        help="Replacement forbidden leakage term. Can be passed multiple times.",
    )
    args = parser.parse_args()

    task_spec = load_yaml(args.task)
    result = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=args.submission_dir,
        execute=not args.skip_notebook_execution,
        timeout=args.timeout,
        executed_output=args.executed_output,
        scan_leakage=args.scan_leakage,
        leakage_terms=args.forbidden_term,
        scan_methodology=args.scan_methodology,
        methodology_fail_on_warnings=args.methodology_fail_on_warnings,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
