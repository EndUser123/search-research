---
created: '2026-07-21'
sources:
- Session 019f8155-f901-79a2-9ba1-ac4614db5225 (2026-07-20/21)
- ~/.grok/sessions/P%3A%5C/ directory structure analysis
summary: 'Grok Build subagents get their own unique UUID session IDs (not inherited from parent). State isolation keyed on GROK_SESSION_ID is safe across parent+child.'
tags:
- grok-build
- subagent
- session-id
- state-isolation
- platform-fact
verification: observed
cognitive_load: 2
host: grok
agent: grok
---

# Grok Build subagent session IDs are unique

## Finding

On Grok Build, `spawn_subagent` children get their **own unique UUID** as `GROK_SESSION_ID` — they do NOT inherit the parent's session ID.

## Evidence

Session directory structure at `~/.grok/sessions/<encoded-cwd>/` shows groups of sessions sharing the **first 8 characters** of their UUID (e.g., `019f7d5d-*`) but differing in the full UUID:

```
019f7d5d-0901-74d3-959d-40956f9dc31f  (parent)
019f7d5d-0902-7600-b0f1-1bf52b5b8d9a  (child — different UUID)
019f7d5d-0902-7600-b0f1-1c0e469660e2  (another child — different UUID)
```

The first 8 chars match because Grok's UUID generation uses a **time-based prefix** (the first segment encodes a timestamp). Sessions created at the same time (parent spawning multiple subagents in one response) share this prefix. But the full UUID is unique per process.

## Why this matters

Any plugin or skill that keys state on `GROK_SESSION_ID` (e.g., `pgm-state-<session_id>.json`) is **safe from parent/child collision**. The state file naming convention guarantees isolation:

- Parent: `pgm-state-019f7d5d-0901-74d3-959d-40956f9dc31f.json`
- Child: `pgm-state-019f7d5d-0902-7600-b0f1-1bf52b5b8d9a.json`

No cross-contamination. The [[llm-handoff-best-practices]] "Implications for a solution architect operating a fleet" section presumes exactly this property.

## What it does NOT mean

- Subagents do NOT share the parent's evidence, repair state, or telemetry.
- Subagents do NOT see the parent's `GROK_PLUGIN_DATA` state (each gets its own session-scoped state file).
- The timestamp prefix sharing means you **cannot** use the first 8 chars as a unique key — always use the full UUID.

## Related

- [[grok-build-stop-hook-agent-text]] — Stop hook payload structure for Grok Build
- [[spawn-subagent-slug-session-snapshot]] — subagent dispatch mechanics
- proposal-grounding-monitor ST-3 finding (resolved by this fact)

## Auto-related

- [[grok-build-disabled-hooks-per-hook-layer]]
- [[grok-build-plan-mode-structured-thinking]]
- [[wiki-lifecycle-state-file]]
- [[grok-build-cc-aca-actually-enabled]]
- [[auto-commit-authority-isolation]]

