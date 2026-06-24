# Workshop Pilot Manuscript

Generated manuscript scaffold for the FinDS-AgentBench arXiv/workshop pilot paper.

## Files

| File | Purpose |
| --- | --- |
| `main.tex` | Main LaTeX manuscript scaffold with release-artifact inputs. |
| `related_work.tex` | Generated related-work positioning section. |
| `references.bib` | Generated BibTeX scaffold for adjacent benchmark citations. |
| `audit_failure_examples.tex` | Generated qualitative examples from the seed manual-audit subset. |
| `audit_failure_examples.md` | Markdown copy of the generated qualitative examples. |
| `audit_failure_examples.json` | Machine-readable selected qualitative examples. |
| `submission_readiness_checklist.md` | Remaining work before a credible arXiv/workshop submission. |
| `metadata.json` | Machine-readable manuscript summary derived from release artifacts. |

## Snapshot

| Field | Value |
| --- | ---: |
| Tasks | 9 |
| Runnable Tasks | 9 |
| Protocol Tasks | 8 |
| Protocol Task-System Cells | 35 |
| Overall Agent Higher Cases | 0 |
| Overall Baseline Higher Cases | 6 |
| Overall Tie Cases | 2 |
| Reviewer Readiness | not_ready_seed_only |
| External Agent Readiness | not_ready_no_external_agents |
| Submission Readiness | not_ready_for_workshop_submission |

## Build

The manuscript is generated from release artifacts:

```bash
PYTHONPATH=src python scripts/build_pilot_manuscript.py
```

The generated `main.tex` inputs LaTeX tables from `docs/releases/pilot_v0/` rather than copying them, so table updates remain traceable to the release pipeline.
