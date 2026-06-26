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
| `formatting_check.md` | Static LaTeX readiness and PDF-risk report. |
| `formatting_check.json` | Machine-readable static formatting report. |
| `submission_readiness_checklist.md` | Remaining work before a credible arXiv/workshop submission. |
| `submission_package_manifest.md` | Submission-level wrapper over manuscript files, release artifacts, claim boundaries, and archive checksums. |
| `submission_package_manifest.json` | Machine-readable submission package manifest. |
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
| Reviewer Readiness | ready_for_submission_claims |
| External Agent Readiness | not_ready_no_external_agents |
| Submission Readiness | not_ready_for_workshop_submission |
| Formatting Check | static_checks_passed_pdf_compile_pending |

## Build

The manuscript is generated from release artifacts:

```bash
PYTHONPATH=src python scripts/build_pilot_manuscript.py
```

Check static LaTeX readiness and PDF-risk warnings:

```bash
PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py
```

Build the submission package manifest:

```bash
PYTHONPATH=src python scripts/build_submission_package_manifest.py
```

The generated `main.tex` inputs LaTeX tables from `docs/releases/pilot_v0/` rather than copying them, so table updates remain traceable to the release pipeline.
