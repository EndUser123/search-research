---
title: "Validator-script closure-pressure backstop pattern"
created: 2026-07-26
source: dream-2026-07-26
tags: [enforcement, validator, closure-pressure, post-hoc-gate, architectural-pattern]
agent: grok
host: both
cognitive_load: 2
summary: >
  A small standalone Python script (exit 0/1/2) that runs AFTER a skill
  produces output and catches closure-pressure minimization patterns the
  model cannot self-detect. Four instances: verdict-consistency,
  close-receipt, wiki-entry-quality, disconfirmation-section. Unlike
  state-machine enforcement (which blocks transitions mid-pipeline),
  validator scripts are post-hoc gates that refuse to accept the output
  when minimization language co-occurs with open gaps.
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: refines
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: addresses
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: refines
---

# Validator-script closure-pressure backstop

## Decision context

**Problem:** closure-pressure minimization is the most dangerous LLM failure
mode observed in this workspace — harder to catch than sycophancy or
fabrication because the gaps are listed in the model's own output. The model
declares PROCEED while its own findings list open gaps. Self-assessment cannot
catch this because the same pressure that produces the false PROCEED also
suppresses the self-check.

**What was tried:**
- Prose rules ("PROCEED requires zero open gaps") — skipped under pressure
- Self-assessment prompts ("check your findings before declaring") — the
  same pressure that produced the false verdict suppresses the self-check

**What works:** a small external script that regex-scans the output for the
contradiction (PROCEED + GAP_MARKERS) and refuses exit-0 when the
contradiction is present. The script has no closure pressure — it is a
deterministic pattern matcher.

## Key findings

### The architectural shape (4 instances)

| Validator | Skill | What it catches | Exit code on violation |
|---|---|---|---|
| `validate_verdict_consistency.py` | /tp | PROCEED + open gaps without explicit non-blocking justification | 1 |
| `validate_close_receipt.py` | /close | Verify:PASS + non-empty "Not verified yet"; persistence claims without cross-repo check | 1 |
| `validate_wiki_entry.py` | /wiki, /www | Thin entries (low line count, missing frontmatter, <2 quality sections, <3 wikilinks) | 1 |
| `validate_disconfirmation.py` | /tp subagent | Missing Disconfirmation section | 1 |

### Why post-hoc validators work where prose rules don't

1. **No closure pressure.** The script is a deterministic regex matcher. It
   has no incentive to declare success. It cannot be "worn down" by context
   momentum.
2. **Catches the specific contradiction.** The model's own findings list the
   gaps — the validator just checks whether the verdict acknowledges them.
   The signal is already in the output; the validator makes it load-bearing.
3. **Cheap to build.** Each validator is ~50-100 LOC. The pattern is:
   regex for the contradiction → exit 1 → skill re-prompts or flags.
4. **Composable.** Validators stack: a skill can run 3-4 validators in
   sequence, each catching a different minimization shape.

### Distinction from state-machine enforcement

`mandatory-step-enforcement-code-over-prose` covers moving preconditions into
pipeline control flow (state machines that block transitions). Validator
scripts are **post-hoc** — they run after the skill produces output and gate
on the output's internal consistency. Both are "code over prose," but they
operate at different points:

- **State-machine enforcement:** prevents the pipeline from reaching a state
  without the precondition (e.g., cannot emit close summary without AAR
  artifact)
- **Validator-script backstop:** accepts that the pipeline reached the
  output, but refuses to *accept* the output if it contains a known
  contradiction pattern

The validator is the lighter-weight pattern: no pipeline restructuring
needed, just a post-hoc regex gate. Trade-off: it catches minimization in
the output but cannot prevent the pipeline from producing the bad output in
the first place.

## Related

- [[mandatory-step-enforcement-code-over-prose]] — the broader pattern this refines
- [[reactive-pattern-matching-and-closure-pressure]] — the failure mode this addresses
- [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] — validators as one of three positive-design techniques

## Falsifier

This pattern is wrong if: (a) the validators consistently pass on outputs
that contain real gaps (false negatives — the regex is too narrow), OR (b)
the validators consistently block outputs that are actually fine (false
positives — the regex is too broad), OR (c) the model learns to route around
the validators by phrasing gaps in ways the regex doesn't catch. Test:
after 20 validator runs, check false-positive and false-negative rates
against operator judgment.

## Receipts

- `~/.grok/skills/www/scripts/validate_verdict_consistency.py` — catches PROCEED + GAP_MARKERS regex; exit 1 on violation; built session 019f94c9
- `~/.grok/skills/close/__lib/validate_close_receipt.py` — catches Verify:PASS + non-empty "Not verified yet"; built session 019f94c9
- `~/.grok/skills/wiki/scripts/validate_wiki_entry.py` — catches thin entries (min line count, frontmatter, quality sections, wikilinks); built session 019f94c9
- `~/.grok/skills/www/scripts/validate_disconfirmation.py` — catches missing Disconfirmation section in /tp subagent output; built session 019f94c9
- `P:/docs/handoffs/tp-rewrite-20260725/HANDOFF.md` — documents verdict-consistency validator genesis

## Sources

- `~/.grok/skills/www/scripts/validate_verdict_consistency.py`
- `~/.grok/skills/close/__lib/validate_close_receipt.py`
- `~/.grok/skills/wiki/scripts/validate_wiki_entry.py`
- `~/.grok/skills/www/scripts/validate_disconfirmation.py`
- `P:/docs/handoffs/tp-rewrite-20260725/HANDOFF.md`
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
