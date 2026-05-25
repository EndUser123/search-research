---
description: "Debugging discipline: green state axiom, runtime mismatch diagnosis, observation hierarchy"
alwaysApply: false
---

# Debugging Protocol

## Green State Axiom

The codebase was working before the change. If something breaks after an edit:
1. The edit caused it — investigate the edit first
2. Revert to verify: `git stash` or `git checkout -- <file>`
3. Only after confirming the edit is the cause, investigate why

## Runtime Mismatch Diagnosis

When the code looks correct but behavior is wrong:
1. **Check what's actually running** — is it the code you think it is?
2. **Check the runtime config** — settings.json, environment variables, plugin cache
3. **Check the execution path** — is the hook even being called? Check logs.
4. **Check the data** — is the input what you expect? Print/log it.

Order matters: don't debug logic until you've confirmed the runtime matches the source.

## User Observation Hierarchy

When the user reports a problem, trust their observation but verify their diagnosis:

| Priority | Source | Trust Level |
|----------|--------|-------------|
| 1 | User's direct observation ("it crashed") | High |
| 2 | User's diagnosis ("because of X") | Medium — verify |
| 3 | User's suggested fix ("change Y to Z") | Low — investigate first |

## Broken Symlink Handling

On Windows, broken junctions or symlinks silently fail. If a file should exist but doesn't:
1. Check if it's a junction: `fsutil reparsepoint query <path>`
2. Check if the target exists
3. Re-create the junction if the target is valid but the link broke
