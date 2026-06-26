# Submission Readiness Checklist

This checklist tracks work that should be complete before treating the workshop manuscript as submission-ready.

## Already Present

- Reproducible pilot release command.
- Task cards, evaluation cards, data manifests, and release manifest.
- Reference result tables and paper-ready result exports.
- Statistical uncertainty and paired-comparison artifacts.
- Seed manual-audit rubric and adjudication workflow.
- Reviewer-readiness report that separates seed-only audit status from submission-strength agreement claims.
- Independent-reviewer handoff and packet validator for second-reviewer audit collection.
- Independent participant brief covering reviewer, external-agent, and optional reader roles.
- External-agent protocol and readiness report that separate bundled reference agents from independent external-agent evidence.
- External-agent handoff, registration template, and registry-evidence validator.
- Unified submission-readiness gate for the workshop manuscript.
- Generated qualitative failure examples with exact task/run/artifact references.
- Audited related-work matrix with corrected venue-neighbor citations and positioning notes.
- Static manuscript formatting checker covering inputs, citations, labels, table structure, and PDF-risk warnings.
- Manuscript table-layout mitigations for related-work, result, uncertainty, and protocol tables.
- Publication-gate manifest connecting CI checks, archive verification, manuscript formatting, and external evidence blockers.
- Workshop submission-package manifest inventorying manuscript files, release artifacts, claim boundaries, archive checksums, and remaining blockers.

## Required Before Submission

- Fill an independent second-reviewer packet and rebuild agreement/adjudication reports.
- Validate the completed second-reviewer packet before using it for agreement claims.
- Add at least one stronger external agent beyond environment-wrapped baseline selection.
- Validate external-agent registry evidence before using it for external-agent claims.
- Expand qualitative examples after independent second-reviewer adjudication.
- Freeze a release tag and archive the release artifact bundle.
- Install/run a LaTeX engine, compile the final PDF, and inspect table width, appendix length, and venue formatting.

## Current Risk Flags

- Manual audit status: `seed_author_adjudication_only`.
- Reviewer readiness status: `ready_for_submission_claims`.
- Completed independent reviewer packets: `1`.
- Independent agreement status: `pairwise_agreement_available`.
- External-agent readiness status: `not_ready_no_external_agents`.
- Completed external agent configurations: `0`.
- Submission readiness status: `not_ready_for_workshop_submission`.
- Submission gates ready: `4 / 6`.
- Pilot repeated-run count is small; statistical claims must remain caveated.
- Bundled example agents should not be framed as a comprehensive model leaderboard.

## Manual-Audit Gate Blockers

- No reviewer-readiness blockers recorded.

## External-Agent Gate Blockers

- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
