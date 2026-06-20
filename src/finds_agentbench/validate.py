from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


def validate_task_spec(task_spec: dict[str, Any], schema_spec: dict[str, Any]) -> ValidationResult:
    """Validate the structural contract for a task spec.

    This is intentionally lightweight. Full semantic validation will be added
    after the first pilot tasks are locked.
    """
    errors: list[str] = []

    required_top_level = schema_spec.get("required_top_level_keys", [])
    for key in required_top_level:
        if key not in task_spec:
            errors.append(f"Missing top-level section: {key}")

    sections = schema_spec.get("sections", {})
    for section_name, section_schema in sections.items():
        if section_name not in task_spec:
            continue
        section_value = task_spec[section_name]
        if not isinstance(section_value, dict):
            errors.append(f"Section `{section_name}` must be a mapping.")
            continue
        for required_key in section_schema.get("required", []):
            if required_key not in section_value:
                errors.append(f"Section `{section_name}` missing required key: {required_key}")

    metadata = task_spec.get("metadata", {})
    track = metadata.get("track")
    allowed_tracks = set(schema_spec.get("enums", {}).get("track", []))
    if track is not None and allowed_tracks and track not in allowed_tracks:
        errors.append(f"metadata.track `{track}` is not one of: {sorted(allowed_tracks)}")

    status = metadata.get("status")
    allowed_status = set(schema_spec.get("enums", {}).get("status", []))
    if status is not None and allowed_status and status not in allowed_status:
        errors.append(f"metadata.status `{status}` is not one of: {sorted(allowed_status)}")

    return ValidationResult(ok=not errors, errors=errors)

