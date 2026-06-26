from __future__ import annotations

import json
from pathlib import Path

from finds_agentbench.publication_gate import (
    build_publication_gate_artifacts,
    stale_publication_gate_artifacts,
)


def test_build_publication_gate_manifest_tracks_ci_and_submission_blockers(tmp_path: Path):
    output_json = tmp_path / "publication_gate_manifest.json"
    output_markdown = tmp_path / "publication_gate_manifest.md"

    result = build_publication_gate_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )

    manifest = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_markdown.read_text(encoding="utf-8")

    assert result.manifest == manifest
    assert manifest["benchmark_id"] == "finds_agentbench_pilot_v0"
    assert manifest["status"] == "blocked_on_submission_evidence_and_pdf_compile"
    assert manifest["ready_for_final_submission_package"] is False
    assert manifest["automated_gate_count"] == 7
    assert manifest["ci_enforced_automated_gate_count"] == 7
    assert manifest["blocking_evidence_gate_count"] == 3

    automated_gate_ids = {gate["gate_id"] for gate in manifest["automated_gates"]}
    assert "release_gate_regression_suite" in automated_gate_ids
    assert "publication_gate_manifest_staleness" in automated_gate_ids
    assert "submission_package_manifest_staleness" in automated_gate_ids
    assert "release_archive_build_and_verify" in automated_gate_ids
    assert "pilot_release_reproducibility_smoke" in automated_gate_ids
    assert any(
        "tests/test_submission_package.py" in gate["local_command"]
        for gate in manifest["automated_gates"]
    )
    assert any(
        "tests/test_publication_gate.py" in gate["local_command"]
        for gate in manifest["automated_gates"]
    )

    evidence_gates = {gate["gate_id"]: gate for gate in manifest["evidence_gates"]}
    assert evidence_gates["pilot_release_scope"]["ready"] is True
    assert evidence_gates["manual_audit_independent_review"]["ready"] is True
    assert evidence_gates["external_agent_evidence"]["ready"] is False
    assert evidence_gates["release_tag_and_archive"]["ready"] is False
    assert evidence_gates["latex_pdf_compile_visual_inspection"]["ready"] is False
    assert (
        evidence_gates["latex_pdf_compile_visual_inspection"]["evidence"][
            "latex_engine_available"
        ]
        is False
    )
    assert not any("independent reviewer packet" in item for item in manifest["blocking_items"])
    assert any("non-author external agent" in item for item in manifest["blocking_items"])
    assert any("LaTeX engine" in item for item in manifest["blocking_items"])
    assert any(
        "Inspect the official manual-audit agreement" in item
        for item in manifest["recommended_completion_order"]
    )

    assert "Publication Gate Manifest" in markdown
    assert "release_archive_build_and_verify" in markdown
    assert "PYTHONPATH=src python scripts/build_submission_package_manifest.py --check" in markdown
    assert "PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check" in markdown


def test_stale_publication_gate_artifacts_detects_outdated_outputs(tmp_path: Path):
    output_json = tmp_path / "publication_gate_manifest.json"
    output_markdown = tmp_path / "publication_gate_manifest.md"

    stale_before_write = stale_publication_gate_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert stale_before_write == [output_json, output_markdown]

    build_publication_gate_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert (
        stale_publication_gate_artifacts(
            output_json_path=output_json,
            output_markdown_path=output_markdown,
        )
        == []
    )

    output_markdown.write_text("stale\n", encoding="utf-8")
    stale_after_tamper = stale_publication_gate_artifacts(
        output_json_path=output_json,
        output_markdown_path=output_markdown,
    )
    assert stale_after_tamper == [output_markdown]
