from pathlib import Path

from finds_agentbench.scoring import score_leakage_audit_submission
from finds_agentbench.synthetic import write_leakage_audit_task


def test_generate_leakage_audit_task(tmp_path: Path):
    output_dir = tmp_path / "public"
    private_dir = tmp_path / "private"

    paths = write_leakage_audit_task(output_dir=output_dir, private_dir=private_dir, seed=7)

    assert paths.public_panel.exists()
    assert paths.flawed_workflow.exists()
    assert paths.answer_key.exists()

    panel_text = paths.public_panel.read_text(encoding="utf-8")
    assert "feature_future_return_leak" in panel_text
    assert "private_temporal_holdout" in panel_text


def test_score_expert_leakage_audit_submission(tmp_path: Path):
    paths = write_leakage_audit_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        seed=7,
    )

    score = score_leakage_audit_submission(
        submission_dir="baselines/leakage_audit_temporal_split_v0/expert_submission",
        answer_key_path=paths.answer_key,
    )

    assert score.execution_success == 1.0
    assert score.leakage_identification == 1.0
    assert score.validation_correction == 1.0
    assert score.before_after_quantification == 1.0
    assert score.overall_score == 1.0

