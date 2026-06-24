# Treasury Curve Steepening Baselines

Implemented baselines:

- `previous_day_direction_baseline.py`
- `logistic_regression_baseline.py`
- `random_forest_baseline.py`
- `extra_trees_baseline.py`

Run after building task data:

```bash
PYTHONPATH=src python scripts/download_front_end_spread_widening_v0.py
PYTHONPATH=src python baselines/front_end_spread_widening_v0/previous_day_direction_baseline.py
PYTHONPATH=src python baselines/front_end_spread_widening_v0/logistic_regression_baseline.py
PYTHONPATH=src python baselines/front_end_spread_widening_v0/random_forest_baseline.py
PYTHONPATH=src python baselines/front_end_spread_widening_v0/extra_trees_baseline.py
PYTHONPATH=src python scripts/score_front_end_spread_widening_v0.py \
  --submission runs/front_end_spread_widening_v0/logistic_regression_baseline/predictions.csv
```

The baseline script writes a complete submission directory:

- `predictions.csv`
- `writeup.md`
- `notebook.ipynb`
- `baseline_metadata.json`
