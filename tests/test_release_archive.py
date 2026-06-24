from __future__ import annotations

import json
import tarfile
from pathlib import Path

from finds_agentbench.release_archive import build_release_archive, collect_release_archive_files


def write_release_archive_fixture(root: Path) -> None:
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    (root / "src" / "fixture").mkdir(parents=True)
    (root / "src" / "fixture" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    release_root = root / "docs" / "releases" / "pilot_v0"
    release_root.mkdir(parents=True)
    (release_root / "manifest.json").write_text(
        json.dumps(
            {
                "benchmark_id": "finds_agentbench_pilot_v0",
                "benchmark_version": "0.1.0",
                "release_stage": "pilot",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (release_root / "submission_readiness.json").write_text(
        json.dumps(
            {
                "status": "not_ready_for_workshop_submission",
                "ready_for_workshop_submission": False,
                "blocking_gate_count": 3,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (release_root / "archive_manifest.json").write_text('{"stale": true}\n', encoding="utf-8")
    (release_root / "archive_manifest.md").write_text("stale\n", encoding="utf-8")


def test_build_release_archive_is_deterministic_and_excludes_archive_manifest(tmp_path: Path):
    write_release_archive_fixture(tmp_path)
    include_paths = ["README.md", "pyproject.toml", "src", "docs/releases/pilot_v0"]

    result = build_release_archive(workspace_root=tmp_path, include_paths=include_paths)
    first_archive_sha256 = result.manifest["archive_sha256"]
    second_result = build_release_archive(workspace_root=tmp_path, include_paths=include_paths)

    assert second_result.manifest["archive_sha256"] == first_archive_sha256
    assert result.manifest["archive_status"] == "candidate_unfrozen"
    assert result.manifest["expected_tag"] == "v0.1.0-pilot"
    assert result.manifest_json_path.exists()
    assert result.manifest_markdown_path.exists()
    archived_paths = {entry["path"] for entry in result.manifest["files"]}
    assert "docs/releases/pilot_v0/archive_manifest.json" not in archived_paths
    assert "docs/releases/pilot_v0/archive_manifest.md" not in archived_paths
    assert "docs/releases/pilot_v0/manifest.json" in archived_paths
    assert "docs/releases/pilot_v0/submission_readiness.json" in archived_paths

    with tarfile.open(result.archive_path, mode="r:gz") as archive:
        names = archive.getnames()
        assert names == sorted(names)
        assert archive.getmember("finds_agentbench_pilot_v0-0.1.0-pilot/README.md").mtime == 0


def test_collect_release_archive_files_rejects_missing_include_path(tmp_path: Path):
    write_release_archive_fixture(tmp_path)

    try:
        collect_release_archive_files(workspace_root=tmp_path, include_paths=["missing"])
    except FileNotFoundError as exc:
        assert "Release archive include path does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing include path to raise FileNotFoundError.")
