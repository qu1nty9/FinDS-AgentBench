from finds_agentbench.submission_readiness import build_submission_readiness_report


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
        "manual_audit": {
            "ready_for_submission_claims": False,
            "reviewer_readiness_status": "not_ready_seed_only",
            "case_count": 6,
            "independent_completed_reviewer_packet_count": 0,
            "agreement_status": "insufficient_independent_overlap",
            "reviewer_readiness_blocking_items": ["Complete second reviewer packet."],
        },
        "external_agents": {
            "ready_for_external_agent_claims": False,
            "readiness_status": "not_ready_no_external_agents",
            "completed_external_agent_configuration_count": 0,
            "external_task_coverage_count": 0,
            "expected_task_count": 8,
            "blocking_items": ["Register external agent."],
        },
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
