"""
Regression tests for Stop_deletion_verification_guard FP narrowing.

Phase 2 data-driven tuning (2026-06-01):
  Baseline: 8 blocks/7d, 72% FP rate (18/25 sampled).
  Two root causes fixed:
    1. Stopword filter: verb+preposition/conjunction claims no longer trigger
       ("removed from", "deleted in", "dropped when", "removed —", etc.)
    2. Root-path filter: drive-root paths ("P:\\", "C:/") excluded from
       path-extraction so they can't cause false "file still exists" blocks.
"""
from __future__ import annotations

import re
import pytest


# ── Inline copies of the patterns for unit-testing without bootstrap ──────────

DELETION_CLAIM_PATTERNS = re.compile(
    r"\b(?:files?|directories?|folders?|paths?)\s+(?:are|were|have been)\s+(?:deleted|removed|cleaned\s+up|gone)\b"
    r"|\b(?:successfully\s+)?(?:deleted|removed|cleaned\s+up)\s+\S+"
    r"|\b(?:all|both)\s+(?:files?|directories?|folders?)\s+(?:deleted|removed)\b"
    r"|\bdropped?\s+\S+",
    re.IGNORECASE,
)

_DELETION_VERB_STOPWORDS = re.compile(
    r"(?:deleted|removed|cleaned\s+up|dropped?)\s+"
    r"(?:from|in|of|to|at|by|for|via|into|onto|"
    r"when|since|because|if|while|as|after|before|too|also|[—–(])",
    re.IGNORECASE,
)


def _is_root_path(p: str) -> bool:
    return len(p) <= 3 and ":" in p


def _claims_after_filter(text: str) -> list[str]:
    """Return matched claim texts that survive the stopword filter."""
    results = []
    for m in DELETION_CLAIM_PATTERNS.finditer(text):
        matched = m.group(0)
        if not _DELETION_VERB_STOPWORDS.search(matched):
            results.append(matched)
    return results


# ── Stopword FP cases (all must be filtered out) ─────────────────────────────

@pytest.mark.parametrize("text,label", [
    ("The changes were summarised — removed — here’s what changed", "em-dash after removed"),
    ("The config was deleted in the process of migration", "deleted in"),
    ("Removed from the plugin registry", "removed from"),
    ("The module was removed too", "removed too"),
    ("dropped (since we migrated to the new system)", "dropped (since"),
    ("dropped when condition was false", "dropped when"),
    ("removed (source: fact-guard plugin)", "removed (source:"),
    ("deleted from tracking system", "deleted from"),
    ("removed – see change log", "en-dash after removed"),
    ("Removed from config file", "removed from config"),
    ("deleted in favor of the new approach", "deleted in favor"),
    ("dropped since the interface changed", "dropped since"),
    ("removed by the cleanup script", "removed by"),
    ("deleted after ingestion", "deleted after"),
    ("removed via script automation", "removed via"),
])
def test_stopword_fp_filtered(text: str, label: str) -> None:
    claims = _claims_after_filter(text)
    assert claims == [], f"[{label}] expected no claims but got: {claims}"


# ── Genuine cases (must NOT be filtered) ─────────────────────────────────────

@pytest.mark.parametrize("text,label", [
    ("the old files were deleted", "passive-voice files deleted"),
    ("Deleted both files", "deleted both"),
    ("Successfully deleted foo.py", "deleted with extension"),
    ("removed config.db-wal", "removed named artifact"),
    ("files were deleted", "plain files were deleted"),
    ("removed old_module.py from the project", "removed named .py file"),
    ("Deleted the backup.tar.gz", "deleted backup archive"),
    ("cleaned up temp directory", "cleaned up dir"),
    ("all files deleted", "all files deleted"),
    ("both directories removed", "both dirs removed"),
    ("Dropped table old_sessions", "dropped db table"),
])
def test_genuine_cases_not_filtered(text: str, label: str) -> None:
    claims = _claims_after_filter(text)
    assert claims != [], f"[{label}] expected a claim to pass through but nothing detected"


# ── Root-path filter ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("path,expected_root", [
    ("P:", True),
    ("P:\\", True),
    ("P:/", True),
    ("C:", True),
    ("C:\\", True),
    ("C:/", True),
    ("P:\\packages\\foo.py", False),
    ("P:/packages/foo.py", False),
    ("config.db-wal", False),
    ("foo.py", False),
    ("relative/path.py", False),
    ("P:\\packages", False),
])
def test_root_path_filter(path: str, expected_root: bool) -> None:
    result = _is_root_path(path)
    assert result == expected_root, f"_is_root_path({path!r}) = {result}, expected {expected_root}"


# ── Regression: specific blocks from diagnostics DB ──────────────────────────

def test_regression_removed_emdash() -> None:
    """'removed —' em-dash continuations must not fire (was block 2026-05-31)."""
    text = "Phase 1 complete — removed — here’s the current state"
    assert _claims_after_filter(text) == []


def test_regression_dropped_since() -> None:
    """'dropped (since' parenthetical must not fire (was block 2026-05-27)."""
    text = "The old router was dropped (since we migrated to plugin-local dispatch)"
    assert _claims_after_filter(text) == []


def test_regression_deleted_in() -> None:
    """'deleted in' prepositional phrase must not fire (was block 2026-05-28)."""
    # Use "deleted in favor of" — not "files are deleted" (which triggers arm 1 legitimately)
    text = "The old bootstrap was deleted in favor of the new resolver"
    assert _claims_after_filter(text) == []


def test_regression_removed_from_config() -> None:
    """'Removed from' config reference must not fire (was block 2026-05-27)."""
    text = "Removed from the marketplace configuration (plugin-audit-and-fix.py still present)"
    assert _claims_after_filter(text) == []


def test_regression_dropped_when() -> None:
    """'dropped when' temporal clause must not fire (was block 2026-05-12)."""
    text = "The assumption was dropped when the interface changed in v2"
    assert _claims_after_filter(text) == []
