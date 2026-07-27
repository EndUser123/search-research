---
thread_id: auto-verify-check-stop-hook-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T19:00:00Z
status: open
handoff_type: investigation
parent_handoff_path: P:/docs/handoffs/auto-test-quality-gate-20260727/HANDOFF.md
---

# Auto-verification hooks: when and how to fire /check, /grok-verify, /review after file writes or Stop

## Objective

Design and build hooks that automatically trigger verification skills (`/grok-verify`, `/check`, `/review`) at the right points in the session lifecycle — either after file writes (PostToolUse) or after a Stop event. The goal: the agent should not be able to claim "done" without verification, and verification should happen at the right time (not too early, not too late).

## The problem (one sentence)

The agent writes files and makes completion claims without running verification, and the existing hooks (quality_gate.py, mutation_receipt.py) enforce receipt presence but don't actually run the verification skills — they just check whether a verification command *was* run.

## What we know (verified)

- `[FACT]` The existing `quality_gate.py` Stop hook checks whether verification commands were run in the transcript — it does NOT run them itself. Receipt: `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py` lines 1015-1060 (reads payload, scans transcript for verification tokens, blocks if missing).
- `[FACT]` `/grok-verify` exists as a Grok-native skill at `~/.grok/skills/grok-verify/SKILL.md`. It's a self-check completion gate (restate criteria → prove code path → run tests → git hygiene → definition-of-done → VERIFY: PASS/FAIL). Receipt: read this session.
- `[FACT]` `/check` exists at `P:/.grok/skills/check/SKILL.md`. It's an independent verification skill (spawns fresh subagents, one per concern). Receipt: read this session.
- `[FACT]` `/review` exists at `~/.grok/skills/review/SKILL.md`. Fresh-eyes defect hunting. Receipt: in skill catalog.
- `[FACT]` `/check` already auto-escalates to `/review` when load-bearing triggers fire (hooks/plugins/schemas touched, verifier-flagged code issues, behavior claims not verified). Receipt: `P:/.grok/skills/check/SKILL.md` Step 6.2.
- `[FACT]` Grok Build hooks support: `command` and `http` types only. Events: PreToolUse, PostToolUse, PostToolUseFailure, Stop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification, SubagentStop. Receipt: `~/.grok/docs/user-guide/10-hooks.md`.
- `[FACT]` Stop hooks can provide feedback via: exit-2+stderr (block), `decision:block` JSON (block), `additionalContext` JSON (advisory). Receipt: `[[grok-build-stop-hook-patterns-and-feedback-mechanism]]`.

## Design considerations

### When to fire: PostToolUse vs Stop

| Trigger point | Pros | Cons | Best for |
|--------------|------|------|----------|
| **PostToolUse (after write/search_replace)** | Catches errors immediately; file is fresh in context; can block before the agent moves on | Too granular — fires on every file write, including doc-only edits; latency per write; the agent may not be done yet (mid-implementation) | `/grok-verify`-style edit-then-verify (did the bytes land? is the file valid?) |
| **Stop (after agent finishes response)** | Catches completion claims; the full turn's work is visible; the agent has declared intent; can fire /check with full context | Latency at turn boundary (if /check spawns subagents, that's 60-200s); may fire on turns where no code was written | `/check` (full session-grounded verification), `/review` (fresh-eyes) |
| **UserPromptSubmit (before next user turn)** | Last chance to block before the operator sees the response; catches "done" claims that weren't verified | Operator has already seen the response — blocking here is disruptive | Blocking enforcement (quality_gate.py already uses Stop for this) |

**Recommended split:**
- PostToolUse: lightweight `/grok-verify`-style check (edit landed, file valid, tests if cheap) — fast, per-write
- Stop: `/grok-verify` completion gate (did the agent do what it said?) — advisory via additionalContext, not blocking
- Stop with escalation: if completion claim detected + code modified + no verification → block (quality_gate.py already does this; extend to suggest `/check` or `/grok-verify`)

### What skills to auto-fire

The operator asked about `/check`, `/verify`, `/risks`, and "others?" Here's the full menu:

| Skill | When to auto-fire | How (hook mechanism) | Latency |
|-------|------------------|---------------------|---------|
| `/grok-verify` | After Stop with completion claim | additionalContext suggestion: "Run /grok-verify before claiming done" | 0ms (advisory) or 5-30s (if the hook runs it) |
| `/check` | After Stop with completion claim + code modified + load-bearing surface | additionalContext: "Run /check for independent verification" — or auto-fire if triggers are strong | 60-200s (subagent spawns) |
| `/review` | NOT auto-fire from a hook — /check already auto-escalates to /review when triggers fire | N/A (delegated to /check Step 6.2) | N/A |
| `/risks` | Not a skill we have. Closest: `/red-team` (for proposals) or `/wargame` (for plans). Neither should auto-fire. | N/A | N/A |
| `/why` | When a hook BLOCK fires and the agent needs to understand why | additionalContext: "blocked because X — consider /why to trace the root cause" | 0ms (advisory) |

### The auto-/check escalation question

**Should a Stop hook auto-fire `/check` when triggers are strong?**

Arguments FOR auto-firing:
- The operator has said multiple times: "I shouldn't have to remember to run verification"
- `/check` already auto-escalates to `/review` — chaining from Stop would create a full pipeline
- Quality_gate.py already blocks on missing verification — extending it to suggest `/check` is incremental

Arguments AGAINST auto-firing:
- `/check` spawns subagents (60-200s latency). Auto-firing at every Stop with code changes would make every turn 1-3 minutes slower.
- The operator may be mid-implementation (not claiming done yet) — auto-firing /check prematurely wastes effort.
- `/check` is session-grounded — it needs to know what the session's goals were, which requires the agent to state them.

**Recommended approach: advisory, not auto-fire.** The Stop hook emits additionalContext: "Code was modified this turn and no verification was run. Consider `/grok-verify` (self-check, fast) or `/check` (independent verification, ~60-200s) before claiming completion." The quality_gate.py block (existing) handles the case where the agent claims "done" without ANY verification — this just adds the suggestion of WHICH skill to run.

### Design: what to build

**Hook 1: `verify_nudge.py` (Stop hook, lightweight)**
- Fires at Stop when: code files were modified this turn (check transcript for search_replace/write to .py/.ps1/.js/.ts/etc.)
- Does NOT fire when: only docs (.md), config (.toml/.json), or wiki concepts were modified
- Output: additionalContext suggesting `/grok-verify` or `/check`
- Latency: <100ms (just scans the transcript for file extensions)

**Hook 2: extend `quality_gate.py` (Stop hook, existing)**
- Existing: blocks when completion claim + code modified + no verification command
- Extension: when blocking, the stderr message now suggests `/grok-verify` and `/check` as the skills to run
- The suggestion includes the specific files modified (from the transcript scan) so the operator knows what to verify

**Hook 3: `post_write_check.py` (PostToolUse hook, optional, opt-in)**
- Fires after search_replace/write to code files
- Runs a lightweight check: does the file parse? (Python: `python -c "import ast; ast.parse(open('<file>').read())"`)
- If parse fails: block with stderr (syntax error in written file)
- If parse succeeds: pass silently
- Latency: ~100-500ms per write
- Opt-in via config flag (default: off — the latency may not be worth it for every write)

## Dependencies

- **Requires:** nothing blocking. All skills exist.
- **Blocks:** nothing.
- **Related:** the auto-test-quality-gate handoff (extends quality_gate.py to auto-run ruff + pytest); this handoff is the complementary "suggest verification skills" layer.

## Cross-reference couplings

- `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py` — existing Stop hook to extend
- `C:/Users/brsth/.grok/skills/grok-verify/SKILL.md` — the self-check skill to suggest
- `P:/.grok/skills/check/SKILL.md` — the independent verification skill to suggest
- `P:/docs/handoffs/auto-test-quality-gate-20260727/HANDOFF.md` — sibling handoff (auto-test extension)
- `~/.grok/docs/user-guide/10-hooks.md` — hook event types and feedback mechanisms
- `[[grok-build-stop-hook-patterns-and-feedback-mechanism]]` — Stop hook feedback mechanisms

## Recommended fix path

1. **Build `verify_nudge.py`** (Stop hook) — scans transcript for code-file writes, emits additionalContext suggesting `/grok-verify` or `/check`. Lightweight (<100ms).
2. **Extend `quality_gate.py`** — when blocking, suggest `/grok-verify` and `/check` with specific file list.
3. **(Optional) Build `post_write_check.py`** (PostToolUse) — syntax-check written files. Opt-in; default off.
4. **Test** — run a session that writes code + claims "done" without verification. Confirm the nudge fires.
5. **Register** in `~/.grok/hooks/`.

## Next session protocol

1. Read this handoff + the auto-test-quality-gate handoff
2. Read `quality_gate.py` to understand the existing block mechanism
3. Read `10-hooks.md` for the Stop event payload format
4. Build `verify_nudge.py` (Step 1 above)
5. Extend `quality_gate.py` with skill suggestions (Step 2)
6. Test end-to-end
7. Consider: should the nudge be advisory (additionalContext) or blocking (decision:block with "run /grok-verify first")? Advisory is safer for rollout.

## Last user message (verbatim)

> /handoff consider a hook to use '/check' and '/verify' automatically after a file is written or after a stop which is probably the better time to use '/check', '/verify', '/risks'? others?

## Provenance

Written from session 019f9f4f after the operator's question about auto-verification hooks. The design separates PostToolUse (lightweight per-write checks) from Stop (session-level verification suggestions). The key insight: don't auto-fire `/check` (too slow, 60-200s), but DO suggest it via additionalContext when triggers fire. The existing quality_gate.py already handles the blocking case; this adds the suggestion layer.
