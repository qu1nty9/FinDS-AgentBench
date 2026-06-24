#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.external_agents import (
    DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH,
    DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH,
    build_external_agent_registration_validation_report,
    load_external_agent_registry,
    render_external_agent_registration_validation_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate FinDS-AgentBench external-agent registration evidence."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("agents/external_agent_registry.yaml"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH,
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH,
    )
    args = parser.parse_args()

    registry = load_external_agent_registry(args.registry)
    report = build_external_agent_registration_validation_report(registry)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(
        render_external_agent_registration_validation_markdown(report),
        encoding="utf-8",
    )

    print(f"validation_json: {args.output_json}")
    print(f"validation_markdown: {args.output_markdown}")
    print(f"validation_status: {report['status']}")
    print(f"ready_for_external_agent_claims: {report['ready_for_external_agent_claims']}")
    print(f"blocking_item_count: {len(report['blocking_items'])}")
    return 0 if report["ready_for_external_agent_claims"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
