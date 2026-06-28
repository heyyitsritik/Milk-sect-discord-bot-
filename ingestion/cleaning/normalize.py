"""
Milestone 4: text normalization (Phase 4).

These functions are pure — given the same input, they always return the
same output, with no database or network calls. That makes them easy to
test in isolation before wiring them into the import pipeline.

Emoji are deliberately NOT modified here. Per the Phase 4 decision, raw
stored content keeps the original emoji exactly as typed; normalization
for statistics happens later, at analysis time, not at storage time.
"""

import re
import unicodedata

from shared.logging import get_logger

logger = get_logger(__name__)


def normalize_unicode(text: str) -> str:
    """
    Convert text to NFC (Normalization Form C) — one canonical encoding
    for visually-identical characters. Prevents two messages that look
    the same on screen from being treated as different strings.
    """
    return unicodedata.normalize("NFC", text)


# Matches a "?" or "&" followed by a tracking-style key=value pair.
# Covers the most common tracking parameters without needing a full
# URL-parsing library for this simple case.
_TRACKING_PARAM_PATTERN = re.compile(
    r"[?&](utm_[a-zA-Z_]+|fbclid|gclid|ref|si)=[^&\s]*"
)


def normalize_urls(text: str) -> str:
    """
    Strip common tracking parameters from any URLs found in the text.
    Example: "example.com/article?utm_source=discord" -> "example.com/article"
    """
    cleaned = _TRACKING_PARAM_PATTERN.sub("", text)
    # If stripping left a stray "?" with nothing after it (all params were
    # tracking params), remove the now-empty "?" too.
    cleaned = re.sub(r"\?(?=\s|$)", "", cleaned)
    return cleaned


def clean_message_text(text: str) -> str:
    """
    The single entry point the importer will call: runs all normalization
    steps in order. Add new steps here as the pipeline grows.
    """
    if text is None:
        return text
    text = normalize_unicode(text)
    text = normalize_urls(text)
    return text