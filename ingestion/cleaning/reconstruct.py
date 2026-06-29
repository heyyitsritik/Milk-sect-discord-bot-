"""
Milestone 5: conversation reconstruction (Phase 4).

Computes a conversation_id for every message using:
  1. Hard links — explicit reply_to_message_id pointers (ground truth)
  2. Soft links — time-proximity fallback for messages with no reply pointer

This is probabilistic for soft-linked messages, not guaranteed-correct —
exactly the honest limitation flagged in Phase 4. Worth spot-checking the
output by eye, not just trusting it blindly.
"""

import uuid
from datetime import datetime, timedelta

from storage.db import get_connection
from shared.logging import get_logger

logger = get_logger(__name__)

# Soft-link time window: messages in the same channel within this gap
# are treated as candidates for the same conversation.
SOFT_LINK_WINDOW = timedelta(minutes=5)


def _parse_timestamp(ts: str) -> datetime:
    # Our sample timestamps look like "2026-01-10T14:22:01.000Z"
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def reconstruct_conversations() -> int:
    """
    Read every message from the database, compute a conversation_id for
    each one, and write that back. Returns the number of messages updated.
    """
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT message_id, channel_id, reply_to_message_id, sent_at
            FROM messages
            ORDER BY sent_at
            """
        ).fetchall()

        message_id_to_conversation_id: dict[str, str] = {}
        # Tracks the most recent message seen so far, per channel —
        # needed for the soft-link time-proximity check.
        last_message_in_channel: dict[str, tuple[str, datetime]] = {}

        for message_id, channel_id, reply_to_message_id, sent_at_str in rows:
            sent_at = _parse_timestamp(sent_at_str)

            if reply_to_message_id and reply_to_message_id in message_id_to_conversation_id:
                # Hard link: join the conversation of the message we're replying to.
                conversation_id = message_id_to_conversation_id[reply_to_message_id]
                logger.info(
                    "Message %s hard-linked to conversation of %s",
                    message_id, reply_to_message_id,
                )
            else:
                # No usable hard link — try the soft-link fallback.
                previous = last_message_in_channel.get(channel_id)
                if previous is not None:
                    previous_message_id, previous_sent_at = previous
                    gap = sent_at - previous_sent_at
                    if gap <= SOFT_LINK_WINDOW:
                        conversation_id = message_id_to_conversation_id[previous_message_id]
                        logger.info(
                            "Message %s soft-linked to conversation of %s (gap: %s)",
                            message_id, previous_message_id, gap,
                        )
                    else:
                        conversation_id = str(uuid.uuid4())
                        logger.info(
                            "Message %s starts a NEW conversation (gap too large: %s)",
                            message_id, gap,
                        )
                else:
                    # First message ever seen in this channel.
                    conversation_id = str(uuid.uuid4())
                    logger.info("Message %s starts a NEW conversation (first in channel)", message_id)

            message_id_to_conversation_id[message_id] = conversation_id
            last_message_in_channel[channel_id] = (message_id, sent_at)

        # Write all computed conversation_ids back to the database.
        for message_id, conversation_id in message_id_to_conversation_id.items():
            connection.execute(
                "UPDATE messages SET conversation_id = ? WHERE message_id = ?",
                (conversation_id, message_id),
            )

        connection.commit()
        logger.info("Reconstructed conversation_id for %d messages", len(message_id_to_conversation_id))
        return len(message_id_to_conversation_id)

    finally:
        connection.close()


if __name__ == "__main__":
    reconstruct_conversations()