# Treasury Yield Direction Baselines

Implemented baselines:

- `previous_day_direction_baseline.py`
- `logistic_regression_baseline.py`
- `random_forest_baseline.py`
- `extra_trees_baseline.py`

Run after building task data:

```bash
PYTHONPATH=src python baselines/yield_direction_treasury10y_v0/previous_day_direction_baseline.py
PYTHONPATH=src python baselines/yield_direction_treasury10y_v0/logistic_regression_baseline.py
PYTHONPATH=src python baselines/yield_direction_treasury10y_v0/random_forest_baseline.py
PYTHONPATH=src python baselines/yield_direction_treasury10y_v0/extra_trees_baseline.py
PYTHONPATH=src python scripts/score_yield_direction_treasury10y_v0.py \
  --submission runs/yield_direction_treasury10y_v0/logistic_regression_baseline/predictions.csv
```

The baseline script writes a complete submission directory:

- `predictions.csv`
- `writeup.md`
- `notebook.ipynb`
- `baseline_metadata.json`

Recommended pipeline entrypoints:

```bash
PYTHONPATH=src python scripts/run_yield_direction_treasury10y_previous_day_pipeline.py
PYTHONPATH=src python scripts/run_yield_direction_treasury10y_logistic_pipeline.py
PYTHONPATH=src python scripts/run_yield_direction_treasury10y_random_forest_pipeline.py
PYTHONPATH=src python scripts/run_yield_direction_treasury10y_extra_trees_pipeline.py
```
