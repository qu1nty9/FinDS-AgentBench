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

## Artifact Validation

Submission directories can be checked before scoring:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir
```

The validator executes the notebook when `deliverables.notebook.must_execute_cleanly` is true, then checks required files, prediction columns, and writeup length.

Use `--scan-leakage` to fail submissions that reference forbidden private artifacts such as `data/private` or `answer_key`:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir \
  --scan-leakage \
  --scan-methodology
```

The methodology scan also flags suspicious feature/target construction patterns such as `shift(-1)`, centered rolling windows, backfilling, and target-like columns appearing in feature definitions.
