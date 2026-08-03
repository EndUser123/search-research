---
thread_id: a4f2e8c1-7b3d-4e9f-a6c2-1d8e5f3a7b09
parent_handoff_path: none
current_session_id: 019f9488-2a86-7bf1-ae6f-eeb341ec7095
current_terminal_id: console_83b3323a-a71b-4f55-8a5d-6a41f2ccb3d3
produced_at: 2026-07-25T07:30:00Z
status: CLOSED
handoff_type: investigation
accurate_as_of_head: 4b32781159cbf885a35c4a204ca02f95bcdeaa93
---

# Handoff: /tp rewrite — structured around 4D matrix, split protocol, integrate thinking skills

## Objective

Rewrite `~/.grok/skills/tp/SKILL.md` to be cleaner, shorter (~300 lines), and better structured. Rename the current version to `SKILL-old.md` as a working fallback. Split the subagent prompt template into `protocol.md`. Integrate confidence-based depth routing and cross-references to Claude-side thinking skills.

## Status

READY_TO_START — design is agreed, no implementation started.

## Background

Session 019f9488 (2026-07-24/25) was originally an epistemic-integrity correction that expanded into receipt-system implementation, red-team review, `/check` orchestrator design, `/tp` enhancement, and thinking-skills research. The `/tp` rewrite is the last unfinished item from the session.

The current `/tp` SKILL.md is ~1,060 lines and has accreted complexity across 5+ sessions. It works but is hard to read. The operator approved a rewrite structured around the 4-dimensional matrix (lens × horizon × target × posture) with the protocol split out.

## What was decided this session

### 1. `/tp` structure changes (all agreed, none implemented)

- **Rename current `SKILL.md` → `SKILL-old.md`** — keeps it as fallback
- **Write new `SKILL.md` (~300 lines)** structured around:
  - The 4D matrix (lens × horizon × target × posture) as the organizing principle
  - Semantic intent classification (replaces trigger phrases — already implemented in current version)
  - `/tp session` as the highest-value explicit variant (NOW/NEXT/LATER format, `/close` integration)
  - `/tp help` with the purpose-first table + 4D matrix diagram (already implemented)
  - Horizon auto-detection (already implemented — no explicit `horizon=now` needed)
  - `/close` invokes `/tp session` before final summary (already implemented in `/close` SKILL.md)
- **Move subagent prompt template to `protocol.md`** — SKILL.md becomes routing + decision logic, not a 200-line prompt template
- **Move failure modes table + circuit breaker to `reference/`** — reference material, not routing logic

### 2. Three new ideas from Claude-side thinking skills research (agreed, not yet implemented)

These were identified by mining the cc-skills-thinking plugin (17 skills: dream, execution-clarity, genius, learn, pace, probe, prospect, reason, reflect, response-atomicity, s, sequential-thinking, skeptic, tot, truth, ut, ux). The plugin is currently **disabled** in `config.toml [plugins] disabled`, so cross-references must be informational, not dependency-creating.

- **Confidence-based depth routing (from `/reason`):** `/tp` currently runs the same domains regardless of orchestrator confidence. Add a confidence dimension: high-confidence → lighter domains; uncertain → full depth including pre-mortem and steelman. This extends the existing horizon parameter.

- **Optional GCI round (from `/sequential-thinking`):** After synthesis, if verdict is REVISE or BLOCK, offer a second critique round on the revised position. The two-lens architecture already does one round; an explicit second round catches meta-problems.

- **Cross-references to thinking skills in `/tp help`:** Add a "Related thinking tools" section pointing to `/reason` (confidence-based), `/skeptic` (evidence validation), `/tot` (branch exploration). Informational only — no dependency on the disabled plugin.

### 3. Already-implemented changes (done in this session, verified)

These are **already shipped** in the current `/tp` SKILL.md and `/close` SKILL.md. The rewrite must preserve them:

- Semantic intent classification replacing trigger phrases (L122-132)
- `/tp session` named variant with NOW/NEXT/LATER/FILTER protocol (L210-260)
- `/tp help` with purpose-first table + 4D matrix (L828-900)
- `/close` invokes `/tp session` before summary (close SKILL.md L285+)
- Transcript path in context bundle (L370)
- Accurate tool-access description: subagent doesn't inherit conversation but CAN read transcript via read_file/grep (L448-457)
- `/local:red-team` converted from overlay to standalone skill (P:/.grok/skills/red-team/SKILL.md)
- `red-team` plugin disabled in config.toml

### 4. The 4-dimensional matrix (the organizing principle for the rewrite)

```
Question arrives
  │
  ├── DIMENSION 1: LENS (who thinks?)
  │     ├── two-lens (spawn subagent)     → default /tp
  │     ├── same-agent (inline)           → /tp quick, /tp check, /tp session
  │     └── hybrid (inline + workspace)   → opportunity scan
  │
  ├── DIMENSION 2: TIME HORIZON (when?)
  │     ├── now   → skip pre-mortem, steelman, second-order
  │     ├── next  → include second-order
  │     ├── later → full depth (all domains)
  │     └── all   → default (full depth)
  │
  ├── DIMENSION 3: TARGET (what?)
  │     ├── live question      → default
  │     ├── prior turn         → /tp check
  │     ├── session state      → /tp session
  │     ├── file/artifact      → /tp <path>
  │     └── workspace state    → opportunity scan (subagent scans)
  │
  └── DIMENSION 4: POSTURE (how?)
        ├── critique           → default /tp
        ├── diagnostic         → /tp check
        ├── opportunity review → /tp session
        └── dialogue           → /tp quick

  The semantic classifier picks the point in this space automatically.
  Explicit invocation (e.g. /tp session) overrides the classifier.
```

### 5. Wiki concepts created this session (context for the rewrite)

- `P:/.data/wiki/concepts/intent-based-routing-for-ai-agent-skills-2026.md` — validates LLM-based semantic classification for <15 categories
- `P:/.data/wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md` — orchestrator + specialized sub-agents pattern
- `P:/.data/wiki/concepts/best-practices-enforcement-mechanism-grok-build.md` — detect→block→prompt→terminate pattern

## Key decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Split protocol to separate file | SKILL.md becomes readable (~300 lines vs 1,060) | Keep monolithic (hard to read) |
| Keep `/tp-old` as fallback | Rewrite starts from zero uses; fallback preserves tested behavior | Delete old (risky — first use may surface issues) |
| Informational cross-refs to thinking skills, not dependencies | cc-skills-thinking is disabled; depending on it makes /tp fragile | Hard dependency (breaks if plugin stays disabled) |
| 4D matrix as organizing principle | Operator identified it as the correct mental model; cleaner than 13-variant list | Variant-list structure (current — accreted, hard to read) |
| Confidence-based depth as NEW dimension | From `/reason` routing table; adapts depth to uncertainty | Fixed-depth always (current — wasteful when confident) |

## Scope

### In scope

1. Rename `~/.grok/skills/tp/SKILL.md` → `SKILL-old.md`
2. Write new `~/.grok/skills/tp/SKILL.md` (~300 lines, 4D-matrix-structured)
3. Write `~/.grok/skills/tp/protocol.md` (subagent prompt template, Steps A-D, evidence tagging, disconfirmation format)
4. Move failure modes + circuit breaker to `~/.grok/skills/tp/reference/failure-modes.md`
5. Add confidence-based depth routing
6. Add "Related thinking tools" cross-reference section
7. Verify `/close` still invokes `/tp session` correctly after rename
8. Verify `/tp help` output is correct

### Out of scope

- Radical refactor to depend on cc-skills-thinking (plugin is disabled)
- GCI second-round critique (deferred — note in protocol.md as future enhancement)
- Multi-persona subagent dispatch (deferred — that's `/red-team`'s domain)
- Changes to `/close`, `/design`, or other skills that reference `/tp`

## Next steps

1. Read the current `~/.grok/skills/tp/SKILL.md` in full
2. Rename to `SKILL-old.md`
3. Write new `SKILL.md` structured per the 4D matrix
4. Split `protocol.md` from the subagent prompt template
5. Split `reference/failure-modes.md` from the failure modes table
6. Add confidence-based depth dimension
7. Add thinking-skills cross-reference
8. Verify `/tp help` works
9. Verify `/close` → `/tp session` still works
10. Smoke-test with one real `/tp` invocation

## Files for orientation

- `C:\Users\brsth\.grok\skills\tp\SKILL.md` — current (1,060 lines, to be renamed)
- `C:\Users\brsth\.grok\skills\tp\protocol.md` — existing deep reference (may need updating)
- `C:\Users\brsth\.grok\skills\close\SKILL.md` — references `/tp session` at Step 4
- `P:\packages\.claude-marketplace\plugins\cc-skills-thinking\references\reasoning-mode-routing-table.md` — thinking-skills routing table (for cross-reference)
- `P:\packages\.claude-marketplace\plugins\cc-skills-thinking\skills\` — 17 thinking skills (for descriptions)
- `~/.grok/AGENTS.md` — contains epistemic-integrity rules (5 rules added this session)

## Evidence

- Session 019f9488 chat_history (1,549 messages)
- 5 wiki concepts created
- `/www` research ledger: `P:/.data/www-ledger/intent-based-routing.md`
- `/check` orchestrator design doc: `P:/docs/designs/2026-07-25-check-orchestrator-design.md` (APPROVED, not yet implemented)
- 101 receipt-system tests passing at `~/.grok/hooks/scripts/`
- Receipt system built and tested but NOT REGISTERED in hook dispatch — shadow data is all zeros (35 sessions, 0 completion_attempts). See `multi-terminal-auto-commit-20260725/HANDOFF.md` for the full picture.

## Other outstanding streams

1. **`/check` orchestrator implementation** — design approved (1,096-line design doc), not yet implemented. 4 PRs planned.
2. **Receipt system hook registration** — hooks built and tested but NOT wired into dispatch JSON. Shadow evaluation produces empty summaries. Needs registration + 20-30 live sessions before promotion. F4 (fingerprint caching in /check) is blocked on this.
3. **Epistemic-policy deployment validation** — rules in `~/.grok/AGENTS.md` but not validated through fresh-session loading path (this session predates the edit).
4. **`~/.grok/` git commit** — hook scripts + AGENTS.md changes are uncommitted in the `dotgrok` repo. Run `git -C ~/.grok add -A && git commit` in a fresh session.
5. **`/aar` for this session** — deferred. Substantial friction: scope drift, Stop-hook blocks, GLM max_tokens, red-team bugs, misleading empty-scope metrics.

## Last user message (verbatim)

> If I compact now, will you be able to efficiently carry on this work?
