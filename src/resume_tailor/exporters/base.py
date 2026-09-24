from abc import ABC, abstractmethod
from pathlib import Path

from resume_tailor.core.models import TailoredResume


class BaseResumeExporter(ABC):
    @abstractmethod
    def export(self, tailored_resume: TailoredResume, output_path: Path) -> Path:
        """Writes the tailored resume content to disk and returns the resolved path."""
        pass
