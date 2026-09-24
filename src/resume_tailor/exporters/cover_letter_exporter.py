import shutil
import subprocess
from pathlib import Path

from resume_tailor.core.exceptions import ResumeExportError
from resume_tailor.core.models import ContactInfo, CoverLetter
from resume_tailor.exporters.latex_exporter import escape_latex

COVER_LETTER_TEX_TEMPLATE = r"""\documentclass[10.5pt,a4paper]{article}

\usepackage[margin=0.75in,top=0.6in,bottom=0.6in]{geometry}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{9pt}

\begin{document}

%==================== HEADER ====================
\begin{center}
    {\Large\textbf{<NAME>}}\\[1pt]
    \textbf{<TAGLINE>}\\[2pt]
    <CONTACT_LINE>
\end{center}

\vspace{-2pt}
\hrule
\vspace{10pt}

%==================== RECIPIENT & METADATA ====================
\begin{flushleft}
    <DATE>\\[8pt]
    \textbf{<RECIPIENT>}\\
    <COMPANY_NAME><COMPANY_LOCATION_LINE>
\end{flushleft}

\vspace{4pt}
\textbf{Subject: <SUBJECT>}\\[4pt]

<SALUTATION>

<OPENING_PARAGRAPH>

<BODY_PARAGRAPH_1>

<BODY_PARAGRAPH_2>

<CLOSING_PARAGRAPH>

\vspace{12pt}
<SIGN_OFF>\\[24pt]
\textbf{<NAME>}

\end{document}
"""


class CoverLetterExporter:
    """Exports tailored cover letters into a LaTeX document matching the resume style

    and compiles it into a production PDF via pdflatex.
    """

    def __init__(self, compile_pdf: bool = True) -> None:
        self.compile_pdf = compile_pdf

    def export(
        self,
        cover_letter: CoverLetter,
        contact: ContactInfo,
        output_path: Path,
    ) -> Path:
        try:
            resolved_output = output_path.resolve()
            resolved_output.parent.mkdir(parents=True, exist_ok=True)

            tex_path = resolved_output.with_suffix(".tex")

            name = escape_latex(contact.name or cover_letter.candidate_name or "Candidate Name")
            tagline = escape_latex(cover_letter.target_job_title or "Software Engineer")

            # Contact line matching resume header
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

            company_loc_line = (
                f"\\\\\n    {escape_latex(cover_letter.company_location)}"
                if cover_letter.company_location
                else ""
            )

            subject = (
                cover_letter.subject or f"Application for {cover_letter.target_job_title} Position"
            )

            body_2 = (
                escape_latex(cover_letter.body_paragraph_2) if cover_letter.body_paragraph_2 else ""
            )

            rendered = (
                COVER_LETTER_TEX_TEMPLATE.replace("<NAME>", name)
                .replace("<TAGLINE>", tagline)
                .replace("<CONTACT_LINE>", contact_line)
                .replace("<DATE>", escape_latex(cover_letter.date_str))
                .replace("<RECIPIENT>", escape_latex(cover_letter.recipient or "Hiring Team"))
                .replace("<COMPANY_NAME>", escape_latex(cover_letter.target_company or "Company"))
                .replace("<COMPANY_LOCATION_LINE>", company_loc_line)
                .replace("<SUBJECT>", escape_latex(subject))
                .replace(
                    "<SALUTATION>", escape_latex(cover_letter.salutation or "Dear Hiring Team,")
                )
                .replace("<OPENING_PARAGRAPH>", escape_latex(cover_letter.opening_paragraph))
                .replace("<BODY_PARAGRAPH_1>", escape_latex(cover_letter.body_paragraph_1))
                .replace("<BODY_PARAGRAPH_2>", body_2)
                .replace("<CLOSING_PARAGRAPH>", escape_latex(cover_letter.closing_paragraph))
                .replace("<SIGN_OFF>", escape_latex(cover_letter.sign_off or "Sincerely,"))
            )

            tex_path.write_text(rendered, encoding="utf-8")

            if self.compile_pdf and shutil.which("pdflatex"):
                self._compile_to_pdf(tex_path)

            return tex_path
        except Exception as e:
            if isinstance(e, ResumeExportError):
                raise
            raise ResumeExportError(f"Failed to export cover letter: {e}") from e

    def _compile_to_pdf(self, tex_path: Path) -> Path:
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
                return tex_path

            for ext in [".aux", ".log", ".out"]:
                aux_file = tex_path.with_suffix(ext)
                if aux_file.exists():
                    aux_file.unlink()

            return pdf_path
        except Exception:
            return tex_path
