#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.external_agents import build_external_agent_readiness_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build FinDS-AgentBench external-agent protocol and readiness artifacts."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("agents/external_agent_registry.yaml"),
    )
    parser.add_argument(
        "--protocol-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/external_agent_protocol.md"),
    )
    parser.add_argument(
        "--handoff-markdown",
        type=Path,
        default=Path("agents/external_agent_handoff.md"),
    )
    parser.add_argument(
        "--readiness-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/external_agent_readiness.json"),
    )
    parser.add_argument(
        "--readiness-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/external_agent_readiness.md"),
    )
    parser.add_argument(
        "--registration-validation-json",
        type=Path,
        default=Path("docs/releases/pilot_v0/external_agent_registration_validation.json"),
    )
    parser.add_argument(
        "--registration-validation-markdown",
        type=Path,
        default=Path("docs/releases/pilot_v0/external_agent_registration_validation.md"),
    )
    args = parser.parse_args()

    result = build_external_agent_readiness_artifacts(
        registry_path=args.registry,
        protocol_markdown_path=args.protocol_markdown,
        handoff_markdown_path=args.handoff_markdown,
        readiness_json_path=args.readiness_json,
        readiness_markdown_path=args.readiness_markdown,
        registration_validation_json_path=args.registration_validation_json,
        registration_validation_markdown_path=args.registration_validation_markdown,
    )

    print(f"registry: {result['registry_path']}")
    print(f"protocol_markdown: {result['protocol_markdown_path']}")
    print(f"handoff_markdown: {result['handoff_markdown_path']}")
    print(f"readiness_json: {result['readiness_json_path']}")
    print(f"readiness_markdown: {result['readiness_markdown_path']}")
    print(f"registration_validation_json: {result['registration_validation_json_path']}")
    print(f"registration_validation_markdown: {result['registration_validation_markdown_path']}")
    print(f"external_agent_readiness_status: {result['readiness']['status']}")
    print(f"external_agent_registration_validation_status: {result['registration_validation']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
