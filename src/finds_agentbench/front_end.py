from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import nbformat
import pandas as pd

from finds_agentbench.treasury import (
    DEFAULT_OBSERVATION_END,
    DEFAULT_OBSERVATION_START,
    DEFAULT_REALTIME_SNAPSHOT_DATE,
    SERIES_IDS,
    TRAIN_END,
    PUBLIC_VALIDATION_END,
    PRIVATE_HOLDOUT_END,
    choose_threshold,
    clip_probability,
    fetch_treasury_source_frame,
    write_probability_predictions,
)


TASK_ID = "front_end_spread_widening_v0"
ASSET_ID = "us_treasury_front_end_spread_2y_ff"
SOURCE_TASK_ID = "yield_direction_treasury10y_v0"
DEFAULT_TREASURY_TRAIN_PUBLIC_PATH = Path("data/raw/yield_direction_treasury10y_v0/train_public.csv")
DEFAULT_TREASURY_HOLDOUT_FEATURES_PATH = Path(
    "data/raw/yield_direction_treasury10y_v0/private_holdout_features.csv"
)
DEFAULT_TREASURY_METADATA_PATH = Path("data/raw/yield_direction_treasury10y_v0/metadata.json")

FEATURE_COLUMNS = [
    "dgs10_level",
    "dgs2_level",
    "dgs3mo_level",
    "dff_level",
    "curve_10y_2y",
    "curve_10y_3mo",
    "front_end_spread",
    "front_end_spread_change_1d",
    "front_end_spread_change_5d",
    "curve_10y_2y_change_5d",
    "curve_10y_3mo_change_5d",
    "dgs2_change_1d",
    "dff_change_1d",
    "front_end_spread_vol_5d",
    "front_end_spread_vol_20d",
    "front_end_spread_minus_20d_mean",
]


@dataclass(frozen=True)
class FrontEndSpreadTaskPaths:
    train_public: Path
    private_holdout_features: Path
    sample_submission: Path
    metadata: Path
    answer_key: Path


def split_for_date(value) -> str:
    if value <= TRAIN_END:
        return "train"
    if value <= PUBLIC_VALIDATION_END:
        return "public_validation"
    if value <= PRIVATE_HOLDOUT_END:
        return "private_temporal_holdout"
    return "excluded"


def _format_numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    formatted = frame.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: f"{value:.8f}")
        elif pd.api.types.is_integer_dtype(formatted[column]):
            formatted[column] = formatted[column].map(str)
    return formatted


def _resolve_existing_task_paths(
    output_path: Path,
    private_path: Path,
) -> FrontEndSpreadTaskPaths | None:
    candidate = FrontEndSpreadTaskPaths(
        train_public=output_path / "train_public.csv",
        private_holdout_features=output_path / "private_holdout_features.csv",
        sample_submission=output_path / "sample_submission.csv",
        metadata=output_path / "metadata.json",
        answer_key=private_path / "answer_key.csv",
    )
    required_paths = (
        candidate.train_public,
        candidate.private_holdout_features,
        candidate.sample_submission,
        candidate.metadata,
        candidate.answer_key,
    )
    if all(path.exists() for path in required_paths):
        return candidate
    return None


def _existing_task_matches_request(
    *,
    metadata_path: Path,
    task_id: str,
    observation_start: str,
    observation_end: str,
    snapshot_date: str | None,
) -> bool:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        metadata.get("task_id") == task_id
        and metadata.get("observation_start") == observation_start
        and metadata.get("observation_end") == observation_end
        and metadata.get("snapshot_date") == snapshot_date
    )


def _load_source_frame_from_existing_treasury_snapshot(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
) -> pd.DataFrame:
    frames = []
    for path in (train_public_path, holdout_features_path):
        frame = pd.read_csv(
            path,
            usecols=[
                "date",
                "dgs10_level",
                "dgs2_level",
                "dgs3mo_level",
                "dff_level",
            ],
        )
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["date"])
    combined["date"] = pd.to_datetime(combined["date"], format="%Y-%m-%d")
    combined = combined.rename(
        columns={
            "dgs10_level": "dgs10",
            "dgs2_level": "dgs2",
            "dgs3mo_level": "dgs3mo",
            "dff_level": "dff",
        }
    )
    combined = combined.sort_values("date").set_index("date")
    combined.index.name = "date"
    return combined


def _resolve_existing_treasury_snapshot_source_frame(
    *,
    observation_start: str,
    observation_end: str,
    snapshot_date: str | None,
    treasury_train_public_path: Path,
    treasury_holdout_features_path: Path,
    treasury_metadata_path: Path,
) -> tuple[pd.DataFrame, str] | None:
    required_paths = (
        treasury_train_public_path,
        treasury_holdout_features_path,
        treasury_metadata_path,
    )
    if not all(path.exists() for path in required_paths):
        return None
    if not _existing_task_matches_request(
        metadata_path=treasury_metadata_path,
        task_id=SOURCE_TASK_ID,
        observation_start=observation_start,
        observation_end=observation_end,
        snapshot_date=snapshot_date,
    ):
        return None
    return (
        _load_source_frame_from_existing_treasury_snapshot(
            train_public_path=treasury_train_public_path,
            holdout_features_path=treasury_holdout_features_path,
        ),
        "derived_from_existing_treasury_snapshot",
    )


def build_front_end_spread_widening_frame(source_frame: pd.DataFrame) -> pd.DataFrame:
    if source_frame.empty:
        raise ValueError("source_frame must contain observations.")

    frame = source_frame.copy().sort_index()
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("source_frame index must be a pandas DatetimeIndex.")

    required_columns = set(SERIES_IDS)
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise ValueError(f"source_frame is missing required columns: {sorted(missing_columns)}")

    frame["curve_10y_2y"] = frame["dgs10"] - frame["dgs2"]
    frame["curve_10y_3mo"] = frame["dgs10"] - frame["dgs3mo"]
    frame["front_end_spread"] = frame["dgs2"] - frame["dff"]
    frame["front_end_spread_change_1d"] = frame["front_end_spread"].diff(1)
    frame["front_end_spread_change_5d"] = frame["front_end_spread"].diff(5)
    frame["curve_10y_2y_change_5d"] = frame["curve_10y_2y"].diff(5)
    frame["curve_10y_3mo_change_5d"] = frame["curve_10y_3mo"].diff(5)
    frame["dgs2_change_1d"] = frame["dgs2"].diff(1)
    frame["dff_change_1d"] = frame["dff"].diff(1)
    daily_front_end_change = frame["front_end_spread"].diff(1)
    frame["front_end_spread_vol_5d"] = daily_front_end_change.rolling(5).std()
    frame["front_end_spread_vol_20d"] = daily_front_end_change.rolling(20).std()
    frame["front_end_spread_minus_20d_mean"] = (
        frame["front_end_spread"] - frame["front_end_spread"].rolling(20).mean()
    )
    frame["next_day_front_end_change_bp"] = (
        frame["front_end_spread"].shift(-1) - frame["front_end_spread"]
    ) * 100.0
    frame["next_day_directional_return"] = frame["next_day_front_end_change_bp"] / 10000.0
    frame["next_day_front_end_widening"] = (frame["next_day_front_end_change_bp"] > 0.0).astype(int)
    frame["split"] = [split_for_date(timestamp.date()) for timestamp in frame.index]
    frame = frame.rename(
        columns={
            "dgs10": "dgs10_level",
            "dgs2": "dgs2_level",
            "dgs3mo": "dgs3mo_level",
            "dff": "dff_level",
        }
    )
    frame = frame.dropna(
        subset=FEATURE_COLUMNS + ["next_day_front_end_change_bp", "next_day_directional_return"]
    )
    frame = frame.loc[frame["split"] != "excluded"].copy()
    frame["asset_id"] = ASSET_ID
    frame["row_id"] = [
        f"{timestamp.date().isoformat()}_{ASSET_ID}" for timestamp in frame.index.to_pydatetime()
    ]
    frame["date"] = frame.index.strftime("%Y-%m-%d")

    ordered_columns = [
        "row_id",
        "date",
        "asset_id",
        "split",
        *FEATURE_COLUMNS,
        "next_day_front_end_widening",
        "next_day_front_end_change_bp",
        "next_day_directional_return",
    ]
    return frame.loc[:, ordered_columns]


def write_front_end_spread_widening_task(
    *,
    output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    source_frame: pd.DataFrame | None = None,
    treasury_train_public_path: str | Path = DEFAULT_TREASURY_TRAIN_PUBLIC_PATH,
    treasury_holdout_features_path: str | Path = DEFAULT_TREASURY_HOLDOUT_FEATURES_PATH,
    treasury_metadata_path: str | Path = DEFAULT_TREASURY_METADATA_PATH,
) -> FrontEndSpreadTaskPaths:
    output_path = Path(output_dir)
    private_path = Path(private_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    existing_paths = _resolve_existing_task_paths(output_path, private_path)
    if (
        source_frame is None
        and existing_paths is not None
        and _existing_task_matches_request(
            metadata_path=existing_paths.metadata,
            task_id=TASK_ID,
            observation_start=observation_start,
            observation_end=observation_end,
            snapshot_date=snapshot_date,
        )
    ):
        return existing_paths

    source_mode = "provided_source_frame"
    if source_frame is None:
        treasury_snapshot = _resolve_existing_treasury_snapshot_source_frame(
            observation_start=observation_start,
            observation_end=observation_end,
            snapshot_date=snapshot_date,
            treasury_train_public_path=Path(treasury_train_public_path),
            treasury_holdout_features_path=Path(treasury_holdout_features_path),
            treasury_metadata_path=Path(treasury_metadata_path),
        )
        if treasury_snapshot is not None:
            source_frame, source_mode = treasury_snapshot
        else:
            source_frame = fetch_treasury_source_frame(
                api_key=api_key,
                observation_start=observation_start,
                observation_end=observation_end,
                snapshot_date=snapshot_date,
            )
            source_mode = (
                "fred_api_realtime_snapshot"
                if (api_key or os.environ.get("FRED_API_KEY")) and snapshot_date is not None
                else (
                    "alfred_graph_vintage_snapshot"
                    if snapshot_date is not None
                    else "fred_graph_current"
                )
            )

    task_frame = build_front_end_spread_widening_frame(source_frame)
    formatted = _format_numeric_frame(task_frame)

    feature_columns = [
        "row_id",
        "date",
        "asset_id",
        "split",
        *FEATURE_COLUMNS,
    ]
    public_columns = feature_columns + [
        "next_day_front_end_widening",
        "next_day_front_end_change_bp",
        "next_day_directional_return",
    ]
    answer_columns = [
        "row_id",
        "date",
        "asset_id",
        "next_day_front_end_widening",
        "next_day_front_end_change_bp",
        "next_day_directional_return",
    ]

    train_public = formatted.loc[formatted["split"] != "private_temporal_holdout", public_columns]
    holdout = formatted.loc[formatted["split"] == "private_temporal_holdout"]

    train_public_path = output_path / "train_public.csv"
    holdout_features_path = output_path / "private_holdout_features.csv"
    sample_submission_path = output_path / "sample_submission.csv"
    metadata_path = output_path / "metadata.json"
    answer_key_path = private_path / "answer_key.csv"

    train_public.to_csv(train_public_path, index=False)
    holdout.loc[:, feature_columns].to_csv(holdout_features_path, index=False)
    pd.DataFrame(
        {
            "row_id": holdout["row_id"],
            "prediction": "0",
            "probability": "0.5",
        }
    ).to_csv(sample_submission_path, index=False)
    holdout.loc[:, answer_columns].to_csv(answer_key_path, index=False)

    metadata = {
        "task_id": TASK_ID,
        "asset_id": ASSET_ID,
        "source_series": SERIES_IDS,
        "observation_start": observation_start,
        "observation_end": observation_end,
        "snapshot_date": snapshot_date,
        "source_mode": source_mode,
        "splits": {
            "train": {
                "start": str(task_frame.loc[task_frame["split"] == "train", "date"].min()),
                "end": str(task_frame.loc[task_frame["split"] == "train", "date"].max()),
            },
            "public_validation": {
                "start": str(
                    task_frame.loc[task_frame["split"] == "public_validation", "date"].min()
                ),
                "end": str(
                    task_frame.loc[task_frame["split"] == "public_validation", "date"].max()
                ),
            },
            "private_temporal_holdout": {
                "start": str(
                    task_frame.loc[
                        task_frame["split"] == "private_temporal_holdout", "date"
                    ].min()
                ),
                "end": str(
                    task_frame.loc[
                        task_frame["split"] == "private_temporal_holdout", "date"
                    ].max()
                ),
            },
        },
        "feature_columns": FEATURE_COLUMNS,
        "target": "next_day_front_end_widening",
        "return_column": "next_day_directional_return",
        "forbidden_private_columns": [
            "next_day_front_end_widening",
            "next_day_front_end_change_bp",
            "next_day_directional_return",
        ],
        "row_count": int(len(task_frame)),
        "private_holdout_row_count": int((task_frame["split"] == "private_temporal_holdout").sum()),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return FrontEndSpreadTaskPaths(
        train_public=train_public_path,
        private_holdout_features=holdout_features_path,
        sample_submission=sample_submission_path,
        metadata=metadata_path,
        answer_key=answer_key_path,
    )


def load_front_end_train_validation_rows(train_public_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(train_public_path)
    train_rows = frame.loc[frame["split"] == "train"].copy()
    validation_rows = frame.loc[frame["split"] == "public_validation"].copy()
    if train_rows.empty:
        raise ValueError("No train rows found in train_public data.")
    if validation_rows.empty:
        raise ValueError("No public_validation rows found in train_public data.")
    return train_rows, validation_rows


def train_front_end_sklearn_probability_model(
    train_public_path: Path,
    *,
    estimator,
    model_name: str,
    random_state: int,
) -> tuple[Any, dict[str, Any]]:
    train_rows, validation_rows = load_front_end_train_validation_rows(train_public_path)
    estimator.fit(train_rows[FEATURE_COLUMNS], train_rows["next_day_front_end_widening"].astype(int))
    validation_probabilities = pd.Series(
        estimator.predict_proba(validation_rows[FEATURE_COLUMNS])[:, 1],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_front_end_widening"],
        validation_probabilities,
    )
    return estimator, {
        "baseline_family": model_name,
        "feature_columns": FEATURE_COLUMNS,
        "random_state": random_state,
        "train_rows": int(len(train_rows)),
        "public_validation_rows": int(len(validation_rows)),
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def write_front_end_baseline_writeup(
    output_path: Path,
    *,
    title: str,
    body_lines: list[str],
    metadata: dict[str, Any],
) -> None:
    lines = [f"# {title}", "", *body_lines, ""]
    if "selected_threshold" in metadata:
        lines.append(f"Selected threshold: `{metadata['selected_threshold']}`.")
    if "public_validation_balanced_accuracy" in metadata:
        lines.append(
            "Public validation balanced accuracy: "
            f"`{metadata['public_validation_balanced_accuracy']:.6f}`."
        )
    lines.extend(
        [
            "",
            "The baseline does not read private labels, answer keys, or future front-end spread changes during prediction generation.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_front_end_baseline_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Treasury Front-End Spread Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "for path in ['predictions.csv', 'writeup.md', 'baseline_metadata.json']:",
                    "    assert Path(path).exists(), f'missing {path}'",
                    "print('Treasury front-end spread baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def finalize_front_end_submission_artifacts(
    *,
    output_dir: Path,
    metadata: dict[str, Any],
    title: str,
    body_lines: list[str],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_front_end_baseline_writeup(
        output_dir / "writeup.md",
        title=title,
        body_lines=body_lines,
        metadata=metadata,
    )
    write_front_end_baseline_notebook(output_dir / "notebook.ipynb")
    (output_dir / "baseline_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def train_front_end_logistic_model(train_public_path: Path, *, random_state: int = 41):
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury front-end logistic baseline requires scikit-learn."
        ) from exc

    estimator = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=random_state),
    )
    return train_front_end_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="logistic_regression",
        random_state=random_state,
    )


def train_front_end_random_forest_model(train_public_path: Path, *, random_state: int = 41):
    try:
        from sklearn.ensemble import RandomForestClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury front-end random forest baseline requires scikit-learn."
        ) from exc

    estimator = RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_front_end_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="random_forest",
        random_state=random_state,
    )


def train_front_end_extra_trees_model(train_public_path: Path, *, random_state: int = 41):
    try:
        from sklearn.ensemble import ExtraTreesClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury front-end extra trees baseline requires scikit-learn."
        ) from exc

    estimator = ExtraTreesClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_front_end_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="extra_trees",
        random_state=random_state,
    )


def train_front_end_previous_day_direction_baseline(
    train_public_path: Path,
) -> dict[str, Any]:
    train_rows, validation_rows = load_front_end_train_validation_rows(train_public_path)
    train_indicator = train_rows["front_end_spread_change_1d"] > 0
    train_rate = float(train_rows["next_day_front_end_widening"].astype(int).mean())
    up_rate = clip_probability(
        float(
            train_rows.loc[train_indicator, "next_day_front_end_widening"].astype(int).mean()
        )
        if train_indicator.any()
        else train_rate
    )
    down_rate = clip_probability(
        float(
            train_rows.loc[~train_indicator, "next_day_front_end_widening"].astype(int).mean()
        )
        if (~train_indicator).any()
        else train_rate
    )
    validation_probabilities = pd.Series(
        [
            up_rate if indicator else down_rate
            for indicator in (validation_rows["front_end_spread_change_1d"] > 0).tolist()
        ],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_front_end_widening"],
        validation_probabilities,
    )
    return {
        "baseline_family": "previous_day_direction_rule",
        "feature_columns": ["front_end_spread_change_1d"],
        "train_rows": int(len(train_rows)),
        "public_validation_rows": int(len(validation_rows)),
        "probability_if_previous_day_widened": up_rate,
        "probability_if_previous_day_nonpositive": down_rate,
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def _write_front_end_model_predictions(
    model,
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(model.predict_proba(frame[FEATURE_COLUMNS])[:, 1], index=frame.index)
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_front_end_previous_day_direction_predictions(
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
    probability_if_previous_day_widened: float,
    probability_if_previous_day_nonpositive: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(
        [
            probability_if_previous_day_widened
            if value > 0
            else probability_if_previous_day_nonpositive
            for value in frame["front_end_spread_change_1d"]
        ],
        index=frame.index,
    )
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_front_end_logistic_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 41,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_front_end_logistic_model(train_public_path, random_state=random_state)
    _write_front_end_model_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_front_end_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Front-End Spread Logistic Regression Baseline",
        body_lines=[
            "This baseline trains a logistic regression model on the chronological train split only.",
            "Feature scaling is fit on the train split and reused on public validation and private holdout rows.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_front_end_random_forest_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 41,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_front_end_random_forest_model(train_public_path, random_state=random_state)
    _write_front_end_model_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_front_end_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Front-End Spread Random Forest Baseline",
        body_lines=[
            "This baseline trains a random forest classifier on the chronological train split only.",
            "It captures nonlinear interactions among the front-end spread, rate levels, and recent rates dynamics.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_front_end_extra_trees_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 41,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_front_end_extra_trees_model(train_public_path, random_state=random_state)
    _write_front_end_model_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_front_end_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Front-End Spread Extra Trees Baseline",
        body_lines=[
            "This baseline trains an extra-trees ensemble on the chronological train split only.",
            "It injects stronger randomization than the random forest baseline while preserving point-in-time features.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_front_end_previous_day_direction_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = train_front_end_previous_day_direction_baseline(train_public_path)
    write_front_end_previous_day_direction_predictions(
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
        probability_if_previous_day_widened=float(
            metadata["probability_if_previous_day_widened"]
        ),
        probability_if_previous_day_nonpositive=float(
            metadata["probability_if_previous_day_nonpositive"]
        ),
    )
    return finalize_front_end_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Front-End Spread Previous-Day Rule Baseline",
        body_lines=[
            "This baseline maps the previous day's 2Y minus fed-funds spread change into a validation-calibrated probability.",
            "The conditional probabilities are estimated on the train split only.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )
