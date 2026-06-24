# Statistical Methods Snippet

The pilot release reports repeated-run uncertainty directly from the combined protocol run table.
The source table is `reports/release_runs/pilot_protocol_run_results.csv`, and the reported metrics are `score.overall_score`, `score.balanced_accuracy`, `score.roc_auc`.

For each task, system, run type, and metric, we retain completed runs with numeric metric values and report the sample mean, sample standard deviation, standard error, and a two-sided 95% t-interval. Single-run groups are reported with zero-width intervals rather than extrapolated uncertainty.

For agent-vs-baseline comparisons, the best baseline is selected independently for each task and metric using the completed-run mean. Agent and baseline runs are then paired by `trace.repeat_index`, falling back to `trace.seed` only when no repeat index is available. We report the paired agent-minus-baseline mean difference, its t-interval, and an exact two-sided sign-test p-value after dropping zero differences.

Because the pilot uses a small repeated-run count, these statistics are treated as transparent uncertainty and regression artifacts rather than definitive significance claims.
