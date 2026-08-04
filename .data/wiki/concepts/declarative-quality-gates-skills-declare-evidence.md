---
title: "Declarative quality gates: skills declare evidence, Stop hook enforces"
concept_type: "architecture-decision"
created: 2026-08-04
source: session-20260804
tags: [hooks, quality-gates, enforcement, skills, stop-hook, multi-agent, evidence]
summary: >
  Skills declare quality_gates in SKILL.md frontmatter — each gate names a glob
  pattern for an evidence file that must exist on disk when the agent claims
  completion after invoking that skill. The existing Stop hook reads the
  invoked skills' frontmatter, checks whether evidence exists, and blocks
  completion if it's missing. This converts skill instructions from suggestions
  (6-66% activation rate) into mechanically enforced requirements (~100%
  compliance). The design separates enforced skills (with quality_gates) from
  advisory skills (without) — intentional, not a gap. Consumer-side gates
  (/ship requiring /check evidence) are stronger than producer-side gates
  (/check requiring its own output).
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: extends
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Declarative quality gates: skills declare evidence, Stop hook enforces

## Decision context

**The problem:** this session's `/ship` invocation skipped `/check` and `/review`
because the ship receipt had no mechanical gate on skill invocations — only on
tests/lint/types. The agent filled receipt fields with "not run" instead of
actually running the skills. This is the activation gap documented in
[[llm-instruction-non-compliance-activation-gap-2026]]: skills have 6-66%
activation rate because the LLM compresses/skips them under pressure.

**What alternatives were explored:**
- More AGENTS.md rules (behavioral — already shown insufficient per activation gap research)
- Porting the Claude side's full skill-guard plugin (heavyweight execution-state machine)
- UserPromptSubmit pre-computation hook (duplicates work the Stop hook already does)
- Heuristic evidence awareness for non-gated skills (wrong abstraction — convention-based matching is fragile)

**What was chosen:** declarative quality gates with two coupled layers:
1. **Declarative** — skills opt in by declaring `quality_gates` in frontmatter
2. **Mechanical enforcement** — the existing Stop hook checks evidence and blocks

## Key findings

### Consumer-side gates are stronger than producer-side

A consumer declaring what upstream evidence it needs (/ship requiring /check's
check-run.json) is a real constraint — the consumer can't satisfy it without
the upstream actually running. A producer declaring its own output as a gate
(/check requiring check-run.json) is self-referential — the same agent that
ran /check checks whether /check produced output, and can write garbage to
satisfy its own gate.

**Implication:** quality_gates should be added to orchestration skills that
consume upstream evidence (/ship, future /close-check), not to producer skills
(/check, /review).

### Content-based session scoping prevents cross-session contamination

The initial implementation used `glob.glob()` with no session binding — any
session's check-run.json satisfied the gate. The fix uses content-based
filtering: JSON evidence files contain a `session_id` field, and the gate
declares `session_field: "session_id"` to filter by content. Non-JSON evidence
(markdown) cannot be content-filtered and passes through unscooped — a
documented limitation.

This pattern is borrowed from close_accounting.py:619-622 which already does
`manifest.get("session_id")` filtering for /close.

### Mechanical scanner catches the bug class at definition time

A new scanner check (script_scan.py check 8g) flags quality_gates frontmatter
with JSON evidence missing `session_field`. This runs during /skill-dev create
and /skill-dev measure — catching the contamination bug class before it ships,
with ~100% compliance (mechanical enforcement over behavioral reminder).

### Advisory skills are intentional, not a gap

Skills without quality_gates (/tp, /explore, /brainstorming) are advisory by
design — they produce judgment, not checkable artifacts. Forcing artifact
creation on them would be process theater. The enforced-vs-advisory distinction
is the correct axis for deciding which skills get gates.

## What this means for our workspace

- **Adding enforcement to a skill:** add `quality_gates` to SKILL.md frontmatter.
  The Stop hook enforces it immediately — no new hook registration needed.
- **Session-scoping JSON evidence:** declare `session_field: "session_id"` on
  JSON evidence gates. The scanner will warn if you forget.
- **Conditional skills (/handoff, /wiki, /aar):** do NOT gate these. Their
  legitimate outcome can be "nothing needed" — forcing an artifact creates
  perverse incentives.
- **Non-JSON evidence limitation:** markdown evidence (FINDINGS.md) cannot be
  session-scoped via content. Either accept the limitation or embed session
  metadata in the output format.

## How to declare quality gates

```yaml
quality_gates:
  - evidence: "P:/.artifacts/**/check-run.json"
    message: "/check receipt missing — run /check before claiming done"
    session_field: "session_id"          # filter JSON by content session_id
  - evidence: "P:/.artifacts/**/FINDINGS.md"
    message: "/review findings missing — run /review before claiming done"
    # no session_field — markdown can't be content-filtered
```

## Falsifier

This design is wrong if:
- The Stop hook's quality gate check never fires in practice (the invoked_skills
  tracking doesn't work, or the transcript scan misses skill invocations)
- The contamination fix (content-based session scoping) blocks legitimate
  evidence because session_id fields are missing or wrong in JSON artifacts
- The scanner check (8g) produces false positives that block skill creation
- Advisory skills consistently need enforcement that quality_gates can't provide
  (judgment-based compliance that no evidence file can capture)

## Sources

- Session 019fa8f8 (2026-08-04): quality gates system built, contamination bug
  found and fixed, scanner added
- [[llm-instruction-non-compliance-activation-gap-2026]] — activation gap research
- [[multi-terminal-isolation-stale-data-immunity]] — baseline requirements + case study
- /tp critique (glm-5-2, 20 tool calls): found consumer-side vs producer-side
  distinction, cross-session contamination, and /close already having superior enforcement

## Receipts

- `quality_gates_frontmatter.py:check_evidence()` (lines 370-413) — content-based
  session filtering implementation: parses JSON evidence, filters by `session_id`
  content field when `session_field` is declared
- `quality_gates_frontmatter.py:check_quality_gates()` (lines 519-580) — main entry
  point: reads frontmatter, checks evidence, returns QualityGateReport
- `quality_gate.py:_quality_gate_check()` (lines 1095-1133) — Stop hook integration:
  called at all 4 allow-paths (lines 1492, 1522, 1542, 1614)
- `script_scan.py:_check_quality_gates_session_scoping()` (lines 610-680) — scanner
  check 8g: flags JSON evidence gates missing session_field
- `ship/SKILL.md` frontmatter (lines 17-22) — first consumer: declares
  quality_gates with session_field on check-run.json
- `close_accounting.py:scan_check_receipts()` (line 541+) — existing pattern for
  session-scoped evidence scanning (manifest.get("session_id") filtering)

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[claude-code-hooks-system]]
- [[claude-code-skills-and-mcp-integration]]

