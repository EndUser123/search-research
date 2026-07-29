---
title: "Handoff fragmentation under recurrence: single-writer-per-file produces N authoritative files for one workstream"
created: 2026-07-27
source: session-019fa5a1
tags: [handoff, system-behavior, single-writer, recurrence, consolidation, stale-data, multi-agent, structural-property]
summary: >
  The /handoff skill's single-writer-per-file design (Hard Constraint #5) combined
  with create-new-file-per-invocation produces a structural side effect: when work
  recurs across sessions (e.g., a workstream spanning 2026-07-24 → 07-26 → 07-27),
  it generates N files for one workstream. The newest is authoritative, but priors
  are NOT auto-marked superseded. A fresh session reading any prior gets a stale or
  wrong picture — including recommendations that the newest has since BLOCKed. This
  is the structural reason periodic consolidation is needed; it is not carelessness
  but a consequence of the single-writer safety constraint.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "P:/docs/handoffs/close-aar-mechanical-enforcement/HANDOFF.md (session 019f91d3, 2026-07-24) — recurrence 1 of the AAR non-skippable workstream"
  - "P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md (session 019f94c9, 2026-07-26) — recurrence 2; red-team revision recommending Stop hook"
  - "P:/docs/handoffs/aar-non-skippable-enforcement-20260726-design-blocked/HANDOFF.md (session 019fa39d, 2026-07-27) — recurrence 3; BLOCKs the Stop-hook approach, reframes to scanner/validator"
relations:
  - target: wiki/concepts/llm-handoff-best-practices.md
    type: refines — that page covers external handoff patterns (event sourcing, single-writer); this names a side effect of the single-writer choice as implemented in our /handoff skill
  - target: wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md
    type: related — same structural shape: a design choice that is correct for its primary purpose produces a secondary failure mode that prose rules cannot fix
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: related — the AAR non-skippable workstream that exemplifies fragmentation is itself an instance of the prose-to-code promotion pattern
---

# Handoff fragmentation under recurrence

## Decision context

**Why this finding was captured.** During a `/handoff`-driven triage of AAR-related
handoffs (session 019fa5a1, 2026-07-27), the operator asked "find handoffs related
to AAR. Should we consolidate them?" The triage surfaced 14 AAR-related handoffs,
of which 3 were the *same workstream at three stages* (the `/aar` non-skippable
enforcement arc): a 2026-07-24 origin, a 2026-07-26 red-team revision, and a
2026-07-27 design-blocked reframe. The three are explicitly chained via
`parent_handoff_path` and "supersedes" language in their bodies — yet all three
carry `status: open`, and a fresh session reading the middle one (2026-07-26) would
see a Stop-hook recommendation that the newest one (2026-07-27) has since BLOCKed
as fatally flawed.

The real question behind this finding: *why does consolidation keep being needed?*
The answer is structural, not behavioral. It is a side effect of a correct safety
constraint, and naming the root cause lets future triage sessions and skill-improvement
sessions address it rather than re-deriving it.

## The structural property

The `/handoff` skill enforces single-writer-per-file (Hard Constraint #5): one
session owns a handoff file at a time, and auto-update mode only appends revision
blocks to same-session handoffs. Cross-session continuation creates a NEW file with
`parent_handoff_path` pointing at the prior. This is correct for write-safety on a
multi-agent shared tree — two sessions cannot clobber each other's handoff.

The side effect: **when work recurs across sessions, the skill produces N files for
one workstream, and nothing auto-propagates `status: superseded` to the priors.** The
chain is recorded (the new handoff's header points at the prior; the body may say
"supersedes"), but the prior's own `status` field stays `open`. The chain is
*explicit but one-directional* — it flows from child to parent in the child's
metadata, never from child back into the parent's status.

## Why this harms the next session

A fresh session doing handoff triage (or `/handoff list`) sees N rows that all
appear `open`. Without opening and reading each one in creation order, the triager
cannot tell:

1. Which is authoritative (the answer: the newest by `produced_at`, but only if the
   chain is intact and the newest is the true leaf).
2. Whether the prior's recommendations still hold (the 2026-07-26 AAR handoff
   recommends a Stop-hook approach; the 2026-07-27 one BLOCKs it as having a fatal
   granularity flaw — Stop hooks fire per-turn, not per-close).
3. Whether the work is active or abandoned (all three say `open`, but the workstream
   has progressed through three stages).

The concrete harm observed this session: the `/handoff list --head` output showed
all three AAR non-skippable handoffs as `yaml:open` with no signal that they were
one chain. Detecting the chain required reading the headers and bodies — exactly the
open-each-file labor that `/handoff list` was designed to avoid.

## Why this is not a bug in the skill

The single-writer-per-file constraint is load-bearing. It prevents two concurrent
sessions from silently destroying each other's handoff writes on the shared Windows
tree (a verified failure class on this host). Removing it to enable cross-session
in-place updates would reintroduce the collision risk the constraint exists to solve.

The create-new-file-per-invocation rule is similarly load-bearing: it gives each
session a write-safe target without coordination. Auto-update mode (revision blocks)
handles the within-session case; cross-session recurrence is genuinely a different
case that the v0.1 design deferred (the SKILL.md's `/handoff continue <path>` is
listed under "v0.1 does NOT do — deferred to v0.2+").

So the fragmentation is the *expected* output of two correct constraints
interacting with a recurring workstream. The fix is not to weaken the constraints;
it is to add a propagation step that the v0.1 design omitted.

## What this means for our workspace

Two candidate fixes, both skill-level (not prose rules — prose rules do not fire
under session pressure; see [[rule-not-fired-vs-rule-doesnt-exist]]):

1. **Auto-supersede on explicit parent chain (skill-level, /handoff v0.2 candidate).**
   When `/handoff` writes a new file whose `parent_handoff_path` points at an existing
   handoff AND the body contains "supersedes" language, the skill should update the
   prior's frontmatter to `status: superseded` and add a `superseded_by:` field
   pointing at the new file. This is a one-directional write into a file the new
   session did not create — but it is a *narrow, mechanical* write (two frontmatter
   fields), not a content mutation, so it does not violate the single-writer intent.
   The risk: a race if two sessions supersede the same prior simultaneously. Mitigation:
   atomic frontmatter patch via the same atomic-write pattern the skill already uses.

2. **Periodic consolidation passes (operational, current).** Until the skill-level
   fix ships, consolidation is a periodic operational task. The heuristic for detecting
   same-workstream-at-stages: (a) `/handoff list` shows multiple rows with overlapping
   objective prefixes, (b) headers chain via `parent_handoff_path`, (c) bodies contain
   "supersedes" language. The triager consolidates by writing one new authoritative
   handoff from the current session and marking priors `superseded`.

Until fix 1 ships, fix 2 is the standing practice. This finding documents *why* fix 2
is needed periodically so the next triage session does not treat the fragmentation as
an anomaly or a one-off.

## Receipts

Mechanism claims about the `/handoff` skill are grounded in the skill's governing
specification and observed runtime output, not inferred:

- **[FACT] Single-writer-per-file (Hard Constraint #5):** `C:\Users\brsth\.grok\skills\handoff\SKILL.md` § "Hard constraints" #5 — "The file is single-writer — one session owns it at a time. Auto-update mode appends revision blocks at the bottom; they never mutate prior content. Only the current session may update its own handoffs (verified by `current_session_id` match)." Read in session 019fa5a1 via the skill_information load.
- **[FACT] Auto-update mode is within-session only:** same SKILL.md, auto-update step 4 — "For each stale handoff from this session, append a revision block... Do NOT rewrite the original content — append only." Cross-session recurrence is not covered by auto-update; it creates new files.
- **[FACT] `/handoff continue <path>` deferred to v0.2:** same SKILL.md, "v0.1 does NOT do" — "`/handoff continue <path>` — cross-session chain traversal via `/aar`" is listed under deferred features.
- **[FACT] Create-new-file-per-invocation:** same SKILL.md, "Output location" — `P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md`; the standard process step 5 writes one file per handoff invocation.
- **[FACT] All 3 AAR non-skippable handoffs show `yaml:open` with no supersession signal:** `python ~/.grok/skills/handoff/__lib/list_handoffs.py --head <sha>` output from this session (Turn 1) showed `aar-non-skippable-enforcement-20260726`, `aar-non-skippable-enforcement-20260726-design-blocked`, and `close-aar-mechanical-enforcement` all as `yaml:open`. The chain was detectable only by reading headers, not from the list output.
- **[FACT] The chain is explicit but one-directional:** `P:/docs/handoffs/aar-non-skippable-enforcement-20260726-design-blocked/HANDOFF.md` header sets `parent_handoff_path: P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md` and body says "This handoff supersedes the prior red-team handoff" — but the prior's own `status` field remains `open` (verified by direct read, Turn 1).
- **[INFERENCE] Auto-supersede-on-parent-chain (fix 1) is safe under single-writer intent:** the proposed fix writes two frontmatter fields into a file the new session did not create. Whether the atomic-write + file-lock pattern the skill uses (per `references/core-fields.md`) covers this cross-session write case has NOT been verified against the implementation. The fix is a candidate, not a validated design.

## Falsifier

This finding is wrong or obsolete if:

- A future `/handoff` skill version ships auto-supersede-on-parent-chain (fix 1 above),
  making the fragmentation self-resolving. In that world, this concept should be marked
  `status: superseded` by the skill-design concept that replaces it.
- The `/handoff continue <path>` command (v0.2 deferred feature) ships with in-place
  chain traversal that makes priors read-only-displayed-as-superseded, achieving the
  same outcome without a status-field write.
- Empirically, recurring workstreams turn out to be rare (this finding would then be
  low-value). The AAR non-skippable arc (3 recurrences in 4 days) and the close-scanner
  arc suggest recurrence is common, not rare — but a longer measurement window could
  revise this.

**Discriminating test:** after fix 1 ships, run `/handoff list` on a directory with a
known 3-stage chain. If all three still show `status: open`, the fix is not working.
If the priors show `status: superseded`, this finding is resolved.

## Related

- [[llm-handoff-best-practices]] — external research grounding the single-writer choice;
  this finding names the side effect of that choice as implemented
- [[rule-not-fired-vs-rule-doesnt-exist]] — same structural shape: correct primary
  design with a secondary failure mode that prose cannot fix
- [[mandatory-step-enforcement-code-over-prose]] — the AAR non-skippable workstream
  that exemplifies fragmentation is itself an instance of prose-to-code promotion
