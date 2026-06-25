# External Agent Handoff

Use this protocol to register and run a non-author external agent for FinDS-AgentBench.

## Claim Boundary

- Bundled reference agents are benchmark-maintained examples.
- A submission-strength external-agent claim requires a non-author configuration with completed run evidence.
- Do not mark `stronger_external_evidence: true` until the run manifests are included in reference results.

## Registration

- Start from `agents/external_agent_registration_template.yaml`.
- Verify the intake files against `docs/releases/pilot_v0/external_agent_intake_manifest.md` before running the agent.
- Add the completed entry under `external_agent_configurations` in `agents/external_agent_registry.yaml`.
- Set `maintainer_type: external` and `provenance: external_submission`.
- Record `completed_runs_per_task` and every `run_manifest_path` after the harness finishes.

## Required Coverage

- Minimum external configurations: `1`
- Minimum completed runs per task: `3`
- Expected task IDs: `synthetic_market_direction_v0, synthetic_event_response_v0, yield_direction_treasury10y_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, front_end_spread_widening_v0, usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0`

## Validation

```bash
PYTHONPATH=src python scripts/validate_external_agent_registry.py
```

The registry is eligible for external-agent claims only when the validation report and readiness report both say ready.

## Existing Harness Families

| Bundled Agent | Command Family | Tasks |
| --- | --- | --- |
| market_research_sweep_env_agent | scripts/run_synthetic_market_agent_suite.py | synthetic_market_direction_v0 |
| event_rule_env_agent | scripts/run_synthetic_event_response_agent_suite.py | synthetic_event_response_v0 |
| treasury_research_sweep_env_agent | scripts/run_yield_direction_treasury10y_agent_suite.py | yield_direction_treasury10y_v0 |
| treasury_curve_research_sweep_env_agent | scripts/run_yield_curve_10y2y_steepening_agent_suite.py | yield_curve_10y2y_steepening_v0 |
| treasury_curve_10y3mo_research_sweep_env_agent | scripts/run_yield_curve_10y3mo_steepening_agent_suite.py | yield_curve_10y3mo_steepening_v0 |
| treasury_front_end_research_sweep_env_agent | scripts/run_front_end_spread_widening_v0_agent_suite.py | front_end_spread_widening_v0 |
| usd_research_sweep_env_agent | scripts/run_usd_broad_direction_v0_agent_suite.py | usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0 |
