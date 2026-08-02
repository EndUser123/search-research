---
current_session_id: 019fba58-c6a0-7680-a52a-a08cd6f870d4
last_updated_by: 019fba58-c6a0-7680-a52a-a08cd6f870d4
last_updated_at: 2026-08-02T16:35:00.000000
parent_session: none
produced_at: 2026-08-02T16:35:00.000000
status: open
handoff_type: design
---

# HANDOFF: Handoff lifecycle visibility — progress tracking, claim TTL, changelog enforcement

## Status: OPEN — `/handoff claim` shipped, design needed for the rest

## Objective

Make handoff files self-describing their work lifecycle so any agent or operator can answer "is this being worked on right now, by whom, and how far along?" without grepping git logs or asking the operator.

## What's done

- **`/handoff claim <path>`** — shipped (`claim_handoff.py`). Sets `assigned_to`/`assigned_at`/`assigned_by` + changelog row. Conflict detection. Release via `--release`.

## What needs design (3 open questions)

### Q1: Progress tracking — how to model work phases?

The handoff has `work_status` (field 2: `OPEN` / `READY_FOR_REVIEW` / `BLOCKED` / `CLOSED` / `WONTFIX`) but nothing between OPEN and CLOSED that says "I'm actively implementing this."

**Options:**
- A) Add a `work_phase` field: `unclaimed → claimed → designing → implementing → verifying → done`
- B) Use the changelog as the progress log (each phase transition appends a row)
- C) Reuse `work_status` with intermediate states: `OPEN → IN_PROGRESS → READY_FOR_REVIEW → CLOSED`

**Considerations:**
- Option A adds a new field — more schema churn, more validator work
- Option B is zero-schema but relies on agents appending changelog rows (historically unreliable)
- Option C extends existing field — least new infrastructure but conflates "what phase" with "is it blocked"

### Q2: Claim TTL — how do stale claims expire?

A session that claims a handoff and crashes (or compacts and loses context) leaves a stale claim forever. The operator asked about this specifically.

**Options:**
- A) TTL based on `assigned_at` timestamp — claims older than N hours are considered stale
- B) Heartbeat file — the claiming session writes a timestamp periodically; absence means stale
- C) Git-based — check if the claiming session has committed since the claim; no commits = stale
- D) No TTL — rely on manual `--release` or operator override

**Considerations:**
- Option A is simplest but what's the right TTL? 1 hour? 4 hours? A session can legitimately work for hours without updating the handoff.
- Option B is the most accurate but requires a hook or periodic write — infrastructure cost
- Option C is clever but assumes the session commits to the same repo — cross-repo work breaks it
- Option D punts the problem — stale claims accumulate

### Q3: Changelog enforcement — warn or block?

The changelog is "mandatory" in the spec (field 16, "active as of 2026-08-01") but there's no blocking validator. Promoting from warn to error could break:
- The 216+ existing handoffs that may not have changelogs
- close-check's coverage scan (reads handoff files)
- list_handoffs.py (parses frontmatter)
- The close_accounting scanner

**Options:**
- A) Block only on write (not on read) — new handoffs must have changelogs, existing ones are grandfathered
- B) Migration script that adds empty changelogs to all existing handoffs, then enforce
- C) Warn always, block only when `/handoff close` is invoked
- D) Leave as warn — the claim command already writes changelog rows, which is the main use case

## Constraints

- Must build on existing scaffolding (assignment fields, changelog, work_status, list_handoffs.py)
- Must not break the 216+ existing handoffs
- Must work across multiple terminals and sessions
- Must be enforceable through hooks (the only reliable enforcement tier on this host)
- The `/handoff claim` command already exists — design builds on it

## File paths

- Claim script: `~/.grok/skills/handoff/__lib/claim_handoff.py` (shipped)
- List script: `~/.grok/skills/handoff/__lib/list_handoffs.py` (reads assignment fields)
- Validators: `~/.grok/skills/handoff/__lib/validators.py` (has `validate_assignment_fields`)
- Core fields spec: `~/.grok/skills/handoff/references/core-fields.md`
- Handoff SKILL.md: `~/.grok/skills/handoff/SKILL.md`

## Suggested next invocation

```
/design P:/docs/handoffs/handoff-lifecycle-visibility-design/HANDOFF.md
```
