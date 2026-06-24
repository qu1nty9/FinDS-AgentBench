from __future__ import annotations

import csv
import difflib
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.pilot_release import build_pilot_release
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


SUMMARY_REPORT_FILENAMES = (
    "pilot_baseline_run_summary.csv",
    "pilot_baseline_run_summary.md",
    "pilot_agent_run_summary.csv",
    "pilot_agent_run_summary.md",
    "pilot_protocol_run_summary.csv",
    "pilot_protocol_run_summary.md",
)


@dataclass(frozen=True)
class ReleaseReproPaths:
    root: Path
    baseline_runs_root: Path
    agent_runs_root: Path
    protocol_runs_root: Path
    reports_root: Path
    release_output_root: Path
    cards_root: Path
    data_manifests_root: Path


@dataclass(frozen=True)
class ReleaseReproCheckResult:
    first_root: Path
    second_root: Path
    compared_artifact_count: int
    compared_relative_paths: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseArtifactComparison:
    shared_relative_paths: tuple[str, ...]
    missing_in_second: tuple[str, ...]
    missing_in_first: tuple[str, ...]
    changed: tuple[str, ...]

    @property
    def matches(self) -> bool:
        return not self.missing_in_second and not self.missing_in_first and not self.changed

    def error_message(self) -> str:
        messages: list[str] = []
        if self.missing_in_second:
            messages.append("missing in second build: " + ", ".join(self.missing_in_second))
        if self.missing_in_first:
            messages.append("missing in first build: " + ", ".join(self.missing_in_first))
        if self.changed:
            messages.append("content mismatch: " + ", ".join(self.changed))
        return "; ".join(messages)


@dataclass(frozen=True)
class ReleaseReproForensicsResult:
    output_dir: Path
    summary_json_path: Path
    summary_markdown_path: Path
    comparison: ReleaseArtifactComparison


def build_release_repro_paths(root: str | Path) -> ReleaseReproPaths:
    work_root = Path(root)
    return ReleaseReproPaths(
        root=work_root,
        baseline_runs_root=work_root / "runs" / "baseline",
        agent_runs_root=work_root / "runs" / "agent",
        protocol_runs_root=work_root / "runs" / "protocol",
        reports_root=work_root / "reports",
        release_output_root=work_root / "release",
        cards_root=work_root / "cards",
        data_manifests_root=work_root / "data_manifests",
    )


def iter_release_comparison_targets(paths: ReleaseReproPaths) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    for filename in SUMMARY_REPORT_FILENAMES:
        target = paths.reports_root / filename
        if target.exists():
            targets.append((f"reports/{filename}", target))

    for label, root in (
        ("release", paths.release_output_root),
        ("cards", paths.cards_root),
        ("data_manifests", paths.data_manifests_root),
    ):
        if not root.exists():
            continue
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            targets.append((f"{label}/{path.relative_to(root).as_posix()}", path))
    return targets


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_release_artifact_digests(paths: ReleaseReproPaths) -> dict[str, str]:
    digests: dict[str, str] = {}
    for relative_path, absolute_path in iter_release_comparison_targets(paths):
        digests[relative_path] = file_sha256(absolute_path)
    return digests


def collect_release_artifact_paths(paths: ReleaseReproPaths) -> dict[str, Path]:
    return {relative_path: absolute_path for relative_path, absolute_path in iter_release_comparison_targets(paths)}


def build_release_artifact_comparison(
    first: dict[str, str],
    second: dict[str, str],
) -> ReleaseArtifactComparison:
    first_keys = set(first)
    second_keys = set(second)
    return ReleaseArtifactComparison(
        shared_relative_paths=tuple(sorted(first_keys & second_keys)),
        missing_in_second=tuple(sorted(first_keys - second_keys)),
        missing_in_first=tuple(sorted(second_keys - first_keys)),
        changed=tuple(sorted(path for path in first_keys & second_keys if first[path] != second[path])),
    )


def compare_release_artifact_digests(
    first: dict[str, str],
    second: dict[str, str],
) -> tuple[str, ...]:
    comparison = build_release_artifact_comparison(first, second)
    if comparison.matches:
        return comparison.shared_relative_paths
    raise ValueError(comparison.error_message())


def validate_summary_run_counts(paths: ReleaseReproPaths, *, expected_run_count: int) -> None:
    expected_value = str(expected_run_count)
    for filename in SUMMARY_REPORT_FILENAMES:
        if not filename.endswith(".csv"):
            continue
        summary_path = paths.reports_root / filename
        with summary_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"Summary report is empty: {summary_path}")
        observed_counts = sorted({row["run_count"] for row in rows})
        if observed_counts != [expected_value]:
            raise ValueError(
                f"Unexpected run_count values in {summary_path}: {observed_counts}; expected {expected_value}"
            )


def snapshot_output_path(base_dir: Path, relative_path: str) -> Path:
    return base_dir / Path(relative_path)


def diff_output_path(base_dir: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    suffix = relative.suffix + ".diff" if relative.suffix else ".diff"
    return base_dir / relative.with_suffix(suffix)


def copy_artifact_snapshot(source_path: Path, destination_root: Path, relative_path: str) -> str:
    destination_path = snapshot_output_path(destination_root, relative_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)
    return str(destination_path)


def read_text_artifact(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def write_release_reproducibility_forensics(
    *,
    first_paths: ReleaseReproPaths,
    second_paths: ReleaseReproPaths,
    output_dir: str | Path,
    failure_message: str | None = None,
) -> ReleaseReproForensicsResult:
    output_root = Path(output_dir)
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    first_targets = collect_release_artifact_paths(first_paths)
    second_targets = collect_release_artifact_paths(second_paths)
    first_digests = {relative_path: file_sha256(path) for relative_path, path in first_targets.items()}
    second_digests = {relative_path: file_sha256(path) for relative_path, path in second_targets.items()}
    comparison = build_release_artifact_comparison(first_digests, second_digests)

    first_snapshot_root = output_root / "snapshots" / "first"
    second_snapshot_root = output_root / "snapshots" / "second"
    diffs_root = output_root / "diffs"

    changed_entries: list[dict[str, Any]] = []
    for relative_path in comparison.changed:
        first_path = first_targets[relative_path]
        second_path = second_targets[relative_path]
        diff_path_value: str | None = None
        first_text = read_text_artifact(first_path)
        second_text = read_text_artifact(second_path)
        if first_text is not None and second_text is not None:
            diff_path = diff_output_path(diffs_root, relative_path)
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_lines = difflib.unified_diff(
                first_text.splitlines(),
                second_text.splitlines(),
                fromfile=f"first/{relative_path}",
                tofile=f"second/{relative_path}",
                lineterm="",
            )
            diff_path.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
            diff_path_value = str(diff_path)

        changed_entries.append(
            {
                "relative_path": relative_path,
                "first_sha256": first_digests[relative_path],
                "second_sha256": second_digests[relative_path],
                "first_snapshot_path": copy_artifact_snapshot(
                    first_path,
                    first_snapshot_root,
                    relative_path,
                ),
                "second_snapshot_path": copy_artifact_snapshot(
                    second_path,
                    second_snapshot_root,
                    relative_path,
                ),
                "diff_path": diff_path_value,
            }
        )

    missing_in_second_entries: list[dict[str, Any]] = []
    for relative_path in comparison.missing_in_second:
        missing_in_second_entries.append(
            {
                "relative_path": relative_path,
                "first_sha256": first_digests[relative_path],
                "first_snapshot_path": copy_artifact_snapshot(
                    first_targets[relative_path],
                    first_snapshot_root,
                    relative_path,
                ),
            }
        )

    missing_in_first_entries: list[dict[str, Any]] = []
    for relative_path in comparison.missing_in_first:
        missing_in_first_entries.append(
            {
                "relative_path": relative_path,
                "second_sha256": second_digests[relative_path],
                "second_snapshot_path": copy_artifact_snapshot(
                    second_targets[relative_path],
                    second_snapshot_root,
                    relative_path,
                ),
            }
        )

    status = "reproducible" if comparison.matches and failure_message is None else "failed"
    summary = {
        "status": status,
        "failure_message": failure_message,
        "first_root": str(first_paths.root),
        "second_root": str(second_paths.root),
        "shared_artifact_count": len(comparison.shared_relative_paths),
        "changed_artifact_count": len(comparison.changed),
        "missing_in_second_count": len(comparison.missing_in_second),
        "missing_in_first_count": len(comparison.missing_in_first),
        "shared_relative_paths": list(comparison.shared_relative_paths),
        "missing_in_second": missing_in_second_entries,
        "missing_in_first": missing_in_first_entries,
        "changed": changed_entries,
    }

    summary_json_path = output_root / "summary.json"
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markdown_lines = [
        "# Pilot Release Reproducibility Forensics",
        "",
        f"- Status: `{status}`",
        f"- First Root: `{first_paths.root}`",
        f"- Second Root: `{second_paths.root}`",
        f"- Shared Artifacts: `{len(comparison.shared_relative_paths)}`",
        f"- Changed Artifacts: `{len(comparison.changed)}`",
        f"- Missing In Second: `{len(comparison.missing_in_second)}`",
        f"- Missing In First: `{len(comparison.missing_in_first)}`",
    ]
    if failure_message:
        markdown_lines.extend(["", "## Failure", "", f"- `{failure_message}`"])
    if comparison.changed:
        markdown_lines.extend(["", "## Content Mismatches", ""])
        for entry in changed_entries:
            line = f"- `{entry['relative_path']}`"
            if entry["diff_path"] is not None:
                line += f" (`{entry['diff_path']}`)"
            markdown_lines.append(line)
    if comparison.missing_in_second:
        markdown_lines.extend(["", "## Missing In Second Build", ""])
        markdown_lines.extend(f"- `{entry['relative_path']}`" for entry in missing_in_second_entries)
    if comparison.missing_in_first:
        markdown_lines.extend(["", "## Missing In First Build", ""])
        markdown_lines.extend(f"- `{entry['relative_path']}`" for entry in missing_in_first_entries)
    summary_markdown_path = output_root / "summary.md"
    summary_markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    return ReleaseReproForensicsResult(
        output_dir=output_root,
        summary_json_path=summary_json_path,
        summary_markdown_path=summary_markdown_path,
        comparison=comparison,
    )


def run_release_reproducibility_check(
    *,
    work_root: str | Path = "tmp/pilot_release_repro_check",
    repeat: int = 1,
    market_seed: int = 11,
    event_seed: int = 23,
    treasury_seed: int = 29,
    curve_seed: int = 31,
    curve3mo_seed: int = 33,
    front_end_seed: int = 31,
    usd_seed: int = 37,
    treasury_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve3mo_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    front_end_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    usd_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    build_kwargs: dict[str, Any] | None = None,
) -> ReleaseReproCheckResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    first_paths = build_release_repro_paths(root / "first")
    second_paths = build_release_repro_paths(root / "second")
    extra_kwargs = dict(build_kwargs or {})

    for paths in (first_paths, second_paths):
        build_pilot_release(
            repeat=repeat,
            market_seed=market_seed,
            event_seed=event_seed,
            treasury_seed=treasury_seed,
            curve_seed=curve_seed,
            curve3mo_seed=curve3mo_seed,
            front_end_seed=front_end_seed,
            usd_seed=usd_seed,
            baseline_runs_root=paths.baseline_runs_root,
            agent_runs_root=paths.agent_runs_root,
            protocol_runs_root=paths.protocol_runs_root,
            reports_root=paths.reports_root,
            release_output_root=paths.release_output_root,
            reference_results_markdown_path=paths.release_output_root / "reference_results.md",
            reference_results_json_path=paths.release_output_root / "reference_results.json",
            paper_artifacts_output_dir=paths.release_output_root / "paper_artifacts",
            statistical_artifacts_output_dir=paths.release_output_root / "statistical_artifacts",
            cards_root=paths.cards_root,
            data_manifests_root=paths.data_manifests_root,
            clean_existing_outputs=True,
            treasury_snapshot_date=treasury_snapshot_date,
            curve_snapshot_date=curve_snapshot_date,
            curve3mo_snapshot_date=curve3mo_snapshot_date,
            front_end_snapshot_date=front_end_snapshot_date,
            usd_snapshot_date=usd_snapshot_date,
            **extra_kwargs,
        )
        validate_summary_run_counts(paths, expected_run_count=repeat)

    first_digests = collect_release_artifact_digests(first_paths)
    second_digests = collect_release_artifact_digests(second_paths)
    compared_relative_paths = compare_release_artifact_digests(first_digests, second_digests)

    return ReleaseReproCheckResult(
        first_root=first_paths.root,
        second_root=second_paths.root,
        compared_artifact_count=len(compared_relative_paths),
        compared_relative_paths=compared_relative_paths,
    )
