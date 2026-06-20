# Research Scope

FinDS-AgentBench evaluates AI agents that produce end-to-end financial ML research artifacts.

The benchmark is not limited to prediction accuracy. A run can achieve a high predictive score and still fail if it uses future information, invalid temporal validation, unreproducible code, or unsupported financial claims.

## Central Claim

Financial ML agent evaluation must jointly test:

- point-in-time information use;
- temporal validation;
- leakage resistance;
- reproducibility;
- financial decision quality;
- narrative discipline in the final writeup.

## Stage 1 Scope

The pilot paper should use 8-12 tasks across:

- predictive financial ML;
- event-aware temporal reasoning;
- leakage audit and research replication.

The pilot should avoid becoming a general finance benchmark. Its job is to prove that validity-gated evaluation reveals failures that ordinary predictive scoring hides.

The first implemented vertical slices are:

- `leakage_audit_temporal_split_v0`: a synthetic audit task with controlled future-feature leakage, random temporal split misuse, and full-dataset preprocessing leakage.
- `synthetic_market_direction_v0`: a synthetic predictive task with public train/validation labels and private temporal holdout labels.

## Stage 2 Scope

The full benchmark should expand to 30-50 tasks, add portfolio/backtest construction, hidden temporal holdouts, public task cards, evaluation cards, and a stronger benchmark harness.

## Stage 3 Scope

The journal version should study reliability mechanisms, not merely announce the benchmark. It should include intervention experiments, repeated-run variance, failure-mode analysis, and implications for financial model risk management.
