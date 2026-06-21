# Reports

Generated figures, tables, and benchmark summaries belong here.

Large generated reports should go under `reports/generated/` and are ignored by git by default.

Build reports from run manifests:

```bash
PYTHONPATH=src python scripts/build_run_report.py \
  --runs-root runs \
  --csv-output reports/generated/run_results.csv \
  --markdown-output reports/generated/run_results.md
```

The CSV contains flattened manifest metadata, scores, validation results, artifact counts, and failure counts. The Markdown report is a compact paper-facing table.

For the synthetic momentum baseline, the full generation-to-report path is:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py
```

For the synthetic logistic regression baseline:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py
```
