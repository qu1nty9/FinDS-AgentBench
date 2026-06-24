# Independent Reviewer Packet Manifest

Checksum manifest for the reviewer-facing manual-audit intake packet.

## Status

| Field | Value |
| --- | --- |
| Status | `ready_for_independent_review_intake` |
| Ready for reviewer distribution | yes |
| Cases | 6 / 6 |
| Dimensions | temporal_protocol_correctness, leakage_awareness_and_feature_hygiene, quantitative_evidence_use, baseline_comparison_or_counterfactual_context, claim_discipline, reproducibility_trace_completeness |

## Claim Boundary

- Allowed current claim: A frozen blank reviewer packet and reviewer-facing handoff are available.
- Disallowed current claim: Independent inter-rater reliability or completed second-reviewer evidence.

## Reviewer-Facing Files

| Role | Path | Size Bytes | SHA256 |
| --- | --- | --- | --- |
| review_packet_manifest_readme | `audits/pilot_v0/reviews/README.md` | 1755 | `a71009823aad755f4207d2a869462ceeb516f863c06727b1b2f3db2beda0f915` |
| independent_reviewer_handoff | `audits/pilot_v0/reviews/independent_reviewer_handoff.md` | 2830 | `c676a1a4a8f8683d6adbf84b4a76e3e66682abada753f309a780c7beddb00c85` |
| blank_reviewer_packet | `audits/pilot_v0/reviews/reviewer_2_blank_template.csv` | 3117 | `c2adadf512f888cd5873e6df6bd200079afa2a7a7a774d14b7353da0c9a58299` |
| scoring_rubric | `audits/pilot_v0/manual_audit_rubric.yaml` | 5608 | `34f29a90f2a396448682e647bd79bd2b8c0bd956f6ef87ee585924f2084d5bbe` |

## Excluded Files

| Role | Path | Reason |
| --- | --- | --- |
| benchmark_author_seed_packet | `audits/pilot_v0/reviews/reviewer_1_seed.csv` | Author seed review; not reviewer-facing intake material. |
| synthetic_shadow_packet | `audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv` | Synthetic dry-run packet; not official independent-review evidence. |
| author_adjudicated_subset | `audits/pilot_v0/adjudicated_subset.json` | Author-adjudicated source subset; not reviewer-facing intake material. |

## Target Cases

| Case | Task | Run Type | Agent | Artifact Root |
| --- | --- | --- | --- | --- |
| pilot_market_momentum_baseline_release_001 | synthetic_market_direction_v0 | baseline | momentum_baseline | `runs/suites/pilot_baselines_v0/synthetic_market_direction_v0/momentum_baseline/release_pilot_market_001_seed_11` |
| pilot_market_logistic_baseline_release_001 | synthetic_market_direction_v0 | baseline | logistic_regression_baseline | `runs/suites/pilot_baselines_v0/synthetic_market_direction_v0/logistic_regression_baseline/release_pilot_market_001_seed_11` |
| pilot_event_rule_baseline_release_001 | synthetic_event_response_v0 | baseline | event_rule_baseline | `runs/suites/pilot_baselines_v0/synthetic_event_response_v0/event_rule_baseline/release_pilot_event_001_seed_23` |
| pilot_event_rule_env_agent_protocol_001 | synthetic_event_response_v0 | agent | event_rule_env_agent | `runs/suites/pilot_protocol_v0/synthetic_event_response_v0/event_rule_env_agent/release_protocol_agent_event_001_seed_23` |
| pilot_treasury_previous_day_baseline_release_001 | yield_direction_treasury10y_v0 | baseline | previous_day_direction_baseline | `runs/suites/pilot_baselines_v0/yield_direction_treasury10y_v0/previous_day_direction_baseline/release_pilot_treasury_001_seed_29` |
| pilot_treasury_logistic_baseline_release_001 | yield_direction_treasury10y_v0 | baseline | logistic_regression_baseline | `runs/suites/pilot_baselines_v0/yield_direction_treasury10y_v0/logistic_regression_baseline/release_pilot_treasury_001_seed_29` |

## Completion Requirements

- Copy reviewer_2_blank_template.csv to a reviewer-specific filename.
- Use one non-author reviewer_id throughout the packet.
- Set reviewer_role=independent_reviewer, review_status=complete, and an independent review_source for every row.
- Fill every rubric score, evidence field, overall_label, and primary_manual_findings.
- Validate with scripts/validate_manual_audit_review_packet.py before submitting the packet.

## Validation Command

```bash
PYTHONPATH=src python scripts/validate_manual_audit_review_packet.py --packet audits/pilot_v0/reviews/reviewer_2_completed.csv
```

