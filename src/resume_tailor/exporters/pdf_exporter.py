from pathlib import Path

from jinja2 import Environment, select_autoescape
from weasyprint import HTML

from resume_tailor.core.exceptions import ResumeExportError
from resume_tailor.core.models import TailoredResume
from resume_tailor.exporters.base import BaseResumeExporter

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page { margin: 18mm 16mm; size: A4; }
    body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #222; margin: 0; }
    h1 { font-size: 18pt; margin: 0 0 4px 0; text-transform: uppercase; color: #111; }
    .contact { font-size: 8.5pt; color: #555; margin-bottom: 14px; }
    h2 { font-size: 10.5pt; text-transform: uppercase; border-bottom: 1px solid #111; padding-bottom: 2px; margin-top: 14px; margin-bottom: 6px; letter-spacing: 0.5px; }
    .role-header { display: flex; justify-content: space-between; font-weight: bold; margin-top: 6px; }
    ul { margin: 4px 0 8px 18px; padding: 0; }
    li { margin-bottom: 2px; }
</style>
</head>
<body>
    <h1>{{ resume.contact_info.name or "Candidate Name" }}</h1>
    <div class="contact">
        {{ [resume.contact_info.email, resume.contact_info.phone, resume.contact_info.location, resume.contact_info.linkedin] | select | join(" | ") }}
    </div>

    {% if resume.summary %}
    <h2>Professional Summary</h2>
    <p>{{ resume.summary }}</p>
    {% endif %}

    {% if resume.skills %}
    <h2>Skills</h2>
    <p>{{ resume.skills | join(", ") }}</p>
    {% endif %}

    {% if resume.experience %}
    <h2>Experience</h2>
    {% for exp in resume.experience %}
        <div class="role-header">
            <span><strong>{{ exp.role }}</strong> — {{ exp.company }}</span>
            <span>{{ exp.start_date }} - {{ exp.end_date }}</span>
        </div>
        <ul>
            {% for b in exp.bullet_points %}
            <li>{{ b }}</li>
            {% endfor %}
        </ul>
    {% endfor %}
    {% endif %}

    {% if resume.education %}
    <h2>Education</h2>
    {% for edu in resume.education %}
        <div class="role-header">
            <span><strong>{{ edu.degree }}</strong> — {{ edu.institution }}</span>
            <span>{{ edu.graduation_date }}</span>
        </div>
    {% endfor %}
    {% endif %}
</body>
</html>
"""


class PDFResumeExporter(BaseResumeExporter):
    def export(self, tailored_resume: TailoredResume, output_path: Path) -> Path:
        try:
            resolved_output = output_path.resolve()
            resolved_output.parent.mkdir(parents=True, exist_ok=True)

            env = Environment(autoescape=select_autoescape(["html", "xml"]))
            template = env.from_string(HTML_TEMPLATE)
            rendered_html = template.render(resume=tailored_resume.parsed_resume)
            HTML(string=rendered_html).write_pdf(str(resolved_output))
            return resolved_output
        except Exception as e:
            if isinstance(e, ResumeExportError):
                raise
            raise ResumeExportError(f"Failed to generate PDF resume: {e}") from e
