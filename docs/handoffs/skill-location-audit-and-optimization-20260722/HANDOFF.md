---
thread_id: skill-location-audit-and-optimization-20260722
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T14:00:00Z
status: open
handoff_type: investigation
assigned_to: unassigned
accurate_as_of_head: 642c7ab
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: Skill location audit + optimization review

## Objective (one sentence)

Audit every skill across all 4 scope locations for (1) optimal placement per the `.agents/` open standard and the user-scope convention, and (2) optimization opportunities (size, structure, test coverage, cross-host portability) — then produce a disposition per skill: keep / move / consolidate / refactor / retire.

## Why this exists

Session 2026-07-22 established two conventions that not all skills follow:
1. **User-scope default** (`~/.grok/skills/`) for Grok skills (`/tp`, `/go`, `/handoff`, etc.) — already documented in the file-editing protocol and the skill-refactoring handoff
2. **`.agents/` open standard** for shared agent-callable tools and cross-host skills — established when dgemma_read.py was moved to `P:/.agents/scripts/models/`

The skill inventory shows **59 skills across 4 locations** with no consistent rationale for why each is where it is. Some are obvious (bundled = shipped with Grok; don't move). Others are ambiguous (why is `/check` at project scope when every other consolidated skill moved to user scope? Why are `avant-garde-ui` and `preflight` at `.agents/skills/` when they're Grok-loaded?).

Additionally, this session's `/tp` critiques and `/review` findings surfaced optimization opportunities across many skills (over-specification, missing tests, stale references, size bloat) that haven't been systematically addressed.

## Current inventory (verified 2026-07-22)

### User scope (`~/.grok/skills/`) — 32 skills
Grok skills and personalizations. This is the default for new skills.

| Skill | Size | Notes |
|-------|------|-------|
| aar | 39KB | Has `__lib/` (19 files), `references/` (6). Dense SKILL.md. |
| agy | 24KB | Cross-model CLI conductor. |
| check-work | 13KB | DEPRECATED per catalog. Candidate for retirement. |
| close | 12KB | New this session. Has scanner + tests. |
| code-review | 13KB | May duplicate `/review`. |
| codex | 33KB | Cross-model CLI conductor. |
| create-skill | 3KB | Scaffolding. |
| debrief | 13KB | 5-lens retrospective. |
| design | 57KB | **Largest skill.** Top refactoring candidate per skill-refactoring handoff. |
| go | 37KB | Primary orchestrator. High consumption. |
| grok-discovery | 4KB | Sub-skill of /go. |
| grok-go | 0.5KB | Alias for /go. |
| grok-parallel | 5KB | Sub-skill of /go. |
| grok-route | 4KB | Sub-skill of /go. |
| grok-safe-git | 4KB | Sub-skill of /go. |
| grok-sdlc | 0.5KB | Alias for /go. |
| grok-verify | 4KB | Sub-skill of /go. |
| handoff | 22KB | Has `__lib/` (6 files), `references/`. |
| help | 3KB | Documentation help. |
| imagine | 10KB | Image generation guidance. |
| marketplace-bridge | 4KB | Skill marketplace discovery. |
| mmx | 35KB | Cross-model CLI conductor. |
| plan | 15KB | Plan mode rules. |
| refactor | 21KB | Structure-focused refactoring. |
| review | 41KB | Code/package review. Has tests. |
| search-fleet | 10KB | Fleet search. |
| tasks | 4KB | Claude Code task store bridge. |
| tp | 32KB | Critical-friend critique. Has `protocol.md` (43KB) + `replay-cases.md` (47KB). |
| wargame | 6KB | Content discipline for hard-to-reverse plans. |
| web | 6KB | Web research routing. |
| wiki | 5KB | Wiki operations. |
| www | 24KB | Wiki-web-wiki compound research. |

### Project scope (`P:/.grok/skills/`) — 1 skill
| Skill | Size | Notes |
|-------|------|-------|
| check | 27KB | **Should this have moved to user scope with aar/handoff/refactor/review?** The consolidation session moved those but left check here. |

### Bundled (`~/.grok/bundled/skills/`) — 21 skills
Shipped with Grok. **Do not move or edit** (overwritten on reinstall).

### `.agents/skills/` (`P:/.agents/skills/`) — 5 skills
| Skill | Size | Notes |
|-------|------|-------|
| avant-garde-ui | 4KB | UI design skill. Cross-host? |
| contract-status | 1KB | Contract system health dashboard. |
| notebooklm | 27KB | NotebookLM API skill. Has `__lib/` + `src/` + tests. |
| preflight | 6KB | Source-authority discovery. Has `__lib/`. |
| test-skill-integration | 0KB | Test scaffold. |

## What needs to be done

### Task 1: Location audit (per-skill disposition)

For each of the 38 non-bundled skills, determine the optimal location:

| Question | Answer determines |
|----------|-----------------|
| Is it a Grok-specific skill (`/tp`, `/go`, `/handoff`)? | User scope (`~/.grok/skills/`) |
| Is it cross-host (usable by Claude, Codex, PI, opencode)? | `.agents/skills/` (the open standard) |
| Is it project-specific (depends on `P:/packages/` code paths)? | Project scope (`P:/.grok/skills/`) |
| Is it deprecated or superseded? | Retire (delete or mark `status: superseded`) |
| Is it a duplicate of another skill? | Consolidate |

**Specific questions to resolve:**
- `/check` at project scope — deliberate or missed by the consolidation session?
- `avant-garde-ui`, `contract-status` at `.agents/skills/` — are these cross-host, or accidentally placed?
- `check-work` — confirmed deprecated; retire?
- `code-review` at user scope vs `/review` — duplicate or distinct?
- `grok-go`, `grok-sdlc` — 0.5KB aliases. Keep as convenience or fold into /go?
- `search-fleet` — what does this do? Still relevant?

### Task 2: Optimization review (per-skill improvement opportunities)

For each skill, assess:

| Dimension | What to check |
|-----------|--------------|
| **Size** | >30KB SKILL.md → offload to `references/` or `protocol.md` (per skill-refactoring handoff) |
| **Test coverage** | Has `__lib/*.py`? → has tests? → coverage gate? |
| **Cross-host portability** | Uses `host: grok` frontmatter? → valid for Claude/Codex? |
| **Stale references** | References paths that moved (e.g., old dgemma path)? |
| **Convention compliance** | Follows the instrument-vs-reference pattern? Terminal-scoped state? Multi-terminal isolation? |
| **Model pool integration** | If it spawns subagents, does it use the pool (per /tp Step 2 rewrite)? |

**Known optimization candidates (from this session's work):**
- `design` (57KB) — #1 refactoring candidate
- `review` (41KB), `aar` (39KB) — dense SKILL.md, could offload
- `go` (37KB) — most-consumed skill; cold-start cost matters
- `tp` (32KB + 90KB references) — already offloaded; SKILL.md could be slimmer
- `mmx` (35KB), `codex` (33KB) — CLI conductors; may have shared patterns to extract

### Task 3: Produce the disposition table

Output: a table with one row per skill:

| Skill | Current location | Recommended location | Action | Rationale | Priority |
|-------|-----------------|---------------------|--------|-----------|----------|
| /check | project | user | **Move** | Consistent with consolidated skills | High |
| /design | user | user (refactor) | **Refactor** | 57KB → offload to references/ | High |
| /check-work | user | — | **Retire** | Deprecated per catalog | Low |
| ... | ... | ... | ... | ... | ... |

## Acceptance criteria

1. Every non-bundled skill (38 total) has a disposition row
2. Each disposition cites a reason (convention, size, duplication, deprecation)
3. Location moves are **one at a time with verification** (per skill-refactoring handoff rule — no bulk moves)
4. Optimization recommendations connect to existing handoffs (skill-refactoring-program-20260722, test-code-drift, etc.)
5. The disposition table is persisted to the wiki or a durable doc, not just in the handoff

## What NOT to do

- **Do NOT bulk-move skills.** Each move is a separate work item with path-reference updates + verification.
- **Do NOT retire skills without checking for consumers.** grep for the skill name across the workspace before deleting.
- **Do NOT edit bundled skills.** They're overwritten on reinstall.
- **Do NOT confuse "location optimization" with "skill improvement."** Location is about where the file lives; improvement is about what the skill does. Both are in scope but they're separate dispositions.

## Multi-terminal + stale-data notes

- Location moves use `git mv` where the path is tracked; `mv` for user-scope (not tracked by P:/ repo)
- All path references must be updated atomically with the move (per file-editing protocol)
- The disposition table itself lives in `P:/docs/` (shared, durable)
- Concurrent sessions may be actively editing skills — verify no concurrent writes before moving

## Resumption protocol

1. Read this handoff (the inventory + the 3 tasks)
2. Read the skill-refactoring handoff: `P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md`
3. Read the `.agents/` standard decision: `P:/docs/handoffs/session-2026-07-22-shipped-work/HANDOFF.md` § "`.agents/` open standard adoption"
4. Start with Task 1 (location audit) — it's the prerequisite for Task 2 (you need to know where skills are before optimizing them)
5. For each skill, produce the disposition row
6. Work through the moves one at a time (highest priority first)

## Related artifacts

- Skill-refactoring handoff: `P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md` (11 skills >20KB to refactor)
- Shipped-work consolidation: `P:/docs/handoffs/session-2026-07-22-shipped-work/HANDOFF.md` (includes `.agents/` decision)
- Test-code drift handoff: `P:/docs/handoffs/test-code-drift-multi-agent-20260722/HANDOFF.md` (coverage gate pattern)
- Wiki: `P:/.data/wiki/concepts/session-close-out-skill-design.md` (instrument-vs-reference pattern)
- Wiki: `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` (which models support tool use — relevant for skills that spawn subagents)

## Falsifier

This audit is wrong if:
- The current locations are actually optimal (every skill is where it should be) → the audit produces zero moves; document why each location is correct
- The `.agents/` standard doesn't actually apply to skills (only to scripts/tools) → narrow the audit to location consistency, not standard adoption
- The optimization review is too broad to be actionable → narrow to the top 5 highest-ROI improvements

If any pattern appears within 3 months, iterate.
