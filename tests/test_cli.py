from pathlib import Path

from typer.testing import CliRunner

from resume_tailor.cli import app

runner = CliRunner()


def test_cli_missing_job_description(tmp_path: Path):
    dummy_resume = tmp_path / "resume.pdf"
    dummy_resume.write_text("dummy resume content")

    result = runner.invoke(app, ["--resume", str(dummy_resume)])
    assert result.exit_code != 0
    assert "You must provide either --jd-url or --jd-text" in result.stdout or result.exit_code == 1


def test_cli_missing_resume_file():
    result = runner.invoke(app, ["--resume", "non_existent.pdf", "--jd-text", "Sample JD"])
    assert result.exit_code != 0
