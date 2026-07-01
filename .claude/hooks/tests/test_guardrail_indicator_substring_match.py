#!/usr/bin/env python3
"""Guardrail: prevent reintroduction of the #882 indicator-substring bug.

The #882 root cause was hooks doing bare-substring matching of error-indicator
words ("error", "failed", ...) against tool OUTPUT TEXT:

    any(err in output.lower() for err in ["error", "failed", ...])

That fires on any path/identifier containing the letters (error_attribution_hook.py,
non_failed_state, 0 failed). The fix is whole-token matching via the shared
posttooluse.falsification_assessor.FalsificationAssessor._indicator_match helper
(lookaround (?<!\\w)...(?!\\w), which also handles non-word-edge patterns like '[]').

This guardrail is deliberately NARROW to stay low-false-positive:
  - It targets the comprehension-over-indicator-list signature only:
        any(<needle> in <text>(.lower())? for <needle> in (<indicator literals>))
    That shape is never a dict-key membership check, so it does not flag the
    safe `"error" in tool_result` dict-key idiom.
  - It does NOT flag the `for sig in (...): if sig in output` loop form, masked
    classifier substrings (system2_hook), or passive-metric recorders
    (failure_recorder). Those are lower-severity / not model-visible noise and
    are reviewed separately. Listing them here documents the accepted residual.

Baseline today: one hit — posttooluse/change_verification.py (DEAD CODE, not in
create_registry()). Allowlisted with a reason. Any NEW occurrence in a live
module fails this test; the author must either use the shared matcher or extend
the allowlist with a justification.
"""
from __future__ import annotations

import re
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent

# Modules whose PostToolUse output-text matching can reach the model.
SCAN_DIRS = [
    HOOKS_DIR / "posttooluse",
]
SCAN_FILES = [
    HOOKS_DIR / "PostToolUse.py",
]

INDICATOR_WORDS = ("error", "failed", "exception", "traceback", "errno", "empty")
INDICATOR_LITERAL = re.compile(rf"""["']({"|".join(INDICATOR_WORDS)})["']""")
# The #882 signature: any( ... in ... for ... in ... ) with a .lower() call.
COMPREHENSION_MATCH = re.compile(r"any\s*\(.*\bin\b.*\bfor\b.*\bin\b")

# Allowlist: (file_stem, line_substring, reason). Dead/masked/accepted only.
ALLOWLIST = [
    (
        "change_verification.py",
        "err in tool_response_str.lower()",
        "DEAD CODE — not registered in create_registry() (see __init__.py:108). "
        "Flagged so a future re-registration triggers review.",
    ),
]


def _scan_files() -> list[Path]:
    files = list(SCAN_FILES)
    for d in SCAN_DIRS:
        files.extend(p for p in d.glob("*.py"))
    return [f for f in files if f.exists()]


def _find_violations() -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for f in _scan_files():
        for i, raw in enumerate(
            f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if not COMPREHENSION_MATCH.search(line):
                continue
            if not INDICATOR_LITERAL.search(line):
                continue
            if ".lower(" not in line:
                continue
            violations.append((f.name, i, line))
    return violations


def _is_allowlisted(name: str, line: str) -> bool:
    return any(name == a_name and a_sub in line for a_name, a_sub, _ in ALLOWLIST)


def test_no_new_indicator_substring_comprehension_in_live_hooks():
    """Fail on any NEW comprehension-over-indicator-list substring match. The
    only accepted instance today is dead code (change_verification.py)."""
    violations = _find_violations()
    new = [(n, i, ln) for (n, i, ln) in violations if not _is_allowlisted(n, ln)]
    assert not new, (
        "New #882-shape indicator substring match found (bare-substring over a "
        "list of error words on lowercased output). Use the shared whole-token "
        "matcher FalsificationAssessor._indicator_match instead, or extend the "
        "allowlist with a justification. Violations:\n  "
        + "\n  ".join(f"{n}:{i}: {ln}" for (n, i, ln) in new)
    )


def test_allowlist_entries_still_exist():
    """If an allowlisted line is removed/changed, the allowlist is stale —
    surface it so the entry is pruned rather than silently rotting."""
    by_name = {f.name: f for f in _scan_files()}
    for name, sub, _reason in ALLOWLIST:
        f = by_name.get(name)
        assert f is not None, f"allowlist entry {name}: file no longer scanned"
        text = f.read_text(encoding="utf-8", errors="ignore")
        assert sub in text, (
            f"allowlist entry {name!r} ({sub!r}) not found in file — prune it"
        )
