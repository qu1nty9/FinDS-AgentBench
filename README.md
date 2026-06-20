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

## Status

Draft scaffold. APIs, task specs, and metrics are expected to evolve until the pilot benchmark is locked.
