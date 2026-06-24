# Submission Readiness

Release-facing gate for treating the pilot manuscript as workshop-submission ready.

## Status

| Field | Value |
| --- | --- |
| Status | `not_ready_for_workshop_submission` |
| Ready for workshop submission | no |
| Ready gates | 3 / 6 |
| Blocking gates | 3 |

## Gates

| Gate | Ready | Status | Blockers |
| --- | --- | --- | --- |
| pilot_release_scope | yes | `ready` | - |
| statistical_artifacts | yes | `ready` | - |
| manual_audit_independent_review | no | `not_ready_seed_only` | Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.; Rebuild official agreement reporting after an independent completed packet is available. |
| external_agent_evidence | no | `not_ready_no_external_agents` | Register and run at least one non-author external agent configuration through the pilot harness.; Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset. |
| methodology_calibration_review | yes | `ready` | - |
| release_tag_and_archive | no | `not_ready_unfrozen` | Create a release tag and archive the release artifact bundle after the remaining gates pass. |

## Blocking Items

- Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.
- Rebuild official agreement reporting after an independent completed packet is available.
- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
- Create a release tag and archive the release artifact bundle after the remaining gates pass.
