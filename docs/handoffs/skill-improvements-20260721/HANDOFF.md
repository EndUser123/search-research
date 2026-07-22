---
thread_id: skill-improvements-20260721
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T21:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: a58d372
source_transcript: C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl
---

# Skill improvements — pattern audit, CJK hook, handoff v0.2, review nits

## Objective

Four independent skill-improvement workstreams that can be worked on without waiting for hook diagnostics or context-file dedup.

## Status

OPEN — all four threads can start immediately.

## Thread A: Cross-skill pattern audit Phase 2/3

**Status:** Phase 1 complete. Phase 2/3 pending. Phase 1 inventory is hot in the session transcript.

**Phase 1 findings (from subagent `019f8502-71b5-7040-b42c-11bf2314c199`):**
- 42 skills read (25 user + 17 bundled)
- 12 patterns identified
- Maturity is bimodal: tp/codex/mmx at 5-7 signals; help/game-*/resume-* at 0
- 8 skills are stubs/duplicates/deprecated (consolidation candidates)

**The 12 patterns:**
1. Bracketed role tag in `spawn_subagent` description
2. Persona injection by reading sibling file
3. Scratch dir + state file + REVIEW_ID pattern
4. Disk-backed findings handoff + `resume_from`
5. Domain selection (core + context-derived)
6. Fresh subagent for different lens + spot-check gate
7. Falsifier section
8. Advocate vs adversary posture distinction
9. Developer preferences block
10. Compatibility stubs (8 skills)
11. Failure-mode vocabulary as named modes
12. `host:` frontmatter tag (30% adoption)

**Phase 2 deliverable:** for each pattern, name the canonical owner skill and rate maturity across all 42 skills.

**Phase 3 deliverable:** for each pattern, propose promote/demote/consolidate.

**Where the data lives:** session transcript at `C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl`. The subagent output is the richest source.

## Thread B: Pre-commit CJK detection hook (OPP-1 from AAR)

**Status:** Not started. AAR rated this ACT_NOW.

**What:** a pre-commit hook that greps staged commit messages for CJK Unicode ranges (`\u4e00-\u9fff`, `\u3040-\u30ff`, `\uac00-\ud7af`) and rejects the commit if found.

**Why:** GLM-5.2 code-switched into Chinese under cognitive load in commit `2f83805`. CLAUDE.md says "English only" but there's no structural enforcement. A pre-commit hook is the durable fix.

**Where:** `~/.grok/hooks/scripts/precommit_cjk_check.py` or a git `pre-commit` hook at `P:/.git/hooks/pre-commit`.

**Design:**
- Scans `$1` or the prepared commit message file for CJK ranges
- If found: prints "ERROR: non-English characters detected in commit message. English only per workspace contract." and exits 1
- If not found: exits 0 (silent)
- Should also scan the full `git diff --cached` for CJK in added lines? (scope decision — may produce false positives for legitimate CJK content in wiki/sources)

## Thread C: `/handoff` v0.2 chain traversal

**Status:** Design documented. Implementation is a separate arc.

**Wiki concept:** `P:/.data/wiki/concepts/optimal-cross-session-chain-traversal-aar-handoff-grok.md`

**Pre-existing handoff:** `P:/docs/handoffs/handoff-v02-aar-integration-20260720/` (READY_FOR_REVIEW, 29h old)

**Design summary:**
1. `/handoff continue <path>` reads prior handoff's five layers (state, narrative, decisions, priorities, warnings)
2. Follows `source_transcript` only if needed and authorized
3. Chain health check: drift detection + citation verification + acyclic
4. New session's first action must reference inherited context (silent-load-failure guard)
5. `/aar` integration: reads prior handoff as evidence, labeled `from_prior_session: true`

**Research base:** five-layer protocol (dev.to aureus_c), durable execution (vadim.blog), cross-session awareness (Medium).

## Thread D: Three `/review` nits

**Status:** Non-blocking cleanup from the `/review` run.

**Source:** `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-review/post-check/20260721-121345/FINDINGS.md`

**Nit 1:** `qmd-patches.exec.log` will grow indefinitely. Add rotation or line cap (e.g., keep last 100 entries).
**Nit 2:** Hook prints PASS every session. Match `active-surface` convention: silent on PASS, print only FAIL/SKIP. *(Note: likely resolved by Group A's stderr fix — coordinate.)*
**Nit 3:** `_read_global_hooks()` synthetic labels may not match `~/.grok/disabled-hooks` schema. Latent, not regression-introduced.

## Dependencies

- **Thread A:** no dependencies — can start immediately
- **Thread B:** no dependencies — can start immediately
- **Thread C:** no dependencies — can start immediately (design is done)
- **Thread D:** Nit 2 may be resolved by Group A (hook diagnostics). Check before fixing.
- **Non-blocking to:** Groups A and B
