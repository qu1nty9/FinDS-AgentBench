# Pilot Manual Audit

This directory contains the seed manual-audit bundle for the runnable pilot release.

The current bundle is intentionally honest about its maturity:

- it is machine-readable;
- it is grounded in real committed run artifacts;
- it is useful for paper-writing and benchmark design;
- it is not yet a dual-review agreement study.

## Files

- `manual_audit_rubric.yaml`: canonical rubric for writeup-quality and methodology review.
- `adjudicated_subset.json`: seed subset of reviewed cases linked to concrete run artifacts.
- `reviews/`: reviewer packet workflow, including a seed reviewer packet and a blank second-reviewer template.
- `reports/`: generated agreement summaries and workflow status reports.

The `reviews/` directory also contains `reviewer_2_shadow_demo.csv`. That file is a synthetic dry-run reviewer used to verify disagreement and adjudication tooling. It must never be cited as an independent human review.

## Current Status

- Status: `seed_author_adjudication_only`
- Coverage: 6 cases across 3 runnable tasks
- Run types: `baseline`, `agent`
- Scope: predictive and event-aware tasks with notebook, prediction, and writeup artifacts
- Excluded for now: `leakage_audit_temporal_split_v0`, which needs a separate note-centric rubric

## Why This Matters

All six seed cases pass the automatic artifact validators. The manual rubric still finds systematic research-quality gaps:

- missing baseline or counterfactual comparison in the narrative;
- uneven use of quantitative evidence in writeups;
- thinner temporal-protocol explanations for rule-based submissions than for calibrated model baselines.

That is exactly the signal the benchmark needs if it wants to claim more than raw predictive scoring.

## Next Upgrade

Before any benchmark-paper claim about subjective audit reliability, fill an independent second-reviewer packet under `reviews/`, rebuild the agreement report under `reports/`, and only then adjudicate disagreements into the canonical subset. The shadow demo reviewer is only for tooling validation.
