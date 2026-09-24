from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings (supports: "gemini/gemini-3.6-flash", "gemini/gemini-3.1-pro-preview", etc.)
    llm_model: str = "gemini/gemini-3.6-flash"
    llm_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    # Output defaults
    default_output_dir: Path = Path("./applications")
    log_level: str = "INFO"

    def get_api_key_for_model(self, model_name: str) -> str | None:
        """Resolves the appropriate API key based on the model prefix or direct settings."""
        if self.llm_api_key:
            return self.llm_api_key
        if model_name.startswith("gemini/") or "gemini" in model_name:
            return self.gemini_api_key
        if model_name.startswith("openai/") or "gpt" in model_name:
            return self.openai_api_key
        if model_name.startswith("anthropic/") or "claude" in model_name:
            return self.anthropic_api_key
        return None


settings = Settings()
