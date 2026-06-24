# usd_broad_direction_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | usd_broad_direction_v0 |
| Title | Broad U.S. Dollar Index Next-Day Direction Under Point-in-Time H.10 and H.15 Features |
| Track | predictive_financial_ml |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | fx, macro_finance, dollar, classification, temporal_validation |
| Source Spec | tasks/pilot/usd_broad_direction_v0.yaml |
| Data Access | download_script |
| License Status | public_domain_citation_requested |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict whether the broad nominal U.S. dollar index will rise on the next business day using only point-in-time Board of Governors H.10 FX index observations and same-day H.15 rates information available by the prediction timestamp.

**Research Question**: Can an agent build a leakage-safe next-day dollar direction model that improves on simple chronological baselines on a private temporal holdout?

**Instructions**: Build a model that predicts whether the broad nominal U.S. dollar index rises on the next business day. Use only information available by the end of day t from the Board of Governors H.10 dollar indexes and same-day H.15 rates context, validate temporally, compare against naive chronological baselines, and produce a notebook, predictions file, and short writeup.



**Prohibited Shortcuts**

- Do not use next-day dollar index levels or next-day returns as features.
- Do not tune on the private temporal holdout.
- Do not use random train/test splits or full-sample preprocessing.

## Data

**Local Paths**: data/raw/usd_broad_direction_v0/

**Generator/Download Script**: scripts/download_usd_broad_direction_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| DTWEXBGS from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DTWEXBGS&vintage_date=2026-06-21 |
| DTWEXAFEGS from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DTWEXAFEGS&vintage_date=2026-06-21 |
| DTWEXEMEGS from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DTWEXEMEGS&vintage_date=2026-06-21 |
| DGS2 from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS2&vintage_date=2026-06-21 |
| DGS10 from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10&vintage_date=2026-06-21 |
| DFF from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DFF&vintage_date=2026-06-21 |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| date | Observation date for the end-of-day prediction timestamp. | Known after the daily H.10 and H.15 observations are published for day t. |
| asset_id | Fixed benchmark asset identifier for the broad nominal U.S. dollar index. | Static metadata. |
| split | Chronological split assignment. | Static benchmark metadata. |
| usd_broad_level | Broad nominal U.S. dollar index level. | Known by prediction time on day t. |
| usd_afe_level | Nominal U.S. dollar index against advanced foreign economies. | Known by prediction time on day t. |
| usd_eme_level | Nominal U.S. dollar index against emerging market economies. | Known by prediction time on day t. |
| dgs2_level | 2-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dgs10_level | 10-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dff_level | Effective federal funds rate in percent. | Known by prediction time on day t. |
| usd_broad_return_1d | One-day simple return of the broad dollar index. | Computed from observations through day t only. |
| usd_broad_return_5d | Five-day simple return of the broad dollar index. | Computed from observations through day t only. |
| usd_afe_return_1d | One-day simple return of the advanced-foreign-economies dollar index. | Computed from observations through day t only. |
| usd_eme_return_1d | One-day simple return of the emerging-markets dollar index. | Computed from observations through day t only. |
| usd_afe_minus_eme | Level spread between the advanced-foreign-economies and emerging-markets dollar indexes. | Computed from day t observations only. |
| usd_broad_minus_20d_mean | Broad dollar index minus its 20-day rolling mean. | Computed from observations through day t only. |
| usd_broad_vol_5d | Rolling 5-day standard deviation of one-day broad-dollar returns. | Computed from observations through day t only. |
| usd_broad_vol_20d | Rolling 20-day standard deviation of one-day broad-dollar returns. | Computed from observations through day t only. |
| term_spread_10y_2y | 10-year minus 2-year Treasury slope. | Computed from day t observations only. |
| front_end_spread | 2-year Treasury minus effective fed funds rate. | Computed from day t observations only. |
| next_day_return | Next business-day simple return of the broad nominal U.S. dollar index. | Known only after day t+1 is observed; available in public train/validation labels and private answer key only. |

## Information Set

**Prediction Timestamp**: After day t H.10 and H.15 observations are available, before the next business-day broad dollar move is known.


**Allowed Information**

- H.10 broad, advanced-foreign-economies, and emerging-markets dollar index observations through day t only.
- H.15 rates observations through day t only.
- Lagged and rolling features computed from observations through day t only.
- Public benchmark metadata and split definitions.


**Forbidden Information**

- Day t+1 or later broad dollar index levels or returns.
- Any feature derived from next_day_usd_broad_up or next_day_return.
- Private temporal holdout labels.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Day t H.10 dollar indexes | After the day t release is published. | Prediction for the next business day. |
| Day t H.15 rates context | After the day t release is published. | Prediction for the next business day. |
| Day t+1 broad dollar move | After the next business-day release is published. | Not usable for the day t to t+1 prediction. |


**Timestamp Alignment Rules**

- All lagged and rolling features must use observations through day t only.
- Target is sign(DTWEXBGS[t+1] / DTWEXBGS[t] - 1) over the next observed business day.

## Target

| Field | Value |
| --- | --- |
| Name | next_day_usd_broad_up |
| Definition | Binary label equal to 1 when the broad nominal U.S. dollar index increases on the next business day. |
| Horizon | 1 business day |
| Label Construction | Compute DTWEXBGS[t+1] / DTWEXBGS[t] - 1 and map positive values to class 1. |
| Positive Class | positive next-day broad-dollar return |
| Ranking Group | - |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One business-day target horizon between feature cutoff and label realization.



| Split | Start | End |
| --- | --- | --- |
| train | 2006-01-31 | 2018-12-31 |
| public_validation | 2019-01-02 | 2021-12-30 |
| private_temporal_holdout | 2022-01-03 | 2025-12-31 |
| stress_test:usd_strength_cycle_2022_2024 | 2022-03-01 | 2024-12-31 |

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
| Rerun Command | python scripts/download_usd_broad_direction_v0.py --observation-start 2006-01-03 --observation-end 2026-01-02 --snapshot-date 2026-06-21 |
| Expected Runtime Limit | 10 minutes |
| CPU Limit | local_cpu |
| Memory Limit | 4GB |


**Artifact Retention**

- final notebook
- predictions
- writeup
- execution log


**Trace Requirements**

- Store all commands and code execution errors.
- Store final selected features and validation protocol.
