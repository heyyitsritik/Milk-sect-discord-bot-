"""
Milestone 2: a minimal Discord data importer.

Reads a JSON file shaped like a simplified Discord export and inserts it
into the database built in Milestone 1 — proving the schema fits real
(for now: fake-but-realistic) data before scaling to a full export.

Insertion order matters because of foreign keys (Phase 3):
  users -> messages -> reactions
A message's author must exist before the message can reference it.
A reaction's user must exist before the reaction can reference it.
"""

import json
from pathlib import Path

from storage.db import get_connection
from shared.logging import get_logger

logger = get_logger(__name__)


def _ensure_user_exists(connection, user_id: str, username: str, is_bot: bool = False) -> None:
    """Insert a user row if one doesn't already exist for this user_id."""
    connection.execute(
        """
        INSERT OR IGNORE INTO users (user_id, current_username, is_bot, is_deleted_account)
        VALUES (?, ?, ?, FALSE)
        """,
        (user_id, username, is_bot),
    )


def _ensure_channel_exists(connection, channel_id: str) -> None:
    """Insert a channel row if one doesn't already exist. We don't have
    a real channel name from our sample data, so we use a placeholder —
    a real export would supply the actual name."""
    connection.execute(
        """
        INSERT OR IGNORE INTO channels (channel_id, channel_name)
        VALUES (?, ?)
        """,
        (channel_id, f"channel-{channel_id}"),
    )


def import_messages(json_path: Path) -> int:
    """
    Read the JSON file at json_path and insert every message (plus any
    users/channels/reactions it references) into the database.

    Returns the number of messages imported.
    """
    logger.info("Reading sample export from %s", json_path)
    raw_messages = json.loads(json_path.read_text())

    connection = get_connection()
    imported_count = 0

    try:
        for message in raw_messages:
            author_id = message["author"]["id"]
            username = message["author"]["username"]
            channel_id = message["channel_id"]
            is_bot = message["author"].get("is_bot", False)

            # Step 1: make sure the user and channel exist first (foreign key order).
            _ensure_user_exists(connection, author_id, username, is_bot)
            _ensure_channel_exists(connection, channel_id)


            # Step 2: insert the message itself.
            message_source = "BOT" if is_bot else "USER"
            connection.execute(
                """
                INSERT INTO messages (
                    message_id, author_id, channel_id, reply_to_message_id,
                    content, content_type, message_source, sent_at
                )
                VALUES (?, ?, ?, ?, ?, 'TEXT', ?, ?)
                """,
                (
                    message["id"],
                    author_id,
                    channel_id,
                    message.get("reply_to"),
                    message["content"],
                    message_source,
                    message["timestamp"],
                ),
            )
            imported_count += 1

            # Step 3: insert any reactions, making sure each reacting user exists first.
            for reaction in message.get("reactions", []):
                emoji = reaction["emoji"]
                for reacting_user_id in reaction["users"]:
                    _ensure_user_exists(connection, reacting_user_id, reacting_user_id, is_bot=False)
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO reactions (message_id, user_id, emoji)
                        VALUES (?, ?, ?)
                        """,
                        (message["id"], reacting_user_id, emoji),
                    )

        connection.commit()
        logger.info("Imported %d messages successfully", imported_count)
        return imported_count

    except Exception:
        connection.rollback()
        logger.exception("Import failed, rolling back all changes")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    sample_path = Path("./data/sample_export/sample_messages.json")
    import_messages(sample_path)