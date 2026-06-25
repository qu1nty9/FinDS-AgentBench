# External Agent Intake Manifest

Checksum manifest for the external-agent intake packet and harness entry points.

## Status

| Field | Value |
| --- | --- |
| Status | `ready_for_external_agent_intake` |
| Ready for external-agent distribution | yes |
| Expected task coverage | 8 |
| Minimum completed runs per task | 3 |

## Claim Boundary

- Allowed current claim: A frozen external-agent intake packet and validation protocol are available.
- Disallowed current claim: Completed non-author external-agent evidence or stronger external-agent benchmark claims.

## External-Agent-Facing Files

| Role | Path | Size Bytes | SHA256 |
| --- | --- | --- | --- |
| external_agent_protocol | `docs/releases/pilot_v0/external_agent_protocol.md` | 2037 | `6552a6d995d557e90a2f950dfd5dafbf16247137fbc39e3d39106e6e296ef53a` |
| external_agent_handoff | `agents/external_agent_handoff.md` | 2488 | `0ecb38dbf783335d9280dd091edb05909d6aa0336663e2f708235c39a11cc086` |
| external_agent_registry | `agents/external_agent_registry.yaml` | 3606 | `393ce033894220b1e75796cb98e5804d7a4aaffa287de0f43add380ba4e0d4d1` |
| external_agent_registration_template | `agents/external_agent_registration_template.yaml` | 920 | `fd4e29ce474525968cb0790e1a4f28705d3f3e5579fbd7105ed650cb865d53d3` |
| external_agent_readiness_report | `docs/releases/pilot_v0/external_agent_readiness.md` | 1812 | `f023225f3c55da31b0c0b9f9bab7a5072ec833424ea430f095508c9116254dcd` |
| external_agent_registration_validation | `docs/releases/pilot_v0/external_agent_registration_validation.md` | 1589 | `5e68b3344a61162b1f1e707e4ac182fcb4b4c0e15ac5977d58c6ada7228a898d` |

## Harness Command Files

| Path | Size Bytes | SHA256 |
| --- | --- | --- |
| scripts/run_synthetic_market_agent_suite.py | 3819 | `1c1a3802e79585e2581c00828470b432fa1f788d180e871f7a093fba9214defd` |
| scripts/run_synthetic_event_response_agent_suite.py | 3825 | `b4d09d72a316adb742b36e8201197af006be8ec6d56241c5199c8e5e4f3ee5b7` |
| scripts/run_yield_direction_treasury10y_agent_suite.py | 4145 | `6a5457daf0a460d331f606d3511a563145c343de203ec53f1b821960eb070ac9` |
| scripts/run_yield_curve_10y2y_steepening_agent_suite.py | 4163 | `8902648601c272124d5e88acd7e3743aff7db74ca2abac5935f955e1ab92fd64` |
| scripts/run_yield_curve_10y3mo_steepening_agent_suite.py | 4183 | `a4f6106bf49cedf83248397928153822768ab96fdcaf57ade4efd03f1edfcb80` |
| scripts/run_front_end_spread_widening_v0_agent_suite.py | 4151 | `3bf5be260f98edfbeef362af2bc8c6a7e6e1906ac75392b502b5a8f994e1bf21` |
| scripts/run_usd_broad_direction_v0_agent_suite.py | 4106 | `3343bbc0c95a16bfb5bf196abab2c5f6728c0b3cd33cda903c28807827a3efec` |

## Expected Task Coverage

- `synthetic_market_direction_v0`
- `synthetic_event_response_v0`
- `yield_direction_treasury10y_v0`
- `yield_curve_10y2y_steepening_v0`
- `yield_curve_10y3mo_steepening_v0`
- `front_end_spread_widening_v0`
- `usd_broad_direction_v0`
- `usd_afe_vs_eme_relative_direction_v0`

## Required Environment Variables

- `FINDS_TASK_ID`
- `FINDS_RUN_SEED`
- `FINDS_TASK_SPEC_PATH`
- `FINDS_PUBLIC_DATA_DIR`
- `FINDS_TRAIN_PUBLIC_PATH`
- `FINDS_HOLDOUT_FEATURES_PATH`
- `FINDS_PRIVATE_HOLDOUT_FEATURES_PATH`
- `FINDS_SAMPLE_SUBMISSION_PATH`
- `FINDS_METADATA_PATH`
- `FINDS_SUBMISSION_DIR`

## Required Submission Artifacts

- `notebook.ipynb`
- `predictions.csv`
- `writeup.md`

## Bundled Reference Configurations

| Agent | Command Family | Tasks | Reason Not External Evidence |
| --- | --- | --- | --- |
| market_research_sweep_env_agent | scripts/run_synthetic_market_agent_suite.py | synthetic_market_direction_v0 | Bundled reference agents are maintained by benchmark authors. |
| event_rule_env_agent | scripts/run_synthetic_event_response_agent_suite.py | synthetic_event_response_v0 | Bundled reference agents are maintained by benchmark authors. |
| treasury_research_sweep_env_agent | scripts/run_yield_direction_treasury10y_agent_suite.py | yield_direction_treasury10y_v0 | Bundled reference agents are maintained by benchmark authors. |
| treasury_curve_research_sweep_env_agent | scripts/run_yield_curve_10y2y_steepening_agent_suite.py | yield_curve_10y2y_steepening_v0 | Bundled reference agents are maintained by benchmark authors. |
| treasury_curve_10y3mo_research_sweep_env_agent | scripts/run_yield_curve_10y3mo_steepening_agent_suite.py | yield_curve_10y3mo_steepening_v0 | Bundled reference agents are maintained by benchmark authors. |
| treasury_front_end_research_sweep_env_agent | scripts/run_front_end_spread_widening_v0_agent_suite.py | front_end_spread_widening_v0 | Bundled reference agents are maintained by benchmark authors. |
| usd_research_sweep_env_agent | scripts/run_usd_broad_direction_v0_agent_suite.py | usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0 | Bundled reference agents are maintained by benchmark authors. |

## Completion Requirements

- Copy agents/external_agent_registration_template.yaml into an external_agent_configurations entry.
- Set maintainer_type=external and provenance=external_submission for the non-author configuration.
- Run the agent through the registered command family for the required repeated runs per task.
- Record completed_runs_per_task and every run_manifest_path after the harness finishes.
- Rebuild reference results and readiness artifacts before making external-agent claims.
- Validate with scripts/validate_external_agent_registry.py before submission claims.

## Validation Command

```bash
PYTHONPATH=src python scripts/validate_external_agent_registry.py
```

