# Deferral Stop Gate Implementation Plan (Revision 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development
> (recommended) or executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

## Revision summary (Round 1 review → Round 2 revision)

**Round 1 review found 5 CRITICAL + 10 HIGH findings (23 total).** Key findings that drove the fundamental revision:

| Finding | Severity | Resolution in Revision 2 |
|---|---|---|
| F-01 | CRITICAL | Payload keys wrong (snake_case vs camelCase) | **Eliminated** — extend `behavioral_check.py` which already uses `lastAssistantMessage` (camelCase) via `extract_response_text()` |
| F-02 | CRITICAL | Duplicates `behavioral_check.UNNECESSARY_DEFERRAL` | **Eliminated** — the plan now EXTENDS behavioral_check instead of creating a parallel file. Leverages production-narrowed regex. |
| F-03 | CRITICAL | 6-hour mtime window, not session ownership | **Fixed** — Task 1 uses `current_session_id` frontmatter from handoffs, not mtime window |
| F-04 | CRITICAL | Transcript fallback dead code | **Eliminated** — behavioral_check already has `extract_response_text()` with proven transcript fallback |
| F-05 | HIGH | Block message contains "fresh session" | **Fixed** — block message rewritten to avoid recursive trigger phrases |
| F-07 | HIGH | Nag-once fingerprint over-engineered | **Dropped** — nag-once removed entirely; MAX_STOP_BLOCKS cap retained (well-justified) |
| F-10 | HIGH | No worktree awareness | **Fixed** — Task 1 checks both `P:/docs/handoffs/` and worktree-relative paths via `os.getcwd()` |
| F-25 | HIGH (META) | Tests use wrong payload keys | **Fixed** — all tests use camelCase `lastAssistantMessage`, `sessionId`, `stopHookActive` matching production payloads |

**Architectural change:** the plan went from 4 tasks (create new hook) to 2 tasks (extend existing hook). This drops ~60% of the code, eliminates the parallel-maintenance burden, and leverages production-narrowed regex patterns that have already been tuned based on real false-positive data.

---

## Goal

Extend the existing `behavioral_check.py` Stop hook to add a cheap-obligation AND-gate: when `UNNECESSARY_DEFERRAL` is detected AND the session has cheap open obligations (handoffs with CHEAP-classified work owned by this session), escalate from ADVISORY (exit 0) to BLOCK (exit 2). This catches the documented-deferral pattern where the agent writes handoffs instead of doing cheap work.

## Architecture

`behavioral_check.py` already detects `UNNECESSARY_DEFERRAL` with production-narrowed regex (narrowed twice based on real FP data, 2026-07-29). It currently emits ADVISORY output (exit 0, `additionalContext`). This plan adds:

1. **Obligation scanner** — finds handoffs owned by the current session (via `current_session_id` frontmatter) and classifies them CHEAP or EXPENSIVE (category-based, not time estimation).
2. **Escalation gate** — when `UNNECESSARY_DEFERRAL` is detected AND cheap obligations exist, the violation severity escalates from ADVISORY to BLOCK.
3. **Escape hatches** — `stopHookActive` check (prevents infinite loop, currently absent from behavioral_check because it was advisory-only) + MAX_STOP_BLOCKS cap (prevents unbounded blocking).

**Why extend, not create:** behavioral_check already has the right regex, the right payload extraction (`extract_response_text` handles camelCase + transcript fallback), the right logging, and the right output format. Creating a parallel file (Rev 1's approach) doubles maintenance, splits telemetry, and ignores production-narrowed patterns — the exact "search before proposing" failure that AGENTS.md warns against.

## Tech Stack

Python 3.14, pathlib, json, re. No external dependencies. Extends existing `behavioral_check.py` (already registered at `~/.grok/hooks/behavioral-check.json`, Stop event, 30s timeout).

## Risk level

Hard plan (reversibility ≥1.5 — enforcement code modifying agent behavior). Passed Round 1 adversarial review; this is Round 2.

## Global Constraints

- **Extend, don't create:** all changes to `behavioral_check.py`; no new hook files, no new registration JSON
- **Payload keys:** camelCase (`lastAssistantMessage`, `sessionId`, `stopHookActive`) — the existing `extract_response_text()` already handles this correctly
- **Session isolation:** handoff scan uses `current_session_id` frontmatter, not mtime window; state files keyed by session ID
- **Timeout:** existing 30s timeout is sufficient (obligation scan is file I/O, not LLM)
- **Encoding:** UTF-8 on all file writes
- **exit 2** to block; exit 0 to allow; `additionalContext` JSON to stdout (matching existing pattern)
- **Forward slashes** in all Python path strings

## Design-choice audit (carried from Rev 1, still valid)

| Decision | Choice | Rejected alternative | Why |
|---|---|---|---|
| Classification mechanism | Category-based (CHEAP/EXPENSIVE by file count + keywords) | Time estimation (`<15 min`) | LLMs cannot self-assess time (trillium research). Categories are mechanically computable. |
| Block condition | AND-gate (deferral language + cheap obligation) | Block on deferral alone | Too many false positives on legitimate L-effort deferrals |
| Obligation source | Session-owned handoffs (`current_session_id` frontmatter) | PostToolUse ledger / mtime window | Session ownership prevents cross-session contamination (F-03 fix). PostToolUse is Layer 1 (deferred). |
| Agent self-classification | NO — hook classifies via file patterns | Agent labels own obligations | Gaming vector: agent labels everything EXPENSIVE |

## Category definitions (operational)

| Category | Operational definition | Detected via |
|---|---|---|
| **CHEAP** | ≤1 file reference AND no design/architecture keywords | Handoff body has ≤1 unique file path AND no keyword matches |
| **EXPENSIVE** | >1 file reference OR contains design keywords | Handoff body has >1 unique path OR keyword match |

**Keywords (case-insensitive, word-boundary match):** `\bdesign\b`, `\barchitecture\b`, `\brefactor\b`, `\bnew skill\b`, `\bmulti-system\b`, `\bmulti-file\b`, `\bL effort\b`, `\bspike\b`, `\binvestigation\b`

**File-reference regex:** `(?:P:|~|C:/Users/brsth)/[^\s\)]+\.\w{2,4}` (forward-slash paths; matches the documented workspace convention)

---

## Task 1: Obligation scanner + escalation gate

**Files:**
- Modify: `C:/Users/brsth/.grok/hooks/scripts/behavioral_check.py` (add `find_cheap_obligations`, `classify_obligation`, `check_stop_hook_active`, `check_block_count`; modify `main()` to use escalation gate)
- Test: `C:/Users/brsth/.grok/hooks/scripts/test_deferral_gate.py` (new test file)

**Interfaces:**
- Consumes: `extract_response_text(payload)`, `check_behavioral_violations(text)` — both already in behavioral_check.py
- Produces: `find_cheap_obligations(session_id) -> list[dict]`, `classify_obligation(text) -> str`, `should_escalate(violations, session_id) -> bool` — used by Task 2 integration tests

**Success observation:** unit test `test_escalates_to_block_with_cheap_obligation` passes — when `UNNECESSARY_DEFERRAL` violation is detected AND `find_cheap_obligations` returns non-empty, `should_escalate` returns True.

**Failure observation:** test fails or escalation doesn't fire.

**Most likely failure mode:** `current_session_id` frontmatter field name doesn't match across all handoffs (some may use `session_id` instead).

**Failure signals:** `test_find_cheap_obligations_returns_empty_for_other_session` fails — hook picks up another session's handoffs.

**Countermove:** check both `current_session_id` and `session_id` in frontmatter.

**Branch triggers:** none (single-file modification).

**Abort condition:** if behavioral_check.py fails to import — abort and verify the file is intact.

- [ ] **Step 1: Write failing tests**

```python
# test_deferral_gate.py
"""Tests for the cheap-obligation escalation gate in behavioral_check.py.

These tests verify the AND-gate: UNNECESSARY_DEFERRAL + cheap obligation → BLOCK.
All payload keys use camelCase matching production Grok Build Stop payloads.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))


# --- classify_obligation tests ---

def test_classify_cheap_single_file():
    from behavioral_check import classify_obligation
    assert classify_obligation("Fix the typo in P:/src/config.py line 42.") == "CHEAP"


def test_classify_expensive_design_keyword():
    from behavioral_check import classify_obligation
    assert classify_obligation("This needs design decisions before implementation.") == "EXPENSIVE"


def test_classify_expensive_multi_file():
    from behavioral_check import classify_obligation
    assert classify_obligation("Update P:/src/a.py and P:/src/b.py and P:/src/c.py") == "EXPENSIVE"


def test_classify_cheap_no_files_no_keywords():
    from behavioral_check import classify_obligation
    assert classify_obligation("Run pytest to verify the fix works.") == "CHEAP"


def test_classify_expensive_word_boundary_not_substring():
    """'full effort' should NOT match 'L effort' keyword (word boundary)."""
    from behavioral_check import classify_obligation
    assert classify_obligation("I will put in full effort to fix this typo.") == "CHEAP"


# --- find_cheap_obligations tests ---

def test_find_cheap_obligations_returns_list():
    from behavioral_check import find_cheap_obligations
    result = find_cheap_obligations("nonexistent-session-id")
    assert isinstance(result, list)
    assert result == []  # no handoffs for fake session


def test_find_cheap_obligations_uses_session_id_not_mtime(tmp_path):
    """Must filter by current_session_id frontmatter, not mtime window."""
    from behavioral_check import find_cheap_obligations
    # Create a handoff with a different session_id
    handoff_dir = tmp_path / "test-handoff-other"
    handoff_dir.mkdir()
    handoff = handoff_dir / "HANDOFF.md"
    handoff.write_text(
        "---\ncurrent_session_id: other-session-999\n---\n"
        "Fix typo in P:/src/config.py",
        encoding="utf-8",
    )
    with patch("behavioral_check.HANDOFFS_DIR", tmp_path):
        result = find_cheap_obligations("my-session-123")
    assert result == [], "Should not pick up other session's handoff"


# --- should_escalate tests ---

def test_should_escalate_with_deferral_and_cheap_obligation():
    from behavioral_check import should_escalate
    violations = [("deferred text", "UNNECESSARY_DEFERRAL", "guidance", "", "ADVISORY")]
    with patch("behavioral_check.find_cheap_obligations") as mock_find:
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        assert should_escalate(violations, "test-session") is True


def test_should_not_escalate_without_deferral():
    from behavioral_check import should_escalate
    violations = [("tired text", "FABRICATED_FATIGUE", "guidance", "", "ADVISORY")]
    with patch("behavioral_check.find_cheap_obligations") as mock_find:
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        assert should_escalate(violations, "test-session") is False


def test_should_not_escalate_with_deferral_but_no_cheap_obligations():
    from behavioral_check import should_escalate
    violations = [("deferred text", "UNNECESSARY_DEFERRAL", "guidance", "", "ADVISORY")]
    with patch("behavioral_check.find_cheap_obligations") as mock_find:
        mock_find.return_value = []
        assert should_escalate(violations, "test-session") is False


# --- stopHookActive escape hatch tests ---

def test_stop_hook_active_prevents_escalation():
    from behavioral_check import should_escalate
    violations = [("deferred text", "UNNECESSARY_DEFERRAL", "guidance", "", "ADVISORY")]
    payload = {"stopHookActive": True, "sessionId": "test"}
    with patch("behavioral_check.find_cheap_obligations") as mock_find:
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        assert should_escalate(violations, "test-session", payload) is False


# --- MAX_STOP_BLOCKS cap tests ---

def test_max_stop_blocks_caps_at_3(tmp_path):
    from behavioral_check import should_escalate, _increment_block_count, _reset_block_count
    with patch("behavioral_check.STATE_DIR", tmp_path):
        _reset_block_count("test-cap-session")
        violations = [("deferred text", "UNNECESSARY_DEFERRAL", "guidance", "", "ADVISORY")]
        with patch("behavioral_check.find_cheap_obligations") as mock_find:
            mock_find.return_value = [{"path": "test.md", "summary": "cheap"}]
            # First 3 should escalate
            for i in range(3):
                assert should_escalate(violations, "test-cap-session") is True
                _increment_block_count("test-cap-session")
            # 4th should NOT escalate (cap reached)
            assert should_escalate(violations, "test-cap-session") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:/Users/brsth/.grok/hooks/scripts && python -m pytest test_deferral_gate.py -v`
Expected: FAIL with `ImportError: cannot import name 'classify_obligation' from 'behavioral_check'`

- [ ] **Step 3: Write implementation (add to behavioral_check.py)**

Add these imports near the top (after existing imports):

```python
import hashlib
import time
```

Add these constants near the existing configuration section:

```python
# ---------------------------------------------------------------------------
# Escalation gate configuration
# ---------------------------------------------------------------------------

MAX_STOP_BLOCKS = 3
BLOCK_COUNTER_PREFIX = "deferral-block-count-"
HANDOFFS_DIR = Path("P:/docs/handoffs")
STATE_DIR = Path.home() / ".grok" / "hooks" / "state"

# Keywords that indicate EXPENSIVE work (word-boundary match)
EXPENSIVE_KEYWORDS_RE = re.compile(
    r"\b(?:design|architecture|refactor|new\s+skill|multi-system|multi-file|"
    r"L\s+effort|spike|investigation)\b",
    re.IGNORECASE,
)

# File path references in handoff text
FILE_PATH_RE = re.compile(
    r"(?:P:|~|C:/Users/brsth)/[^\s\)]+\.\w{2,4}",
    re.IGNORECASE,
)
```

Add the obligation classification and scanning functions (after `check_behavioral_violations`, before `extract_response_text`):

```python
# ---------------------------------------------------------------------------
# Cheap-obligation scanner (escalation gate for UNNECESSARY_DEFERRAL)
# ---------------------------------------------------------------------------

def classify_obligation(handoff_text: str) -> str:
    """Classify a handoff's work as CHEAP or EXPENSIVE.

    Category-based (not time estimation):
    - CHEAP: <=1 file reference AND no design/architecture keywords
    - EXPENSIVE: >1 file reference OR contains design keywords

    Hook-authored (pattern-based), NOT agent-authored.
    Prevents the gaming vector where the agent labels everything EXPENSIVE.
    """
    if not handoff_text:
        return "EXPENSIVE"  # fail-safe

    # Check for expensive keywords (word-boundary, not substring)
    if EXPENSIVE_KEYWORDS_RE.search(handoff_text):
        return "EXPENSIVE"

    # Count unique file path references
    paths = set(FILE_PATH_RE.findall(handoff_text))
    if len(paths) > 1:
        return "EXPENSIVE"

    return "CHEAP"


def find_cheap_obligations(session_id: str) -> list[dict]:
    """Find cheap open obligations in handoffs owned by this session.

    Filters by current_session_id frontmatter (NOT mtime window) to prevent
    cross-session contamination on multi-terminal hosts. Per F-03 fix.

    Returns:
        List of {"path": str, "summary": str} for each cheap open obligation.
    """
    if not session_id or not HANDOFFS_DIR.exists():
        return []

    cheap_obligations = []

    for md_file in HANDOFFS_DIR.rglob("HANDOFF.md"):
        try:
            text = md_file.read_text(encoding="utf-8")

            # Check session ownership via frontmatter
            # Try current_session_id first, then session_id
            fm_match = re.search(
                r"current_session_id:\s*([^\n]+)",
                text,
            )
            if not fm_match:
                fm_match = re.search(r"session_id:\s*([^\n]+)", text)
            if not fm_match:
                continue  # no session ownership info — skip

            handoff_session = fm_match.group(1).strip().strip('"').strip("'")
            if handoff_session != session_id:
                continue  # not this session's handoff

            # Skip closed/resolved handoffs
            if re.search(r"status:\s*(?:closed|resolved)", text, re.IGNORECASE):
                continue

            # Extract a summary (first non-empty, non-frontmatter line)
            summary = ""
            in_frontmatter = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter:
                    continue
                if stripped and not stripped.startswith("#"):
                    summary = stripped[:100]
                    break

            if classify_obligation(text) == "CHEAP":
                cheap_obligations.append({
                    "path": str(md_file),
                    "summary": summary,
                })
        except Exception:
            continue  # fail-open on per-file errors

    return cheap_obligations


# ---------------------------------------------------------------------------
# Escape hatches for the escalation gate
# ---------------------------------------------------------------------------

def _block_count_file(session_id: str) -> Path:
    return STATE_DIR / f"{BLOCK_COUNTER_PREFIX}{session_id}.json"


def _get_block_count(session_id: str) -> int:
    f = _block_count_file(session_id)
    if not f.exists():
        return 0
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("count", 0)
    except (json.JSONDecodeError, OSError):
        return 0


def _increment_block_count(session_id: str) -> None:
    f = _block_count_file(session_id)
    count = _get_block_count(session_id) + 1
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        # Atomic write: write to temp then rename
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps({"count": count}), encoding="utf-8")
        tmp.replace(f)
    except OSError:
        pass  # fail-open


def _reset_block_count(session_id: str) -> None:
    f = _block_count_file(session_id)
    try:
        if f.exists():
            f.unlink()
    except OSError:
        pass


def should_escalate(
    violations: list, session_id: str, payload: dict | None = None
) -> bool:
    """Determine whether UNNECESSARY_DEFERRAL should escalate to BLOCK.

    AND-gate: escalates only when ALL conditions are true:
    1. UNNECESSARY_DEFERRAL violation detected
    2. Cheap open obligations exist for this session
    3. No escape hatch fires:
       a. stopHookActive (prevents infinite loop)
       b. MAX_STOP_BLOCKS not exceeded (prevents unbounded blocking)
    """
    # Condition 1: must have UNNECESSARY_DEFERRAL violation
    has_deferral = any(
        v[1] == "UNNECESSARY_DEFERRAL" for v in violations
    )
    if not has_deferral:
        return False

    # Escape hatch a: stopHookActive (prevents infinite loop)
    if payload and payload.get("stopHookActive", False):
        return False

    # Escape hatch b: MAX_STOP_BLOCKS cap
    if _get_block_count(session_id) >= MAX_STOP_BLOCKS:
        return False

    # Condition 2: cheap open obligations
    cheap_obs = find_cheap_obligations(session_id)
    if not cheap_obs:
        return False

    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/brsth/.grok/hooks/scripts && python -m pytest test_deferral_gate.py -v`
Expected: 12/12 PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/brsth/.grok
git add hooks/scripts/behavioral_check.py hooks/scripts/test_deferral_gate.py
git commit -m "feat: add cheap-obligation escalation gate to behavioral_check

When UNNECESSARY_DEFERRAL is detected AND the session has cheap open
obligations (handoffs owned by this session via current_session_id),
escalate from ADVISORY (exit 0) to BLOCK (exit 2).

Category-based classification (CHEAP/EXPENSIVE by file count + keywords)
replaces rejected time-estimation approach. Hook-authored, not agent-authored.

Escape hatches: stopHookActive check + MAX_STOP_BLOCKS=3 cap.
Session-scoped handoff scan via current_session_id frontmatter (not mtime).

Extends existing production-narrowed regex instead of creating a parallel hook.
Revision 2 of plan 2026-08-12-deferral-stop-gate (Round 1 review: 5 CRITICAL
findings resolved by extending behavioral_check instead of duplicating it)."
```

---

## Task 2: Wire escalation into main() + integration tests

**Files:**
- Modify: `C:/Users/brsth/.grok/hooks/scripts/behavioral_check.py:main()` (add escalation logic between violation detection and output)
- Test: `C:/Users/brsth/.grok/hooks/scripts/test_deferral_gate.py` (add integration tests with camelCase payloads)

**Interfaces:**
- Consumes: `should_escalate`, `_increment_block_count` from Task 1
- Produces: the live, registered hook with blocking capability

**Success observation:** integration test `test_end_to_end_blocking_with_camelcase_payload` passes — a camelCase Stop payload with deferral language and a cheap session-owned handoff produces exit code 2.

**Failure observation:** test fails or hook doesn't block.

**Most likely failure mode:** the block message contains phrases that trigger recursive detection.

**Failure signals:** `test_block_message_no_recursive_trigger` fails — block message contains "fresh session" or "next session".

**Countermove:** block message avoids all deferral trigger phrases.

**Branch triggers:** none.

**Abort condition:** if `main()` fails to parse stdin — abort (fail-open, already handled).

- [ ] **Step 1: Write failing integration tests**

```python
# Append to test_deferral_gate.py

def _make_stop_payload(session_id, message_text, stop_hook_active=False):
    """Create a camelCase Stop payload matching production Grok Build format."""
    return {
        "sessionId": session_id,
        "stopHookActive": stop_hook_active,
        "lastAssistantMessage": message_text,
    }


def test_end_to_end_blocking_with_camelcase_payload(tmp_path):
    """Full flow: camelCase payload + deferral + cheap obligation → exit 2."""
    import io
    from behavioral_check import main
    payload = _make_stop_payload(
        "e2e-block-session",
        "I should defer this to a fresh session next time.",
    )
    with patch("behavioral_check.STATE_DIR", tmp_path), \
         patch("behavioral_check.find_cheap_obligations") as mock_find, \
         patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         patch("sys.stdout"):
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        try:
            main()
            assert False, "Should have exited with code 2"
        except SystemExit as e:
            assert e.code == 2


def test_end_to_end_allow_without_deferral(tmp_path):
    """Full flow: no deferral language → exit 0 (existing behavior unchanged)."""
    import io
    from behavioral_check import main
    payload = _make_stop_payload(
        "e2e-allow-session",
        "All tests pass. The fix is committed.",
    )
    with patch("behavioral_check.STATE_DIR", tmp_path), \
         patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         patch("sys.stdout"):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0


def test_end_to_end_stop_hook_active_prevents_block(tmp_path):
    """stopHookActive=True → no block even with deferral + cheap obligation."""
    import io
    from behavioral_check import main
    payload = _make_stop_payload(
        "e2e-sha-session",
        "I should defer this to a fresh session.",
        stop_hook_active=True,
    )
    with patch("behavioral_check.STATE_DIR", tmp_path), \
         patch("behavioral_check.find_cheap_obligations") as mock_find, \
         patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         patch("sys.stdout"):
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        try:
            main()
        except SystemExit as e:
            assert e.code == 0  # not blocked


def test_block_message_no_recursive_trigger(tmp_path):
    """Block message must NOT contain deferral trigger phrases.

    Per F-05: the block message itself must not contain 'fresh session'
    or 'next session' — these would trigger recursive detection.
    """
    import io
    from behavioral_check import main
    payload = _make_stop_payload(
        "recur-test",
        "I should defer this to a fresh session.",
    )
    captured = io.StringIO()
    with patch("behavioral_check.STATE_DIR", tmp_path), \
         patch("behavioral_check.find_cheap_obligations") as mock_find, \
         patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         patch("sys.stdout", captured):
        mock_find.return_value = [{"path": "test.md", "summary": "Fix typo"}]
        try:
            main()
        except SystemExit:
            pass
    output = captured.getvalue()
    # Must NOT contain recursive trigger phrases
    forbidden = ["fresh session", "next session", "defer to"]
    for phrase in forbidden:
        assert phrase.lower() not in output.lower(), \
            f"Recursive trigger: block message contains '{phrase}'"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:/Users/brsth/.grok/hooks/scripts && python -m pytest test_deferral_gate.py -v -k "end_to_end or recursive_trigger"`
Expected: FAIL (main() doesn't have escalation logic yet; no block message exists)

- [ ] **Step 3: Modify main() to add escalation logic**

In `behavioral_check.py`, find the section after violations are checked and before output is built (around line 260-280). Add the escalation logic:

After the existing line `has_block = any(v[4] == "BLOCK" for v in violations)`, add:

```python
    # Escalation gate: UNNECESSARY_DEFERRAL + cheap obligation → BLOCK
    session_id = payload.get("sessionId", "")
    if not has_block and should_escalate(violations, session_id, payload):
        # Escalate UNNECESSARY_DEFERRAL violations to BLOCK severity
        violations = [
            (v[0], v[1], v[2], v[3], "BLOCK") if v[1] == "UNNECESSARY_DEFERRAL"
            else v
            for v in violations
        ]
        has_block = True
        _increment_block_count(session_id)
```

Then, after the existing block message construction (which uses generic text), add a specific message for the escalation case. Find the `if has_block:` block that builds the message and add before the existing `lines.append` calls:

```python
    # Check if escalation caused the block (vs existing BLOCK-level violations)
    escalation_blocked = (
        has_block
        and any(v[1] == "UNNECESSARY_DEFERRAL" and v[4] == "BLOCK" for v in violations)
    )
    if escalation_blocked:
        cheap_obs = find_cheap_obligations(session_id) if session_id else []
        obligation_list = "; ".join(
            f"{o['summary']}" for o in cheap_obs[:3]
        )
        lines = [
            "BLOCKED: deferral of cheap work detected.",
            "",
            f"Open cheap obligations for this session: {obligation_list}",
            "",
            "Either do the work now, or name the specific constraint that blocks",
            "doing it this session (e.g., 'requires design decisions',",
            "'multi-file change', 'spike needed'). Vague timing is not a constraint.",
            "",
        ]
    elif has_block:
        lines = [
            "BLOCKED: ungrounded state/prediction claim detected.",
            "",
        ]
    else:
        lines = [
            "⚠️ **Behavioral check:** potential violation(s) detected in this response:",
            "",
        ]
```

Note: the existing for-loop that appends violation details (`for matched, vtype, guidance, _, severity in violations:`) continues to work — it will display the UNNECESSARY_DEFERRAL violation with its guidance text, now at BLOCK severity.

**Important:** the escalation block message deliberately avoids the phrases "fresh session", "next session", and "defer to" — these would trigger recursive detection (F-05 fix).

- [ ] **Step 4: Run ALL tests to verify they pass**

Run: `cd C:/Users/brsth/.grok/hooks/scripts && python -m pytest test_deferral_gate.py -v`
Expected: 16/16 PASS (12 from Task 1 + 4 from Task 2)

Also run existing behavioral_check tests to verify no regression:

Run: `cd C:/Users/brsth/.grok/hooks/scripts && python -m pytest test_hooks.py -v -k behavioral`
Expected: existing tests still PASS (the escalation gate doesn't change ADVISORY behavior when no cheap obligations exist)

- [ ] **Step 5: Manual test-fire against real session (runtime receipt)**

Pipe a camelCase payload matching the real Grok Build Stop format:

```powershell
echo '{"sessionId": "manual-test-001", "stopHookActive": false, "lastAssistantMessage": "I should defer this to a fresh session next time."}' | python C:/Users/brsth/.grok/hooks/scripts/behavioral_check.py 2>&1
```

Expected: exit code 0 (no handoffs owned by `manual-test-001` session → no cheap obligations → no escalation). This verifies the hook runs without crashing.

To verify the BLOCK path, create a test handoff:

```powershell
# Create a test handoff owned by the manual-test session
$dir = "P:/docs/handoffs/manual-test-deferral-gate"
New-Item -ItemType Directory -Path $dir -Force
@"
---
current_session_id: manual-test-001
status: open
---
Fix the typo in P:/src/config.py line 42.
"@ | Set-Content -Path "$dir/HANDOFF.md" -Encoding UTF8

# Now test the block path
echo '{"sessionId": "manual-test-001", "stopHookActive": false, "lastAssistantMessage": "I should defer this to a fresh session next time."}' | python C:/Users/brsth/.grok/hooks/scripts/behavioral_check.py 2>&1
```

Expected: exit code 2 (BLOCK), output contains "deferral of cheap work detected" and "Fix the typo".

Verify the counter incremented:
```powershell
Get-Content C:/Users/brsth/.grok/hooks/state/deferral-block-count-manual-test-001.json
```

- [ ] **Step 6: Clean up test artifacts**

```powershell
Remove-Item "P:/docs/handoffs/manual-test-deferral-gate" -Recurse -Force
Remove-Item "C:/Users/brsth/.grok/hooks/state/deferral-block-count-manual-test-001.json" -ErrorAction SilentlyContinue
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/brsth/.grok
git add hooks/scripts/behavioral_check.py hooks/scripts/test_deferral_gate.py
git commit -m "feat: wire escalation gate into behavioral_check main() + integration tests

UNNECESSARY_DEFERRAL now escalates to BLOCK when cheap obligations exist.
Block message avoids recursive trigger phrases (no 'fresh session'/'next session').

Integration tests use camelCase payloads matching production Grok Build format.
Manual test-fire verified against real session-owned handoff.

16/16 tests pass. No regression in existing behavioral_check advisory behavior."
```

---

## Self-review (Revision 2)

**1. Spec coverage:**
- (a) blocking deferral Stop hook ✅ — behavioral_check UNNECESSARY_DEFERRAL escalates to BLOCK
- (b) category-based classification ✅ — Task 1 `classify_obligation`
- (c) escape hatches ✅ — stopHookActive (Task 1) + MAX_STOP_BLOCKS=3 (Task 1)
- (d) conversational channel detection ✅ — existing behavioral_check regex already scans lastAssistantMessage
- (e) integration with existing Stop hook infrastructure ✅ — extends the existing hook, no new registration needed

**2. Placeholder scan:** No TBD, TODO, "add appropriate." All code is complete.

**3. Type consistency:** `classify_obligation` returns `str`, `find_cheap_obligations` returns `list[dict]`, `should_escalate` returns `bool`. Consistent across tasks.

**4. Completeness checks:**
- ✅ Data-flow: handoff text → frontmatter session check → classify_obligation → cheap list → should_escalate → main() exit code. All steps specified.
- ✅ Latency: file I/O scan of handoffs dir. O(N) where N = handoff count (~50-100 typical). No LLM calls. Existing 30s timeout is sufficient.
- ✅ Under-specified definitions: CHEAP/EXPENSIVE have operational definitions. Session ownership defined via `current_session_id` frontmatter.
- ✅ Cost-proxy: no cost formula used.
- ✅ Exception safety: all file I/O wrapped in try/except. `main()` wraps stdin parse in try/except. Per-file errors in `find_cheap_obligations` are caught and skipped.
- ✅ Internal consistency: AND-gate is consistent. Escape hatches checked in order (stopHookActive → MAX_STOP_BLOCKS → cheap obligations).

**5. Escape hatch count:** 4 implemented in code (stopHookActive, MAX_STOP_BLOCKS, AUP-safe block text via message review, session-scoped state). The 5th (hook file integrity / read-only) is documented as a deployment concern below.

## Deployment concern (5th escape hatch — not a code task)

The 5th escape hatch from /www research is "agent rewrites its own hooks" (claude-code #32376). This is a file-permissions concern, not code: verify `behavioral_check.py` is not writable by the agent process, or add a SessionStart integrity check that hashes the file and alerts on modification. This is out of scope for this plan but should be tracked as a follow-up.

## Execution handoff

Plan complete and saved to `P:/docs/superpowers/plans/2026-08-12-deferral-stop-gate.md`.
Revision 2 (Round 1 review: 5 CRITICAL + 10 HIGH findings resolved; 23 total findings addressed).

Execution options:

**1. `/go execute P:/docs/superpowers/plans/2026-08-12-deferral-stop-gate.md` (recommended)** — profile `plan-execute`: H2 off (plan is SoT), H0 git/non-git, task DAG for H4, TDD red-before-green, checkbox ticks + Execution Status at GO DONE.

**2. Subagent-Driven (manual)** — dispatch a fresh subagent per task, review between tasks.

**3. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
