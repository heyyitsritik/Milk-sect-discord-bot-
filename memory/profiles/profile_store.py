"""
Milestone 8: user profile storage (Phase 6).

Profiles are ALWAYS accessed by a direct, keyed lookup on user_id —
never through vector similarity search. This file is intentionally
simple and has no dependency on retrieval/vector_store.py at all,
which is itself proof that the separation is real, not just a
comment in a docstring.
"""

import json
from datetime import datetime, timezone

from storage.db import get_connection
from shared.logging import get_logger

logger = get_logger(__name__)


def save_profile_facts(user_id: str, facts: dict) -> None:
    """
    Save (or overwrite) the facts known about a user. Per Phase 6,
    semantic facts are overwritten wholesale here, not merged/stacked —
    the caller is responsible for passing the complete, current set of
    facts they want stored.
    """
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO user_profiles (user_id, facts_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                facts_json = excluded.facts_json,
                updated_at = excluded.updated_at
            """,
            (user_id, json.dumps(facts), datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
        logger.info("Saved profile for user %s: %s", user_id, facts)
    finally:
        connection.close()


def get_profile(user_id: str) -> dict | None:
    """
    Fetch a user's profile by direct lookup. Returns None if no profile
    exists yet for this user — that's a normal, expected case, not an error.
    """
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT facts_json, updated_at FROM user_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            logger.info("No profile found for user %s", user_id)
            return None
        facts_json, updated_at = row
        return {"facts": json.loads(facts_json), "updated_at": updated_at}
    finally:
        connection.close()


if __name__ == "__main__":
    # Proof: save a profile, fetch it back, confirm it's an exact direct
    # lookup — no similarity search, no vector store import anywhere above.
    save_profile_facts("u1", {"job": "ML engineer", "interest": "vedic astrology"})
    result = get_profile("u1")
    logger.info("Fetched profile for u1: %s", result)

    # Also prove a non-existent user returns None cleanly.
    missing = get_profile("u_does_not_exist")
    logger.info("Fetched profile for nonexistent user: %s", missing)