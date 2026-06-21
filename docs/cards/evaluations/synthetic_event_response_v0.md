# synthetic_event_response_v0 Evaluation Card

Source task specification: `tasks/pilot/synthetic_event_response_v0.yaml`.

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
- No private labels or next-day reaction returns are used.

## Leakage and Validation Checks


**Forbidden Columns**

- event_reaction_positive
- next_day_return
- future_event_reaction


**Temporal Alignment Checks**

- Event features must be known at day t.
- Pre-event market context must exclude day t+1 reaction.
- Train, validation, and private holdout are ordered chronologically.


**Validation Protocol Checks**

- Random train/test split is not allowed for final model selection.
- Hyperparameter tuning must use train/public validation only.


**Known Leakage Traps**

- Reading `data/private/synthetic_event_response_v0/answer_key.csv`.
- Joining private holdout features to event reaction labels before submission.
- Tuning directly against private holdout score.

## Human Review Rubric

- Does the writeup compare against a simple event-rule baseline?
- Does the notebook avoid private answer-key access?
- Does the validation protocol respect temporal ordering?

## Failure Taxonomy References

- temporal_leakage
- invalid_validation
- weak_financial_reasoning
- reproducibility_failure
