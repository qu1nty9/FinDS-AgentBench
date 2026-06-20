#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.runs import build_run_manifest, validate_run_manifest, write_run_manifest


def load_optional_json(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a FinDS-AgentBench run manifest.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--agent-version", required=True)
    parser.add_argument("--submission-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-type", default="baseline")
    parser.add_argument("--status", default="completed")
    parser.add_argument("--scores-json", type=Path, default=None)
    parser.add_argument("--validations-json", type=Path, default=None)
    parser.add_argument("--tool-permission", action="append", default=None)
    args = parser.parse_args()

    manifest = build_run_manifest(
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_version=args.agent_version,
        submission_dir=args.submission_dir,
        run_type=args.run_type,
        status=args.status,
        scores=load_optional_json(args.scores_json),
        validations=load_optional_json(args.validations_json),
        tool_permissions=args.tool_permission or [],
    )
    result = validate_run_manifest(manifest)
    if not result.ok:
        print(json.dumps(result.as_dict(), indent=2))
        return 1

    output = write_run_manifest(manifest, args.output)
    print(f"Wrote run manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

