---
name: handoff
description: >
  Write a durable handoff document for the work stream the user asks about.
  Within-session compaction recovery (reads compaction/segment_*.md). Default
  scope: the current user request's work stream. Notes other outstanding
  streams if obvious from current context. Cross-session chain (thread_id,
  parent_handoff_path) is supported structurally but continuation is v0.2.
  Use for /handoff, handoff, session handoff, continuing work, work brief.
argument-hint: "[new <topic> | close <path> | list]  (default: new)"
user-invocable: true
---

# /handoff — work handoff for the next session

## Purpose

A `/handoff` writes a structured document that lets a future session continue
the work stream the user asks about, without re-deriving it. It is **not** a
chat summary. It is the operational artifact that preserves goal, decisions,
evidence, status, and next steps.

## v0.1 scope (what this skill does)

- `/handoff new <topic>` or just `/handoff` — write one handoff for the stream
  the user asks about. Default: the work stream behind the current request.
- `/handoff close <path>` — close a completed handoff: prompt for wiki
  promotion, then delete the file.
- `/handoff list` — list all open handoffs at `P:\docs\handoffs\` via the
  `__lib/list_handoffs.py` CLI (surfaces work status, freshness, ownership,
  mismatch, claim consistency, and optional `--head` drift detection; see
  the `/handoff list` section below).
- Reads `compaction/segment_*.md` from the current session to recover
  pre-compaction context (within-session only).
- Writes one file at `P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md`.
- Notes other outstanding streams if obvious from current context (does not
  write handoffs for them — just names them so the user knows to ask).
- Single handoff type: Investigation (the most common shape). Other types
  are recognized in the body but use the same 16 mandatory fields.

## v0.1 does NOT do (deferred to v0.2+)

- `/handoff continue <path>` — cross-session chain traversal via `/aar`
- `/handoff update`, `/handoff status`
- Multi-stream handoff writing (only notes other streams; does not write them)
- PLAN.md, DECISIONS.md, per-terminal status.jsonl
- Five-type templates (Investigation is the default; others are v0.2)

See `ROADMAP.md` for what's planned and why each piece is deferred.

## Stance

You are a **handoff author**, not a summarizer. Produce a document a fresh
session can act on without guessing.

- Distill work into load-bearing structure (goal, decisions, status, next)
- Verify every claim against evidence in the session before writing it as fact
- Preserve the verbatim last user message (never let summarizers reframe intent)
- Cite event-ids or file:line for every `[FACT]`
- Label uncertainty explicitly: `[FACT]`, `[INFERENCE]`, `[UNKNOWN]`

## Process

1. **Resolve session-id.** Read from `summary.json` in the current session
   directory (`~/.grok/sessions/<encoded-cwd>/<session-id>/`). Never infer
   from newest-timestamp. If `summary.json` is missing, stop and report.

2. **Identify the work stream.**
   - If the user named a topic, use it.
   - Otherwise, default to the work stream behind the current request.
   - **Multi-stream rule:** write the handoff for the stream the user asked
     about. If other streams are obvious from current context and any are
     open/outstanding, name them in an "Other outstanding streams" section
     with a one-line summary each. **Do not** write handoffs for them. The
     user will ask specifically when they want a prior-session stream
     documented; v0.1 does not traverse the prior-session chain.

3. **Recover within-session compaction.** If the session has compacted:
   - Read `compaction/INDEX.md` to enumerate segments
   - Read each `segment_NNN.md` (these are frozen transcript chunks;
     header is `# HISTORICAL -- DO NOT EDIT`)
   - Use the segments that pertain to the chosen stream; ignore unrelated ones

4. **Gather evidence.** Cite event-ids, file:line, or tool output. Do not
   write claims you cannot cite.

5. **Write the handoff** using the chain header + 16 mandatory fields in
   `references/core-fields.md`. Include the "Last user message (verbatim)"
   section — verbatim text wins over summary framing when they conflict
   (per `P:\docs\adrs\ADR-006-compact-handoff-verbatim-field.md`).
   Populate `accurate_as_of_head` from `summary.json.head_commit` in the
   producing session's directory.

6. **Verify the file persisted** by reading it back. Confirm structure.

7. **Report path** to the user.

## `/handoff close <path>` — complete and clean up

When the work described in a handoff is done, close it. Closing a handoff
has two steps:

1. **Promote durable findings.** Ask the user: "Did this work produce a
   durable lesson or decision worth finding later?" If yes:
   - Promote to `P:/.data/wiki/concepts/<slug>.md` (as a Concept or ADR per
     the `/design` Step 6d framework: Concept = lightweight; ADR = full
     solo-ADR format with shelf life, assumptions, revert path).
   - Write the promoted file with: decision, rationale, alternatives
     rejected, falsifier, source citation (the handoff path + date).
   - Confirm the wiki file was written.

2. **Delete the handoff.** Remove the handoff directory
   (`P:\docs\handoffs\<topic>-<YYYYMMDD>\`). The handoff was scaffolding;
   if there was durable value, it's now in the wiki. If there wasn't, the
   handoff is clutter.

**Do NOT keep completed handoffs as "provenance."** That's what the wiki is
for. A handoff that's been open for 30 days but still says "status: open"
is clutter that a fresh session has to triage.

**What if the user says "no durable findings"?** Skip promotion, delete the
handoff. Not every work stream produces a reusable lesson.

## `/handoff list` — show open handoffs

Run the list CLI to survey every `P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md`
in one pass without opening each file:

```bash
# Basic: list every handoff with work status, freshness, ownership.
python P:/.grok/skills/handoff/__lib/list_handoffs.py [handoffs_root]

# With HEAD-drift detection (recommended when triaging against current state):
HEAD=$(git -C P:/ rev-parse HEAD)
python P:/.grok/skills/handoff/__lib/list_handoffs.py --head "$HEAD"
```

Output columns per row:

- `<topic>-<date>` — directory name
- `yaml:<status>` — chain header `status` (file status: open/closed/superseded)
- `work:<STATUS>` — leading keyword from the body `## Status` section
  (OPEN / READY_FOR_REVIEW / BLOCKED / CLOSED / WONTFIX). Shows `?` when the
  body Status section is missing or doesn't open with a recognized keyword —
  a real signal that the handoff deviates from the contract.
- `MISMATCH` — flagged when body work-status is terminal (CLOSED or WONTFIX)
  but the file is still `yaml:open`. This is the "should have been closed"
  signal — a triager can act on it without reading the body.
- `claimed:<host>` — present only when the optional `assigned_to` field is
  set in the chain header AND all three assignment fields (`assigned_to`,
  `assigned_at`, `assigned_by`) are consistent. Inconsistent claims are
  hidden (the validator would warn on them) so the triager never sees a
  claim that doesn't have provenance. Two handoffs claimed by the same host
  on the same topic is a coordination failure; a claimed handoff should not
  be touched by another terminal.
- `head:DRIFT` — flagged only when `--head <sha>` is passed AND the handoff's
  `accurate_as_of_head` differs from the current HEAD. This is the
  stale-data-immunity signal (Hard Constraint #2): the handoff's cited
  tree paths may no longer exist or may have moved. Re-verify file:line
  references against the current tree before acting on the handoff.
  `head:?` means the handoff predates the v0.1.1 schema and has no
  `accurate_as_of_head` recorded at all — treat its references as
  unverified. (No flag = either matches current HEAD or `--head` was
  omitted.)
- `produced` — relative time (`just now`, `12m`, `3h`, `2d`, `5w`)
- `terminal` — short form of `current_terminal_id` (the prefix before first
  `_`). A row produced in the last hour by an unfamiliar terminal is likely
  in-flight from another session.
- `objective` — first non-empty line of `## Objective` (or `## Goal` as a
  fallback). Truncated to ~70 chars.

Rows are sorted newest-first by `produced_at`. Handoffs with unparseable
timestamps sink to the bottom and show `?` for the relative time. The script
tolerates small future-deltas (timezone drift in how `produced_at` was
written) by clamping to `just now`.

**Why `--head` is opt-in.** Resolving HEAD requires a git call. For ad-hoc
listing where staleness isn't the question, that's overhead. When triaging
or deciding whether to trust a handoff's tree references, pass `--head` and
the drift column appears. The summary line counts `N HEAD-drift` and
`N no-head-field` only when `--head` is active.

**Triage under multi-agent mutation.** `P:\docs\handoffs\` is shared across
all terminals. During a triage, new directories may appear that were not in
the user's named target set — this is normal, not anomalous. Default posture
toward handoffs outside the user's named set:

1. Note their existence (visible in `/handoff list` output: name, mtime,
   terminal, claim, HEAD-drift).
2. Do **not** open or read them — another terminal may be mid-write.
3. Report them as *"not in the named set; likely active elsewhere"* and ask
   whether to include.

The vocabulary matters: *"not in the set you named"* (honest) — not
*"outside scope"* (which implies a scope decision the user did not make) or
*"unexpected state"* (which implies anomaly). The user has fleet awareness
the triager lacks; surface the observation and let them decide.

**Why this is a script, not prompt instructions.** Opening 8 handoffs to
discover 5 are done doesn't scale. The list CLI extracts the load-bearing
fields (work status, freshness, ownership, claim, HEAD-drift) in one pass so
the triager opens only the rows that need attention. The HEAD-drift column
in particular is the structural fix for the trust-without-verify failure
mode: it cross-checks each handoff's recorded git HEAD against current
reality, which is the one signal the handoff author cannot self-certify.

## Hard constraints (always loaded)

1. **Multi-terminal isolation.** Handoffs write to
   `P:\docs\handoffs\<topic>-<YYYYMMDD>\` — shared read, single-writer. The
   `current_terminal_id` and `current_session_id` in the chain header record
   who owns the write. Another terminal wanting to write must branch a new
   handoff with `parent_handoff_path` pointing at the prior.

2. **Stale-data immunity.** Authority is the `(session_id, terminal_id)`
   recorded in the chain header. Facts in the handoff bind to the source
   state at production time (`produced_at` and `accurate_as_of_head`). A
   reader treating a handoff older than 24h as current, OR one whose
   `accurate_as_of_head` differs from current `git rev-parse HEAD`, must
   re-verify cited paths before acting.

3. **No `LATEST-*` pointers, no newest-timestamp discovery.** A new terminal
   starts fresh. If prior context is needed, the user supplies the path
   explicitly or invokes `/handoff continue <path>` (v0.2).

4. **Verbatim last-user-message preservation.** Never classify turn intent.
   A question is not a directive. Preserve actual text. (ADR-006.)

5. **Single-writer per handoff.** The file is single-writer — one session
   owns it at a time. Updates (v0.2) append revision blocks at the bottom;
   they never mutate prior content.

6. **Reads are deep copies.** A reader consuming another terminal's handoff
   gets a snapshot; mutations don't propagate back.

Detail and concrete examples: `references/core-fields.md`.

## Chain header (YAML frontmatter, mandatory)

```yaml
---
thread_id: <uuid>                       # stable across the work thread
parent_handoff_path: <path|none>        # prior handoff in this thread, if any
current_session_id: <uuid>              # session writing this handoff
current_terminal_id: <id>               # terminal writing this handoff
produced_at: <iso8601>
status: open
handoff_type: investigation             # v0.1 default; v0.2 adds others
accurate_as_of_head: <git-sha>          # git HEAD at production time; sourced from summary.json.head_commit
# Optional assignment block (v0.1.1) — uncomment when claiming for fleet coordination
# assigned_to: <host|none>              # e.g., "grok", "claude" — who has claimed this
# assigned_at: <iso8601>                # when the claim was made
# assigned_by: <session-id>             # session that made the claim (provenance)
---
```

The header is **immutable per handoff file**. A new handoff = new file with
a new header. `thread_id` is generated fresh by `/handoff new`; it will be
inherited by `/handoff continue` when that ships in v0.2.

For v0.1, `parent_handoff_path` is almost always `none` — the user invokes
`/handoff new` for fresh work. If the user explicitly names a prior handoff
to continue from, set `parent_handoff_path` to that path and inherit its
`thread_id`; this is the v0.1 escape hatch for cross-session continuation
without the full chain-walking machinery.

**Assignment fields (v0.1.1):** When a handoff is claimed so other hosts or
agents don't duplicate the work, set `assigned_to`, `assigned_at`, and
`assigned_by`. These are **optional** — absent means unclaimed (anyone may
take it). Present means a claim exists; `/handoff list` surfaces it. See
`references/core-fields.md` for the full semantics. The
`validate_assignment_fields` validator warns on inconsistency (e.g.,
`assigned_to` set but `assigned_at` missing).

## Output location

```
P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md
```

- `<topic>` — short kebab-case identifier from the user's request
- `<YYYYMMDD>` — production date

The directory holds just `HANDOFF.md` in v0.1. PLAN.md / DECISIONS.md /
status.jsonl are v0.2 additions when the work warrants them.

## Falsifier

If `/handoff` produces a handoff that a fresh session cannot act on without
re-deriving the work, the design has failed. If this happens twice in one
session, iterate this SKILL.md rather than continuing.

## Tests

Behavior and mutation tests live at `tests/`. Run with:
```bash
cd P:\.grok\skills\handoff && python -m pytest tests/ -v
```

See `tests/README.md` for what each test verifies and how to add new ones.

## References

- `references/core-fields.md` — the 16 mandatory fields + chain header schema
- `ROADMAP.md` — what's deferred to v0.2+ and why

Load `references/core-fields.md` when writing a handoff. The roadmap is for
planning, not for invocation.

## Boundaries

- `/handoff` writes operational artifacts only. It does not implement code,
  edit other skills, or modify the wiki.
- `/handoff` does not auto-fire. The user invokes it.
- `/handoff` is distinct from `/aar`. `/aar` reviews a session for lessons;
  `/handoff` writes the next session's brief. v0.2 will reuse `/aar`'s
  transcript parser for cross-session chain traversal; v0.1 reads
  compaction segments directly.
- `/handoff` is distinct from `/debrief`. `/debrief` captures session
  improvements across 5 lenses; `/handoff` produces the next session's brief.
