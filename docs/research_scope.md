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

Pilot result tables should report repeated-run uncertainty, not only single-run scores. The run manifest trace records seed and run labels so benchmark summaries can aggregate count, mean, standard deviation, min, and max per task/agent configuration.

The first implemented vertical slices are:

- `leakage_audit_temporal_split_v0`: a synthetic audit task with controlled future-feature leakage, random temporal split misuse, and full-dataset preprocessing leakage.
- `synthetic_market_direction_v0`: a synthetic predictive task with public train/validation labels and private temporal holdout labels.
- `synthetic_event_response_v0`: a synthetic event-aware temporal reasoning task with event features, public train/validation labels, and private temporal holdout labels.
- `yield_direction_treasury10y_v0`: a real-data predictive rates task built from public-domain H.15/FRED series with public train/validation labels and a private temporal holdout.
- `yield_curve_10y2y_steepening_v0`: a real-data predictive curve task built from the same public-domain H.15/FRED series, relabeled for next-day 10Y-2Y steepening on a private temporal holdout.
- `yield_curve_10y3mo_steepening_v0`: a real-data predictive curve task built from the same public-domain H.15/FRED series, relabeled for next-day 10Y-3M steepening on a private temporal holdout.
- `front_end_spread_widening_v0`: a real-data predictive rates task built from the same public-domain H.15/FRED surface, relabeled for next-day 2Y-minus-fed-funds spread widening on a private temporal holdout.
- `usd_broad_direction_v0`: a real-data predictive FX task built from public-domain H.10/H.15 series with public train/validation labels and a private temporal holdout.
- `usd_afe_vs_eme_relative_direction_v0`: a real-data predictive FX relative-value task built from the same public-domain H.10/H.15 surface, relabeled for next-day AFE-versus-EME outperformance on a private temporal holdout.

## Stage 2 Scope

The full benchmark should expand to 30-50 tasks, add portfolio/backtest construction, hidden temporal holdouts, public task cards, evaluation cards, and a stronger benchmark harness.

## Stage 3 Scope

The journal version should study reliability mechanisms, not merely announce the benchmark. It should include intervention experiments, repeated-run variance, failure-mode analysis, and implications for financial model risk management.
