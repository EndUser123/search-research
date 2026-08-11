---
title: close-py post-/tp-review followup — deferred /todo items
status: OPEN
created: 2026-08-11
last_updated_at: 2026-08-11T14:00:00Z
session: 019fef48-02ff-7f30-9abd-67bf440382f0
host: grok
chronicity: acute
---

# close-py post-/tp-review followup — deferred /todo items

## Problem

After shipping the close-py infrastructure blockers (B1-B4) and the
fleet-wide session-ID migration, a /tp review found 3 multi-terminal
safety issues (fixed in-session: commit `e42b2a7`) and a /why RCA found
the verification-loop root cause (receipt writer doesn't fire on
backgrounded tasks). The remaining items from the /todo scan need a
fresh session with full context budget.

## Shipped this session (done)

- ✅ B1-B4 original fixes (4 commits)
- ✅ Track A: 10 Python scripts + 9 SKILL.md migrated to shared resolver
- ✅ /tp review items 1-3: B3 terminal-scoped, B4 AUTO_GENERATED, B1 per-file delete (`e42b2a7`)
- ✅ Item 7: pytest added to AGENTS.md timeout guidance (`645045e`)

## Remaining work

### Item 4: /review on close-py changes
**What:** Run `/review --local` on the diff from this session's 11 modified Python files.
**Why deferred:** /review is a 10-15 min skill that needs full context budget. This session is near compaction.
**Files:** close/__lib/{close_runner,coverage_scan,validate_close_receipt,validate_stop_narrative,close_accounting}.py, aar/__lib/{auto_capture,reference_loader}.py, handoff/__lib/{list_handoffs,migrate_handoff,verify_handoff,claim_handoff}.py
**Acceptance:** FINDINGS.md on disk with verified findings.

### Item 5: /config-audit on AGENTS.md
**What:** Run `/config-audit` to optimize ~/.grok/AGENTS.md (142KB / 1743 lines).
**Why deferred:** 10-20 min skill invocation. AGENTS.md exceeds the 100KB/1000-line threshold.
**Acceptance:** AGENTS.md under 100KB with no information loss.

### Item 6: Receipt writer for backgrounded tasks (ARCHITECTURAL)
**What:** Wire verification_receipt_writer.py to fire when backgrounded tasks complete, not just at PostToolUse time.
**Why deferred:** Architectural change to the hook system. Needs design before implementation.
**Root cause:** Documented in [[posttooluse-fires-on-tool-call-completion-not-process-completion]] — PostToolUse fires on tool-call launch, not process completion. Backgrounded commands produce no receipt → 5-block Stop-hook loop.
**Design constraint:** Multi-terminal safe; must not race with concurrent receipt writes.

### Item 8: 12 SKILL.md spec-drift references
**What:** Fix broken script references in 8 skills (design, go, insight, maintain, marketplace-bridge, model-benchmark, model-discover, refactor).
**Why deferred:** Multi-file fleet work. Mechanical but touches many skills.
**Acceptance:** /skill-dev measure passes on each affected skill.

### Item 9: /maintain
**What:** Full fleet maintenance pass — 55 stale worktrees, config.toml 1323 lines, 16 repos behind upstream.
**Why deferred:** Full skill invocation, separate session.

## Related

- Handoff: `close-py-infrastructure-blockers-20260810` (original B1-B4, status OPEN → now mostly fixed)
- Handoff: `fleet-wide-grok-session-id-empty-env-20260809` (Track A, status IN_PROGRESS → now mostly done)
- Wiki: [[posttooluse-fires-on-tool-call-completion-not-process-completion]] (item 6 design basis)
- Wiki: [[stop-hook-scope-binding-fix-design-decisions]] (receipt writer scope-binding context)
