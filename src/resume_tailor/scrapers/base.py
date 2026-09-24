from abc import ABC, abstractmethod

from resume_tailor.core.models import JobDescription


class BaseJDScraper(ABC):
    @abstractmethod
    def scrape(self, source: str) -> JobDescription:
        """Extracts job posting details from a URL or raw text string."""
        pass
