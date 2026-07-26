---
title: "Delegate to the skill, don't extract its internals"
created: 2026-07-21
source: session-2026-07-21
tags: [skill-design, coupling, delegation, architecture, anti-pattern, maintenance]
summary: >
  When one skill needs a capability another skill provides, delegate to
  that skill — don't extract its internal implementation. The caller should
  never know how the callee implements its job. Extracting internals
  creates coupling: when the callee evolves (new backends, different
  search methods, additional state), the caller misses the improvement
  because it's using a frozen copy of the old implementation.
agent: grok
host: both
cognitive_load: 1
verification: single-source-verified
relations:
  - target: wiki/concepts/skill-enforcement-layers
    type: related
  - target: wiki/concepts/compound-skill-improvement-patterns
    type: related
---

# Delegate to the skill, don't extract its internals

## The pattern

When `/plan` needed to check the wiki for prior decisions before
proposing a plan, the initial implementation hardcoded `qmd search`
inline:

```bash
qmd search "<plan topic>" -c wiki --limit 5 --format cli
```

The user caught the coupling problem immediately: "if we change wiki to
add more backends like session history, wouldn't you miss that
functionality?"

The fix: delegate to `/wiki` instead:

```
/wiki <plan topic>
```

`/plan` inherits whatever search backends `/wiki` currently supports,
without coupling to a specific implementation.

## Why this matters

| Approach | What happens when the callee evolves |
|---|---|
| **Delegate** (`/wiki <topic>`) | Caller automatically gets new backends, methods, state |
| **Extract internals** (`qmd search ...`) | Caller is frozen at the old implementation; misses improvements |

This is the same principle as "don't call private methods" in OOP:
the internal API is an implementation detail that can change without
notice. The skill's invocation interface is the public contract.

## Where this applies

- `/plan` checking the wiki → delegate to `/wiki`, don't call `qmd search` inline
- `/design` Step 5.5 critical friend → delegate to `/tp`, don't inline the two-lens logic
- `/go` running review → delegate to `/review`, don't inline the specialist dispatch
- `/check` building evidence packets → delegate to the preprocessor, don't inline the parsing
- Any skill that needs another skill's capability → invoke the skill, don't copy its code

## The test

If the callee skill adds a new backend or changes its internal method,
does the caller automatically benefit? If yes → delegation. If no →
coupling. Fix it.

## Reference incident

Session 2026-07-21: `/plan` SKILL.md hardcoded `qmd search` for the
wiki grounding check. User pointed out the coupling. Fixed in commit
`62d304b` — replaced inline `qmd search` with `/wiki <topic>` delegation.

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[portfolio-deep-read-transferable-techniques]]
- [[skill-enforcement-layers]]
- [[handoff-pre-compact-problems]]
- [[skill-enforcement-deep-dive]]

