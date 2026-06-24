# Qualitative Failure Examples

Generated from `audits/pilot_v0/adjudicated_subset.json` for use in the workshop manuscript.

## pilot_event_rule_baseline_release_001

- Task: `synthetic_event_response_v0`
- System: `event_rule_baseline` (`baseline`)
- Run label: `release_pilot_event_001_seed_23`
- Audit label: `minimally_defensible`
- Total score: `6`
- Low-scoring dimensions: `temporal_protocol_correctness, quantitative_evidence_use, baseline_comparison_or_counterfactual_context, reproducibility_trace_completeness`
- Primary findings: Strong predictive score is not accompanied by quantitative narrative support; Temporal protocol description is brief; No comparator or ablation context appears in the writeup.
- Evidence: No ablation, heuristic comparison, or simpler event rule is discussed.
- Writeup reference: `runs/suites/pilot_baselines_v0/synthetic_event_response_v0/event_rule_baseline/release_pilot_event_001_seed_23/writeup.md`

## pilot_market_momentum_baseline_release_001

- Task: `synthetic_market_direction_v0`
- System: `momentum_baseline` (`baseline`)
- Run label: `release_pilot_market_001_seed_11`
- Audit label: `minimally_defensible`
- Total score: `6`
- Low-scoring dimensions: `temporal_protocol_correctness, quantitative_evidence_use, baseline_comparison_or_counterfactual_context, reproducibility_trace_completeness`
- Primary findings: No quantitative support in the writeup; No baseline or counterfactual comparison; Temporal protocol rationale is thinner than the artifact package itself.
- Evidence: The submission does not compare the momentum rule to any simpler or more expressive alternative.
- Writeup reference: `runs/suites/pilot_baselines_v0/synthetic_market_direction_v0/momentum_baseline/release_pilot_market_001_seed_11/writeup.md`

## pilot_event_rule_env_agent_protocol_001

- Task: `synthetic_event_response_v0`
- System: `event_rule_env_agent` (`agent`)
- Run label: `release_protocol_agent_event_001_seed_23`
- Audit label: `minimally_defensible`
- Total score: `7`
- Low-scoring dimensions: `temporal_protocol_correctness, quantitative_evidence_use, baseline_comparison_or_counterfactual_context`
- Primary findings: Agent trace provenance is stronger than the baseline trace; Narrative quality is still thin; No quantitative or comparative justification appears in the writeup.
- Evidence: The agent output does not situate the rule against any competing event heuristic.
- Writeup reference: `runs/suites/pilot_protocol_v0/synthetic_event_response_v0/event_rule_env_agent/release_protocol_agent_event_001_seed_23/writeup.md`

## pilot_market_logistic_baseline_release_001

- Task: `synthetic_market_direction_v0`
- System: `logistic_regression_baseline` (`baseline`)
- Run label: `release_pilot_market_001_seed_11`
- Audit label: `strong_but_incomplete`
- Total score: `10`
- Low-scoring dimensions: `baseline_comparison_or_counterfactual_context`
- Primary findings: Method description is strong; Quantitative support is present; Main remaining gap is missing comparison against simpler alternatives.
- Evidence: Even though a momentum baseline exists in the suite, the writeup does not compare against it or justify model complexity relative to a rule baseline.
- Writeup reference: `runs/suites/pilot_baselines_v0/synthetic_market_direction_v0/logistic_regression_baseline/release_pilot_market_001_seed_11/writeup.md`
