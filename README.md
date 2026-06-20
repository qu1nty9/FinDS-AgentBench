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
  --submission runs/synthetic_market_direction_v0/momentum_baseline/predictions.csv
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

Create and validate a run manifest after scoring:

```bash
PYTHONPATH=src python scripts/create_run_manifest.py \
  --task-id synthetic_market_direction_v0 \
  --agent-id momentum_baseline \
  --agent-version 0.1.0 \
  --submission-dir runs/synthetic_market_direction_v0/momentum_baseline \
  --output runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json

PYTHONPATH=src python scripts/validate_run_manifest.py \
  runs/synthetic_market_direction_v0/momentum_baseline/run_manifest.json
```

## Status

Draft scaffold. APIs, task specs, and metrics are expected to evolve until the pilot benchmark is locked.
