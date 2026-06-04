from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    anthropic_api_key: str = ""
    # Bulk model for consolidation / improve / QA; judge/REM can use a stronger model.
    nocturne_model: str = "claude-sonnet-4-6"
    nocturne_judge_model: str = "claude-opus-4-8"
    nocturne_token_budget: int = 1200
    nocturne_cassette_dir: str = "runs/cassettes"

    # OpenAI-compatible provider (DigitalOcean Gradient / serverless inference).
    openai_base_url: str = "https://inference.do-ai.run/v1"
    openai_api_key: str = ""
    openai_model: str = ""       # light/bulk model: triage, consolidate, QA, improve, briefing
    openai_rem_model: str = ""   # heavier model for REM cross-thread synthesis (falls back to bulk)


def get_settings() -> Settings:
    return Settings()
