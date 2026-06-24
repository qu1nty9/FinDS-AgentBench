# Pilot Reference Results

Reference repeated-run result snapshot for `finds_agentbench_pilot_v0`.

## Snapshot

| Field | Value |
| --- | --- |
| Benchmark ID | finds_agentbench_pilot_v0 |
| Benchmark Version | 0.1.0 |
| Release Stage | pilot |
| Treasury Snapshot Date | 2026-06-21 |
| Baseline Summary Rows | 27 |
| Agent Summary Rows | 8 |
| Protocol Summary Rows | 35 |

All summary statistics report repeated-run mean and sample standard deviation across the configured seeds.

## Pilot Baseline Suite

Baseline-only pilot evaluation across synthetic market direction, synthetic event response, Treasury 10Y direction, 10Y-2Y and 10Y-3M curve steepening, front-end spread widening, USD broad direction, and USD AFE-versus-EME relative direction tasks.

Official command: `PYTHONPATH=src python scripts/run_pilot_baseline_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --run-label-prefix pilot`

| task_id | agent_id | run_type | run_count | completed_count | score.overall_score.mean | score.overall_score.std | score.balanced_accuracy.mean | score.balanced_accuracy.std | score.roc_auc.mean | score.roc_auc.std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| front_end_spread_widening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.508542 | 0.0134051 | 0.508542 | 0.0134051 | 0.529279 | 0.00296427 |
| front_end_spread_widening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.542971 | 0 | 0.542971 | 0 | 0.5363 | 0 |
| front_end_spread_widening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.540203 | 0 | 0.540203 | 0 | 0.540203 | 0 |
| front_end_spread_widening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.510608 | 0.00750677 | 0.510608 | 0.00750677 | 0.518086 | 0.0031868 |
| synthetic_event_response_v0 | event_rule_baseline | baseline | 3 | 3 | 0.637239 | 0.0106743 | 0.637239 | 0.0106743 | 0.690593 | 0.0182386 |
| synthetic_market_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.514442 | 0.0160653 | 0.514442 | 0.0160653 | 0.527834 | 0.0279151 |
| synthetic_market_direction_v0 | momentum_baseline | baseline | 3 | 3 | 0.521015 | 0.018434 | 0.521015 | 0.018434 | 0.517726 | 0.0235361 |
| usd_afe_vs_eme_relative_direction_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.528971 | 0.00245043 | 0.528971 | 0.00245043 | 0.540997 | 0.00178546 |
| usd_afe_vs_eme_relative_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.542018 | 0 |
| usd_afe_vs_eme_relative_direction_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.510781 | 0 | 0.510781 | 0 | 0.510781 | 0 |
| usd_afe_vs_eme_relative_direction_v0 | random_forest_baseline | baseline | 3 | 3 | 0.512229 | 0.0125427 | 0.512229 | 0.0125427 | 0.532164 | 0.00230507 |
| usd_broad_direction_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.4998 | 0.00255277 | 0.4998 | 0.00255277 | 0.489566 | 0.00695741 |
| usd_broad_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.506758 | 0 | 0.506758 | 0 | 0.494513 | 0 |
| usd_broad_direction_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.509505 | 0 | 0.509505 | 0 | 0.509505 | 0 |
| usd_broad_direction_v0 | random_forest_baseline | baseline | 3 | 3 | 0.500098 | 0.00597319 | 0.500098 | 0.00597319 | 0.506084 | 0.00590458 |
| yield_curve_10y2y_steepening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.500768 | 0.00370569 | 0.500768 | 0.00370569 | 0.522073 | 0.000221609 |
| yield_curve_10y2y_steepening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.529693 | 0 | 0.529693 | 0 | 0.557649 | 0 |
| yield_curve_10y2y_steepening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.530405 | 0 |
| yield_curve_10y2y_steepening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.497591 | 0.00350376 | 0.497591 | 0.00350376 | 0.510803 | 0.000514251 |
| yield_curve_10y3mo_steepening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.53338 | 0.0112404 | 0.53338 | 0.0112404 | 0.550471 | 0.00326014 |
| yield_curve_10y3mo_steepening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.517247 | 0 | 0.517247 | 0 | 0.526163 | 0 |
| yield_curve_10y3mo_steepening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.510978 | 0 |
| yield_curve_10y3mo_steepening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.532129 | 0.00787466 | 0.532129 | 0.00787466 | 0.540375 | 0.00577626 |
| yield_direction_treasury10y_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.506369 | 0.0077616 | 0.506369 | 0.0077616 | 0.525349 | 0.00251459 |
| yield_direction_treasury10y_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.486959 | 0 | 0.486959 | 0 | 0.485977 | 0 |
| yield_direction_treasury10y_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.493743 | 0 | 0.493743 | 0 | 0.493743 | 0 |
| yield_direction_treasury10y_v0 | random_forest_baseline | baseline | 3 | 3 | 0.503342 | 0.00858396 | 0.503342 | 0.00858396 | 0.522969 | 0.00381081 |

## Pilot Agent Suite

External-agent pilot evaluation across the implemented synthetic, rates, curve, front-end, and FX env-agent wrappers.

Official command: `PYTHONPATH=src python scripts/run_pilot_agent_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --run-label-prefix pilot_agent`

| task_id | agent_id | run_type | run_count | completed_count | score.overall_score.mean | score.overall_score.std | score.balanced_accuracy.mean | score.balanced_accuracy.std | score.roc_auc.mean | score.roc_auc.std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| front_end_spread_widening_v0 | treasury_front_end_research_sweep_env_agent | agent | 3 | 3 | 0.542971 | 0 | 0.542971 | 0 | 0.5363 | 0 |
| synthetic_event_response_v0 | event_rule_env_agent | agent | 3 | 3 | 0.637239 | 0.0106743 | 0.637239 | 0.0106743 | 0.690593 | 0.0182386 |
| synthetic_market_direction_v0 | market_research_sweep_env_agent | agent | 3 | 3 | 0.511405 | 0.0203245 | 0.511405 | 0.0203245 | 0.518167 | 0.0234117 |
| usd_afe_vs_eme_relative_direction_v0 | usd_research_sweep_env_agent | agent | 3 | 3 | 0.50683 | 0.00684276 | 0.50683 | 0.00684276 | 0.517023 | 0.0108115 |
| usd_broad_direction_v0 | usd_research_sweep_env_agent | agent | 3 | 3 | 0.501737 | 0.00536385 | 0.501737 | 0.00536385 | 0.497256 | 0.0147307 |
| yield_curve_10y2y_steepening_v0 | treasury_curve_research_sweep_env_agent | agent | 3 | 3 | 0.500768 | 0.00370569 | 0.500768 | 0.00370569 | 0.522073 | 0.000221609 |
| yield_curve_10y3mo_steepening_v0 | treasury_curve_10y3mo_research_sweep_env_agent | agent | 3 | 3 | 0.517247 | 0 | 0.517247 | 0 | 0.526163 | 0 |
| yield_direction_treasury10y_v0 | treasury_research_sweep_env_agent | agent | 3 | 3 | 0.504146 | 0.00394689 | 0.504146 | 0.00394689 | 0.526971 | 0.000295832 |

## Combined Pilot Protocol

End-to-end combined benchmark snapshot including both baseline and external-agent runs under the same repeated-run protocol across the full pilot task set.

Official command: `PYTHONPATH=src python scripts/run_pilot_protocol.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --run-label-prefix pilot_protocol`

| task_id | agent_id | run_type | run_count | completed_count | score.overall_score.mean | score.overall_score.std | score.balanced_accuracy.mean | score.balanced_accuracy.std | score.roc_auc.mean | score.roc_auc.std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| front_end_spread_widening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.508542 | 0.0134051 | 0.508542 | 0.0134051 | 0.529279 | 0.00296427 |
| front_end_spread_widening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.542971 | 0 | 0.542971 | 0 | 0.5363 | 0 |
| front_end_spread_widening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.540203 | 0 | 0.540203 | 0 | 0.540203 | 0 |
| front_end_spread_widening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.510608 | 0.00750677 | 0.510608 | 0.00750677 | 0.518086 | 0.0031868 |
| front_end_spread_widening_v0 | treasury_front_end_research_sweep_env_agent | agent | 3 | 3 | 0.542971 | 0 | 0.542971 | 0 | 0.5363 | 0 |
| synthetic_event_response_v0 | event_rule_baseline | baseline | 3 | 3 | 0.637239 | 0.0106743 | 0.637239 | 0.0106743 | 0.690593 | 0.0182386 |
| synthetic_event_response_v0 | event_rule_env_agent | agent | 3 | 3 | 0.637239 | 0.0106743 | 0.637239 | 0.0106743 | 0.690593 | 0.0182386 |
| synthetic_market_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.514442 | 0.0160653 | 0.514442 | 0.0160653 | 0.527834 | 0.0279151 |
| synthetic_market_direction_v0 | momentum_baseline | baseline | 3 | 3 | 0.521015 | 0.018434 | 0.521015 | 0.018434 | 0.517726 | 0.0235361 |
| synthetic_market_direction_v0 | market_research_sweep_env_agent | agent | 3 | 3 | 0.511405 | 0.0203245 | 0.511405 | 0.0203245 | 0.518167 | 0.0234117 |
| usd_afe_vs_eme_relative_direction_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.528971 | 0.00245043 | 0.528971 | 0.00245043 | 0.540997 | 0.00178546 |
| usd_afe_vs_eme_relative_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.542018 | 0 |
| usd_afe_vs_eme_relative_direction_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.510781 | 0 | 0.510781 | 0 | 0.510781 | 0 |
| usd_afe_vs_eme_relative_direction_v0 | random_forest_baseline | baseline | 3 | 3 | 0.512229 | 0.0125427 | 0.512229 | 0.0125427 | 0.532164 | 0.00230507 |
| usd_afe_vs_eme_relative_direction_v0 | usd_research_sweep_env_agent | agent | 3 | 3 | 0.50683 | 0.00684276 | 0.50683 | 0.00684276 | 0.517023 | 0.0108115 |
| usd_broad_direction_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.4998 | 0.00255277 | 0.4998 | 0.00255277 | 0.489566 | 0.00695741 |
| usd_broad_direction_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.506758 | 0 | 0.506758 | 0 | 0.494513 | 0 |
| usd_broad_direction_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.509505 | 0 | 0.509505 | 0 | 0.509505 | 0 |
| usd_broad_direction_v0 | random_forest_baseline | baseline | 3 | 3 | 0.500098 | 0.00597319 | 0.500098 | 0.00597319 | 0.506084 | 0.00590458 |
| usd_broad_direction_v0 | usd_research_sweep_env_agent | agent | 3 | 3 | 0.501737 | 0.00536385 | 0.501737 | 0.00536385 | 0.497256 | 0.0147307 |
| yield_curve_10y2y_steepening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.500768 | 0.00370569 | 0.500768 | 0.00370569 | 0.522073 | 0.000221609 |
| yield_curve_10y2y_steepening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.529693 | 0 | 0.529693 | 0 | 0.557649 | 0 |
| yield_curve_10y2y_steepening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.530405 | 0 |
| yield_curve_10y2y_steepening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.497591 | 0.00350376 | 0.497591 | 0.00350376 | 0.510803 | 0.000514251 |
| yield_curve_10y2y_steepening_v0 | treasury_curve_research_sweep_env_agent | agent | 3 | 3 | 0.500768 | 0.00370569 | 0.500768 | 0.00370569 | 0.522073 | 0.000221609 |
| yield_curve_10y3mo_steepening_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.53338 | 0.0112404 | 0.53338 | 0.0112404 | 0.550471 | 0.00326014 |
| yield_curve_10y3mo_steepening_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.517247 | 0 | 0.517247 | 0 | 0.526163 | 0 |
| yield_curve_10y3mo_steepening_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.5 | 0 | 0.5 | 0 | 0.510978 | 0 |
| yield_curve_10y3mo_steepening_v0 | random_forest_baseline | baseline | 3 | 3 | 0.532129 | 0.00787466 | 0.532129 | 0.00787466 | 0.540375 | 0.00577626 |
| yield_curve_10y3mo_steepening_v0 | treasury_curve_10y3mo_research_sweep_env_agent | agent | 3 | 3 | 0.517247 | 0 | 0.517247 | 0 | 0.526163 | 0 |
| yield_direction_treasury10y_v0 | extra_trees_baseline | baseline | 3 | 3 | 0.506369 | 0.0077616 | 0.506369 | 0.0077616 | 0.525349 | 0.00251459 |
| yield_direction_treasury10y_v0 | logistic_regression_baseline | baseline | 3 | 3 | 0.486959 | 0 | 0.486959 | 0 | 0.485977 | 0 |
| yield_direction_treasury10y_v0 | previous_day_direction_baseline | baseline | 3 | 3 | 0.493743 | 0 | 0.493743 | 0 | 0.493743 | 0 |
| yield_direction_treasury10y_v0 | random_forest_baseline | baseline | 3 | 3 | 0.503342 | 0.00858396 | 0.503342 | 0.00858396 | 0.522969 | 0.00381081 |
| yield_direction_treasury10y_v0 | treasury_research_sweep_env_agent | agent | 3 | 3 | 0.504146 | 0.00394689 | 0.504146 | 0.00394689 | 0.526971 | 0.000295832 |
