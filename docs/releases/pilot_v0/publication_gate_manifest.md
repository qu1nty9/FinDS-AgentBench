# Publication Gate Manifest

Machine-readable gate map for the FinDS-AgentBench pilot submission package.

## Status

| Field | Value |
| --- | --- |
| Benchmark ID | finds_agentbench_pilot_v0 |
| Benchmark Version | 0.1.0 |
| Release Stage | pilot |
| Status | `blocked_on_submission_evidence_and_pdf_compile` |
| Ready for Final Submission Package | no |
| Automated Gates | 7 |
| CI-Enforced Automated Gates | 7 |
| Evidence Gates | 7 |
| Blocking Evidence Gates | 3 |
| Blocking Items | 5 |

## Automated Gates

| Gate | CI Job | CI Enforced | Blocks Publication |
| --- | --- | --- | --- |
| full_repository_lint | release-gate-tests | yes | yes |
| release_gate_regression_suite | release-gate-tests | yes | yes |
| manuscript_static_formatting | release-gate-tests | yes | yes |
| publication_gate_manifest_staleness | release-gate-tests | yes | yes |
| submission_package_manifest_staleness | release-gate-tests | yes | yes |
| release_archive_build_and_verify | release-gate-tests | yes | yes |
| pilot_release_reproducibility_smoke | pilot-release-repro-smoke | yes | yes |

## Evidence Gates

| Gate | Ready | Status | Blockers |
| --- | --- | --- | --- |
| pilot_release_scope | yes | `ready` | 0 |
| statistical_artifacts | yes | `ready` | 0 |
| manual_audit_independent_review | yes | `ready_for_submission_claims` | 0 |
| external_agent_evidence | no | `not_ready_no_external_agents` | 2 |
| methodology_calibration_review | yes | `ready` | 0 |
| release_tag_and_archive | no | `not_ready_unfrozen` | 1 |
| latex_pdf_compile_visual_inspection | no | `static_checks_passed_pdf_compile_pending` | 2 |

## Blocking Items

- Register and run at least one non-author external agent configuration through the pilot harness.
- Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset.
- Create a release tag and archive the release artifact bundle after the remaining gates pass.
- Run a real LaTeX engine and inspect the generated PDF before final submission.
- Install latexmk, tectonic, pdflatex, xelatex, or lualatex for PDF compilation.

## Command Catalog

### full_repository_lint

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
python -m ruff check .
```

### release_gate_regression_suite

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python -m pytest tests/test_curve_10y3mo_and_scoring.py tests/test_pipelines.py tests/test_benchmark_manifest.py tests/test_task_cards.py tests/test_manual_audit.py tests/test_external_agents.py tests/test_pilot_release.py tests/test_release_archive.py tests/test_reference_results.py tests/test_paper_artifacts.py tests/test_release_reproducibility.py tests/test_submission_readiness.py tests/test_manuscript_formatting.py tests/test_submission_package.py tests/test_publication_gate.py -q
```

### manuscript_static_formatting

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py
```

### publication_gate_manifest_staleness

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check
```

### submission_package_manifest_staleness

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python scripts/build_submission_package_manifest.py --check
```

### release_archive_build_and_verify

- CI job: `release-gate-tests`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python scripts/build_release_archive.py --output-dir tmp/ci_release_archives --manifest-json tmp/ci_release_archive_manifest.json --manifest-markdown tmp/ci_release_archive_manifest.md && PYTHONPATH=src python scripts/verify_release_archive.py --archive-manifest tmp/ci_release_archive_manifest.json
```

### pilot_release_reproducibility_smoke

- CI job: `pilot-release-repro-smoke`
- Status: `defined_in_ci`

```bash
PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py --work-root tmp/pilot_release_repro_check --repeat 1 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21
```

## Recommended Completion Order

1. Run CI-backed automated gates on every publication-facing change.
2. Inspect the official manual-audit agreement and adjudication queue before strengthening qualitative claims.
3. Register and run at least one non-author external agent configuration.
4. Compile and inspect the manuscript PDF with a real LaTeX engine.
5. Rebuild and verify the deterministic release archive.
6. Freeze the final release tag after all evidence gates pass.
