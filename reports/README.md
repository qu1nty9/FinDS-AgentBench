# Reports

Generated figures, tables, and benchmark summaries belong here.

Large generated reports should go under `reports/generated/` and are ignored by git by default.

Build reports from run manifests:

```bash
PYTHONPATH=src python scripts/build_run_report.py \
  --runs-root runs \
  --csv-output reports/generated/run_results.csv \
  --markdown-output reports/generated/run_results.md \
  --summary-csv-output reports/generated/run_summary.csv \
  --summary-markdown-output reports/generated/run_summary.md
```

The detailed CSV contains flattened manifest metadata, scores, validation results, artifact counts, failure counts, and trace fields such as `trace.seed` and `trace.run_label`. The detailed Markdown report is a compact run-level table.

The summary CSV/Markdown aggregates repeated runs by `task_id`, `agent_id`, and `run_type`, reporting run counts plus mean/std/min/max for the core benchmark metrics.

For the synthetic momentum baseline, the full generation-to-report path is:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py
```

For the synthetic logistic regression baseline:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py
```

For repeated-run pilot experiments:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py \
  --repeat 3 \
  --seed 11 \
  --run-label pilot_logistic
```
