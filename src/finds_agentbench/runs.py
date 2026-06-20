from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


RUN_SCHEMA_VERSION = "0.1.0"

ALLOWED_RUN_TYPES = {"agent", "baseline", "human", "expert"}
ALLOWED_STATUSES = {
    "completed",
    "failed_runtime",
    "failed_format",
    "failed_validity_gate",
    "timed_out",
    "manually_excluded",
}
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "run_id",
    "task_id",
    "run_type",
    "agent",
    "timing",
    "status",
    "tool_permissions",
    "commands",
    "artifacts",
    "validations",
    "scores",
    "failures",
}


@dataclass(frozen=True)
class RunManifestValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "unknown"


def make_run_id(task_id: str, agent_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{slugify(task_id)}__{slugify(agent_id)}__{timestamp}__{uuid4().hex[:8]}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_inventory(submission_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(submission_dir)
    files: list[dict[str, Any]] = []
    if not root.exists():
        return files

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        files.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return files


def build_run_manifest(
    *,
    task_id: str,
    agent_id: str,
    agent_version: str,
    submission_dir: str | Path,
    run_type: str = "baseline",
    status: str = "completed",
    run_id: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    tool_permissions: list[str] | None = None,
    commands: list[dict[str, Any]] | None = None,
    validations: dict[str, Any] | None = None,
    scores: dict[str, Any] | None = None,
    failures: list[str] | None = None,
    trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = started_at or utc_now()
    completed = completed_at or utc_now()
    run_identifier = run_id or make_run_id(task_id, agent_id)

    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_identifier,
        "task_id": task_id,
        "run_type": run_type,
        "agent": {
            "agent_id": agent_id,
            "agent_version": agent_version,
        },
        "timing": {
            "started_at": started,
            "completed_at": completed,
        },
        "status": status,
        "tool_permissions": tool_permissions or [],
        "commands": commands or [],
        "artifacts": {
            "submission_dir": str(submission_dir),
            "files": artifact_inventory(submission_dir),
        },
        "validations": validations or {},
        "scores": scores or {},
        "failures": failures or [],
        "trace": trace or {},
    }


def write_run_manifest(manifest: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_run_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected run manifest JSON object in {path}.")
    return data


def validate_run_manifest(manifest: dict[str, Any]) -> RunManifestValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in manifest:
            errors.append(f"missing top-level key: {key}")

    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {RUN_SCHEMA_VERSION}, got {manifest.get('schema_version')!r}"
        )

    if not str(manifest.get("run_id", "")).strip():
        errors.append("run_id must be non-empty")

    if not str(manifest.get("task_id", "")).strip():
        errors.append("task_id must be non-empty")

    run_type = manifest.get("run_type")
    if run_type not in ALLOWED_RUN_TYPES:
        errors.append(f"run_type must be one of {sorted(ALLOWED_RUN_TYPES)}, got {run_type!r}")

    status = manifest.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"status must be one of {sorted(ALLOWED_STATUSES)}, got {status!r}")

    agent = manifest.get("agent", {})
    if not isinstance(agent, dict):
        errors.append("agent must be an object")
    else:
        for key in ("agent_id", "agent_version"):
            if not str(agent.get(key, "")).strip():
                errors.append(f"agent.{key} must be non-empty")

    timing = manifest.get("timing", {})
    if not isinstance(timing, dict):
        errors.append("timing must be an object")
    else:
        for key in ("started_at", "completed_at"):
            if not str(timing.get(key, "")).strip():
                errors.append(f"timing.{key} must be non-empty")

    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be an object")
    else:
        if not str(artifacts.get("submission_dir", "")).strip():
            errors.append("artifacts.submission_dir must be non-empty")
        files = artifacts.get("files")
        if not isinstance(files, list):
            errors.append("artifacts.files must be a list")
        else:
            if not files:
                warnings.append("artifacts.files is empty")
            for idx, item in enumerate(files):
                if not isinstance(item, dict):
                    errors.append(f"artifacts.files[{idx}] must be an object")
                    continue
                for key in ("path", "size_bytes", "sha256"):
                    if key not in item:
                        errors.append(f"artifacts.files[{idx}] missing key: {key}")

    for key in ("tool_permissions", "commands", "failures"):
        if key in manifest and not isinstance(manifest[key], list):
            errors.append(f"{key} must be a list")

    for key in ("validations", "scores"):
        if key in manifest and not isinstance(manifest[key], dict):
            errors.append(f"{key} must be an object")

    if "commands" in manifest and isinstance(manifest["commands"], list):
        for idx, command in enumerate(manifest["commands"]):
            if not isinstance(command, dict):
                errors.append(f"commands[{idx}] must be an object")
                continue
            for required_key in ("command", "started_at", "completed_at", "exit_code"):
                if required_key not in command:
                    errors.append(f"commands[{idx}] missing key: {required_key}")

    return RunManifestValidationResult(ok=not errors, errors=errors, warnings=warnings)

