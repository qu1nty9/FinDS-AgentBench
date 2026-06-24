# Independent Reviewer Packet Validation

Validation report for a submission-strength manual-audit second-reviewer packet.

## Status

| Field | Value |
| --- | --- |
| Status | `invalid_or_incomplete` |
| Ready for independent agreement | no |
| Completed cases | 0 / 6 |
| Rows | 6 |
| Reviewer IDs | reviewer_2 |
| Reviewer Roles | independent_reviewer |
| Review Sources | blank_template |
| Errors | 4 |

## Errors

- review_source is not acceptable for independent review: blank_template
- review_status must be complete for every row: pilot_market_momentum_baseline_release_001, pilot_market_logistic_baseline_release_001, pilot_event_rule_baseline_release_001, pilot_event_rule_env_agent_protocol_001, pilot_treasury_previous_day_baseline_release_001, pilot_treasury_logistic_baseline_release_001
- all rubric scores, evidence notes, and overall_label must be complete for every row: pilot_market_momentum_baseline_release_001, pilot_market_logistic_baseline_release_001, pilot_event_rule_baseline_release_001, pilot_event_rule_env_agent_protocol_001, pilot_treasury_previous_day_baseline_release_001, pilot_treasury_logistic_baseline_release_001
- primary_manual_findings must be non-empty for: pilot_market_momentum_baseline_release_001, pilot_market_logistic_baseline_release_001, pilot_event_rule_baseline_release_001, pilot_event_rule_env_agent_protocol_001, pilot_treasury_previous_day_baseline_release_001, pilot_treasury_logistic_baseline_release_001

## Next Actions

- Fix validation errors in the reviewer packet.
- Re-run scripts/validate_manual_audit_review_packet.py.
- Rebuild manual-audit workflow artifacts once validation passes.
