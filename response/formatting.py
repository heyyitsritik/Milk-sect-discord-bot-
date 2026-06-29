"""
Milestone 13: response formatting (Phase 2's "response generator" box).

Deliberately simple for now — real length/style targets need Phase 5
statistics at real scale, which our small sample can't yet provide.
This proves the mechanism: raw LLM output goes through a formatting
step before being sent, rather than being sent completely unmodified.
"""

from shared.logging import get_logger

logger = get_logger(__name__)


def format_reply(raw_reply: str) -> str:
    """Strip stray whitespace and quotation marks the LLM sometimes adds."""
    cleaned = raw_reply.strip().strip('"').strip("'")
    return cleaned


if __name__ == "__main__":
    examples = ['  "yeah totally"  ', "'me too lol'", "no change needed"]
    for example in examples:
        print(repr(example), "->", repr(format_reply(example)))