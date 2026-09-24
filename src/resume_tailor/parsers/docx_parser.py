from pathlib import Path

import docx

from resume_tailor.core.exceptions import ResumeParseError
from resume_tailor.core.models import ParsedResume
from resume_tailor.parsers.base import BaseResumeParser


class DocxResumeParser(BaseResumeParser):
    def parse(self, file_path: Path) -> ParsedResume:
        resolved_path = file_path.resolve()
        if not resolved_path.exists():
            raise ResumeParseError(f"DOCX file not found: {file_path}")

        try:
            doc = docx.Document(str(resolved_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs).strip()

            if not full_text:
                raise ResumeParseError(f"DOCX document at {file_path} is empty.")

            return ParsedResume(raw_text=full_text)

        except Exception as e:
            if isinstance(e, ResumeParseError):
                raise
            raise ResumeParseError(f"Failed to parse DOCX {file_path}: {e}") from e
