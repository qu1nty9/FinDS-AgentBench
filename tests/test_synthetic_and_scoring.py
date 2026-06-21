from pathlib import Path

import csv

from finds_agentbench.scoring import (
    score_leakage_audit_submission,
    score_synthetic_event_response_submission,
    score_synthetic_market_submission,
)
from finds_agentbench.synthetic import (
    write_leakage_audit_task,
    write_synthetic_event_response_task,
    write_synthetic_market_direction_task,
)


def test_generate_leakage_audit_task(tmp_path: Path):
    output_dir = tmp_path / "public"
    private_dir = tmp_path / "private"

    paths = write_leakage_audit_task(output_dir=output_dir, private_dir=private_dir, seed=7)

    assert paths.public_panel.exists()
    assert paths.flawed_workflow.exists()
    assert paths.answer_key.exists()

    panel_text = paths.public_panel.read_text(encoding="utf-8")
    assert "feature_future_return_leak" in panel_text
    assert "private_temporal_holdout" in panel_text


def test_score_expert_leakage_audit_submission(tmp_path: Path):
    paths = write_leakage_audit_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        seed=7,
    )

    score = score_leakage_audit_submission(
        submission_dir="baselines/leakage_audit_temporal_split_v0/expert_submission",
        answer_key_path=paths.answer_key,
    )

    assert score.execution_success == 1.0
    assert score.leakage_identification == 1.0
    assert score.validation_correction == 1.0
    assert score.before_after_quantification == 1.0
    assert score.overall_score == 1.0


def test_generate_synthetic_market_direction_task(tmp_path: Path):
    paths = write_synthetic_market_direction_task(
        output_dir=tmp_path / "public_market",
        private_dir=tmp_path / "private_market",
        seed=11,
    )

    assert paths.train_public.exists()
    assert paths.private_holdout_features.exists()
    assert paths.sample_submission.exists()
    assert paths.answer_key.exists()

    with paths.private_holdout_features.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert "next_day_positive_return" not in (reader.fieldnames or [])
        assert "next_day_return" not in (reader.fieldnames or [])

    with paths.answer_key.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert {"row_id", "next_day_positive_return", "next_day_return"}.issubset(
            set(reader.fieldnames or [])
        )


def test_score_synthetic_market_submission(tmp_path: Path):
    paths = write_synthetic_market_direction_task(
        output_dir=tmp_path / "public_market",
        private_dir=tmp_path / "private_market",
        seed=11,
    )
    submission = tmp_path / "predictions.csv"

    with paths.private_holdout_features.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with submission.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["row_id", "prediction", "probability"])
            writer.writeheader()
            for row in reader:
                probability = 0.6 if float(row["momentum_20d"]) >= 0 else 0.4
                writer.writerow(
                    {
                        "row_id": row["row_id"],
                        "prediction": "1" if probability >= 0.5 else "0",
                        "probability": str(probability),
                    }
                )

    score = score_synthetic_market_submission(
        submission_path=submission,
        answer_key_path=paths.answer_key,
    )

    assert score.execution_success == 1.0
    assert score.rows_scored > 0
    assert score.balanced_accuracy is not None
    assert 0.0 <= score.balanced_accuracy <= 1.0
    assert score.roc_auc is not None
    assert 0.0 <= score.roc_auc <= 1.0


def test_generate_synthetic_event_response_task(tmp_path: Path):
    paths = write_synthetic_event_response_task(
        output_dir=tmp_path / "public_event",
        private_dir=tmp_path / "private_event",
        seed=23,
    )

    assert paths.train_public.exists()
    assert paths.private_holdout_features.exists()
    assert paths.sample_submission.exists()
    assert paths.answer_key.exists()

    with paths.private_holdout_features.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert "event_reaction_positive" not in (reader.fieldnames or [])
        assert "next_day_return" not in (reader.fieldnames or [])

    with paths.answer_key.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert {"row_id", "event_reaction_positive", "next_day_return"}.issubset(
            set(reader.fieldnames or [])
        )


def test_score_synthetic_event_response_submission(tmp_path: Path):
    paths = write_synthetic_event_response_task(
        output_dir=tmp_path / "public_event",
        private_dir=tmp_path / "private_event",
        seed=23,
    )
    submission = tmp_path / "event_predictions.csv"

    with paths.private_holdout_features.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with submission.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["row_id", "prediction", "probability"])
            writer.writeheader()
            for row in reader:
                probability = 0.65 if float(row["event_surprise"]) >= 0 else 0.35
                writer.writerow(
                    {
                        "row_id": row["row_id"],
                        "prediction": "1" if probability >= 0.5 else "0",
                        "probability": str(probability),
                    }
                )

    score = score_synthetic_event_response_submission(
        submission_path=submission,
        answer_key_path=paths.answer_key,
    )

    assert score.task_id == "synthetic_event_response_v0"
    assert score.execution_success == 1.0
    assert score.rows_scored > 0
    assert score.balanced_accuracy is not None
    assert 0.0 <= score.balanced_accuracy <= 1.0
    assert score.roc_auc is not None
    assert 0.0 <= score.roc_auc <= 1.0
