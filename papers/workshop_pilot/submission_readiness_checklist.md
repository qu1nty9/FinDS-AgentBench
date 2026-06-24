# Submission Readiness Checklist

This checklist tracks work that should be complete before treating the workshop manuscript as submission-ready.

## Already Present

- Reproducible pilot release command.
- Task cards, evaluation cards, data manifests, and release manifest.
- Reference result tables and paper-ready result exports.
- Statistical uncertainty and paired-comparison artifacts.
- Seed manual-audit rubric and adjudication workflow.
- Reviewer-readiness report that separates seed-only audit status from submission-strength agreement claims.
- External-agent protocol and readiness report that separate bundled reference agents from independent external-agent evidence.
- Unified submission-readiness gate for the workshop manuscript.
- Generated qualitative failure examples with exact task/run/artifact references.

## Required Before Submission

- Fill an independent second-reviewer packet and rebuild agreement/adjudication reports.
- Add at least one stronger external agent beyond environment-wrapped baseline selection.
- Audit the generated related-work citations, add any venue-specific neighboring benchmarks, and tighten the positioning narrative.
- Expand qualitative examples after independent second-reviewer adjudication.
- Freeze a release tag and archive the release artifact bundle.
- Compile the final LaTeX and inspect table width, appendix length, and venue formatting.

## Current Risk Flags

- Manual audit status: `seed_author_adjudication_only`.
- Reviewer readiness status: `not_ready_seed_only`.
- Completed independent reviewer packets: `0`.
- Independent agreement status: `insufficient_independent_overlap`.
- External-agent readiness status: `not_ready_no_external_agents`.
- Completed external agent configurations: `0`.
- Submission readiness status: `not_ready_for_workshop_submission`.
- Submission gates ready: `3 / 6`.
- Pilot repeated-run count is small; statistical claims must remain caveated.
- Bundled example agents should not be framed as a comprehensive model leaderboard.

## Manual-Audit Gate Blockers

- Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv.
- Rebuild official agreement reporting after an independent completed packet is available.

## External-Agent Gate Blockers

- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
