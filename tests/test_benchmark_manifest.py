import json
from pathlib import Path

from finds_agentbench.benchmark_manifest import (
    PILOT_RELEASE_BUILD_COMMAND,
    build_benchmark_manifest,
)


def test_build_benchmark_manifest_generates_release_index(tmp_path: Path):
    cards_root = tmp_path / "cards"
    data_manifests_root = tmp_path / "data_manifests"
    output_root = tmp_path / "release"

    result = build_benchmark_manifest(
        tasks_root=Path("tasks/pilot"),
        cards_root=cards_root,
        data_manifests_root=data_manifests_root,
        output_root=output_root,
    )

    assert result.manifest_path.exists()
    assert result.readme_path.exists()
    assert result.cards_index_path.exists()
    assert result.data_manifests_readme_path.exists()

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    readme = result.readme_path.read_text(encoding="utf-8")

    assert manifest["benchmark_id"] == "finds_agentbench_pilot_v0"
    assert manifest["release_stage"] == "pilot"
    assert manifest["release_build_command"] == PILOT_RELEASE_BUILD_COMMAND
    assert manifest["tasks_root"] == "tasks/pilot"
    assert manifest["cards_root"] == "docs/cards"
    assert manifest["data_manifests_root"] == "docs/data_manifests/pilot_v0"
    assert manifest["reference_results_path"] == "docs/releases/pilot_v0/reference_results.md"
    assert manifest["paper_artifacts_path"] == "docs/releases/pilot_v0/paper_artifacts/README.md"
    assert (
        manifest["statistical_artifacts_path"]
        == "docs/releases/pilot_v0/statistical_artifacts/README.md"
    )
    assert (
        manifest["release_archive_path"]
        == "dist/release_archives/finds_agentbench_pilot_v0-0.1.0-pilot.tar.gz"
    )
    assert (
        manifest["release_archive_manifest_json_path"]
        == "docs/releases/pilot_v0/archive_manifest.json"
    )
    assert (
        manifest["release_archive_manifest_markdown_path"]
        == "docs/releases/pilot_v0/archive_manifest.md"
    )
    assert manifest["external_agents"]["registry_path"] == "agents/external_agent_registry.yaml"
    assert (
        manifest["external_agents"]["protocol_markdown_path"]
        == "docs/releases/pilot_v0/external_agent_protocol.md"
    )
    assert manifest["external_agents"]["handoff_markdown_path"] == "agents/external_agent_handoff.md"
    assert (
        manifest["external_agents"]["intake_manifest_markdown_path"]
        == "docs/releases/pilot_v0/external_agent_intake_manifest.md"
    )
    assert (
        manifest["external_agents"]["intake_manifest_status"]
        == "ready_for_external_agent_intake"
    )
    assert (
        manifest["external_agents"]["readiness_markdown_path"]
        == "docs/releases/pilot_v0/external_agent_readiness.md"
    )
    assert (
        manifest["external_agents"]["registration_validation_markdown_path"]
        == "docs/releases/pilot_v0/external_agent_registration_validation.md"
    )
    assert (
        manifest["external_agents"]["registration_validation_status"]
        == "no_external_agent_registered"
    )
    assert manifest["external_agents"]["readiness_status"] == "not_ready_no_external_agents"
    assert manifest["external_agents"]["ready_for_external_agent_claims"] is False
    assert manifest["external_agents"]["bundled_reference_agent_count"] >= 7
    assert manifest["external_agents"]["external_agent_configuration_count"] == 0
    assert manifest["external_agents"]["completed_external_agent_configuration_count"] == 0
    assert manifest["external_agents"]["external_task_coverage_count"] == 0
    assert manifest["external_agents"]["expected_task_count"] == 8
    assert any(
        "non-author external agent" in item for item in manifest["external_agents"]["blocking_items"]
    )
    assert (
        manifest["submission_readiness"]["markdown_path"]
        == "docs/releases/pilot_v0/submission_readiness.md"
    )
    assert (
        manifest["submission_readiness"]["json_path"]
        == "docs/releases/pilot_v0/submission_readiness.json"
    )
    assert (
        manifest["submission_readiness"]["evidence_ledger_markdown_path"]
        == "docs/releases/pilot_v0/submission_evidence_ledger.md"
    )
    assert (
        manifest["submission_readiness"]["evidence_ledger_status"]
        == "submission_evidence_incomplete"
    )
    assert manifest["submission_readiness"]["status"] == "not_ready_for_workshop_submission"
    assert manifest["submission_readiness"]["ready_for_workshop_submission"] is False
    assert manifest["submission_readiness"]["gate_count"] == 6
    assert manifest["submission_readiness"]["ready_gate_count"] == 3
    assert manifest["submission_readiness"]["blocking_gate_count"] == 3
    assert any(
        "Complete at least one independent reviewer packet" in item
        for item in manifest["submission_readiness"]["blocking_items"]
    )
    assert not any(
        "methodology calibration" in item.lower()
        for item in manifest["submission_readiness"]["blocking_items"]
    )
    assert manifest["manual_audit"]["rubric_path"] == "audits/pilot_v0/manual_audit_rubric.yaml"
    assert manifest["manual_audit"]["subset_path"] == "audits/pilot_v0/adjudicated_subset.json"
    assert manifest["manual_audit"]["readme_path"] == "audits/pilot_v0/README.md"
    assert manifest["manual_audit"]["reviews_readme_path"] == "audits/pilot_v0/reviews/README.md"
    assert (
        manifest["manual_audit"]["independent_reviewer_handoff_path"]
        == "audits/pilot_v0/reviews/independent_reviewer_handoff.md"
    )
    assert (
        manifest["manual_audit"]["independent_reviewer_packet_manifest_markdown_path"]
        == "audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md"
    )
    assert (
        manifest["manual_audit"]["independent_reviewer_packet_manifest_status"]
        == "ready_for_independent_review_intake"
    )
    assert (
        manifest["manual_audit"]["independent_reviewer_packet_validation_markdown_path"]
        == "audits/pilot_v0/reports/independent_reviewer_packet_validation.md"
    )
    assert manifest["manual_audit"]["reviewer_1_seed_path"] == "audits/pilot_v0/reviews/reviewer_1_seed.csv"
    assert (
        manifest["manual_audit"]["reviewer_2_template_path"]
        == "audits/pilot_v0/reviews/reviewer_2_blank_template.csv"
    )
    assert (
        manifest["manual_audit"]["agreement_report_markdown_path"]
        == "audits/pilot_v0/reports/agreement_summary.md"
    )
    assert (
        manifest["manual_audit"]["adjudication_report_markdown_path"]
        == "audits/pilot_v0/reports/adjudication_queue.md"
    )
    assert (
        manifest["manual_audit"]["reviewer_readiness_markdown_path"]
        == "audits/pilot_v0/reports/reviewer_readiness.md"
    )
    assert manifest["manual_audit"]["reviewer_readiness_status"] == "not_ready_seed_only"
    assert manifest["manual_audit"]["ready_for_submission_claims"] is False
    assert manifest["manual_audit"]["independent_completed_reviewer_packet_count"] == 0
    assert any(
        "independent reviewer packet" in item
        for item in manifest["manual_audit"]["reviewer_readiness_blocking_items"]
    )
    assert manifest["manual_audit"]["agreement_status"] == "insufficient_independent_overlap"
    assert manifest["manual_audit"]["exploratory_agreement_status"] == "pairwise_agreement_available"
    assert manifest["manual_audit"]["eligible_reviewer_packet_count"] == 1
    assert manifest["manual_audit"]["exploratory_eligible_reviewer_packet_count"] == 2
    assert manifest["manual_audit"]["exploratory_pairwise_agreement_count"] >= 1
    assert manifest["manual_audit"]["adjudication_entry_count"] >= 1
    assert manifest["manual_audit"]["case_count"] >= 6
    assert manifest["manual_audit"]["reviewed_task_count"] >= 3
    assert manifest["task_count"] >= 5
    assert manifest["runnable_task_count"] >= 5
    assert {"pilot_baseline_suite", "pilot_agent_suite", "pilot_protocol"}.issubset(
        {protocol["protocol_id"] for protocol in manifest["protocols"]}
    )
    pilot_agent_protocol = next(
        protocol for protocol in manifest["protocols"] if protocol["protocol_id"] == "pilot_agent_suite"
    )

    rates_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "yield_direction_treasury10y_v0"
    )
    usd_entry = next(task for task in manifest["tasks"] if task["task_id"] == "usd_broad_direction_v0")
    usd_relative_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "usd_afe_vs_eme_relative_direction_v0"
    )
    front_end_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "front_end_spread_widening_v0"
    )
    curve_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "yield_curve_10y2y_steepening_v0"
    )
    curve3mo_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "yield_curve_10y3mo_steepening_v0"
    )
    market_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "synthetic_market_direction_v0"
    )
    assert rates_entry["runnable"] is True
    assert rates_entry["release_status"] == "runnable_public_pilot"
    assert curve_entry["runnable"] is True
    assert curve_entry["release_status"] == "runnable_public_pilot"
    assert curve3mo_entry["runnable"] is True
    assert curve3mo_entry["release_status"] == "runnable_public_pilot"
    assert front_end_entry["runnable"] is True
    assert front_end_entry["release_status"] == "runnable_public_pilot"
    assert usd_entry["runnable"] is True
    assert usd_relative_entry["runnable"] is True
    assert market_entry["runnable"] is True
    assert market_entry["task_card_path"] == "docs/cards/tasks/synthetic_market_direction_v0.md"
    assert market_entry["data_manifest_path"] == "docs/data_manifests/pilot_v0/synthetic_market_direction_v0.json"
    assert "public_data_present" in market_entry
    assert "yield_direction_treasury10y_v0" in pilot_agent_protocol["task_ids"]
    assert "yield_curve_10y2y_steepening_v0" in pilot_agent_protocol["task_ids"]
    assert "yield_curve_10y3mo_steepening_v0" in pilot_agent_protocol["task_ids"]
    assert "front_end_spread_widening_v0" in pilot_agent_protocol["task_ids"]
    assert "usd_broad_direction_v0" in pilot_agent_protocol["task_ids"]
    assert "usd_afe_vs_eme_relative_direction_v0" in pilot_agent_protocol["task_ids"]
    assert "--treasury-snapshot-date 2026-06-21" in pilot_agent_protocol["command"]
    assert "--curve-snapshot-date 2026-06-21" in pilot_agent_protocol["command"]
    assert "--curve3mo-snapshot-date 2026-06-21" in pilot_agent_protocol["command"]
    assert "--front-end-snapshot-date 2026-06-21" in pilot_agent_protocol["command"]
    assert "--usd-snapshot-date 2026-06-21" in pilot_agent_protocol["command"]
    assert "--clean-existing-runs" in pilot_agent_protocol["command"]
    assert "--clean-existing-outputs" in PILOT_RELEASE_BUILD_COMMAND
    assert "Canonical pilot release manifest for FinDS-AgentBench." in readme
    assert "../../cards/tasks/yield_direction_treasury10y_v0.md" in readme
    assert "../../cards/tasks/yield_curve_10y2y_steepening_v0.md" in readme
    assert "../../cards/tasks/yield_curve_10y3mo_steepening_v0.md" in readme
    assert "../../cards/tasks/front_end_spread_widening_v0.md" in readme
    assert "../../cards/tasks/usd_broad_direction_v0.md" in readme
    assert "../../cards/tasks/usd_afe_vs_eme_relative_direction_v0.md" in readme
    assert "../../cards/tasks/synthetic_market_direction_v0.md" in readme
    assert "../../data_manifests/pilot_v0/README.md" in readme
    assert "reference_results.md" in readme
    assert "paper_artifacts/README.md" in readme
    assert "statistical_artifacts/README.md" in readme
    assert "External Agent Protocol" in readme
    assert "External Agent Handoff" in readme
    assert "External Agent Intake Manifest" in readme
    assert "docs/releases/pilot_v0/external_agent_intake_manifest.md" in readme
    assert "External Agent Readiness" in readme
    assert "Registration Validation" in readme
    assert "Submission Readiness" in readme
    assert "Submission Evidence Ledger" in readme
    assert "docs/releases/pilot_v0/submission_evidence_ledger.md" in readme
    assert "not_ready_no_external_agents" in readme
    assert "not_ready_for_workshop_submission" in readme
    assert "0 / 8" in readme
    assert "scripts/build_pilot_release.py" in readme
    assert "audits/pilot_v0/README.md" in readme
    assert "audits/pilot_v0/manual_audit_rubric.yaml" in readme
    assert "audits/pilot_v0/adjudicated_subset.json" in readme
    assert "audits/pilot_v0/reviews/README.md" in readme
    assert "audits/pilot_v0/reviews/independent_reviewer_handoff.md" in readme
    assert "audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md" in readme
    assert "audits/pilot_v0/reports/independent_reviewer_packet_validation.md" in readme
    assert "audits/pilot_v0/reviews/reviewer_1_seed.csv" in readme
    assert "audits/pilot_v0/reviews/reviewer_2_blank_template.csv" in readme
    assert "audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv" in readme
    assert "audits/pilot_v0/reports/agreement_summary.md" in readme
    assert "audits/pilot_v0/reports/adjudication_queue.md" in readme
    assert "audits/pilot_v0/reports/reviewer_readiness.md" in readme
    assert "not_ready_seed_only" in readme
