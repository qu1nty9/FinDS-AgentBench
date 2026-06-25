from finds_agentbench.submission_readiness import (
    build_submission_evidence_ledger,
    build_submission_readiness_report,
    render_submission_evidence_ledger_markdown,
)


def complete_review_rows() -> list[dict[str, str]]:
    return [
        {
            "review_type": "finding_review",
            "review_status": "complete",
            "review_decision": "true_positive",
        },
        {
            "review_type": "clean_control_review",
            "review_status": "complete",
            "review_decision": "true_negative",
        },
    ]


def base_manifest() -> dict:
    return {
        "benchmark_id": "finds_agentbench_pilot_v0",
        "benchmark_version": "0.1.0",
        "release_stage": "pilot",
        "task_count": 9,
        "runnable_task_count": 9,
        "statistical_artifacts_path": "docs/releases/pilot_v0/statistical_artifacts/README.md",
        "independent_participant_brief_path": "docs/releases/pilot_v0/independent_participant_brief.md",
        "manual_audit": {
            "ready_for_submission_claims": False,
            "reviewer_readiness_status": "not_ready_seed_only",
            "case_count": 6,
            "independent_completed_reviewer_packet_count": 0,
            "agreement_status": "insufficient_independent_overlap",
            "reviewer_readiness_blocking_items": ["Complete second reviewer packet."],
            "readme_path": "audits/pilot_v0/README.md",
            "rubric_path": "audits/pilot_v0/manual_audit_rubric.yaml",
            "subset_path": "audits/pilot_v0/adjudicated_subset.json",
            "reviews_readme_path": "audits/pilot_v0/reviews/README.md",
            "reviewer_readiness_markdown_path": "audits/pilot_v0/reports/reviewer_readiness.md",
            "agreement_report_markdown_path": "audits/pilot_v0/reports/agreement_summary.md",
            "adjudication_report_markdown_path": "audits/pilot_v0/reports/adjudication_queue.md",
            "independent_reviewer_handoff_path": "audits/pilot_v0/reviews/independent_reviewer_handoff.md",
            "independent_reviewer_packet_manifest_markdown_path": "audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md",
            "independent_reviewer_packet_validation_markdown_path": "audits/pilot_v0/reports/independent_reviewer_packet_validation.md",
        },
        "external_agents": {
            "ready_for_external_agent_claims": False,
            "readiness_status": "not_ready_no_external_agents",
            "completed_external_agent_configuration_count": 0,
            "external_task_coverage_count": 0,
            "expected_task_count": 8,
            "blocking_items": ["Register external agent."],
            "registry_path": "agents/external_agent_registry.yaml",
            "handoff_markdown_path": "agents/external_agent_handoff.md",
            "intake_manifest_markdown_path": "docs/releases/pilot_v0/external_agent_intake_manifest.md",
            "protocol_markdown_path": "docs/releases/pilot_v0/external_agent_protocol.md",
            "readiness_markdown_path": "docs/releases/pilot_v0/external_agent_readiness.md",
            "registration_validation_markdown_path": "docs/releases/pilot_v0/external_agent_registration_validation.md",
        },
        "release_archive_path": "dist/release_archives/finds_agentbench_pilot_v0-0.1.0-pilot.tar.gz",
        "release_archive_manifest_json_path": "docs/releases/pilot_v0/archive_manifest.json",
        "release_archive_manifest_markdown_path": "docs/releases/pilot_v0/archive_manifest.md",
    }


def methodology_summary() -> dict:
    return {
        "counts": {"scanned_file_count": 617},
        "review_packet": {
            "finding_row_count": 5,
            "clean_control_row_count": 14,
        },
        "fixture_evaluation": {"true_positive_count": 4},
    }


def test_submission_readiness_report_collects_blocking_gates():
    report = build_submission_readiness_report(
        manifest=base_manifest(),
        methodology_calibration_summary=methodology_summary(),
        methodology_review_rows=[{"review_status": "template", "review_decision": ""}],
    )

    assert report["status"] == "not_ready_for_workshop_submission"
    assert report["ready_for_workshop_submission"] is False
    assert report["ready_gate_count"] == 2
    assert report["blocking_gate_count"] == 4
    assert "Complete second reviewer packet." in report["blocking_items"]
    assert "Register external agent." in report["blocking_items"]
    assert any(gate["gate_id"] == "methodology_calibration_review" for gate in report["gates"])


def test_submission_readiness_report_keeps_release_tag_as_final_blocker():
    manifest = base_manifest()
    manifest["manual_audit"] = {
        **manifest["manual_audit"],
        "ready_for_submission_claims": True,
        "reviewer_readiness_status": "ready_for_submission_claims",
        "independent_completed_reviewer_packet_count": 1,
        "agreement_status": "pairwise_agreement_available",
        "reviewer_readiness_blocking_items": [],
    }
    manifest["external_agents"] = {
        **manifest["external_agents"],
        "ready_for_external_agent_claims": True,
        "readiness_status": "ready_for_external_agent_claims",
        "completed_external_agent_configuration_count": 1,
        "external_task_coverage_count": 8,
        "blocking_items": [],
    }

    report = build_submission_readiness_report(
        manifest=manifest,
        methodology_calibration_summary=methodology_summary(),
        methodology_review_rows=complete_review_rows(),
    )

    assert report["status"] == "not_ready_for_workshop_submission"
    assert report["ready_gate_count"] == 5
    assert report["blocking_gate_count"] == 1
    assert report["blocking_items"] == [
        "Create a release tag and archive the release artifact bundle after the remaining gates pass."
    ]


def test_submission_evidence_ledger_records_claim_boundaries():
    manifest = base_manifest()
    report = build_submission_readiness_report(
        manifest=manifest,
        methodology_calibration_summary=methodology_summary(),
        methodology_review_rows=complete_review_rows(),
    )

    ledger = build_submission_evidence_ledger(report=report, manifest=manifest)
    markdown = render_submission_evidence_ledger_markdown(ledger)

    assert ledger["status"] == "submission_evidence_incomplete"
    assert ledger["blocking_gate_count"] == 3
    assert "Independent manual-audit agreement" in " ".join(
        ledger["current_disallowed_claims"]
    )
    manual_gate = next(
        gate for gate in ledger["gates"] if gate["gate_id"] == "manual_audit_independent_review"
    )
    manual_paths = {entry["path"] for entry in manual_gate["evidence_artifacts"]}
    assert manual_gate["claim_status"] == "claim_blocked"
    assert "audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md" in manual_paths
    assert "docs/releases/pilot_v0/independent_participant_brief.md" in manual_paths
    external_gate = next(
        gate for gate in ledger["gates"] if gate["gate_id"] == "external_agent_evidence"
    )
    external_paths = {entry["path"] for entry in external_gate["evidence_artifacts"]}
    assert "docs/releases/pilot_v0/independent_participant_brief.md" in external_paths
    assert any("build_manual_audit_workflow.py" in command for command in manual_gate["verification_commands"])
    assert "# Submission Evidence Ledger" in markdown
    assert "## Disallowed Current Claims" in markdown
