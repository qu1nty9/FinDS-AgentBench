from __future__ import annotations

import json
from pathlib import Path

from finds_agentbench.submission_package import (
    build_submission_package_artifacts,
    stale_submission_package_artifacts,
)


def test_build_submission_package_manifest_tracks_claims_artifacts_and_targets(tmp_path: Path):
    output_json = tmp_path / "submission_package_manifest.json"
    output_markdown = tmp_path / "submission_package_manifest.md"

    result = build_submission_package_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )

    manifest = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_markdown.read_text(encoding="utf-8")

    assert result.manifest == manifest
    assert manifest["benchmark_id"] == "finds_agentbench_pilot_v0"
    assert manifest["status"] == "candidate_blocked_on_missing_artifacts_and_evidence"
    assert manifest["ready_for_workshop_submission_package"] is False
    assert manifest["publication_gate_status"] == "blocked_on_submission_evidence_and_pdf_compile"
    assert manifest["archive_status"] == "candidate_unfrozen"
    assert len(manifest["archive_sha256"]) == 64
    assert manifest["artifact_count"] >= 30
    assert manifest["missing_required_artifact_count"] >= 1

    artifacts = {(artifact["group"], artifact["role"]): artifact for artifact in manifest["artifacts"]}
    assert artifacts[("manuscript", "main_tex")]["exists"] is True
    assert artifacts[("manuscript", "compiled_pdf")]["exists"] is False
    assert artifacts[("release_candidate", "release_archive")]["materialization"] == (
        "declared_by_archive_manifest"
    )
    assert artifacts[("release_candidate", "release_archive")]["sha256"] == manifest["archive_sha256"]
    assert artifacts[("ci", "github_actions_workflow")]["exists"] is True
    assert artifacts[("package_control", "submission_package_script")]["exists"] is True
    assert artifacts[("package_control", "submission_package_module")]["exists"] is True

    target_statuses = {target["target_id"]: target["status"] for target in manifest["stage_targets"]}
    assert target_statuses["arxiv_workshop"] == "not_ready_blocked_by_current_gates"
    assert (
        target_statuses["top_benchmark_dataset_venue"]
        == "not_ready_requires_scale_and_external_validation"
    )
    assert target_statuses["journal_extension"] == "not_ready_requires_longitudinal_reliability_study"

    assert any("External-agent registration" in claim for claim in manifest["allowed_current_claims"])
    assert any("Independent external-agent performance" in claim for claim in manifest["disallowed_current_claims"])
    assert any("independent reviewer packet" in item for item in manifest["blocking_items"])
    assert any(
        command.endswith("scripts/build_submission_package_manifest.py --check")
        for command in manifest["pre_submission_verification_commands"]
    )

    assert "Workshop Submission Package Manifest" in markdown
    assert "candidate_blocked_on_missing_artifacts_and_evidence" in markdown
    assert "papers/workshop_pilot/main.pdf" in markdown


def test_stale_submission_package_artifacts_detects_outdated_outputs(tmp_path: Path):
    output_json = tmp_path / "submission_package_manifest.json"
    output_markdown = tmp_path / "submission_package_manifest.md"

    stale_before_write = stale_submission_package_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert stale_before_write == [output_json, output_markdown]

    build_submission_package_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert (
        stale_submission_package_artifacts(
            output_json_path=output_json,
            output_markdown_path=output_markdown,
        )
        == []
    )

    output_json.write_text('{"stale": true}\n', encoding="utf-8")
    stale_after_tamper = stale_submission_package_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert stale_after_tamper == [output_json]
