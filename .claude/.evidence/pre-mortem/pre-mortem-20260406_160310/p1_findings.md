# Phase 1 Findings — adversarial review of lib/render.py

**Target:** `P:/.claude/skills/rns/lib/render.py`
**Session:** pre-mortem-20260406_160310
**Specialists:** adversarial-logic, adversarial-quality, adversarial-testing (3/3 completed)

---

## Consolidated Findings

### BLOCKER

- **LOGIC-001** (render.py:107): Subletter overflow at 27+ items per domain — `chr(ord('a') + idx - 1)` produces `{` at idx=27, corrupting output. Same overflow in `render_machine_format` at line 222.

### HIGH

- **LOGIC-002** (chain.py:233-243): `file_ref` correctly assigned in bug_statement branch, then **unconditionally overwritten to None** at line 236 (else branch). All non-file_reference signals lose their file references even when valid `@ file.py:123` patterns are present.
- **TEST-001** (render.py:139-141): `len()` counts code units, not visual characters. Emoji/non-ASCII descriptions truncate to ~1/3 of intended visual width.
- **TEST-002** (chain.py:279-286): Dedupe key uses `description[:50]` — actions whose descriptions diverge after 50 chars are incorrectly collapsed as duplicates.

### MEDIUM

- **QUAL-001** (chain.py:231-243): Duplicate `file_ref = None` at line 239 makes the first assignment (line 234) dead code. Same root cause as LOGIC-002.
- **LOGIC-003** (chain.py:92): `priority_part.replace('high', 'high')` is a no-op. Comment implies it should normalize variants.
- **LOGIC-004** (chain.py:91): `priority_part` not stripped before replace — fragile but currently coincidentally functional.
- **TEST-003** (render.py:189-205): `render_machine_format` accepts `carryover` param but never iterates it — carryover items silently dropped from machine format.
- **TEST-004** (render.py): No end-to-end test for unknown domain through full `render_actions()` pipeline.
- **TEST-005** (render.py:260): `format_rns_output` passes unknown kwargs directly to `RenderOptions` — raises raw TypeError instead of helpful message.

### LOW

- **QUAL-002** (chain.py:232): `file_ref` loop variable set but unused after loop body — dead store.
- **QUAL-003** (test_render.py:188-196): Test assertion `endswith("1a [recover/high] recover/high")` uses same string as description — zero validation of correct sort order.
- **QUAL-004** (chain.py:279): `seen: set[str] = []` — list used as set, O(n²) dedupe instead of O(n).
- **TEST-006** (render.py:186): No test for domain sort stability with equal priority/count tiebreaking.

---

## Cross-Specialist Consensus

1. **file_ref destruction (LOGIC-002 / QUAL-001):** Both logic and quality specialists independently identified the same bug — unconditional `file_ref = None` overwrite destroying correctly extracted file references. Single fix resolves both.
2. **TEST-001, TEST-002 are Path B (heuristic extraction) issues:** The unicode truncation and dedupe hash collision both affect Path B extraction, not the renderer itself.
3. **LOGIC-003 and LOGIC-004:** Both stem from the same code block — fragile priority normalization with a no-op replace and missing strip.

## Deduplication

| Bug | IDs | Root Cause |
|-----|-----|-----------|
| file_ref overwritten to None | LOGIC-002, QUAL-001 | lines 233-243 chain.py |
| Priority no-op replace | LOGIC-003, LOGIC-004 | chain.py:91-92 |

## Open Questions

1. Is the 26-item-per-domain limit intentional? If two-letter suffixes (aa, ab) are acceptable, LOGIC-001 severity reduces from BLOCKER to HIGH.
2. Is it intentional that Path B only sets `file_ref` for the `file_reference` signal, not other signals containing `@` patterns?
3. Should `render_machine_format` support carryover? If not, TEST-003 should be closed as intentional exclusion.
