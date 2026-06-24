import json

from finds_agentbench.manual_audit import (
    build_independent_reviewer_packet_validation_report,
    build_manual_audit_workflow_artifacts,
    compute_pairwise_review_packet_agreement,
    load_review_packet_csv,
    load_manual_audit_bundle,
    summarize_review_packet,
    write_independent_reviewer_packet_validation_artifacts,
    write_review_packet_csv,
)


def test_load_manual_audit_bundle_validates_repo_seed_subset():
    bundle = load_manual_audit_bundle()

    assert bundle.summary["status"] == "seed_author_adjudication_only"
    assert bundle.summary["case_count"] == 6
    assert bundle.summary["reviewed_task_count"] == 3
    assert bundle.summary["dimension_count"] == 6
    assert set(bundle.summary["run_types"]) == {"agent", "baseline"}
    assert bundle.summary["score_range"]["min_total_score"] == 6
    assert bundle.summary["score_range"]["max_total_score"] == 10

    logistic_case = next(
        case for case in bundle.subset["cases"] if case["case_id"] == "pilot_market_logistic_baseline_release_001"
    )
    assert logistic_case["total_score"] == 10
    assert (
        logistic_case["rubric_scores"]["baseline_comparison_or_counterfactual_context"]["score"] == 0
    )


def test_build_manual_audit_workflow_artifacts_writes_seed_template_and_report(tmp_path):
    bundle = load_manual_audit_bundle()

    result = build_manual_audit_workflow_artifacts(
        bundle=bundle,
        reviews_dir=tmp_path / "reviews",
        reports_dir=tmp_path / "reports",
        reviews_readme_path=tmp_path / "reviews" / "README.md",
        independent_reviewer_handoff_path=tmp_path / "reviews" / "independent_reviewer_handoff.md",
        reviewer_1_seed_path=tmp_path / "reviews" / "reviewer_1_seed.csv",
        reviewer_2_template_path=tmp_path / "reviews" / "reviewer_2_blank_template.csv",
        reviewer_2_shadow_path=tmp_path / "reviews" / "reviewer_2_shadow_demo.csv",
        agreement_json_path=tmp_path / "reports" / "agreement_summary.json",
        agreement_markdown_path=tmp_path / "reports" / "agreement_summary.md",
        adjudication_json_path=tmp_path / "reports" / "adjudication_queue.json",
        adjudication_markdown_path=tmp_path / "reports" / "adjudication_queue.md",
        reviewer_readiness_json_path=tmp_path / "reports" / "reviewer_readiness.json",
        reviewer_readiness_markdown_path=tmp_path / "reports" / "reviewer_readiness.md",
    )

    assert result["reviews_readme_path"].exists()
    assert result["independent_reviewer_handoff_path"].exists()
    assert result["independent_reviewer_packet_manifest_json_path"].exists()
    assert result["independent_reviewer_packet_manifest_markdown_path"].exists()
    assert result["reviewer_1_seed_path"].exists()
    assert result["reviewer_2_template_path"].exists()
    assert result["reviewer_2_shadow_path"].exists()
    assert result["agreement_json_path"].exists()
    assert result["agreement_markdown_path"].exists()
    assert result["adjudication_json_path"].exists()
    assert result["adjudication_markdown_path"].exists()
    assert result["reviewer_readiness_json_path"].exists()
    assert result["reviewer_readiness_markdown_path"].exists()
    assert result["independent_reviewer_packet_validation_json_path"].exists()
    assert result["independent_reviewer_packet_validation_markdown_path"].exists()

    summary = json.loads(result["agreement_json_path"].read_text(encoding="utf-8"))
    assert summary["status"] == "insufficient_independent_overlap"
    assert summary["exploratory_status"] == "pairwise_agreement_available"
    assert summary["eligible_reviewer_packet_count"] == 1
    assert summary["exploratory_eligible_reviewer_packet_count"] == 2

    adjudication = json.loads(result["adjudication_json_path"].read_text(encoding="utf-8"))
    assert adjudication["status"] == "adjudication_queue_ready"
    assert adjudication["entry_count"] > 0

    readiness = json.loads(result["reviewer_readiness_json_path"].read_text(encoding="utf-8"))
    readiness_markdown = result["reviewer_readiness_markdown_path"].read_text(encoding="utf-8")
    assert readiness["status"] == "not_ready_seed_only"
    assert readiness["ready_for_submission_claims"] is False
    assert readiness["seed_completed_reviewer_packet_count"] == 1
    assert readiness["independent_completed_reviewer_packet_count"] == 0
    assert readiness["required_independent_completed_reviewers"] == 1
    assert readiness["official_agreement_status"] == "insufficient_independent_overlap"
    assert any("independent reviewer packet" in item for item in readiness["blocking_items"])
    assert (
        result["independent_reviewer_packet_validation"]["status"]
        == "invalid_or_incomplete"
    )
    packet_manifest = json.loads(
        result["independent_reviewer_packet_manifest_json_path"].read_text(encoding="utf-8")
    )
    packet_manifest_markdown = result[
        "independent_reviewer_packet_manifest_markdown_path"
    ].read_text(encoding="utf-8")
    assert packet_manifest["status"] == "ready_for_independent_review_intake"
    assert packet_manifest["ready_for_reviewer_distribution"] is True
    assert packet_manifest["case_count"] == bundle.summary["case_count"]
    reviewer_facing_paths = {
        item["path"] for item in packet_manifest["reviewer_facing_files"]
    }
    assert any(path.endswith("reviewer_2_blank_template.csv") for path in reviewer_facing_paths)
    assert not any(path.endswith("reviewer_1_seed.csv") for path in reviewer_facing_paths)
    excluded_paths = {
        item["path"] for item in packet_manifest["excluded_from_reviewer_packet"]
    }
    assert any(path.endswith("reviewer_1_seed.csv") for path in excluded_paths)
    assert any(path.endswith("reviewer_2_shadow_demo.csv") for path in excluded_paths)
    assert any(path.endswith("adjudicated_subset.json") for path in excluded_paths)
    assert "Checksum manifest" in packet_manifest_markdown
    assert "reviewer_1_seed.csv" in packet_manifest_markdown
    assert "adjudicated_subset.json" in packet_manifest_markdown
    assert "reviewer_2_shadow_demo.csv" in readiness_markdown
    assert "must not be cited as official inter-rater agreement" in readiness_markdown
    handoff = result["independent_reviewer_handoff_path"].read_text(encoding="utf-8")
    assert "validate_manual_audit_review_packet.py" in handoff
    assert "ready_for_independent_agreement" in handoff


def test_build_manual_audit_workflow_artifacts_honors_custom_roots(tmp_path):
    result = build_manual_audit_workflow_artifacts(
        bundle=load_manual_audit_bundle(),
        reviews_dir=tmp_path / "custom_reviews",
        reports_dir=tmp_path / "custom_reports",
    )

    assert result["reviews_readme_path"] == tmp_path / "custom_reviews" / "README.md"
    assert (
        result["independent_reviewer_handoff_path"]
        == tmp_path / "custom_reviews" / "independent_reviewer_handoff.md"
    )
    assert (
        result["independent_reviewer_packet_manifest_json_path"]
        == tmp_path / "custom_reviews" / "independent_reviewer_packet_manifest.json"
    )
    assert (
        result["independent_reviewer_packet_manifest_markdown_path"]
        == tmp_path / "custom_reviews" / "independent_reviewer_packet_manifest.md"
    )
    assert result["reviewer_1_seed_path"] == tmp_path / "custom_reviews" / "reviewer_1_seed.csv"
    assert (
        result["reviewer_2_template_path"]
        == tmp_path / "custom_reviews" / "reviewer_2_blank_template.csv"
    )
    assert result["agreement_json_path"] == tmp_path / "custom_reports" / "agreement_summary.json"
    assert result["adjudication_json_path"] == tmp_path / "custom_reports" / "adjudication_queue.json"
    assert (
        result["independent_reviewer_packet_validation_json_path"]
        == tmp_path / "custom_reports" / "independent_reviewer_packet_validation.json"
    )
    assert (
        result["reviewer_readiness_markdown_path"]
        == tmp_path / "custom_reports" / "reviewer_readiness.md"
    )
    assert result["reviewer_readiness"]["status"] == "not_ready_seed_only"


def test_compute_pairwise_review_packet_agreement_is_perfect_for_identical_packets(tmp_path):
    bundle = load_manual_audit_bundle()
    result = build_manual_audit_workflow_artifacts(
        bundle=bundle,
        reviews_dir=tmp_path / "reviews",
        reports_dir=tmp_path / "reports",
        reviews_readme_path=tmp_path / "reviews" / "README.md",
        reviewer_1_seed_path=tmp_path / "reviews" / "reviewer_1_seed.csv",
        reviewer_2_template_path=tmp_path / "reviews" / "reviewer_2_blank_template.csv",
        reviewer_2_shadow_path=tmp_path / "reviews" / "reviewer_2_shadow_demo.csv",
        agreement_json_path=tmp_path / "reports" / "agreement_summary.json",
        agreement_markdown_path=tmp_path / "reports" / "agreement_summary.md",
        adjudication_json_path=tmp_path / "reports" / "adjudication_queue.json",
        adjudication_markdown_path=tmp_path / "reports" / "adjudication_queue.md",
        reviewer_readiness_json_path=tmp_path / "reports" / "reviewer_readiness.json",
        reviewer_readiness_markdown_path=tmp_path / "reports" / "reviewer_readiness.md",
    )

    left_rows = load_review_packet_csv(result["reviewer_1_seed_path"])
    right_rows = [dict(row, reviewer_id="reviewer_2_copy") for row in left_rows]

    left_packet = summarize_review_packet(
        result["reviewer_1_seed_path"],
        left_rows,
        bundle.rubric,
    )
    right_packet = summarize_review_packet(
        tmp_path / "reviews" / "reviewer_2_copy.csv",
        right_rows,
        bundle.rubric,
    )
    agreement = compute_pairwise_review_packet_agreement(left_packet, right_packet, bundle.rubric)

    assert agreement["status"] == "pairwise_agreement_available"
    assert agreement["overlap_case_count"] == bundle.summary["case_count"]
    assert agreement["overall_label_exact_agreement"] == 1.0
    assert agreement["exact_total_score_match_rate"] == 1.0
    assert agreement["mean_abs_total_score_diff"] == 0.0
    assert agreement["cases_with_any_disagreement"] == 0
    assert all(item["exact_agreement_rate"] == 1.0 for item in agreement["per_dimension"])


def test_independent_reviewer_packet_validator_rejects_blank_template(tmp_path):
    bundle = load_manual_audit_bundle()
    result = build_manual_audit_workflow_artifacts(
        bundle=bundle,
        reviews_dir=tmp_path / "reviews",
        reports_dir=tmp_path / "reports",
    )

    report = build_independent_reviewer_packet_validation_report(
        packet_path=result["reviewer_2_template_path"],
        bundle=bundle,
    )

    assert report["ready_for_independent_agreement"] is False
    assert report["status"] == "invalid_or_incomplete"
    assert any("review_source is not acceptable" in error for error in report["errors"])
    assert any("review_status must be complete" in error for error in report["errors"])


def test_independent_reviewer_packet_validator_accepts_completed_packet(tmp_path):
    bundle = load_manual_audit_bundle()
    result = build_manual_audit_workflow_artifacts(
        bundle=bundle,
        reviews_dir=tmp_path / "reviews",
        reports_dir=tmp_path / "reports",
    )
    rows = load_review_packet_csv(result["reviewer_1_seed_path"])
    completed_rows = [
        {
            **row,
            "reviewer_id": "reviewer_2_completed",
            "reviewer_role": "independent_reviewer",
            "review_status": "complete",
            "review_source": "independent_manual_review",
        }
        for row in rows
    ]
    packet_path = tmp_path / "reviews" / "reviewer_2_completed.csv"
    write_review_packet_csv(completed_rows, bundle.rubric, packet_path)

    report = build_independent_reviewer_packet_validation_report(
        packet_path=packet_path,
        bundle=bundle,
    )
    outputs = write_independent_reviewer_packet_validation_artifacts(
        report=report,
        output_json_path=tmp_path / "reports" / "independent_validation.json",
        output_markdown_path=tmp_path / "reports" / "independent_validation.md",
    )

    assert report["ready_for_independent_agreement"] is True
    assert report["status"] == "ready_for_independent_agreement"
    assert report["error_count"] == 0
    assert report["completed_case_count"] == bundle.summary["case_count"]
    assert outputs["json_path"].exists()
    assert "Ready for independent agreement" in outputs["markdown_path"].read_text(
        encoding="utf-8"
    )
