import pytest

from resume_tailor.core.models import (
    ChangeDiff,
    ContactInfo,
    EducationItem,
    ExperienceItem,
    JobDescription,
    ParsedResume,
    ProjectItem,
    TailoredResume,
)


@pytest.fixture
def sample_parsed_resume() -> ParsedResume:
    return ParsedResume(
        raw_text="Sample Resume Text",
        contact_info=ContactInfo(
            name="Jane Doe",
            email="jane@example.com",
            phone="123-456-7890",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janedoe",
        ),
        summary="Experienced Software Engineer with a passion for distributed systems.",
        skills=["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"],
        experience=[
            ExperienceItem(
                company="Acme Corp",
                role="Senior Engineer",
                start_date="2021",
                end_date="Present",
                bullet_points=[
                    "Spearheaded migration of legacy services to microservices.",
                    "Improved API response latency by 35%.",
                ],
            )
        ],
        education=[
            EducationItem(
                institution="University of Technology",
                degree="B.S. in Computer Science",
                graduation_date="2020",
            )
        ],
        projects=[
            ProjectItem(
                title="Distributed Cache",
                technologies=["Go", "Redis"],
                description=["Built high throughput LRU caching layer."],
            )
        ],
    )


@pytest.fixture
def sample_job_description() -> JobDescription:
    return JobDescription(
        source="https://careers.example.com/job/123",
        title="Senior Python Backend Engineer",
        company="Tech Innovators",
        raw_text="We are seeking a Senior Python Backend Engineer skilled in FastAPI, Docker, and distributed systems.",
        required_skills=["Python", "FastAPI", "Docker"],
        preferred_skills=["AWS", "PostgreSQL"],
        key_responsibilities=["Architect reliable APIs", "Mentor junior engineers"],
    )


@pytest.fixture
def sample_tailored_resume(sample_parsed_resume: ParsedResume) -> TailoredResume:
    return TailoredResume(
        parsed_resume=sample_parsed_resume,
        target_job_title="Senior Python Backend Engineer",
        changes=[
            ChangeDiff(
                section="Experience",
                original="Spearheaded migration of legacy services to microservices.",
                tailored="Architected and executed microservices migration improving uptime to 99.99%.",
                reasoning="Highlighted measurable reliability metrics and architecture leadership.",
            )
        ],
        ats_score_estimate=92,
        recommendations=["Add metrics on team mentorship and system scale."],
    )
