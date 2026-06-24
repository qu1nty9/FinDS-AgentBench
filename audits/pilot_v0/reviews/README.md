# Manual Audit Review Packets

This directory holds flat reviewer packets for the pilot manual-audit workflow.

## Files

- `reviewer_1_seed.csv`: projection of the current seed adjudicated subset into one-row-per-case reviewer format.
- `reviewer_2_blank_template.csv`: blank packet for an independent second reviewer.
- `reviewer_2_shadow_demo.csv`: synthetic dry-run second reviewer packet for exercising agreement and adjudication code paths. This file is not eligible for official benchmark agreement claims.
- `independent_reviewer_handoff.md`: reviewer-facing instructions and validation protocol.

## Workflow

1. Copy `reviewer_2_blank_template.csv` to a reviewer-specific filename.
2. Fill one row per case, including all rubric scores, evidence snippets, primary findings, and the overall label.
3. Validate the completed packet with `scripts/validate_manual_audit_review_packet.py`.
4. Rebuild the audit workflow artifacts to refresh the agreement and adjudication reports.
5. Once two complete official reviewer packets exist, adjudicate disagreements into the canonical subset.

The shadow demo packet exists only to prove the pipeline works end to end before a real second reviewer is available.

## Covered Cases

- Case count: `6`
- Task IDs: `synthetic_event_response_v0, synthetic_market_direction_v0, yield_direction_treasury10y_v0`
- Dimension IDs: `temporal_protocol_correctness, leakage_awareness_and_feature_hygiene, quantitative_evidence_use, baseline_comparison_or_counterfactual_context, claim_discipline, reproducibility_trace_completeness`

