import csv
import json
from pathlib import Path

from finds_agentbench.data_manifest import build_data_manifests


def test_build_data_manifests_reports_public_files_and_checksums(tmp_path: Path):
    workspace_root = tmp_path / "workspace"
    tasks_root = workspace_root / "tasks"
    data_root = workspace_root / "data" / "raw" / "demo_task"
    nested_experiment_root = data_root / "repeat_001"
    scripts_root = workspace_root / "scripts"
    output_root = workspace_root / "docs" / "data_manifests"

    tasks_root.mkdir(parents=True)
    data_root.mkdir(parents=True)
    nested_experiment_root.mkdir(parents=True)
    scripts_root.mkdir(parents=True)

    spec_path = tasks_root / "demo_task.yaml"
    script_path = scripts_root / "generate_demo.py"
    csv_path = data_root / "train_public.csv"
    script_path.write_text("print('demo')\n", encoding="utf-8")
    csv_path.write_text("row_id,value\nrow_1,1\n", encoding="utf-8")
    (nested_experiment_root / "extra.csv").write_text("row_id,value\nrow_2,2\n", encoding="utf-8")
    spec_path.write_text(
        """
metadata:
  task_id: demo_task
  title: Demo Task
  track: predictive_financial_ml
  version: "0.1.0"
  status: draft
data:
  license_status: usable
  access: synthetic_generator
  local_paths:
    - data/raw/demo_task/
  download_or_generation_script: scripts/generate_demo.py
  sources:
    - name: Demo source
      url_or_reference: generated locally
      license: project_generated
      access: synthetic_generator
""".lstrip(),
        encoding="utf-8",
    )

    result = build_data_manifests(
        tasks_root=tasks_root,
        output_root=output_root,
        workspace_root=workspace_root,
    )

    assert len(result.manifest_paths) == 1
    manifest = json.loads(result.manifest_paths[0].read_text(encoding="utf-8"))
    assert manifest["task_id"] == "demo_task"
    assert manifest["public_data_present"] is True
    assert manifest["public_file_count"] == 1
    assert manifest["generator_script"]["exists"] is True
    assert manifest["generator_script"]["sha256"]
    assert manifest["public_local_paths"][0]["files"][0]["path"] == "data/raw/demo_task/train_public.csv"
    assert manifest["public_local_paths"][0]["ignored_subdirectories"] == ["data/raw/demo_task/repeat_001"]

    index_entries = json.loads(result.index_json_path.read_text(encoding="utf-8"))
    assert index_entries[0]["task_id"] == "demo_task"

    with result.index_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["task_id"] == "demo_task"
    assert rows[0]["public_data_present"] == "True"

    readme = result.readme_path.read_text(encoding="utf-8")
    assert "Generated public-data provenance manifests" in readme
    assert "[manifest](demo_task.json)" in readme
