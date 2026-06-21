# leakage_audit_temporal_split_v0 Evaluation Card

Source task specification: `tasks/pilot/leakage_audit_temporal_split_v0.yaml`.

## Metrics

| Field | Value |
| --- | --- |
| Primary Metric | audit_correctness_score |
| Aggregation | rubric_plus_vector_scores |
| Secondary Metrics | leakage_identification, corrected_temporal_validation, before_after_quantification, execution_success, reproducibility |
| Financial Metrics | - |

## Validity Gates

- artifact_executable
- temporal_holdout_respected
- no_forbidden_features
- validation_protocol_valid
- reproducible_rerun

## Minimum Success Conditions

- Agent identifies at least one true leakage mechanism.
- Corrected notebook uses temporal validation.
- Audit note reports both flawed and corrected metrics.

## Leakage and Validation Checks


**Forbidden Columns**

- feature_future_return_leak
- target


**Temporal Alignment Checks**

- Target-derived features are shifted.
- Validation rows are later than training rows.


**Validation Protocol Checks**

- Random splits are replaced with temporal splits.
- Preprocessing is fit on train only.


**Known Leakage Traps**

- Future-return feature included in training.
- StandardScaler fit on the full dataset.
- Random split across dates.

## Human Review Rubric

- Did the agent correctly identify the leakage trap?
- Did the corrected workflow remove the trap?
- Did the writeup avoid presenting flawed results as valid?

## Failure Taxonomy References

- temporal_leakage
- invalid_validation
- reproducibility_failure
- unsupported_narrative
