from __future__ import annotations

import csv
from pathlib import Path

import nbformat


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

