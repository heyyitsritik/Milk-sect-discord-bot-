"""
Database connection handling.

This file is the ONLY place that opens a raw connection to the database.
Every other file that needs to read/write data should go through functions
defined here (or in future storage files), not open their own connection.

Why SQLite for now: it's a single file on disk, perfect for local
development with zero setup. Phase 7/11's "swappable components"
principle means we can move to a different database later without
rewriting the rest of the app — only this file would change.
"""

import sqlite3
from pathlib import Path

from shared.logging import get_logger

logger = get_logger(__name__)

# This matches DATABASE_URL's file path in spirit, kept simple for now —
# we'll wire this fully to settings.database_url in a later milestone.
DB_PATH = Path("./data/bot.db")
SCHEMA_PATH = Path("./storage/schema.sql")


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the SQLite database file, creating the
    containing folder if it doesn't exist yet.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    # Enforces FOREIGN KEY rules — SQLite has this OFF by default,
    # which would silently let us break the "ID must reference a
    # real row" guarantee from Phase 3.
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_schema() -> None:
    """
    Read schema.sql and execute it against the database, creating
    every table if it doesn't already exist.
    """
    logger.info("Initializing database schema from %s", SCHEMA_PATH)
    schema_sql = SCHEMA_PATH.read_text()

    connection = get_connection()
    try:
        connection.executescript(schema_sql)
        connection.commit()
        logger.info("Schema initialized successfully at %s", DB_PATH)
    finally:
        connection.close()


def list_tables() -> list[str]:
    """Return the names of all tables currently in the database — useful for verifying Milestone 1's test criterion."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_schema()
    tables = list_tables()
    logger.info("Tables now in database: %s", tables)