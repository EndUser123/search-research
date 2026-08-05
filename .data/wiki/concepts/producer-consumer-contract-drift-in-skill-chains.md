---
title: "Producer-consumer contract drift in skill chains"
created: 2026-07-25
source: session-2026-07-25 (/risks on /refine + readiness gates)
sources:
  - P:/.artifacts/risks/019f9b6f-98fc-7883-9d5f-cf570a0b3812/20260725-182300/scope-gap.json (SCOPE-2)
  - P:/.artifacts/risks/019f9b6f-98fc-7883-9d5f-cf570a0b3812/20260725-182300/workflow.json (WF-4, WF-5)
tags: [skill-design, contract-drift, producer-consumer, handoff, inter-skill-contract, anti-pattern, red-team-finding]
summary: >
  When a new skill is added as a producer (writes an artifact that other skills
  consume), the contract between producer and consumers must be negotiated
  explicitly. Designing the producer in isolation — inventing field names,
  adding fields the consumers don't read, assuming the consumer's schema —
  produces a "write-only contract": the producer writes; nobody reads; the
  fields are documentation, not enforcement. Detected via /risks on the
  /refine skill, which invented "Original task (verbatim)" (handoff's actual
  field is "Last user message (verbatim)") and wrote three structured fields
  ([NEEDS CLARIFICATION], [DO NOT CHANGE], rollback plan) that no downstream
  skill (/go, /check, /review) reads. The fix is not to remove the fields; it
  is to wire the consumers or explicitly mark the fields as operator-facing
  documentation.
agent: grok
host: both
cognitive_load: 2
verification: red-team-verified
relations:
  - target: wiki/concepts/task-refinement-interview-detection-template-patterns
    type: refines — that concept is the producer's design rationale; this is the consumer-side gap that design missed
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: related — templates/validators pattern; this is the missing validator (consumer-side check)
  - target: wiki/concepts/llm-handoff-best-practices
    type: extends — adds the producer-consumer coordination layer
  - target: wiki/concepts/skill-authoring-patterns-dos-and-donts
    type: related
---

# Producer-consumer contract drift in skill chains

## Decision context

**Why this knowledge was needed:** a `/risks quick` run on the new `/refine
skill and its readiness gates surfaced a BLOCK-severity cluster: `/refine`
writes three structured handoff fields (`[NEEDS CLARIFICATION]`, `[DO NOT
CHANGE]`, rollback plan) that no downstream skill reads, and invented a field
name ("Original task (verbatim)") that does not match the consumer's schema
(`/handoff`'s actual field is "Last user message (verbatim)"). The red-team
verifier confirmed via grep across `/go`, `/check`, `/review`, `/plan-writer`,
`/refactor` — zero matches.

The pattern generalizes beyond `/refine`: any time a new skill is added as a
producer in a skill chain, the same drift can occur.

## The anti-pattern

```
Producer skill (new) ──writes artifact──▶ Consumer skill (existing)
        │                                       │
        │  invents field names                  │  reads its own schema
        │  adds fields consumers don't read      │  silently ignores new fields
        │  assumes schema alignment             │  (or actively fails on them)
        ▼                                       ▼
   "Write-only contract" — the producer's fields are documentation, not enforcement
```

Three observable symptoms:

1. **Field name drift.** Producer invents a name; consumer has a different name for the same concept. Result: the producer's field is orphaned; the consumer reads its own field, missing the producer's content.
2. **Unread structured fields.** Producer writes structured markers (`[NEEDS CLARIFICATION]`, `[DO NOT CHANGE]`) intended to drive downstream behavior. No downstream skill is wired to read them. Result: the fields are inert decoration.
3. **Schema assumption without verification.** Producer assumes the consumer's format (e.g., "16 mandatory fields") without reading the consumer's actual schema document. Result: drift goes unnoticed until a red-team or runtime failure surfaces it.

## Why this is architectural, not implementation

This is not "the code has a bug." It is "the design didn't coordinate with its
neighbors." No amount of refining the producer's prompt fixes it; the consumers
must also change, OR the producer's fields must be explicitly reclassified as
operator-facing documentation (not inter-skill contract).

The failure compounds silently: the producer skill ships, appears to work (it
writes the fields), passes `/check` (the fields are well-formed Markdown), and
the contract drift persists until either (a) a red-team catches it, or (b) the
operator notices downstream skills ignoring the new structure.

## Detection

Grep-based: for each field the producer writes, search all consumers for the
field name or a semantic equivalent. Zero matches = write-only contract.

```bash
# Example detection command
rg "NEEDS CLARIFICATION|DO NOT CHANGE|rollback plan" \
   ~/.grok/skills/go ~/.grok/skills/check ~/.grok/skills/review \
   ~/.grok/skills/plan-writer ~/.grok/skills/refactor
# 0 matches = drift; the fields are not enforced anywhere downstream
```

This is the structural validator the `designing-harnesses...` concept calls for
as Technique 2. Without it, the producer's prompt-level instructions ("write
[NEEDS CLARIFICATION] markers") are advisory rules that don't fire under
pressure.

## Fix patterns

**Option A — Wire the consumers (preferred for load-bearing fields).** Add a
read instruction to each consumer: "/check verifies [NEEDS CLARIFICATION]
markers were addressed; /review flags violations of [DO NOT CHANGE] blocks."
The fields become enforced contract.

**Option B — Reclassify as operator-facing documentation.** Explicitly mark
the fields as "written for the operator reading the handoff, not for downstream
skill consumption." This is honest and cheap; it's the right answer when the
field is genuinely for human reading (e.g., rollback plan, which the operator
uses to decide whether to authorize a change).

**Option C — Remove the field.** If neither A nor B fits, the field is cargo
from a template the producer copied. Drop it.

The key discipline: **make the choice explicitly.** Drift happens when the
choice is implicit (the producer writes, nobody decides whether anyone reads).

## Relation to existing patterns

- **[[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] Technique 2 (validators):** this is the missing
  validator for inter-skill contracts. The wiki documented the template-side
  validator (`validate_wiki_entry.py`); the producer-consumer validator is the
  analogous pattern for skills.
- **[[llm-handoff-best-practices]]:** the handoff format is a typed contract.
  This pattern is what happens when a new producer extends the contract without
  updating the type definition.
- **[[prompting-patterns-for-ai-agent-control]] § "source-of-truth directives":**
  the source of truth for field names is `/handoff/references/core-fields.md`.
  Producers that invent names without reading it violate the directive.
- **[[task-refinement-interview-detection-template-patterns]]:** the producer-side design rationale; this concept is the consumer-side gap that design missed.
- **[[skill-authoring-patterns-dos-and-donts]]:** broader skill-authoring patterns this extends.

## Falsifier

This pattern is wrong if:

- The producer's fields are genuinely useful even when unread by downstream
  skills (e.g., they guide the operator's manual review). Then they are
  documentation, not contract — Option B applies, and there's no drift.
- The downstream skills are eventually wired to read the fields, and the gap
  was just sequencing (producer shipped before consumer update). Then it's
  implementation debt, not architectural drift.
- The fields were always intended as producer-internal scaffolding that doesn't
  need to survive into the consumed artifact. Then they should be stripped
  before write, not written into the handoff.

The test: ask "what consumer reads this field?" If the answer is "the operator
manually" → documentation (Option B). If the answer is "nobody, yet" → drift
(Options A or C). If the answer is "a specific downstream skill" → verify by
grep that it actually does.

## Reference incident

2026-07-25 `/refine` ship: the skill was designed with three new structured
handoff fields (`[NEEDS CLARIFICATION]`, `[DO NOT CHANGE]` tri-state, rollback
plan) and one renamed field ("Original task (verbatim)" vs `/handoff`'s "Last
user message (verbatim)"). Red-team grep across 5 consumers returned 0 matches.
The fields were carrying weight in `/refine`'s prompt (Hard Rule #4 caps
`[NEEDS CLARIFICATION]` at 3) but nowhere else.

**Severity correction after /tp critique (2026-07-25):** the red-team originally
rated this BLOCK. The /tp fresh-lens critique argued, and verification confirmed,
that the handoff body explicitly permits additional fields ("the 16 mandatory
fields are the floor, not the ceiling" — `core-fields.md:177`). The drift is
real but it is a naming + verification defect, not a contract violation.
**Corrected severity: REVISE.** The structural fix is the producer-side
validator pattern (`validate_refinement_markers` added to `/handoff/__lib/validators.py`
2026-07-25), matching `validate_scope_bounds` and `validate_falsifier_strength`.

## Fix applied

- Renamed "Original task (verbatim)" → "Last user message (verbatim)" in /refine
  to match the /handoff schema.
- Added `validate_refinement_markers` to `/handoff/__lib/validators.py` —
  validates that every `[NEEDS CLARIFICATION: ...]` marker carries a
  `Resolution:` field (unanswered | answered: <one-line>). This is the
  producer-side validator the wiki concept's own "templates + validators are
  paired" rule called for; the original red-team missed it because of
  shared-framing anchor (same agent wrote the research, the skill, and the
  red-team).

## Source

- `/risks quick` run on `/refine` + readiness gates, 2026-07-25
- Findings file: `P:/.artifacts/risks/019f9b6f-98fc-7883-9d5f-cf570a0b3812/20260725-182300/scope-gap.json` (SCOPE-2)
- Findings file: `P:/.artifacts/risks/019f9b6f-98fc-7883-9d5f-cf570a0b3812/20260725-182300/workflow.json` (WF-4, WF-5)
- Cluster: RC-1 (BLOCK severity, 2-specialist amplification)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
