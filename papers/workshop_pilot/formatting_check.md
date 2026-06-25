# Manuscript Formatting Check

Static LaTeX readiness report for the workshop manuscript scaffold.

## Summary

| Field | Value |
| --- | --- |
| Status | `static_checks_passed_pdf_compile_pending` |
| Main TeX | `papers/workshop_pilot/main.tex` |
| Static formatting claims ready | yes |
| PDF formatting claims ready | no |
| PDF compile status | `not_run_no_latex_engine` |
| LaTeX engine | `unavailable` |
| TeX files checked | 7 |
| Bibliographies checked | 1 |
| Citations | 16 |
| Bib entries | 16 |
| Tables | 4 |
| Tables with placement/width mitigation | 2 |
| Hard errors | 0 |
| Warnings | 1 |

## Hard Errors

- None.

## Warnings

- `latex_engine_unavailable`: Install latexmk, tectonic, pdflatex, xelatex, or lualatex before PDF compilation.

## Table Inventory

| Path | Label | Columns | Rows | Max Row Length | Placement | Width Mitigation |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `papers/workshop_pilot/related_work.tex` | `tab:related-work-positioning` | 3 | 17 | 184 | main |  |
| `docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex` | `tab:pilot-agent-vs-best-baseline-score-overall-score` | 6 | 9 | 109 | main |  |
| `docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex` | `tab:pilot-uncertainty-score-overall-score` | 6 | 36 | 95 | appendix |  |
| `docs/releases/pilot_v0/paper_artifacts/tables/pilot_protocol.tex` | `tab:pilot-protocol` | 7 | 36 | 124 | appendix | resizebox |

## Next Actions

- Run a real LaTeX engine and inspect the generated PDF before final submission.
- Install latexmk, tectonic, pdflatex, xelatex, or lualatex for PDF compilation.
