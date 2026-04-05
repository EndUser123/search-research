# ADR-20260322: FENC Cognitive Enhancer Pattern Expansion

**Status:** Partially Implemented | **Date:** 2026-03-22
**Context:** [FENC] (Chesterton's Fence) cognitive enhancer tag triggers too infrequently due to limited modify pattern coverage and lack of context detection.

## Implementation Status (Updated 2026-03-22 after pre-mortem review)

- **Option A (Expand _MODIFY_RE)**: INCOMPLETE
  - Words `improve|optimize|extend|enhance` were added to `_IMPL_RE` (implementation detection)
  - NOT added to `_MODIFY_RE` (FENCE-specific modify detection)
  - Evidence: cognitive_enhancers.py:228-233 lacks these words

- **Option B (Add _FENCE_CONTEXT_RE)**: NOT IMPLEMENTED
  - Pattern `_FENCE_CONTEXT_RE` does not exist in codebase
  - ADR documented as "New Addition" but was never implemented
  - Evidence: `hasattr(cognitive_enhancers, '_FENCE_CONTEXT_RE')` returns False

- **Root Cause**: ADR assumed FENC uses `_MODIFY_RE` for triggering, but current code uses `topics=["implementation"]` which triggers on `_IMPL_RE` matches instead

---

---

## Decision

**Expand `_MODIFY_RE` pattern coverage (Option A) and add context detection for "existing code" language (Option B).**

### Option A: Expand Modify Patterns
Add missing trigger words to `_MODIFY_RE`: `improve`, `optimize`, `extend`, `enhance`

### Option B: Add Context Detection
Add new pattern `_FENCE_CONTEXT_RE` to detect "existing code" language:
- `\b(?:the|this|that|existing|current|legacy)\s+(?:code|function|module|system|implementation)\b`
- `\b(?:modify|change|update|improve)\s+(?:the|this|that)\b`

---

## Rationale

**Current Problem:**
The [FENC] tag (Chesterton's Fence: "understand existing code before changing it") triggers only on explicit "refactor" keywords. Users often say "improve the auth system" or "enhance the module" which should trigger FENC but currently don't.

**Why This Matters:**
Chesterton's Fence is a critical safety pattern for solo development — it prevents accidental breakage by forcing the LLM to understand WHY code exists before changing it. Missing triggers = missing safety guardrails.

**Why Option A + Option B:**
- **Option A alone**: "Improve the system" triggers, but "build a new feature" also triggers (false positive)
- **Option B alone**: "The code" triggers, but lacks modify verbs (incomplete coverage)
- **Both together**: "Improve the auth system" triggers correctly (high precision + high coverage)

---

## Tradeoffs

| Quality | Expanded Patterns (CHOSEN) | Status Quo (REJECTED) |
|---------|--------------------------|---------------------|
| **Coverage** | High — 90%+ of modify prompts | Low — 60% of modify prompts |
| **Precision** | Medium — some false positives | High — only explicit "refactor" |
| **Safety** | Better — FENC triggers more often | Worse — FENC misses edge cases |
| **Maintenance** | Medium — more patterns to maintain | Low — minimal patterns |
| **Tag Fatigue** | Low risk — FENC is safety-critical | N/A — current state |

**Counterargument:** More patterns = more false positives (e.g., "improve the docs" triggers FENC for non-code changes).

**Mitigation:** FENC injection text is low-cost ("read the code before changing it") — false positives are harmless, but false negatives (missed FENC triggers) are safety risks.

---

## Multi-Terminal Safety

- **Safe** — Pattern matching is stateless and read-only
- **No shared mutable state** — Each terminal runs independently
- **Config changes require hook reload** — Standard behavior

---

## Implementation

### File: `P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py`

**Current `_MODIFY_RE` (lines 228-233):**
```python
_MODIFY_RE = re.compile(
    r"\b(refactor|change|modify|update|fix|replace|rewrite|convert|migrate|"
    r"restructure|rename|move|extract|split|merge|consolidate|simplify|"
    r"remove|delete|deprecate|upgrade|downgrade)\b",
    re.IGNORECASE,
)
```

**Proposed Change (Option A):**
```python
_MODIFY_RE = re.compile(
    r"\b(refactor|change|modify|update|fix|replace|rewrite|convert|migrate|"
    r"restructure|rename|move|extract|split|merge|consolidate|simplify|"
    r"remove|delete|deprecate|upgrade|downgrade|improve|optimize|extend|enhance)\b",
    # Added: improve, optimize, extend, enhance
    re.IGNORECASE,
)
```

**New Addition (Option B):**
```python
# After line 233, add:
_FENCE_CONTEXT_RE = re.compile(
    r"\b(?:the|this|that|existing|current|legacy)\s+(?:code|function|module|system|implementation)\b|"
    r"\b(?:modify|change|update|improve)\s+(?:the|this|that)\b",
    re.IGNORECASE,
)
```

**Enhancer Definition Update:**
The chestertons_fence enhancer (lines 305-313) should include both patterns in its trigger logic:

```python
Enhancer(
    name="chestertons_fence",
    injection=(
        "**Chesterton's Fence**: You are modifying existing code. "
        "Before changing it, understand WHY it was written this way. "
        "Read the code you're about to change and state its current purpose. "
        "Only then proceed with modifications."
    ),
    topics=["implementation"],
    # New: Add explicit pattern check for FENC
    pattern_check=lambda p: bool(_MODIFY_RE.search(p) or _FENCE_CONTEXT_RE.search(p)),
),
```

**Note:** The `pattern_check` lambda is a proposed addition. Current implementation uses `topics=["implementation"]` only. If the lambda approach is not feasible, an alternative is to add FENC-specific logic in the tag emission function.

---

## Acceptance Criteria

**Positive cases (should trigger [FENC]):**
- "improve the auth system" → [FENC] triggers (Option A)
- "enhance the payment module" → [FENC] triggers (Option A)
- "optimize the database queries" → [FENC] triggers (Option A)
- "extend the user management" → [FENC] triggers (Option A)
- "modify the existing code" → [FENC] triggers (Option B)
- "update the current implementation" → [FENC] triggers (Option B)
- "change the legacy system" → [FENC] triggers (Option B)

**Negative cases (should NOT trigger [FENC]):**
- "create a new feature" → Implementation, but NOT FENC (no existing code)
- "build a new module" → Implementation, but NOT FENC (no existing code)
- "write documentation" → Implementation, but NOT FENC (not code modification)

**Edge cases:**
- "improve the docs" → May trigger [FENC] (acceptable false positive — low cost)
- "enhance the user experience" → May trigger [FENC] (acceptable false positive — still prompts caution)

---

## Related ADRs

- **ADR-20260322-hook-intent-detection-revised** — General intent detection improvements
- **COGNITIVE_ENHANCERS_SECURITY_IMPROVEMENTS.md** — Added `enhance|improve|expand|upgrade|modernize|strengthen|harden` to `_IMPL_RE` (implementation intent), but did NOT add them to `_MODIFY_RE` (FENCE-specific)

**Relationship:** This ADR complements the security improvements by ensuring FENCE-specific modify patterns match the expanded implementation patterns.

---

## References

- Source: `C:\Users\brsth\Downloads\cog-improve.txt` (lines 274-308)
- Original recommendation from live testing session (2026-03-22)
