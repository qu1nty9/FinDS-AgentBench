# Manual Audit Reviewer Readiness

This report gates manuscript claims about independent manual-audit agreement.

## Status

| Field | Value |
| --- | --- |
| Status | `not_ready_seed_only` |
| Ready for submission claims | no |
| Independent completed reviewers | 0 / 1 |
| Official agreement status | `insufficient_independent_overlap` |
| Exploratory dry-run status | `pairwise_agreement_available` |
| Seed completed packets | 1 |
| Official eligible packets | 1 |
| Case count | 6 |

## Claim Boundary

- Allowed current claim: Seed manual-audit rubric, adjudicated subset, and reviewer workflow are present.
- Disallowed current claim: Independent inter-rater reliability or official second-reviewer agreement.

## Blocking Items

- Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.
- Rebuild official agreement reporting after an independent completed packet is available.

## Packet Roles

| Role | Packet |
| --- | --- |
| Seed | `audits/pilot_v0/reviews/reviewer_1_seed.csv` |
| Independent complete | (none) |
| Blank template | `audits/pilot_v0/reviews/reviewer_2_blank_template.csv` |
| Synthetic shadow | `audits/pilot_v0/reviews/reviewer_2_shadow_demo.csv` |

## Non-Blocking Cautions

- reviewer_2_shadow_demo.csv is exploratory dry-run evidence only and must not be cited as official inter-rater agreement.

## Next Actions

- Copy reviewer_2_blank_template.csv to a reviewer-specific CSV.
- Fill every case with rubric scores, evidence, overall labels, and review_status=complete.
- Rebuild manual-audit workflow artifacts and adjudicate any official disagreements.
