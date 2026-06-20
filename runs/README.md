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

Create a manifest:

```bash
PYTHONPATH=src python scripts/create_run_manifest.py \
  --task-id synthetic_market_direction_v0 \
  --agent-id momentum_baseline \
  --agent-version 0.1.0 \
  --submission-dir runs/synthetic_market_direction_v0/momentum_baseline \
  --output runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```

Validate a manifest:

```bash
PYTHONPATH=src python scripts/validate_run_manifest.py \
  runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```
