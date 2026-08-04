---
thread_id: 019fa8f8-quality-gates-20260804
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-04T15:00:00-06:00
status: open
handoff_type: implementation
accurate_as_of_head: 60d450b (P:\) / 383e3cf (~/.grok)
---

# Handoff: Declarative quality gates system

## 1. Objective

Build a declarative quality gates system where skills declare evidence
requirements in SKILL.md frontmatter and the existing Stop hook mechanically
enforces them — converting skill instructions from suggestions (6-66%
activation rate) into requirements (~100% compliance).

## 2. Status

OPEN — core system shipped, contamination bug found and fixed, scanner added.
Two consumers deployed (/ship). /close-check migration pending.

## 3. Producing context

This session (019fa8f8, spanning 2026-07-28 to 2026-08-04) built the full
quality gates system across multiple work phases:

**Phase 1: System design and implementation**
- Built `quality_gates_frontmatter.py` (~430 lines): frontmatter parser,
  evidence checker, transcript scanner for skill invocations, waiver handler
- Integrated into `quality_gate.py` (the existing ~1800 line Stop hook) at
  all 4 allow-paths: tracks `invoked_skills` in state file, scans transcript
  for `/skillname` patterns, checks gates after code-verification passes
- 28 tests (now 35 after session-scoping tests added)

**Phase 2: Cross-session contamination bug (found by /tp critique)**
- The initial `glob.glob()` matched ANY session's evidence file
- On a multi-agent host, Session B could pass quality gates using Session
  A's evidence
- Root cause: artifact directories use terminal IDs, not session IDs —
  path-based `{session_id}` substitution wouldn't work
- Fix: content-based session filtering — JSON evidence files contain a
  `session_id` field; when gate declares `session_field`, matched JSON files
  are parsed and filtered by content session_id
- Pattern borrowed from `close_accounting.py:619-622`
- 7 new tests covering the contamination scenario

**Phase 3: Mechanical scanner (per /tp critique recommendation)**
- New check 8g in `script_scan.py`: `_check_quality_gates_session_scoping()`
- Scans SKILL.md frontmatter for JSON evidence gates missing `session_field`
- Reports `CRAFT-UNSCOPED-JSON-EVIDENCE` with link to wiki concept
- Runs during `/skill-dev create` and `/skill-dev measure`
- Mechanical enforcement over behavioral reminder (workspace principle)

**Phase 4: Documentation and wiki concepts**
- Wiki: `multi-terminal-isolation-stale-data-immunity.md` (baseline requirements + case study)
- Wiki: `declarative-quality-gates-skills-declare-evidence.md` (design decision)
- AGENTS.md: one-line rule under "Multi-terminal isolation (evidence and shared state)"
- /tp v3.8: explicit lens count feature (`/tp critique N`)

## 4. Remaining work

### NEXT-1: Add quality_gates to /close-check when it becomes a skill

The operator is migrating `/close` → `/close-check` as a skill wrapper around
the workflow. When `/close-check` exists as a skill (with SKILL.md), add
`quality_gates` frontmatter declaring check-run.json + FINDINGS.md evidence.
The old `/close` already has session-scoped enforcement via
`close_accounting.py` + `close_enforcement_gate.py` — the quality gates
system would extend this to the Stop hook level.

**Important:** the /tp critique found that `/close` already has SUPERIOR
enforcement (session-scoped scanner + two-layer gate). Adding quality_gates
to the old `/close` would be net-negative (redundant + introduces unscooped
contamination). Only add to `/close-check` when it's the new active path.

### NEXT-2: Solve the markdown evidence limitation

FINDINGS.md (markdown) cannot use content-based session scoping because it
has no structured session binding. Currently passes through unscooped — any
session's FINDINGS.md satisfies the gate.

**Options:**
- Embed a session header in /review's output format (e.g., `<!-- session_id: <uuid> -->`)
- Parse the session ID from the directory path convention
- Accept the limitation and document it (current state)

### NEXT-3: Verify quality gates fire in production

The system has 35 passing tests but has not yet been observed firing in a
live session (the /ship that triggered this session's work was the motivating
failure — no live test of the new system has occurred). Next time `/ship` is
invoked in a session that hasn't run `/check`, the quality gate should block.

**Acceptance criteria:** observe the Stop hook blocking a `/ship` completion
claim when check-run.json is missing for the current session.

## 5. Key decisions

- **Consumer-side gates over producer-side:** /ship (consumer) declaring what
  upstream evidence it needs is stronger than /check (producer) declaring its
  own output. The same agent that ran /check can write garbage to satisfy a
  self-referential gate. Consumer gates can't be self-satisfied.
- **Content-based session scoping over path-based:** artifact directories use
  terminal IDs, not session IDs. Path-based `{session_id}` substitution
  produces zero matches. Content-based filtering (parse JSON, check session_id
  field) works and is proven by `close_accounting.py`.
- **Mechanical enforcement over behavioral reminder:** the scanner (check 8g)
  catches missing `session_field` at skill creation time with ~100% compliance.
  Per workspace principle: `[[mechanical-enforcement-over-behavioral-reminder]]`.
- **Advisory skills are intentional:** /tp, /explore, /brainstorming produce
  judgment, not checkable artifacts. Forcing artifacts would be process theater.
- **/tp lens count feature:** `/tp critique N` controls how many reasoning
  models fire in parallel (1=fastest, 3=default, 5=high-stakes).

## 6. Source files

- `~/.grok/hooks/scripts/quality_gates_frontmatter.py` (NEW — ~430 lines)
- `~/.grok/hooks/scripts/quality_gate.py` (MODIFIED — quality gate integration)
- `~/.grok/hooks/tests/test_quality_gates_frontmatter.py` (NEW — 35 tests)
- `~/.grok/skills/ship/SKILL.md` (MODIFIED v2.2→v2.3 — quality_gates + session_field)
- `~/.grok/skills/skill-dev/__lib/script_scan.py` (MODIFIED — check 8g scanner)
- `~/.grok/skills/tp/SKILL.md` (MODIFIED v3.7→v3.8 — lens count feature)
- `~/.grok/AGENTS.md` (MODIFIED — evidence isolation rule)
- `P:/.data/wiki/concepts/multi-terminal-isolation-stale-data-immunity.md` (NEW)
- `P:/.data/wiki/concepts/declarative-quality-gates-skills-declare-evidence.md` (NEW)
- Commits: 63201f6, 383e3cf, 2326dd3, cae2da2 (all on main)

## Suggested next invocation

```
/go Continue the quality gates workstream. Read this handoff. Key remaining work: (1) verify the quality gates fire in production by observing a Stop hook block when /check evidence is missing, (2) evaluate whether /close-check is ready to become a skill wrapper (the operator is migrating /close → /close-check), (3) if ready, add quality_gates frontmatter to /close-check. Start with verifying the system works end-to-end — invoke /ship in a session that hasn't run /check and confirm the gate blocks.
```
