#!/usr/bin/env python3
"""
anti_lazy_policy - Canonical source for anti-lazy enforcement policy.

Shared by PreToolUse_user_delegation_gate.py (UserPromptSubmit/PreToolUse phase)
and anti_sycophancy/lazy_closure_detector.py (Stop phase).

Keeps both enforcement points in sync: identical noise lists, keyword extraction,
and ledger-checking logic. Previously each module had its own copy with divergent
noise lists (PreToolUse: 26 entries, lazy_closure: 27 entries, missing 'all',
'any', 'some', 'most', 'each', 'folder', 'directory').
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Dict, List, Set


# ── Noise word list ──────────────────────────────────────────────────────────
# Canonical frozenset — must be identical across both enforcement points.
# PreToolUse and lazy_closure_detector previously had divergent lists.
NOISE_WORDS: frozenset[str] = frozenset((
    # PreToolUse base (26): the, a, an, and, or, but, in, on, at, to, for,
    # of, with, by, from, as, is, are, was, were, be, been, being, have,
    # has, had, do, does, did, will, would, should, could, may, might, must,
    # can, this, that, these, those, i, you, he, she, it, we, they, what,
    # which, who, when, where, why, how, all, each, every, both, few, more,
    # most, other, some, such, no, nor, not, only, own, same, so, than, too,
    # very
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "must", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    # lazy_closure additions (from diff)
    "all", "any", "some", "most", "each",
    # PreToolUse extras
    "folder", "directory",
    # More noise from PreToolUse
    "src", "lib", "test", "tests", "spec", "specs", "tmp", "temp",
    "py", "js", "ts", "md", "json", "yaml", "yml", "txt",
    "log", "cfg", "ini", "toml",
    "where", "can", "could", "should", "would", "will", "are",
    "is", "was", "does", "did", "has", "had", "have",
    "show", "me", "tell", "know", "help", "please",
    "can", "you", "your", "it", "they", "them",
))


def extract_topic_keywords(prompt: str) -> Set[str]:
    """Extract scorable topic keywords from a user prompt.

    Splits on path separators, underscores, dots, hyphens, and whitespace.
    Filters noise words and short tokens.

    Both PreToolUse and lazy_closure_detector use this function.

    Args:
        prompt: Raw user prompt string.

    Returns:
        Set of significant topic keywords (lowercased, 3+ chars, alphanumeric,
        noise-filtered).
    """
    if not prompt:
        return set()

    prompt_lower = prompt.lower()
    parts = re.split(r"[/\\._\-\s]+", prompt_lower)
    keywords = {
        p for p in parts
        if len(p) >= 3 and p.isalnum() and p not in NOISE_WORDS
    }
    return keywords


def load_investigation_ledger() -> Dict[str, List]:
    """Load the investigation ledger.

    Uses importlib.util to load the ledger module from the Claude root,
    compatible with both PreToolUse subprocess context and Stop in-process
    context.

    Returns:
        Dict with keys: files_read, searches, executions, topics.
        Returns empty dict on any error (fail-open).
    """
    try:
        hooks_dir = Path(__file__).resolve().parent.parent  # P:/.claude/hooks
        ledger_path = hooks_dir / "investigation-ledger" / "ledger.py"

        if not ledger_path.exists():
            return {}

        spec = importlib.util.spec_from_file_location("_ledger", ledger_path)
        ledger_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ledger_mod)
        return ledger_mod._load_ledger()
    except Exception:
        return {}


def check_topic_relevant_investigation(prompt: str) -> bool:
    """Determine if relevant investigation has occurred for the prompt's topics.

    Checks whether the investigation ledger contains files_read or searches
    matching the topic keywords extracted from the prompt. Both PreToolUse
    and lazy_closure_detector use this function.

    Returns True (allow) when:
      - Ledger has relevant files_read or searches matching topic keywords
      - No topic keywords can be extracted (nothing to scope against)
      - Ledger is empty or error occurs (fail-open)

    Returns False (block) only when:
      - Topic keywords exist AND
      - Ledger has no files_read or searches containing those keywords
      - Ledger has no executions

    Args:
        prompt: Raw user prompt string.

    Returns:
        True if investigation is sufficient or no scoping possible (allow).
        False if no relevant investigation found (block).
    """
    try:
        ledger = load_investigation_ledger()
        files_read = ledger.get("files_read", [])
        searches = ledger.get("searches", [])
        executions = ledger.get("executions", [])

        if not files_read and not searches and not executions:
            return False  # No investigation at all

        keywords = extract_topic_keywords(prompt)
        if not keywords:
            return True  # No scorable topic — allow (nothing to scope against)

        # Check if any files_read or searches contain topic keywords
        for fp in files_read:
            fp_lower = fp.lower()
            if any(kw in fp_lower for kw in keywords):
                return True
        for sq in searches:
            sq_lower = sq.lower()
            if any(kw in sq_lower for kw in keywords):
                return True

        return False  # No relevant investigation found
    except Exception:
        return True  # Fail open


def check_investigation_in_ledger() -> bool:
    """Return True if the investigation ledger shows any prior investigation.

    Checks files_read, searches, and executions for non-empty lists.
    Fails open (returns True) on ledger errors to avoid false positives.

    Used as fallback when no user_prompt is available (e.g., detect_all_lazy_closure
    called without topic context). Prefer check_topic_relevant_investigation() when
    a prompt is available, as it scopes against topic keywords.

    Returns:
        True if any investigative activity exists (allow).
        False if ledger is empty (block).
    """
    try:
        ledger = load_investigation_ledger()
        files_read = ledger.get("files_read", [])
        searches = ledger.get("searches", [])
        executions = ledger.get("executions", [])
        return bool(files_read or searches or executions)
    except Exception:
        return True  # Fail open


# ── Diagnostic keywords (PreToolUse only — not shared) ──────────────────────
# These are used by PreToolUse_user_delegation_gate to detect diagnostic topics
# BEFORE checking the ledger. lazy_closure_detector doesn't need this filter
# because user_delegation patterns are checked on every response regardless.
DIAGNOSTIC_KEYWORDS: frozenset[str] = frozenset((
    "debug", "investigate", "investigation", "diagnose", "diagnostic",
    "error", "issue", "problem", "bug", "fix", "broken", "failing",
    "hook", "gate", "block", "unexpected", "incorrect",
    "root", "cause", "trace", "rca", "root-cause",
    "behavior", "symptom", "failure", "crash",
))


def is_diagnostic_topic(prompt: str) -> bool:
    """Return True if prompt mentions diagnostic/investigative topics.

    Used by PreToolUse_user_delegation_gate to decide whether to apply
    the AskUserQuestion blocking logic. lazy_closure_detector does not
    use this function — user_delegation patterns fire on all responses.

    Args:
        prompt: Raw user prompt string.

    Returns:
        True if any diagnostic keyword appears in prompt.
    """
    if not prompt:
        return False
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in DIAGNOSTIC_KEYWORDS)
