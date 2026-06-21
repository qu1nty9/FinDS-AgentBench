# leakage_audit_temporal_split_v0 Task Card

Generated from the benchmark task specification.

## Snapshot

| Field | Value |
| --- | --- |
| Task ID | leakage_audit_temporal_split_v0 |
| Title | Audit a Financial ML Notebook for Temporal Leakage |
| Track | research_replication_and_audit |
| Version | 0.1.0 |
| Status | draft |
| Owner | FinDS-AgentBench contributors |
| Tags | leakage, audit, replication, validation |
| Source Spec | tasks/pilot/leakage_audit_temporal_split_v0.yaml |
| Data Access | bundled |
| License Status | usable |
| Primary Metric | audit_correctness_score |

## Research Prompt

**Summary**: Detect and correct leakage in a flawed financial ML notebook.

**Research Question**: Can an agent identify invalid validation and future leakage, repair the workflow, and quantify the performance drop?

**Instructions**: You are given a financial ML notebook with suspiciously strong results. Audit the notebook, identify leakage or validation flaws, rerun the analysis with a correct temporal split, and write a before/after audit note.



**Prohibited Shortcuts**

- Do not preserve random splits if the task has temporal structure.
- Do not report the flawed score as the final valid score.
- Do not change labels or rows to hide the performance drop.

## Data

**Local Paths**: data/raw/leakage_audit_temporal_split_v0/

**Generator/Download Script**: scripts/generate_leakage_audit_temporal_split_v0.py


**Sources**

| Name | License | Access | Reference |
| --- | --- | --- | --- |
| Synthetic financial panel with controlled leakage traps | project_generated | synthetic_generator | generated locally |


**Data Dictionary**

| Column | Meaning | Availability Lag |
| --- | --- | --- |
| date | Observation date. | Known at prediction timestamp. |
| asset_id | Synthetic asset identifier. | Known at prediction timestamp. |
| feature_lagged_signal | Legitimate lagged signal. | Known at prediction timestamp. |
| feature_future_return_leak | Intentionally leaked future information. | Not available at prediction timestamp. |
| target | Future outcome label. | Known only after target horizon. |

## Information Set

**Prediction Timestamp**: End of period t, before target outcome for t+1 is known.


**Allowed Information**

- Synthetic features marked as known at or before t.
- Lagged target history only when shifted before t.


**Forbidden Information**

- feature_future_return_leak
- target for validation or holdout rows during model selection
- Any feature computed using t+1 outcome.


**Availability Calendar**

| Item | Known At | Usable For Prediction At |
| --- | --- | --- |
| feature_lagged_signal | End of period t. | t+1 prediction. |
| feature_future_return_leak | After t+1 outcome. | Never for t+1 prediction. |


**Timestamp Alignment Rules**

- All target-derived features must be shifted by one full horizon.
- Split must be chronological at the row date level.

## Target

| Field | Value |
| --- | --- |
| Name | target |
| Definition | Binary future outcome for the next period. |
| Horizon | 1 period |
| Label Construction | Generated from latent process and aligned to period t features. |
| Positive Class | positive future outcome |
| Ranking Group | asset_id |

## Splits

**Split Method**: temporal

**Embargo or Gap**: One full target horizon.



| Split | Start | End |
| --- | --- | --- |
| train | 2020-01-02 | 2020-12-31 |
| public_validation | 2021-01-01 | 2021-06-30 |
| private_temporal_holdout | 2021-07-01 | 2021-12-29 |
| stress_test:leak_removed_stress | 2021-07-01 | 2021-12-29 |

## Deliverables


**Required Files**

- corrected_notebook.ipynb
- audit_note.md
- before_after_metrics.csv

| Field | Value |
| --- | --- |
| Notebook Path | corrected_notebook.ipynb |
| Notebook Must Execute Cleanly | true |
| Predictions Path | before_after_metrics.csv |
| Predictions Required Columns | metric, flawed_value, corrected_value |
| Writeup Path | audit_note.md |
| Writeup Max Words | 1500 |
| Retain Agent Trace | true |

## Reproducibility and Audit

| Field | Value |
| --- | --- |
| Environment | pyproject.toml |
| Random Seed Policy | Generator and models must use fixed seeds. |
| Rerun Command | python scripts/generate_leakage_audit_temporal_split_v0.py --seed 7 |
| Expected Runtime Limit | 20 minutes |
| CPU Limit | local_cpu |
| Memory Limit | 4GB |


**Artifact Retention**

- corrected notebook
- audit note
- before/after metrics
- execution log


**Trace Requirements**

- Store identified leakage mechanisms.
- Store corrected split code.
