# usd_broad_direction_v0 Evaluation Card

Source task specification: `tasks/pilot/usd_broad_direction_v0.yaml`.

## Metrics

| Field | Value |
| --- | --- |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |
| Aggregation | report_vector_scores |
| Secondary Metrics | roc_auc, log_loss, execution_success, leakage_safety, validation_correctness, reproducibility |
| Financial Metrics | long_flat_mean_return, turnover, max_drawdown |

## Validity Gates

- artifact_executable
- prediction_format_valid
- temporal_holdout_respected
- no_forbidden_features
- validation_protocol_valid
- reproducible_rerun

## Minimum Success Conditions

- Notebook executes cleanly.
- Prediction file covers every private holdout row.
- No future H.10 or H.15 observations are used.

## Leakage and Validation Checks


**Forbidden Columns**

- next_day_usd_broad_up
- next_day_return
- usd_broad_t_plus_1
- future_usd_index
- future_fx_return


**Temporal Alignment Checks**

- All lagged and rolling features exclude day t+1 or later observations.
- Train, validation, and holdout rows are ordered chronologically.


**Validation Protocol Checks**

- Random train/test split is not allowed.
- Hyperparameter tuning must use train/public validation only.


**Known Leakage Traps**

- Using unshifted rolling windows that include the next-day return in normalization statistics.
- Standardizing features on the full dataset before chronological splitting.
- Joining later macro or policy annotations directly onto prediction rows.

## Human Review Rubric

- Does the writeup compare against a chronological sign or logistic baseline?
- Does the writeup avoid causal claims that exceed the benchmark evidence?
- Does the notebook enforce point-in-time feature alignment?

## Failure Taxonomy References

- temporal_leakage
- invalid_validation
- weak_macro_financial_reasoning
- unsupported_narrative
