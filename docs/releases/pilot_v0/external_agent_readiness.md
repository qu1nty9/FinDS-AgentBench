# External Agent Readiness

This report gates claims about independent or stronger external-agent evidence.

## Status

| Field | Value |
| --- | --- |
| Status | `not_ready_no_external_agents` |
| Ready for external-agent claims | no |
| Bundled reference agents | 7 |
| External agent configurations | 0 |
| Completed external agent configurations | 0 |
| External task coverage | 0 / 8 |
| Minimum completed runs per task | 3 |

## Claim Boundary

- Allowed current claim: The benchmark includes a command-based external-agent harness and bundled reference agents.
- Disallowed current claim: Broad external-agent leaderboard or stronger external-agent evidence.

## Blocking Items

- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.

## Bundled Reference Agents

| Agent ID |
| --- |
| event_rule_env_agent |
| market_research_sweep_env_agent |
| treasury_curve_10y3mo_research_sweep_env_agent |
| treasury_curve_research_sweep_env_agent |
| treasury_front_end_research_sweep_env_agent |
| treasury_research_sweep_env_agent |
| usd_research_sweep_env_agent |

## Missing External Task Coverage

- `front_end_spread_widening_v0`
- `synthetic_event_response_v0`
- `synthetic_market_direction_v0`
- `usd_afe_vs_eme_relative_direction_v0`
- `usd_broad_direction_v0`
- `yield_curve_10y2y_steepening_v0`
- `yield_curve_10y3mo_steepening_v0`
- `yield_direction_treasury10y_v0`

## Next Actions

- Add an external_agent_configurations entry for a non-author agent.
- Run the agent with the same command harness, repeated seeds, task specs, and hidden-label protections.
- Regenerate reference results, readiness reports, and the manuscript checklist.
