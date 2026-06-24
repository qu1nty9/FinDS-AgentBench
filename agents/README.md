# Agents

This directory holds wrappers and protocol notes for evaluated agents.

The generated external-agent submission contract is tracked in
`docs/releases/pilot_v0/external_agent_protocol.md`; the machine-readable
registry that distinguishes bundled reference agents from independent external
submissions is `agents/external_agent_registry.yaml`.

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

The repository includes a task-aware reference agent that sweeps public baselines and selects the best candidate on public validation:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py \
  --agent-id market_research_sweep_env_agent \
  --agent-version 0.2.0 \
  --agent-command "python agents/examples/research_sweep_env_agent.py" \
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

The same `agents/examples/research_sweep_env_agent.py` entrypoint also works for `yield_direction_treasury10y_v0` and `usd_broad_direction_v0`; the harness passes `FINDS_TASK_ID`, and the agent switches candidate families by task.

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
