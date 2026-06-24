# External Agent Protocol

This protocol defines how non-author agents should be evaluated in FinDS-AgentBench.

## Submission Contract

- Agents are launched through the existing `scripts/run_*_agent_suite.py` wrappers.
- Commands are parsed with `shlex`; private answer-key paths are not exposed in the agent environment.
- Each completed run must write the required submission artifacts before scoring.
- Run manifests, stdout, stderr, validation, score, and methodology reports are retained under the run directory.

## Required Environment

| Variable | Meaning |
| --- | --- |
| FINDS_TASK_ID | provided by the harness |
| FINDS_RUN_SEED | provided by the harness |
| FINDS_TASK_SPEC_PATH | provided by the harness |
| FINDS_PUBLIC_DATA_DIR | provided by the harness |
| FINDS_TRAIN_PUBLIC_PATH | provided by the harness |
| FINDS_HOLDOUT_FEATURES_PATH | provided by the harness |
| FINDS_PRIVATE_HOLDOUT_FEATURES_PATH | provided by the harness |
| FINDS_SAMPLE_SUBMISSION_PATH | provided by the harness |
| FINDS_METADATA_PATH | provided by the harness |
| FINDS_SUBMISSION_DIR | provided by the harness |

## Required Artifacts

| Artifact | Requirement |
| --- | --- |
| notebook.ipynb | required in FINDS_SUBMISSION_DIR |
| predictions.csv | required in FINDS_SUBMISSION_DIR |
| writeup.md | required in FINDS_SUBMISSION_DIR |

## Workshop Readiness Requirement

- Minimum external agent configurations: `1`
- Minimum completed runs per task: `3`
- Expected task coverage: `synthetic_market_direction_v0, synthetic_event_response_v0, yield_direction_treasury10y_v0, yield_curve_10y2y_steepening_v0, yield_curve_10y3mo_steepening_v0, front_end_spread_widening_v0, usd_broad_direction_v0, usd_afe_vs_eme_relative_direction_v0`

## Current Claim Boundary

- Current readiness status: `not_ready_no_external_agents`
- Allowed current claim: The benchmark includes a command-based external-agent harness and bundled reference agents.
- Disallowed current claim: Broad external-agent leaderboard or stronger external-agent evidence.
