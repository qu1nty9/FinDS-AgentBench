# Independent Reviewer Handoff

Use this packet to collect a submission-strength second manual-audit review.

## Required Inputs

- Start from `audits/pilot_v0/reviews/reviewer_2_blank_template.csv`.
- Verify the blank template against `audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md` before editing.
- Copy it to a reviewer-specific filename such as `reviewer_2_completed.csv`.
- Keep exactly one reviewer ID across the file.
- Set `reviewer_role` to `independent_reviewer` for every row.
- Set `review_status` to `complete` for every row only after all scores and notes are filled.
- Replace `review_source=blank_template` with a provenance value such as `independent_manual_review`.

## Required Fields Per Case

- Every rubric dimension must have a score in `{0, 1, 2}` and a non-empty evidence note.
- `total_score` must equal the sum of the six dimension scores.
- `overall_label` must match the rubric interpretation band for `total_score`.
- `primary_manual_findings` must be non-empty.
- `general_notes` is optional, but recommended for disagreements or uncertainty.

## Validation

Run the validator before asking the benchmark owner to rebuild agreement artifacts:

```bash
PYTHONPATH=src python scripts/validate_manual_audit_review_packet.py --packet audits/pilot_v0/reviews/reviewer_2_completed.csv
```

The packet is eligible for official agreement only when the validator reports `ready_for_independent_agreement`.

## Rubric Dimensions

| Dimension | Question | Evidence Sources |
| --- | --- | --- |
| temporal_protocol_correctness | Does the submission explain and appear to respect chronological training, validation, and holdout boundaries? | writeup.md; run_manifest.json; notebook.ipynb |
| leakage_awareness_and_feature_hygiene | Does the submission explicitly guard against target leakage, answer-key access, and forbidden future-derived features? | writeup.md; artifact_validation.json; notebook.ipynb |
| quantitative_evidence_use | Does the writeup support its claims with task-relevant metrics, calibration choices, or validation evidence? | writeup.md; score.json; run_manifest.json |
| baseline_comparison_or_counterfactual_context | Does the submission compare itself to simpler alternatives, prior baselines, or counterfactual checks? | writeup.md; score.json |
| claim_discipline | Are claims narrow, defensible, and proportional to the available evidence? | writeup.md; score.json |
| reproducibility_trace_completeness | Does the artifact set expose enough trace material to reconstruct how outputs were produced? | run_manifest.json; artifact_validation.json; notebook.ipynb; writeup.md |

## Claim Boundary

This handoff is for a real independent reviewer. `reviewer_2_shadow_demo.csv` is synthetic dry-run evidence and must not be cited as independent inter-rater agreement.
