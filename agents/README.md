# Agents

This directory holds wrappers and protocol notes for evaluated agents.

Every agent run should record:

- model and agent framework;
- tool permissions;
- prompt version;
- compute and time budget;
- random seed or run id;
- commands executed;
- final artifacts;
- errors and retries.

## Synthetic Market Agent Contract

The first runnable agent harness is:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_command.py \
  --agent-id my_agent \
  --agent-version dev \
  --agent-command "python agents/my_agent.py" \
  --run-label pilot_001_seed_11
```

Repeated agent evaluation uses the suite runner:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py \
  --agent-id my_agent \
  --agent-version dev \
  --agent-command "python agents/my_agent.py" \
  --repeat 3 \
  --seed 11 \
  --run-label-prefix pilot_agent
```

The repository includes a contract-only reference agent:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py \
  --agent-id momentum_env_agent \
  --agent-version 0.1.0 \
  --agent-command "python agents/examples/momentum_env_agent.py" \
  --repeat 3
```

The event-response task uses the same artifact contract:

```bash
PYTHONPATH=src python scripts/run_synthetic_event_response_agent_suite.py \
  --agent-id event_rule_env_agent \
  --agent-version 0.1.0 \
  --agent-command "python agents/examples/event_rule_env_agent.py" \
  --repeat 3
```

The command is parsed with `shlex` and runs with `FINDS_*` environment variables:

- `FINDS_TASK_ID`
- `FINDS_RUN_SEED`
- `FINDS_TASK_SPEC_PATH`
- `FINDS_PUBLIC_DATA_DIR`
- `FINDS_TRAIN_PUBLIC_PATH`
- `FINDS_HOLDOUT_FEATURES_PATH`
- `FINDS_PRIVATE_HOLDOUT_FEATURES_PATH`
- `FINDS_SAMPLE_SUBMISSION_PATH`
- `FINDS_METADATA_PATH`
- `FINDS_SUBMISSION_DIR`

`FINDS_HOLDOUT_FEATURES_PATH` and `FINDS_PRIVATE_HOLDOUT_FEATURES_PATH` point to the same label-free holdout feature file. The harness does not expose private answer-key paths to the agent environment. The agent must write these files into `FINDS_SUBMISSION_DIR`:

- `notebook.ipynb`
- `predictions.csv`
- `writeup.md`

After the command exits, the evaluator scores `predictions.csv`, validates required artifacts, scans for leakage and methodology risks, captures stdout/stderr under `logs/`, writes `run_manifest.json`, and rebuilds run reports.
