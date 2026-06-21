# Runs

Agent and baseline run artifacts are written here during evaluation.

Do not commit large run directories by default. Publish curated artifacts separately when licensing and privacy constraints allow.

Each completed run should include a `run_manifest.json` with:

- `run_id`;
- `task_id`;
- run type: `agent`, `baseline`, `human`, or `expert`;
- agent or baseline metadata;
- timing;
- tool permissions;
- commands;
- retained artifact inventory with `sha256`;
- validation outputs;
- scores;
- failures.
- trace metadata such as seed, run label, and repeat index.

Repeated runs should use separate run directories under the same task/agent root:

```text
runs/synthetic_market_direction_v0/logistic_regression_baseline/pilot_001_seed_11/
runs/synthetic_market_direction_v0/logistic_regression_baseline/pilot_002_seed_12/
runs/synthetic_market_direction_v0/logistic_regression_baseline/pilot_003_seed_13/
```

This keeps artifacts immutable per run and lets the report builder compute run-level and aggregate tables from manifests.

For controlled paper-facing experiments, use a dedicated suite root such as:

```text
runs/suites/synthetic_market_direction_v0_pilot/synthetic_market_direction_v0/logistic_regression_baseline/pilot_001_seed_11/
```

Dedicated suite roots prevent summary reports from mixing controlled repeated runs with earlier prototype or smoke runs.

Create a manifest:

```bash
PYTHONPATH=src python scripts/create_run_manifest.py \
  --task-id synthetic_market_direction_v0 \
  --agent-id momentum_baseline \
  --agent-version 0.1.0 \
  --submission-dir runs/synthetic_market_direction_v0/momentum_baseline \
  --scores-json runs/synthetic_market_direction_v0/momentum_baseline/score.json \
  --output runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```

Validate a manifest:

```bash
PYTHONPATH=src python scripts/validate_run_manifest.py \
  runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```
