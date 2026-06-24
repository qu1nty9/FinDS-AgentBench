# Methodology Calibration

This directory holds the calibration workflow for the static methodology and leakage heuristics.

The workflow serves two purposes:

- check whether new rules fire on known-bad temporal patterns;
- generate a manual review packet over clean pilot submissions so false positives and false negatives can be tracked explicitly.

## Contents

- `corpus.yaml`: declarative corpus definition for real pilot run artifacts and curated fixtures.
- `fixtures/`: seed positive cases that should trigger specific methodology rules.
- `reviews/calibration_review_packet.csv`: generated packet for manual calibration labels.
- `reports/summary.json`: machine-readable calibration summary.
- `reports/summary.md`: human-readable calibration summary.

## Current Design

The calibration corpus combines:

- real run submissions from `runs/suites/pilot_baselines_v0/` and `runs/suites/pilot_agents_v0/`;
- curated positive fixtures that intentionally violate temporal or task-specific methodology rules.

Real pilot submissions are primarily used as clean-control candidates. Curated fixtures are primarily used as recall probes for the static rules.

## Rebuild

```bash
PYTHONPATH=src python scripts/build_methodology_calibration_workflow.py
```

After rebuilding, fill `reviews/calibration_review_packet.csv`:

- mark finding rows as `true_positive` or `false_positive`;
- mark clean-control rows as `true_negative` or `false_negative`;
- record reviewer notes for any heuristic miss or unjustified warning.
