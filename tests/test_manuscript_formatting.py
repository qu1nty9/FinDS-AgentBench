from pathlib import Path

from finds_agentbench.manuscript_formatting import (
    build_manuscript_formatting_report,
    write_manuscript_formatting_artifacts,
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_manuscript_formatting_report_accepts_traceable_latex_scaffold(tmp_path: Path):
    paper_root = tmp_path / "papers" / "workshop_pilot"
    main_tex = paper_root / "main.tex"
    related_tex = paper_root / "related_work.tex"
    table_tex = tmp_path / "docs" / "table.tex"
    references_bib = paper_root / "references.bib"
    write_text(
        main_tex,
        "\n".join(
            [
                "\\documentclass{article}",
                "\\begin{document}",
                "\\input{related_work.tex}",
                "\\input{../../docs/table.tex}",
                "See Table~\\ref{tab:demo}.",
                "\\bibliography{references}",
                "\\end{document}",
                "",
            ]
        ),
    )
    write_text(related_tex, "Neighbor~\\cite{demo2026}.\n")
    write_text(
        table_tex,
        "\n".join(
            [
                "\\begin{table}[t]",
                "\\centering",
                "\\begin{tabular}{lc}",
                "\\toprule",
                "Name & Score \\\\",
                "\\midrule",
                "Demo & 1.0 \\\\",
                "\\bottomrule",
                "\\end{tabular}",
                "\\caption{Demo table.}",
                "\\label{tab:demo}",
                "\\end{table}",
                "",
            ]
        ),
    )
    write_text(
        references_bib,
        "\n".join(
            [
                "@article{demo2026,",
                "  title={Demo},",
                "  author={Example, A.},",
                "  journal={arXiv preprint arXiv:2601.00001},",
                "  year={2026}",
                "}",
                "",
            ]
        ),
    )

    report = build_manuscript_formatting_report(main_tex_path=main_tex, workspace_root=tmp_path)

    assert report["ready_for_static_formatting_claims"] is True
    assert report["hard_error_count"] == 0
    assert report["tex_file_count"] == 3
    assert report["bibliography_count"] == 1
    assert report["citation_count"] == 1
    assert report["table_count"] == 1
    assert report["tables"][0]["label"] == "tab:demo"


def test_manuscript_formatting_report_rejects_missing_inputs_and_citations(tmp_path: Path):
    paper_root = tmp_path / "papers" / "workshop_pilot"
    main_tex = paper_root / "main.tex"
    references_bib = paper_root / "references.bib"
    write_text(
        main_tex,
        "\n".join(
            [
                "\\documentclass{article}",
                "\\begin{document}",
                "\\input{missing_section.tex}",
                "Missing citation~\\cite{missing2026}.",
                "\\bibliography{references}",
                "\\end{document}",
                "",
            ]
        ),
    )
    write_text(references_bib, "")

    result = write_manuscript_formatting_artifacts(
        main_tex_path=main_tex,
        output_json_path=tmp_path / "formatting_check.json",
        output_markdown_path=tmp_path / "formatting_check.md",
        workspace_root=tmp_path,
    )

    hard_error_kinds = {entry["kind"] for entry in result.report["hard_errors"]}
    assert result.report["status"] == "failed_static_checks"
    assert result.report["ready_for_static_formatting_claims"] is False
    assert "missing_tex_input" in hard_error_kinds
    assert "unresolved_citation" in hard_error_kinds
    assert result.json_path.exists()
    assert result.markdown_path.exists()


def test_manuscript_formatting_report_treats_appendix_and_resizebox_as_mitigations(
    tmp_path: Path,
):
    paper_root = tmp_path / "papers" / "workshop_pilot"
    main_tex = paper_root / "main.tex"
    wide_tex = paper_root / "wide_table.tex"
    appendix_tex = paper_root / "appendix_table.tex"
    write_text(
        main_tex,
        "\n".join(
            [
                "\\documentclass{article}",
                "\\usepackage{graphicx}",
                "\\begin{document}",
                "\\input{wide_table.tex}",
                "\\appendix",
                "\\input{appendix_table.tex}",
                "\\end{document}",
                "",
            ]
        ),
    )
    write_text(
        wide_tex,
        "\n".join(
            [
                "\\begin{table}[t]",
                "\\centering",
                "\\resizebox{\\textwidth}{!}{%",
                "\\begin{tabular}{llllllll}",
                "A & B & C & D & E & F & G & H \\\\",
                "\\end{tabular}",
                "}",
                "\\caption{Wide table.}",
                "\\label{tab:wide}",
                "\\end{table}",
                "",
            ]
        ),
    )
    appendix_rows = ["A & B \\\\" for _ in range(35)]
    write_text(
        appendix_tex,
        "\n".join(
            [
                "\\begin{table}[t]",
                "\\centering",
                "\\begin{tabular}{ll}",
                *appendix_rows,
                "\\end{tabular}",
                "\\caption{Appendix table.}",
                "\\label{tab:appendix}",
                "\\end{table}",
                "",
            ]
        ),
    )

    report = build_manuscript_formatting_report(main_tex_path=main_tex, workspace_root=tmp_path)

    warning_kinds = {entry["kind"] for entry in report["warnings"]}
    assert "wide_table_candidate" not in warning_kinds
    assert "long_table_candidate" not in warning_kinds
    assert report["mitigated_table_count"] == 2
    assert any(table["placement"] == "appendix" for table in report["tables"])
    assert any(table["width_mitigation"] == "resizebox" for table in report["tables"])
