from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import nbformat

from finds_agentbench.scoring import balanced_accuracy


FEATURE_COLUMNS = [
    "ret_1d",
    "ret_5d",
    "momentum_20d",
    "volatility_10d",
    "market_regime_proxy",
]


def probability_from_momentum(momentum_20d: float, volatility_10d: float) -> float:
    scaled = momentum_20d / max(volatility_10d, 1e-6)
    probability = 0.5 + max(min(0.04 * scaled, 0.2), -0.2)
    return min(max(probability, 0.05), 0.95)


def write_momentum_predictions(features_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with features_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["row_id", "prediction", "probability"])
            writer.writeheader()
            for row in reader:
                probability = probability_from_momentum(
                    float(row["momentum_20d"]),
                    float(row["volatility_10d"]),
                )
                writer.writerow(
                    {
                        "row_id": row["row_id"],
                        "prediction": "1" if probability >= 0.5 else "0",
                        "probability": f"{probability:.8f}",
                    }
                )


def write_momentum_writeup(output_path: Path) -> None:
    output_path.write_text(
        "\n".join(
            [
                "# Momentum Baseline",
                "",
                "This baseline predicts the private holdout with a simple point-in-time momentum rule.",
                "It uses `momentum_20d` scaled by `volatility_10d` to produce a bounded probability.",
                "Rows with probability at least 0.5 are classified as positive next-day return.",
                "",
                "The baseline does not use private labels, answer keys, future returns, or random splits.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_momentum_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Momentum Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "assert Path('predictions.csv').exists(), 'missing predictions.csv'",
                    "assert Path('writeup.md').exists(), 'missing writeup.md'",
                    "print('Momentum baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def write_momentum_submission_artifacts(features_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_momentum_predictions(features_path, output_dir / "predictions.csv")
    write_momentum_writeup(output_dir / "writeup.md")
    write_momentum_notebook(output_dir / "notebook.ipynb")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def feature_matrix(rows: list[dict[str, str]]) -> list[list[float]]:
    return [[float(row[column]) for column in FEATURE_COLUMNS] for row in rows]


def labels(rows: list[dict[str, str]]) -> list[int]:
    return [int(row["next_day_positive_return"]) for row in rows]


def choose_threshold(y_true: list[int], probabilities: list[float]) -> tuple[float, float]:
    candidates = sorted({round(value, 6) for value in probabilities})
    candidates.extend([0.5])
    best_threshold = 0.5
    best_score = -1.0
    for threshold in sorted(set(candidates)):
        predictions = [1 if probability >= threshold else 0 for probability in probabilities]
        score = balanced_accuracy(y_true, predictions)
        if score > best_score:
            best_threshold = threshold
            best_score = score
    return best_threshold, best_score


def train_logistic_model(train_public_path: Path, *, random_state: int = 11):
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The logistic baseline requires scikit-learn. Install project ML dependencies first."
        ) from exc

    rows = read_csv_rows(train_public_path)
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "public_validation"]
    if not train_rows:
        raise ValueError("No train rows found in train_public data.")
    if not validation_rows:
        raise ValueError("No public_validation rows found in train_public data.")

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=random_state),
    )
    model.fit(feature_matrix(train_rows), labels(train_rows))
    validation_probabilities = [
        float(value) for value in model.predict_proba(feature_matrix(validation_rows))[:, 1]
    ]
    threshold, validation_balanced_accuracy = choose_threshold(
        labels(validation_rows),
        validation_probabilities,
    )
    return model, {
        "feature_columns": FEATURE_COLUMNS,
        "random_state": random_state,
        "train_rows": len(train_rows),
        "public_validation_rows": len(validation_rows),
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def write_logistic_predictions(
    model,
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
) -> None:
    holdout_rows = read_csv_rows(holdout_features_path)
    probabilities = [float(value) for value in model.predict_proba(feature_matrix(holdout_rows))[:, 1]]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "prediction", "probability"])
        writer.writeheader()
        for row, probability in zip(holdout_rows, probabilities):
            writer.writerow(
                {
                    "row_id": row["row_id"],
                    "prediction": "1" if probability >= threshold else "0",
                    "probability": f"{probability:.8f}",
                }
            )


def write_logistic_writeup(output_path: Path, metadata: dict) -> None:
    output_path.write_text(
        "\n".join(
            [
                "# Logistic Regression Baseline",
                "",
                "This baseline trains a logistic regression model using only the chronological train split.",
                "A standard scaler is fit inside the training pipeline, so public validation and private holdout rows are transformed using train-fitted parameters.",
                "The classification threshold is selected on the public validation split only.",
                "",
                f"Selected threshold: `{metadata['selected_threshold']}`.",
                f"Public validation balanced accuracy: `{metadata['public_validation_balanced_accuracy']:.6f}`.",
                "",
                "The baseline does not read private labels or answer keys during prediction generation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_logistic_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Logistic Regression Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "for path in ['predictions.csv', 'writeup.md', 'baseline_metadata.json']:",
                    "    assert Path(path).exists(), f'missing {path}'",
                    "print('Logistic regression baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def write_logistic_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 11,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_logistic_model(train_public_path, random_state=random_state)
    write_logistic_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    write_logistic_writeup(output_dir / "writeup.md", metadata)
    write_logistic_notebook(output_dir / "notebook.ipynb")
    (output_dir / "baseline_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def event_probability(row: dict[str, str]) -> float:
    event_type_weight = {
        "earnings": 0.95,
        "macro": 0.55,
        "guidance": 1.20,
    }.get(row["event_type"], 0.75)
    signal = (
        event_type_weight * float(row["event_surprise"]) * float(row["event_importance"])
        + 0.35 * float(row["sentiment_score"])
        + 3.0 * float(row["pre_event_momentum_5d"])
        - 4.0 * float(row["volatility_20d"])
        + 0.20 * float(row["sector_stress"])
    )
    probability = 1.0 / (1.0 + math.exp(-signal))
    return min(max(probability, 0.03), 0.97)


def write_event_rule_predictions(features_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with features_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["row_id", "prediction", "probability"])
            writer.writeheader()
            for row in reader:
                probability = event_probability(row)
                writer.writerow(
                    {
                        "row_id": row["row_id"],
                        "prediction": "1" if probability >= 0.5 else "0",
                        "probability": f"{probability:.8f}",
                    }
                )


def write_event_rule_writeup(output_path: Path) -> None:
    output_path.write_text(
        "\n".join(
            [
                "# Event Response Rule Baseline",
                "",
                "This baseline predicts event response direction using only",
                "label-free holdout features.",
                "The rule combines event surprise, event importance, sentiment, recent momentum,",
                "volatility, and sector stress into a bounded probability.",
                "",
                "It does not read private labels, answer keys, next-day returns, or future events.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_event_rule_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Event Response Rule Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "assert Path('predictions.csv').exists(), 'missing predictions.csv'",
                    "assert Path('writeup.md').exists(), 'missing writeup.md'",
                    "print('Event response rule baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def write_event_rule_submission_artifacts(features_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_event_rule_predictions(features_path, output_dir / "predictions.csv")
    write_event_rule_writeup(output_dir / "writeup.md")
    write_event_rule_notebook(output_dir / "notebook.ipynb")
