from finds_agentbench.io import load_yaml
from finds_agentbench.validate import validate_task_spec


def test_template_task_matches_schema():
    schema = load_yaml("schemas/task_schema.yaml")
    task = load_yaml("tasks/templates/task.yaml")

    result = validate_task_spec(task, schema)

    assert result.ok, result.errors

