# Core fields — mandatory for every handoff

Every handoff has a **chain header** (YAML frontmatter) and **16 mandatory fields** (markdown body). v0.1 uses Investigation type only; v0.2 will add optional blocks per type.

## Chain header (YAML frontmatter)

```yaml
---
thread_id: <uuid>                       # stable across the work thread
parent_handoff_path: <path|none>        # prior handoff in this thread, if any
current_session_id: <uuid>              # session writing this handoff
current_terminal_id: <id>               # terminal writing this handoff
produced_at: <iso8601>
status: open                            # v0.1: always "open" on new writes
handoff_type: investigation             # v0.1 default; v0.2 adds implementation|diagnostic|architectural|retrospective
accurate_as_of_head: <git-sha>          # git HEAD at production time; sourced from summary.json.head_commit
# Optional assignment block (v0.1.1) — uncomment when claiming for fleet coordination
# assigned_to: <host|none>              # who has claimed this work (e.g., "grok", "claude")
# assigned_at: <iso8601>                # when the claim was made
# assigned_by: <session-id>             # session that made the claim
---
```

**Field semantics:**

- `thread_id` — UUID generated when the thread starts. `/handoff new` generates a fresh one. If the user explicitly names a prior handoff to continue from, inherit its `thread_id`. Propagated unchanged through every handoff in the chain (v0.2).
- `parent_handoff_path` — absolute path to the prior handoff. `none` for a fresh start.
- `current_session_id` / `current_terminal_id` — who is writing this handoff.
- `produced_at` — ISO 8601 timestamp. Used for staleness detection (>24h requires re-verification).
- `status` — `open` on new writes in v0.1. v0.2 adds `closed`, `superseded`.
- `handoff_type` — `investigation` in v0.1. The type selects optional blocks in v0.2; for v0.1 it's metadata only.
- `accurate_as_of_head` — git HEAD sha at production time. Sourced from `summary.json.head_commit` in the producing session's directory. **Reader obligation:** if `git rev-parse HEAD` differs from this value, re-verify cited paths before acting — the tree has moved since the handoff was written. This is the cheap stale-data immunity anchor; the data is already in session metadata, the writer just captures it.
- `assigned_to` / `assigned_at` / `assigned_by` — **optional** (v0.1.1). When a handoff is claimed for fleet coordination (so other hosts/agents don't duplicate the work), set all three. `assigned_to` is the host or role identifier (e.g., `grok`, `claude`); `assigned_at` is an ISO 8601 timestamp; `assigned_by` is the session-id that made the claim. If the producing session is ending (the common case), `assigned_by` records provenance — the claim belongs to any future session on that host. The `/handoff list` command surfaces these fields so fleet operators can see what's claimed at a glance. If all three are absent, the handoff is unclaimed (anyone may take it).

The header is immutable per file. Updates (v0.2) append a revision block at the bottom; they do not mutate the header except for `status`.

## The 16 mandatory fields

### 1. Objective (one sentence)
What this thread of work is trying to accomplish. If you cannot state it in one sentence, the work is not clear enough to hand off.

**Scope bounds (mandatory when the work is a subset).** If the work touches a subset of a larger set (e.g., "the latest 7,000 of 51,337 pending videos"), state **both numbers** and label which is the work scope and which is the ambient total. A reader who sees only one number will misestimate the work, mis-calibrate acceptance criteria, and declare success at the wrong threshold. Add a `**Scope bounds:**` line immediately after the objective sentence whenever the work scope differs from the total population.

Example:
```markdown
## Objective

Migrate the transcript fetch path to notebooklm-py.

**Scope bounds:** Work scope is ~7,000 latest videos. Total pending backlog is 51,337; the remaining ~44,000 are out of scope for this handoff (deferred to a follow-on fetch).
```

The scope-bounds validator (`validate_scope_bounds`) will warn if a Verified Facts number is >3× the Objective's largest number and no scope-labeling keywords are present.

### 2. Status
Explicit: `OPEN` / `READY_FOR_REVIEW` / `BLOCKED` / `CLOSED` / `WONTFIX`. Never inferred from context. This is the *work* status, separate from the chain header's `status` (which is the *handoff file* status).

### 3. Producing context
Date, producing session-id (matches `current_session_id`), producing terminal-id, host/version if material. Provenance for staleness detection.

### 4. Read-first list (ordered, with reasons)
The ordered file list a fresh session should read before acting. Each entry has a one-line "why this order" explanation.

Example:
```markdown
1. `P:\packages\...\SKILL.md` — intended behavior
2. `P:\packages\...\routing.py` — per-domain ranking order
3. `P:\packages\...\bf_agent.py` — runtime source of truth
4. `P:\packages\...\tests\test_bf_agent.py` — invariants that must not break
```

### 5. Verified facts (with source paths)
`[FACT]` claims with file:line or event-id citations. Not narrative.

```markdown
- [FACT] `cc-council` engine returns empty outcome (`council.py:71-79`, "Placeholder implementation")
- [FACT] `test.db` has 0 rows in every table (verified via sqlite3 query, 2026-07-20)
```

### 6. Current state
What's already in place vs. what's not. Distinguishes "work done" from "work remaining."

### 7. Task packets (one per bounded unit of residual work)
Each packet has:
- `id` — stable identifier (e.g., `AC-CONTAIN-01`)
- `goal` — one concrete outcome
- `in scope` — what this task touches
- `out of scope` — what it does not touch
- `files / anchors` — exact paths and code regions
- `acceptance` — how to prove it succeeded
- `falsifier` — what would prove it failed. **Must catch the disaster case, not just the catastrophic case.** "Produces 0 output" only catches total failure; a 30% success rate passes that bar but is still a disaster for a production run. For bulk/batch/scale operations, the falsifier must specify a **success-rate threshold** (e.g., "success rate < 90%", "fewer than N of M items land"). The `validate_falsifier_strength` validator will warn when a bulk-operation task has a falsifier that only mentions zero/crash without a rate threshold.
- `verification level required` — `STATIC_INSPECTION` / `UNIT_TEST` / `LIVE_BEHAVIOR`
- `no_live_run_reason` (if deferred) — why a live run was not done
- `estimate` (optional, for bulk/run operations) — expected duration **with the math shown** (per-unit rate × count ÷ parallelism). "Several hours" without math is a story; `5 videos = 42s → 8.4s/video → 7000 @ 1 worker ≈ 16.3h` is an estimate a reader can sanity-check and scale.
- `auth-expiry mitigation` / `session-boundary risk` (optional, for tasks whose runtime exceeds session/auth lifespan) — what happens if the run outlives the session. State the mitigation: chunking, keepalive, re-bootstrap tolerance, or explicit "not handled, risk accepted."

### 8. Open decisions (explicit, framed as questions)
What's blocked on user input. Each decision has:
- The question
- The options with trade-offs
- The selection criterion
- Which option currently leads, and why
- What evidence would change the lead

### 9. Hard constraints
Non-negotiable invariants. Named explicitly so they survive into the next session.

### 10. Cross-reference couplings (mandatory; "none identified" allowed)

The dependency map: what this work depends on, and what depends on it. Surfaces dangling references and coupling that would otherwise be discovered only after acting. Promoted to mandatory in v0.1.1 after corpus review showed the single best handoff in the workspace (design-skill-runtime-foundation-20260720) was the only one with this section, and it was the load-bearing structure that made that handoff skimmable.

Format: a bulleted list of arrows. Each entry names a dependency direction and what dangles if either side changes.

```markdown
## Cross-reference couplings

- `P:/AGENTS.md "Session start" rule` → reads M1 snapshot. If M1 is reverted, this rule dangles.
- `~/.grok/AGENTS.md routing table` → names /check, /review. Both exist; no dangling reference.
- This handoff's `accurate_as_of_head` → `47b2322`. If HEAD moves, re-verify cited paths.
```

If the work is genuinely standalone, write `None identified.` — the explicit assertion is itself evidence.

### 11. Other outstanding streams (if any)
**v0.1 multi-stream rule.** If other work streams are obvious from current context and any are open, name them here with a one-line summary each. Do **not** write handoffs for them. The user will ask specifically when they want one documented.

```markdown
## Other outstanding streams (not handed off)

- **<stream name>** — one-line summary. Open / closed.
- **<stream name>** — one-line summary. Open / closed.
```

If no other streams are obvious, omit this section. Do not invent streams to fill the section.

### 12. Explicit non-goals
What NOT to do. Equally important as task packets. Prevents scope creep and well-meaning overreach.

### 13. Resumption protocol
The first concrete step for the next session. Numbered, actionable, with the exact command or file to touch.

### 14. Suggested next invocation
Copy-pasteable prompt for the next session. Includes scope, constraints, and verification.

### 15. Last user message (verbatim)
The verbatim text of the last user message that drove the work. Never summarize, never classify intent. Verbatim wins over summary framing when they conflict (per ADR-006).

```markdown
## Last user message (verbatim)

> "fix the problems. for the multiple streams the default is to do the stream that I asked for..."
```

### 16. Epistemic labels per claim
Every material claim is labeled:
- `[FACT]` — directly verifiable, with source citation
- `[INFERENCE]` — logical deduction from facts; state the chain
- `[UNKNOWN]` — cannot determine; state what would resolve it

## Optional section: Failure-mode catalog

For diagnostic-shaped investigations only. v0.1 includes it as an optional section; v0.2 will formalize it as a type-specific block.

Enumerate failure mechanisms (A/B/C/D...) with mechanism, isolation impact, stale-data impact.

## What v0.1 deliberately omits

The following appear in real handoffs (auto-commit, ccr-fleet, ai-api) but are **not** required in v0.1. Add them when the work warrants; do not pad.

- Options table with selection criterion (architectural decisions)
- Layered root-cause (material diagnostic failures)
- Evidence packet (implementation work)
- Value accounting and lesson calibration (retrospective work)
- ADR draft (architectural decisions; v0.2 promotes on close)

When one of these is genuinely needed for the work at hand, include it. The 16 mandatory fields are the floor, not the ceiling.

## Revision history (v0.2; documented for forward compatibility)

When v0.2 ships `/handoff update`, modifications append a revision block at the bottom:

```markdown
## Revision history

### Revision 1 — <iso8601> — <terminal_id>
- Changed: status OPEN → READY_FOR_REVIEW
- Changed: task AC-CONTAIN-01 acceptance criteria tightened
- Reason: live-behavior test showed foreign file appeared in commit despite gate
```

Never mutate prior content. Append only. This preserves the reasoning trace.
