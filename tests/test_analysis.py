from pathlib import Path

from resume_tailor.core.models import (
    ApplicationAnalysis,
    ChangeDiff,
    ContactInfo,
    InterviewQuestion,
    ParsedResume,
    TailoredResume,
)
from resume_tailor.exporters.analysis_exporter import AnalysisExporter


def test_analysis_model_creation():
    analysis = ApplicationAnalysis(
        target_company="Allianz Technology SE",
        target_job_title="AI Engineer",
        ats_score_estimate=94,
        key_strengths=[
            "Hands-on experience developing enterprise multi-agent systems with OpenAI Agents SDK",
            "Strong foundation in cloud infrastructure and distributed data engineering",
        ],
        skill_gaps_or_suggestions=[
            "Deep dive into internal Allianz security compliance for autonomous agents",
        ],
        interview_questions=[
            InterviewQuestion(
                category="Technical",
                question="How do you handle error recovery and state preservation in multi-agent routing?",
                why_asked="To test reliability engineering in production LLM workflows.",
                recommended_talking_points=[
                    "Discuss checkpointing and fallback mechanisms implemented at Allianz.",
                ],
            ),
            InterviewQuestion(
                category="Behavioral",
                question="Tell me about a time you had to align technical architecture with non-technical business units.",
                why_asked="Assess communication and cross-functional leadership.",
                recommended_talking_points=[
                    "Describe gathering requirements from service desk leads for automated routing.",
                ],
            ),
        ],
        smart_questions_to_ask_interviewer=[
            "What is the team's roadmap for moving from single-agent prototypes to production multi-agent swarms?",
        ],
    )

    assert analysis.target_company == "Allianz Technology SE"
    assert analysis.ats_score_estimate == 94
    assert len(analysis.interview_questions) == 2
    assert analysis.interview_questions[0].category == "Technical"


def test_analysis_exporter(tmp_path: Path):
    analysis = ApplicationAnalysis(
        target_company="Google",
        target_job_title="Senior AI Engineer",
        ats_score_estimate=95,
        key_strengths=["Production LLM orchestration", "Distributed data systems"],
        skill_gaps_or_suggestions=["Familiarity with TPU pod networking"],
        interview_questions=[
            InterviewQuestion(
                category="System Design",
                question="Design a real-time retrieval system serving 10k QPS.",
                why_asked="Evaluates high-scale systems capability.",
                recommended_talking_points=["Vector indexing", "Caching layer with Redis"],
            )
        ],
        smart_questions_to_ask_interviewer=[
            "How does the team evaluate prompt regressions across model updates?"
        ],
    )

    tailored_resume = TailoredResume(
        parsed_resume=ParsedResume(
            contact_info=ContactInfo(name="Mehak Sharma"),
            summary="Experienced AI Engineer",
        ),
        target_job_title="Senior AI Engineer",
        target_company="Google",
        ats_score_estimate=95,
        changes=[
            ChangeDiff(
                section="Professional Experience",
                original="Worked on AI agents",
                tailored="Engineered enterprise multi-agent software system reducing latency by 35%",
                reasoning="Quantified impact using Google X-Y-Z framework",
            )
        ],
    )

    exporter = AnalysisExporter()
    out_file = tmp_path / "analysis.md"
    exported_path = exporter.export(
        analysis=analysis,
        tailored_resume=tailored_resume,
        output_path=out_file,
    )

    assert exported_path.exists()
    content = exported_path.read_text(encoding="utf-8")
    assert "Application Match & Interview Prep Report: Google" in content
    assert "95/100" in content
    assert "Production LLM orchestration" in content
    assert "Familiarity with TPU pod networking" in content
    assert "Design a real-time retrieval system serving 10k QPS" in content
    assert "Engineered enterprise multi-agent software system" in content
    assert "Quantified impact using Google X-Y-Z framework" in content
    assert "How does the team evaluate prompt regressions" in content
