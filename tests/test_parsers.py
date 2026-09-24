from pathlib import Path

import pytest

from resume_tailor.core.exceptions import ResumeParseError
from resume_tailor.parsers.docx_parser import DocxResumeParser
from resume_tailor.parsers.pdf_parser import PDFResumeParser


def test_pdf_parser_nonexistent_file():
    parser = PDFResumeParser()
    with pytest.raises(ResumeParseError):
        parser.parse(Path("non_existent_file.pdf"))


def test_docx_parser_nonexistent_file():
    parser = DocxResumeParser()
    with pytest.raises(ResumeParseError):
        parser.parse(Path("non_existent_file.docx"))
