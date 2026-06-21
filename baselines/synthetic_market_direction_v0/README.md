# Synthetic Market Direction Baseline

The momentum baseline predicts positive next-day return when the 20-day momentum-derived probability is at least 0.5.

Run after generating task data:

```bash
PYTHONPATH=src python baselines/synthetic_market_direction_v0/momentum_baseline.py
PYTHONPATH=src python scripts/score_synthetic_market_direction_v0.py \
  --submission runs/synthetic_market_direction_v0/momentum_baseline/predictions.csv
```

The baseline script writes a complete submission directory:

- `predictions.csv`
- `writeup.md`
- `notebook.ipynb`

The full pipeline can be run with:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py
```
