import re
from pathlib import Path

from resume_tailor.core.exceptions import ResumeParseError
from resume_tailor.core.models import ParsedResume
from resume_tailor.parsers.base import BaseResumeParser


class LaTeXResumeParser(BaseResumeParser):
    """Parses a LaTeX (.tex) resume and converts it to clean structured text for the LLM."""

    def parse(self, file_path: Path) -> ParsedResume:
        resolved_path = file_path.resolve()
        if not resolved_path.exists():
            raise ResumeParseError(f"LaTeX file not found: {file_path}")

        try:
            raw_content = resolved_path.read_text(encoding="utf-8")
            clean_text = self._strip_latex_formatting(raw_content)

            if not clean_text or len(clean_text.strip()) < 50:
                raise ResumeParseError(f"LaTeX document at {file_path} yielded insufficient text.")

            return ParsedResume(raw_text=clean_text)

        except Exception as e:
            if isinstance(e, ResumeParseError):
                raise
            raise ResumeParseError(f"Failed to parse LaTeX file {file_path}: {e}") from e

    def _strip_latex_formatting(self, tex: str) -> str:
        """Removes LaTeX macro syntax and normalizes text for LLM comprehension."""
        # 1. Remove comments
        lines = [line for line in tex.splitlines() if not line.strip().startswith("%")]
        tex = "\n".join(lines)

        # 2. Extract content from \begin{document} ... \end{document}
        doc_match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", tex, re.DOTALL)
        if doc_match:
            tex = doc_match.group(1)

        # 3. Clean styling / font commands that may touch other commands
        tex = re.sub(
            r"\\(Huge|huge|LARGE|Large|large|normalsize|small|footnotesize|scriptsize|tiny|bfseries|itshape)\b\s*",
            " ",
            tex,
        )

        # 4. Replace content-bearing commands
        tex = re.sub(r"\\section\{([^}]+)\}", r"\n\n### \1\n", tex)
        tex = re.sub(r"\\textbf\{([^}]+)\}", r" \1 ", tex)
        tex = re.sub(r"\\textit\{([^}]+)\}", r" \1 ", tex)
        tex = re.sub(r"\\href\{[^}]+\}\{([^}]+)\}", r" \1 ", tex)
        tex = re.sub(r"\\item\s+", r"- ", tex)

        # 5. Remove remaining control sequences and spacing tags
        tex = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{([^}]*)\})?", r" ", tex)
        tex = tex.replace(r"\&", "&").replace(r"\%", "%").replace(r"\$", "$")
        tex = tex.replace(r"\_", "_").replace(r"\\", "\n")
        tex = tex.replace(r"\;", " ").replace(r"\quad", " ")

        # 6. Clean up excessive whitespace and braces
        tex = tex.replace("{", " ").replace("}", " ")
        clean_lines = [line.strip() for line in tex.splitlines() if line.strip()]
        return "\n".join(clean_lines)
