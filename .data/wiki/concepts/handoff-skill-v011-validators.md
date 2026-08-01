---
title: "Handoff skill v0.1.1: scope-bounds, falsifier-strength, assignment fields"
created: 2026-07-20
source: session-2026-07-20
tags: [handoff, skill, validator, scope, falsifier, assignment, cross-host, fleet-coordination]
summary: >
  Four validators added to the handoff skill after a session-skip incident
  (2026-07-20) where a handoff said "7000+ videos" in the Objective but a
  Verified Fact mentioned "51,337 pending videos" with no labeling of which
  was the work scope. The validators catch: (1) scope-number discrepancies
  between Objective and Verified Facts, (2) weak falsifiers on bulk tasks
  ("produces 0 output" passes a 30% success rate that is still a disaster),
  (3) inconsistent assignment/lock fields, (4) heading-match false positives
  where descriptive headings like "## 1. Objective (one sentence)" were
  rejected. Plus: optional `assigned_to` / `assigned_at` / `assigned_by`
  frontmatter for fleet coordination, surfaced in `/handoff list`.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/llm-handoff-best-practices
    type: refines
  - target: wiki/concepts/operator-collaboration-style-and-leverage
    type: related
  - target: wiki/concepts/host-surface-boundary
    type: related
---

# Handoff skill v0.1.1: scope-bounds, falsifier-strength, assignment fields

## Summary

Four new validators and one optional frontmatter block added to
`P:/.grok/skills/handoff/__lib/validators.py` after a real handoff
produced ambiguous scope numbers that would have misled a fresh session.

The pattern this captures: **handoff content is operational; small
ambiguities compound into wrong acceptance criteria, wrong throughput
estimates, and wrong falsifier thresholds.** Validators make the
failure class mechanically detectable rather than author-dependent.

## Reference failure (2026-07-20)

A handoff at `P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md`
carried:

- Objective: "Make `yt-is fetch` reliably download transcripts... at production
  scale (7000+ videos)"
- Verified Fact #8: "All **51,337** pending videos have `has_captions=0`"
- Task packet acceptance: "transcript_cache grows by **~7000** rows"

A fresh session reading "7000" would declare success at 7000 and leave ~44,000
on the table. The 51,337 ambient total and the 7,000 work scope were both
correct numbers; the handoff never labeled which was which. Throughput
estimates ("several hours") were calibrated to 7,000 — off by ~7× if the
backlog was actually 51,337.

Separately, the same handoff's TASK-01 had falsifier: *"produces 0 transcripts
or crashes with auth error."* A run producing 3,000/7,000 (43%, rpc_code=9
eating the rest) would pass that bar despite being a disaster.

## The four new validators

All severity = `warn` (advisory, not blocking). Heuristics with explicit
false-positive suppressions.

### 1. `validate_scope_bounds` — detect Objective/Verified-Facts number mismatch

**Fires when:** the largest number in the Objective section is >3× smaller than
a number in the Verified Facts section, AND no scope-labeling keyword is present
("scope bound", "work scope", "of these", "deferred", etc.).

**Suppression:** explicit scope labels in the combined text silence the warning.
Author writing "Scope: ~7,000 of 51,337 total" passes cleanly.

**Heuristic limits:** integers only, comma-grouped thousands handled
("51,337" → 51337), filters out years (1800–2099) and small numbers (<100).

### 2. `validate_falsifier_strength` — weak falsifier on bulk task

**Fires when:** a task packet's goal or in-scope contains a bulk keyword
(`fetch`, `batch`, `bulk`, `backlog`, `scale`, `migrate`, `production`, etc.)
AND the falsifier contains a catastrophe word (`0`, `zero`, `crash`, `empty`)
but no rate indicator (`%`, `percent`, `rate`, `threshold`, `>=, `at least`).

**The reasoning:** "produces 0 output" only catches total failure. For
bulk/scale tasks, a 30% success rate passes that bar but is a production
disaster. The validator pushes the author toward a rate-threshold falsifier
("success rate < 90%") rather than a catastrophe-only one.

### 3. `validate_assignment_fields` — inconsistent fleet-claim fields

**Fires when:** `assigned_to` is present in frontmatter but `assigned_at`
or `assigned_by` is missing (or vice versa).

**Purpose:** the optional assignment/lock block records fleet claims
machine-readably. A partial block (assignee without timestamp or provenance)
is broken coordination state.

### 4. `validate_body_sections` — heading-match prefix fix (latent bug)

**Was:** exact-string match after numbered-prefix strip. A heading like
`## 1. Objective (one sentence)` lowercased to `objective (one sentence)`
and failed to match the required section `objective`. The validator reported
4 false-positive "missing section" errors on a handoff using the descriptive
heading style shown in the skill's own examples.

**Now:** prefix match — a heading matches a required section if it starts
with the section name followed by a word boundary (space, paren, colon, or
end-of-string). `objective (one sentence)` matches `objective`. Backward
compatible: exact-match headings still pass.

## Optional assignment block (v0.1.1 schema extension)

Three optional frontmatter fields for fleet coordination:

```yaml
assigned_to: grok              # host or role identifier ("grok", "claude", "codex")
assigned_at: 2026-07-20T16:48:47Z  # ISO 8601 timestamp of the claim
assigned_by: 019f81b3-...      # session-id that made the claim (provenance)
```

**Semantics:**
- All three absent = unclaimed (anyone may take it)
- All three present = claimed; `/handoff list` surfaces the claim
- The producing session is usually ending; `assigned_by` records provenance,
  the claim belongs to any future session on that host

**Immutability note:** the chain header is immutable per file per the skill
contract. Adding the assignment fields is defensible as *additive metadata* —
we're not rewriting `produced_at` or `accurate_as_of_head`, just recording
fleet-coordination state alongside them.

## What this does NOT validate (deferred)

- **Parameter single-source-of-truth.** Detecting that the same parameter
  (e.g., `--workers N`) is cited differently across sections requires
  cross-section semantic analysis. Too fragile for a generic validator.
  Stays as author discipline.
- **Throughput-math correctness.** "Several hours" without math is a story;
  verifying arithmetic ("5 videos = 42s → 8.4s/video → 7000 @ 1 worker ≈ 16.3h")
  is too hard to validate generically. Lives as task-packet guidance:
  `estimate` field with "math shown" expectation.
- **Long-running-task risk.** Runs exceeding session/auth lifespan need an
  `auth-expiry mitigation` field on the task packet. Guidance only —
  validation would need to detect duration > auth lifespan, which requires
  parsing the estimate field.

## Why warn-severity, not error

The validators are heuristic. Real-world false positives include:
- A Verified Fact legitimately mentions a much larger unrelated number
  (e.g., "the dataset has 1M rows but we're touching 500")
- A bulk task with a non-catastrophe falsifier that's still weak ("if it
  fails") — no rate threshold, but no catastrophe language either

Error-severity would block valid handoffs. Warn-severity surfaces the
concern; the author decides.

## Test coverage

133 tests total (114 pre-existing + 19 new), all passing. New tests:
- 6 assignment-field tests (complete triple, each-missing, bad timestamp,
  at-without-to)
- 4 scope-bounds tests (silent on no-numbers, warn on 7000-vs-51337,
  suppressed by subset-label, silent on small discrepancy)
- 4 falsifier-strength tests (bulk+catastrophe warns, bulk+rate passes,
  non-bulk silent, integration via `validate_handoff_text`)
- 1 heading-match test (descriptive-suffix acceptance)
- Plus mutation-test coverage for each validator's specific failure mode

## Cross-host applicability

The handoff skill lives at `P:/.grok/skills/handoff/` (Grok's surface), but
the contract — 16 mandatory fields, chain header, validators — is host-agnostic.
Claude Code could adopt the same skill with its own invocation path. The
validators are pure Python functions with no host-specific imports.

The 2026-07-20 reference failure is host-agnostic in shape: any handoff
produced by any host can carry scope ambiguity, weak falsifiers, or
descriptive headings. The validators catch the pattern regardless of producer.

## Falsifier

If the validators fire on a handoff where the scope discrepancy is legitimate
and clearly labeled (e.g., "**Scope bounds:** work scope is N of M total"),
but the suppression keywords don't catch the label, the `_SCOPE_LABEL_KEYWORDS`
list is too narrow and needs the missing phrase added.

If the falsifier-strength validator fires on a bulk task that genuinely only
has catastrophe as a failure mode (rare — e.g., a one-shot migration that
either completes or doesn't), the `_BULK_KEYWORDS` list is too broad.

If the heading-match prefix logic accepts a heading that shouldn't match
(e.g., "objective-like thinking" matching "objective" because of the
space-prefix rule), the word-boundary check needs tightening.

## Sources

- Reference failure: `P:/docs/handoffs/ytis-nlm-fetch-and-migration-20260720/HANDOFF.md`
  (2026-07-20 session, reviewed before the validators existed)
- Skill source: `P:/.grok/skills/handoff/__lib/validators.py`,
  `P:/.grok/skills/handoff/references/core-fields.md`,
  `P:/.grok/skills/handoff/SKILL.md`
- Test suite: `P:/.grok/skills/handoff/tests/test_mutation.py`
- Sibling concept: [[llm-handoff-best-practices]] §9 ("evidence for done") —
  this page is the mechanical implementation of that advisory rule for the
  scope/falsifier/heading dimensions

## Related

- [[llm-handoff-best-practices]] — master external-research doc on handoff
  patterns; this page refines §9 with mechanical validators
- [[operator-collaboration-style-and-leverage]] §2.1 — "evidence for done"
  gap; these validators close one dimension of it
- [[host-surface-boundary]] — sibling finding from the same session

## Auto-related

<!-- Populated by wiki_after_write.py via QMD semantic search. -->
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
