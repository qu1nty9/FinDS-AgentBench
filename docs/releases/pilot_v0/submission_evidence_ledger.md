# Submission Evidence Ledger

Machine-readable claim boundary and evidence index for the workshop submission gates.

## Status

| Field | Value |
| --- | --- |
| Ledger status | `submission_evidence_incomplete` |
| Submission readiness | `not_ready_for_workshop_submission` |
| Ready for workshop submission | no |
| Ready gates | 3 / 6 |
| Blocking gates | 3 |

## Allowed Current Claims

- The pilot release is within the planned 8-12 runnable-task workshop scope.
- Pilot uncertainty and paired-comparison statistical artifacts are generated.
- Manual-audit rubric, seed review, reviewer handoff, blank reviewer packet, and dry-run plumbing are available.
- External-agent registration, handoff, and readiness gates are available.
- Methodology-calibration findings have a completed author review packet.
- A deterministic candidate archive and archive manifest can be built before final tagging.

## Disallowed Current Claims

- Independent manual-audit agreement or submission-strength second-reviewer evidence.
- Independent external-agent performance evidence.
- A frozen tagged release archive exists.

## Gate Summary

| Gate | Ready | Status | Claim Status | Evidence Artifacts | Verification Commands |
| --- | --- | --- | --- | --- | --- |
| pilot_release_scope | yes | `ready` | `claim_allowed` | 6 | 3 |
| statistical_artifacts | yes | `ready` | `claim_allowed` | 4 | 1 |
| manual_audit_independent_review | no | `not_ready_seed_only` | `claim_blocked` | 10 | 2 |
| external_agent_evidence | no | `not_ready_no_external_agents` | `claim_blocked` | 5 | 2 |
| methodology_calibration_review | yes | `ready` | `claim_allowed` | 4 | 1 |
| release_tag_and_archive | no | `not_ready_unfrozen` | `claim_blocked` | 3 | 2 |

## Gate Evidence

### pilot_release_scope

- Current allowed claim: The pilot release is within the planned 8-12 runnable-task workshop scope.
- Blockers: none
- Evidence artifacts:
  - `docs/releases/pilot_v0/manifest.json` (release_manifest)
  - `docs/releases/pilot_v0/README.md` (release_readme)
  - `docs/cards/task_registry.json` (task_registry_json)
  - `docs/cards/task_registry.csv` (task_registry_csv)
  - `docs/cards` (task_cards_index)
  - `docs/data_manifests/pilot_v0` (data_manifests_index)
- Verification commands:
  - `PYTHONPATH=src python scripts/build_task_cards.py`
  - `PYTHONPATH=src python scripts/build_data_manifests.py`
  - `PYTHONPATH=src python scripts/build_benchmark_manifest.py`

### statistical_artifacts

- Current allowed claim: Pilot uncertainty and paired-comparison statistical artifacts are generated.
- Blockers: none
- Evidence artifacts:
  - `docs/releases/pilot_v0/statistical_artifacts/README.md` (statistical_artifacts_index)
  - `docs/releases/pilot_v0/statistical_artifacts/summary_uncertainty.md` (summary_uncertainty)
  - `docs/releases/pilot_v0/statistical_artifacts/agent_vs_best_baseline.md` (agent_vs_best_baseline)
  - `docs/releases/pilot_v0/statistical_artifacts/methods/statistical_methods.md` (statistical_methods)
- Verification commands:
  - `PYTHONPATH=src python scripts/build_pilot_statistical_artifacts.py`

### manual_audit_independent_review

- Current allowed claim: Manual-audit rubric, seed review, reviewer handoff, blank reviewer packet, and dry-run plumbing are available.
- Current disallowed claim: Independent manual-audit agreement or submission-strength second-reviewer evidence.
- Blockers:
  - Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.
  - Rebuild official agreement reporting after an independent completed packet is available.
- Evidence artifacts:
  - `audits/pilot_v0/README.md` (manual_audit_readme)
  - `audits/pilot_v0/manual_audit_rubric.yaml` (rubric)
  - `audits/pilot_v0/adjudicated_subset.json` (seed_subset)
  - `audits/pilot_v0/reviews/README.md` (reviews_workflow)
  - `audits/pilot_v0/reports/reviewer_readiness.md` (reviewer_readiness)
  - `audits/pilot_v0/reports/agreement_summary.md` (agreement_report)
  - `audits/pilot_v0/reports/adjudication_queue.md` (adjudication_queue)
  - `audits/pilot_v0/reviews/independent_reviewer_handoff.md` (independent_handoff)
  - `audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md` (independent_packet_manifest)
  - `audits/pilot_v0/reports/independent_reviewer_packet_validation.md` (independent_packet_validation)
- Verification commands:
  - `PYTHONPATH=src python scripts/build_manual_audit_workflow.py`
  - `PYTHONPATH=src python scripts/validate_manual_audit_review_packet.py --packet audits/pilot_v0/reviews/reviewer_2_completed.csv`

### external_agent_evidence

- Current allowed claim: External-agent registration, handoff, and readiness gates are available.
- Current disallowed claim: Independent external-agent performance evidence.
- Blockers:
  - Register and run at least one non-author external agent configuration through the pilot harness.
  - Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
- Evidence artifacts:
  - `agents/external_agent_registry.yaml` (external_agent_registry)
  - `agents/external_agent_handoff.md` (external_agent_handoff)
  - `docs/releases/pilot_v0/external_agent_protocol.md` (external_agent_protocol)
  - `docs/releases/pilot_v0/external_agent_readiness.md` (external_agent_readiness)
  - `docs/releases/pilot_v0/external_agent_registration_validation.md` (external_agent_registration_validation)
- Verification commands:
  - `PYTHONPATH=src python scripts/validate_external_agent_registry.py`
  - `PYTHONPATH=src python scripts/build_external_agent_readiness.py`

### methodology_calibration_review

- Current allowed claim: Methodology-calibration findings have a completed author review packet.
- Blockers: none
- Evidence artifacts:
  - `audits/methodology_calibration/README.md` (methodology_calibration_readme)
  - `audits/methodology_calibration/corpus.yaml` (methodology_calibration_corpus)
  - `audits/methodology_calibration/reports/summary.json` (methodology_calibration_summary)
  - `audits/methodology_calibration/reviews/calibration_review_packet.csv` (methodology_calibration_review_packet)
- Verification commands:
  - `PYTHONPATH=src python scripts/build_methodology_calibration_workflow.py`

### release_tag_and_archive

- Current allowed claim: A deterministic candidate archive and archive manifest can be built before final tagging.
- Current disallowed claim: A frozen tagged release archive exists.
- Blockers:
  - Create a release tag and archive the release artifact bundle after the remaining gates pass.
- Evidence artifacts:
  - `dist/release_archives/finds_agentbench_pilot_v0-0.1.0-pilot.tar.gz` (release_archive)
  - `docs/releases/pilot_v0/archive_manifest.json` (release_archive_manifest_json)
  - `docs/releases/pilot_v0/archive_manifest.md` (release_archive_manifest_markdown)
- Verification commands:
  - `PYTHONPATH=src python scripts/build_release_archive.py`
  - `PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py --repeat 1 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21`

