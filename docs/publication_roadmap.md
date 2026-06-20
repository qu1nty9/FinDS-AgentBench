# Publication Roadmap

FinDS-AgentBench should be built as a staged research program. Each stage must be complete enough to publish independently, while also preparing the next stage.

## Stage 0: Foundation

Goal: convert the research idea into a precise benchmark specification.

Required outputs:

- related-work matrix;
- formal task schema;
- scoring schema;
- failure taxonomy;
- data-source and license register;
- repository skeleton;
- two flagship draft tasks.

Acceptance criteria:

- every task can define prediction timestamp, allowed information, target horizon, temporal splits, forbidden features, leakage checks, and reproducibility rules;
- scoring separates predictive performance from research validity;
- data sources are marked as usable, risky, rejected, private-only, or pending.

## Stage 1: arXiv / Workshop Pilot

Goal: prove the benchmark thesis with a compact, rigorous pilot.

Scope:

- 8-12 tasks;
- 3 tracks: predictive financial ML, event-aware temporal reasoning, leakage audit;
- 4-6 agents or model-agent configurations;
- 3 runs per stochastic agent/task;
- naive and classical baselines;
- manual audit for a subset of outputs.

Main thesis:

> Agents often produce plausible financial ML notebooks, but apparent performance is fragile once temporal availability, leakage checks, transaction costs, and reproducibility are enforced.

Required outputs:

- arXiv/workshop paper;
- public pilot task suite;
- minimal evaluator;
- baseline notebooks;
- validity-adjusted result tables;
- failure taxonomy with examples.

Stop rule:

- do not expand beyond 12 pilot tasks until the task schema, evaluator, and failure taxonomy are stable.

## Stage 2: Top Benchmark / Dataset Venue

Goal: scale the pilot into a durable public benchmark suitable for a benchmark/dataset venue.

Scope:

- 30-50 tasks;
- 4 tracks: predictive ML, event-aware reasoning, research replication/audit, portfolio/backtest construction;
- hidden temporal holdout;
- public/private scoring split;
- task cards and evaluation cards;
- broader agent and baseline suite;
- expert audit rubric.

Required outputs:

- benchmark harness;
- private-holdout scorer or evaluation server;
- task registry;
- data manifests and checksums;
- leakage checker;
- notebook execution validator;
- artifact collector;
- public documentation;
- benchmark/dataset paper.

Acceptance criteria:

- external users can run the public subset without private instructions;
- hidden labels are not exposed;
- all public tasks have documented licenses and provenance;
- at least 8 agent/baseline configurations are evaluated;
- subjective writeup/audit scoring uses a rubric and reports agreement on a subset.

## Stage 3: Journal Extension

Goal: turn the benchmark into a methodological study of reliable AI-assisted financial ML research.

The journal version should add analysis beyond the benchmark announcement:

- repeated-run variance;
- intervention study with checklists, leakage feedback, and self-audit;
- task difficulty calibration;
- relationship between predictive score and validity dimensions;
- failure-mode co-occurrence;
- cost/reliability frontier;
- model-risk and governance implications.

Main thesis:

> Reliable AI-assisted financial ML research requires joint evaluation of point-in-time information use, temporal validation, leakage resistance, reproducibility, financial decision quality, and narrative discipline.

Acceptance criteria:

- benchmark version is frozen and archived;
- all experiments are reproducible from released artifacts or documented private evaluator;
- statistical claims include uncertainty estimates;
- subjective audit uses a documented rubric;
- conclusions distinguish benchmark performance from real-market deployment claims.

## Immediate Next Steps

1. Harden the current runnable slices with notebook execution validation.
2. Select a license-safe data source for `return_direction_etf_v0`.
3. Add a model-based baseline for `synthetic_market_direction_v0`.
4. Add a leakage checker that detects private answer-key access in agent artifacts.
5. Expand from 2 runnable tasks to the 8-12 task workshop pilot.
