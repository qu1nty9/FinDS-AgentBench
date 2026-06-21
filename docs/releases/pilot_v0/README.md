# finds_agentbench_pilot_v0

Canonical pilot release manifest for FinDS-AgentBench.

## Snapshot

| Field | Value |
| --- | --- |
| Benchmark ID | finds_agentbench_pilot_v0 |
| Benchmark Version | 0.1.0 |
| Release Stage | pilot |
| Task Count | 4 |
| Runnable Task Count | 3 |
| Cards Index | ../../cards/README.md |
| Data Manifests Index | ../../data_manifests/pilot_v0/README.md |

## Tracks

| Track | Task Count | Task IDs |
| --- | --- | --- |
| event_aware_time_series_reasoning | 1 | synthetic_event_response_v0 |
| predictive_financial_ml | 2 | return_direction_etf_v0, synthetic_market_direction_v0 |
| research_replication_and_audit | 1 | leakage_audit_temporal_split_v0 |

## Tasks

| Task ID | Track | Spec Status | Release Status | Runnable | Public Data Present | Task Card | Evaluation Card | Data Manifest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leakage_audit_temporal_split_v0 | research_replication_and_audit | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/leakage_audit_temporal_split_v0.md) | [evaluation](../../cards/evaluations/leakage_audit_temporal_split_v0.md) | [data](../../data_manifests/pilot_v0/leakage_audit_temporal_split_v0.json) |
| return_direction_etf_v0 | predictive_financial_ml | draft | spec_only_pending_data_review | no | no | [task](../../cards/tasks/return_direction_etf_v0.md) | [evaluation](../../cards/evaluations/return_direction_etf_v0.md) | [data](../../data_manifests/pilot_v0/return_direction_etf_v0.json) |
| synthetic_event_response_v0 | event_aware_time_series_reasoning | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/synthetic_event_response_v0.md) | [evaluation](../../cards/evaluations/synthetic_event_response_v0.md) | [data](../../data_manifests/pilot_v0/synthetic_event_response_v0.json) |
| synthetic_market_direction_v0 | predictive_financial_ml | draft | runnable_public_pilot | yes | yes | [task](../../cards/tasks/synthetic_market_direction_v0.md) | [evaluation](../../cards/evaluations/synthetic_market_direction_v0.md) | [data](../../data_manifests/pilot_v0/synthetic_market_direction_v0.json) |

## Protocols

| Protocol | Run Types | Task IDs | Runs Root | Status |
| --- | --- | --- | --- | --- |
| pilot_baseline_suite | baseline | synthetic_market_direction_v0, synthetic_event_response_v0 | runs/suites/pilot_baselines_v0 | active |
| pilot_agent_suite | agent | synthetic_market_direction_v0, synthetic_event_response_v0 | runs/suites/pilot_agents_v0 | active |
| pilot_protocol | baseline, agent | synthetic_market_direction_v0, synthetic_event_response_v0 | runs/suites/pilot_protocol_v0 | active |

## Official Commands

- `PYTHONPATH=src python scripts/run_pilot_baseline_suite.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot`
- `PYTHONPATH=src python scripts/run_pilot_agent_suite.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot_agent`
- `PYTHONPATH=src python scripts/run_pilot_protocol.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot_protocol`

