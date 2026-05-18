from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    anthropic_api_key: str = ""
    nocturne_model: str = "claude-opus-4-7"
    nocturne_memory_path: str = "./memory.json"
    nocturne_max_tool_iters: int = 8


def get_settings() -> Settings:
    return Settings()
