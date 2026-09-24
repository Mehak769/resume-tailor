from pathlib import Path

from pypdf import PdfReader

from resume_tailor.core.exceptions import ResumeParseError
from resume_tailor.core.models import ParsedResume
from resume_tailor.parsers.base import BaseResumeParser


class PDFResumeParser(BaseResumeParser):
    def parse(self, file_path: Path) -> ParsedResume:
        resolved_path = file_path.resolve()
        if not resolved_path.exists():
            raise ResumeParseError(f"PDF file not found: {file_path}")

        try:
            reader = PdfReader(str(resolved_path))
            extracted_text: list[str] = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text.append(page_text)

            full_text = "\n".join(extracted_text).strip()
            if not full_text:
                raise ResumeParseError(
                    f"No extractable text found in {file_path}. Is it a scanned image?"
                )

            return ParsedResume(raw_text=full_text)

        except Exception as e:
            if isinstance(e, ResumeParseError):
                raise
            raise ResumeParseError(f"Failed to parse PDF {file_path}: {e}") from e
