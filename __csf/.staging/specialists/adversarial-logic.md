# Adversarial Logic Review: Stop Completion/Negative Existence Guards

## Files Reviewed
- `P:\.claude\hooks\Stop_completion_verification_guard.py`
- `P:\.claude\hooks\Stop_negative_existence_guard.py`

## Change 1: tool_events is None — Fail-Closed to Fail-Warn

**Change:** Convert the `if tool_events is None:` branch from blocking to advisory (warn-only).

### Completion Guard (lines 519–542)

**FINDING: Logical error in conditional scope — NOT introduced by proposed change, but LATENT**

The `tool_events is None` block in `Stop_completion_verification_guard.py` returns a block dict with `"decision": "block"`. Changing to fail-warn means emitting an advisory instead. However:

```python
# Line 520
if tool_events is None:
    ...
    return {"decision": "block", ...}  # ← BLOCK

# Line 545
if not tool_events:  # ← This is a SEPARATE condition for []
    ...
    return {"decision": "block", ...}  # ← BLOCK
```

The fail-warn conversion only affects the first branch. The second branch (`not tool_events`, i.e., empty list) remains blocking. This is **correct and intentional** — an empty list means evidence is available but no tools were used this turn, which is a genuine gap. Only `None` (evidence system unavailable) would flip to warn.

**Verdict: No logical error introduced. The `None` vs `[]` distinction is preserved.**

### Negative Guard (lines 478–504)

```python
# Line 478
if tool_events is None:
    return {"decision": "block", ...}

# Line 507
if not tool_events:  # empty list
    return {"decision": "block", ...}
```

Same structure as completion guard. The `None` vs `[]` separation is maintained.

**Verdict: No logical error introduced.**

---

## Change 2: Context Window Expansion (200/200 → 400/100)

**Change:** Expand `start = max(0, match.start() - 200)` to `match.start() - 400` and shrink `end` window from `+200` to `+100`.

### Completion Guard — `_detect_claims()` (lines 372–373)

```python
start = max(0, match.start() - 200)
end = min(len(response), match.end() + 200)
```

**FINDING: `+200` to `+100` shrink is BACKWARDS for path extraction quality.**

The `end` window controls how much text AFTER the match is included when extracting file paths. Expanding `start` from `-200` to `-400` is good (captures more preceding context). But shrinking `end` from `+200` to `+100` means less trailing context for path extraction.

This is not an off-by-one error — it is a **trade-off that may reduce extraction quality** for claims where the filename appears after the match. For example:

```
"... deleted the [MATCH] and then created /path/to/config.yaml [TRAILING CONTEXT NEEDED]"
```

With `+100` instead of `+200`, some long trailing contexts may be truncated, causing regex-based path extraction to miss filenames at the end of the window.

**Verdict: Not an error, but the asymmetric expansion (more before, less after) is an unprincipled trade-off. A symmetric expansion (400/400) or at minimum keeping the `+200` for the trailing window would be more defensible.**

### Path Extraction Is Informational Only

Critically, the extracted `file_paths` in `_detect_claims()` (line 376) are **only used for logging and block messages** — they do NOT gate the decision. The actual claim verification uses `_verify_claim_has_evidence()` which checks tool types, not extracted paths.

Therefore, expanding or shrinking the context window does NOT affect whether a claim is blocked — only what appears in the block message.

---

## Change 3: Add Conversational Verification Phrases to Allowlist

### Completion Guard — OBVIOUS_ALLOWLIST (lines 282–299)

**FINDING: Regex verb-form mismatch — "I didn't modify" is NOT matched by the allowlist.**

The allowlist pattern for conversational denials is:

```
\bI\s+did(?:n'?t|dn't| not)\s+(?:create|modify|delete|remove|write|copy|move|backup)
```

After "didn't", it expects **bare infinitives** (`create`, `modify`, etc.). But grammatically, "I didn't modify" uses the **bare infinitive** after "didn't", which IS correct. However:

```
"I didn't initialize the config"
"I didn't generate the report"
"I didn't set up the directory"
```

These verbs (`initialize`, `generate`, `set up`) are NOT in the list. A user saying "I didn't initialize anything" would NOT be exempted.

Meanwhile, the CREATION_PATTERNS regex at line 181 captures "initialized", "set up", etc. as creation claims. So a user saying "I didn't initialize anything" could be incorrectly flagged.

**Verdict: Narrow verb coverage in allowlist is a GAP, not a logical error. It means more false positives may pass through to claim detection, but claim detection still correctly identifies the claim. The allowlist provides partial relief, not complete coverage.**

### Negative Guard — OBVIOUS_ALLOWLIST Lines 110–111

```python
r"|\bI\s+don(?:'?t)?\s+(?:think\s+)?I\s+(?:change|modify|delete|deleted|remove|create|make|do)\b"
```

**FINDING: Mixing bare infinitive and past participle forms in same choice group.**

This regex alternation includes both `delete` (bare infinitive) and `deleted` (past participle). This means:
- "I don't think I delete" — matched (infinitive) ✓
- "I don't think I deleted" — matched (participle) ✓

But for a sentence like "I don't think I modified" — `modified` is NOT in the list! The list is `change|modify|delete|deleted|remove|create|make|do`. It has `modify` but not `modified`.

So "I don't think I modified anything" would NOT be exempted by this pattern.

**Verdict: Same verb-coverage gap as completion guard — not a logical error, but inconsistent coverage that could let some false positives through the allowlist while blocking others.**

### Negative Guard — Lines 117–118: "that's not something I X" Pattern

```python
r"|\b(?:that's\s+not|that\s+isn't|that\s+is\s+not|that\s+wasn't|that\s+was\s+not)\s+(?:something\s+)?I\s+(?:change|modify|delete|remove|create|make|do)\b"
```

**FINDING: Only bare infinitives — no past participles. "that's not something I modified" is NOT matched.**

The verbs here are only bare infinitives: `change|modify|delete|remove|create|make|do`. There is no `modified`, `deleted`, `created`, etc. So:

- "that's not something I modify" — matched ✓
- "that's not something I modified" — NOT matched ✗

This is the same pattern as the completion guard allowlist — bare infinitives only.

---

## Summary of Findings

| Change | Component | Severity | Issue |
|--------|-----------|----------|-------|
| tool_events is None → warn | completion_guard | None | No logical error. `None` vs `[]` distinction preserved. |
| tool_events is None → warn | negative_guard | None | No logical error. `None` vs `[]` distinction preserved. |
| Context 200/200 → 400/100 | completion_guard | Low | Asymmetric window trade-off (more before, less after) is unprincipled. Path extraction is informational only, so no blocking impact. |
| Allowlist verb coverage | completion_guard | Low | Allowlist misses verbs like "initialize", "generate" — not a logical error, partial coverage only. |
| Allowlist verb coverage | negative_guard | Low | Allowlist mixes verb forms inconsistently (bare infinitive + past participle in same choice group). "modified" missing from "that's not something I X" pattern. |

## Recommendations

1. **For fail-warn change**: The change is logically sound. The `None` vs `[]` separation is maintained in both files.

2. **For context window**: Consider either symmetric expansion (400/400) or keeping `+200` for the trailing window. The asymmetric trade-off provides more context before the match but less after, which is an unprincipled compromise.

3. **For allowlist verbs**: Add past participle forms (`initialized`, `generated`, `set up`, `modified`, etc.) to the conversational denial allowlist in completion_guard to match the verbs actually used in CREATION_PATTERNS and MODIFICATION_PATTERNS.

4. **For negative_guard line 110**: Remove the inconsistency — either use bare infinitives only or past participles only throughout the alternation, not a mix.

5. **For negative_guard lines 117–118**: Add past participle verb forms to the "that's not something I X" pattern to match the coverage of other conversational denial patterns.
