import json
from pathlib import Path

from finds_agentbench.external_agents import (
    build_external_agent_readiness_artifacts,
    build_external_agent_readiness_report,
    load_external_agent_registry,
)


def test_build_external_agent_readiness_artifacts_marks_default_registry_not_ready(tmp_path: Path):
    result = build_external_agent_readiness_artifacts(
        protocol_markdown_path=tmp_path / "external_agent_protocol.md",
        readiness_json_path=tmp_path / "external_agent_readiness.json",
        readiness_markdown_path=tmp_path / "external_agent_readiness.md",
    )

    readiness = json.loads(result["readiness_json_path"].read_text(encoding="utf-8"))
    markdown = result["readiness_markdown_path"].read_text(encoding="utf-8")
    protocol = result["protocol_markdown_path"].read_text(encoding="utf-8")

    assert result["protocol_markdown_path"].exists()
    assert result["readiness_json_path"].exists()
    assert result["readiness_markdown_path"].exists()
    assert readiness["status"] == "not_ready_no_external_agents"
    assert readiness["ready_for_external_agent_claims"] is False
    assert readiness["bundled_reference_agent_count"] >= 7
    assert readiness["external_agent_configuration_count"] == 0
    assert readiness["completed_external_agent_configuration_count"] == 0
    assert any("non-author external agent" in item for item in readiness["blocking_items"])
    assert "not_ready_no_external_agents" in markdown
    assert "FINDS_SUBMISSION_DIR" in protocol


def test_external_agent_readiness_accepts_completed_external_configuration():
    registry = load_external_agent_registry()
    registry["required_for_workshop_submission"] = {
        "minimum_external_agent_configurations": 1,
        "minimum_completed_runs_per_task": 3,
        "expected_task_ids": ["synthetic_market_direction_v0"],
    }
    registry["external_agent_configurations"] = [
        {
            "agent_id": "external_agent_a",
            "version": "2026-06-24",
            "provenance": "external_submission",
            "maintainer_type": "external",
            "agent_type": "llm_research_agent",
            "status": "completed",
            "included_in_reference_results": True,
            "stronger_external_evidence": True,
            "task_ids": ["synthetic_market_direction_v0"],
            "command_family": "scripts/run_synthetic_market_agent_suite.py",
        }
    ]

    readiness = build_external_agent_readiness_report(registry)

    assert readiness["status"] == "ready_for_external_agent_claims"
    assert readiness["ready_for_external_agent_claims"] is True
    assert readiness["completed_external_agent_ids"] == ["external_agent_a"]
    assert readiness["missing_external_task_ids"] == []
    assert readiness["blocking_items"] == []
