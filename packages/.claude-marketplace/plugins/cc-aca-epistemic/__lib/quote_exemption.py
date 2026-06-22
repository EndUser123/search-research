"""Position-based quote exemption for prose pattern matching.

Detects whether a regex match in text falls inside quoted content (fenced code
blocks, blockquotes, inline backticks, or prose double-quotes). Used by Stop gates
that match prose patterns to filter out use/mention false positives: when the model
discusses a trigger phrase (e.g., "deletes files") inside quotes, it's not asserting
the trigger -- just discussing it.

Pattern types exempt:
- Fenced code blocks (triple backtick markers)
- Blockquotes (> ...)
- Inline backticks (single backtick wrapped)
- Prose double-quotes (ASCII or Unicode variants)
"""
import re
from typing import Iterator, Match, Pattern

# Balanced single-line double-quote spans: ASCII "..." or curly U+201C...U+201D.
# Matched LOCALLY (not via global open/close parity) so one stray/unbalanced quote
# cannot mis-bracket the rest of the document. Bounded to a single line ([^...\n]):
# multi-line prose quotes are rare; long quotes use blockquotes/fences (handled).
_QUOTED_SPAN_RE = re.compile('"[^"\n]*"|“[^”\n]*”')


def is_inside_quoted_content(text: str, match: Match) -> bool:
    """Check if a regex match falls inside quoted content."""
    pos = match.start()

    # Fenced blocks
    in_fence = False
    for fence_m in re.finditer(r"^```", text, re.MULTILINE):
        if pos < fence_m.start():
            return in_fence
        if in_fence:
            in_fence = False
        else:
            in_fence = True
    if in_fence:
        return True

    # Blockquotes: ^> ...
    for line_m in re.finditer(r"^> .+$", text, re.MULTILINE):
        if line_m.start() <= pos < line_m.end():
            return True

    # Inline backticks: `...`
    for bt_m in re.finditer(r"`[^`]*`", text):
        if bt_m.start() <= pos < bt_m.end():
            return True

    # Prose double-quotes: match BALANCED single-line spans LOCALLY, instead of the
    # old global open/close parity. The parity scan paired quotes across the whole
    # text, so a single stray/unbalanced quote earlier in the response flipped parity
    # and exposed every later quoted span as "unquoted" (false positive). A span that
    # forms no balanced pair is simply ignored and cannot corrupt the rest of the text.
    for q_m in _QUOTED_SPAN_RE.finditer(text):
        if q_m.start() <= pos < q_m.end():
            return True

    return False


def search_unquoted(pattern: Pattern, text: str) -> Match | None:
    """Find first unquoted match of a regex pattern."""
    for m in pattern.finditer(text):
        if not is_inside_quoted_content(text, m):
            return m
    return None


def finditer_unquoted(pattern: Pattern, text: str) -> Iterator[Match]:
    """Find all unquoted matches of a regex pattern."""
    for m in pattern.finditer(text):
        if not is_inside_quoted_content(text, m):
            yield m


def has_unquoted_match(pattern: Pattern, text: str) -> bool:
    """Check if pattern has at least one unquoted match."""
    return search_unquoted(pattern, text) is not None
