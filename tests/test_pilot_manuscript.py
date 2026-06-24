import json
from pathlib import Path

from finds_agentbench.pilot_manuscript import build_pilot_manuscript


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_pilot_manuscript_writes_traceable_workshop_scaffold(tmp_path: Path):
    manifest = {
        "benchmark_id": "finds_agentbench_pilot_v0",
        "benchmark_version": "0.1.0",
        "release_stage": "pilot",
        "task_count": 9,
        "runnable_task_count": 9,
        "tracks": [
            {"track": "predictive_financial_ml"},
            {"track": "event_aware_time_series_reasoning"},
            {"track": "research_replication_and_audit"},
        ],
        "protocols": [
            {
                "protocol_id": "pilot_protocol",
                "task_ids": ["task_a", "task_b"],
            }
        ],
        "manual_audit": {
            "case_count": 6,
            "reviewed_task_count": 3,
            "status": "seed_author_adjudication_only",
            "reviewer_readiness_status": "not_ready_seed_only",
            "ready_for_submission_claims": False,
            "independent_completed_reviewer_packet_count": 0,
            "reviewer_readiness_markdown_path": "audits/pilot_v0/reports/reviewer_readiness.md",
            "reviewer_readiness_blocking_items": [
                "Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.",
                "Rebuild official agreement reporting after an independent completed packet is available.",
            ],
            "agreement_status": "insufficient_independent_overlap",
            "exploratory_agreement_status": "pairwise_agreement_available",
        },
        "external_agents": {
            "readiness_status": "not_ready_no_external_agents",
            "ready_for_external_agent_claims": False,
            "external_agent_configuration_count": 0,
            "completed_external_agent_configuration_count": 0,
            "blocking_items": [
                "Register and run at least one non-author external agent configuration through the pilot harness.",
                "Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.",
            ],
        },
        "release_build_command": "PYTHONPATH=src python scripts/build_pilot_release.py --repeat 3",
    }
    reference_results = {
        "sections": [
            {
                "section_id": "pilot_protocol",
                "rows": [
                    {
                        "task_id": "task_a",
                        "agent_id": "baseline_a",
                        "run_type": "baseline",
                        "run_count": 3,
                        "completed_count": 3,
                    },
                    {
                        "task_id": "task_a",
                        "agent_id": "agent_a",
                        "run_type": "agent",
                        "run_count": 3,
                        "completed_count": 3,
                    },
                ],
            }
        ]
    }
    statistical_comparison = {
        "rows": [
            {"metric": "score.overall_score", "direction": "baseline_higher"},
            {"metric": "score.overall_score", "direction": "tie"},
            {"metric": "score.roc_auc", "direction": "agent_higher"},
        ]
    }
    manual_audit_subset = {
        "cases": [
            {
                "case_id": "case_a",
                "task_id": "task_a",
                "run_type": "agent",
                "agent_id": "agent_a",
                "run_label": "run_a",
                "artifact_root": "runs/task_a/agent_a/run_a",
                "source_paths": {"writeup": "runs/task_a/agent_a/run_a/writeup.md"},
                "overall_label": "minimally_defensible",
                "total_score": 6,
                "rubric_scores": {
                    "quantitative_evidence_use": {
                        "score": 0,
                        "evidence": "No quantitative evidence is provided.",
                    },
                    "claim_discipline": {
                        "score": 2,
                        "evidence": "Claims stay narrow.",
                    },
                },
                "primary_manual_findings": ["No quantitative support."],
                "adjudication_note": "Useful failure example.",
            }
        ]
    }

    manifest_path = tmp_path / "release" / "manifest.json"
    reference_path = tmp_path / "release" / "reference_results.json"
    manual_audit_subset_path = tmp_path / "audit" / "adjudicated_subset.json"
    comparison_path = tmp_path / "release" / "stats" / "agent_vs_best_baseline.json"
    methods_path = tmp_path / "release" / "stats" / "methods" / "statistical_methods.tex"
    summary_table_path = tmp_path / "release" / "stats" / "tables" / "summary.tex"
    comparison_table_path = tmp_path / "release" / "stats" / "tables" / "comparison.tex"
    protocol_table_path = tmp_path / "release" / "paper" / "pilot_protocol.tex"
    for path in (methods_path, summary_table_path, comparison_table_path, protocol_table_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("% input\n", encoding="utf-8")
    write_json(manifest_path, manifest)
    write_json(reference_path, reference_results)
    write_json(manual_audit_subset_path, manual_audit_subset)
    write_json(comparison_path, statistical_comparison)

    result = build_pilot_manuscript(
        manifest_path=manifest_path,
        reference_results_path=reference_path,
        manual_audit_subset_path=manual_audit_subset_path,
        statistical_comparison_path=comparison_path,
        statistical_methods_tex_path=methods_path,
        summary_uncertainty_table_path=summary_table_path,
        agent_vs_baseline_table_path=comparison_table_path,
        protocol_table_path=protocol_table_path,
        output_dir=tmp_path / "papers" / "workshop_pilot",
    )

    main_tex = result.main_tex_path.read_text(encoding="utf-8")
    readme = result.readme_path.read_text(encoding="utf-8")
    checklist = result.checklist_path.read_text(encoding="utf-8")
    audit_examples_tex = result.audit_failure_examples_tex_path.read_text(encoding="utf-8")
    audit_examples_markdown = result.audit_failure_examples_markdown_path.read_text(encoding="utf-8")
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "\\title{FinDS-AgentBench" in main_tex
    assert "\\input{related_work.tex}" in main_tex
    assert "\\input{audit_failure_examples.tex}" in main_tex
    assert "\\bibliography{references}" in main_tex
    assert "\\input{" in main_tex
    assert "baseline-higher" not in main_tex
    assert "2 task-system cells" in main_tex
    assert "not\\_ready\\_seed\\_only" in main_tex
    assert "not\\_ready\\_no\\_external\\_agents" in main_tex
    assert "Workshop Pilot Manuscript" in readme
    assert "Reviewer Readiness" in readme
    assert "External Agent Readiness" in readme
    assert result.related_work_tex_path.exists()
    assert result.references_bib_path.exists()
    assert result.audit_failure_examples_tex_path.exists()
    assert result.audit_failure_examples_markdown_path.exists()
    assert result.audit_failure_examples_json_path.exists()
    assert "Related Work" in result.related_work_tex_path.read_text(encoding="utf-8")
    assert "@article{mlebench2024" in result.references_bib_path.read_text(encoding="utf-8")
    assert "Qualitative Failure Examples" in audit_examples_tex
    assert "case_a" in audit_examples_markdown
    assert "Required Before Submission" in checklist
    assert "Generated qualitative failure examples" in checklist
    assert "Reviewer-readiness report" in checklist
    assert "Complete at least one independent reviewer packet" in checklist
    assert "External-agent protocol and readiness report" in checklist
    assert "External-Agent Gate Blockers" in checklist
    assert "Register and run at least one non-author external agent" in checklist
    assert metadata["overall_baseline_higher_count"] == 1
    assert metadata["overall_tie_count"] == 1
    assert metadata["reviewer_readiness_status"] == "not_ready_seed_only"
    assert metadata["external_agent_readiness_status"] == "not_ready_no_external_agents"
