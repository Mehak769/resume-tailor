from datetime import datetime
from pathlib import Path

from resume_tailor.core.exceptions import ResumeExportError
from resume_tailor.core.models import ApplicationAnalysis, TailoredResume


class AnalysisExporter:
    """Exports structured application analysis, change audit logs, and interview prep

    kits into a clean, comprehensive Markdown report (analysis.md).
    """

    def export(
        self,
        analysis: ApplicationAnalysis,
        tailored_resume: TailoredResume,
        output_path: Path,
    ) -> Path:
        try:
            resolved_output = output_path.resolve()
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            md_path = resolved_output.with_suffix(".md")

            date_str = datetime.now().strftime("%B %d, %Y")
            company = analysis.target_company or tailored_resume.target_company or "Company"
            role = analysis.target_job_title or tailored_resume.target_job_title or "Role"
            score = analysis.ats_score_estimate or tailored_resume.ats_score_estimate

            lines: list[str] = [
                f"# 🎯 Application Match & Interview Prep Report: {company}",
                "",
                f"- **Target Role:** {role}",
                f"- **Target Company:** {company}",
                f"- **Estimated ATS Alignment Score:** {score}/100",
                f"- **Generated Date:** {date_str}",
                "",
                "---",
                "",
                "## 📊 Executive Match Summary",
                "",
                "### 🌟 Key Candidate Strengths",
            ]

            if analysis.key_strengths:
                for s in analysis.key_strengths:
                    lines.append(f"- {s}")
            else:
                lines.append(
                    "- Strong domain alignment with software engineering and cloud data systems."
                )

            lines.extend(
                [
                    "",
                    "### 🔍 Skill Gaps & Strategic Focus Areas",
                ]
            )

            if analysis.skill_gaps_or_suggestions:
                for g in analysis.skill_gaps_or_suggestions:
                    lines.append(f"- {g}")
            else:
                lines.append(
                    "- Review company-specific domain architectures and proprietary internal tooling."
                )

            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 🛠️ Resume Optimization Audit Trail",
                    "",
                    "| Section | Original Bullet / Text | Tailored Bullet / Text | Optimization Rationale |",
                    "|---|---|---|---|",
                ]
            )

            if tailored_resume.changes:
                for change in tailored_resume.changes:
                    sec = change.section.replace("|", r"\|").strip()
                    orig = change.original.replace("|", r"\|").replace("\n", " ").strip()
                    tail = change.tailored.replace("|", r"\|").replace("\n", " ").strip()
                    reas = change.reasoning.replace("|", r"\|").replace("\n", " ").strip()
                    lines.append(f"| **{sec}** | {orig} | {tail} | {reas} |")
            else:
                lines.append(
                    "| Summary | Master profile | Preserved baseline qualifications | Accurate domain representation |"
                )

            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 🎙️ Interview Preparation Kit",
                    "",
                ]
            )

            tech_questions = [
                q for q in analysis.interview_questions if q.category.lower() != "behavioral"
            ]
            behav_questions = [
                q for q in analysis.interview_questions if q.category.lower() == "behavioral"
            ]

            if tech_questions:
                lines.extend(
                    [
                        "### 💡 High-Yield Technical & Architecture Questions",
                        "",
                    ]
                )
                for idx, q in enumerate(tech_questions, 1):
                    lines.append(f"#### {idx}. [{q.category}] {q.question}")
                    if q.why_asked:
                        lines.append(f"**Why the interviewer asks this:** {q.why_asked}\n")
                    if q.recommended_talking_points:
                        lines.append("**Recommended Talking Points:**")
                        for pt in q.recommended_talking_points:
                            lines.append(f"- {pt}")
                    lines.append("")

            if behav_questions:
                lines.extend(
                    [
                        "### 🤝 Behavioral & Leadership Scenarios",
                        "",
                    ]
                )
                for idx, q in enumerate(behav_questions, 1):
                    lines.append(f"#### {idx}. [Behavioral] {q.question}")
                    if q.why_asked:
                        lines.append(f"**Why the interviewer asks this:** {q.why_asked}\n")
                    if q.recommended_talking_points:
                        lines.append("**Recommended Talking Points (STAR Method):**")
                        for pt in q.recommended_talking_points:
                            lines.append(f"- {pt}")
                    lines.append("")

            if analysis.smart_questions_to_ask_interviewer:
                lines.extend(
                    [
                        "---",
                        "",
                        "## 🙋 High-Impact Questions to Ask the Interviewer",
                        "",
                    ]
                )
                for idx, sq in enumerate(analysis.smart_questions_to_ask_interviewer, 1):
                    lines.append(f"{idx}. {sq}")
                lines.append("")

            lines.extend(
                [
                    "---",
                    "*Report generated automatically by [Resume Tailor](https://github.com/Mehak769/resume-tailor).*",
                    "",
                ]
            )

            md_content = "\n".join(lines)
            md_path.write_text(md_content, encoding="utf-8")
            return md_path

        except Exception as e:
            if isinstance(e, ResumeExportError):
                raise
            raise ResumeExportError(f"Failed to export analysis report: {e}") from e
