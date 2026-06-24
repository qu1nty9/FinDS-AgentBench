# External Agent Registration Validation

Validation report for non-author external-agent registration and run evidence.

## Status

| Field | Value |
| --- | --- |
| Status | `no_external_agent_registered` |
| Ready for external-agent claims | no |
| External configurations | 0 |
| Completed external configurations | 0 |
| External task coverage | 0 / 8 |
| Validation errors | 0 |
| Path errors | 0 |
| Template | agents/external_agent_registration_template.yaml |

## External Configurations

| Agent | Status | Maintainer | In Reference Results | Stronger Evidence | Tasks | Completed Runs | Run Manifests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (none) | n/a | n/a | no | no | n/a | n/a | 0 |

## Blocking Items

- No external_agent_configurations entries are registered.
- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.

## Next Actions

- Copy agents/external_agent_registration_template.yaml into an external_agent_configurations entry.
- Run the external agent through the pilot command harness for the required repeated runs.
- Record completed_runs_per_task and run_manifest_paths for every completed run.
- Re-run scripts/validate_external_agent_registry.py and rebuild release artifacts.
