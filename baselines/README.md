# Baselines

Baseline implementations should be simple, reproducible, and hard for agents to beat only by exploiting leakage.

Planned baseline classes:

- naive financial baselines;
- logistic regression and random forest;
- LightGBM/XGBoost/CatBoost where dependencies are acceptable;
- simple time-series baselines;
- portfolio baselines such as equal-weight, buy-and-hold, and volatility targeting;
- expert-written notebooks for selected flagship tasks.

Implemented runnable baselines:

- `synthetic_market_direction_v0/momentum_baseline.py`
- `synthetic_market_direction_v0/logistic_regression_baseline.py`
- `synthetic_event_response_v0/event_rule_baseline.py`
