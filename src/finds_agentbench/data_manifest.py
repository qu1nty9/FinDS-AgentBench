from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.io import load_yaml
from finds_agentbench.runs import file_sha256
from finds_agentbench.task_cards import discover_task_specs, markdown_table


@dataclass(frozen=True)
class DataManifestBuildResult:
    manifest_paths: list[Path]
    index_json_path: Path
    index_csv_path: Path
    readme_path: Path


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def describe_file(path: Path, *, root: Path) -> dict[str, Any]:
    return {
        "path": relative_to_root(path, root),
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def describe_path(path: Path, *, workspace_root: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": relative_to_root(path, workspace_root),
            "exists": False,
            "is_dir": False,
            "file_count": 0,
            "total_size_bytes": 0,
            "files": [],
            "ignored_subdirectories": [],
        }

    if path.is_file():
        file_entry = describe_file(path, root=workspace_root)
        return {
            "path": relative_to_root(path, workspace_root),
            "exists": True,
            "is_dir": False,
            "file_count": 1,
            "total_size_bytes": file_entry["size_bytes"],
            "files": [file_entry],
            "ignored_subdirectories": [],
        }

    children = sorted(path.iterdir())
    files = [describe_file(file_path, root=workspace_root) for file_path in children if file_path.is_file()]
    ignored_subdirectories = [
        relative_to_root(directory_path, workspace_root)
        for directory_path in children
        if directory_path.is_dir()
    ]
    return {
        "path": relative_to_root(path, workspace_root),
        "exists": True,
        "is_dir": True,
        "file_count": len(files),
        "total_size_bytes": sum(int(file_entry["size_bytes"]) for file_entry in files),
        "files": files,
        "ignored_subdirectories": ignored_subdirectories,
    }


def render_data_manifest_readme(entries: list[dict[str, Any]]) -> str:
    rows = [
        [
            entry["task_id"],
            entry["license_status"],
            entry["data_access"],
            "yes" if entry["public_data_present"] else "no",
            entry["public_file_count"],
            entry["public_total_size_bytes"],
            f"[manifest]({entry['task_id']}.json)",
        ]
        for entry in entries
    ]
    return "\n".join(
        [
            "# Data Manifests",
            "",
            "Generated public-data provenance manifests for the pilot benchmark tasks.",
            "",
            "Checksums cover top-level public files under each declared `local_path`; nested experimental subdirectories are ignored.",
            "",
            markdown_table(
                [
                    "Task ID",
                    "License Status",
                    "Access",
                    "Public Data Present",
                    "File Count",
                    "Total Size (bytes)",
                    "Manifest",
                ],
                rows,
            ).strip(),
            "",
            "- Machine-readable index: `index.json`",
            "- CSV summary: `index.csv`",
            "",
        ]
    ) + "\n"


def build_data_manifest_entry(
    spec: dict[str, Any],
    *,
    spec_path: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    metadata = spec.get("metadata", {})
    data = spec.get("data", {})
    generator_script_value = data.get("download_or_generation_script")
    generator_script_path = workspace_root / str(generator_script_value) if generator_script_value else None

    public_paths = [
        describe_path(workspace_root / str(local_path), workspace_root=workspace_root)
        for local_path in data.get("local_paths", [])
    ]
    public_data_present = any(path_entry["exists"] and path_entry["file_count"] > 0 for path_entry in public_paths)
    public_file_count = sum(int(path_entry["file_count"]) for path_entry in public_paths)
    public_total_size_bytes = sum(int(path_entry["total_size_bytes"]) for path_entry in public_paths)

    entry = {
        "task_id": str(metadata.get("task_id", "")),
        "title": str(metadata.get("title", "")),
        "track": str(metadata.get("track", "")),
        "version": str(metadata.get("version", "")),
        "status": str(metadata.get("status", "")),
        "source_spec": {
            "path": relative_to_root(spec_path, workspace_root),
            "sha256": file_sha256(spec_path),
        },
        "data_access": str(data.get("access", "")),
        "license_status": str(data.get("license_status", "")),
        "sources": data.get("sources", []),
        "generator_script": {
            "path": relative_to_root(generator_script_path, workspace_root) if generator_script_path else None,
            "exists": bool(generator_script_path and generator_script_path.exists()),
            "sha256": file_sha256(generator_script_path)
            if generator_script_path is not None and generator_script_path.exists()
            else None,
        },
        "public_local_paths": public_paths,
        "public_data_present": public_data_present,
        "public_file_count": public_file_count,
        "public_total_size_bytes": public_total_size_bytes,
    }
    return entry


def build_data_manifests(
    *,
    tasks_root: str | Path = "tasks/pilot",
    output_root: str | Path = "docs/data_manifests/pilot_v0",
    workspace_root: str | Path = ".",
) -> DataManifestBuildResult:
    workspace_path = Path(workspace_root).resolve()
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    task_specs = discover_task_specs(tasks_root)
    entries: list[dict[str, Any]] = []
    manifest_paths: list[Path] = []
    for spec_path in task_specs:
        resolved_spec = spec_path.resolve()
        spec = load_yaml(resolved_spec)
        entry = build_data_manifest_entry(spec, spec_path=resolved_spec, workspace_root=workspace_path)
        manifest_path = output_path / f"{entry['task_id']}.json"
        manifest_path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.append(entry)
        manifest_paths.append(manifest_path)

    index_json_path = output_path / "index.json"
    index_json_path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    index_csv_path = output_path / "index.csv"
    with index_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "title",
                "track",
                "version",
                "status",
                "data_access",
                "license_status",
                "public_data_present",
                "public_file_count",
                "public_total_size_bytes",
                "manifest_path",
            ],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "task_id": entry["task_id"],
                    "title": entry["title"],
                    "track": entry["track"],
                    "version": entry["version"],
                    "status": entry["status"],
                    "data_access": entry["data_access"],
                    "license_status": entry["license_status"],
                    "public_data_present": entry["public_data_present"],
                    "public_file_count": entry["public_file_count"],
                    "public_total_size_bytes": entry["public_total_size_bytes"],
                    "manifest_path": f"{entry['task_id']}.json",
                }
            )

    readme_path = output_path / "README.md"
    readme_path.write_text(render_data_manifest_readme(entries), encoding="utf-8")

    return DataManifestBuildResult(
        manifest_paths=manifest_paths,
        index_json_path=index_json_path,
        index_csv_path=index_csv_path,
        readme_path=readme_path,
    )
