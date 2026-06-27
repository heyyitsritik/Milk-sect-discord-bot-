"""
Centralized configuration.

This is the ONE place that reads from the environment / .env file.
Every other module should import `settings` from here rather than
reading os.environ directly.

This file does NOT log secret values. Never add logging here that
prints them.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Discord ---
    discord_bot_token: str = ""

    # --- LLM provider ---
    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_model_name: str = "deepseek-chat"

    # --- Embeddings ---
    embedding_api_key: str = ""
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # --- Storage ---
    database_url: str = "sqlite:///./data/bot.db"

    # --- Vector database ---
    vector_db_backend: str = "chroma"
    vector_db_path: str = "./data/chroma"
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # --- App behavior ---
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


# A single shared instance — import THIS, don't create your own Settings() elsewhere.
settings = Settings()