"""
Milestone 12: the engagement decision (Phase 2's "cheap gatekeeper").

Deliberately rules-based, NOT an LLM call. This must stay fast and
free to run on every single incoming message, since most messages
in a busy server should never trigger the expensive retrieval/prompt/
LLM pipeline at all.
"""

import random

from shared.logging import get_logger

logger = get_logger(__name__)

# Tunable — per Phase 11, behavior knobs like this should eventually
# move into config/settings.py so they're adjustable without a code
# change. For this milestone, a constant here is fine.
RANDOM_ENGAGEMENT_CHANCE = 0.10

BOT_USER_ID = "persona_bot"  # placeholder until Milestone 14 gives us a real bot user id


def should_respond(message_content: str, author_id: str, mentions_bot: bool, is_reply_to_bot: bool) -> bool:
    """
    Decide whether the bot should respond to this message at all.
    Returns True/False — no side effects, no network calls.
    """
    if author_id == BOT_USER_ID:
        logger.info("Skipping — message is from the bot itself")
        return False

    if mentions_bot or is_reply_to_bot:
        logger.info("Responding — directly mentioned or replied to")
        return True

    roll = random.random()
    if roll < RANDOM_ENGAGEMENT_CHANCE:
        logger.info("Responding — random engagement triggered (roll=%.2f)", roll)
        return True

    logger.info("Skipping — no trigger matched (roll=%.2f)", roll)
    return False


if __name__ == "__main__":
    # Proof 1: bot's own message should NEVER trigger a response.
    print("Bot's own message:", should_respond("hello", BOT_USER_ID, mentions_bot=False, is_reply_to_bot=False))

    # Proof 2: a direct mention should ALWAYS trigger a response.
    print("Direct mention:", should_respond("@bot help", "u1", mentions_bot=True, is_reply_to_bot=False))

    # Proof 3: run an ordinary message 20 times — roughly ~10% should return True,
    # not exactly 2/20 every time (it's random), but in the right ballpark.
    print("--- 20 ordinary messages, no mention, no reply ---")
    true_count = sum(
        should_respond("just chatting", "u2", mentions_bot=False, is_reply_to_bot=False)
        for _ in range(20)
    )
    print(f"Responded to {true_count} out of 20 (expect roughly 1-4)")