# FinDS-AgentBench

FinDS-AgentBench is a benchmark and evaluation suite for AI agents that perform end-to-end financial data science research.

The benchmark asks:

> Can current AI agents conduct reliable financial ML research under realistic temporal, leakage, reproducibility, and decision-quality constraints?

## Positioning

Most agent benchmarks evaluate machine-learning engineering, generic data science, financial QA, tool use, or spreadsheet artifacts. FinDS-AgentBench targets the missing intersection: financial ML research workflows where an agent must produce executable notebooks and writeups while respecting point-in-time data availability, temporal validation, leakage safety, reproducibility, and financial plausibility.

## Publication Path

The project is staged intentionally:

1. **arXiv/workshop pilot**: 8-12 tasks, 3 tracks, 4-6 agents/baselines, repeated runs, and a clear failure taxonomy.
2. **top benchmark/dataset venue**: 30-50 tasks, hidden temporal holdout, public harness, task cards, evaluation cards, and broad baselines.
3. **journal extension**: methodological study of reliability, leakage, reproducibility, intervention effects, and model-risk implications.

The public roadmap is tracked in `docs/publication_roadmap.md`.


## Core Evaluation Dimensions

- Execution success: artifact runs without manual repair.
- Predictive performance: task-specific score on temporal holdout.
- Financial performance: cost-adjusted return, Sharpe, drawdown, turnover, calibration, or task-relevant financial metric.
- Leakage safety: no future information, forbidden columns, or invalid timestamp alignment.
- Validation correctness: temporal split and benchmark protocol are respected.
- Reproducibility: deterministic environment, fixed seeds, documented dependencies, rerunnable notebooks.
- Robustness: performance across regimes, assets, perturbations, or task variants.
- Writeup validity: claims are supported by results and limitations are explicit.
- Auditability: agent actions, artifacts, and failures are traceable.

## Repository Layout

```text
agents/             Agent wrappers and evaluation notes.
baselines/          Naive, classical ML, AutoML, and expert baselines.
data/               Local data cache. Raw/private data is not committed.
docs/               Research scope, related work, licensing, taxonomy.
papers/             Manuscript drafts and publication artifacts.
reports/            Generated benchmark reports and figures.
runs/               Agent and baseline run artifacts. Not committed by default.
schemas/            Task and scoring schemas.
scripts/            Utility scripts.
src/finds_agentbench/ Benchmark package and validation helpers.
tasks/              Task specifications and templates.
tests/              Unit tests for benchmark utilities.
```

## First Milestone

The first milestone is not a leaderboard. It is a reliable pilot benchmark:

- two flagship tasks runnable end to end;
- formal task and scoring schemas;
- minimal scorer and task validator;
- data licensing register;
- first naive/classical baselines;
- initial failure taxonomy.

## Current Runnable Task

The first runnable vertical slice is `leakage_audit_temporal_split_v0`, a synthetic audit task with controlled leakage traps.

Generate the task data and private answer key:

```bash
PYTHONPATH=src python scripts/generate_leakage_audit_temporal_split_v0.py --seed 7
```

Validate the task spec:

```bash
PYTHONPATH=src python scripts/validate_task.py tasks/pilot/leakage_audit_temporal_split_v0.yaml
```

Score the included expert sanity-check submission:

```bash
PYTHONPATH=src python scripts/score_leakage_audit_temporal_split_v0.py \
  --submission-dir baselines/leakage_audit_temporal_split_v0/expert_submission
```

The generated `data/raw/`, `data/private/`, and `runs/` artifacts are ignored by git.

The first runnable predictive slice is `synthetic_market_direction_v0`, a synthetic market panel with a private temporal holdout.

Generate data:

```bash
PYTHONPATH=src python scripts/generate_synthetic_market_direction_v0.py --seed 11
```

Run and score the momentum baseline:

```bash
PYTHONPATH=src python baselines/synthetic_market_direction_v0/momentum_baseline.py
PYTHONPATH=src python scripts/score_synthetic_market_direction_v0.py \
  --submission runs/synthetic_market_direction_v0/momentum_baseline/predictions.csv \
  --output-json runs/synthetic_market_direction_v0/momentum_baseline/score.json
```

Validate a full submission directory, including notebook execution:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir
```

Add leakage scanning for forbidden private-artifact access:

```bash
PYTHONPATH=src python scripts/validate_submission_artifacts.py \
  tasks/pilot/synthetic_market_direction_v0.yaml path/to/submission_dir \
  --scan-leakage
```

The standalone scanner is also available:

```bash
PYTHONPATH=src python scripts/scan_submission_leakage.py path/to/submission_dir
```

Scan for temporal-validation and preprocessing methodology risks:

```bash
PYTHONPATH=src python scripts/scan_submission_methodology.py path/to/submission_dir
```

Create and validate a run manifest after scoring:

```bash
PYTHONPATH=src python scripts/create_run_manifest.py \
  --task-id synthetic_market_direction_v0 \
  --agent-id momentum_baseline \
  --agent-version 0.1.0 \
  --submission-dir runs/synthetic_market_direction_v0/momentum_baseline \
  --scores-json runs/synthetic_market_direction_v0/momentum_baseline/score.json \
  --output runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json

PYTHONPATH=src python scripts/validate_run_manifest.py \
  runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```

Build paper-ready run summary tables:

```bash
PYTHONPATH=src python scripts/build_run_report.py \
  --runs-root runs \
  --csv-output reports/generated/run_results.csv \
  --markdown-output reports/generated/run_results.md \
  --summary-csv-output reports/generated/run_summary.csv \
  --summary-markdown-output reports/generated/run_summary.md
```

Run the complete synthetic momentum baseline pipeline in one command:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py
```

This generates data, writes baseline submission artifacts, scores predictions, validates artifacts with leakage scanning, writes a run manifest, and rebuilds reports. Add `--execute-notebook` when the environment supports Jupyter kernel execution.

Run the model-based logistic regression baseline:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py
```

The logistic baseline fits preprocessing and the classifier on the chronological train split, selects the classification threshold on public validation, and only then predicts the private temporal holdout.

The first runnable event-aware slice is `synthetic_event_response_v0`, a synthetic event panel with event surprise, sentiment, importance, pre-event context, and a private temporal holdout.

Run its rule baseline end to end:

```bash
PYTHONPATH=src python scripts/run_synthetic_event_response_rule_pipeline.py
```

Run a repeated external-agent evaluation on the event-response task:

```bash
PYTHONPATH=src python scripts/run_synthetic_event_response_agent_suite.py \
  --agent-id event_rule_env_agent \
  --agent-version 0.1.0 \
  --agent-command "python agents/examples/event_rule_env_agent.py" \
  --repeat 3 \
  --seed 23 \
  --run-label-prefix pilot_event_agent
```

Run a repeated baseline protocol for uncertainty estimates:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_baseline_suite.py \
  --repeat 3 \
  --seed 11 \
  --run-label-prefix pilot
```

Repeated runs write separate run directories, preserve per-run `seed` and `run_label` metadata in `run_manifest.json`, and rebuild both `reports/generated/run_results.*` and `reports/generated/run_summary.*`. The summary tables aggregate by task, agent, and run type with count/mean/std/min/max for core metrics.

The suite runner uses `runs/suites/synthetic_market_direction_v0_pilot` by default so paper-facing summaries do not mix prototype runs with controlled repeated-run experiments.

Run an external agent command through the synthetic-market harness:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_command.py \
  --agent-id my_agent \
  --agent-version dev \
  --agent-command "python agents/my_agent.py" \
  --run-label pilot_001_seed_11
```

The harness exposes only public task/data paths through `FINDS_*` environment variables, captures logs, scores the submission, validates artifacts, writes `run_manifest.json`, and rebuilds reports.

Run repeated external-agent evaluation:

```bash
PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py \
  --agent-id momentum_env_agent \
  --agent-version 0.1.0 \
  --agent-command "python agents/examples/momentum_env_agent.py" \
  --repeat 3 \
  --seed 11 \
  --run-label-prefix pilot_agent
```

The agent suite defaults to `runs/suites/synthetic_market_direction_v0_agents`, giving agent experiments the same count/mean/std reporting protocol as baseline suites.

## Status

Draft scaffold. APIs, task specs, and metrics are expected to evolve until the pilot benchmark is locked.
