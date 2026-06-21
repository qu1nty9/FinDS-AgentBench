# synthetic_market_direction_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | synthetic_market_direction_v0 |
| Title | Synthetic Market Next-Day Direction Prediction |
| Track | predictive_financial_ml |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | synthetic, market_panel, classification, temporal_validation |
| Source Spec | tasks/pilot/synthetic_market_direction_v0.yaml |
| Data Access | synthetic_generator |
| License Status | usable |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict next-day return direction in a synthetic market panel using point-in-time features.

**Research Question**: Can an agent build a leakage-safe direction model that beats a simple momentum baseline on a private temporal holdout?

**Instructions**: Build a model that predicts whether each synthetic asset has a positive next-day return. Use the train and public validation rows for development, submit predictions for the private temporal holdout, compare against simple baselines, and write a short research report.



**Prohibited Shortcuts**

- Do not use private holdout labels.
- Do not infer labels from private answer-key files.
- Do not use random splits for model selection.

## Data

**Local Paths**: data/raw/synthetic_market_direction_v0/

**Generator/Download Script**: scripts/generate_synthetic_market_direction_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| Project-generated synthetic market panel | project_generated | synthetic_generator | generated locally |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| row_id | Unique date-asset row id. | Known at prediction timestamp. |
| date | Observation date. | Known at prediction timestamp. |
| asset_id | Synthetic asset identifier. | Known at prediction timestamp. |
| ret_1d | One-day return through day t. | Known after close on day t. |
| ret_5d | Five-day cumulative return through day t. | Known after close on day t. |
| momentum_20d | Twenty-day cumulative return through day t. | Known after close on day t. |
| volatility_10d | Ten-day trailing return volatility through day t. | Known after close on day t. |
| market_regime_proxy | Synthetic regime indicator known at day t. | Known at prediction timestamp. |
| next_day_positive_return | Binary target; hidden for private holdout. | Known after day t+1 close. |

## Information Set

**Prediction Timestamp**: After close on day t, before day t+1 return is known.


**Allowed Information**

- Features in `train_public.csv` for train and public validation rows.
- Features in `private_holdout_features.csv` for private holdout rows.
- Labels only for train and public validation rows.


**Forbidden Information**

- Private holdout labels.
- next_day_return for private holdout rows.
- Any feature computed from day t+1 return.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Day t trailing features | After close on day t. | Day t+1 direction prediction. |
| Day t+1 return | After close on day t+1. | Not usable for day t+1 prediction. |


**Timestamp Alignment Rules**

- All features use returns through day t only.
- The target is aligned to the next business day.

## Target

| Field | Value |
| --- | --- |
| Name | next_day_positive_return |
| Definition | Binary label equal to 1 when next-day synthetic return is positive. |
| Horizon | 1 business day |
| Label Construction | Compute next-day return from the synthetic return process and align it to features known at day t. |
| Positive Class | positive next-day return |
| Ranking Group | asset_id |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One business day target horizon.



| Split | Start | End |
| --- | --- | --- |
| train | 2019-01-30 | 2020-12-31 |
| public_validation | 2021-01-01 | 2021-06-30 |
| private_temporal_holdout | 2021-07-01 | 2021-11-29 |
| stress_test:post_validation_holdout | 2021-07-01 | 2021-11-29 |

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
| Random Seed Policy | Generator and models must use fixed seeds. |
| Rerun Command | python scripts/generate_synthetic_market_direction_v0.py --seed 11 |
| Expected Runtime Limit | 30 minutes |
| CPU Limit | local_cpu |
| Memory Limit | 4GB |


**Artifact Retention**

- final notebook
- predictions
- writeup
- execution log


**Trace Requirements**

- Store commands and code execution errors.
- Store final selected features and validation protocol.
