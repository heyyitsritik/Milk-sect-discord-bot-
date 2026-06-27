"""
Milestone 0 entry point.

Running this file proves the skeleton works:
  - config loads from .env without crashing
  - logging is wired up and writes to both console and a log file
  - no secret values are ever printed
"""

from config.settings import settings
from shared.logging import configure_logging, get_logger

configure_logging(log_level=settings.log_level)
logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting discord-persona-bot (Milestone 0: scaffolding check)")
    logger.info("Environment: %s", settings.environment)
    logger.info("Log level: %s", settings.log_level)

    secret_fields = {
        "discord_bot_token": settings.discord_bot_token,
        "llm_api_key": settings.llm_api_key,
        "embedding_api_key": settings.embedding_api_key,
    }
    for field_name, value in secret_fields.items():
        status = "present" if value else "MISSING"
        logger.info("Secret check — %s: %s", field_name, status)

    logger.info("Database URL configured: %s", settings.database_url)
    logger.info("Vector DB backend: %s", settings.vector_db_backend)
    logger.info("Milestone 0 scaffolding check complete.")


if __name__ == "__main__":
    main()