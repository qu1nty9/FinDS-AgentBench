from __future__ import annotations

import gzip
import json
import stat
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from finds_agentbench.runs import file_sha256


DEFAULT_RELEASE_MANIFEST_PATH = Path("docs/releases/pilot_v0/manifest.json")
DEFAULT_SUBMISSION_READINESS_PATH = Path("docs/releases/pilot_v0/submission_readiness.json")
DEFAULT_RELEASE_ARCHIVE_OUTPUT_DIR = Path("dist/release_archives")
DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH = Path("docs/releases/pilot_v0/archive_manifest.json")
DEFAULT_RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH = Path("docs/releases/pilot_v0/archive_manifest.md")
DEFAULT_RELEASE_ARCHIVE_INCLUDE_PATHS = (
    Path("README.md"),
    Path("pyproject.toml"),
    Path("schemas"),
    Path("src"),
    Path("scripts"),
    Path("tasks/pilot"),
    Path("baselines"),
    Path("agents"),
    Path("docs/cards"),
    Path("docs/data_manifests/pilot_v0"),
    Path("docs/releases/pilot_v0"),
    Path("audits/pilot_v0"),
    Path("audits/methodology_calibration"),
)
DEFAULT_RELEASE_ARCHIVE_EXCLUDE_PATHS = (
    DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    DEFAULT_RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH,
)
DEFAULT_EXCLUDE_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    ".ipynb_checkpoints",
}


@dataclass(frozen=True)
class ReleaseArchiveBuildResult:
    archive_path: Path
    manifest_json_path: Path
    manifest_markdown_path: Path
    manifest: dict[str, Any]


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(payload).__name__}.")
    return payload


def relative_to_workspace(path: Path, *, workspace_root: Path) -> str:
    resolved_root = workspace_root.resolve()
    resolved_path = path.resolve()
    try:
        relative_path = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path is outside workspace root: {path}") from exc
    return relative_path.as_posix()


def should_skip_file(
    path: Path,
    *,
    workspace_root: Path,
    exclude_relative_paths: set[str],
    exclude_dir_names: set[str],
) -> bool:
    relative_path = Path(relative_to_workspace(path, workspace_root=workspace_root))
    if relative_path.as_posix() in exclude_relative_paths:
        return True
    return any(part in exclude_dir_names for part in relative_path.parts)


def collect_release_archive_files(
    *,
    workspace_root: str | Path = ".",
    include_paths: Iterable[str | Path] = DEFAULT_RELEASE_ARCHIVE_INCLUDE_PATHS,
    exclude_paths: Iterable[str | Path] = DEFAULT_RELEASE_ARCHIVE_EXCLUDE_PATHS,
    exclude_dir_names: Iterable[str] = DEFAULT_EXCLUDE_DIR_NAMES,
) -> list[Path]:
    root = Path(workspace_root)
    exclude_relative_paths = {
        relative_to_workspace(root / path, workspace_root=root) for path in exclude_paths
    }
    exclude_dir_names_set = set(exclude_dir_names)
    files_by_relative_path: dict[str, Path] = {}
    for include_path in include_paths:
        candidate = root / include_path
        if not candidate.exists():
            raise FileNotFoundError(f"Release archive include path does not exist: {candidate}")
        if candidate.is_file():
            if not should_skip_file(
                candidate,
                workspace_root=root,
                exclude_relative_paths=exclude_relative_paths,
                exclude_dir_names=exclude_dir_names_set,
            ):
                files_by_relative_path[relative_to_workspace(candidate, workspace_root=root)] = candidate
            continue
        for path in candidate.rglob("*"):
            if not path.is_file():
                continue
            if should_skip_file(
                path,
                workspace_root=root,
                exclude_relative_paths=exclude_relative_paths,
                exclude_dir_names=exclude_dir_names_set,
            ):
                continue
            files_by_relative_path[relative_to_workspace(path, workspace_root=root)] = path
    return [files_by_relative_path[key] for key in sorted(files_by_relative_path)]


def tar_mode_for_file(path: Path) -> int:
    mode = stat.S_IMODE(path.stat().st_mode)
    return 0o755 if mode & stat.S_IXUSR else 0o644


def write_deterministic_tar_gz(
    *,
    archive_path: str | Path,
    files: Iterable[Path],
    workspace_root: str | Path = ".",
    archive_prefix: str,
) -> None:
    root = Path(workspace_root)
    output_path = Path(archive_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            with tarfile.open(fileobj=gzip_handle, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in files:
                    relative_path = relative_to_workspace(path, workspace_root=root)
                    tar_info = tarfile.TarInfo(name=f"{archive_prefix}/{relative_path}")
                    tar_info.size = path.stat().st_size
                    tar_info.mode = tar_mode_for_file(path)
                    tar_info.mtime = 0
                    tar_info.uid = 0
                    tar_info.gid = 0
                    tar_info.uname = ""
                    tar_info.gname = ""
                    with path.open("rb") as handle:
                        archive.addfile(tar_info, handle)


def release_archive_filename(manifest: dict[str, Any]) -> str:
    benchmark_id = str(manifest.get("benchmark_id", "finds_agentbench_pilot_v0"))
    version = str(manifest.get("benchmark_version", "0.1.0"))
    stage = str(manifest.get("release_stage", "pilot"))
    return f"{benchmark_id}-{version}-{stage}.tar.gz"


def release_archive_prefix(manifest: dict[str, Any]) -> str:
    benchmark_id = str(manifest.get("benchmark_id", "finds_agentbench_pilot_v0"))
    version = str(manifest.get("benchmark_version", "0.1.0"))
    stage = str(manifest.get("release_stage", "pilot"))
    return f"{benchmark_id}-{version}-{stage}"


def build_release_archive_manifest(
    *,
    manifest: dict[str, Any],
    submission_readiness: dict[str, Any],
    archive_path: Path,
    files: list[Path],
    workspace_root: str | Path = ".",
    include_paths: Iterable[str | Path] = DEFAULT_RELEASE_ARCHIVE_INCLUDE_PATHS,
    exclude_paths: Iterable[str | Path] = DEFAULT_RELEASE_ARCHIVE_EXCLUDE_PATHS,
) -> dict[str, Any]:
    root = Path(workspace_root)
    file_entries = [
        {
            "path": relative_to_workspace(path, workspace_root=root),
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in files
    ]
    ready_for_submission = bool(submission_readiness.get("ready_for_workshop_submission", False))
    stage = str(manifest.get("release_stage", "pilot"))
    version = str(manifest.get("benchmark_version", "0.1.0"))
    return {
        "benchmark_id": manifest["benchmark_id"],
        "benchmark_version": version,
        "release_stage": stage,
        "archive_status": "ready_to_tag" if ready_for_submission else "candidate_unfrozen",
        "expected_tag": f"v{version}-{stage}",
        "archive_path": relative_to_workspace(archive_path, workspace_root=root),
        "archive_sha256": file_sha256(archive_path),
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_mtime_policy": "tar and gzip mtimes are normalized to 0",
        "file_count": len(file_entries),
        "total_uncompressed_size_bytes": sum(entry["size_bytes"] for entry in file_entries),
        "include_paths": [Path(path).as_posix() for path in include_paths],
        "exclude_paths": [Path(path).as_posix() for path in exclude_paths],
        "submission_readiness": {
            "status": submission_readiness.get("status", "unknown"),
            "ready_for_workshop_submission": ready_for_submission,
            "blocking_gate_count": submission_readiness.get("blocking_gate_count", 0),
        },
        "files": file_entries,
    }


def render_release_archive_manifest_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Release Archive Manifest",
        "",
        "Deterministic archive manifest for the FinDS-AgentBench pilot release candidate.",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Benchmark ID | {manifest['benchmark_id']} |",
        f"| Benchmark Version | {manifest['benchmark_version']} |",
        f"| Release Stage | {manifest['release_stage']} |",
        f"| Archive Status | `{manifest['archive_status']}` |",
        f"| Expected Tag | `{manifest['expected_tag']}` |",
        f"| Archive Path | `{manifest['archive_path']}` |",
        f"| Archive SHA256 | `{manifest['archive_sha256']}` |",
        f"| File Count | {manifest['file_count']} |",
        f"| Total Uncompressed Size | {manifest['total_uncompressed_size_bytes']} bytes |",
        "",
        "## Submission Readiness",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | `{manifest['submission_readiness']['status']}` |",
        "| Ready for Workshop Submission | "
        f"{'yes' if manifest['submission_readiness']['ready_for_workshop_submission'] else 'no'} |",
        f"| Blocking Gates | {manifest['submission_readiness']['blocking_gate_count']} |",
        "",
        "## Files",
        "",
        "| Path | Size Bytes | SHA256 |",
        "| --- | ---: | --- |",
    ]
    lines.extend(
        f"| `{entry['path']}` | {entry['size_bytes']} | `{entry['sha256']}` |"
        for entry in manifest["files"]
    )
    return "\n".join(lines) + "\n"


def build_release_archive(
    *,
    workspace_root: str | Path = ".",
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    output_dir: str | Path = DEFAULT_RELEASE_ARCHIVE_OUTPUT_DIR,
    manifest_json_path: str | Path = DEFAULT_RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
    manifest_markdown_path: str | Path = DEFAULT_RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH,
    include_paths: Iterable[str | Path] | None = None,
    exclude_paths: Iterable[str | Path] | None = None,
) -> ReleaseArchiveBuildResult:
    root = Path(workspace_root)
    release_manifest = load_json(root / release_manifest_path)
    submission_readiness = load_json(root / submission_readiness_path)
    archive_include_paths = include_paths or DEFAULT_RELEASE_ARCHIVE_INCLUDE_PATHS
    archive_exclude_paths = exclude_paths or DEFAULT_RELEASE_ARCHIVE_EXCLUDE_PATHS
    files = collect_release_archive_files(
        workspace_root=root,
        include_paths=archive_include_paths,
        exclude_paths=archive_exclude_paths,
    )
    archive_path = root / output_dir / release_archive_filename(release_manifest)
    write_deterministic_tar_gz(
        archive_path=archive_path,
        files=files,
        workspace_root=root,
        archive_prefix=release_archive_prefix(release_manifest),
    )
    archive_manifest = build_release_archive_manifest(
        manifest=release_manifest,
        submission_readiness=submission_readiness,
        archive_path=archive_path,
        files=files,
        workspace_root=root,
        include_paths=archive_include_paths,
        exclude_paths=archive_exclude_paths,
    )
    json_path = root / manifest_json_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(archive_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markdown_path = root / manifest_markdown_path
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_release_archive_manifest_markdown(archive_manifest),
        encoding="utf-8",
    )
    return ReleaseArchiveBuildResult(
        archive_path=archive_path,
        manifest_json_path=json_path,
        manifest_markdown_path=markdown_path,
        manifest=archive_manifest,
    )
