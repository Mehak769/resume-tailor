from abc import ABC, abstractmethod
from pathlib import Path

from resume_tailor.core.models import ParsedResume


class BaseResumeParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedResume:
        """Parses the given resume file into a structured ParsedResume object."""
        pass
