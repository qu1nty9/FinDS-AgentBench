from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

from finds_agentbench.paper_artifacts import latex_escape, pretty_agent_label, pretty_task_label
from finds_agentbench.reports import results_to_markdown, to_float


DEFAULT_STATISTICAL_METRICS = (
    "score.overall_score",
    "score.balanced_accuracy",
    "score.roc_auc",
)

SUMMARY_UNCERTAINTY_COLUMNS = [
    "task_id",
    "agent_id",
    "run_type",
    "metric",
    "n",
    "mean",
    "std",
    "se",
    "ci95_low",
    "ci95_high",
    "min",
    "max",
]

PAIRED_COMPARISON_COLUMNS = [
    "task_id",
    "metric",
    "agent_id",
    "best_baseline_agent_id",
    "paired_count",
    "nonzero_difference_count",
    "agent_higher_count",
    "baseline_higher_count",
    "tie_count",
    "agent_mean",
    "best_baseline_mean",
    "mean_difference",
    "difference_std",
    "difference_se",
    "ci95_low",
    "ci95_high",
    "sign_test_p_value",
    "direction",
]

PAPER_SUMMARY_METRIC = "score.overall_score"

METRIC_LABELS = {
    "score.overall_score": "Overall",
    "score.balanced_accuracy": "Balanced Acc.",
    "score.roc_auc": "ROC AUC",
}

T_CRITICAL_975_BY_DF = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.16,
    14: 2.145,
    15: 2.131,
    16: 2.12,
    17: 2.11,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.08,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.06,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def load_protocol_result_rows(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def completed_numeric_values(rows: Iterable[dict[str, Any]], metric: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if row.get("status") != "completed":
            continue
        numeric = to_float(row.get(metric))
        if numeric is not None:
            values.append(numeric)
    return values


def t_critical_975(sample_size: int) -> float:
    if sample_size <= 1:
        return 0.0
    df = sample_size - 1
    return T_CRITICAL_975_BY_DF.get(df, 1.96)


def summarize_values(values: list[float]) -> dict[str, float | int]:
    if not values:
        raise ValueError("values must not be empty")
    n = len(values)
    mean_value = mean(values)
    std_value = stdev(values) if n > 1 else 0.0
    se_value = std_value / math.sqrt(n) if n > 1 else 0.0
    half_width = t_critical_975(n) * se_value
    return {
        "n": n,
        "mean": mean_value,
        "std": std_value,
        "se": se_value,
        "ci95_low": mean_value - half_width,
        "ci95_high": mean_value + half_width,
        "min": min(values),
        "max": max(values),
    }


def group_result_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("task_id", "")),
            str(row.get("agent_id", "")),
            str(row.get("run_type", "")),
        )
        grouped[key].append(row)
    return dict(grouped)


def build_summary_uncertainty_rows(
    rows: list[dict[str, Any]],
    *,
    metrics: Iterable[str] = DEFAULT_STATISTICAL_METRICS,
) -> list[dict[str, Any]]:
    grouped = group_result_rows(rows)
    output_rows: list[dict[str, Any]] = []
    for (task_id, agent_id, run_type), group_rows in sorted(grouped.items()):
        for metric in metrics:
            values = completed_numeric_values(group_rows, metric)
            if not values:
                continue
            output_rows.append(
                {
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "run_type": run_type,
                    "metric": metric,
                    **summarize_values(values),
                }
            )
    return output_rows


def pairing_key(row: dict[str, Any]) -> str | None:
    for column in ("trace.repeat_index", "trace.seed"):
        value = row.get(column)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def completed_numeric_values_by_pair(rows: Iterable[dict[str, Any]], metric: str) -> dict[str, float]:
    paired_values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("status") != "completed":
            continue
        key = pairing_key(row)
        if key is None:
            continue
        numeric = to_float(row.get(metric))
        if numeric is not None:
            paired_values[key].append(numeric)
    return {key: mean(values) for key, values in paired_values.items()}


def exact_two_sided_sign_test_p_value(differences: Iterable[float]) -> float | None:
    positive = 0
    negative = 0
    for value in differences:
        if value > 0:
            positive += 1
        elif value < 0:
            negative += 1
    nonzero_count = positive + negative
    if nonzero_count == 0:
        return None
    smaller_side = min(positive, negative)
    tail_probability = sum(
        math.comb(nonzero_count, successes) for successes in range(smaller_side + 1)
    ) / (2**nonzero_count)
    return min(1.0, 2.0 * tail_probability)


def best_baseline_group(
    baseline_groups: dict[str, list[dict[str, Any]]],
    metric: str,
) -> tuple[str, list[dict[str, Any]]] | None:
    candidates: list[tuple[float, str, list[dict[str, Any]]]] = []
    for agent_id, rows in baseline_groups.items():
        values = completed_numeric_values(rows, metric)
        if values:
            candidates.append((mean(values), agent_id, rows))
    if not candidates:
        return None
    _, agent_id, rows = sorted(candidates, key=lambda item: (-item[0], item[1]))[0]
    return agent_id, rows


def build_agent_vs_best_baseline_rows(
    rows: list[dict[str, Any]],
    *,
    metrics: Iterable[str] = DEFAULT_STATISTICAL_METRICS,
) -> list[dict[str, Any]]:
    grouped = group_result_rows(rows)
    tasks = sorted({task_id for task_id, _, _ in grouped})
    output_rows: list[dict[str, Any]] = []
    for task_id in tasks:
        baseline_groups = {
            agent_id: group_rows
            for (group_task_id, agent_id, run_type), group_rows in grouped.items()
            if group_task_id == task_id and run_type == "baseline"
        }
        agent_groups = {
            agent_id: group_rows
            for (group_task_id, agent_id, run_type), group_rows in grouped.items()
            if group_task_id == task_id and run_type == "agent"
        }
        if not baseline_groups or not agent_groups:
            continue

        for metric in metrics:
            best_baseline = best_baseline_group(baseline_groups, metric)
            if best_baseline is None:
                continue
            best_baseline_agent_id, best_baseline_rows = best_baseline
            best_baseline_by_pair = completed_numeric_values_by_pair(best_baseline_rows, metric)

            for agent_id, agent_rows in sorted(agent_groups.items()):
                if not completed_numeric_values(agent_rows, metric):
                    continue
                agent_by_pair = completed_numeric_values_by_pair(agent_rows, metric)
                shared_pairs = sorted(set(agent_by_pair) & set(best_baseline_by_pair), key=str)
                agent_values = [agent_by_pair[key] for key in shared_pairs]
                baseline_values = [best_baseline_by_pair[key] for key in shared_pairs]
                differences = [
                    agent_value - baseline_value
                    for agent_value, baseline_value in zip(agent_values, baseline_values, strict=True)
                ]
                paired_count = len(differences)
                positive_count = sum(1 for difference in differences if difference > 0)
                negative_count = sum(1 for difference in differences if difference < 0)
                tie_count = paired_count - positive_count - negative_count

                if differences:
                    diff_summary = summarize_values(differences)
                    mean_difference = float(diff_summary["mean"])
                    direction = (
                        "agent_higher"
                        if mean_difference > 0
                        else "baseline_higher"
                        if mean_difference < 0
                        else "tie"
                    )
                    output_rows.append(
                        {
                            "task_id": task_id,
                            "metric": metric,
                            "agent_id": agent_id,
                            "best_baseline_agent_id": best_baseline_agent_id,
                            "paired_count": paired_count,
                            "nonzero_difference_count": positive_count + negative_count,
                            "agent_higher_count": positive_count,
                            "baseline_higher_count": negative_count,
                            "tie_count": tie_count,
                            "agent_mean": mean(agent_values),
                            "best_baseline_mean": mean(baseline_values),
                            "mean_difference": mean_difference,
                            "difference_std": diff_summary["std"],
                            "difference_se": diff_summary["se"],
                            "ci95_low": diff_summary["ci95_low"],
                            "ci95_high": diff_summary["ci95_high"],
                            "sign_test_p_value": exact_two_sided_sign_test_p_value(differences),
                            "direction": direction,
                        }
                    )
                else:
                    output_rows.append(
                        {
                            "task_id": task_id,
                            "metric": metric,
                            "agent_id": agent_id,
                            "best_baseline_agent_id": best_baseline_agent_id,
                            "paired_count": 0,
                            "nonzero_difference_count": 0,
                            "agent_higher_count": 0,
                            "baseline_higher_count": 0,
                            "tie_count": 0,
                            "agent_mean": None,
                            "best_baseline_mean": None,
                            "mean_difference": None,
                            "difference_std": None,
                            "difference_se": None,
                            "ci95_low": None,
                            "ci95_high": None,
                            "sign_test_p_value": None,
                            "direction": "unpaired",
                        }
                    )
    return output_rows


def write_csv_rows(path: str | Path, rows: list[dict[str, Any]], *, columns: list[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def write_json_payload(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def release_facing_source_path(path: str | Path) -> str:
    source_path = Path(path)
    parts = source_path.parts
    if "reports" in parts:
        report_index = len(parts) - 1 - list(reversed(parts)).index("reports")
        return Path(*parts[report_index:]).as_posix()
    return source_path.name


def metric_label(metric: str) -> str:
    return METRIC_LABELS.get(metric, metric.replace("score.", "").replace("_", " ").title())


def format_latex_float(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.{digits}f}"


def format_latex_ci(row: dict[str, Any], *, digits: int = 3) -> str:
    return (
        f"[{format_latex_float(row['ci95_low'], digits)}, "
        f"{format_latex_float(row['ci95_high'], digits)}]"
    )


def direction_label(direction: str) -> str:
    labels = {
        "agent_higher": "Agent higher",
        "baseline_higher": "Baseline higher",
        "tie": "Tie",
        "unpaired": "Unpaired",
    }
    return labels.get(direction, direction.replace("_", " ").title())


def latex_label_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def render_summary_uncertainty_latex_table(
    rows: list[dict[str, Any]],
    *,
    metric: str = PAPER_SUMMARY_METRIC,
) -> str:
    selected_rows = [row for row in rows if row["metric"] == metric]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\begin{tabular}{llllcc}",
        "\\toprule",
        "Task & System & Type & $n$ & Mean & 95\\% CI \\\\",
        "\\midrule",
    ]
    for row in selected_rows:
        lines.append(
            " & ".join(
                [
                    latex_escape(pretty_task_label(str(row["task_id"]))),
                    latex_escape(pretty_agent_label(str(row["agent_id"]))),
                    latex_escape(str(row["run_type"]).title()),
                    str(row["n"]),
                    format_latex_float(row["mean"]),
                    format_latex_ci(row),
                ]
            )
            + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            (
                "\\caption{Pilot repeated-run uncertainty for "
                f"{latex_escape(metric_label(metric))}. Intervals are t-based 95\\% "
                "confidence intervals over completed runs.}"
            ),
            f"\\label{{tab:pilot-uncertainty-{latex_label_slug(metric)}}}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def render_agent_vs_best_baseline_latex_table(
    rows: list[dict[str, Any]],
    *,
    metric: str = PAPER_SUMMARY_METRIC,
) -> str:
    selected_rows = [row for row in rows if row["metric"] == metric]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\begin{tabular}{lllrrrrr}",
        "\\toprule",
        "Task & Agent & Best Baseline & $n$ & Agent & Baseline & $\\Delta$ & $p_{sign}$ \\\\",
        "\\midrule",
    ]
    for row in selected_rows:
        p_value = row.get("sign_test_p_value")
        lines.append(
            " & ".join(
                [
                    latex_escape(pretty_task_label(str(row["task_id"]))),
                    latex_escape(pretty_agent_label(str(row["agent_id"]))),
                    latex_escape(pretty_agent_label(str(row["best_baseline_agent_id"]))),
                    str(row["paired_count"]),
                    format_latex_float(row["agent_mean"]),
                    format_latex_float(row["best_baseline_mean"]),
                    format_latex_float(row["mean_difference"]),
                    format_latex_float(p_value) if p_value is not None else "",
                ]
            )
            + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            (
                "\\caption{Paired agent-minus-best-baseline comparison for "
                f"{latex_escape(metric_label(metric))}. Baselines are selected separately "
                "within each task by completed-run mean. The sign-test p-value is exact "
                "and two-sided.}"
            ),
            f"\\label{{tab:pilot-agent-vs-best-baseline-{latex_label_slug(metric)}}}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def render_statistical_methods_markdown(
    *,
    protocol_results_source_path: str,
    metrics: Iterable[str],
) -> str:
    metric_text = ", ".join(f"`{metric}`" for metric in metrics)
    return "\n".join(
        [
            "# Statistical Methods Snippet",
            "",
            "The pilot release reports repeated-run uncertainty directly from the combined protocol run table.",
            f"The source table is `{protocol_results_source_path}`, and the reported metrics are {metric_text}.",
            "",
            "For each task, system, run type, and metric, we retain completed runs with numeric metric values and report the sample mean, sample standard deviation, standard error, and a two-sided 95% t-interval. Single-run groups are reported with zero-width intervals rather than extrapolated uncertainty.",
            "",
            "For agent-vs-baseline comparisons, the best baseline is selected independently for each task and metric using the completed-run mean. Agent and baseline runs are then paired by `trace.repeat_index`, falling back to `trace.seed` only when no repeat index is available. We report the paired agent-minus-baseline mean difference, its t-interval, and an exact two-sided sign-test p-value after dropping zero differences.",
            "",
            "Because the pilot uses a small repeated-run count, these statistics are treated as transparent uncertainty and regression artifacts rather than definitive significance claims.",
            "",
        ]
    )


def render_statistical_methods_latex(
    *,
    protocol_results_source_path: str,
    metrics: Iterable[str],
) -> str:
    metric_text = ", ".join(latex_escape(metric) for metric in metrics)
    return "\n".join(
        [
            "\\paragraph{Statistical reporting.}",
            (
                "We report repeated-run uncertainty from the combined protocol run table "
                f"\\texttt{{{latex_escape(protocol_results_source_path)}}}. "
                f"The reported metrics are {metric_text}."
            ),
            (
                "For each task, system, run type, and metric, completed runs with numeric "
                "metric values are summarized by the sample mean, sample standard deviation, "
                "standard error, and a two-sided 95\\% t-interval. Single-run groups are "
                "reported with zero-width intervals rather than extrapolated uncertainty."
            ),
            (
                "For agent-vs-baseline comparisons, the best baseline is selected independently "
                "for each task and metric using the completed-run mean. Agent and baseline runs "
                "are paired by \\texttt{trace.repeat\\_index}, falling back to \\texttt{trace.seed} "
                "only when no repeat index is available. We report the paired agent-minus-baseline "
                "mean difference, its t-interval, and an exact two-sided sign-test p-value after "
                "dropping zero differences."
            ),
            (
                "Because the pilot uses a small repeated-run count, these statistics are treated "
                "as transparent uncertainty and regression artifacts rather than definitive "
                "significance claims."
            ),
            "",
        ]
    )


def render_statistical_artifacts_readme(
    *,
    protocol_results_source_path: str,
    summary_row_count: int,
    comparison_row_count: int,
) -> str:
    metrics = ", ".join(f"`{metric}`" for metric in DEFAULT_STATISTICAL_METRICS)
    return "\n".join(
        [
            "# Statistical Artifacts",
            "",
            "Pilot uncertainty and paired-comparison exports generated from the combined protocol run results.",
            "",
            "## Source",
            "",
            f"- Protocol run results: `{protocol_results_source_path}`",
            f"- Metrics: {metrics}",
            "",
            "## Files",
            "",
            "| File | Description |",
            "| --- | --- |",
            "| `summary_uncertainty.csv` | Tidy per-task, per-agent, per-metric mean, sample standard deviation, standard error, and 95% confidence interval. |",
            "| `summary_uncertainty.json` | Machine-readable copy of the uncertainty rows with method metadata. |",
            "| `summary_uncertainty.md` | Markdown table for review and paper drafting. |",
            "| `agent_vs_best_baseline.csv` | Paired agent-minus-best-baseline comparisons by task and metric. |",
            "| `agent_vs_best_baseline.json` | Machine-readable copy of the paired comparison rows with method metadata. |",
            "| `agent_vs_best_baseline.md` | Markdown table for review and paper drafting. |",
            "| `tables/summary_uncertainty_overall_score.tex` | Paper-ready LaTeX table for repeated-run overall-score uncertainty. |",
            "| `tables/agent_vs_best_baseline_overall_score.tex` | Paper-ready LaTeX table for paired overall-score agent-vs-baseline comparisons. |",
            "| `methods/statistical_methods.md` | Manuscript-ready statistical reporting text in Markdown. |",
            "| `methods/statistical_methods.tex` | Manuscript-ready statistical reporting text in LaTeX. |",
            "",
            "## Method",
            "",
            "- Only rows with `status=completed` and numeric metric values are included.",
            "- Uncertainty intervals are `mean +/- t_0.975,df * SE`; single-run groups have zero-width intervals.",
            "- The best baseline is selected separately for each task and metric by completed-run mean, with higher values treated as better.",
            "- Paired comparisons match runs by `trace.repeat_index`; `trace.seed` is used only when `trace.repeat_index` is unavailable.",
            "- The sign-test p-value is exact, two-sided, and ignores zero differences.",
            "",
            "## Pilot Caveat",
            "",
            "The pilot release uses a small repeated-run count. These artifacts provide transparent uncertainty reporting and regression checks; they should not be read as definitive significance claims.",
            "",
            "## Row Counts",
            "",
            "| Artifact | Rows |",
            "| --- | ---: |",
            f"| Summary uncertainty | {summary_row_count} |",
            f"| Agent vs. best baseline | {comparison_row_count} |",
            "",
        ]
    )


def build_statistical_artifacts(
    *,
    protocol_results_csv_path: str | Path,
    output_dir: str | Path,
    metrics: Iterable[str] = DEFAULT_STATISTICAL_METRICS,
) -> dict[str, Path]:
    metric_list = tuple(metrics)
    rows = load_protocol_result_rows(protocol_results_csv_path)
    protocol_results_source_path = release_facing_source_path(protocol_results_csv_path)
    output_root = Path(output_dir)
    tables_dir = output_root / "tables"
    methods_dir = output_root / "methods"
    output_root.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    methods_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = build_summary_uncertainty_rows(rows, metrics=metric_list)
    comparison_rows = build_agent_vs_best_baseline_rows(rows, metrics=metric_list)

    summary_csv_path = write_csv_rows(
        output_root / "summary_uncertainty.csv",
        summary_rows,
        columns=SUMMARY_UNCERTAINTY_COLUMNS,
    )
    summary_json_path = write_json_payload(
        output_root / "summary_uncertainty.json",
        {
            "source_protocol_results_csv": protocol_results_source_path,
            "metrics": list(metric_list),
            "method": "completed-run t-interval summary",
            "rows": summary_rows,
        },
    )
    summary_markdown_path = output_root / "summary_uncertainty.md"
    summary_markdown_path.write_text(
        results_to_markdown(summary_rows, columns=SUMMARY_UNCERTAINTY_COLUMNS),
        encoding="utf-8",
    )

    comparison_csv_path = write_csv_rows(
        output_root / "agent_vs_best_baseline.csv",
        comparison_rows,
        columns=PAIRED_COMPARISON_COLUMNS,
    )
    comparison_json_path = write_json_payload(
        output_root / "agent_vs_best_baseline.json",
        {
            "source_protocol_results_csv": protocol_results_source_path,
            "metrics": list(metric_list),
            "method": "paired agent-minus-best-baseline comparison with exact two-sided sign test",
            "rows": comparison_rows,
        },
    )
    comparison_markdown_path = output_root / "agent_vs_best_baseline.md"
    comparison_markdown_path.write_text(
        results_to_markdown(comparison_rows, columns=PAIRED_COMPARISON_COLUMNS),
        encoding="utf-8",
    )

    summary_latex_path = tables_dir / "summary_uncertainty_overall_score.tex"
    summary_latex_path.write_text(
        render_summary_uncertainty_latex_table(summary_rows),
        encoding="utf-8",
    )
    comparison_latex_path = tables_dir / "agent_vs_best_baseline_overall_score.tex"
    comparison_latex_path.write_text(
        render_agent_vs_best_baseline_latex_table(comparison_rows),
        encoding="utf-8",
    )
    statistical_methods_markdown_path = methods_dir / "statistical_methods.md"
    statistical_methods_markdown_path.write_text(
        render_statistical_methods_markdown(
            protocol_results_source_path=protocol_results_source_path,
            metrics=metric_list,
        ),
        encoding="utf-8",
    )
    statistical_methods_latex_path = methods_dir / "statistical_methods.tex"
    statistical_methods_latex_path.write_text(
        render_statistical_methods_latex(
            protocol_results_source_path=protocol_results_source_path,
            metrics=metric_list,
        ),
        encoding="utf-8",
    )

    readme_path = output_root / "README.md"
    readme_path.write_text(
        render_statistical_artifacts_readme(
            protocol_results_source_path=protocol_results_source_path,
            summary_row_count=len(summary_rows),
            comparison_row_count=len(comparison_rows),
        ),
        encoding="utf-8",
    )

    return {
        "readme": readme_path,
        "summary_uncertainty_csv": summary_csv_path,
        "summary_uncertainty_json": summary_json_path,
        "summary_uncertainty_markdown": summary_markdown_path,
        "agent_vs_best_baseline_csv": comparison_csv_path,
        "agent_vs_best_baseline_json": comparison_json_path,
        "agent_vs_best_baseline_markdown": comparison_markdown_path,
        "summary_uncertainty_latex": summary_latex_path,
        "agent_vs_best_baseline_latex": comparison_latex_path,
        "statistical_methods_markdown": statistical_methods_markdown_path,
        "statistical_methods_latex": statistical_methods_latex_path,
    }
