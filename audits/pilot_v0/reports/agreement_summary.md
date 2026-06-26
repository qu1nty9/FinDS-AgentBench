# Manual Audit Agreement Summary

Agreement reporting for the pilot manual-audit workflow.

## Status

- Official agreement status: `pairwise_agreement_available`
- Exploratory dry-run status: `pairwise_agreement_available`
- Official eligible completed reviewer packets: `2`
- Exploratory eligible completed reviewer packets: `3`
- Seed subset cases: `6`

## Packet Inventory

| Packet | Reviewer | Role | Status | Completed Cases | Official Eligible | Exploratory Eligible | Errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| audits/pilot_v0/reviews/external_reviewer_1_completed.csv | external_reviewer_1 | independent_reviewer | complete | 6 | yes | yes | 0 |
| audits/pilot_v0/reviews/reviewer_1_seed.csv | reviewer_1_seed | benchmark_author_seed_reviewer | complete | 6 | yes | yes | 0 |
| audits/pilot_v0/reviews/reviewer_2_blank_template.csv | reviewer_2 | independent_reviewer | template | 0 | no | no | 0 |
| audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv | reviewer_2_shadow_demo | synthetic_shadow_reviewer | complete | 6 | no | yes | 0 |

## Official Pairwise Agreement

### external_reviewer_1 vs reviewer_1_seed

- Status: `pairwise_agreement_available`
- Overlap case count: `6`
- Overall-label exact agreement: `0.0`
- Overall-label kappa: `0.0`
- Exact total-score match rate: `0.0`
- Mean absolute total-score difference: `4.166667`
- Cases with any disagreement: `6`

| Dimension | Exact Agreement | Quadratic Weighted Kappa |
| --- | --- | --- |
| temporal_protocol_correctness | 0.0 | 0.0 |
| leakage_awareness_and_feature_hygiene | 0.0 | 0.0 |
| quantitative_evidence_use | 0.0 | 0.0 |
| baseline_comparison_or_counterfactual_context | 0.0 | 0.0 |
| claim_discipline | 0.0 | 0.0 |
| reproducibility_trace_completeness | 0.333333 | 0.0 |

## Exploratory Dry Run

### external_reviewer_1 vs reviewer_1_seed

- Status: `pairwise_agreement_available`
- Overlap case count: `6`
- Overall-label exact agreement: `0.0`
- Overall-label kappa: `0.0`
- Exact total-score match rate: `0.0`
- Mean absolute total-score difference: `4.166667`
- Cases with any disagreement: `6`

| Dimension | Exact Agreement | Quadratic Weighted Kappa |
| --- | --- | --- |
| temporal_protocol_correctness | 0.0 | 0.0 |
| leakage_awareness_and_feature_hygiene | 0.0 | 0.0 |
| quantitative_evidence_use | 0.0 | 0.0 |
| baseline_comparison_or_counterfactual_context | 0.0 | 0.0 |
| claim_discipline | 0.0 | 0.0 |
| reproducibility_trace_completeness | 0.333333 | 0.0 |

### external_reviewer_1 vs reviewer_2_shadow_demo

- Status: `pairwise_agreement_available`
- Overlap case count: `6`
- Overall-label exact agreement: `0.0`
- Overall-label kappa: `0.0`
- Exact total-score match rate: `0.0`
- Mean absolute total-score difference: `4.333333`
- Cases with any disagreement: `6`

| Dimension | Exact Agreement | Quadratic Weighted Kappa |
| --- | --- | --- |
| temporal_protocol_correctness | 0.0 | 0.0 |
| leakage_awareness_and_feature_hygiene | 0.0 | 0.0 |
| quantitative_evidence_use | 0.333333 | 0.0 |
| baseline_comparison_or_counterfactual_context | 0.333333 | 0.0 |
| claim_discipline | 0.166667 | 0.0 |
| reproducibility_trace_completeness | 0.5 | 0.0 |

### reviewer_1_seed vs reviewer_2_shadow_demo

- Status: `pairwise_agreement_available`
- Overlap case count: `6`
- Overall-label exact agreement: `0.833333`
- Overall-label kappa: `0.714286`
- Exact total-score match rate: `0.166667`
- Mean absolute total-score difference: `0.833333`
- Cases with any disagreement: `6`

| Dimension | Exact Agreement | Quadratic Weighted Kappa |
| --- | --- | --- |
| temporal_protocol_correctness | 0.833333 | 0.666667 |
| leakage_awareness_and_feature_hygiene | 1.0 | 1.0 |
| quantitative_evidence_use | 0.666667 | 0.8 |
| baseline_comparison_or_counterfactual_context | 0.666667 | 0.0 |
| claim_discipline | 0.833333 | 0.0 |
| reproducibility_trace_completeness | 0.833333 | 0.666667 |

