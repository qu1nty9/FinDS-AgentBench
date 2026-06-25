# Related Work Matrix

This file tracks adjacent benchmarks and the specific gap FinDS-AgentBench should claim.

| Work | Year | Primary focus | Relevant overlap | Gap for FinDS-AgentBench | Source |
| --- | ---: | --- | --- | --- | --- |
| AgentBench | 2023 | Interactive LLM-agent evaluation across multiple environments. | Frames LLMs as agents acting over multi-turn environments. | Not specialized for financial ML research artifacts, point-in-time data, leakage checks, or writeup validity. | [arXiv](https://arxiv.org/abs/2308.03688) |
| SWE-bench | 2023 | Repository-level issue resolution from real GitHub issues and pull requests. | Execution-based, artifact-producing agent evaluation. | Software engineering rather than financial data-science research with temporal holdouts and financial validity gates. | [arXiv](https://arxiv.org/abs/2310.06770) |
| DS-1000 | 2022 | Data-science code generation with reliable functional tests. | Data analysis and modeling tasks with executable evaluation. | Short code-generation tasks rather than full financial research workflows with notebooks, writeups, and temporal validity checks. | [arXiv](https://arxiv.org/abs/2211.11501) |
| InfiAgent-DABench | 2024 | Agentic data-analysis tasks over CSV datasets and execution environments. | End-to-end data analysis agents with executable code and structured evaluation. | General data analysis rather than finance-specific temporal information sets, private holdouts, leakage gates, and research writeup audit. | [arXiv](https://arxiv.org/abs/2401.05507) |
| MLAgentBench | 2023 | Language agents conducting ML experimentation tasks. | Long-horizon ML experimentation with file editing and code execution. | Not domain-specific to financial ML, point-in-time data availability, backtest realism, or claim audit. | [arXiv](https://arxiv.org/abs/2310.03302) |
| MLE-bench | 2024 | Kaggle-style ML engineering competitions for agents. | Agentic ML engineering, leaderboard-style scoring, and contamination analysis. | Broad ML engineering rather than finance-specific temporal information sets, leakage-safe research notebooks, and validity-gated writeups. | [arXiv](https://arxiv.org/abs/2410.07095) |
| ScienceAgentBench | 2024 | Scientific workflow tasks extracted from peer-reviewed publications. | Research-style agent evaluation with code execution and expert validation. | Not specialized for market data, point-in-time financial constraints, financial metrics, or investment-style claim discipline. | [arXiv](https://arxiv.org/abs/2410.05080) |
| MLR-Bench | 2025 | Open-ended ML research tasks with proposal, experimentation, and paper-writing stages. | Evaluates research automation and paper-style outputs. | Not focused on finance-specific leakage, temporal validation, private holdouts, or financial model-risk framing. | [arXiv](https://arxiv.org/abs/2505.19955) |
| FinanceBench | 2023 | Open-book financial QA over company documents. | Finance-domain LLM evaluation with evidence requirements. | QA rather than executable financial ML research with notebooks, temporal holdouts, and private scoring. | [arXiv](https://arxiv.org/abs/2311.11944) |
| FinBen | 2024 | Broad financial LLM benchmark across language, QA, forecasting, risk, and decision tasks. | Finance-specific LLM evaluation across heterogeneous task types. | Broad LLM capability suite rather than validity-gated end-to-end financial ML research artifacts. | [arXiv](https://arxiv.org/abs/2402.12659) |
| Profit Mirage / FinLake-Bench | 2025 | Information leakage in LLM-based financial agents and leakage-robust evaluation. | Closest finance-agent neighbor for leakage-aware evaluation. | Focuses on leakage and trading-agent generalization; FinDS-AgentBench broadens to reproducible ML research artifacts, task/evaluation cards, writeup audit, and multi-track validity scoring. | [arXiv](https://arxiv.org/abs/2510.07920) |
| TemporalBench | 2026 | Contextual and event-informed time-series reasoning across multiple domains. | Temporal reasoning and event-conditioned prediction. | Multi-domain time-series reasoning rather than financial ML research artifacts with point-in-time market data, leakage scanning, and narrative audit. | [arXiv](https://arxiv.org/abs/2602.13272) |
| FinToolBench | 2026 | Financial tool-learning agents over executable financial tools. | Auditable financial agent execution and finance-specific tool use. | Tool invocation rather than leakage-safe financial ML research notebooks and validity-gated result claims. | [arXiv](https://arxiv.org/abs/2603.08262) |
| FinMCP-Bench | 2026 | Financial tool invocation through model context protocol servers. | Financial agent execution with real and synthetic tool-use queries. | MCP/tool-use benchmark rather than end-to-end financial ML research with temporal holdouts and artifact audit. | [arXiv](https://arxiv.org/abs/2603.24943) |
| WorkstreamBench | 2026 | End-to-end financial spreadsheet construction and review. | Finance workflow artifacts and multidimensional professional-quality evaluation. | Spreadsheet modeling rather than financial ML research with temporal prediction tasks, private holdouts, and leakage/reproducibility gates. | [arXiv](https://arxiv.org/abs/2605.22664) |
| BlueFin | 2026 | Financial spreadsheet synthesis, manipulation, and comprehension tasks. | Finance-domain agent artifacts with granular rubric-based evaluation. | Spreadsheet workbook workflows rather than executable financial ML research notebooks, temporal prediction tasks, and leakage-safe private scoring. | [arXiv](https://arxiv.org/abs/2605.30907) |

## Citation Audit Notes

- Last audited against arXiv records: 2026-06-25.
- arXiv:2605.22664 is tracked as WorkstreamBench, not MBABench.
- BlueFin is included as a finance-spreadsheet neighbor distinct from end-to-end financial ML research.

## Working Novelty Claim

FinDS-AgentBench is a benchmark for end-to-end financial ML research agents, combining point-in-time data calendars, temporal validation, leakage checks, executable notebooks, financial decision metrics, reproducibility gates, writeup audit, and agent trace analysis.

## Venue Positioning

- For an arXiv/workshop pilot, the strongest claim is a compact, reproducible stress test showing that plausible financial ML notebooks fail under temporal, leakage, reproducibility, and claim-discipline checks.
- For a benchmark/dataset venue, the required advance is a larger frozen task suite with hidden temporal holdouts, external-agent evidence, public/private scoring, and independently reviewed audit rubrics.
- For a journal extension, the required advance is methodological analysis of repeated-run variance, intervention effects, validity dimensions, and financial model-risk implications.
