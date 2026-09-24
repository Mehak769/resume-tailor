class ResumeTailorError(Exception):
    """Base exception for all domain errors."""


class ResumeParseError(ResumeTailorError):
    """Raised when parsing a resume fails."""


class JobDescriptionScraperError(ResumeTailorError):
    """Raised when fetching or extracting JD fails."""


class LLMTailoringError(ResumeTailorError):
    """Raised when LLM invocation or structured output generation fails."""


class ResumeExportError(ResumeTailorError):
    """Raised when exporting the tailored resume fails."""
