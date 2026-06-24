from pathlib import Path

from finds_agentbench.related_work import (
    RELATED_WORK_ENTRIES,
    build_related_work_artifacts,
    render_bibtex,
    render_related_work_markdown,
    render_related_work_tex,
)


def test_related_work_renderers_include_key_positioning_and_citations():
    markdown = render_related_work_markdown()
    tex = render_related_work_tex()
    bibtex = render_bibtex()

    assert len(RELATED_WORK_ENTRIES) >= 10
    assert "MLE-bench" in markdown
    assert "Profit Mirage / FinLake-Bench" in markdown
    assert "\\section{Related Work}" in tex
    assert "\\cite{mlebench2024" in tex
    assert "\\label{tab:related-work-positioning}" in tex
    assert "@article{mlebench2024" in bibtex
    assert "@article{financebench2023" in bibtex


def test_build_related_work_artifacts_writes_markdown_tex_and_bib(tmp_path: Path):
    written = build_related_work_artifacts(
        markdown_path=tmp_path / "docs" / "related_work_matrix.md",
        tex_path=tmp_path / "papers" / "related_work.tex",
        bib_path=tmp_path / "papers" / "references.bib",
    )

    assert written["markdown"].exists()
    assert written["tex"].exists()
    assert written["bib"].exists()
    assert "FinDS-AgentBench" in written["markdown"].read_text(encoding="utf-8")
    assert "\\cite{financebench2023" in written["tex"].read_text(encoding="utf-8")
    assert "arXiv preprint" in written["bib"].read_text(encoding="utf-8")
