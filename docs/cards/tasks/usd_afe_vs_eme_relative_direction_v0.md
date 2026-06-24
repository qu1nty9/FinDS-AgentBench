# usd_afe_vs_eme_relative_direction_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | usd_afe_vs_eme_relative_direction_v0 |
| Title | U.S. Dollar AFE vs EME Next-Day Relative Direction Under Point-in-Time H.10 and H.15 Features |
| Track | predictive_financial_ml |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | fx, macro_finance, dollar, relative_value, classification, temporal_validation |
| Source Spec | tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml |
| Data Access | download_script |
| License Status | public_domain_citation_requested |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict whether the advanced-foreign-economies U.S. dollar index will outperform the emerging-markets U.S. dollar index on the next business day using only point-in-time H.10 FX observations and same-day H.15 rates context.

**Research Question**: Can an agent build a leakage-safe next-day AFE-versus-EME relative-direction model that improves on simple chronological baselines on a private temporal holdout?

**Instructions**: Build a model that predicts whether the advanced-foreign-economies U.S. dollar index outperforms the emerging-markets U.S. dollar index on the next business day. Use only information available by the end of day t from the Board of Governors H.10 dollar indexes and same-day H.15 rates context, validate temporally, compare against naive chronological baselines, and produce a notebook, predictions file, and short writeup.



**Prohibited Shortcuts**

- Do not use next-day AFE, EME, or relative returns as features.
- Do not tune on the private temporal holdout.
- Do not use random train/test splits or full-sample preprocessing.

## Data

**Local Paths**: data/raw/usd_afe_vs_eme_relative_direction_v0/

**Generator/Download Script**: scripts/download_usd_afe_vs_eme_relative_direction_v0.py


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
| asset_id | Fixed benchmark asset identifier for the AFE-versus-EME relative-direction task. | Static metadata. |
| split | Chronological split assignment. | Static benchmark metadata. |
| usd_broad_level | Broad nominal U.S. dollar index level. | Known by prediction time on day t. |
| usd_afe_level | Nominal U.S. dollar index against advanced foreign economies. | Known by prediction time on day t. |
| usd_eme_level | Nominal U.S. dollar index against emerging market economies. | Known by prediction time on day t. |
| dgs2_level | 2-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dgs10_level | 10-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dff_level | Effective federal funds rate in percent. | Known by prediction time on day t. |
| usd_broad_return_1d | One-day simple return of the broad dollar index. | Computed from observations through day t only. |
| usd_broad_return_5d | Five-day simple return of the broad dollar index. | Computed from observations through day t only. |
| usd_afe_return_1d | One-day simple return of the AFE dollar index. | Computed from observations through day t only. |
| usd_afe_return_5d | Five-day simple return of the AFE dollar index. | Computed from observations through day t only. |
| usd_eme_return_1d | One-day simple return of the EME dollar index. | Computed from observations through day t only. |
| usd_eme_return_5d | Five-day simple return of the EME dollar index. | Computed from observations through day t only. |
| afe_eme_relative_return_1d | One-day AFE return minus one-day EME return. | Computed from observations through day t only. |
| afe_eme_relative_return_5d | Five-day AFE return minus five-day EME return. | Computed from observations through day t only. |
| usd_afe_minus_eme | Level spread between the AFE and EME dollar indexes. | Computed from day t observations only. |
| usd_afe_to_eme_ratio | Ratio of the AFE dollar index to the EME dollar index. | Computed from day t observations only. |
| afe_eme_relative_vol_5d | Rolling 5-day standard deviation of one-day AFE-minus-EME relative returns. | Computed from observations through day t only. |
| afe_eme_relative_vol_20d | Rolling 20-day standard deviation of one-day AFE-minus-EME relative returns. | Computed from observations through day t only. |
| term_spread_10y_2y | 10-year minus 2-year Treasury slope. | Computed from day t observations only. |
| front_end_spread | 2-year Treasury minus effective fed funds rate. | Computed from day t observations only. |
| next_day_relative_return | Next business-day AFE return minus next business-day EME return. | Known only after day t+1 is observed; available in public train/validation labels and the private answer key only. |

## Information Set

**Prediction Timestamp**: After day t H.10 and H.15 observations are available, before the next business-day AFE-versus-EME relative move is known.


**Allowed Information**

- H.10 broad, advanced-foreign-economies, and emerging-markets dollar index observations through day t only.
- H.15 rates observations through day t only.
- Lagged and rolling features computed from observations through day t only.
- Public benchmark metadata and split definitions.


**Forbidden Information**

- Day t+1 or later AFE, EME, or relative returns.
- Any feature derived from next_day_afe_outperforms_eme or next_day_relative_return.
- Private temporal holdout labels.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Day t H.10 dollar indexes | After the day t release is published. | Prediction for the next business day. |
| Day t H.15 rates context | After the day t release is published. | Prediction for the next business day. |
| Day t+1 AFE-versus-EME relative move | After the next business-day release is published. | Not usable for the day t to t+1 prediction. |


**Timestamp Alignment Rules**

- All lagged and rolling features must use observations through day t only.
- Target is sign((DTWEXAFEGS[t+1] / DTWEXAFEGS[t] - 1) - (DTWEXEMEGS[t+1] / DTWEXEMEGS[t] - 1)).

## Target

| Field | Value |
| --- | --- |
| Name | next_day_afe_outperforms_eme |
| Definition | Binary label equal to 1 when the AFE dollar index return exceeds the EME dollar index return on the next business day. |
| Horizon | 1 business day |
| Label Construction | Compute next-day AFE and EME simple returns and map positive AFE-minus-EME values to class 1. |
| Positive Class | AFE next-day return exceeds EME next-day return |
| Ranking Group | - |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One business-day target horizon between feature cutoff and label realization.



| Split | Start | End |
| --- | --- | --- |
| train | 2006-01-31 | 2018-12-31 |
| public_validation | 2019-01-02 | 2021-12-30 |
| private_temporal_holdout | 2022-01-03 | 2025-12-31 |
| stress_test:usd_relative_regime_shift_2022_2024 | 2022-03-01 | 2024-12-31 |

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
| Rerun Command | python scripts/download_usd_afe_vs_eme_relative_direction_v0.py --observation-start 2006-01-03 --observation-end 2026-01-02 --snapshot-date 2026-06-21 |
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
