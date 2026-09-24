from pathlib import Path

import pytest

from resume_tailor.core.exceptions import ResumeParseError
from resume_tailor.core.models import TailoredResume
from resume_tailor.exporters.latex_exporter import LaTeXResumeExporter, escape_latex
from resume_tailor.parsers.latex_parser import LaTeXResumeParser


def test_escape_latex():
    raw = "Working with R&D, 50% increase in $ profit, C# & C++"
    escaped = escape_latex(raw)
    assert r"\&" in escaped
    assert r"\%" in escaped
    assert r"\$" in escaped
    assert r"\#" in escaped


def test_latex_parser_nonexistent():
    parser = LaTeXResumeParser()
    with pytest.raises(ResumeParseError):
        parser.parse(Path("missing_file.tex"))


def test_latex_parser_base_resume():
    base_file = (
        Path("base_resume/resume.tex")
        if Path("base_resume/resume.tex").exists()
        else Path("base_resume.tex")
    )
    if base_file.exists():
        parser = LaTeXResumeParser()
        parsed = parser.parse(base_file)
        assert "Mehak Sharma" in parsed.raw_text
        assert "Allianz Technology SE" in parsed.raw_text
        assert "Data Engineer" in parsed.raw_text


def test_latex_exporter_export(sample_tailored_resume: TailoredResume, tmp_path: Path):
    exporter = LaTeXResumeExporter(compile_pdf=False)
    out_file = tmp_path / "tailored.tex"
    result = exporter.export(sample_tailored_resume, out_file)
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert r"\documentclass" in content
    assert sample_tailored_resume.parsed_resume.contact_info.name in content
    assert r"\href{https://linkedin.com" in content
