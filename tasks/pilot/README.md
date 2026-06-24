# Pilot Tasks

This directory contains draft task specifications for the arXiv/workshop pilot.

Pilot tasks should stay small enough to run repeatedly across agents while still enforcing the benchmark's central constraints:

- point-in-time data availability;
- temporal validation;
- leakage checks;
- executable artifact;
- reproducible output;
- defensible writeup.

The first target is 8-12 locked tasks across predictive financial ML, event-aware reasoning, and leakage audit.

Build public task cards and evaluation cards for the current pilot specs:

```bash
PYTHONPATH=src python scripts/build_task_cards.py
```

Build public data manifests and checksums:

```bash
PYTHONPATH=src python scripts/build_data_manifests.py
```

Build the canonical pilot release manifest:

```bash
PYTHONPATH=src python scripts/build_benchmark_manifest.py
```

## Runnable Vertical Slice

`leakage_audit_temporal_split_v0.yaml` is the first runnable task spec.

Commands:

```bash
PYTHONPATH=src python scripts/generate_leakage_audit_temporal_split_v0.py --seed 7
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/leakage_audit_temporal_split_v0.yaml
PYTHONPATH=src python scripts/score_leakage_audit_temporal_split_v0.py \
  --submission-dir baselines/leakage_audit_temporal_split_v0/expert_submission
```

The scorer currently checks the audit note and before/after metrics. Notebook execution validation will be added after the first model-based baseline is implemented.

`synthetic_market_direction_v0.yaml` is the first runnable predictive task spec.

Commands:

```bash
PYTHONPATH=src python scripts/generate_synthetic_market_direction_v0.py --seed 11
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/synthetic_market_direction_v0.yaml
PYTHONPATH=src python baselines/synthetic_market_direction_v0/momentum_baseline.py
PYTHONPATH=src python scripts/score_synthetic_market_direction_v0.py \
  --submission runs/synthetic_market_direction_v0/momentum_baseline/predictions.csv \
  --output-json runs/synthetic_market_direction_v0/momentum_baseline/score.json
```

The public data contains train and public-validation labels. Private holdout labels are written only to `data/private/` and are ignored by git.

The one-command baseline pipeline is:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py
```

`synthetic_event_response_v0.yaml` is the first runnable event-aware temporal reasoning task spec.

Commands:

```bash
PYTHONPATH=src python scripts/generate_synthetic_event_response_v0.py --seed 23
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/synthetic_event_response_v0.yaml
PYTHONPATH=src python scripts/run_synthetic_event_response_rule_pipeline.py
```

The task asks agents to predict next-day event reaction direction using event surprise, sentiment, event importance, and pre-event market context. Private event-reaction labels are written only to `data/private/` and are ignored by git.

`yield_curve_10y2y_steepening_v0.yaml` adds a second public-domain macro-rates slice without introducing a new licensing surface.

Commands:

```bash
PYTHONPATH=src python scripts/download_yield_curve_10y2y_steepening_v0.py --snapshot-date 2026-06-21
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/yield_curve_10y2y_steepening_v0.yaml
PYTHONPATH=src python baselines/yield_curve_10y2y_steepening_v0/previous_day_direction_baseline.py
PYTHONPATH=src python scripts/score_yield_curve_10y2y_steepening_v0.py \
  --submission runs/yield_curve_10y2y_steepening_v0/previous_day_direction_baseline/predictions.csv
```

The download script first tries to derive the new task offline from the existing frozen Treasury snapshot, then falls back to ALFRED/FRED retrieval when needed.

`yield_curve_10y3mo_steepening_v0.yaml` adds a third public-domain macro-rates slice from the same Treasury surface, relabeled for long-end versus bill-curve steepening.

Commands:

```bash
PYTHONPATH=src python scripts/download_yield_curve_10y3mo_steepening_v0.py --snapshot-date 2026-06-21
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml
PYTHONPATH=src python baselines/yield_curve_10y3mo_steepening_v0/previous_day_direction_baseline.py
PYTHONPATH=src python scripts/score_yield_curve_10y3mo_steepening_v0.py \
  --submission runs/yield_curve_10y3mo_steepening_v0/previous_day_direction_baseline/predictions.csv
```

The download script first tries to derive the task offline from the existing frozen Treasury snapshot, then falls back to ALFRED/FRED retrieval when needed.

`usd_afe_vs_eme_relative_direction_v0.yaml` adds a second public-domain FX slice without introducing a new licensing surface.

Commands:

```bash
PYTHONPATH=src python scripts/download_usd_afe_vs_eme_relative_direction_v0.py --snapshot-date 2026-06-21
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml
PYTHONPATH=src python baselines/usd_afe_vs_eme_relative_direction_v0/previous_day_direction_baseline.py
PYTHONPATH=src python scripts/score_usd_afe_vs_eme_relative_direction_v0.py \
  --submission runs/usd_afe_vs_eme_relative_direction_v0/previous_day_direction_baseline/predictions.csv
```

The download script first tries to derive the new task offline from the existing frozen USD-broad snapshot, then falls back to ALFRED/FRED retrieval when needed.

## Artifact Validation

Submission directories can be checked before scoring:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir
```

The validator executes the notebook when `deliverables.notebook.must_execute_cleanly` is true, then checks required files, prediction columns, task-forbidden output columns, and writeup length.

Use `--scan-leakage` to fail submissions that reference forbidden private artifacts such as `data/private` or `answer_key`:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir \
  --scan-leakage \
  --scan-methodology
```

The methodology scan also flags suspicious feature/target construction patterns such as `shift(-1)`, centered rolling windows, backfilling, target-like columns appearing in feature definitions, task-specific forbidden columns appearing in feature selection or merge logic, and horizon-aware `merge` / `join` / `merge_asof` patterns that look future-aligned for short-horizon tasks.

Rebuild the methodology-calibration workflow with:

```bash
PYTHONPATH=src python scripts/build_methodology_calibration_workflow.py
```

This scans the current pilot run corpus plus curated positive fixtures, writes `audits/methodology_calibration/reports/summary.md`, and generates `audits/methodology_calibration/reviews/calibration_review_packet.csv` for manual false-positive / false-negative review.

## Manual Audit

The pilot now has a machine-readable seed manual-audit bundle under `audits/pilot_v0/`:

- `manual_audit_rubric.yaml`: canonical rubric for writeup-quality and methodology review.
- `adjudicated_subset.json`: six reviewed cases linked to committed run artifacts.
- `reviews/reviewer_2_blank_template.csv`: blank packet for an independent second reviewer.
- `reviews/reviewer_2_shadow_demo.csv`: synthetic dry-run second reviewer used only to validate disagreement and adjudication tooling.
- `reports/agreement_summary.md`: generated status report for reviewer coverage and pairwise agreement.
- `reports/adjudication_queue.md`: generated disagreement queue for adjudication.

Build or refresh the reviewer workflow artifacts with:

```bash
PYTHONPATH=src python scripts/build_manual_audit_workflow.py
```

This bundle is strong enough to structure workshop and arXiv writing, but it is still a seed author-coded subset. Do not claim inter-rater agreement from it yet. The shadow demo reviewer exists only to validate the pipeline. Before benchmark-paper or journal submission, expand it into a dual-review adjudicated sample and report agreement from real independent reviewers.
