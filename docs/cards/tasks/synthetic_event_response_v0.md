# synthetic_event_response_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | synthetic_event_response_v0 |
| Title | Synthetic Event Response Direction Prediction |
| Track | event_aware_time_series_reasoning |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | synthetic, event_response, classification, temporal_validation |
| Source Spec | tasks/pilot/synthetic_event_response_v0.yaml |
| Data Access | synthetic_generator |
| License Status | usable |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict next-day asset reaction direction after timestamped synthetic events.

**Research Question**: Can an agent use event surprise, sentiment, importance, and pre-event market context without leaking future reactions?

**Instructions**: Build a model that predicts whether each asset has a positive next-day event reaction. Use train and public validation rows for development, submit predictions for the private temporal holdout, compare against simple event-rule baselines, and write a short research report.



**Prohibited Shortcuts**

- Do not use private holdout labels.
- Do not use next-day event reaction returns as features.
- Do not tune directly against private temporal holdout scores.
- Do not use random splits for final model selection.

## Data

**Local Paths**: data/raw/synthetic_event_response_v0/

**Generator/Download Script**: scripts/generate_synthetic_event_response_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| Project-generated synthetic event response panel | project_generated | synthetic_generator | generated locally |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| row_id | Unique date-asset event row id. | Known at prediction timestamp. |
| date | Event date. | Known at prediction timestamp. |
| asset_id | Synthetic asset identifier. | Known at prediction timestamp. |
| sector | Synthetic asset sector bucket. | Known before event timestamp. |
| event_type | Synthetic event category. | Known at event timestamp. |
| event_surprise | Signed event surprise available at event timestamp. | Known at prediction timestamp. |
| sentiment_score | Event text sentiment proxy available at event timestamp. | Known at prediction timestamp. |
| event_importance | Ex ante event importance score. | Known at prediction timestamp. |
| pre_event_momentum_5d | Five-day return momentum ending before the event reaction horizon. | Known before next-day reaction. |
| volatility_20d | Twenty-day pre-event volatility. | Known before next-day reaction. |
| sector_stress | Sector-level stress proxy known at event timestamp. | Known at prediction timestamp. |
| event_reaction_positive | Binary target; hidden for private temporal holdout. | Known after next-day event reaction. |

## Information Set

**Prediction Timestamp**: After the event is observed on day t, before the next-day reaction return is known.


**Allowed Information**

- Event metadata and event surprise available at day t.
- Sentiment and importance proxies computed at day t.
- Pre-event momentum, volatility, and sector stress through day t.
- Labels only for train and public validation rows.


**Forbidden Information**

- Private holdout labels.
- next_day_return for private holdout rows.
- Any feature computed from day t+1 event reaction.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Event surprise and sentiment | Event timestamp on day t. | Next-day event reaction prediction. |
| Pre-event market context | Through day t before next-day reaction. | Next-day event reaction prediction. |
| Day t+1 event reaction return | After day t+1 close. | Not usable for day t+1 reaction prediction. |


**Timestamp Alignment Rules**

- Pre-event rolling features must not include the next-day reaction.
- Target is aligned to the next business day after the event.

## Target

| Field | Value |
| --- | --- |
| Name | event_reaction_positive |
| Definition | Binary label equal to 1 when next-day event reaction return is positive. |
| Horizon | 1 business day |
| Label Construction | Compute next-day return after the event and align it to features known at the event timestamp. |
| Positive Class | positive next-day event reaction |
| Ranking Group | asset_id |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One business day target horizon.



| Split | Start | End |
| --- | --- | --- |
| train | 2019-01-02 | 2020-12-31 |
| public_validation | 2021-01-01 | 2021-06-30 |
| private_temporal_holdout | 2021-07-01 | 2021-11-29 |
| stress_test:high_stress_regime | 2020-03-02 | 2020-05-29 |

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
| Rerun Command | python scripts/generate_synthetic_event_response_v0.py --seed 23 |
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
