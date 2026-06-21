# Synthetic Event Response Baselines

Baselines for `synthetic_event_response_v0`.

Run the event-rule baseline after generating task data:

```bash
PYTHONPATH=src python scripts/generate_synthetic_event_response_v0.py --seed 23
PYTHONPATH=src python baselines/synthetic_event_response_v0/event_rule_baseline.py
PYTHONPATH=src python scripts/score_synthetic_event_response_v0.py \
  --submission runs/synthetic_event_response_v0/event_rule_baseline/predictions.csv
```

The one-command path is:

```bash
PYTHONPATH=src python scripts/run_synthetic_event_response_rule_pipeline.py
```
