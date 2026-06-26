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

Public task cards and evaluation cards can be generated from the YAML task specs:

```bash
PYTHONPATH=src python scripts/build_task_cards.py
```

This builds `docs/cards/README.md`, per-task cards, per-task evaluation cards, and a machine-readable task registry.

Public data manifests and checksums can be generated with:

```bash
PYTHONPATH=src python scripts/build_data_manifests.py
```

This builds `docs/data_manifests/pilot_v0/README.md`, per-task public-data manifests, and machine-readable checksum indexes.

A full pilot release snapshot can be rebuilt with one command:

```bash
PYTHONPATH=src python scripts/build_pilot_release.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --treasury-seed 29 \
  --curve-seed 31 \
  --curve3mo-seed 33 \
  --front-end-seed 31 \
  --usd-seed 37 \
  --treasury-snapshot-date 2026-06-21 \
  --curve-snapshot-date 2026-06-21 \
  --curve3mo-snapshot-date 2026-06-21 \
  --front-end-snapshot-date 2026-06-21 \
  --usd-snapshot-date 2026-06-21 \
  --clean-existing-outputs
```

This runs the pilot baseline suite, pilot agent suite, combined pilot protocol, reference-results build, paper-artifact build, statistical-artifact build, and benchmark-manifest build under one reproducible release pipeline.

The deterministic smoke check used in CI can also be run locally:

```bash
PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py \
  --work-root tmp/pilot_release_repro_check \
  --repeat 1 \
  --treasury-snapshot-date 2026-06-21 \
  --curve-snapshot-date 2026-06-21 \
  --curve3mo-snapshot-date 2026-06-21 \
  --front-end-snapshot-date 2026-06-21 \
  --usd-snapshot-date 2026-06-21
```

This builds the pilot release twice on isolated roots and compares deterministic publication-facing outputs: suite summaries, reference results, paper artifacts, statistical artifacts, benchmark manifest, task cards, and public data manifests.

The pilot release candidate can be packaged as a deterministic archive with file-level checksums:

```bash
PYTHONPATH=src python scripts/build_release_archive.py
```

This writes a generated archive under `dist/release_archives/` and records the archive checksum and per-file SHA256 manifest in `docs/releases/pilot_v0/archive_manifest.json` and `docs/releases/pilot_v0/archive_manifest.md`. The archive remains marked as a candidate until the independent-review, external-agent, and final tag gates pass.

Verify the archive against its checksum manifest before sharing it:

```bash
PYTHONPATH=src python scripts/verify_release_archive.py
```

If only the manifest/cards/data indexes need to be refreshed, the canonical pilot release manifest can be built with:

```bash
PYTHONPATH=src python scripts/build_benchmark_manifest.py
```

This writes `docs/releases/pilot_v0/manifest.json` and `docs/releases/pilot_v0/README.md`, linking task cards, data manifests, runnable status, and official pilot suite commands.

The arXiv/workshop manuscript scaffold can be regenerated from the release artifacts with:

```bash
PYTHONPATH=src python scripts/build_pilot_manuscript.py
```

This writes `papers/workshop_pilot/main.tex`, manuscript metadata, and a submission-readiness checklist while inputting result tables directly from `docs/releases/pilot_v0/`.

Check static LaTeX readiness, citation/label consistency, and PDF-risk warnings with:

```bash
PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py
```

Build the publication-gate manifest that maps CI checks, release verification, manuscript formatting, and remaining evidence blockers:

```bash
PYTHONPATH=src python scripts/build_publication_gate_manifest.py
```

CI uses the same generator in stale-check mode:

```bash
PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check
```

Build the workshop submission package manifest that inventories manuscript files, release artifacts, claim boundaries, archive checksums, and remaining blockers:

```bash
PYTHONPATH=src python scripts/build_submission_package_manifest.py
```

CI checks it for staleness as well:

```bash
PYTHONPATH=src python scripts/build_submission_package_manifest.py --check
```


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

The methodology scanner now flags obvious temporal anti-patterns such as random splits, K-fold on temporal data, negative shifts like `shift(-1)`, centered rolling windows, backfilling, and feature construction that appears to reference target-like columns.

Rebuild the methodology-calibration workflow over the current pilot corpus:

```bash
PYTHONPATH=src python scripts/build_methodology_calibration_workflow.py
```

This writes a machine-readable summary under `audits/methodology_calibration/reports/` and a manual review packet under `audits/methodology_calibration/reviews/calibration_review_packet.csv` so false positives and false negatives can be tracked explicitly.

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

The pilot also now includes a second public-domain macro-rates slice, `yield_curve_10y2y_steepening_v0`, which predicts next-day steepening in the U.S. 10Y-2Y Treasury curve under the same point-in-time H.15 constraints used for the 10-year yield task.

It also includes a second public-domain FX slice, `usd_afe_vs_eme_relative_direction_v0`, which predicts whether the advanced-foreign-economies dollar index outperforms the emerging-markets dollar index on the next business day under the same vintage-frozen H.10/H.15 constraints used for `usd_broad_direction_v0`.

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

Run all implemented pilot baselines across runnable tasks:

```bash
PYTHONPATH=src python scripts/run_pilot_baseline_suite.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot
```

This currently runs the synthetic baselines plus the Treasury 10Y, Treasury curve, USD broad, and USD AFE-versus-EME relative baseline families under one report root: `runs/suites/pilot_baselines_v0`.

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
  --agent-id market_research_sweep_env_agent \
  --agent-version 0.2.0 \
  --agent-command "python agents/examples/research_sweep_env_agent.py" \
  --repeat 3 \
  --seed 11 \
  --run-label-prefix pilot_agent
```

The agent suite defaults to `runs/suites/synthetic_market_direction_v0_agents`, giving agent experiments the same count/mean/std reporting protocol as baseline suites.

`agents/examples/research_sweep_env_agent.py` is task-aware: it compares multiple public baselines on public validation for synthetic market, Treasury 10Y, Treasury curve, USD broad, and USD AFE-versus-EME relative tasks, then writes holdout predictions with the selected candidate.

Run the cross-task pilot agent suite with the bundled example wrappers:

```bash
PYTHONPATH=src python scripts/run_pilot_agent_suite.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot_agent
```

This runs the task-aware `agents/examples/research_sweep_env_agent.py` for market, Treasury, curve, and USD tasks plus `agents/examples/event_rule_env_agent.py` for the event task under one report root: `runs/suites/pilot_agents_v0`.

Run the combined pilot protocol across implemented baselines and example agents:

```bash
PYTHONPATH=src python scripts/run_pilot_protocol.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --run-label-prefix pilot_protocol
```

This produces one shared publication-facing report root, `runs/suites/pilot_protocol_v0`, with both baseline and agent runs included in the same result and summary tables.

Rebuild the full pilot release bundle in one shot:

```bash
PYTHONPATH=src python scripts/build_pilot_release.py \
  --repeat 3 \
  --market-seed 11 \
  --event-seed 23 \
  --treasury-seed 29 \
  --curve-seed 31 \
  --curve3mo-seed 33 \
  --front-end-seed 31 \
  --usd-seed 37 \
  --treasury-snapshot-date 2026-06-21 \
  --curve-snapshot-date 2026-06-21 \
  --curve3mo-snapshot-date 2026-06-21 \
  --front-end-snapshot-date 2026-06-21 \
  --usd-snapshot-date 2026-06-21 \
  --clean-existing-outputs
```

This writes the publication-facing suite reports under `reports/release_runs/`, then refreshes `docs/releases/pilot_v0/reference_results.{md,json}`, `docs/releases/pilot_v0/paper_artifacts/`, `docs/releases/pilot_v0/statistical_artifacts/`, and `docs/releases/pilot_v0/manifest.json`.

GitHub Actions runs this release gate in `.github/workflows/ci.yml`, including a smoke job that rebuilds the pilot release twice and fails on deterministic artifact drift.
When that smoke job fails, it uploads a compact forensics bundle with `summary.json`, `summary.md`, copied conflicting artifacts, and unified text diffs for direct diagnosis.

## Status

Draft scaffold. APIs, task specs, and metrics are expected to evolve until the pilot benchmark is locked.
