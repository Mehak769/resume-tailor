from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""


class ExperienceItem(BaseModel):
    company: str
    role: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullet_points: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str
    degree: str
    field_of_study: str = ""
    graduation_date: str = ""
    details: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    title: str
    technologies: list[str] = Field(default_factory=list)
    description: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    raw_text: str = ""
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)


class JobDescription(BaseModel):
    source: str  # URL or "raw_text"
    title: str = ""
    company: str = ""
    raw_text: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    key_responsibilities: list[str] = Field(default_factory=list)


class ChangeDiff(BaseModel):
    section: str
    original: str
    tailored: str
    reasoning: str


class TailoredResume(BaseModel):
    parsed_resume: ParsedResume
    target_job_title: str
    target_company: str = ""
    changes: list[ChangeDiff] = Field(default_factory=list)
    ats_score_estimate: int = Field(default=0, ge=0, le=100)
    recommendations: list[str] = Field(default_factory=list)


class CoverLetter(BaseModel):
    candidate_name: str = ""
    target_company: str = ""
    target_job_title: str = ""
    date_str: str = ""
    recipient: str = "Hiring Team"
    company_location: str = ""
    salutation: str = "Dear Hiring Team,"
    subject: str = ""
    opening_paragraph: str = ""
    body_paragraph_1: str = ""
    body_paragraph_2: str = ""
    closing_paragraph: str = ""
    sign_off: str = "Sincerely,"
