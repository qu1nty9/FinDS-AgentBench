from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from finds_agentbench.paper_artifacts import latex_escape


@dataclass(frozen=True)
class RelatedWorkEntry:
    key: str
    title: str
    short_name: str
    year: int
    category: str
    primary_focus: str
    relevant_overlap: str
    gap_for_finds: str
    url: str
    bibtex: str


RELATED_WORK_AUDIT_DATE = "2026-06-25"


RELATED_WORK_ENTRIES = [
    RelatedWorkEntry(
        key="agentbench2023",
        title="AgentBench: Evaluating LLMs as Agents",
        short_name="AgentBench",
        year=2023,
        category="general_agent_benchmark",
        primary_focus="Interactive LLM-agent evaluation across multiple environments.",
        relevant_overlap="Frames LLMs as agents acting over multi-turn environments.",
        gap_for_finds="Not specialized for financial ML research artifacts, point-in-time data, leakage checks, or writeup validity.",
        url="https://arxiv.org/abs/2308.03688",
        bibtex="""@article{agentbench2023,
  title={AgentBench: Evaluating LLMs as Agents},
  author={Liu, Xiao and Yu, Hao and Zhang, Hanchen and Xu, Yifan and Lei, Xuanyu and others},
  journal={arXiv preprint arXiv:2308.03688},
  year={2023}
}""",
    ),
    RelatedWorkEntry(
        key="swebench2023",
        title="SWE-bench: Can Language Models Resolve Real-World GitHub Issues?",
        short_name="SWE-bench",
        year=2023,
        category="software_engineering_agent_benchmark",
        primary_focus="Repository-level issue resolution from real GitHub issues and pull requests.",
        relevant_overlap="Execution-based, artifact-producing agent evaluation.",
        gap_for_finds="Software engineering rather than financial data-science research with temporal holdouts and financial validity gates.",
        url="https://arxiv.org/abs/2310.06770",
        bibtex="""@article{swebench2023,
  title={SWE-bench: Can Language Models Resolve Real-World GitHub Issues?},
  author={Jimenez, Carlos E. and Yang, John and Wettig, Alexander and Yao, Shunyu and Pei, Kexin and Press, Ofir and Narasimhan, Karthik},
  journal={arXiv preprint arXiv:2310.06770},
  year={2023}
}""",
    ),
    RelatedWorkEntry(
        key="ds10002022",
        title="DS-1000: A Natural and Reliable Benchmark for Data Science Code Generation",
        short_name="DS-1000",
        year=2022,
        category="data_science_code_generation",
        primary_focus="Data-science code generation with reliable functional tests.",
        relevant_overlap="Data analysis and modeling tasks with executable evaluation.",
        gap_for_finds="Short code-generation tasks rather than full financial research workflows with notebooks, writeups, and temporal validity checks.",
        url="https://arxiv.org/abs/2211.11501",
        bibtex="""@article{ds10002022,
  title={DS-1000: A Natural and Reliable Benchmark for Data Science Code Generation},
  author={Lai, Yuhang and Li, Chengxi and Wang, Yiming and Zhang, Tianyi and Zhong, Ruiqi and others},
  journal={arXiv preprint arXiv:2211.11501},
  year={2022}
}""",
    ),
    RelatedWorkEntry(
        key="infiagentdabench2024",
        title="InfiAgent-DABench: Evaluating Agents on Data Analysis Tasks",
        short_name="InfiAgent-DABench",
        year=2024,
        category="data_analysis_agent_benchmark",
        primary_focus="Agentic data-analysis tasks over CSV datasets and execution environments.",
        relevant_overlap="End-to-end data analysis agents with executable code and structured evaluation.",
        gap_for_finds=(
            "General data analysis rather than finance-specific temporal information sets, "
            "private holdouts, leakage gates, and research writeup audit."
        ),
        url="https://arxiv.org/abs/2401.05507",
        bibtex="""@article{infiagentdabench2024,
  title={InfiAgent-DABench: Evaluating Agents on Data Analysis Tasks},
  author={Hu, Xueyu and Zhao, Ziyu and Wei, Shuang and Chai, Ziwei and Ma, Qianli and others},
  journal={arXiv preprint arXiv:2401.05507},
  year={2024}
}""",
    ),
    RelatedWorkEntry(
        key="mlagentbench2023",
        title="MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation",
        short_name="MLAgentBench",
        year=2023,
        category="machine_learning_agent_benchmark",
        primary_focus="Language agents conducting ML experimentation tasks.",
        relevant_overlap="Long-horizon ML experimentation with file editing and code execution.",
        gap_for_finds="Not domain-specific to financial ML, point-in-time data availability, backtest realism, or claim audit.",
        url="https://arxiv.org/abs/2310.03302",
        bibtex="""@article{mlagentbench2023,
  title={MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation},
  author={Huang, Qian and Vora, Jian and Liang, Percy and Leskovec, Jure},
  journal={arXiv preprint arXiv:2310.03302},
  year={2023}
}""",
    ),
    RelatedWorkEntry(
        key="mlebench2024",
        title="MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering",
        short_name="MLE-bench",
        year=2024,
        category="machine_learning_engineering_agent_benchmark",
        primary_focus="Kaggle-style ML engineering competitions for agents.",
        relevant_overlap="Agentic ML engineering, leaderboard-style scoring, and contamination analysis.",
        gap_for_finds="Broad ML engineering rather than finance-specific temporal information sets, leakage-safe research notebooks, and validity-gated writeups.",
        url="https://arxiv.org/abs/2410.07095",
        bibtex="""@article{mlebench2024,
  title={MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering},
  author={Chan, Jun Shern and Chowdhury, Neil and Jaffe, Oliver and Aung, James and Sherburn, Dane and others},
  journal={arXiv preprint arXiv:2410.07095},
  year={2024}
}""",
    ),
    RelatedWorkEntry(
        key="scienceagentbench2024",
        title="ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery",
        short_name="ScienceAgentBench",
        year=2024,
        category="scientific_discovery_agent_benchmark",
        primary_focus="Scientific workflow tasks extracted from peer-reviewed publications.",
        relevant_overlap="Research-style agent evaluation with code execution and expert validation.",
        gap_for_finds="Not specialized for market data, point-in-time financial constraints, financial metrics, or investment-style claim discipline.",
        url="https://arxiv.org/abs/2410.05080",
        bibtex="""@article{scienceagentbench2024,
  title={ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery},
  author={Chen, Ziru and Chen, Shijie and Ning, Yuting and Zhang, Qianheng and Wang, Boshi and others},
  journal={arXiv preprint arXiv:2410.05080},
  year={2024}
}""",
    ),
    RelatedWorkEntry(
        key="mlrbench2025",
        title="MLR-Bench: Evaluating AI Agents on Open-Ended Machine Learning Research",
        short_name="MLR-Bench",
        year=2025,
        category="machine_learning_research_agent_benchmark",
        primary_focus="Open-ended ML research tasks with proposal, experimentation, and paper-writing stages.",
        relevant_overlap="Evaluates research automation and paper-style outputs.",
        gap_for_finds="Not focused on finance-specific leakage, temporal validation, private holdouts, or financial model-risk framing.",
        url="https://arxiv.org/abs/2505.19955",
        bibtex="""@article{mlrbench2025,
  title={MLR-Bench: Evaluating AI Agents on Open-Ended Machine Learning Research},
  author={Chen, Hui and Xiong, Miao and Lu, Yujie and Han, Wei and Deng, Ailin and others},
  journal={arXiv preprint arXiv:2505.19955},
  year={2025}
}""",
    ),
    RelatedWorkEntry(
        key="financebench2023",
        title="FinanceBench: A New Benchmark for Financial Question Answering",
        short_name="FinanceBench",
        year=2023,
        category="financial_question_answering",
        primary_focus="Open-book financial QA over company documents.",
        relevant_overlap="Finance-domain LLM evaluation with evidence requirements.",
        gap_for_finds="QA rather than executable financial ML research with notebooks, temporal holdouts, and private scoring.",
        url="https://arxiv.org/abs/2311.11944",
        bibtex="""@article{financebench2023,
  title={FinanceBench: A New Benchmark for Financial Question Answering},
  author={Islam, Pranab and Kannappan, Anand and Kiela, Douwe and Qian, Rebecca and Scherrer, Nino and Vidgen, Bertie},
  journal={arXiv preprint arXiv:2311.11944},
  year={2023}
}""",
    ),
    RelatedWorkEntry(
        key="finben2024",
        title="FinBen: A Holistic Financial Benchmark for Large Language Models",
        short_name="FinBen",
        year=2024,
        category="financial_llm_benchmark",
        primary_focus="Broad financial LLM benchmark across language, QA, forecasting, risk, and decision tasks.",
        relevant_overlap="Finance-specific LLM evaluation across heterogeneous task types.",
        gap_for_finds="Broad LLM capability suite rather than validity-gated end-to-end financial ML research artifacts.",
        url="https://arxiv.org/abs/2402.12659",
        bibtex="""@article{finben2024,
  title={FinBen: A Holistic Financial Benchmark for Large Language Models},
  author={Xie, Qianqian and Han, Weiguang and Chen, Zhengyu and Xiang, Ruoyu and Zhang, Xiao and others},
  journal={arXiv preprint arXiv:2402.12659},
  year={2024}
}""",
    ),
    RelatedWorkEntry(
        key="profitmirage2025",
        title="Profit Mirage: Revisiting Information Leakage in LLM-based Financial Agents",
        short_name="Profit Mirage / FinLake-Bench",
        year=2025,
        category="financial_leakage_agent_benchmark",
        primary_focus="Information leakage in LLM-based financial agents and leakage-robust evaluation.",
        relevant_overlap="Closest finance-agent neighbor for leakage-aware evaluation.",
        gap_for_finds="Focuses on leakage and trading-agent generalization; FinDS-AgentBench broadens to reproducible ML research artifacts, task/evaluation cards, writeup audit, and multi-track validity scoring.",
        url="https://arxiv.org/abs/2510.07920",
        bibtex="""@article{profitmirage2025,
  title={Profit Mirage: Revisiting Information Leakage in LLM-based Financial Agents},
  author={Li, Xiangyu and Zeng, Yawen and Xing, Xiaofen and Xu, Jin and Xu, Xiangmin},
  journal={arXiv preprint arXiv:2510.07920},
  year={2025}
}""",
    ),
    RelatedWorkEntry(
        key="temporalbench2026",
        title="TemporalBench: A Benchmark for Evaluating LLM-Based Agents on Contextual and Event-Informed Time Series Tasks",
        short_name="TemporalBench",
        year=2026,
        category="temporal_reasoning_agent_benchmark",
        primary_focus="Contextual and event-informed time-series reasoning across multiple domains.",
        relevant_overlap="Temporal reasoning and event-conditioned prediction.",
        gap_for_finds="Multi-domain time-series reasoning rather than financial ML research artifacts with point-in-time market data, leakage scanning, and narrative audit.",
        url="https://arxiv.org/abs/2602.13272",
        bibtex="""@article{temporalbench2026,
  title={TemporalBench: A Benchmark for Evaluating LLM-Based Agents on Contextual and Event-Informed Time Series Tasks},
  author={Weng, Muyan and Cao, Defu and Yang, Wei and Sharma, Yashaswi and Liu, Yan},
  journal={arXiv preprint arXiv:2602.13272},
  year={2026}
}""",
    ),
    RelatedWorkEntry(
        key="fintoolbench2026",
        title="FinToolBench: Evaluating LLM Agents for Real-World Financial Tool Use",
        short_name="FinToolBench",
        year=2026,
        category="financial_tool_use_agent_benchmark",
        primary_focus="Financial tool-learning agents over executable financial tools.",
        relevant_overlap="Auditable financial agent execution and finance-specific tool use.",
        gap_for_finds="Tool invocation rather than leakage-safe financial ML research notebooks and validity-gated result claims.",
        url="https://arxiv.org/abs/2603.08262",
        bibtex="""@article{fintoolbench2026,
  title={FinToolBench: Evaluating LLM Agents for Real-World Financial Tool Use},
  author={Lu, Jiaxuan and Wang, Kong and Wang, Yemin and Tang, Qingmei and Zeng, Hongwei and others},
  journal={arXiv preprint arXiv:2603.08262},
  year={2026}
}""",
    ),
    RelatedWorkEntry(
        key="finmcpbench2026",
        title="FinMCP-Bench: Benchmarking LLM Agents for Real-World Financial Tool Use under the Model Context Protocol",
        short_name="FinMCP-Bench",
        year=2026,
        category="financial_tool_use_agent_benchmark",
        primary_focus="Financial tool invocation through model context protocol servers.",
        relevant_overlap="Financial agent execution with real and synthetic tool-use queries.",
        gap_for_finds="MCP/tool-use benchmark rather than end-to-end financial ML research with temporal holdouts and artifact audit.",
        url="https://arxiv.org/abs/2603.24943",
        bibtex="""@article{finmcpbench2026,
  title={FinMCP-Bench: Benchmarking LLM Agents for Real-World Financial Tool Use under the Model Context Protocol},
  author={Zhu, Jie and Tian, Yimin and Li, Boyang and Wu, Kehao and Liang, Zhongzhi and others},
  journal={arXiv preprint arXiv:2603.24943},
  year={2026}
}""",
    ),
    RelatedWorkEntry(
        key="workstreambench2026",
        title="WorkstreamBench: Evaluating LLM Agents on End-to-End Spreadsheet Tasks in Finance",
        short_name="WorkstreamBench",
        year=2026,
        category="financial_spreadsheet_agent_benchmark",
        primary_focus="End-to-end financial spreadsheet construction and review.",
        relevant_overlap="Finance workflow artifacts and multidimensional professional-quality evaluation.",
        gap_for_finds="Spreadsheet modeling rather than financial ML research with temporal prediction tasks, private holdouts, and leakage/reproducibility gates.",
        url="https://arxiv.org/abs/2605.22664",
        bibtex="""@article{workstreambench2026,
  title={WorkstreamBench: Evaluating LLM Agents on End-to-End Spreadsheet Tasks in Finance},
  author={Yen, Thomson and Poeltl, Julian and Gear, Harshith Srinivas and Meng, Yilin and Fan, Joshua and others},
  journal={arXiv preprint arXiv:2605.22664},
  year={2026}
}""",
    ),
    RelatedWorkEntry(
        key="bluefin2026",
        title="BlueFin: Benchmarking LLM Agents on Financial Spreadsheets",
        short_name="BlueFin",
        year=2026,
        category="financial_spreadsheet_agent_benchmark",
        primary_focus="Financial spreadsheet synthesis, manipulation, and comprehension tasks.",
        relevant_overlap="Finance-domain agent artifacts with granular rubric-based evaluation.",
        gap_for_finds=(
            "Spreadsheet workbook workflows rather than executable financial ML research notebooks, "
            "temporal prediction tasks, and leakage-safe private scoring."
        ),
        url="https://arxiv.org/abs/2605.30907",
        bibtex="""@article{bluefin2026,
  title={BlueFin: Benchmarking LLM Agents on Financial Spreadsheets},
  author={Kundurthy, Srivatsa and Na, Clara and Moraine, Colton and Mohta, Anoushka and Winter, Case and others},
  journal={arXiv preprint arXiv:2605.30907},
  year={2026}
}""",
    ),
]


def render_related_work_markdown(entries: list[RelatedWorkEntry] | None = None) -> str:
    selected_entries = entries or RELATED_WORK_ENTRIES
    lines = [
        "# Related Work Matrix",
        "",
        "This file tracks adjacent benchmarks and the specific gap FinDS-AgentBench should claim.",
        "",
        "| Work | Year | Primary focus | Relevant overlap | Gap for FinDS-AgentBench | Source |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for entry in selected_entries:
        lines.append(
            " | ".join(
                [
                    f"| {entry.short_name}",
                    str(entry.year),
                    entry.primary_focus,
                    entry.relevant_overlap,
                    entry.gap_for_finds,
                    f"[arXiv]({entry.url}) |",
                ]
            )
        )
    lines.extend(
        [
            "",
            "## Citation Audit Notes",
            "",
            f"- Last audited against arXiv records: {RELATED_WORK_AUDIT_DATE}.",
            "- arXiv:2605.22664 is tracked as WorkstreamBench, not MBABench.",
            "- BlueFin is included as a finance-spreadsheet neighbor distinct from end-to-end financial ML research.",
            "",
            "## Working Novelty Claim",
            "",
            "FinDS-AgentBench is a benchmark for end-to-end financial ML research agents, combining point-in-time data calendars, temporal validation, leakage checks, executable notebooks, financial decision metrics, reproducibility gates, writeup audit, and agent trace analysis.",
            "",
            "## Venue Positioning",
            "",
            "- For an arXiv/workshop pilot, the strongest claim is a compact, reproducible stress test showing that plausible financial ML notebooks fail under temporal, leakage, reproducibility, and claim-discipline checks.",
            "- For a benchmark/dataset venue, the required advance is a larger frozen task suite with hidden temporal holdouts, external-agent evidence, public/private scoring, and independently reviewed audit rubrics.",
            "- For a journal extension, the required advance is methodological analysis of repeated-run variance, intervention effects, validity dimensions, and financial model-risk implications.",
            "",
        ]
    )
    return "\n".join(lines)


def render_related_work_tex(entries: list[RelatedWorkEntry] | None = None) -> str:
    selected_entries = entries or RELATED_WORK_ENTRIES
    ml_agent_keys = [
        "agentbench2023",
        "mlagentbench2023",
        "mlebench2024",
        "scienceagentbench2024",
        "mlrbench2025",
    ]
    finance_keys = [
        "financebench2023",
        "finben2024",
        "profitmirage2025",
        "fintoolbench2026",
        "finmcpbench2026",
        "workstreambench2026",
        "bluefin2026",
    ]
    data_analysis_keys = ["ds10002022", "infiagentdabench2024"]
    temporal_keys = ["temporalbench2026"]
    general_agent_paragraph = (
        "FinDS-AgentBench sits at the intersection of agent benchmarks, machine-learning "
        "experimentation benchmarks, finance-domain LLM evaluation, and leakage-aware temporal "
        "validation. General agent and software-engineering benchmarks such as "
        + citation_group(["agentbench2023", "swebench2023"])
        + " emphasize multi-step execution, but do not target financial ML research validity."
    )
    ml_agent_paragraph = (
        "ML-oriented agent benchmarks such as "
        + citation_group(ml_agent_keys[1:])
        + " evaluate experimentation, engineering, or open-ended research automation. "
        "FinDS-AgentBench adopts their emphasis on executable artifacts while adding point-in-time "
        "finance data, temporal holdouts, leakage scanning, and writeup audit."
    )
    finance_paragraph = (
        "Finance benchmarks such as "
        + citation_group(finance_keys)
        + " cover financial QA, broad financial LLM capabilities, leakage in financial agents, "
        "tool use, and spreadsheet workflows. These are adjacent but do not provide an end-to-end "
        "financial ML research benchmark with point-in-time task cards, private temporal labels, "
        "repeated-run uncertainty, reproducibility gates, and narrative-discipline scoring."
    )
    data_analysis_paragraph = (
        "Data-science and data-analysis benchmarks such as "
        + citation_group(data_analysis_keys)
        + " motivate reliable code execution and analysis-task evaluation. FinDS-AgentBench extends "
        "that execution focus to financial research protocols where model validation, data timestamp "
        "availability, and claims about economic usefulness must be evaluated jointly."
    )
    temporal_paragraph = (
        "Temporal-reasoning benchmarks such as "
        + citation_group(temporal_keys)
        + " motivate time-aware evaluation. FinDS-AgentBench narrows that lens to finance, where "
        "point-in-time information availability and leakage-safe validation are central rather than "
        "incidental constraints."
    )
    return "\n".join(
        [
            "\\section{Related Work}",
            general_agent_paragraph,
            ml_agent_paragraph,
            finance_paragraph,
            data_analysis_paragraph,
            temporal_paragraph,
            "",
            "\\begin{table}[t]",
            "\\centering",
            "\\small",
            "\\resizebox{\\textwidth}{!}{%",
            "\\begin{tabular}{lll}",
            "\\toprule",
            "Work & Neighbor Area & FinDS-AgentBench distinction \\\\",
            "\\midrule",
            *[
                " & ".join(
                    [
                        f"{latex_escape(entry.short_name)}~\\cite{{{entry.key}}}",
                        latex_escape(related_work_area(entry)),
                        latex_escape(compact_gap_for_table(entry)),
                    ]
                )
                + " \\\\"
                for entry in selected_entries
            ],
            "\\bottomrule",
            "\\end{tabular}",
            "}",
            "\\caption{Related benchmark positioning. FinDS-AgentBench targets the missing intersection of end-to-end financial ML research artifacts, temporal information discipline, leakage resistance, reproducibility, and writeup validity.}",
            "\\label{tab:related-work-positioning}",
            "\\end{table}",
            "",
        ]
    )


def citation_group(keys: list[str]) -> str:
    return "~\\cite{" + ",".join(keys) + "}"


def related_work_area(entry: RelatedWorkEntry) -> str:
    if "finance" in entry.category or "financial" in entry.category:
        return "Finance-domain agent/LLM benchmark"
    if "machine_learning" in entry.category:
        return "ML agent benchmark"
    if "data" in entry.category:
        return "Data-science agent benchmark"
    if "temporal" in entry.category:
        return "Temporal reasoning benchmark"
    if "software" in entry.category:
        return "Software-engineering agent benchmark"
    return "General agent benchmark"


def compact_gap_for_table(entry: RelatedWorkEntry) -> str:
    table_gaps = {
        "agentbench2023": "Broad agent tasks; no financial ML protocol or point-in-time validity gates.",
        "swebench2023": "Software repair rather than financial research notebooks and temporal holdouts.",
        "ds10002022": "Code-generation tasks rather than full financial ML research artifacts.",
        "infiagentdabench2024": "General data analysis without finance-specific leakage and holdout discipline.",
        "mlagentbench2023": "ML experimentation without finance-specific data calendars or claim audit.",
        "mlebench2024": "Kaggle-style ML engineering rather than financial temporal information discipline.",
        "scienceagentbench2024": "Scientific workflows without market data, finance metrics, or investment-claim audit.",
        "mlrbench2025": "Open-ended ML research without finance leakage, private holdouts, or model-risk framing.",
        "financebench2023": "Financial QA rather than executable financial ML research artifacts.",
        "finben2024": "Broad financial LLM skills rather than validity-gated research workflows.",
        "profitmirage2025": "Leakage-aware financial agents, but not reproducible research notebooks and audit cards.",
        "temporalbench2026": "Time-series reasoning without financial ML artifacts and private temporal scoring.",
        "fintoolbench2026": "Tool invocation rather than leakage-safe financial ML notebooks.",
        "finmcpbench2026": "MCP tool use rather than end-to-end financial ML research workflows.",
        "workstreambench2026": "Spreadsheet workflows rather than temporal prediction and leakage-safe scoring.",
        "bluefin2026": "Spreadsheet tasks rather than executable financial ML notebooks and holdouts.",
    }
    return table_gaps.get(entry.key, entry.gap_for_finds)


def render_bibtex(entries: list[RelatedWorkEntry] | None = None) -> str:
    selected_entries = entries or RELATED_WORK_ENTRIES
    return "\n\n".join(entry.bibtex.strip() for entry in selected_entries) + "\n"


def build_related_work_artifacts(
    *,
    markdown_path: str | Path = "docs/related_work_matrix.md",
    tex_path: str | Path = "papers/workshop_pilot/related_work.tex",
    bib_path: str | Path = "papers/workshop_pilot/references.bib",
) -> dict[str, Path]:
    paths = {
        "markdown": Path(markdown_path),
        "tex": Path(tex_path),
        "bib": Path(bib_path),
    }
    paths["markdown"].parent.mkdir(parents=True, exist_ok=True)
    paths["tex"].parent.mkdir(parents=True, exist_ok=True)
    paths["bib"].parent.mkdir(parents=True, exist_ok=True)
    paths["markdown"].write_text(render_related_work_markdown(), encoding="utf-8")
    paths["tex"].write_text(render_related_work_tex(), encoding="utf-8")
    paths["bib"].write_text(render_bibtex(), encoding="utf-8")
    return paths
