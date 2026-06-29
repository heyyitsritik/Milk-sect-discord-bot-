"""
Milestone 6: basic behavior analysis (Phase 5).

Classical, deterministic statistics — no LLM involved. This is the
"ground truth" data that later becomes the grounded persona prompt
in a much later milestone (Phase 8).

Bot messages are excluded throughout — recall Milestone 3 tagged
message_source so this filtering is now a one-line WHERE clause,
not something every analysis function has to re-derive.
"""

from collections import Counter

from storage.db import get_connection
from shared.logging import get_logger

logger = get_logger(__name__)

# A tiny set of common English words to exclude from word-frequency
# stats — otherwise "the", "a", "and" would dominate every result and
# tell us nothing distinctive about the server, per Phase 5's TF-IDF
# discussion (this is a simplified stand-in, not real TF-IDF yet —
# that needs a much larger dataset to be meaningful).
_COMMON_WORDS = {"the", "a", "an", "is", "it", "to", "and", "i", "you", "this", "that"}


def _get_human_message_texts() -> list[str]:
    """Fetch every non-bot message's content."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT content FROM messages WHERE message_source = 'USER' AND content IS NOT NULL"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        connection.close()


def compute_capitalization_ratio(messages: list[str]) -> float:
    """Fraction of messages that are entirely lowercase (ignoring punctuation/emoji)."""
    if not messages:
        return 0.0
    lowercase_count = sum(1 for m in messages if m == m.lower())
    return lowercase_count / len(messages)


def compute_average_message_length(messages: list[str]) -> float:
    """Average number of words per message."""
    if not messages:
        return 0.0
    word_counts = [len(m.split()) for m in messages]
    return sum(word_counts) / len(word_counts)


def compute_word_frequency(messages: list[str], top_n: int = 10) -> list[tuple[str, int]]:
    """
    Simple word frequency count, excluding a small set of common English
    words. NOT real TF-IDF — that needs a much larger dataset than 6
    sample messages to produce anything meaningful. This is a stand-in
    that proves the counting mechanism works.
    """
    counter = Counter()
    for message in messages:
        words = message.lower().split()
        for word in words:
            cleaned_word = word.strip(".,!?'\"")
            if cleaned_word and cleaned_word not in _COMMON_WORDS:
                counter[cleaned_word] += 1
    return counter.most_common(top_n)


def run_style_analysis() -> dict:
    """Compute and log all basic style statistics. Returns them as a dict too."""
    messages = _get_human_message_texts()
    logger.info("Running style analysis on %d human messages", len(messages))

    capitalization_ratio = compute_capitalization_ratio(messages)
    average_length = compute_average_message_length(messages)
    top_words = compute_word_frequency(messages)

    logger.info("Lowercase ratio: %.2f", capitalization_ratio)
    logger.info("Average message length (words): %.2f", average_length)
    logger.info("Top words: %s", top_words)

    return {
        "capitalization_ratio": capitalization_ratio,
        "average_message_length": average_length,
        "top_words": top_words,
        "sample_size": len(messages),
    }


if __name__ == "__main__":
    run_style_analysis()