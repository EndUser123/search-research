---
title: "Lifecycle skill remediation modes: auto-act vs surface-only"
created: 2026-08-01
source: session-019fb937 (close-check Phase 3 design)
sources:
  - internal: ~/.grok/workflows/close-check.rhai (Phase 3 Remediate)
  - internal: ~/.grok/skills/capture/SKILL.md (remediation_mode: auto-act)
  - internal: ~/.grok/skills/friction/SKILL.md (remediation_mode: surface-only)
  - internal: ~/.grok/skills/handoff/SKILL.md (remediation_mode: auto-act)
  - internal: ~/.grok/skills/trace/SKILL.md (remediation_mode: surface-only)
  - internal: ~/.grok/skills/wiki/SKILL.md (remediation_mode: auto-act)
tags: [lifecycle-skills, remediation, close-check, skill-graph, auto-act, surface-only]
agent: grok
host: both
cognitive_load: 1
verification: single-source-verified
summary: >
  Lifecycle skills are classified by how close-check should handle their
  output: auto-act (write findings durably without operator approval) or
  surface-only (report findings for operator decision). This tag lives in
  each skill's frontmatter as remediation_mode. Close-check Phase 3 reads
  this tag to decide whether a skill's output goes directly to durable
  artifacts or surfaces in the Next steps section for human review.
relations:
  - target: wiki/concepts/analysis-over-action-knowledge-capture-without-application.md
    type: related
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: related
---

# Lifecycle skill remediation modes: auto-act vs surface-only

## Decision context

When close-check Phase 3 runs all lifecycle skills, it needs to know which
skills can safely write their output durably (wiki concepts, handoffs, AGENTS.md
rules) and which produce findings that need operator review before action (code
problems, friction patterns requiring fixes). The distinction prevents two
failure modes: (1) auto-fixing code problems the operator should review, and
(2) merely reporting knowledge that should have been captured durably.

## The classification

| Skill | remediation_mode | Why | What close-check does with output |
|---|---|---|---|
| `/capture` | `auto-act` | Writes wiki concepts, AGENTS.md rules, handoffs — all reversible knowledge artifacts | Output goes directly to durable files |
| `/handoff` | `auto-act` | Writes handoffs for open work — operational scaffolding, not code changes | Output goes directly to handoff files |
| `/wiki` | `auto-act` | Writes wiki concepts + logs — durable knowledge, validated before write | Output goes directly to wiki concepts |
| `/trace` | `surface-only` | Finds logic errors in code — does NOT fix them; operator must review and decide | Output surfaces in Next steps section |
| `/friction` | `surface-only` | Reports friction patterns + routes to handoffs, but actual fixes need operator decision | Output surfaces in Next steps section |

## The `remediation_mode` frontmatter field

Every lifecycle skill declares its mode in SKILL.md frontmatter:

```yaml
remediation_mode: auto-act    # or: surface-only
```

This is a skill-graph property, not a close-check-specific config. Any
orchestrator that runs lifecycle skills in a pipeline can read this field
to determine whether the skill's output needs human review.

## How close-check uses it

Close-check Phase 3 hardcodes the split (for reliability — it doesn't depend
on reading 5 skill files at runtime). But the frontmatter field is the
authoritative source. If the hardcoded split and the frontmatter disagree,
the frontmatter wins (a validator should check this).

## Falsifier

This classification is wrong if:
- An auto-act skill writes something that should have needed operator review (e.g., /capture writes a wrong AGENTS.md rule)
- A surface-only skill's output could have been safely auto-acted (e.g., /trace finds a trivial typo that doesn't need review)

The first case is mitigated by the skills' own quality gates (validator, cold-read review). The second case is acceptable — false negatives (surfacing when auto-act would have been fine) are safe; false positives (auto-acting when review was needed) are dangerous.

## What this means for our workspace

New lifecycle skills should declare `remediation_mode` in their frontmatter.
Skills that primarily produce durable knowledge artifacts (wiki, rules,
handoffs) are `auto-act`. Skills that primarily produce findings requiring
human judgment (code reviews, friction analysis, security audits) are
`surface-only`. When in doubt, choose `surface-only` — it's the safe default.
