from resume_tailor.core.models import (
    JobDescription,
    ParsedResume,
    TailoredResume,
)


def test_parsed_resume_instantiation(sample_parsed_resume: ParsedResume):
    assert sample_parsed_resume.contact_info.name == "Jane Doe"
    assert len(sample_parsed_resume.experience) == 1
    assert sample_parsed_resume.experience[0].company == "Acme Corp"


def test_tailored_resume_instantiation(sample_tailored_resume: TailoredResume):
    assert sample_tailored_resume.target_job_title == "Senior Python Backend Engineer"
    assert sample_tailored_resume.ats_score_estimate == 92
    assert len(sample_tailored_resume.changes) == 1


def test_job_description_instantiation(sample_job_description: JobDescription):
    assert "FastAPI" in sample_job_description.required_skills
    assert sample_job_description.company == "Tech Innovators"
