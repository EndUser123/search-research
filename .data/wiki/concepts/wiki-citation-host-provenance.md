---
title: "Wiki citation host provenance — cross-host tag"
created: 2026-07-18
tags: [decision, wiki, citation, host-provenance, cross-host, convention]
host: both
agent: grok
verification: local-only
cognitive_load: 1
summary: >
  Wiki concepts should declare host applicability in frontmatter (host: grok | claude | both)
  so future sessions know whether the finding transfers across hosts.
---

# Wiki citation host provenance

## Rule

Wiki concept frontmatter should include `host:` field:
- `host: grok` — finding applies to Grok Build only
- `host: claude` — finding applies to Claude Code only
- `host: both` — finding is host-agnostic

When citing a wiki concept from AGENTS.md or a handoff, note the host tag if it's not `both`.

## Relation

Companion to [[skill-host-applicability-convention]] — same pattern applied to wiki concepts instead of skills.

## Falsifier

Wrong if all wiki findings are host-agnostic. Test: check if Grok-Build-specific findings (hook payload formats, compat flags) are useful to Claude Code sessions.

## Relations

- [[skill-host-applicability-convention]]
