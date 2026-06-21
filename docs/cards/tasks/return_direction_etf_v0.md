# return_direction_etf_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | return_direction_etf_v0 |
| Title | Daily ETF Return Direction Under Point-in-Time Features |
| Track | predictive_financial_ml |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | equities, etf, classification, temporal_validation |
| Source Spec | tasks/pilot/return_direction_etf_v0.yaml |
| Data Access | download_script |
| License Status | pending_review |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict next-day ETF return direction using only features available before the prediction timestamp.

**Research Question**: Can an agent build a leakage-safe next-day ETF direction model that beats simple baselines on a private temporal holdout?

**Instructions**: Build a model that predicts whether the selected ETF has a positive next-day close-to-close return. Use only information known by the prediction timestamp, validate temporally, compare against naive baselines, and produce a notebook, predictions file, and short writeup.



**Prohibited Shortcuts**

- Do not use next-day returns or future prices as features.
- Do not tune on the private temporal holdout.
- Do not use random train/test splits.

## Data

**Local Paths**: data/raw/return_direction_etf_v0/

**Generator/Download Script**: scripts/download_return_direction_etf_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| Public ETF OHLCV source | pending_review | download_script | TBD |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| date | Trading date. | Known after market close on the same date. |
| open | Daily open price. | Known during the trading day; usable only according to prediction timestamp. |
| high | Daily high price. | Known after market close. |
| low | Daily low price. | Known after market close. |
| close | Daily close price. | Known after market close. |
| volume | Daily trading volume. | Known after market close. |

## Information Set

**Prediction Timestamp**: After market close on day t, before the return from t to t+1 is known.


**Allowed Information**

- OHLCV data through day t.
- Features computed from data through day t and shifted to predict t+1.


**Forbidden Information**

- Close price or return from day t+1 or later.
- Any label-derived feature from the prediction horizon.
- Private temporal holdout labels.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Day t OHLCV | After market close on day t. | Prediction for day t+1. |
| Day t+1 close | After market close on day t+1. | Not usable for day t+1 prediction. |


**Timestamp Alignment Rules**

- All rolling features must use observations through day t only.
- Target is sign(close[t+1] / close[t] - 1).

## Target

| Field | Value |
| --- | --- |
| Name | next_day_positive_return |
| Definition | Binary label equal to 1 when next-day close-to-close return is positive. |
| Horizon | 1 trading day |
| Label Construction | Compute return from close[t] to close[t+1], then align the label to features known at close[t]. |
| Positive Class | positive next-day return |
| Ranking Group | - |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One trading day between feature window end and target realization.



| Split | Start | End |
| --- | --- | --- |
| train | TBD | TBD |
| public_validation | TBD | TBD |
| private_temporal_holdout | TBD | TBD |
| stress_test:high_volatility_regime | TBD | TBD |

## Deliverables


**Required Files**

- notebook.ipynb
- predictions.csv
- writeup.md

| Field | Value |
| --- | --- |
| Notebook Path | notebook.ipynb |
| Notebook Must Execute Cleanly | true |
| Predictions Path | predictions.csv |
| Predictions Required Columns | row_id, prediction, probability |
| Writeup Path | writeup.md |
| Writeup Max Words | 1200 |
| Retain Agent Trace | true |

## Reproducibility and Audit

| Field | Value |
| --- | --- |
| Environment | pyproject.toml |
| Random Seed Policy | Fixed seeds required for all stochastic models. |
| Rerun Command | python scripts/validate_task.py tasks/pilot/return_direction_etf_v0.yaml |
| Expected Runtime Limit | 30 minutes |
| CPU Limit | local_cpu |
| Memory Limit | 8GB |


**Artifact Retention**

- final notebook
- predictions
- writeup
- execution log


**Trace Requirements**

- Store all commands and code execution errors.
- Store final selected features.
