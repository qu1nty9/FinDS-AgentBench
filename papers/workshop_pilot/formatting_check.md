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
| Hard errors | 0 |
| Warnings | 6 |

## Hard Errors

- None.

## Warnings

- `wide_table_candidate`: `tab:related-work-positioning` in `papers/workshop_pilot/related_work.tex` has 4 columns and max row length 394.
- `wide_table_candidate`: `tab:pilot-agent-vs-best-baseline-score-overall-score` in `docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex` has 8 columns and max row length 109.
- `long_table_candidate`: `tab:pilot-uncertainty-score-overall-score` in `docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex` has 36 rows.
- `wide_table_candidate`: `tab:pilot-protocol` in `docs/releases/pilot_v0/paper_artifacts/tables/pilot_protocol.tex` has 7 columns and max row length 124.
- `long_table_candidate`: `tab:pilot-protocol` in `docs/releases/pilot_v0/paper_artifacts/tables/pilot_protocol.tex` has 31 rows.
- `latex_engine_unavailable`: Install latexmk, tectonic, pdflatex, xelatex, or lualatex before PDF compilation.

## Table Inventory

| Path | Label | Columns | Rows | Max Row Length |
| --- | --- | ---: | ---: | ---: |
| `papers/workshop_pilot/related_work.tex` | `tab:related-work-positioning` | 4 | 17 | 394 |
| `docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex` | `tab:pilot-agent-vs-best-baseline-score-overall-score` | 8 | 9 | 109 |
| `docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex` | `tab:pilot-uncertainty-score-overall-score` | 6 | 36 | 95 |
| `docs/releases/pilot_v0/paper_artifacts/tables/pilot_protocol.tex` | `tab:pilot-protocol` | 7 | 31 | 124 |

## Next Actions

- Run a real LaTeX engine and inspect the generated PDF before final submission.
- Inspect wide-table candidates in the compiled PDF and resize or split if needed.
- Inspect long appendix tables and move them to appendix or supplementary material if needed.
- Install latexmk, tectonic, pdflatex, xelatex, or lualatex for PDF compilation.
