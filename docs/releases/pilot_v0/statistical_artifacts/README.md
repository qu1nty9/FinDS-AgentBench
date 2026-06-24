# Statistical Artifacts

Pilot uncertainty and paired-comparison exports generated from the combined protocol run results.

## Source

- Protocol run results: `reports/release_runs/pilot_protocol_run_results.csv`
- Metrics: `score.overall_score`, `score.balanced_accuracy`, `score.roc_auc`

## Files

| File | Description |
| --- | --- |
| `summary_uncertainty.csv` | Tidy per-task, per-agent, per-metric mean, sample standard deviation, standard error, and 95% confidence interval. |
| `summary_uncertainty.json` | Machine-readable copy of the uncertainty rows with method metadata. |
| `summary_uncertainty.md` | Markdown table for review and paper drafting. |
| `agent_vs_best_baseline.csv` | Paired agent-minus-best-baseline comparisons by task and metric. |
| `agent_vs_best_baseline.json` | Machine-readable copy of the paired comparison rows with method metadata. |
| `agent_vs_best_baseline.md` | Markdown table for review and paper drafting. |
| `tables/summary_uncertainty_overall_score.tex` | Paper-ready LaTeX table for repeated-run overall-score uncertainty. |
| `tables/agent_vs_best_baseline_overall_score.tex` | Paper-ready LaTeX table for paired overall-score agent-vs-baseline comparisons. |
| `methods/statistical_methods.md` | Manuscript-ready statistical reporting text in Markdown. |
| `methods/statistical_methods.tex` | Manuscript-ready statistical reporting text in LaTeX. |

## Method

- Only rows with `status=completed` and numeric metric values are included.
- Uncertainty intervals are `mean +/- t_0.975,df * SE`; single-run groups have zero-width intervals.
- The best baseline is selected separately for each task and metric by completed-run mean, with higher values treated as better.
- Paired comparisons match runs by `trace.repeat_index`; `trace.seed` is used only when `trace.repeat_index` is unavailable.
- The sign-test p-value is exact, two-sided, and ignores zero differences.

## Pilot Caveat

The pilot release uses a small repeated-run count. These artifacts provide transparent uncertainty reporting and regression checks; they should not be read as definitive significance claims.

## Row Counts

| Artifact | Rows |
| --- | ---: |
| Summary uncertainty | 105 |
| Agent vs. best baseline | 24 |
