---
title: "Spec File Placement: Project Root Convention"
created: 2026-07-31
source: session-20260730
tags: [spec-driven-development, file-placement, project-structure, ship, convention]
summary: >
  Spec files (SPEC.md, PRD.md) belong at the project root of the effort they
  describe — not in a workspace-wide docs/plans directory. Confirmed by both
  GitHub Spec Kit and OpenSpec conventions, plus practitioner reports. The spec
  is the source of truth that /ship verifies against; it must be discoverable
  from the project it governs.
agent: grok
host: both
cognitive_load: 1
verification: multi-source-verified
sources:
  - https://github.com/github/spec-kit (GitHub Spec Kit, 2025)
  - https://openspec.pro/ (OpenSpec, 2025)
  - https://steviee.medium.com/from-prd-to-production-my-spec-kit-workflow-for-structured-development-d9bf6631d647 (Eberle, Sep 2025)
relations:
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: applies-to
---

# Spec File Placement: Project Root Convention

## Decision context

When writing a ship spec for the Chrome ACP effort, the question arose: where
does the spec file go? The `/go execute` path handling suggests
`docs/superpowers/plans/`, and the workspace has a `docs/plans/` directory.
But the spec is for a specific project (Chrome ACP at
`C:\Users\brsth\chrome-acp\`), not for the workspace as a whole.

## The convention

**The spec lives at the project root of the effort it describes.**

Two major spec-driven development frameworks confirm this:

- **GitHub Spec Kit** places `PRD.md` at the project root. The `.specify/`
  directory holds living memory and templates, but the input spec starts at
  the root.
- **OpenSpec** places `openspec/project.md` at the project root for global
  project context.
- **Practitioner (Eberle, Medium):** "I just place it in the project root
  as `PRD.md`."

## Why not in a workspace plans directory

A workspace-wide `docs/plans/` directory mixes specs for unrelated efforts.
When `/ship` runs on a specific project, it needs the spec for *that* project —
not a flat directory of every plan ever written. The project root is where
both humans and tools look first.

## Application to this workspace

| Effort | Project root | Spec location |
|--------|-------------|---------------|
| Chrome ACP | `C:\Users\brsth\chrome-acp\` | `C:\Users\brsth\chrome-acp\SPEC.md` |
| yt-is package | `P:\packages\yt-is\` | `P:\packages\yt-is\SPEC.md` |
| Fleet config | `P:\` | `P:\docs\plans\` (workspace-wide — different case) |

## Falsifier

If `/ship` is modified to scan a workspace-wide spec directory instead of
project-root specs, this convention would need updating. If a spec spans
multiple projects (cross-cutting), a project-root placement may be ambiguous —
but that's a different problem (multi-project specs) that warrants its own
placement rule.
