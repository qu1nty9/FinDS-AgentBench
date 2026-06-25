# Independent Participant Brief

This brief defines the non-author participants needed before FinDS-AgentBench can make submission-strength independent-review and external-agent evidence claims.

## Required Before Workshop Submission

| Role | Minimum Count | Independence Requirement | Primary Deliverable | Gate Closed |
| --- | ---: | --- | --- | --- |
| Independent manual-audit reviewer | 1 | Not an author, benchmark implementer, or seed-subset adjudicator | Completed reviewer packet copied from `audits/pilot_v0/reviews/reviewer_2_blank_template.csv` | `manual_audit_independent_review` |
| Non-author external-agent participant | 1 | Maintains or operates an agent configuration outside the benchmark authors' bundled reference agents | Registered external-agent configuration with validated run manifests | `external_agent_evidence` |

## Preferred For Stronger Submission

| Role | Target Count | Why It Helps |
| --- | ---: | --- |
| Independent manual-audit reviewer | 2 | Enables more robust disagreement analysis and adjudication before publication. |
| Non-author external-agent participant | 2-3 | Reduces the risk that external-agent claims depend on a single implementation style. |
| Finance/ML domain reader | 1 | Reviews task realism, financial caveats, and overclaiming without changing benchmark outputs. |
| Reproducibility reader | 1 | Runs the release archive verifier and checks that public instructions are executable. |

## Manual-Audit Reviewer Profile

Good candidates:

- understand machine-learning experiment evaluation;
- can read short financial ML writeups and identify leakage, validation, evidence, and reproducibility issues;
- are comfortable assigning rubric scores with short evidence notes;
- have no role in creating the current rubric, seed subset, or benchmark implementation.

Estimated work:

- 6 pilot cases for the current seed subset;
- roughly 60-120 minutes for a careful first pass;
- short follow-up if adjudication needs clarification.

Send them:

- `audits/pilot_v0/reviews/independent_reviewer_handoff.md`;
- `audits/pilot_v0/reviews/independent_reviewer_packet_manifest.md`;
- `audits/pilot_v0/reviews/reviewer_2_blank_template.csv`;
- `audits/pilot_v0/manual_audit_rubric.yaml`;
- the referenced run artifact directories listed in the packet.

Required return:

- a completed reviewer CSV using one non-author `reviewer_id`;
- `reviewer_role=independent_reviewer`;
- `review_status=complete` for every row;
- all rubric scores, evidence notes, `overall_label`, and `primary_manual_findings` filled.

Validation command:

```bash
PYTHONPATH=src python scripts/validate_manual_audit_review_packet.py --packet audits/pilot_v0/reviews/reviewer_2_completed.csv
```

## External-Agent Participant Profile

Good candidates:

- can run a command-line Python benchmark harness;
- can provide or operate an agent that is not a bundled FinDS-AgentBench reference wrapper;
- can preserve run artifacts and run manifests;
- can tolerate public-data-only, hidden-label, and temporal protocol restrictions.

Estimated work:

- minimum: one non-author agent configuration;
- required workshop setting: 3 completed runs per covered task;
- ideal: full expected task coverage across the 8 predictive pilot tasks, or an explicitly declared scoped subset if full coverage is not feasible.

Send them:

- `docs/releases/pilot_v0/external_agent_intake_manifest.md`;
- `docs/releases/pilot_v0/external_agent_protocol.md`;
- `agents/external_agent_handoff.md`;
- `agents/external_agent_registration_template.yaml`;
- `agents/external_agent_registry.yaml`;
- task cards and data manifests under `docs/cards/` and `docs/data_manifests/pilot_v0/`.

Required return:

- an `external_agent_configurations` entry in `agents/external_agent_registry.yaml`;
- `maintainer_type=external`;
- `provenance=external_submission`;
- `included_in_reference_results=true` only after reference results include the runs;
- `stronger_external_evidence=true` only after the evidence is complete and validated;
- `completed_runs_per_task`;
- one `run_manifest.json` path per completed run.

Validation command:

```bash
PYTHONPATH=src python scripts/validate_external_agent_registry.py
```

## Conflict And Eligibility Rules

Do not count a person as independent if they:

- authored benchmark code, task specs, scoring code, or paper text;
- filled the seed adjudicated subset;
- maintain the bundled reference agents;
- have access to private labels or non-public answer keys;
- are being asked to validate their own benchmark contribution.

Acceptable but disclose:

- academic colleagues who did not author this benchmark;
- lab members who did not implement the benchmark, if independence is limited and clearly stated;
- industry practitioners who run a proprietary agent but return only benchmark artifacts.

## Current Claim Boundary

Until these participants return validated artifacts, the project may claim that reviewer and external-agent intake workflows are ready. It must not claim independent manual-audit agreement, external-agent leaderboard coverage, or completed non-author external-agent evidence.
