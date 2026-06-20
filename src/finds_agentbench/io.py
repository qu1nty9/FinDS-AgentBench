from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in incomplete environments
    yaml = None


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file as a mapping."""
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML files. Install with `pip install PyYAML`.")

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}.")
    return data

