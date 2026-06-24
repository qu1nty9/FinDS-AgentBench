# yield_curve_10y3mo_steepening_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | yield_curve_10y3mo_steepening_v0 |
| Title | U.S. 10Y-3M Treasury Curve Next-Day Steepening Under Point-in-Time H.15 Features |
| Track | predictive_financial_ml |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | rates, treasury, yield_curve, classification, temporal_validation |
| Source Spec | tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml |
| Data Access | download_script |
| License Status | public_domain_citation_requested |
| Primary Metric | balanced_accuracy_on_private_temporal_holdout |

## Research Prompt

**Summary**: Predict whether the U.S. 10Y-3M Treasury curve will steepen on the next business day using only point-in-time H.15 information available by the prediction timestamp.

**Research Question**: Can an agent build a leakage-safe next-day Treasury curve steepening model that improves on simple chronological baselines on a private temporal holdout?

**Instructions**: Build a model that predicts whether the 10Y-3M Treasury slope rises on the next business day. Use only information available by the end of day t from the Federal Reserve H.15 release family, validate temporally, compare against naive chronological baselines, and produce a notebook, predictions file, and short writeup.



**Prohibited Shortcuts**

- Do not use next-day yields, next-day slopes, or next-day slope changes as features.
- Do not tune on the private temporal holdout.
- Do not use random train/test splits or full-sample preprocessing.

## Data

**Local Paths**: data/raw/yield_curve_10y3mo_steepening_v0/

**Generator/Download Script**: scripts/download_yield_curve_10y3mo_steepening_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| DGS10 from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10&vintage_date=2026-06-21 |
| DGS2 from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS2&vintage_date=2026-06-21 |
| DGS3MO from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS3MO&vintage_date=2026-06-21 |
| DFF from ALFRED vintage freeze | public_domain_citation_requested | download_script | https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DFF&vintage_date=2026-06-21 |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| date | Observation date for the end-of-day prediction timestamp. | Known after the daily H.15 observation is published for day t. |
| asset_id | Fixed benchmark asset identifier for the U.S. 10Y-3M Treasury slope. | Static metadata. |
| split | Chronological split assignment. | Static benchmark metadata. |
| dgs10_level | 10-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dgs2_level | 2-year Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dgs3mo_level | 3-month Treasury constant-maturity yield in percent. | Known by prediction time on day t. |
| dff_level | Effective federal funds rate in percent. | Known by prediction time on day t. |
| curve_10y_2y | 10-year minus 2-year Treasury slope. | Computed from day t observations only. |
| curve_10y_3mo | 10-year minus 3-month Treasury slope. | Computed from day t observations only. |
| front_end_spread | 2-year Treasury minus effective fed funds rate. | Computed from day t observations only. |
| curve_10y_3mo_change_1d | One-day change in the 10Y-3M slope in percentage points. | Computed from observations through day t only. |
| curve_10y_3mo_change_5d | Five-day change in the 10Y-3M slope in percentage points. | Computed from observations through day t only. |
| curve_10y_2y_change_5d | Five-day change in the 10Y-2Y slope in percentage points. | Computed from observations through day t only. |
| dgs10_change_1d | One-day change in the 10-year yield in percentage points. | Computed from observations through day t only. |
| dgs3mo_change_1d | One-day change in the 3-month Treasury yield in percentage points. | Computed from observations through day t only. |
| front_end_spread_change_5d | Five-day change in the 2-year minus fed-funds spread in percentage points. | Computed from observations through day t only. |
| curve_10y_3mo_vol_5d | Rolling 5-day standard deviation of daily 10Y-3M slope changes. | Computed from observations through day t only. |
| curve_10y_3mo_vol_20d | Rolling 20-day standard deviation of daily 10Y-3M slope changes. | Computed from observations through day t only. |
| curve_10y_3mo_minus_20d_mean | Current 10Y-3M slope minus its 20-day rolling mean. | Computed from observations through day t only. |
| next_day_curve_10y3mo_change_bp | Next business-day change in the 10Y-3M slope, in basis points. | Known only after day t+1 is observed; available in public train/validation labels and private answer key only. |
| next_day_directional_return | Decimal-scaled directional gain used for aggregate strategy metrics, equal to next_day_curve_10y3mo_change_bp / 10000. | Known only after day t+1 is observed; available in public train/validation labels and private answer key only. |

## Information Set

**Prediction Timestamp**: After day t H.15 observations are available, before the next business-day 10Y-3M slope change is known.


**Allowed Information**

- H.15 series observations through day t only.
- Lagged and rolling features computed from observations through day t only.
- Public benchmark metadata and split definitions.


**Forbidden Information**

- Day t+1 or later Treasury yields or slopes.
- Any feature derived from next_day_curve_10y3mo_steepening, next_day_curve_10y3mo_change_bp, or next_day_directional_return.
- Private temporal holdout labels.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| Day t H.15 Treasury and fed funds observations | After the day t release is published. | Prediction for the next business day. |
| Day t+1 10Y-3M slope | After the next business-day release is published. | Not usable for the day t to t+1 prediction. |


**Timestamp Alignment Rules**

- All rolling features must use observations through day t only.
- Target is sign((DGS10[t+1] - DGS3MO[t+1]) - (DGS10[t] - DGS3MO[t])) measured in next observed business-day basis points.

## Target

| Field | Value |
| --- | --- |
| Name | next_day_curve_10y3mo_steepening |
| Definition | Binary label equal to 1 when the 10Y-3M Treasury slope increases on the next business day. |
| Horizon | 1 business day |
| Label Construction | Compute 100 * ((DGS10[t+1] - DGS3MO[t+1]) - (DGS10[t] - DGS3MO[t])) in basis points and map positive values to class 1. |
| Positive Class | positive next-day 10Y-3M slope change |
| Ranking Group | - |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One business-day target horizon between feature cutoff and label realization.



| Split | Start | End |
| --- | --- | --- |
| train | 2003-01-31 | 2018-12-31 |
| public_validation | 2019-01-02 | 2021-12-31 |
| private_temporal_holdout | 2022-01-03 | 2025-12-31 |
| stress_test:hiking_cycle_2022_2023 | 2022-03-01 | 2023-11-30 |

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
| Rerun Command | python scripts/download_yield_curve_10y3mo_steepening_v0.py --observation-start 2003-01-02 --observation-end 2026-01-02 --snapshot-date 2026-06-21 |
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
