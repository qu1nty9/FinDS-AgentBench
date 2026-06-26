from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


PAPER_TASK_LABELS = {
    "synthetic_market_direction_v0": "Synthetic Market",
    "synthetic_event_response_v0": "Synthetic Event",
    "yield_direction_treasury10y_v0": "Treasury 10Y Direction",
    "yield_curve_10y2y_steepening_v0": "Treasury 10Y-2Y Curve",
    "yield_curve_10y3mo_steepening_v0": "Treasury 10Y-3M Curve",
    "front_end_spread_widening_v0": "Front-End Spread",
    "usd_broad_direction_v0": "USD Broad",
    "usd_afe_vs_eme_relative_direction_v0": "USD AFE vs. EME",
}

PAPER_AGENT_LABELS = {
    "momentum_baseline": "Momentum",
    "logistic_regression_baseline": "LogReg",
    "event_rule_baseline": "Event Rule",
    "previous_day_direction_baseline": "Prev-Day",
    "random_forest_baseline": "Rand. Forest",
    "extra_trees_baseline": "Extra Trees",
    "momentum_env_agent": "Momentum Env-Agent",
    "market_research_sweep_env_agent": "Market Sweep Env-Agent",
    "event_rule_env_agent": "Event Rule Env-Agent",
    "treasury_logistic_env_agent": "Treasury LogReg Env-Agent",
    "treasury_research_sweep_env_agent": "Treasury 10Y Sweep Env-Agent",
    "treasury_curve_research_sweep_env_agent": "Treasury 10Y-2Y Sweep Env-Agent",
    "treasury_curve_10y3mo_research_sweep_env_agent": "Treasury 10Y-3M Sweep Env-Agent",
    "treasury_front_end_research_sweep_env_agent": "Front-End Sweep Env-Agent",
    "usd_broad_logistic_env_agent": "USD LogReg Env-Agent",
    "usd_research_sweep_env_agent": "USD Sweep Env-Agent",
    "usd_relative_research_sweep_env_agent": "USD Relative Sweep Env-Agent",
}

RUN_TYPE_COLORS = {
    "baseline": "#4f81bd",
    "agent": "#c0504d",
    "human": "#9bbb59",
    "expert": "#8064a2",
}


def load_reference_results(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def format_float(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def metric_pm(mean_value: Any, std_value: Any, digits: int = 3) -> str:
    return f"\\ensuremath{{{format_float(mean_value, digits)} \\pm {format_float(std_value, digits)}}}"


def latex_escape(value: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    escaped = value
    for source, target in replacements.items():
        escaped = escaped.replace(source, target)
    return escaped


def pretty_task_label(task_id: str) -> str:
    return PAPER_TASK_LABELS.get(task_id, task_id.replace("_", " "))


def pretty_agent_label(agent_id: str) -> str:
    return PAPER_AGENT_LABELS.get(agent_id, agent_id.replace("_", " "))


def protocol_slug(section_id: str) -> str:
    return section_id.replace("_", "-")


def render_section_latex_table(section: dict[str, Any]) -> str:
    rows = section["rows"]
    caption = (
        f"{section['title']} repeated-run summary. "
        "Means and sample standard deviations are computed over the configured seeds."
    )
    label = f"tab:{protocol_slug(section['section_id'])}"
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lllcccc}",
        "\\toprule",
        "Task & Agent & Type & $n$ & Overall & Balanced Acc. & ROC AUC \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    latex_escape(pretty_task_label(str(row["task_id"]))),
                    latex_escape(pretty_agent_label(str(row["agent_id"]))),
                    latex_escape(str(row["run_type"]).title()),
                    str(row["run_count"]),
                    metric_pm(row["score.overall_score.mean"], row["score.overall_score.std"]),
                    metric_pm(
                        row["score.balanced_accuracy.mean"],
                        row["score.balanced_accuracy.std"],
                    ),
                    metric_pm(row["score.roc_auc.mean"], row["score.roc_auc.std"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "}",
            f"\\caption{{{latex_escape(caption)}}}",
            f"\\label{{{label}}}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def _svg_x(value: float, *, x_min: float, x_max: float, left: int, width: int) -> float:
    if x_max <= x_min:
        return float(left)
    return left + ((value - x_min) / (x_max - x_min)) * width


def render_section_svg(section: dict[str, Any]) -> str:
    rows = section["rows"]
    left_margin = 310
    right_margin = 40
    top_margin = 70
    bottom_margin = 50
    row_height = 34
    bar_height = 18
    width = 1040
    height = top_margin + bottom_margin + row_height * max(len(rows), 1)
    chart_width = width - left_margin - right_margin
    means = [float(row["score.overall_score.mean"]) for row in rows]
    stds = [float(row["score.overall_score.std"]) for row in rows]
    x_min = 0.0
    x_max = max(0.75, max((mean + std) for mean, std in zip(means, stds, strict=True)) + 0.03)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(section["title"])} overall score chart">',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="{left_margin}" y="30" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#111111">{escape(section["title"])}</text>',
        f'<text x="{left_margin}" y="50" font-size="12" font-family="Arial, Helvetica, sans-serif" fill="#555555">Overall score mean with sample-standard-deviation error bars</text>',
    ]

    axis_y = height - bottom_margin
    parts.append(
        f'<line x1="{left_margin}" y1="{axis_y}" x2="{left_margin + chart_width}" y2="{axis_y}" stroke="#444444" stroke-width="1"/>'
    )
    for tick in range(0, 9):
        value = tick / 10
        if value > x_max:
            break
        x = _svg_x(value, x_min=x_min, x_max=x_max, left=left_margin, width=chart_width)
        parts.append(
            f'<line x1="{x:.2f}" y1="{axis_y}" x2="{x:.2f}" y2="{axis_y + 6}" stroke="#444444" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{axis_y + 22}" text-anchor="middle" font-size="11" font-family="Arial, Helvetica, sans-serif" fill="#555555">{value:.1f}</text>'
        )

    legend_x = width - 210
    parts.extend(
        [
            f'<rect x="{legend_x}" y="18" width="12" height="12" fill="{RUN_TYPE_COLORS["baseline"]}" />',
            f'<text x="{legend_x + 18}" y="28" font-size="12" font-family="Arial, Helvetica, sans-serif" fill="#333333">Baseline</text>',
            f'<rect x="{legend_x}" y="38" width="12" height="12" fill="{RUN_TYPE_COLORS["agent"]}" />',
            f'<text x="{legend_x + 18}" y="48" font-size="12" font-family="Arial, Helvetica, sans-serif" fill="#333333">Agent</text>',
        ]
    )

    for index, row in enumerate(rows):
        mean_value = float(row["score.overall_score.mean"])
        std_value = float(row["score.overall_score.std"])
        y_center = top_margin + index * row_height + row_height / 2
        bar_y = y_center - bar_height / 2
        label = f"{pretty_task_label(str(row['task_id']))} | {pretty_agent_label(str(row['agent_id']))}"
        color = RUN_TYPE_COLORS.get(str(row["run_type"]), "#7f7f7f")

        parts.append(
            f'<text x="{left_margin - 12}" y="{y_center + 4:.2f}" text-anchor="end" font-size="12" font-family="Arial, Helvetica, sans-serif" fill="#222222">{escape(label)}</text>'
        )
        bar_end = _svg_x(
            mean_value,
            x_min=x_min,
            x_max=x_max,
            left=left_margin,
            width=chart_width,
        )
        err_left = _svg_x(
            max(x_min, mean_value - std_value),
            x_min=x_min,
            x_max=x_max,
            left=left_margin,
            width=chart_width,
        )
        err_right = _svg_x(
            min(x_max, mean_value + std_value),
            x_min=x_min,
            x_max=x_max,
            left=left_margin,
            width=chart_width,
        )
        parts.append(
            f'<rect x="{left_margin}" y="{bar_y:.2f}" width="{bar_end - left_margin:.2f}" height="{bar_height}" rx="2" fill="{color}" opacity="0.9" />'
        )
        parts.append(
            f'<line x1="{err_left:.2f}" y1="{y_center:.2f}" x2="{err_right:.2f}" y2="{y_center:.2f}" stroke="#111111" stroke-width="1.5"/>'
        )
        parts.append(
            f'<line x1="{err_left:.2f}" y1="{y_center - 6:.2f}" x2="{err_left:.2f}" y2="{y_center + 6:.2f}" stroke="#111111" stroke-width="1.5"/>'
        )
        parts.append(
            f'<line x1="{err_right:.2f}" y1="{y_center - 6:.2f}" x2="{err_right:.2f}" y2="{y_center + 6:.2f}" stroke="#111111" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{bar_end + 8:.2f}" y="{y_center + 4:.2f}" font-size="11" font-family="Arial, Helvetica, sans-serif" fill="#333333">{mean_value:.3f} ± {std_value:.3f}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_paper_artifacts_readme(reference_results: dict[str, Any]) -> str:
    section_rows = []
    for section in reference_results["sections"]:
        section_id = str(section["section_id"])
        section_rows.append(
            f"| {section['title']} | `tables/{section_id}.tex` | `figures/{section_id}_overall_score.svg` |"
        )
    return "\n".join(
        [
            "# Paper Artifacts",
            "",
            "Paper-ready exports generated directly from `reference_results.json`.",
            "",
            "The LaTeX tables use `booktabs` commands (`\\toprule`, `\\midrule`, `\\bottomrule`).",
            "",
            "| Section | LaTeX Table | SVG Figure |",
            "| --- | --- | --- |",
            *section_rows,
            "",
        ]
    )


def build_paper_artifacts(
    *,
    reference_results_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    reference_results = load_reference_results(reference_results_path)
    output_root = Path(output_dir)
    tables_dir = output_root / "tables"
    figures_dir = output_root / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for section in reference_results["sections"]:
        section_id = str(section["section_id"])
        table_path = tables_dir / f"{section_id}.tex"
        figure_path = figures_dir / f"{section_id}_overall_score.svg"
        table_path.write_text(render_section_latex_table(section), encoding="utf-8")
        figure_path.write_text(render_section_svg(section), encoding="utf-8")
        written[f"table:{section_id}"] = table_path
        written[f"figure:{section_id}"] = figure_path

    readme_path = output_root / "README.md"
    readme_path.write_text(render_paper_artifacts_readme(reference_results), encoding="utf-8")
    written["readme"] = readme_path
    return written
