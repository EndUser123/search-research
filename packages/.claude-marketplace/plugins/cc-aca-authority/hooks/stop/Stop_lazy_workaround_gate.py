

# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""
Lazy Workaround Detection Gate

Blocks LLM responses that suggest accepting bugs as features instead of fixing root causes.

Pattern: "Accept X as Y" where X is a problem and Y is a euphemism.
Example: "Accept duplicate task bars as 'visible logging'"

This is LAZY and UNACCEPTABLE. Fix the actual problem.
"""

import json
import os
import re
import string
import sys
from pathlib import Path

# Lazy workaround patterns to block
LAZY_PATTERNS = [
    # Accept-as-feature patterns (regex - specific phrase structure)
    (r"accept\s+.+?\s+as\s+(?:a\s+)?(?:visible\s+logging|feature|design|intentional|expected)", "accepting_bug_as_feature"),

    # "Live with it" patterns (regex - specific verb phrase)
    (r"live\s+with\s+((the|this)\s+)?(bug|issue|problem|limitation|behavior|race\s+condition)", "accepting_technical_debt"),

    # "Not worth fixing" - lazy prioritization (regex - specific phrase)
    (r"n[o']t\s+worth\s+(fixing|addressing|investigating)", "avoiding_necessary_work"),

    # "Workaround is fine" instead of fixing (regex - specific phrase)
    (r"workaround\s+(is\s+)?(fine|acceptable|sufficient|good)", "accepting_workaround_over_fix"),

    # ANTI-PATTERN-4: "Fix" that is actually a try/except wrapper (error suppression)
    (r"added?\s+(?:a\s+)?try\s*/\s*except\s+(?:to\s+)?suppress", "try_except_error_suppression"),
    (r"wrapped?\s+(?:it\s+)?in\s+try\s*/\s*except\s+(?:to\s+)?hide", "try_except_error_suppression"),
    (r"catch\s+the\s+exception\s+(?:and\s+)?(ignore|suppress|hide|pass)", "exception_suppression"),
    (r"except\s*\([^)]*\)\s*:\s*pass\s*(?:#|$)", "bare_except_pass"),

    # ANTI-PATTERN-4: "Fix" that reduces timeout to hide slowness
    (r"reduced?\s+(?:the\s+)?timeout\s+(?:to|from)\s+\d+", "reducing_timeout"),
    (r"shortened?\s+timeout", "shortening_timeout"),

    # ANTI-PATTERN-4: "Fix" that adds skip/bypass logic
    (r"skip(?:ped)?\s+(?:the\s+)?(?:check|validation|verification)\s+(?:to\s+)?(?:fix|handle)", "skipping_validation"),
    (r"bypass(?:ed)?\s+(?:the\s+)?(?:check|validation)", "bypassing_checks"),
]

from __lib.stop_gate_telemetry import log_gate_event

# Non-regex duplicate detection: proximity-based keyword matching
# Replaces the brittle (duplicates?|redundant|extra|double).*(is\s+)?(fine|acceptable|expected|normal|ok)
_PROBLEM_WORDS = frozenset({"duplicate", "duplicates", "redundant", "extra", "double"})
_ACCEPTANCE_WORDS = frozenset({"fine", "acceptable", "expected", "normal", "ok"})
_PROXIMITY_TOKENS = 8  # Must be within this many tokens of each other
# Rationale: 8 tokens provides enough context for 'X is fine/acceptable' detection
# while avoiding false positives from distant acceptance words in long responses.

# Module-level punctuation table (cached, created once)
_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation.replace("'", ""))

def _check_duplicate_acceptance_proximity(text: str) -> tuple[bool, list[str]]:
    """
    Check for 'X is fine/acceptable/expected' patterns using proximity-based matching.
    Returns (matched, matched_words) where matched_words contains the problem and acceptance words found.
    Only triggers when problem word and acceptance word are within PROXIMITY_TOKENS of each other.
    """
    tokens = [t.translate(_PUNCTUATION_TABLE).lower() for t in text.split()]

    for i, token in enumerate(tokens):
        if token in _PROBLEM_WORDS:
            end = min(i + _PROXIMITY_TOKENS + 1, len(tokens))
            window = tokens[i+1:end]
            for w in window:
                if w in _ACCEPTANCE_WORDS:
                    return True, [token, w]

            start = max(0, i - _PROXIMITY_TOKENS)
            window = tokens[start:i]
            for w in window:
                if w in _ACCEPTANCE_WORDS:
                    return True, [w, token]

    return False, []

# Dismissal detection: whole-token proximity matching (S-2).
# Replaces the unbounded `(cosmetic|minor|trivial).*(bug|issue|problem|error)` regex,
# which matched the "trivial" SUBSTRING inside identifiers like `_is_trivial_run`.
# Whole-token set membership fixes it: punctuation stripping merges the identifier
# into one token (`istrivialrun`), never equal to a bare adjective — so proximity
# never fires on a symbol that merely contains the adjective as a substring.
_DISMISSAL_ADJECTIVES = frozenset({"cosmetic", "cosmetics", "minor", "trivial"})
_DEFECT_WORDS = frozenset({"bug", "bugs", "issue", "issues", "problem", "problems", "error", "errors"})

def _check_dismissal_proximity(text: str) -> tuple[bool, list[str]]:
    """
    Detect 'cosmetic/minor/trivial <defect>' dismissal via whole-token proximity.
    Mirrors _check_duplicate_acceptance_proximity: adjective and defect-word tokens
    must co-occur within _PROXIMITY_TOKENS. Returns (matched, [adjective, defect]).
    """
    tokens = [t.translate(_PUNCTUATION_TABLE).lower() for t in text.split()]

    for i, token in enumerate(tokens):
        if token in _DISMISSAL_ADJECTIVES:
            end = min(i + _PROXIMITY_TOKENS + 1, len(tokens))
            window = tokens[i+1:end]
            for w in window:
                if w in _DEFECT_WORDS:
                    return True, [token, w]

            start = max(0, i - _PROXIMITY_TOKENS)
            window = tokens[start:i]
            for w in window:
                if w in _DEFECT_WORDS:
                    return True, [w, token]

    return False, []

# Strip-boundary patterns for _strip_quoted_blocks. This is the ORIGINAL dismissal
# regex retained ONLY for end-of-block detection (P1-4): removing the entry from
# LAZY_PATTERNS would otherwise change which quoted lines terminate a Stop-feedback
# block. Detection uses whole-token proximity above; stripping still needs the regex
# set to stay byte-identical.
_DISMISSAL_STRIP_PATTERN = r"(cosmetic|minor|trivial).*(bug|issue|problem|error)"
_STRIP_BOUNDARY_PATTERNS = [pat for pat, _ in LAZY_PATTERNS] + [_DISMISSAL_STRIP_PATTERN]

# Root cause phrases that signal proper investigation
ROOT_CAUSE_PHRASES = [
    # Full investigation phrases
    r"trace\s+(the\s+)?(source|cause|origin)",
    r"investigate\s+why",
    r"find\s+(the\s+)?(root\s+)?cause",
    r"identify\s+where",
    r"debug\s+(the\s+)?(issue|problem)",
    r"fix\s+(the\s+)?(underlying|root)",
    r"prevent\s+(the\s+)?duplication",
    # Investigation verbs (standalone - catches "we should investigate", "let me trace...")
    r"(?:should|will|need to|going to|planning to)\s+(?:trace|investigate|find root|debug|identify)",
    r"(?:let me|let us|i'll|i will)\s+(?:trace|investigate|find|debug|identify)",
    r"(?:tracing|investigating|finding|debugging|identifying)\s+(?:where|why|what|how)",
]

def _has_investigation_intent(text: str) -> bool:
    """Check if text contains a root-cause investigation phrase (bypass pattern)."""
    return any(re.search(phrase, text) for phrase in ROOT_CAUSE_PHRASES)

def _strip_quoted_blocks(text: str) -> str:
    """Remove quoted/attributed sections that are not the LLM's own words.

    Strips:
    - Markdown blockquotes (lines starting with '> ')
    - Stop-hook feedback blocks (after 'Stop hook' or 'Stop says:')
    - system-reminder blocks
    """
    lines = text.split("\n")
    result: list[str] = []
    skip = False

    for line in lines:
        stripped = line.strip()

        # Skip markdown blockquote lines
        if stripped.startswith("> "):
            continue

        # Skip system-reminder blocks (begin/end)
        if stripped.startswith("<system-reminder") or stripped == "</system-reminder>":
            skip = not stripped.endswith(">")
            if stripped.endswith(">") and stripped.startswith("<system-reminder"):
                continue
            continue
        if skip:
            continue

        # Skip Stop-hook feedback artifacts and their continuation lines
        if re.match(
            r"(?:Stop (?:hook|says)|⎿|Stop\s+hook\s+feedback|LAZY WORKAROUND|EPISTEMIC FORMAT REPAIR|Pattern matched:|Required approach:|Remember:|This suggests)",
            stripped,
        ):
            skip = True
            continue
        # Skip continuation of Stop feedback blocks (indented text or short advisory lines)
        if skip and (not stripped or stripped.startswith(("⚠", "1.", "2.", "3.", "4.", "✓", "✗", "Do NOT"))):
            continue
        if skip:
            # After stop-block marker lines, the next line often contains the literal
            # regex pattern text (e.g. "accept\s+.+?\s+as\s+(?:a\s+)?...").
            # Strip it — it's gate output being quoted, not a new proposal.
            if any(re.search(pat, stripped, re.IGNORECASE) for pat in _STRIP_BOUNDARY_PATTERNS):
                skip = False  # End of this stop block
                continue
            skip = False  # End of stop block — keep this line

        result.append(line)

    return "\n".join(result)

def check_lazy_workarounds(response: str) -> dict:
    """
    Check if response contains lazy workaround suggestions.

    Args:
        response: The assistant's response text

    Returns:
        dict with 'decision' ('allow' or 'block') and optional 'reason'
    """
    # Preprocess: strip quoted blocks and Stop-hook artifacts
    clean = _strip_quoted_blocks(response)
    clean_lower = clean.lower()

    # Check for lazy patterns
    for pattern, label in LAZY_PATTERNS:
        if re.search(pattern, clean_lower, re.IGNORECASE):
            # Check if this is actually explaining the problem (not suggesting it)
            # Allow if it's followed by root cause investigation
            if _has_investigation_intent(clean_lower):
                continue  # This is proper investigation, not lazy acceptance

            # Report/implementation context: allow phrases describing intended system behavior.
            # Excludes any pattern containing "bug", "acceptable", or "intentional as" to avoid
            # overlapping with the bug-as-feature lazy patterns.
            _REPORT_ALLOW_PATTERNS = [
                r"\btwo\b.*\bsignals?\b.*\bsuppress",
                r"\bthe\s+advisory\b.*\bsuppress",
                r"\bsuppression\s+is\b.*\bcorrect\b",
                r"\bthe\s+edge\s+case\b.*\bto\s+monitor\b",
            ]
            if any(re.search(p, clean_lower) for p in _REPORT_ALLOW_PATTERNS):
                continue  # Describing intended behavior, not accepting a bug

            log_gate_event(
                gate_name="lazy_workaround_gate",
                classification="lazy",
                profile=os.environ.get("CLAUDE_PROFILE", "default"),
                decision="block",
                session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
                terminal_id=os.environ.get("CLAUDE_TERMINAL_ID", ""),
                extra={
                    "matched_pattern": pattern,
                    "investigation_bypass": _has_investigation_intent(clean_lower),
                    "response_snippet": response[-200:] if response else "",
                },
            )
            return {
                "decision": "block",
                "reason": f"LAZY WORKAROUND DETECTED: {label.replace('_', ' ')}\n\n"
                          f"⚠️  This suggests accepting a problem instead of fixing the root cause.\n\n"
                          f"Required approach:\n"
                          f"1. TRACE: Find where the problem originates\n"
                          f"2. IDENTIFY: What's causing it\n"
                          f"3. FIX: Address the actual root cause\n"
                          f"4. VERIFY: Confirm the fix works\n\n"
                          f"Pattern matched: {pattern}\n\n"
                          f"Remember: 'Accepting bugs as features' creates technical debt.\n"
                          f"Fix the problem, don't document the workaround."
            }

    # Dismissal detection: whole-token proximity (S-2). Replaces the unbounded regex.
    matched, words = _check_dismissal_proximity(clean_lower)
    if matched:
        if _has_investigation_intent(clean_lower):
            return {"decision": "allow"}  # Proper investigation, not lazy dismissal

        log_gate_event(
            gate_name="lazy_workaround_gate",
            classification="lazy",
            profile=os.environ.get("CLAUDE_PROFILE", "default"),
            decision="block",
            session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
            terminal_id=os.environ.get("CLAUDE_TERMINAL_ID", ""),
            extra={
                "matched_pattern": f"dismissal_proximity:{words[0]!r}+{words[1]!r}",
                "investigation_bypass": False,
                "response_snippet": response[-200:] if response else "",
            },
        )
        return {
            "decision": "block",
            "reason": f"LAZY WORKAROUND DETECTED: dismissing functional bug\n\n"
                      f"⚠️  This suggests accepting a problem instead of fixing the root cause.\n\n"
                      f"Matched: {words[0]!r} near {words[1]!r}\n\n"
                      f"Required approach:\n"
                      f"1. TRACE: Find where the problem originates\n"
                      f"2. IDENTIFY: What's causing it\n"
                      f"3. FIX: Address the actual root cause\n"
                      f"4. VERIFY: Confirm the fix works\n\n"
                      f"Detection method: whole-token proximity matching\n\n"
                      f"Remember: 'Accepting bugs as features' creates technical debt.\n"
                      f"Fix the problem, don't document the workaround."
        }

    # Non-regex duplicate detection: check proximity-based matching
    matched, words = _check_duplicate_acceptance_proximity(clean_lower)
    if matched:
        if _has_investigation_intent(clean_lower):
            return {"decision": "allow"}  # Proper investigation, not lazy acceptance

        log_gate_event(
            gate_name="lazy_workaround_gate",
            classification="lazy",
            profile=os.environ.get("CLAUDE_PROFILE", "default"),
            decision="block",
            session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
            terminal_id=os.environ.get("CLAUDE_TERMINAL_ID", ""),
            extra={
                "matched_pattern": f"proximity:{words[0]!r}+{words[1]!r}",
                "investigation_bypass": False,
                "response_snippet": response[-200:] if response else "",
            },
        )
        return {
            "decision": "block",
            "reason": f"LAZY WORKAROUND DETECTED: ignoring duplication\n\n"
                      f"⚠️  This suggests accepting a problem instead of fixing the root cause.\n\n"
                      f"Matched: {words[0]!r} near {words[1]!r}\n\n"
                      f"Required approach:\n"
                      f"1. TRACE: Find where the problem originates\n"
                      f"2. IDENTIFY: What's causing it\n"
                      f"3. FIX: Address the actual root cause\n"
                      f"4. VERIFY: Confirm the fix works\n\n"
                      f"Detection method: proximity-based keyword matching\n\n"
                      f"Remember: 'Accepting bugs as features' creates technical debt.\n"
                      f"Fix the problem, don't document the workaround."
        }

    return {"decision": "allow"}

def main():
    """Main entry point for command-line testing"""
    if len(sys.argv) > 1:
        # Test mode: check a string
        test_response = " ".join(sys.argv[1:])
        result = check_lazy_workarounds(test_response)
        print(json.dumps(result, indent=2))
    else:
        # stdin mode
        response = sys.stdin.read()
        result = check_lazy_workarounds(response)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()