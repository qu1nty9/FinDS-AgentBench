# Manual Audit Reviewer Readiness

This report gates manuscript claims about independent manual-audit agreement.

## Status

| Field | Value |
| --- | --- |
| Status | `ready_for_submission_claims` |
| Ready for submission claims | yes |
| Independent completed reviewers | 1 / 1 |
| Official agreement status | `pairwise_agreement_available` |
| Exploratory dry-run status | `pairwise_agreement_available` |
| Seed completed packets | 1 |
| Official eligible packets | 2 |
| Case count | 6 |

## Claim Boundary

- Allowed current claim: Independent reviewer agreement artifacts are available for submission-strength audit claims.
- Disallowed current claim: n/a

## Blocking Items

- None.

## Packet Roles

| Role | Packet |
| --- | --- |
| Seed | `audits/pilot_v0/reviews/reviewer_1_seed.csv` |
| Independent complete | `audits/pilot_v0/reviews/external_reviewer_1_completed.csv` |
| Blank template | `audits/pilot_v0/reviews/reviewer_2_blank_template.csv` |
| Synthetic shadow | `audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv` |

## Non-Blocking Cautions

- reviewer_2_shadow_demo.csv is exploratory dry-run evidence only and must not be cited as official inter-rater agreement.

## Next Actions

- Inspect pairwise agreement and adjudication queue before making final submission claims.
