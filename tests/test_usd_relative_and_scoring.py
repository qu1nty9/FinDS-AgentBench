import json
from pathlib import Path

import pandas as pd

from finds_agentbench.scoring import score_usd_afe_vs_eme_relative_submission
from finds_agentbench.usd_broad import write_usd_broad_direction_task
from finds_agentbench.usd_relative import (
    FEATURE_COLUMNS,
    train_usd_relative_extra_trees_model,
    train_usd_relative_previous_day_direction_baseline,
    train_usd_relative_random_forest_model,
    write_usd_relative_direction_task,
    write_usd_relative_extra_trees_submission_artifacts,
    write_usd_relative_logistic_submission_artifacts,
    write_usd_relative_previous_day_direction_submission_artifacts,
    write_usd_relative_random_forest_submission_artifacts,
)
from tests.treasury_test_utils import mock_usd_broad_source_frame


def test_write_usd_relative_direction_task(tmp_path: Path):
    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    assert paths.train_public.exists()
    assert paths.private_holdout_features.exists()
    assert paths.sample_submission.exists()
    assert paths.answer_key.exists()

    holdout = pd.read_csv(paths.private_holdout_features)
    assert "next_day_afe_outperforms_eme" not in holdout.columns
    assert "next_day_relative_return" not in holdout.columns
    assert set(FEATURE_COLUMNS).issubset(holdout.columns)

    answer_key = pd.read_csv(paths.answer_key)
    assert {
        "row_id",
        "next_day_afe_outperforms_eme",
        "next_day_relative_return",
    }.issubset(answer_key.columns)


def test_write_usd_relative_direction_task_reuses_matching_existing_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    public_dir = tmp_path / "public"
    private_dir = tmp_path / "private"
    initial_paths = write_usd_relative_direction_task(
        output_dir=public_dir,
        private_dir=private_dir,
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )
    metadata_before = initial_paths.metadata.read_text(encoding="utf-8")

    def fail_fetch(**kwargs):
        raise AssertionError(f"fetch_usd_relative_source_frame should not run: {kwargs}")

    monkeypatch.setattr("finds_agentbench.usd_relative.fetch_usd_relative_source_frame", fail_fetch)

    reused_paths = write_usd_relative_direction_task(
        output_dir=public_dir,
        private_dir=private_dir,
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )

    assert reused_paths == initial_paths
    assert reused_paths.metadata.read_text(encoding="utf-8") == metadata_before


def test_write_usd_relative_direction_task_derives_offline_from_existing_usd_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    usd_public_dir = tmp_path / "usd_public"
    usd_private_dir = tmp_path / "usd_private"
    write_usd_broad_direction_task(
        output_dir=usd_public_dir,
        private_dir=usd_private_dir,
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )

    def fail_fetch(**kwargs):
        raise AssertionError(f"fetch_usd_relative_source_frame should not run: {kwargs}")

    monkeypatch.setattr("finds_agentbench.usd_relative.fetch_usd_relative_source_frame", fail_fetch)

    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "relative_public",
        private_dir=tmp_path / "relative_private",
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
        usd_broad_train_public_path=usd_public_dir / "train_public.csv",
        usd_broad_holdout_features_path=usd_public_dir / "private_holdout_features.csv",
        usd_broad_metadata_path=usd_public_dir / "metadata.json",
    )

    metadata = json.loads(paths.metadata.read_text(encoding="utf-8"))
    assert metadata["source_mode"] == "derived_from_existing_usd_broad_snapshot"


def test_score_usd_afe_vs_eme_relative_submission(tmp_path: Path):
    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    holdout = pd.read_csv(paths.private_holdout_features)
    median_signal = float(holdout["afe_eme_relative_return_1d"].median())
    predictions = pd.DataFrame(
        {
            "row_id": holdout["row_id"],
            "prediction": [
                "1" if value >= median_signal else "0"
                for value in holdout["afe_eme_relative_return_1d"]
            ],
            "probability": [
                "0.65" if value >= median_signal else "0.35"
                for value in holdout["afe_eme_relative_return_1d"]
            ],
        }
    )
    submission_path = tmp_path / "predictions.csv"
    predictions.to_csv(submission_path, index=False)

    score = score_usd_afe_vs_eme_relative_submission(
        submission_path=submission_path,
        answer_key_path=paths.answer_key,
    )

    assert score.task_id == "usd_afe_vs_eme_relative_direction_v0"
    assert score.execution_success == 1.0
    assert score.rows_scored > 0
    assert score.balanced_accuracy is not None
    assert 0.0 <= score.balanced_accuracy <= 1.0
    assert score.roc_auc is not None
    assert 0.0 <= score.roc_auc <= 1.0


def test_usd_relative_logistic_baseline_artifacts(tmp_path: Path):
    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )
    output_dir = tmp_path / "run"

    metadata = write_usd_relative_logistic_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=output_dir,
        random_state=37,
    )

    assert (output_dir / "predictions.csv").exists()
    assert (output_dir / "writeup.md").exists()
    assert (output_dir / "notebook.ipynb").exists()
    assert (output_dir / "baseline_metadata.json").exists()
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_usd_relative_previous_day_baseline_artifacts(tmp_path: Path):
    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    metadata = write_usd_relative_previous_day_direction_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=tmp_path / "previous_day_run",
    )

    assert 0.0 <= metadata["probability_if_previous_day_relative_up"] <= 1.0
    assert 0.0 <= metadata["probability_if_previous_day_relative_nonpositive"] <= 1.0
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_usd_relative_tree_baselines_train_and_write_artifacts(tmp_path: Path):
    paths = write_usd_relative_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_usd_broad_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    _, rf_metadata = train_usd_relative_random_forest_model(paths.train_public, random_state=37)
    _, extra_metadata = train_usd_relative_extra_trees_model(paths.train_public, random_state=37)
    previous_day_metadata = train_usd_relative_previous_day_direction_baseline(paths.train_public)

    rf_output_dir = tmp_path / "rf_run"
    extra_output_dir = tmp_path / "extra_run"
    write_usd_relative_random_forest_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=rf_output_dir,
        random_state=37,
    )
    write_usd_relative_extra_trees_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=extra_output_dir,
        random_state=37,
    )

    assert rf_metadata["baseline_family"] == "random_forest"
    assert extra_metadata["baseline_family"] == "extra_trees"
    assert previous_day_metadata["baseline_family"] == "previous_day_direction_rule"
    assert (rf_output_dir / "predictions.csv").exists()
    assert (extra_output_dir / "predictions.csv").exists()
