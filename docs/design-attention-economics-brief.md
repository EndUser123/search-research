# Task brief: extend `/design` with an attention-cost principle

Hand this to the AI-coder that implements the change. It is the implementation
counterpart to `external-reviewer-preamble.md`.

---

## Goal

Make `/design` rank its recommendations by leverage-per-future-attention-cost
and lead with a single highest-ROI change instead of a pile. Express this in
the vocabulary `/design` already uses. Do **not** introduce a new named
framework, system, or branded concept.

## Step 0 (mandatory, before any edit): rule out NO CHANGE

Before proposing the edit, answer this in writing:

> What single sentence does `lean-system-design.md` (and the evidence-tier /
> frustrated-user sections) currently **lack** that the attention-cost
> principle would add?

If you cannot name a concrete sentence that is missing, the correct output is
`NO CHANGE` — a one-paragraph clarification appended to the existing
`lean-system-design` reference, not the behavior changes below. The
attention-cost principle may be a restatement of what `/design` already says
under a different name. Rule that out first.

## Blocking prerequisite: read source first

Signature packs, TOCs, and descriptions are claims about the code, not the
code. Edit only after reading, at minimum:

- `skills/design/SKILL.md`
- `skills/design/resources/base.md`
- `skills/design/resources/audit-first.md`
- `skills/design/references/lean-system-design.md`
- `skills/design/references/scope-and-contract.md` (if present)
- `skills/design/resources/contract-authority-packet.md` (if present)
- `skills/design/schemas.py` (if present)
- design tests covering frustrated-user, lean integration, claim
  verification, payload validation, contract packets

If any required source file cannot be read, stop and report
`DESIGN_BLOCKED` rather than editing from signatures. Do not invent paths.

## The principle to add

Prefer extending an existing section (lean-system-design, audit-first, or
frustrated-user) over creating a new one. Express it in that section's own
vocabulary — no new proper noun:

> Rank recommendations by expected outcome value divided by future attention
> cost — the files, concepts, and drift points a future session must hold,
> plus the recurring triage and integration surface the change creates. Code
> is written by agents, so build effort is cheap; attention is the scarce
> resource. Lead with the single highest-ROI change regardless of size, then
> minimize that change's attention surface. Smallness is a property of the
> chosen solution, not the selection criterion. "No change" is a valid lead
> when an existing mechanism already covers the failure.

## Behavior changes

1. For skill/workflow/system-improvement requests, lead with **one**
   highest-ROI recommendation, not equally-weighted lists.
2. Before proposing any new gate, stage, ledger, artifact, agent, hook, or
   skill, name the closest existing mechanism and explain why extending,
   simplifying, or deleting it is insufficient. `NO CHANGE` is valid when the
   existing mechanism already covers the failure.
3. For structural failures, consider whether a larger simplifying remedy
   beats a local patch. For one-off failures, don't propose broad mechanisms.
4. For nontrivial recommendations, name ≥2 viable options, the selection
   axis, why the winner wins, the strongest objection to the winner, and what
   would falsify it.
5. New blocking gates need a real corpus/eval that measures TP and FP.
   Without one, the recommendation is advisory-only. **Before implying any
   eval path, grep for the existing calibration harness** (gate-discrimination
   calibration, `feedback_gate_discrimination_rule`) — reuse it, don't clone
   it.
6. Do not weaken existing evidence-tier rules. Pasted LLM output and prior
   assistant claims stay hypotheses. Source/runtime outranks signatures,
   summaries, and prose.

## Implementation guidance

- Modify existing reference/resource text and tests. Do not add a new
  "authority" system, reviewer agent, ledger, or gate unless source
  inspection proves no existing mechanism can carry the rule — then justify
  in writing.
- If an existing mechanism is over-engineered, propose simplifying it instead
  of layering on.
- Keep output-format requirements flat and short. No mandatory multi-page
  artifacts.
- Preserve the `/planning` boundary: `/design` owns architecture decision
  closure; `/planning` owns implementation-plan rewrites.
- **Plugin cache step (required, not optional):** this repo loads `/design`
  from the plugin cache on `C:`, source at `P:`. Edit the marketplace source →
  bump `plugin.json` version → run `plugin-audit-and-fix.py --bump
  cc-skills-sdlc` → verify the cache copy matches source → `/reload-plugins`.
  Without this the edit is inert at runtime; a syntax-clean source edit is
  not a working skill change.

## Output contract for `/design` recommendations

Flat, short. For improvement/design recommendations, include:

- Top recommendation
- Selection axis
- Why this wins on attention-adjusted ROI
- Existing mechanism inspected / extended
- Siblings considered and cut (one line each)
- Strongest objection
- Falsification signal
- Unread or unverified sources, if any

Reconcile this with any existing output shape the frustrated-user or
lean-system-design sections already define — do not create a second parallel
schema.

## Acceptance evidence

### Static invariants (testable now — these are the unit/snapshot tests)

These are the only tests this PR ships. `/design` is a markdown skill; model
behavior at runtime is not unit-testable.

- a. Skill text contains the principle paragraph in the chosen existing
  section (grep invariant), expressed without a new branded concept name.
- b. Skill text contains the 8-field output contract (or reconciles with the
  existing output shape — name which).
- c. Regression grep: evidence-tier language ("pasted LLM output … is not
  authority", "source/runtime outranks …") is present and un-weakened.
- d. Snapshot of the edited skill body, so unintended future drift is caught.
- e. The plugin cache copy matches source after the bump step.

### Runtime behavior (NOT this PR — do not fake it)

The following are **eval-corpus claims**, not pytest claims. Do not write
synthetic fixtures that assert a string in fake model output and call them
behavioral tests:

- "a design-improvement request produces one top recommendation with
  attention-adjusted ROI reasoning"
- "`NO CHANGE` is produced when existing mechanisms cover the failure"
- "a blocking-gate recommendation without corpus evidence is downgraded to
  advisory"
- "nontrivial recommendations include ≥2 options, winner rationale,
  objection, falsification"

Mark these as out-of-scope-for-this-PR, to be validated later against a
held-out corpus via the existing calibration harness. Claiming them as "live
behavior" from synthetic fixtures violates the brief.

### Honest reporting

- Show fresh `git status` before and after; show exact files changed.
- Show source-inspection evidence (the files read) — quote the specific lines
  edited.
- Run the narrow relevant suite first, then any broader design suite that is
  practical.
- Report scoped results honestly. Do not claim "all green" if only a subset
  ran or unrelated failures remain.

## Failure direction

- If required source files cannot be read → `DESIGN_BLOCKED`, no edits.
- If the only implementation path requires a new framework/ledger/gate →
  stop, justify in writing why existing `/design` mechanisms cannot carry it.
- If tests pass only through synthetic fixtures with no real skill text or
  source path exercised → do not claim live behavior.
- If Step 0 finds the principle is already present → `NO CHANGE` with the
  one-paragraph clarification, and stop.

## Do not commit unless explicitly instructed.
