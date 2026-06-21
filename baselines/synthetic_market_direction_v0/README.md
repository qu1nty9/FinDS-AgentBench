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

## Logistic Regression Baseline

This baseline fits `StandardScaler + LogisticRegression` on the chronological train split and selects the decision threshold on public validation only.

Run standalone after generating task data:

```bash
PYTHONPATH=src python baselines/synthetic_market_direction_v0/logistic_regression_baseline.py
```

Run the full pipeline:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py
```
