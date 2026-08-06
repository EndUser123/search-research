---
thread_id: 019fc5eb-todo-consolidation-20260806
parent_handoff_path: P:/docs/handoffs/todo-rns-renderer-and-scanner-20260803/HANDOFF.md
current_session_id: 019fc5eb-183e-7bf2-89bc-160737289cba
current_terminal_id: grok-main
produced_at: 2026-08-06T18:00:00-06:00
status: open
handoff_type: implementation
accurate_as_of_head: fd20f5a
---

# Handoff: /todo renderer consolidation

## 1. Objective

Consolidate the /todo skill from 3 render paths to a single toon renderer, removing ~900 lines of redundant code.

## 2. Status

**CLOSED — work complete.** All changes committed and verified.

## 3. What was done this session

### Commit 533a3eb: mechanical cross-source dedup
- Added `_normalize_ref()` and `_dedup_key()` to `render_rns.py` (initially in `build_actions_from_scan`)
- Fixed cross-source duplicates: `www` and `wiki` both reading the same epistemic-debt cache
- `/tp` critique (REVISE verdict, `zen-deepseek-v4-flash-free`) caught that the initial approach (wire LLM evaluation into v2) was wrong — mechanical dedup at scanner layer is correct

### Commit fd20f5a: renderer consolidation
- `render_rns.py`: 851 → 88 lines (only `format_toon_rns()` remains)
- `scan_functions.py`: dedup moved here (`_normalize_ref`, `_dedup_scan_items`)
- `test_render_rns.py`: rewritten for toon-only coverage (10 tests, all pass)
- SKILL.md: removed `--detailed`, `/todo new`, plain renderer docs

### Verification
- 10/10 tests pass
- Dedup functions verified (cross-source collapse, SKILL.md distinctness)
- Toon renderer functional (4 sections, handoff count, scoped footer)
- Removed code confirmed gone (no dangling imports)
- Ruff lint clean
- Wiki concept written: `P:/.data/wiki/concepts/toon-renderer-consolidation-single-format.md`

## 4. Remaining work

### High priority
- **155 code defects across 10 skills** (close 62, ship-rhai 21, aar 14, model-web 12, ship-py 12, todo 10, handoff 9, skill-dev 7, tp 5, packet 2). Chronic — batch via `/skill-dev measure` or a dedicated defect sweep.
- **Push both repos** — ~/.grok has unpushed commits from this session. P:/ has 23 modified + 19 untracked from sibling sessions.

### Medium priority
- **Record outcome on unresolved tp REVISE** (PreToolUse ship phase-state gate hook, 2026-08-05). Critique verdict has no recorded outcome.
- **Review fresh dream proposal** (2026-08-06-dream, age 0d). Promote via /wiki or retire.

### Low priority
- **8 epistemic debt concepts** (0.52-0.58). Re-verify or accept as-is.
- **Prior handoff `todo-rns-renderer-and-scanner-20260803`** is now superseded — should be marked CLOSED.

## 5. Key decisions

1. **Toon is the sole renderer.** The operator confirmed this format after comparing it against the hierarchical and v2 renderers. The toon format (blank-line-separated items, markdown-collapse-resistant, NOW/NEXT/HANDOFF/LATER sections) is the design standard for /todo output.

2. **Dedup belongs at the scanner layer, not the renderer.** The /tp critique correctly identified that cross-source duplicates should be fixed in `scan_functions.py` where they originate, not patched in each renderer. This is an instance of `[[mechanical-as-input-not-mechanical-as-frame]]`.

3. **LLM evaluation stays between scan and render, not inside render.** The 8-question evaluation filter (is it done? false positive? duplicate? actionable?) runs in the LLM's judgment, not in code. The renderer formats; the LLM evaluates; the scanner deduplicates.
