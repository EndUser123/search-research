---
title: "Session observations: model-selection defect fix + error taxonomy + continuation pipeline"
session: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
date: 2026-08-08
status: CLOSED
host: grok
---

# Session observations

## Work streams completed

### 1. Model-selection defect fix (continuation from prior session)
- **Quarantine GC** (HIGH, flagged twice): `write_quarantine_record()` now prunes expired records on every write via `_quarantine_expired()`. File-growth guard, not correctness (reader-side already handled expiry).
- **Error taxonomy 7→11** (MEDIUM): Added timeout (408/504), contract_malformed, identity_mismatch, scope_violation. Aligned with Codex proposal taxonomy. 39 tests pass.
- **Hook-block logging propagation**: Extracted shared `hook_block_logger.py`, all 4 blocking PreToolUse hooks adopt it. msvcrt.locking for concurrency safety.
- **Dead-zone policy**: Removed docs/designs/ from dead zones (empirically incorrect — 4+ skills actively use it).

### 2. Post-compact continuation prompt system (new)
- **Design** (/www + /tp reviewed): 4-hook pipeline (PreCompact capture → PostCompact arm → UserPromptSubmit inject → SessionEnd cleanup). Uses confirmed-working paths only.
- **Implementation**: 4 scripts, 4 JSON registrations, AGENTS.md section, wiki concept. 8 integration tests.
- **Architecture decision**: Two-hook PostCompact+UserPromptSubmit pattern chosen over SessionStart(compact) because UserPromptSubmit additionalContext is confirmed working on this host (quota-availability-injector proves it). SessionStart additionalContext remains CONTRADICTED between Grok Build and Claude Code docs.

### 3. Refactor plan execution (6 seams)
- A1: Cooldown parameter extraction (eliminates module mutation + self-import cycle)
- A2: Session-id helper extraction (DRY across 8+ hooks)
- A3: State-dir helper extraction (DRY across 4 continuation hooks)
- A4: Self-import cycle resolved (consequence of A1)
- A5: SyntaxWarning fix (raw docstrings in dead_zone_guard.py)
- A6: Formalized continuation pipeline tests into hooks/tests/

### 4. Other
- claude-mem hook fix: set HOME and SHELL user env vars (Windows doesn't have them by default)
- Wiki concepts: 3 created (error taxonomy, hook-block observability, continuation prompt)
- Review docs: 2 updated (Grok review doc C5 finding, taxonomy alignment table)
- SHIP VERIFIED: all 12 ship-py phases passed

## Open items for next session

1. **Monitor first real compaction** — the continuation pipeline has 8 tests but has never fired on a real compaction. Watch for: continuation-{sid}.md appearing, armed-{sid}.md being consumed, additionalContext in first post-compact turn.
2. **Reload hooks** — press 'r' in Hooks tab to activate the 4 new continuation hooks + the hook-block logging changes.
3. **Add Stop-hook auto-write path** — the /tp critique identified this as the main gap: PreCompact fallback captures git commits + handoffs but not session-specific reasoning.
4. **Use larger output budget model for ship-py review** — MiniMax-M3 truncated both review agents. Consider or-ling-3-flash or glm-5-2 for review tasks.

## Commits this session

P:/ repo:
- 915f37e: wiki + review doc 11-class taxonomy update
- 17eeaca: wiki + review doc 11-class taxonomy update
- a240d29: track uncommitted wiki concepts and design docs

~/.grok repo:
- 977e35b: quarantine GC
- 7c9c9af: error taxonomy 7→11
- bbbbcdf: log_block locking
- 813b127: hook-block logging propagation
- 396beed: dead-zone policy docs/designs/ removal
- f388e94: hook-block observability wiki update
- aac39fc: post-compact continuation prompt pipeline
- 915f37e: wiki: post-compact continuation prompt
- 3f4e251: ruff format auto-fix
- 0381a80: refactor 6 seams

Both repos pushed to origin.
