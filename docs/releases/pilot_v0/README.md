# finds_agentbench_pilot_v0

Canonical pilot release manifest for FinDS-AgentBench.

## Snapshot

| Field | Value |
| --- | --- |
| Benchmark ID | finds_agentbench_pilot_v0 |
| Benchmark Version | 0.1.0 |
| Release Stage | pilot |
| Task Count | 9 |
| Runnable Task Count | 9 |
| Cards Index | ../../cards/README.md |
| Data Manifests Index | ../../data_manifests/pilot_v0/README.md |
| Reference Results | reference_results.md |
| Paper Artifacts | paper_artifacts/README.md |
| Statistical Artifacts | statistical_artifacts/README.md |
| Manual Audit | audits/pilot_v0/README.md |
| Agreement Report | audits/pilot_v0/reports/agreement_summary.md |
| Adjudication Queue | audits/pilot_v0/reports/adjudication_queue.md |
| Reviewer Readiness | audits/pilot_v0/reports/reviewer_readiness.md |
| External Agent Protocol | docs/releases/pilot_v0/external_agent_protocol.md |
| External Agent Readiness | docs/releases/pilot_v0/external_agent_readiness.md |
| Submission Readiness | docs/releases/pilot_v0/submission_readiness.md |

## Tracks

| Track | Task Count | Task IDs |
| --- | --- | --- |
| event_aware_time_series_reasoning | 1 | synthetic_event_response_v0 |
| predictive_financial_ml | 7 | front_end_spread_widening_v0, synthetic_market_direction_v0, usd_afe_vs_eme_relative_direction_v0, usd_broad_direction_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, yield_direction_treasury10y_v0 |
| research_replication_and_audit | 1 | leakage_audit_temporal_split_v0 |

## Tasks

| Task ID | Track | Spec Status | Release Status | Runnable | Public Data Present | Task Card | Evaluation Card | Data Manifest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| front_end_spread_widening_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/front_end_spread_widening_v0.md) | [evaluation](../../cards/evaluations/front_end_spread_widening_v0.md) | [data](../../data_manifests/pilot_v0/front_end_spread_widening_v0.json) |
| leakage_audit_temporal_split_v0 | research_replication_and_audit | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/leakage_audit_temporal_split_v0.md) | [evaluation](../../cards/evaluations/leakage_audit_temporal_split_v0.md) | [data](../../data_manifests/pilot_v0/leakage_audit_temporal_split_v0.json) |
| synthetic_event_response_v0 | event_aware_time_series_reasoning | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/synthetic_event_response_v0.md) | [evaluation](../../cards/evaluations/synthetic_event_response_v0.md) | [data](../../data_manifests/pilot_v0/synthetic_event_response_v0.json) |
| synthetic_market_direction_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/synthetic_market_direction_v0.md) | [evaluation](../../cards/evaluations/synthetic_market_direction_v0.md) | [data](../../data_manifests/pilot_v0/synthetic_market_direction_v0.json) |
| usd_afe_vs_eme_relative_direction_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/usd_afe_vs_eme_relative_direction_v0.md) | [evaluation](../../cards/evaluations/usd_afe_vs_eme_relative_direction_v0.md) | [data](../../data_manifests/pilot_v0/usd_afe_vs_eme_relative_direction_v0.json) |
| usd_broad_direction_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/usd_broad_direction_v0.md) | [evaluation](../../cards/evaluations/usd_broad_direction_v0.md) | [data](../../data_manifests/pilot_v0/usd_broad_direction_v0.json) |
| yield_curve_10y2y_steepening_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/yield_curve_10y2y_steepening_v0.md) | [evaluation](../../cards/evaluations/yield_curve_10y2y_steepening_v0.md) | [data](../../data_manifests/pilot_v0/yield_curve_10y2y_steepening_v0.json) |
| yield_curve_10y3mo_steepening_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | no | [task](../../cards/tasks/yield_curve_10y3mo_steepening_v0.md) | [evaluation](../../cards/evaluations/yield_curve_10y3mo_steepening_v0.md) | [data](../../data_manifests/pilot_v0/yield_curve_10y3mo_steepening_v0.json) |
| yield_direction_treasury10y_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/yield_direction_treasury10y_v0.md) | [evaluation](../../cards/evaluations/yield_direction_treasury10y_v0.md) | [data](../../data_manifests/pilot_v0/yield_direction_treasury10y_v0.json) |

## Protocols

| Protocol | Run Types | Task IDs | Runs Root | Status |
| --- | --- | --- | --- | --- |
| pilot_baseline_suite | baseline | synthetic_market_direction_v0, synthetic_event_response_v0, yield_direction_treasury10y_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, front_end_spread_widening_v0, usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0 | runs/suites/pilot_baselines_v0 | active |
| pilot_agent_suite | agent | synthetic_market_direction_v0, synthetic_event_response_v0, yield_direction_treasury10y_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, front_end_spread_widening_v0, usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0 | runs/suites/pilot_agents_v0 | active |
| pilot_protocol | baseline, agent | synthetic_market_direction_v0, synthetic_event_response_v0, yield_direction_treasury10y_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, front_end_spread_widening_v0, usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0 | runs/suites/pilot_protocol_v0 | active |

## Submission Readiness

| Field | Value |
| --- | --- |
| Status | not_ready_for_workshop_submission |
| Ready for Workshop Submission | no |
| Ready Gates | 3 / 6 |
| Blocking Gates | 3 |
| Report | docs/releases/pilot_v0/submission_readiness.md |

## External Agents

| Field | Value |
| --- | --- |
| Readiness Status | not_ready_no_external_agents |
| Ready for External-Agent Claims | no |
| Bundled Reference Agents | 7 |
| External Agent Configurations | 0 |
| Completed External Agent Configurations | 0 |
| External Task Coverage | 0 / 8 |
| Registry | agents/external_agent_registry.yaml |
| Protocol | docs/releases/pilot_v0/external_agent_protocol.md |
| Readiness Report | docs/releases/pilot_v0/external_agent_readiness.md |

## Manual Audit

| Field | Value |
| --- | --- |
| Status | seed_author_adjudication_only |
| Case Count | 6 |
| Reviewed Task Count | 3 |
| Reviewer Readiness Status | not_ready_seed_only |
| Ready for Submission Claims | no |
| Official Agreement Status | insufficient_independent_overlap |
| Exploratory Dry-Run Status | pairwise_agreement_available |
| Scope Tracks | predictive_financial_ml, event_aware_time_series_reasoning |
| Run Types | agent, baseline |
| Rubric | audits/pilot_v0/manual_audit_rubric.yaml |
| Seed Subset | audits/pilot_v0/adjudicated_subset.json |
| Reviews Workflow | audits/pilot_v0/reviews/README.md |
| Seed Reviewer Packet | audits/pilot_v0/reviews/reviewer_1_seed.csv |
| Blank Reviewer Template | audits/pilot_v0/reviews/reviewer_2_blank_template.csv |
| Shadow Demo Reviewer Packet | audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv |
| Agreement Report | audits/pilot_v0/reports/agreement_summary.md |
| Adjudication Queue | audits/pilot_v0/reports/adjudication_queue.md |
| Reviewer Readiness | audits/pilot_v0/reports/reviewer_readiness.md |

## Release Build

- `PYTHONPATH=src python scripts/build_pilot_release.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-outputs`

## Official Commands

- `PYTHONPATH=src python scripts/run_pilot_baseline_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot`
- `PYTHONPATH=src python scripts/run_pilot_agent_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot_agent`
- `PYTHONPATH=src python scripts/run_pilot_protocol.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot_protocol`

