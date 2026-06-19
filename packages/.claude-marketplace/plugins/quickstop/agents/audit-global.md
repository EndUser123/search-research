---
name: audit-global
description: "Audits global Claude Code configuration (~/.claude/) against expert knowledge. Dispatched by /claudit Phase 2."
tools:
  - Read
  - Grep
  - Bash
maxTurns: 30
model: sonnet
---

# Audit Agent: Global Configuration

See AGENTS_REFERENCE.md for full documentation.
