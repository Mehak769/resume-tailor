import json
import time
from typing import Any

from litellm import completion

from resume_tailor.config import settings
from resume_tailor.core.exceptions import LLMTailoringError
from resume_tailor.core.logging import logger
from resume_tailor.core.models import (
    ApplicationAnalysis,
    CoverLetter,
    JobDescription,
    ParsedResume,
    TailoredResume,
)
from resume_tailor.llm.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_USER_PROMPT_TEMPLATE,
    COVER_LETTER_SYSTEM_PROMPT,
    COVER_LETTER_USER_PROMPT_TEMPLATE,
    RESUME_STRUCTURE_PROMPT,
    RESUME_TAILOR_SYSTEM_PROMPT,
    TAILOR_USER_PROMPT_TEMPLATE,
)


def _clean_json_response(content: str) -> str:
    """Strips markdown code blocks (```json ... ```) from LLM output if present."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class LLMTailorService:
    def __init__(self, model_name: str | None = None) -> None:
        model = model_name or settings.llm_model
        # OpenRouter's routing models are named 'openrouter/free' and 'openrouter/auto'.
        # In LiteLLM, passing 'openrouter/openrouter/free' strips the first 'openrouter/'
        # provider prefix and sends model 'openrouter/free' to OpenRouter.
        if model in ("openrouter/free", "openrouter/auto"):
            model = f"openrouter/{model}"
        self.model = model
        self.api_key = settings.get_api_key_for_model(self.model)

    def _call_completion_with_fallback(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Invokes LLM completion with automatic retries and fallback models on temporary 503 spikes."""
        # Models to try in priority order
        candidates = [self.model]
        if self.model.startswith("gemini/"):
            fallbacks = ["gemini/gemini-3.5-flash-lite", "gemini/gemini-3.6-flash"]
            for fb in fallbacks:
                if fb not in candidates:
                    candidates.append(fb)

        last_error: Exception | None = None

        for model in candidates:
            api_key = settings.get_api_key_for_model(model) or self.api_key
            kwargs: dict[str, Any] = {}
            if api_key:
                kwargs["api_key"] = api_key
            if response_format:
                kwargs["response_format"] = response_format

            # Gemini 3 models require temperature=1.0 per Google API guidance
            if model.startswith("gemini/"):
                kwargs["temperature"] = 1.0
            else:
                kwargs["temperature"] = settings.llm_temperature

            for attempt in range(3):
                try:
                    response = completion(
                        model=model,
                        messages=messages,
                        **kwargs,
                    )
                    content = response.choices[0].message.content or "{}"
                    return content
                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    # Retry on 503 (high demand) or 429 (rate limit)
                    if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg:
                        logger.warning(
                            f"Model {model} busy (attempt {attempt + 1}/3). Retrying in {attempt + 1}s..."
                        )
                        time.sleep(attempt + 1)
                        continue
                    break  # If not a transient error, try next candidate model

        raise LLMTailoringError(
            f"LLM request failed across all models: {last_error}"
        ) from last_error

    def parse_raw_resume_to_structure(self, raw_text: str) -> ParsedResume:
        """Converts raw unstructured resume text into a structured ParsedResume model."""
        schema_hint = json.dumps(ParsedResume.model_json_schema(), indent=2)
        try:
            content = self._call_completion_with_fallback(
                messages=[
                    {
                        "role": "system",
                        "content": f"{RESUME_STRUCTURE_PROMPT}\nTarget JSON Schema:\n{schema_hint}",
                    },
                    {
                        "role": "user",
                        "content": f"Parse this resume into JSON:\n\n{raw_text}",
                    },
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(_clean_json_response(content))
            data["raw_text"] = raw_text
            return ParsedResume.model_validate(data)
        except Exception as e:
            if isinstance(e, LLMTailoringError):
                raise
            raise LLMTailoringError(f"Failed to structure resume with LLM: {e}") from e

    def tailor(self, resume: ParsedResume, jd: JobDescription) -> TailoredResume:
        """Tailors the structured resume for the provided job description."""
        schema_hint = json.dumps(TailoredResume.model_json_schema(), indent=2)
        user_prompt = TAILOR_USER_PROMPT_TEMPLATE.format(
            job_description=jd.raw_text,
            current_resume=resume.model_dump_json(indent=2),
        )

        try:
            content = self._call_completion_with_fallback(
                messages=[
                    {
                        "role": "system",
                        "content": f"{RESUME_TAILOR_SYSTEM_PROMPT}\nTarget JSON Schema:\n{schema_hint}",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(_clean_json_response(content))
            tailored = TailoredResume.model_validate(data)
            if not tailored.target_company and jd.company:
                tailored.target_company = jd.company
            return tailored
        except Exception as e:
            if isinstance(e, LLMTailoringError):
                raise
            raise LLMTailoringError(f"LLM tailoring process failed: {e}") from e

    def generate_cover_letter(
        self,
        resume: ParsedResume,
        jd: JobDescription,
        target_company: str,
        target_job_title: str,
    ) -> CoverLetter:
        """Generates a tailored, professional 1-page cover letter matching the candidate's experience and target role."""
        from datetime import datetime

        schema_hint = json.dumps(CoverLetter.model_json_schema(), indent=2)
        user_prompt = COVER_LETTER_USER_PROMPT_TEMPLATE.format(
            company=target_company,
            job_title=target_job_title,
            job_description=jd.raw_text,
            candidate_profile=resume.model_dump_json(indent=2),
        )

        try:
            content = self._call_completion_with_fallback(
                messages=[
                    {
                        "role": "system",
                        "content": f"{COVER_LETTER_SYSTEM_PROMPT}\nTarget JSON Schema:\n{schema_hint}",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(_clean_json_response(content))
            cover_letter = CoverLetter.model_validate(data)
            if not cover_letter.candidate_name:
                cover_letter.candidate_name = resume.contact_info.name
            if not cover_letter.target_company:
                cover_letter.target_company = target_company
            if not cover_letter.target_job_title:
                cover_letter.target_job_title = target_job_title
            if not cover_letter.date_str:
                cover_letter.date_str = datetime.now().strftime("%B %d, %Y")
            return cover_letter
        except Exception as e:
            if isinstance(e, LLMTailoringError):
                raise
            raise LLMTailoringError(f"Cover letter generation failed: {e}") from e

    def generate_analysis(
        self,
        resume: ParsedResume,
        jd: JobDescription,
        tailored_resume: TailoredResume,
        target_company: str,
    ) -> ApplicationAnalysis:
        """Generates a comprehensive Match Analysis and Interview Preparation kit."""
        schema_hint = json.dumps(ApplicationAnalysis.model_json_schema(), indent=2)
        user_prompt = ANALYSIS_USER_PROMPT_TEMPLATE.format(
            company=target_company,
            job_title=tailored_resume.target_job_title,
            ats_score=tailored_resume.ats_score_estimate,
            job_description=jd.raw_text,
            candidate_resume=resume.model_dump_json(indent=2),
        )

        try:
            content = self._call_completion_with_fallback(
                messages=[
                    {
                        "role": "system",
                        "content": f"{ANALYSIS_SYSTEM_PROMPT}\nTarget JSON Schema:\n{schema_hint}",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(_clean_json_response(content))
            analysis = ApplicationAnalysis.model_validate(data)
            if not analysis.target_company:
                analysis.target_company = target_company
            if not analysis.target_job_title:
                analysis.target_job_title = tailored_resume.target_job_title
            if not analysis.ats_score_estimate:
                analysis.ats_score_estimate = tailored_resume.ats_score_estimate
            return analysis
        except Exception as e:
            if isinstance(e, LLMTailoringError):
                raise
            raise LLMTailoringError(f"Analysis generation failed: {e}") from e
