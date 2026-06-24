import json
from pathlib import Path

from finds_agentbench.external_agents import (
    build_external_agent_readiness_artifacts,
    build_external_agent_readiness_report,
    build_external_agent_registration_validation_report,
    load_external_agent_registry,
)
from finds_agentbench.runs import build_run_manifest, write_run_manifest


def write_external_agent_run_manifest(
    path: Path,
    *,
    agent_id: str = "external_agent_a",
    agent_version: str = "2026-06-24",
    task_id: str = "synthetic_market_direction_v0",
    run_id: str,
    run_type: str = "agent",
    status: str = "completed",
) -> None:
    run_dir = path.parent
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.8\n",
        encoding="utf-8",
    )
    (run_dir / "writeup.md").write_text("External agent writeup.\n", encoding="utf-8")
    (run_dir / "notebook.ipynb").write_text("{}\n", encoding="utf-8")
    manifest = build_run_manifest(
        task_id=task_id,
        agent_id=agent_id,
        agent_version=agent_version,
        submission_dir=run_dir,
        run_type=run_type,
        status=status,
        run_id=run_id,
        started_at="2026-06-24T00:00:00+00:00",
        completed_at="2026-06-24T00:01:00+00:00",
        validations={"artifact_validation": {"ok": True}},
        scores={"execution_success": 1.0, "overall_score": 0.5},
        tool_permissions=["filesystem:read", "filesystem:write"],
        commands=[
            {
                "command": "python external_agent.py",
                "started_at": "2026-06-24T00:00:00+00:00",
                "completed_at": "2026-06-24T00:00:30+00:00",
                "exit_code": 0,
            }
        ],
    )
    write_run_manifest(manifest, path)


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
        write_external_agent_run_manifest(path, run_id=f"external_run_{index + 1}")
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
    assert validation["valid_run_manifest_count"] == 3
    assert validation["evidence_error_count"] == 0


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


def test_external_agent_registration_validation_rejects_mismatched_run_manifest(tmp_path: Path):
    registry = load_external_agent_registry()
    registry["required_for_workshop_submission"] = {
        "minimum_external_agent_configurations": 1,
        "minimum_completed_runs_per_task": 1,
        "expected_task_ids": ["synthetic_market_direction_v0"],
    }
    run_manifest_path = tmp_path / "runs" / "run_1" / "run_manifest.json"
    write_external_agent_run_manifest(
        run_manifest_path,
        agent_id="other_agent",
        run_id="external_run_mismatch",
    )
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
            "completed_runs_per_task": {"synthetic_market_direction_v0": 1},
            "run_manifest_paths": [str(run_manifest_path)],
        }
    ]
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = build_external_agent_readiness_artifacts(
        registry_path=registry_path,
        protocol_markdown_path=tmp_path / "external_agent_protocol.md",
        handoff_markdown_path=tmp_path / "external_agent_handoff.md",
        readiness_json_path=tmp_path / "external_agent_readiness.json",
        readiness_markdown_path=tmp_path / "external_agent_readiness.md",
        registration_validation_json_path=tmp_path / "registration_validation.json",
        registration_validation_markdown_path=tmp_path / "registration_validation.md",
        workspace_root=tmp_path,
    )

    readiness = json.loads(result["readiness_json_path"].read_text(encoding="utf-8"))
    validation = json.loads(result["registration_validation_json_path"].read_text(encoding="utf-8"))
    validation_markdown = result["registration_validation_markdown_path"].read_text(
        encoding="utf-8"
    )

    assert validation["status"] == "invalid_external_agent_registration"
    assert validation["ready_for_external_agent_claims"] is False
    assert validation["evidence_error_count"] >= 1
    assert any("agent.agent_id" in item for item in validation["blocking_items"])
    assert readiness["status"] == "not_ready_invalid_external_agent_evidence"
    assert readiness["ready_for_external_agent_claims"] is False
    assert "Evidence errors" in validation_markdown
