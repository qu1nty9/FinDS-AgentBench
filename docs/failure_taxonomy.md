# Failure Taxonomy

FinDS-AgentBench should report failures explicitly instead of hiding them behind one score.

## code_failure

Runtime errors, missing files, invalid dependencies, notebook execution failure, invalid prediction format, or malformed outputs.

## temporal_leakage

Use of future prices, future returns, post-event data, unshifted rolling features, target-derived features, or any information unavailable at the prediction timestamp.

## invalid_validation

Random split on temporal data, cross-validation leakage, missing embargo, holdout tuning, preprocessing fit on the full dataset, or train/validation overlap.

## overfitting

Excessive tuning to public validation, unstable results across regimes, or performance that collapses under perturbation.

## weak_financial_reasoning

Ignoring transaction costs, turnover, drawdown, calibration, base rates, naive baselines, or market-regime dependence.

## unsupported_narrative

Claims in the report are stronger than the evidence: unsupported causal claims, cherry-picked metrics, missing limitations, or hallucinated explanations.

## reproducibility_failure

Missing seeds, missing dependencies, nondeterministic outputs, non-rerunnable notebooks, hidden local state, or undocumented data preprocessing.

## bad_tool_use

Misread files, corrupted data, incorrect shell/tool calls, failure to inspect generated outputs, or use of unavailable external resources.

