import json
from pathlib import Path

from finds_agentbench.external_agents import (
    build_external_agent_readiness_artifacts,
    build_external_agent_readiness_report,
    build_external_agent_registration_validation_report,
    load_external_agent_registry,
)


def test_build_external_agent_readiness_artifacts_marks_default_registry_not_ready(tmp_path: Path):
    result = build_external_agent_readiness_artifacts(
        protocol_markdown_path=tmp_path / "external_agent_protocol.md",
        handoff_markdown_path=tmp_path / "external_agent_handoff.md",
        readiness_json_path=tmp_path / "external_agent_readiness.json",
        readiness_markdown_path=tmp_path / "external_agent_readiness.md",
        registration_validation_json_path=tmp_path / "external_agent_registration_validation.json",
        registration_validation_markdown_path=tmp_path
        / "external_agent_registration_validation.md",
    )

    readiness = json.loads(result["readiness_json_path"].read_text(encoding="utf-8"))
    validation = json.loads(result["registration_validation_json_path"].read_text(encoding="utf-8"))
    markdown = result["readiness_markdown_path"].read_text(encoding="utf-8")
    protocol = result["protocol_markdown_path"].read_text(encoding="utf-8")
    handoff = result["handoff_markdown_path"].read_text(encoding="utf-8")
    validation_markdown = result["registration_validation_markdown_path"].read_text(
        encoding="utf-8"
    )

    assert result["protocol_markdown_path"].exists()
    assert result["handoff_markdown_path"].exists()
    assert result["readiness_json_path"].exists()
    assert result["readiness_markdown_path"].exists()
    assert result["registration_validation_json_path"].exists()
    assert result["registration_validation_markdown_path"].exists()
    assert readiness["status"] == "not_ready_no_external_agents"
    assert readiness["ready_for_external_agent_claims"] is False
    assert validation["status"] == "no_external_agent_registered"
    assert readiness["bundled_reference_agent_count"] >= 7
    assert readiness["external_agent_configuration_count"] == 0
    assert readiness["completed_external_agent_configuration_count"] == 0
    assert any("non-author external agent" in item for item in readiness["blocking_items"])
    assert "not_ready_no_external_agents" in markdown
    assert "FINDS_SUBMISSION_DIR" in protocol
    assert "validate_external_agent_registry.py" in handoff
    assert "No external_agent_configurations" in validation_markdown


def test_external_agent_readiness_accepts_completed_external_configuration(tmp_path: Path):
    registry = load_external_agent_registry()
    registry["required_for_workshop_submission"] = {
        "minimum_external_agent_configurations": 1,
        "minimum_completed_runs_per_task": 3,
        "expected_task_ids": ["synthetic_market_direction_v0"],
    }
    run_manifest_paths = []
    for index in range(3):
        path = tmp_path / "runs" / f"run_{index + 1}" / "run_manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        run_manifest_paths.append(str(path))
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
            "completed_runs_per_task": {"synthetic_market_direction_v0": 3},
            "run_manifest_paths": run_manifest_paths,
        }
    ]

    readiness = build_external_agent_readiness_report(registry)
    validation = build_external_agent_registration_validation_report(
        registry,
        workspace_root=tmp_path,
    )

    assert readiness["status"] == "ready_for_external_agent_claims"
    assert readiness["ready_for_external_agent_claims"] is True
    assert readiness["completed_external_agent_ids"] == ["external_agent_a"]
    assert readiness["missing_external_task_ids"] == []
    assert readiness["blocking_items"] == []
    assert validation["status"] == "ready_for_external_agent_claims"
    assert validation["ready_for_external_agent_claims"] is True


def test_external_agent_registry_validation_rejects_completed_config_without_evidence():
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

    validation = build_external_agent_registration_validation_report(registry)

    assert validation["status"] == "invalid_external_agent_registration"
    assert any("completed_runs_per_task" in item for item in validation["blocking_items"])
    assert any("run_manifest_paths" in item for item in validation["blocking_items"])
