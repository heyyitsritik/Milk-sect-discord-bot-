"""
Centralized logging setup.

Every module in this project logs through this same configuration,
so format, level, and destination are controlled in one place.

Usage in any other file:

    from shared.logging import get_logger
    logger = get_logger(__name__)
    logger.info("something happened")

NEVER log secret values (API keys, tokens). This file does not redact
automatically — that discipline is on every caller.
"""

import logging
import sys
from pathlib import Path

_CONFIGURED = False


def configure_logging(log_level: str = "INFO", log_dir: str = "./data/logs") -> None:
    """
    Configure the root logger once. Safe to call multiple times — only the
    first call takes effect.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "bot.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger scoped to the calling module's name."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)