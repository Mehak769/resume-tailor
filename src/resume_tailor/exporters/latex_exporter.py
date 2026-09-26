import shutil
import subprocess
from pathlib import Path

from resume_tailor.core.exceptions import ResumeExportError
from resume_tailor.core.models import TailoredResume
from resume_tailor.exporters.base import BaseResumeExporter

LATEX_TEMPLATE = r"""\documentclass[9pt,a4paper]{extarticle}

\usepackage{cmap}
\pdfgentounicode=1
\pdfinterwordspaceon

\usepackage[margin=0.35in,top=0.28in,bottom=0.22in]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

\titleformat{\section}{\normalsize\bfseries}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{2.5pt}{1.5pt}

\setlist[itemize]{
    leftmargin=11pt,
    itemsep=0.5pt,
    topsep=1pt,
    parsep=0pt,
    partopsep=0pt
}

\begin{document}

%==================== HEADER ====================

\begin{center}
    {\Large\textbf{<NAME>}}\par\vspace{1pt}
    \textbf{<TAGLINE>}\par\vspace{2pt}
    <CONTACT_LINE>
\end{center}

%==================== PROFILE ====================

\section{Professional Summary}

<SUMMARY>

%==================== SKILLS ====================

\section{Technical Skills}

<SKILLS>

%==================== EXPERIENCE ====================

\section{Professional Experience}

<EXPERIENCE>

%==================== PROJECTS ====================

<PROJECTS_SECTION>

%==================== EDUCATION ====================

\section{Education}

<EDUCATION>

\end{document}
"""


def escape_latex(text: str) -> str:
    """Escapes characters that have special meaning in LaTeX."""
    if not text:
        return ""
    # Map special characters to their LaTeX escaped counterparts
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for orig, repl in replacements:
        text = text.replace(orig, repl)
    return text


class LaTeXResumeExporter(BaseResumeExporter):
    """Exports tailored resumes into a beautifully typeset LaTeX (.tex) document

    and optionally compiles it into a production-ready PDF via pdflatex.
    """

    def __init__(self, compile_pdf: bool = True) -> None:
        self.compile_pdf = compile_pdf

    def export(self, tailored_resume: TailoredResume, output_path: Path) -> Path:
        try:
            resolved_output = output_path.resolve()
            resolved_output.parent.mkdir(parents=True, exist_ok=True)

            # Ensure file ends in .tex
            tex_path = resolved_output.with_suffix(".tex")

            p_res = tailored_resume.parsed_resume
            contact = p_res.contact_info

            # Build Header
            name = escape_latex(contact.name or "Candidate Name")
            tagline = escape_latex(tailored_resume.target_job_title)

            contact_parts: list[str] = []
            if contact.phone:
                contact_parts.append(escape_latex(contact.phone))
            if contact.email:
                clean_email = contact.email.strip()
                mailto_link = (
                    clean_email if clean_email.startswith("mailto:") else f"mailto:{clean_email}"
                )
                contact_parts.append(rf"\href{{{mailto_link}}}{{{escape_latex(clean_email)}}}")
            if contact.linkedin:
                raw_link = contact.linkedin.strip()
                full_link = (
                    raw_link
                    if raw_link.startswith(("http://", "https://"))
                    else f"https://{raw_link}"
                )
                link_clean = raw_link.replace("https://", "").replace("http://", "").rstrip("/")
                contact_parts.append(rf"\href{{{full_link}}}{{{escape_latex(link_clean)}}}")
            if contact.github:
                raw_gh = contact.github.strip()
                full_gh = (
                    raw_gh if raw_gh.startswith(("http://", "https://")) else f"https://{raw_gh}"
                )
                gh_clean = raw_gh.replace("https://", "").replace("http://", "").rstrip("/")
                contact_parts.append(rf"\href{{{full_gh}}}{{{escape_latex(gh_clean)}}}")
            if contact.location:
                contact_parts.append(escape_latex(contact.location))

            contact_line = r" \;|\; ".join(contact_parts)

            # Build Summary
            summary_text = escape_latex(p_res.summary)

            # Build Skills
            if p_res.skills:
                categorized = [s for s in p_res.skills if ":" in s]
                if categorized:
                    skill_lines: list[str] = []
                    for c in categorized:
                        parts = c.split(":", 1)
                        cat_name = escape_latex(parts[0].strip())
                        cat_vals = escape_latex(parts[1].strip())
                        skill_lines.append(rf"\textbf{{{cat_name}:}} {cat_vals}\\")
                    skills_formatted = "\n".join(skill_lines)
                else:
                    skills_formatted = r"\textbf{Core Competencies:} " + ", ".join(
                        [escape_latex(s) for s in p_res.skills]
                    )
            else:
                skills_formatted = ""

            # Build Experience
            exp_blocks: list[str] = []
            for exp in p_res.experience:
                role = escape_latex(exp.role)
                company = escape_latex(exp.company)
                location = escape_latex(exp.location)
                date_str = escape_latex(f"{exp.start_date} -- {exp.end_date}".strip(" -"))

                loc_line = rf" \hfill {location}\\" if location else r"\\"
                header_line = rf"\textbf{{{role} \;|\; {company}}}{loc_line}"
                date_line = rf"\textit{{{date_str}}}" if date_str else ""

                bullet_lines = "\n".join(
                    [rf"    \item {escape_latex(b)}" for b in exp.bullet_points]
                )
                block = f"{header_line}\n{date_line}\n\\begin{{itemize}}\n{bullet_lines}\n\\end{{itemize}}"
                exp_blocks.append(block)

            experience_text = "\n\n".join(exp_blocks)

            # Build Projects
            if p_res.projects:
                proj_blocks: list[str] = [r"\section{Key Projects}"]
                for proj in p_res.projects:
                    title = escape_latex(proj.title)
                    tech_str = (
                        rf" \;|\; \textit{{{', '.join([escape_latex(t) for t in proj.technologies])}}}"
                        if proj.technologies
                        else ""
                    )
                    header = rf"\textbf{{{title}}}{tech_str}"
                    bullets = "\n".join([rf"    \item {escape_latex(d)}" for d in proj.description])
                    proj_blocks.append(f"{header}\n\\begin{{itemize}}\n{bullets}\n\\end{{itemize}}")
                projects_section = "\n\n".join(proj_blocks)
            else:
                projects_section = ""

            # Build Education
            edu_blocks: list[str] = []
            for edu in p_res.education:
                deg = escape_latex(edu.degree)
                inst = escape_latex(edu.institution)
                grad = escape_latex(edu.graduation_date)
                grad_str = rf" \hfill \textit{{{grad}}}" if grad else ""
                edu_blocks.append(rf"\textbf{{{deg}}} --- {inst}{grad_str}\\")
            education_text = "\n".join(edu_blocks)

            # Assemble Document
            rendered_tex = (
                LATEX_TEMPLATE.replace("<NAME>", name)
                .replace("<TAGLINE>", tagline)
                .replace("<CONTACT_LINE>", contact_line)
                .replace("<SUMMARY>", summary_text)
                .replace("<SKILLS>", skills_formatted)
                .replace("<EXPERIENCE>", experience_text)
                .replace("<PROJECTS_SECTION>", projects_section)
                .replace("<EDUCATION>", education_text)
            )

            tex_path.write_text(rendered_tex, encoding="utf-8")

            # Compile to PDF if requested and pdflatex is present
            if self.compile_pdf and shutil.which("pdflatex"):
                self._compile_to_pdf(tex_path)

            return tex_path

        except Exception as e:
            if isinstance(e, ResumeExportError):
                raise
            raise ResumeExportError(f"Failed to export LaTeX resume: {e}") from e

    def _compile_to_pdf(self, tex_path: Path) -> Path:
        """Invokes pdflatex to compile the .tex into a .pdf and cleans auxiliary files."""
        parent_dir = tex_path.parent
        pdf_path = tex_path.with_suffix(".pdf")

        try:
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={parent_dir}",
                str(tex_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                # Still keep the .tex file even if compilation issues arise
                return tex_path

            # Clean up auxiliary LaTeX files (.aux, .log, .out)
            for ext in [".aux", ".log", ".out"]:
                aux_file = tex_path.with_suffix(ext)
                if aux_file.exists():
                    aux_file.unlink()

            return pdf_path
        except Exception:
            # Fallback gracefully to returning the .tex file
            return tex_path
