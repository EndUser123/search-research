---
title: "Dual-path hazard: delete manual instructions when replacing with a mechanical generator"
created: 2026-07-31
source: session-019fb177 (/tp critique of /ship skill)
tags: [mechanical-enforcement, skill-design, dual-path, usability, llm-behavior, transferable-pattern]
summary: >
  When replacing LLM-assembled manual checks with a code-enforced script generator,
  keeping the old manual instructions as "reference" causes dual-path confusion —
  LLMs follow BOTH paths, producing contradictory results. The fix: delete the
  manual instructions entirely. If historical context is needed, link to git
  history. This pattern applies to any mechanical-replacement work: close receipts,
  check receipts, review artifacts, AAR reports.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "Session 019fb177: /tp cold-read critique of /ship skill (explore subagent, 72s, 3 tool calls)"
relations:
  - target: wiki/concepts/ship-receipt-mechanical-generation-from-per-check-results.md
    type: refines
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
  - target: wiki/concepts/deterministic-output-engineering.md
    type: applies
---

# Dual-path hazard: delete manual instructions when replacing with a mechanical generator

## Decision context

**Why this was needed:** `/ship`'s Phase 3 had a 12-item manual check list. We replaced it with `ship_receipt.py`. But we kept the 12 items as "Reference (checks the script runs mechanically — formerly manual items 1-12)." A `/tp` cold-read critique (fresh subagent, no shared framing) found this was the **dominant usability hazard**: an LLM reading top-to-bottom would see the script invocation AND the 12 manual checks, then try to do both. The most dangerous contradiction: item 3 said "Lint the full project: `ruff check .`" while the script lints only changed files. An LLM running both would report `lint: clean` from the scoped script while a whole-repo lint might find unrelated issues — contradictory results.

**The pattern:** this is not specific to `/ship`. It applies to any skill where manual steps are replaced by a mechanical generator. The instinct to keep old instructions "for reference" or "for understanding" is actively harmful because LLMs don't distinguish "reference" from "do this."

## The finding

**[OBSERVED — exit code 0 from /tp subagent]**: the fresh subagent identified the 12-item reference list as HIGH severity finding #1 out of 10 total findings, with the specific failure mode: "An LLM reading top-to-bottom will see the script invocation, then immediately see 12 manual checks, then wonder: 'Should I run the script AND do the 12 items? Or just the 12 items? Is the script redundant?'"

**[DERIVED]**: the `[[mechanical-enforcement-over-behavioral-reminder]]` principle says prompt instructions have ~12% compliance ceiling. But there's a corollary: when TWO instruction sets exist for the same task (manual + mechanical), compliance doesn't double — it splits. The LLM picks one path (often the wrong one) or does both (wasteful + contradictory). The mechanical path only works if it's the ONLY path.

## Why LLMs follow both paths

LLMs read instructions top-to-bottom and attempt to satisfy ALL instructions they encounter. The label "formerly manual items" or "reference only" is a weak signal that most LLMs don't reliably interpret as "do not execute these." This is the same failure mode as [[deterministic-output-engineering]] describes: LLMs prioritize conversational fluidity over structural rigidity. "Reference" is a conversational signal, not a structural one.

The structural fix is deletion. If an LLM needs historical context, link to the git commit that removed the manual steps — git history is the durable record, not the skill text.

## Transferable pattern

This applies to any mechanical-replacement work in the workspace:

| Skill | Manual predecessor | Mechanical successor | Status |
|-------|-------------------|---------------------|--------|
| `/ship` Phase 3 | 12-item check list | `ship_receipt.py` | ✅ Deleted (this session) |
| `/check` | Manual check-state.md | `check_lifecycle.py` manifest + finalizer | Already mechanical |
| `/close` | Manual gate scan | `close_accounting.py` scanner | Already mechanical |
| `/review` | Manual FINDINGS.md | `review` skill's artifact pipeline | Already mechanical |

For future replacements: when building a mechanical generator for any report, delete the manual instructions in the same commit. Don't keep them as reference.

## Falsifier

This finding is wrong if:
- LLMs reliably skip instructions labeled "reference" or "formerly" — they don't (observed in this critique)
- The 12-item list was serving a purpose the script doesn't cover (e.g., edge cases not in the script) — in this case the items should be added to the script, not kept as a parallel manual path
- A future workspace move (different model, different prompting conventions) makes "reference" labels effective as deactivation signals — possible but not observed

## What this means for our workspace

When doing any mechanical-replacement work (replacing LLM-judged steps with code-enforced scripts), the commit that adds the script must also DELETE the manual instructions it replaces. No parallel paths. If historical understanding is needed, link to the git commit diff.

This is now enforced in `/ship` Phase 3 (the 12-item list is deleted). Future mechanical-replacement work in `/handoff`, `/aar`, or other skills should follow the same pattern.

Related: [[mechanical-enforcement-over-behavioral-reminder]] — the parent principle. This concept is the specific application: mechanical enforcement requires being the ONLY path, not the primary path alongside a manual reference.

## Receipts

- `/tp` critique output: subagent 019fb6a2, finding H1 (HIGH severity)
- Fix: commit `85d87bd` — deleted the 42-line reference list from `go/SKILL.md`
- Existing concept: `ship-receipt-mechanical-generation-from-per-check-results.md` — documents the generator design decision
