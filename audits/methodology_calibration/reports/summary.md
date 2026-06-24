# Methodology Calibration Summary

- Corpus entry count: `101`
- Flagged entry count: `4`
- Clean entry count: `97`
- Total methodology findings: `5`
- Scanned files: `617`
- Skipped files: `97`
- Clean-control review rows: `14`

## Corpus Coverage

| Corpus | Entries | Flagged | Clean | Findings |
| --- | --- | --- | --- | --- |
| curated_fixtures | 4 | 4 | 0 | 5 |
| pilot_agents | 21 | 0 | 21 | 0 |
| pilot_baselines | 76 | 0 | 76 | 0 |

## Task Coverage

| Task ID | Entries | Flagged | Clean | Findings |
| --- | --- | --- | --- | --- |
| front_end_spread_widening_v0 | 17 | 2 | 15 | 2 |
| synthetic_event_response_v0 | 7 | 0 | 7 | 0 |
| synthetic_market_direction_v0 | 12 | 1 | 11 | 2 |
| usd_afe_vs_eme_relative_direction_v0 | 15 | 0 | 15 | 0 |
| usd_broad_direction_v0 | 15 | 0 | 15 | 0 |
| yield_curve_10y2y_steepening_v0 | 15 | 0 | 15 | 0 |
| yield_direction_treasury10y_v0 | 20 | 1 | 19 | 1 |

## Rule Counts

| Rule ID | Severity | Finding Count | Flagged Entries |
| --- | --- | --- | --- |
| explicit_shuffle | error | 1 | 1 |
| forward_merge_asof_direction | error | 1 | 1 |
| future_aligned_merge_join | error | 1 | 1 |
| random_train_test_split | error | 1 | 1 |
| task_forbidden_feature_reference__next_day_change_bp | error | 1 | 1 |

## Fixture Evaluation

- Fixture count: `4`
- True positives: `4`
- False negatives: `0`
- False positives: `0`
- True negatives: `0`
- Expected-rule matches: `4`
- Expected-rule mismatches: `0`

| Fixture ID | Task ID | Confusion Label | Finding Count | Actual Rule IDs | Missing Expected Rules |
| --- | --- | --- | --- | --- | --- |
| synthetic_random_split_positive | synthetic_market_direction_v0 | true_positive | 2 | explicit_shuffle, random_train_test_split | - |
| front_end_future_join_positive | front_end_spread_widening_v0 | true_positive | 1 | future_aligned_merge_join | - |
| front_end_forward_merge_asof_positive | front_end_spread_widening_v0 | true_positive | 1 | forward_merge_asof_direction | - |
| treasury_forbidden_target_feature_positive | yield_direction_treasury10y_v0 | true_positive | 1 | task_forbidden_feature_reference__next_day_change_bp | - |

## Next Review Action

Fill `audits/methodology_calibration/reviews/calibration_review_packet.csv` to label finding rows as true or false positives and clean-control rows as true or false negatives.
