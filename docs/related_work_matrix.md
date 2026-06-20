# Related Work Matrix

This file tracks adjacent benchmarks and the specific gap FinDS-AgentBench should claim.

| Work | Primary focus | Relevant overlap | Gap for FinDS-AgentBench |
| --- | --- | --- | --- |
| MLE-bench | ML engineering on Kaggle competitions | Agentic ML experimentation and leaderboard-style scoring | Not finance-specific; does not center point-in-time finance constraints or writeup validity |
| MLAgentBench | Language agents for ML experimentation | Long-horizon ML agent behavior | Not specialized for financial leakage, backtesting, or temporal information sets |
| DSBench / DS-1000 | Data-science tasks and code correctness | Data analysis and modeling | Less emphasis on full financial research artifact and audit trail |
| MLR-Bench | Open-ended ML research automation | Idea, experimentation, paper-writing failures | Not focused on financial ML validity constraints |
| ScienceAgentBench | Scientific data-driven discovery | Research-style agent evaluation | Not specialized for finance, market data, or transaction-cost-aware validation |
| FinanceBench | Financial QA over company documents | Finance-domain LLM evaluation | QA rather than executable ML research workflow |
| FinBen | Broad financial LLM benchmark | Financial language, QA, forecasting, risk, decision tasks | Broad LLM capabilities rather than end-to-end reproducible financial ML research |
| FinToolBench / FinMCP-Bench | Financial tool-use agents | Tool invocation and finance agent infrastructure | Tool use rather than leakage-safe research notebooks and validity-gated scoring |
| TemporalBench | Temporal and event-informed reasoning | Time-aware reasoning and event availability | Not specifically financial ML/backtesting/reproducible notebooks |
| WorkstreamBench | End-to-end finance spreadsheet creation | Finance artifacts and workflow execution | Spreadsheet workflows rather than financial ML research and temporal holdouts |
| Profit Mirage / FinLake-Bench | Leakage in financial LLM agents | Leakage-focused financial agent evaluation | Closest neighbor; FinDS-AgentBench should differentiate through end-to-end ML research artifacts, task cards, temporal holdouts, reproducibility, writeup audit, and broader failure taxonomy |
| Leakage and reproducibility literature | Leakage/reproducibility failures in ML science | Methodological foundation | Not an agent benchmark or reusable financial ML evaluation suite |

## Working Novelty Claim

FinDS-AgentBench is a benchmark for end-to-end financial ML research agents, combining point-in-time data calendars, temporal validation, leakage checks, executable notebooks, financial decision metrics, reproducibility gates, writeup audit, and agent trace analysis.

