#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finds_agentbench.io import load_yaml
from finds_agentbench.validate import validate_task_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a FinDS-AgentBench task spec.")
    parser.add_argument("task", type=Path, help="Path to task YAML file.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/task_schema.yaml"),
        help="Path to task schema YAML file.",
    )
    args = parser.parse_args()

    task_spec = load_yaml(args.task)
    schema_spec = load_yaml(args.schema)
    result = validate_task_spec(task_spec, schema_spec)

    if result.ok:
        print(f"OK: {args.task}")
        return 0

    print(f"INVALID: {args.task}", file=sys.stderr)
    for error in result.errors:
        print(f"- {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

