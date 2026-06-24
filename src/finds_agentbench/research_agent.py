from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

import nbformat

from finds_agentbench.baselines import (
    choose_threshold as choose_market_threshold,
    event_probability,
    labels as market_labels,
    probability_from_momentum,
    read_csv_rows,
    write_logistic_submission_artifacts,
)
from finds_agentbench.treasury import (
    write_yield_extra_trees_submission_artifacts,
    write_yield_logistic_submission_artifacts,
    write_yield_previous_day_direction_submission_artifacts,
    write_yield_random_forest_submission_artifacts,
)
from finds_agentbench.yield_curve import (
    write_curve_extra_trees_submission_artifacts,
    write_curve_logistic_submission_artifacts,
    write_curve_previous_day_direction_submission_artifacts,
    write_curve_random_forest_submission_artifacts,
)
import finds_agentbench.curve_10y3mo as curve_10y3mo_module
from finds_agentbench.front_end import (
    write_front_end_extra_trees_submission_artifacts,
    write_front_end_logistic_submission_artifacts,
    write_front_end_previous_day_direction_submission_artifacts,
    write_front_end_random_forest_submission_artifacts,
)
from finds_agentbench.usd_broad import (
    write_usd_broad_extra_trees_submission_artifacts,
    write_usd_broad_logistic_submission_artifacts,
    write_usd_broad_previous_day_direction_submission_artifacts,
    write_usd_broad_random_forest_submission_artifacts,
)
from finds_agentbench.usd_relative import (
    write_usd_relative_extra_trees_submission_artifacts,
    write_usd_relative_logistic_submission_artifacts,
    write_usd_relative_previous_day_direction_submission_artifacts,
    write_usd_relative_random_forest_submission_artifacts,
)


SYNTHETIC_MARKET_TASK_ID = "synthetic_market_direction_v0"
SYNTHETIC_EVENT_TASK_ID = "synthetic_event_response_v0"
TREASURY_TASK_ID = "yield_direction_treasury10y_v0"
TREASURY_CURVE_TASK_ID = "yield_curve_10y2y_steepening_v0"
TREASURY_CURVE_10Y3MO_TASK_ID = "yield_curve_10y3mo_steepening_v0"
FRONT_END_TASK_ID = "front_end_spread_widening_v0"
USD_BROAD_TASK_ID = "usd_broad_direction_v0"
USD_RELATIVE_TASK_ID = "usd_afe_vs_eme_relative_direction_v0"

PREDICTIONS_FILENAME = "predictions.csv"
METADATA_FILENAME = "baseline_metadata.json"


@dataclass(frozen=True)
class CandidateResult:
    candidate_id: str
    candidate_label: str
    complexity_rank: int
    output_dir: Path
    metadata: dict[str, Any]

    @property
    def public_validation_balanced_accuracy(self) -> float:
        return float(self.metadata["public_validation_balanced_accuracy"])


def run_research_sweep_agent(
    *,
    task_id: str,
    seed: int,
    train_public_path: Path,
    holdout_features_path: Path,
    submission_dir: Path,
) -> dict[str, Any]:
    submission_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="finds_research_agent_") as temp_dir:
        temp_root = Path(temp_dir)
        candidates = build_task_candidates(
            task_id=task_id,
            seed=seed,
            train_public_path=train_public_path,
            holdout_features_path=holdout_features_path,
            temp_root=temp_root,
        )
        selected = select_best_candidate(candidates)
        shutil.copy2(selected.output_dir / PREDICTIONS_FILENAME, submission_dir / PREDICTIONS_FILENAME)

    final_metadata = build_final_metadata(
        task_id=task_id,
        seed=seed,
        candidates=candidates,
        selected=selected,
    )
    write_final_metadata(submission_dir / METADATA_FILENAME, final_metadata)
    write_research_sweep_writeup(submission_dir / "writeup.md", final_metadata)
    write_research_sweep_notebook(submission_dir / "notebook.ipynb")
    return final_metadata


def build_task_candidates(
    *,
    task_id: str,
    seed: int,
    train_public_path: Path,
    holdout_features_path: Path,
    temp_root: Path,
) -> list[CandidateResult]:
    if task_id == SYNTHETIC_MARKET_TASK_ID:
        return [
            build_market_momentum_candidate(
                train_public_path=train_public_path,
                holdout_features_path=holdout_features_path,
                output_dir=temp_root / "momentum_baseline",
            ),
            build_market_logistic_candidate(
                seed=seed,
                train_public_path=train_public_path,
                holdout_features_path=holdout_features_path,
                output_dir=temp_root / "logistic_regression_baseline",
            ),
        ]

    if task_id == SYNTHETIC_EVENT_TASK_ID:
        return [
            build_event_rule_candidate(
                train_public_path=train_public_path,
                holdout_features_path=holdout_features_path,
                output_dir=temp_root / "event_rule_baseline",
            )
        ]

    if task_id == TREASURY_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: write_yield_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: write_yield_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: write_yield_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: write_yield_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    if task_id == TREASURY_CURVE_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: write_curve_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: write_curve_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: write_curve_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: write_curve_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    if task_id == TREASURY_CURVE_10Y3MO_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: curve_10y3mo_module.write_curve_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: curve_10y3mo_module.write_curve_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: curve_10y3mo_module.write_curve_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: curve_10y3mo_module.write_curve_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    if task_id == FRONT_END_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: write_front_end_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: write_front_end_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: write_front_end_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: write_front_end_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    if task_id == USD_BROAD_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: write_usd_broad_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: write_usd_broad_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: write_usd_broad_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: write_usd_broad_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    if task_id == USD_RELATIVE_TASK_ID:
        return build_candidate_family(
            temp_root=temp_root,
            candidates=(
                (
                    "previous_day_direction_baseline",
                    "Previous-Day Direction Rule",
                    0,
                    lambda output_dir: write_usd_relative_previous_day_direction_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                    ),
                ),
                (
                    "logistic_regression_baseline",
                    "Logistic Regression",
                    1,
                    lambda output_dir: write_usd_relative_logistic_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "random_forest_baseline",
                    "Random Forest",
                    2,
                    lambda output_dir: write_usd_relative_random_forest_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
                (
                    "extra_trees_baseline",
                    "Extra Trees",
                    3,
                    lambda output_dir: write_usd_relative_extra_trees_submission_artifacts(
                        train_public_path=train_public_path,
                        holdout_features_path=holdout_features_path,
                        output_dir=output_dir,
                        random_state=seed,
                    ),
                ),
            ),
        )

    raise ValueError(f"Unsupported task_id for research sweep env-agent: {task_id}")


def build_candidate_family(
    *,
    temp_root: Path,
    candidates: tuple[
        tuple[str, str, int, Callable[[Path], dict[str, Any]]],
        ...,
    ],
) -> list[CandidateResult]:
    results: list[CandidateResult] = []
    for candidate_id, candidate_label, complexity_rank, writer in candidates:
        output_dir = temp_root / candidate_id
        metadata = writer(output_dir)
        results.append(
            CandidateResult(
                candidate_id=candidate_id,
                candidate_label=candidate_label,
                complexity_rank=complexity_rank,
                output_dir=output_dir,
                metadata=metadata,
            )
        )
    return results


def build_market_momentum_candidate(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> CandidateResult:
    rows = read_csv_rows(train_public_path)
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "public_validation"]
    validation_probabilities = [
        probability_from_momentum(
            float(row["momentum_20d"]),
            float(row["volatility_10d"]),
        )
        for row in validation_rows
    ]
    threshold, validation_balanced_accuracy = choose_market_threshold(
        market_labels(validation_rows),
        validation_probabilities,
    )
    holdout_rows = read_csv_rows(holdout_features_path)
    holdout_probabilities = [
        probability_from_momentum(
            float(row["momentum_20d"]),
            float(row["volatility_10d"]),
        )
        for row in holdout_rows
    ]
    write_probability_csv(
        rows=holdout_rows,
        probabilities=holdout_probabilities,
        threshold=threshold,
        output_path=output_dir / PREDICTIONS_FILENAME,
    )
    metadata = {
        "baseline_family": "momentum_rule",
        "feature_columns": ["momentum_20d", "volatility_10d"],
        "train_rows": len(train_rows),
        "public_validation_rows": len(validation_rows),
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
        "probability_rule": "bounded linear scaling of momentum_20d / volatility_10d",
    }
    return CandidateResult(
        candidate_id="momentum_baseline",
        candidate_label="Momentum Rule",
        complexity_rank=0,
        output_dir=output_dir,
        metadata=metadata,
    )


def build_market_logistic_candidate(
    *,
    seed: int,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> CandidateResult:
    metadata = write_logistic_submission_artifacts(
        train_public_path=train_public_path,
        holdout_features_path=holdout_features_path,
        output_dir=output_dir,
        random_state=seed,
    )
    enriched_metadata = {"baseline_family": "logistic_regression", **metadata}
    return CandidateResult(
        candidate_id="logistic_regression_baseline",
        candidate_label="Logistic Regression",
        complexity_rank=1,
        output_dir=output_dir,
        metadata=enriched_metadata,
    )


def build_event_rule_candidate(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> CandidateResult:
    rows = read_csv_rows(train_public_path)
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "public_validation"]
    validation_probabilities = [event_probability(row) for row in validation_rows]
    threshold, validation_balanced_accuracy = choose_market_threshold(
        market_labels(validation_rows),
        validation_probabilities,
    )
    holdout_rows = read_csv_rows(holdout_features_path)
    holdout_probabilities = [event_probability(row) for row in holdout_rows]
    write_probability_csv(
        rows=holdout_rows,
        probabilities=holdout_probabilities,
        threshold=threshold,
        output_path=output_dir / PREDICTIONS_FILENAME,
    )
    metadata = {
        "baseline_family": "event_rule",
        "feature_columns": [
            "event_type",
            "event_surprise",
            "sentiment_score",
            "event_importance",
            "pre_event_momentum_5d",
            "volatility_20d",
            "sector_stress",
        ],
        "train_rows": len(train_rows),
        "public_validation_rows": len(validation_rows),
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
        "probability_rule": "sigmoid rule over event surprise, sentiment, importance, momentum, volatility, and sector stress",
    }
    return CandidateResult(
        candidate_id="event_rule_baseline",
        candidate_label="Event Rule",
        complexity_rank=0,
        output_dir=output_dir,
        metadata=metadata,
    )


def write_probability_csv(
    *,
    rows: list[dict[str, str]],
    probabilities: list[float],
    threshold: float,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "prediction", "probability"])
        writer.writeheader()
        for row, probability in zip(rows, probabilities, strict=True):
            writer.writerow(
                {
                    "row_id": row["row_id"],
                    "prediction": "1" if probability >= threshold else "0",
                    "probability": f"{float(probability):.8f}",
                }
            )


def select_best_candidate(candidates: list[CandidateResult]) -> CandidateResult:
    ranking = ranked_candidates(candidates)
    return ranking[0]


def ranked_candidates(candidates: list[CandidateResult]) -> list[CandidateResult]:
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.public_validation_balanced_accuracy,
            -candidate.complexity_rank,
        ),
        reverse=True,
    )


def build_final_metadata(
    *,
    task_id: str,
    seed: int,
    candidates: list[CandidateResult],
    selected: CandidateResult,
) -> dict[str, Any]:
    ranking = ranked_candidates(candidates)
    return {
        "agent_family": "research_sweep_env_agent",
        "task_id": task_id,
        "run_seed": seed,
        "selection_metric": "public_validation_balanced_accuracy",
        "selection_protocol": (
            "Candidate comparison, threshold calibration, and model selection use only "
            "chronological train/public_validation rows."
        ),
        "selected_candidate_id": selected.candidate_id,
        "selected_candidate_label": selected.candidate_label,
        "selected_public_validation_balanced_accuracy": selected.public_validation_balanced_accuracy,
        "selected_candidate_metadata": selected.metadata,
        "candidate_ranking": [
            {
                "rank": index,
                "candidate_id": candidate.candidate_id,
                "candidate_label": candidate.candidate_label,
                "public_validation_balanced_accuracy": candidate.public_validation_balanced_accuracy,
                "complexity_rank": candidate.complexity_rank,
                "metadata": candidate.metadata,
            }
            for index, candidate in enumerate(ranking, start=1)
        ],
    }


def write_final_metadata(output_path: Path, metadata: dict[str, Any]) -> None:
    output_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_research_sweep_writeup(output_path: Path, metadata: dict[str, Any]) -> None:
    task_lines = {
        SYNTHETIC_MARKET_TASK_ID: [
            "This agent compares a calibrated momentum rule against a logistic regression fit on the chronological train split.",
            "The sweep uses only point-in-time market features and public validation labels to pick the final candidate.",
        ],
        SYNTHETIC_EVENT_TASK_ID: [
            "This task currently exposes one public reference candidate: the event-aware rule baseline.",
            "The agent still calibrates its threshold on public validation and records the result in a benchmark-ready trace.",
        ],
        TREASURY_TASK_ID: [
            "This agent compares a previous-day rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates are fit or calibrated on the chronological train split and ranked by public validation balanced accuracy.",
        ],
        TREASURY_CURVE_TASK_ID: [
            "This agent compares a previous-day slope-change rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates use only point-in-time H.15 features and are ranked by public validation balanced accuracy.",
        ],
        TREASURY_CURVE_10Y3MO_TASK_ID: [
            "This agent compares a previous-day 10Y-3M slope-change rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates use only point-in-time H.15 features and are ranked by public validation balanced accuracy.",
        ],
        FRONT_END_TASK_ID: [
            "This agent compares a previous-day spread-change rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates use only point-in-time H.15 front-end rates features and are ranked by public validation balanced accuracy.",
        ],
        USD_BROAD_TASK_ID: [
            "This agent compares a previous-day rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates use only point-in-time dollar-index and rates features available at prediction time.",
        ],
        USD_RELATIVE_TASK_ID: [
            "This agent compares a previous-day rule, logistic regression, random forest, and extra-trees ensemble.",
            "All candidates use only point-in-time macro-financial features available by the prediction timestamp.",
        ],
    }
    selected_metadata = metadata["selected_candidate_metadata"]
    ranking_lines = [
        "| Rank | Candidate | Public validation balanced accuracy |",
        "| --- | --- | ---: |",
    ]
    for candidate in metadata["candidate_ranking"]:
        ranking_lines.append(
            "| "
            f"{candidate['rank']} | {candidate['candidate_label']} | "
            f"{candidate['public_validation_balanced_accuracy']:.6f} |"
        )

    selected_features = ", ".join(selected_metadata.get("feature_columns", []))
    lines = [
        "# Research Sweep Env-Agent",
        "",
        f"Task: `{metadata['task_id']}`.",
        f"Run seed: `{metadata['run_seed']}`.",
        "",
        *task_lines.get(metadata["task_id"], []),
        "",
        f"Selected candidate: `{metadata['selected_candidate_label']}` (`{metadata['selected_candidate_id']}`).",
        "Selection metric: "
        f"`{metadata['selection_metric']} = {metadata['selected_public_validation_balanced_accuracy']:.6f}`.",
        f"Selected threshold: `{selected_metadata.get('selected_threshold', 'n/a')}`.",
        f"Selected feature set: `{selected_features}`.",
        "",
        "## Candidate Leaderboard",
        "",
        *ranking_lines,
        "",
        "The agent does not read private labels, answer keys, or future target values.",
        "Private holdout predictions are generated only after candidate selection on train/public-validation data.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_research_sweep_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Research Sweep Env-Agent Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "import json",
                    "from pathlib import Path",
                    "",
                    "for path in ['predictions.csv', 'writeup.md', 'baseline_metadata.json']:",
                    "    assert Path(path).exists(), f'missing {path}'",
                    "metadata = json.loads(Path('baseline_metadata.json').read_text(encoding='utf-8'))",
                    "print(metadata['selected_candidate_id'])",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)
