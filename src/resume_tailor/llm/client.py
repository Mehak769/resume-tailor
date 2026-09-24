import json
import time
from typing import Any

from litellm import completion

from resume_tailor.config import settings
from resume_tailor.core.exceptions import LLMTailoringError
from resume_tailor.core.logging import logger
from resume_tailor.core.models import JobDescription, ParsedResume, TailoredResume
from resume_tailor.llm.prompts import (
    RESUME_STRUCTURE_PROMPT,
    RESUME_TAILOR_SYSTEM_PROMPT,
    TAILOR_USER_PROMPT_TEMPLATE,
)


class LLMTailorService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model = model_name or settings.llm_model
        self.api_key = settings.get_api_key_for_model(self.model)

    def _call_completion_with_fallback(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Invokes LLM completion with automatic retries and fallback models on temporary 503 spikes."""
        # Models to try in priority order
        candidates = [self.model]
        if "gemini" in self.model:
            fallbacks = ["gemini/gemini-3.5-flash-lite", "gemini/gemini-3.6-flash"]
            for fb in fallbacks:
                if fb not in candidates:
                    candidates.append(fb)

        last_error: Exception | None = None

        for model in candidates:
            api_key = settings.get_api_key_for_model(model) or self.api_key
            kwargs: dict[str, Any] = {
                "num_retries": 2,
            }
            if api_key:
                kwargs["api_key"] = api_key
            if response_format:
                kwargs["response_format"] = response_format

            # Gemini 3 models require temperature=1.0 per Google API guidance
            if "gemini" in model:
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
            data = json.loads(content)
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
            data = json.loads(content)
            tailored = TailoredResume.model_validate(data)
            if not tailored.target_company and jd.company:
                tailored.target_company = jd.company
            return tailored
        except Exception as e:
            if isinstance(e, LLMTailoringError):
                raise
            raise LLMTailoringError(f"LLM tailoring process failed: {e}") from e
