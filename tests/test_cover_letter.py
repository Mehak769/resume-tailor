from pathlib import Path

from resume_tailor.core.models import ContactInfo, CoverLetter
from resume_tailor.exporters.cover_letter_exporter import CoverLetterExporter


def test_cover_letter_model_creation():
    cl = CoverLetter(
        candidate_name="Mehak Sharma",
        target_company="Google",
        target_job_title="Senior AI Engineer",
        date_str="September 24, 2026",
        recipient="AI Engineering Hiring Team",
        company_location="Munich, Germany",
        salutation="Dear Hiring Team,",
        subject="Application for Senior AI Engineer Role",
        opening_paragraph="I am writing to express my strong enthusiasm for the Senior AI Engineer position at Google.",
        body_paragraph_1="With an M.Sc. in AI & Data Science and direct experience developing multi-agent systems at Allianz...",
        body_paragraph_2="At L&T Infotech, I engineered distributed data pipelines handling large-scale analytics...",
        closing_paragraph="I look forward to discussing how my experience aligns with your team's goals.",
        sign_off="Sincerely,",
    )
    assert cl.candidate_name == "Mehak Sharma"
    assert cl.target_company == "Google"
    assert "M.Sc." in cl.body_paragraph_1


def test_cover_letter_export(tmp_path: Path):
    cl = CoverLetter(
        candidate_name="Mehak Sharma",
        target_company="Google",
        target_job_title="Senior AI Engineer",
        date_str="September 24, 2026",
        recipient="Google Recruiting Team",
        opening_paragraph="I am thrilled to apply for the Senior AI Engineer role.",
        body_paragraph_1="My background in building enterprise LLM systems aligns with your infrastructure.",
        body_paragraph_2="I reduced latency by 35% across multi-agent workflows.",
        closing_paragraph="Thank you for your time and consideration.",
    )
    contact = ContactInfo(
        name="Mehak Sharma",
        email="mehak.sharma@stud.th-deg.de",
        phone="+49 15510299776",
        linkedin="linkedin.com/in/mehak-sharma-ml",
        github="github.com/Mehak769",
        location="Munich, Germany",
    )

    exporter = CoverLetterExporter(compile_pdf=False)
    out_file = tmp_path / "cover_letter.tex"
    exported_path = exporter.export(cover_letter=cl, contact=contact, output_path=out_file)

    assert exported_path.exists()
    content = exported_path.read_text(encoding="utf-8")
    assert r"\documentclass" in content
    assert "Mehak Sharma" in content
    assert "Google" in content
    assert "Senior AI Engineer" in content
    assert r"\href{mailto:mehak.sharma@stud.th-deg.de}" in content
    assert r"\href{https://linkedin.com/in/mehak-sharma-ml}" in content
