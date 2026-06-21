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
PYTHONPATH=src python scripts/run_synthetic_market_baseline_suite.py \
  --repeat 3 \
  --seed 11 \
  --run-label-prefix pilot
```

The suite runner defaults to `runs/suites/synthetic_market_direction_v0_pilot` as its report root. Use a dedicated `--runs-root` for each controlled experiment so summary statistics do not mix prototype, smoke, and publication runs.

For the cross-task pilot baseline suite:

```bash
PYTHONPATH=src python scripts/run_pilot_baseline_suite.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot
```

This writes market and event-response baseline manifests under `runs/suites/pilot_baselines_v0` and rebuilds the shared detailed and summary reports.

For the cross-task pilot agent suite:

```bash
PYTHONPATH=src python scripts/run_pilot_agent_suite.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot_agent
```

This writes agent manifests under `runs/suites/pilot_agents_v0` and produces the same shared run-level and summary-level reports across both implemented pilot tasks.

For the combined pilot protocol:

```bash
PYTHONPATH=src python scripts/run_pilot_protocol.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot_protocol
```

This writes baseline and agent manifests under `runs/suites/pilot_protocol_v0` and rebuilds one shared set of reports that can be used directly for pilot-paper tables.
