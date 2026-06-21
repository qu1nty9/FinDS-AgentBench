# synthetic_market_direction_v0 Evaluation Card

Source task specification: `tasks/pilot/synthetic_market_direction_v0.yaml`.

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

- Prediction file covers every private holdout row.
- Probabilities are in [0, 1].
- No private labels are used.

## Leakage and Validation Checks


**Forbidden Columns**

- next_day_positive_return
- next_day_return


**Temporal Alignment Checks**

- Features must use information through day t only.
- Train, validation, and private holdout are ordered chronologically.


**Validation Protocol Checks**

- Random train/test split is not allowed for final model selection.
- Hyperparameter tuning must use train/public validation only.


**Known Leakage Traps**

- Reading `data/private/synthetic_market_direction_v0/answer_key.csv`.
- Joining private holdout features to labels before submission.
- Tuning directly against private holdout score.

## Human Review Rubric

- Does the writeup compare against the momentum baseline?
- Does the notebook avoid private answer-key access?
- Does the validation protocol respect temporal ordering?

## Failure Taxonomy References

- temporal_leakage
- invalid_validation
- weak_financial_reasoning
- reproducibility_failure
