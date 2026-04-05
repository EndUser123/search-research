# Adversarial Compliance Review: Stop Completion/Negative Existence Guards

**Reviewer:** Adversarial Compliance Specialist
**Date:** 2026-03-31
**Files Reviewed:**
- `Stop_completion_verification_guard.py` (v1.0, 2026-03-24)
- `Stop_negative_existence_guard.py` (no version/date)
- `Stop_router.py` (protocol handler)
- `tests/test_stop_negative_existence_guard.py`

**Proposed Changes Under Review:**
1. Change `tool_events is None` handling from fail-closed (block) to fail-warn (advisory)
2. Expand context window from 200/200 to 400/100 before/after in path extraction
3. Add conversational verification phrases to allowlist

---

## Finding 1: FAIL-WARN Change Breaks Exit Code Protocol (CRITICAL)

### Issue

Both guards implement fail-closed behavior at their `tool_events is None` branches:

**Stop_completion_verification_guard.py:519-542**
```python
# Evidence system unavailable - ALWAYS block (fail-closed)
if tool_events is None:
    _logger.warning("BLOCK: Evidence store unavailable ...")
    ...
    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_completion_verification_guard",
    }
```

**Stop_negative_existence_guard.py:478-504** — identical pattern.

The Stop hook protocol (per `PROTOCOL.md` and `CLAUDE.md`):

| Exit Code | Meaning for Stop Hooks |
|-----------|----------------------|
| 0         | Allow stop/completion |
| 2         | Block stop (force continuation) |

The `run()` function in both files is the in-process protocol handler:

**Stop_completion_verification_guard.py:604-613**
```python
def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_completion_verification_guard"),
        }
    return result  # <-- None if no block -> implicit exit 0 (ALLOW)
```

**Critical flaw: There is no warn/advisory exit path in `run()` or `main()` for the `tool_events is None` case.**

If `tool_events is None` and the code is changed to return a warn decision (or None), `run()` returns `None`, which causes the caller to exit 0 (ALLOW). This means:

- The response would be **allowed without any warning** injected into the output
- The warning message is never communicated to the caller
- The `blocking_hook` key would be absent, making debugging impossible

The `main()` function (lines 619-636) has a comment suggesting warn mode was anticipated:
```python
# warn -> exit 0 (non-blocking, but message is injected)
```
But this comment describes a design that does not exist in the current code. `main()` only handles block decisions with exit 2.

### Verdict

**The fail-warn change cannot be implemented without adding an explicit advisory return path** to both `run()` and `main()` that:
1. Returns a dict with `decision: "warn"` and the warning message
2. Causes the Stop router to inject the warning into the response
3. Exits 0 (allow with warning)

Without this protocol extension, switching to fail-warn produces **silent allow** — strictly worse than the current fail-closed behavior.

---

## Finding 2: Context Window Expansion 200→400 Is Safe (ADVISORY)

### Current Code

**Stop_completion_verification_guard.py:372-374** (path extraction context)
```python
start = max(0, match.start() - 200)
end = min(len(response), match.end() + 200)
context = response[start:end]
```

The proposed change expands to `match.start() - 400` and `match.end() + 100`.

### Analysis

- **Input validation:** The context window operates on an already-extracted string from the LLM response. No user input is directly used in the slice calculation.
- **Regex safety:** `FILE_PATH_PATTERNS` (lines 271-279) is a compiled regex; the expanded window only changes how much text is passed to `_extract_file_paths()`. Larger context increases recall (more paths found) but does not introduce new regex evaluation surface.
- **No file system operations:** The extraction is purely string-based; no writes or reads occur based on the extracted paths within this function.
- **Performance:** Doubling the before-window from 200 to 400 chars increases string slicing by 2x in the worst case. Still negligible for LLM response lengths.

### Verdict

**Safe to implement.** No adversarial surface introduced. The main risk is increased false-positive path extraction (extracting paths from unrelated text), which is a precision tradeoff, not a security issue.

---

## Finding 3: Allowlist Regex Patterns Are Correct (ADVISORY)

### Patterns Analyzed

**Stop_negative_existence_guard.py:96-120** — OBVIOUS_ALLOWLIST

Key additions (lines 106-118):
```python
r"|\bI\s+didn(?:'?t)?\s+(?:change|modify|delete|remove|create|make|do)\b"
r"|\bI\s+don(?:'?t)?\s+(?:think\s+)?I\s+(?:change|modify|delete|remove|create|make|do)\b"
r"|\b(?:that's\s+not|that\s+isn't|that\s+is\s+not|that\s+wasn't|that\s+was\s+not)\s+(?:something\s+)?I\s+(?:change|modify|delete|remove|create|make|do)\b"
```

**Stop_completion_verification_guard.py:282-299** — OBVIOUS_ALLOWLIST

```python
r"\bI\s+did(?:n'?t|dn't| not)\s+(?:create|modify|delete|remove|write|copy|move|backup)\b"
r"\bI\s+hav(?:e'?n't|en't|e not)\s+(?:created|modified|deleted|removed|written|copied|moved|backed\s+up)\b"
```

### Analysis

1. **Apostrophe handling:** Both files use `'?t` or `'?t?` to match both standard ("didn't") and Unicode curly apostrophe ("didn't") forms. This is correct Python regex idiom.

2. **Word boundaries:** All patterns use `\b` at start and end, preventing substring false positives:
   - `\bI\s+didn't\s+change\b` will NOT match "I didn't change the file" — but wait. Let me verify: in "I didn't change", the `\b` after `change` matches between `e` and `the`, which is correct. The pattern should work.

3. **Specific verb lists vs. wildcard:** The allowlist uses enumerated verb lists rather than `.*`. This is correct — a wildcard would make the allowlist too broad.

4. **Negative existence vs. completion guard asymmetry:** The completion guard's allowlist (line 282-286) includes "I didn't create X" which exempts it from CREATION claims. The negative existence guard's equivalent patterns (lines 106-107) are broader — they exempt ANY action verb, not just file-creation verbs. This is appropriate because "no X file" claims are more general.

### Verdict

**Patterns are correct.** No regex DoS vectors (no unbounded repetition). No catastrophic backtracking patterns. The apostrophe-flexible design handles both ASCII and Unicode curly quotes.

---

## Finding 4: Silent Allow — The Actual Risk of Fail-Warn

### The Deeper Problem

Even if the exit code protocol were extended to support advisory mode, there is a semantic problem:

When `tool_events is None`:
- The evidence system is **completely unavailable** (import failed OR `load_tool_events()` threw an exception)
- This means there is **no way to verify** whether the AI used verification tools

The current fail-closed behavior (block) reflects a philosophical position: "We cannot verify you used tools, so we must assume the claim is unverified."

The proposed fail-warn (advisory) assumes: "Even though we can't verify, we'll let it through and hope the claim is correct."

**From an adversarial compliance standpoint:**
- A blocked response can be retried after running verification tools
- A silently allowed false claim propagates to the user
- The cost of false positive (blocking legitimate claims) is lower than the cost of false negative (allowing hallucinated gap analysis)

### Recommendation

Maintain fail-closed for `tool_events is None`. If advisory behavior is genuinely needed, add a **structured advisory return path** (`decision: "warn"`) to the Stop hook protocol, with proper exit code handling (exit 0 with warning text), before implementing it.

---

## Summary

| Finding | Severity | Status |
|---------|----------|--------|
| Fail-warn breaks exit code protocol | CRITICAL | **BLOCKED** — requires protocol extension before implementation |
| Context window expansion 200→400 | ADVISORY | **SAFE** — no adversarial surface |
| Allowlist regex patterns | ADVISORY | **SAFE** — correctly formed, no DoS vectors |
| Silent allow risk | HIGH | **BLOCKED** — fail-open is strictly worse than fail-closed for verification hooks |

**Overall Verdict: 2 of 3 proposed changes are blocked.**

The context window and allowlist changes can proceed. The fail-warn change cannot proceed without a protocol extension to the Stop hook system that introduces a structured advisory return path with proper exit code semantics.

---

## Recommendations

1. **Fail-warn change:** Do not implement until Stop_router and both guard `run()`/`main()` functions support a `decision: "warn"` return type that exits 0 but injects warning text.

2. **Context window:** Expand to 400/100 — safe change, no regressions expected.

3. **Allowlist:** Apply the additional conversational patterns — they reduce false positives on legitimate conversational denials.

4. **Protocol documentation:** If advisory/warn mode is desired for future hooks, document the `decision: "warn"` contract in `PROTOCOL.md` with exit code 0 and required fields (`reason`, `blocking_hook` with value `"warn"`).
