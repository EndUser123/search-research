"""
destructive_cleanup_detector.py

Flags responses that recommend destructive cleanup (broken symlink deletion, hook
registration removal, config entry deletion) without showing evidence of repair analysis
(target search, rename/move diagnosis, replacement identification, obsolescence verification).

Advisory only (severity=warn). Does not block.

Guard name: destructive_cleanup_without_repair_analysis
"""

from __future__ import annotations

import re
from typing import NamedTuple


class CleanupMatch(NamedTuple):
    matched: str
    pattern_type: str
    suggestion: str
    severity: str = "warn"


# Destructive cleanup action patterns — phrases that recommend deletion/removal
# of symlinks, registrations, or config entries
CLEANUP_PATTERNS = [
    # Broken symlink cleanup
    re.compile(r"\bdelete[d]?\s+the\s+broken\s+symlink\b", re.I),
    re.compile(r"\bremove?\s+the\s+broken\s+symlink\b", re.I),
    re.compile(r"\bdelete[d]?\s+a\s+broken\s+symlink\b", re.I),
    re.compile(r"\bremove\s+orphaned\s+symlink\b", re.I),
    # Dead/broken symlink removal (no repair context)
    re.compile(r"\b(?:dead|broken)\s+symlink\b.*(?:delete|remove|rm)", re.I),
    re.compile(r"(?:delete|remove|rm).*(?:dead|broken)\s+symlink\b", re.I),
    # Hook registration/config removal
    re.compile(r"\bremove\s+the\s+hook\s+registr(?:y|ation)\b", re.I),
    re.compile(r"\bremove\s+(?:the\s+)?(?:hook\s+)?entry\s+from\s+settings", re.I),
    re.compile(r"\bdelete\s+(?:the\s+)?hook\s+registr(?:y|ation)\b", re.I),
    re.compile(r"\bremove\s+(?:the\s+)?(?:hook\s+)?config\b", re.I),
    re.compile(r"\bdelete\s+(?:the\s+)?(?:hook\s+)?config\b", re.I),
    re.compile(r"\bremove\s+(?:the\s+)?stale\s+hook\b", re.I),
    re.compile(r"\bdelete\s+(?:the\s+)?stale\s+hook\b", re.I),
    re.compile(r"\bremove\s+the\s+dead\s+(?:hook|file|module)\b", re.I),
    re.compile(r"\bdelete\s+the\s+dead\s+(?:hook|file|module)\b", re.I),
    # Missing-file registration cleanup
    re.compile(r"\bremove\s+(?:the\s+)?missing[-\s]file\s+registr(?:y|ation)\b", re.I),
    re.compile(r"\bdrop\s+(?:the\s+)?(?:orphan(?:ed)?|missing)\s+(?:hook|file|module)\b", re.I),
    # Settings/entry cleanup combos
    re.compile(r"\b(?:delete|remove)\s+(?:the\s+)?settings.*entry\b", re.I),
    re.compile(r"\bremove\s+it\s+from\s+(?:settings|config|registration)\b", re.I),
]

# Repair analysis signals — presence of these in the same response exempts cleanup actions
REPAIR_SIGNALS = [
    # Search/diagnostic actions
    re.compile(r"\bsearch(?:ed|ing)?\s+(?:for|the\s+)?(?:target|replacement|moved|renamed)\b", re.I),
    re.compile(r"\blooked\s+(?:for|in|at)\b.*(?:target|replacement|rename|move)", re.I),
    re.compile(r"\binspect(?:ed)?\s+(?:the\s+)?symlink\b", re.I),
    re.compile(r"\bchecked\s+(?:the\s+)?target\b", re.I),
    # Verification actions
    re.compile(r"\bverif(?:ied|y)\s+(?:that\s+)?(?:the\s+)?hook\s+is\s+obsolete\b", re.I),
    re.compile(r"\bverif(?:ied|y)\s+(?:that\s+)?(?:the\s+)?(?:registration|entry)\s+is\s+stale\b", re.I),
    re.compile(r"\bverif(?:ied|y)\s+(?:that\s+)?no\s+(?:other|remaining)\s+(?:reference|use|consumer)\b", re.I),
    re.compile(r"\bconfirmed\s+(?:the\s+)?(?:replacement|target|successor)\b", re.I),
    re.compile(r"\bconfirmed\s+(?:that\s+)?(?:it\s+)?(?:was\s+)?(?:moved|renamed|replaced)\b", re.I),
    # Repair actions (not just cleanup)
    re.compile(r"\bupdated\s+(?:the\s+)?(?:symlink|registration|config|entry)\s+(?:to|with)\s+(?:point\s+to|correct)\b", re.I),
    re.compile(r"\brepoint(?:ed)?\s+(?:the\s+)?symlink\b", re.I),
    re.compile(r"\bpoint(?:ed)?\s+the\s+(?:symlink|hook|config)\s+to\b", re.I),
    re.compile(r"\brestore[sd]?\b.*(?:target|replacement)\b", re.I),
    re.compile(r"\b(renamed|moved)\s+(?:the\s+)?(?:target|source)\s+(?:to|into)\b", re.I),
    # Explicit obsolescence
    re.compile(r"\bobsolete\b.*(?:hook|registration|entry|symlink)\b", re.I),
    re.compile(r"\b(?:hook|registration|entry)\s+is\s+(?:no\s+longer\s+)?(?:used|needed|active|referenced)\b", re.I),
    re.compile(r"\bno\s+longer\s+(?:needed|used|referenced)\b", re.I),
    # Found replacement
    re.compile(r"\bfound\s+(?:the\s+)?(?:replacement|renamed|moved)\s+(?:target|file|hook|module)\b", re.I),
    re.compile(r"\bthe\s+(?:hook|target|module)\s+(?:was\s+)?renamed\s+to\b", re.I),
    re.compile(r"\b(?:renamed|moved)\s+(?:to|as)\s+\w+\s+—\s+updated\s+(?:symlink|registration|config)\b", re.I),
]


def detect_destructive_cleanup(response: str) -> list[CleanupMatch]:
    """Return list of destructive cleanup matches that lack repair analysis signals.

    Each match has severity="warn" (advisory only, does not block).
    """
    if not response:
        return []

    matches: list[CleanupMatch] = []
    text = response

    for pattern in CLEANUP_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        matched = m.group(0)

        # Check if ANY repair signal is present in the response
        has_repair = any(signal.search(text) for signal in REPAIR_SIGNALS)

        if not has_repair:
            matches.append(CleanupMatch(
                matched=matched,
                pattern_type="destructive_cleanup_without_repair_analysis",
                suggestion=(
                    "Destructive cleanup recommended without showing repair analysis. "
                    "Include evidence of: target search, rename/move diagnosis, "
                    "replacement identification, or explicit obsolescence verification."
                ),
                severity="warn",
            ))

    return matches


def detect_all_destructive_cleanup(response: str) -> list[CleanupMatch]:
    """Alias for detect_destructive_cleanup (matches anti_sycophancy pattern)."""
    return detect_destructive_cleanup(response)
