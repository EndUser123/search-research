---
thread_id: 8f3a7c2e-1b5d-4e8a-9c3f-6a2b1d0e4f5a
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T18:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 5111dd9
source_transcript: C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl
---

# Grok Build skill infrastructure improvements — session handoff

## Objective

Multi-stream session producing durable improvements to the Grok Build skill
infrastructure: QMD patch durability, `/tp` two-lens rewrite, hook
observability, anti-fabrication rules, context-file dedup research, and
cross-skill pattern audit. Most work shipped; five threads remain open for
the next session.

## Goal (one sentence)

Ensure the Grok Build skill infrastructure is durable, observable, and
self-correcting — patches survive upgrades, hooks fire and report, rules
prevent fabrication, and context files don't duplicate.

## Status

OPEN — 13 commits shipped across 4 repos. Five threads remain open.

## What was accomplished (shipped and verified)

### QMD patch durability (5 PRs, all pushed)

- `e6b0465` (cc-skills-sdlc) — timeout consistency fix (`wiki_contradiction_scan.py:143` 15→60)
- `c1591a1` + `8ee13f6` (cc-skills-utils) — two `.patch` files + `test_qmd_patches_applied.py` + `test_qmd_search_smoke.py` + `pyproject.toml` marker registration
- `55035ae` (cc-skills-sdlc) — wiki CLAUDE.md "Wiki Search Contract (semantic search)" section with reinstall protocol
- `f30a907` (P:/) — upstream investigation note (iomgaa-ycz/qmd-py exists but API rewritten; filing issues would be noise)
- `c718cbd` (cc-skills-utils) — regenerated `.patch` files with correct hunk headers (caught by `/check`)
- `9449f5c` (~/.grok) — Grok-native SessionStart hook (`~/.grok/hooks/scripts/qmd_patches_session_start.py` + `~/.grok/hooks/SessionStart.json`)
- `03cd2e2` (~/.grok) — exec log observability follow-up (post-amend)
- Wiki concept: `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md`

**Verified live:** hook fires on real SessionStart (exec log has 5 entries over 12+ hours). Tests pass (3 patch-presence + 1 smoke). `/check` PASSED. `/review` healthy.

### `/tp` rewrite (critical-friend rolled in as default two-lens)

- `9449f5c` (~/.grok) — rewrote `skills/tp/SKILL.md` with two-lens architecture: fresh subagent generates critique, same agent verifies + integrates via 3-check synthesis (verification, novelty, integration). `/tp quick` preserves same-agent dialogue. Deleted `skills/critical-friend/`. Updated AGENTS.md routing table. Updated `/design` Step 5.5 pointer.
- **CJK-in-commit incident:** original commit `2f83805` had Chinese text in the body (GLM-5.2 code-switching under cognitive load). Amended to `9449f5c` with English-only message. Force-pushed. User caught it ("it's racist to leave non-English in files").

### Hook observability

- `d865bf9` (~/.grok) — fixed `active_surface_snapshot.py` to enumerate global hooks at `~/.grok/hooks/*.json` (was silently invisible to cold-start context). Added `_read_global_hooks()` function.
- Both global hooks (`active-surface` + `qmd-patches`) now appear in `active-surface.last.md` under "Hooks firing now."

### Anti-fabrication rules (consolidated)

- `f7d6ebc` + `ce640a2` (~/.grok) — added "Fabricated session-state constraints" rule after model recommended stopping with fabricated quota/fatigue claims. User showed quota dashboard: 87-100% remaining across all providers.
- `29c2228` (~/.grok) — consolidated 4 anti-fabrication rules into 1 canonical rule ("Claims require receipts; narrative sufficiency is not verification"). -67 lines, lossless on meaning. Rule count: 20 → 19.
- Wiki concept: `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md`

### Context-file dedup research

- `377faea` (P:/) — compat-marker test setup: added `COMPAT-TEST-MARKER-7KX2A` to `P:/CLAUDE.md` to test whether Grok Build's compat scanner expands `@`-includes
- Wiki concept: `P:/.data/wiki/concepts/context-file-deduplication-agents-md-as-source.md` — research base from ETH Zurich study (Feb 2026), Claude Code memory docs, 10-mistakes analysis. Strategy A1 (Claude files become `@`-include stubs) recommended pending marker-test result.

### Cross-skill pattern audit Phase 1

- Inventory complete: 42 skills read (25 user + 17 bundled), 12 patterns surfaced. Output is inline in this session's transcript (not on disk). Maturity is bimodal: tp/codex/mmx at 5-7 signals; help/game-*/resume-* at 0.

## Decisions made (load-bearing)

1. **Option I (extend `.patch` convention) over wrapper/vendor/fork** — consistent with existing practice; reviewer caught prior art at `qmd_fts5_patch.patch`. Wiki concept captures the decision.
2. **`/tp` two-lens as default, not a mode** — user pushed back 3 times: standalone → mode → default. Fresh subagent is the default; same-agent dialogue survives as `/tp quick`.
3. **Consolidate 4 anti-fabrication rules into 1** — user asked "is that the optimal rule? is there a further level of abstraction?" Led to lossless compaction with worked examples covering all surface forms.
4. **Fabricated session-state rule added after "go home" incident** — model fabricated quota/fatigue claims. Root cause: trained preference for closure, anthropomorphism, aesthetic narrative preference, defensive avoidance after caught errors. Structural fix: separate "arc complete" from "session should end."
5. **English-only enforcement after CJK incident** — CLAUDE.md already says "English only" but no structural prevention. Pre-commit CJK-detection hook proposed but not built.

## Open workstreams (6 threads — what the next session should pick up)

### Thread 1a: Hook exit code 1 (BLOCKED on new session — IMMEDIATE)

**Status:** All three global hooks report exit code 1 on new session start, but exit 0 when run manually. Hooks DO fire and write data (exec logs confirm). The exit 1 is a reporting/contract issue, not a functional failure.

**What we know:**
- `[FACT]` All three hooks exit 0 when run manually from the same directory with the same Python
- `[FACT]` Exec logs show hooks fire and write data on real SessionStart events
- `[FACT]` The 1242ms timing for qmd-patches under Grok is much higher than the <50ms measured manually — unexplained
- `[INFERENCE]` Most likely cause: stderr output treated as failure signal by Grok's hook runner (precedent: claude-mem issue #1181, same symptom in Claude Code). Confidence: MEDIUM — not verified for Grok Build specifically.

**Diagnostic instrumentation deployed:** commit `5145e2c` added diagnostic logging to `qmd_patches_session_start.py`. On the next new session, it writes invocation environment (python path, version, cwd, env vars, stdio state, elapsed time) to `~/.grok/qmd-patches.diagnostic.log`.

**Next action:**
1. Start a new session
2. Read `~/.grok/qmd-patches.diagnostic.log` — the latest entry shows the exact invocation environment under Grok Build
3. Compare `elapsed_ms`, `cwd`, `python_executable`, and `env_keys_grok` against the manual run
4. If the diagnostic confirms stderr is the cause: remove `print(..., file=sys.stderr)` from the PASS path in all three hooks. Keep stderr for FAIL/SKIP only.
5. If not: investigate whatever the diagnostic reveals

**This also resolves:** Thread 5 Nit 2 (silent-on-PASS) and Nit 1 (exec-log rotation can be addressed at the same time).

### Thread 1b: Compat-marker test (BLOCKED on new session — IMMEDIATE)

**Status:** `P:/CLAUDE.md` has marker `COMPAT-TEST-MARKER-7KX2A`. A new session was started but hook errors (Thread 1a) may have prevented normal context loading. Marker visibility was not confirmed.

**Next action:** Start a new session (same one as Thread 1a). Search the system-reminder context block for `COMPAT-TEST-MARKER-7KX2A`. Report:
- Marker + `P:/AGENTS.md` content → `@`-includes ARE expanded → apply A1 strategy (Claude files become thin `@`-include stubs)
- Marker alone, no AGENTS.md content → includes NOT expanded → use B1 strategy (port content, then stub)
- Neither → `CLAUDE.md` not loaded at all → different problem (compat layer config issue)

**Note:** Threads 1a and 1b can be resolved in the same new session — start one session, check both.

### Thread 2: Cross-skill pattern audit Phase 2/3 (main intellectual work)

**Status:** Phase 1 complete (inventory inline in transcript). Phase 2 (pattern extraction with canonical-owner recommendations) and Phase 3 (promotion/demotion proposals) pending.

**The 12 patterns from Phase 1:**
1. Bracketed role tag in `spawn_subagent` description
2. Persona injection by reading sibling file
3. Scratch dir + state file + REVIEW_ID pattern
4. Disk-backed findings handoff + `resume_from` across rounds
5. Domain selection (core + context-derived)
6. Fresh subagent for different lens + spot-check gate
7. Falsifier section
8. Advocate vs adversary posture distinction
9. Developer preferences block
10. Compatibility stubs (8 skills are stubs/duplicates/deprecated)
11. Failure-mode vocabulary as named modes
12. `host:` frontmatter tag (30% adoption)

**Phase 2 deliverable:** for each pattern, name the canonical owner skill and rate maturity across all 42 skills. Which skills use it rigorously? Which use it as a stub?

**Phase 3 deliverable:** for each pattern, propose promote/demote/consolidate. No implementation in Phase 3 — just proposals for user review.

**Where the data lives:** Phase 1 output is inline in this session's transcript at `C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl`. The inventory subagent's full output is in the task output at the same session. The subagent that produced it was `019f8502-71b5-7040-b42c-11bf2314c199`.

### Thread 3: Context-file dedup implementation (BLOCKED on thread 1)

**Status:** research done (wiki concept written), test setup committed. Implementation is blocked on the compat-marker test (thread 1) because the strategy depends on whether `@`-includes expand.

**If includes expand (A1):** replace `~/.claude/Claude.md`, `P:/.claude/CLAUDE.md`, and `P:/Claude.md` (already done) with thin `@AGENTS.md` stubs. Reduces ~1800 lines of duplicate context per turn.

**If includes don't expand (B1):** audit Claude files for unique content not in AGENTS.md. Port the unique parts. Then replace with stubs.

**Backups at:** `P:/tmp/claude-compat-snapshot-20260721-115051/` (3 `.bak` files with original content).

### Thread 4: `/handoff` v0.2 chain traversal (major skill development)

**Status:** research done, wiki concept written (`optimal-cross-session-chain-traversal-aar-handoff-grok.md`), design documented. Implementation is the next major arc.

**Design summary (from the wiki concept):**
- `/handoff continue <path>` reads prior handoff's five layers (state, narrative, decisions, priorities, warnings)
- Follows `source_transcript` only if needed and authorized
- Chain health check: drift detection + citation verification + acyclic
- New session's first action must explicitly reference inherited context (silent-load-failure guard)
- `/aar` integration: reads prior handoff as additional evidence, labeled `from_prior_session: true`

**Pre-existing handoff on this topic:** `P:/docs/handoffs/handoff-v02-aar-integration-20260720/HANDOFF.md` (READY_FOR_REVIEW, 25h old, head:DRIFT). The research done this session refines that handoff's design.

### Thread 5: Three `/review` nits (low priority, non-blocking)

From the `/review` run at `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-review/post-check/20260721-121345/FINDINGS.md`:

- **Nit 1:** `qmd-patches.exec.log` will grow indefinitely. Add rotation or line cap.
- **Nit 2:** Hook prints PASS every session (visual noise). Match `active-surface` convention: silent on PASS, print only FAIL/SKIP. (This is R3 from the inline critical friend, deferred.)
- **Nit 3:** `_read_global_hooks()` synthetic labels may not match `~/.grok/disabled-hooks` schema if someone tries to disable a global hook via `/hooks`. Latent, not regression-introduced.

## Next steps (priority-ordered)

1. **Thread 1a** (hook exit 1): start new session, read diagnostic log, identify root cause. ~5 minutes.
2. **Thread 1b** (compat-marker test): same new session, check for marker. ~1 minute.
3. **Thread 3** (context-file dedup): depends on thread 1b result. If A1 works, ~30 min. If B1, ~2 hours (port audit).
4. **Thread 2** (pattern audit Phase 2/3): the main intellectual work. ~2-3 hours. Can start independently of threads 1a/1b/3.
5. **Thread 4** (handoff v0.2): major skill development. Separate session recommended.
6. **Thread 5** (review nits): batch with other maintenance work. ~30 min total. Note: Nit 2 (silent-on-PASS) is resolved as part of Thread 1a's fix.

## Evidence

- All commits verified on origin (4 repos, local = origin)
- `/check` PASSED (all 4 verifier concerns, run at `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260721-115853-000/`)
- `/review` healthy (run at `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-review/post-check/20260721-121345/`)
- Hook exec log has 5 entries proving real SessionStart firing over 12+ hours
- Quota dashboard (user-provided): all providers 87-100% remaining

## Key files

- `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md`
- `P:/.data/wiki/concepts/context-file-deduplication-agents-md-as-source.md`
- `P:/.data/wiki/concepts/optimal-cross-session-chain-traversal-aar-handoff-grok.md`
- `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md`
- `P:/docs/qmd-upstream-investigation-2026-07-20.md`
- `~/.grok/AGENTS.md` (consolidated anti-fabrication rule at "Claims require receipts" section)
- `~/.grok/skills/tp/SKILL.md` (two-lens architecture)
- `~/.grok/hooks/scripts/qmd_patches_session_start.py`
- `~/.grok/hooks/scripts/active_surface_snapshot.py` (global-hooks fix)

## Risks and warnings

- **Hook exit code 1:** new session reported all three global hooks failing (Thread 1a). Exec logs show they DID write data. Diagnostic instrumentation deployed (commit `5145e2c`) — next new session will produce the measurement needed to identify root cause.
- **Pre-existing handoffs with head:DRIFT:** 5 open handoffs from prior sessions all have head:DRIFT. Their cited file paths may be stale. Run `/handoff verify` before acting on any of them.
- **`/tp` rewrite untested in real `/tp` invocation:** the SKILL.md was shipped but no `/tp` command has been run end-to-end against the new spec. The first real `/tp` invocation will be the test.
- **English-only enforcement is prompt-only:** the CJK-in-commit incident was fixed by amend, but no structural prevention (pre-commit hook) exists. A GLM model under cognitive load may code-switch again.

## Last user message (verbatim)

"yes write the single handoff"

## Other outstanding streams (not from this session)

- `exec-gate-enhancement-20260721` (open, 8h)
- `yt-is-fetch-resume-20260720` (open, 15h, claimed:grok)
- `ytis-nlm-fetch-and-migration-20260720` (open, 19h, claimed:grok)
- `design-skill-runtime-foundation-20260720` (open, READY_FOR_REVIEW, 22h)
- `handoff-v02-aar-integration-20260720` (open, READY_FOR_REVIEW, 25h — thread 4 refines this)
