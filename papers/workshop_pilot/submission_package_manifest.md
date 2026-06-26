# Workshop Submission Package Manifest

Submission-level wrapper around the manuscript source, release candidate, evidence ledger, publication gate, and archive checksum manifest.

## Status

| Field | Value |
| --- | --- |
| Benchmark ID | finds_agentbench_pilot_v0 |
| Benchmark Version | 0.1.0 |
| Release Stage | pilot |
| Package Status | `candidate_blocked_on_evidence_gates` |
| Ready for Workshop Submission Package | no |
| Publication Gate | `blocked_on_submission_evidence` |
| Submission Readiness | `not_ready_for_workshop_submission` |
| Formatting Status | `pdf_compile_verified` |
| Archive Status | `candidate_unfrozen` |
| Archive SHA256 | `c28ce7d780845b2ed9ee99ee3e9ffdbf516123bc5940211751a6f800276e8f5b` |
| Artifacts | 67 |
| Missing Required Artifacts | 0 |

## Stage Targets

| Target | Status | Scope |
| --- | --- | --- |
| arxiv_workshop | `not_ready_blocked_by_current_gates` | Pilot manuscript plus deterministic public benchmark release candidate. |
| top_benchmark_dataset_venue | `not_ready_requires_scale_and_external_validation` | Dataset/benchmark paper with public harness, stronger agent coverage, and governance. |
| journal_extension | `not_ready_requires_longitudinal_reliability_study` | Methodological extension focused on reliability and model-risk implications. |

## Blocking Items

- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
- Create a release tag and archive the release artifact bundle after the remaining gates pass.

## Missing Required Artifacts

- None.

## Allowed Current Claims

- The pilot release is within the planned 8-12 runnable-task workshop scope.
- Pilot uncertainty and paired-comparison statistical artifacts are generated.
- The manual-audit subset has completed independent-review evidence and official agreement reporting.
- External-agent registration, handoff, and readiness gates are available.
- Methodology-calibration findings have a completed author review packet.
- A deterministic candidate archive and archive manifest can be built before final tagging.

## Disallowed Current Claims

- Independent external-agent performance evidence.
- A frozen tagged release archive exists.

## Artifact Inventory

| Group | Role | Path | Kind | Exists |
| --- | --- | --- | --- | --- |
| manuscript | main_tex | papers/workshop_pilot/main.tex | file | yes |
| manuscript | related_work_tex | papers/workshop_pilot/related_work.tex | file | yes |
| manuscript | references_bib | papers/workshop_pilot/references.bib | file | yes |
| manuscript | metadata | papers/workshop_pilot/metadata.json | file | yes |
| manuscript | audit_failure_examples_tex | papers/workshop_pilot/audit_failure_examples.tex | file | yes |
| manuscript | audit_failure_examples_md | papers/workshop_pilot/audit_failure_examples.md | file | yes |
| manuscript | formatting_check_json | papers/workshop_pilot/formatting_check.json | file | yes |
| manuscript | formatting_check_md | papers/workshop_pilot/formatting_check.md | file | yes |
| manuscript | submission_readiness_checklist | papers/workshop_pilot/submission_readiness_checklist.md | file | yes |
| manuscript | compiled_pdf | papers/workshop_pilot/main.pdf | file | yes |
| paper_inputs | reference_results | docs/releases/pilot_v0/reference_results.md | file | yes |
| paper_inputs | paper_artifacts_index | docs/releases/pilot_v0/paper_artifacts/README.md | file | yes |
| paper_inputs | statistical_artifacts_index | docs/releases/pilot_v0/statistical_artifacts/README.md | file | yes |
| paper_inputs | agent_vs_baseline_table | docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex | file | yes |
| paper_inputs | uncertainty_table | docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex | file | yes |
| release_candidate | release_manifest | docs/releases/pilot_v0/manifest.json | file | yes |
| release_candidate | release_readme | docs/releases/pilot_v0/README.md | file | yes |
| release_candidate | archive_manifest_json | docs/releases/pilot_v0/archive_manifest.json | file | yes |
| release_candidate | archive_manifest_md | docs/releases/pilot_v0/archive_manifest.md | file | yes |
| release_candidate | publication_gate_json | docs/releases/pilot_v0/publication_gate_manifest.json | file | yes |
| release_candidate | publication_gate_md | docs/releases/pilot_v0/publication_gate_manifest.md | file | yes |
| release_candidate | submission_readiness_json | docs/releases/pilot_v0/submission_readiness.json | file | yes |
| release_candidate | submission_readiness_md | docs/releases/pilot_v0/submission_readiness.md | file | yes |
| release_candidate | evidence_ledger_json | docs/releases/pilot_v0/submission_evidence_ledger.json | file | yes |
| release_candidate | evidence_ledger_md | docs/releases/pilot_v0/submission_evidence_ledger.md | file | yes |
| ci | github_actions_workflow | .github/workflows/ci.yml | file | yes |
| package_control | submission_package_script | scripts/build_submission_package_manifest.py | file | yes |
| package_control | submission_package_module | src/finds_agentbench/submission_package.py | file | yes |
| package_control | publication_gate_script | scripts/build_publication_gate_manifest.py | file | yes |
| package_control | publication_gate_module | src/finds_agentbench/publication_gate.py | file | yes |
| release_candidate | release_archive | dist/release_archives/finds_agentbench_pilot_v0-0.1.0-pilot.tar.gz | file | declared |
| submission_package | submission_package_json | papers/workshop_pilot/submission_package_manifest.json | file | declared |
| submission_package | submission_package_markdown | papers/workshop_pilot/submission_package_manifest.md | file | declared |
| evidence:pilot_release_scope | release_manifest | docs/releases/pilot_v0/manifest.json | file | yes |
| evidence:pilot_release_scope | release_readme | docs/releases/pilot_v0/README.md | file | yes |
| evidence:pilot_release_scope | task_registry_json | docs/cards/task_registry.json | file | yes |
| evidence:pilot_release_scope | task_registry_csv | docs/cards/task_registry.csv | file | yes |
| evidence:pilot_release_scope | task_cards_index | docs/cards | directory | yes |
| evidence:pilot_release_scope | data_manifests_index | docs/data_manifests/pilot_v0 | directory | yes |
| evidence:statistical_artifacts | statistical_artifacts_index | docs/releases/pilot_v0/statistical_artifacts/README.md | file | yes |
| evidence:statistical_artifacts | summary_uncertainty | docs/releases/pilot_v0/statistical_artifacts/summary_uncertainty.md | file | yes |
| evidence:statistical_artifacts | agent_vs_best_baseline | docs/releases/pilot_v0/statistical_artifacts/agent_vs_best_baseline.md | file | yes |
| evidence:statistical_artifacts | statistical_methods | docs/releases/pilot_v0/statistical_artifacts/methods/statistical_methods.md | file | yes |
| evidence:manual_audit_independent_review | independent_participant_brief | docs/releases/pilot_v0/independent_participant_brief.md | file | yes |
| evidence:manual_audit_independent_review | manual_audit_readme | audits/pilot_v0/README.md | file | yes |
| evidence:manual_audit_independent_review | rubric | audits/pilot_v0/manual_audit_rubric.yaml | file | yes |
| evidence:manual_audit_independent_review | seed_subset | audits/pilot_v0/adjudicated_subset.json | file | yes |
| evidence:manual_audit_independent_review | reviews_workflow | audits/pilot_v0/reviews/README.md | file | yes |
| evidence:manual_audit_independent_review | reviewer_readiness | audits/pilot_v0/reports/reviewer_readiness.md | file | yes |
| evidence:manual_audit_independent_review | agreement_report | audits/pilot_v0/reports/agreement_summary.md | file | yes |
| evidence:manual_audit_independent_review | adjudication_queue | audits/pilot_v0/reports/adjudication_queue.md | file | yes |
| evidence:manual_audit_independent_review | independent_handoff | audits/pilot_v0/reviews/independent_reviewer_handoff.md | file | yes |
| evidence:manual_audit_independent_review | independent_packet_manifest | audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md | file | yes |
| evidence:manual_audit_independent_review | independent_packet_validation | audits/pilot_v0/reports/independent_reviewer_packet_validation.md | file | yes |
| evidence:external_agent_evidence | independent_participant_brief | docs/releases/pilot_v0/independent_participant_brief.md | file | yes |
| evidence:external_agent_evidence | external_agent_registry | agents/external_agent_registry.yaml | file | yes |
| evidence:external_agent_evidence | external_agent_handoff | agents/external_agent_handoff.md | file | yes |
| evidence:external_agent_evidence | external_agent_intake_manifest | docs/releases/pilot_v0/external_agent_intake_manifest.md | file | yes |
| evidence:external_agent_evidence | external_agent_protocol | docs/releases/pilot_v0/external_agent_protocol.md | file | yes |
| evidence:external_agent_evidence | external_agent_readiness | docs/releases/pilot_v0/external_agent_readiness.md | file | yes |
| evidence:external_agent_evidence | external_agent_registration_validation | docs/releases/pilot_v0/external_agent_registration_validation.md | file | yes |
| evidence:methodology_calibration_review | methodology_calibration_readme | audits/methodology_calibration/README.md | file | yes |
| evidence:methodology_calibration_review | methodology_calibration_corpus | audits/methodology_calibration/corpus.yaml | file | yes |
| evidence:methodology_calibration_review | methodology_calibration_summary | audits/methodology_calibration/reports/summary.json | file | yes |
| evidence:methodology_calibration_review | methodology_calibration_review_packet | audits/methodology_calibration/reviews/calibration_review_packet.csv | file | yes |
| evidence:release_tag_and_archive | release_archive_manifest_json | docs/releases/pilot_v0/archive_manifest.json | file | yes |
| evidence:release_tag_and_archive | release_archive_manifest_markdown | docs/releases/pilot_v0/archive_manifest.md | file | yes |

## Pre-Submission Verification Commands

```bash
python -m ruff check .
```

```bash
PYTHONPATH=src python -m pytest tests/test_curve_10y3mo_and_scoring.py tests/test_pipelines.py tests/test_benchmark_manifest.py tests/test_task_cards.py tests/test_manual_audit.py tests/test_external_agents.py tests/test_pilot_release.py tests/test_release_archive.py tests/test_reference_results.py tests/test_paper_artifacts.py tests/test_release_reproducibility.py tests/test_submission_readiness.py tests/test_manuscript_formatting.py tests/test_submission_package.py tests/test_publication_gate.py -q
```

```bash
PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py
```

```bash
PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check
```

```bash
PYTHONPATH=src python scripts/build_submission_package_manifest.py --check
```

```bash
PYTHONPATH=src python scripts/build_release_archive.py --output-dir tmp/ci_release_archives --manifest-json tmp/ci_release_archive_manifest.json --manifest-markdown tmp/ci_release_archive_manifest.md && PYTHONPATH=src python scripts/verify_release_archive.py --archive-manifest tmp/ci_release_archive_manifest.json
```

```bash
PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py --work-root tmp/pilot_release_repro_check --repeat 1 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21
```
