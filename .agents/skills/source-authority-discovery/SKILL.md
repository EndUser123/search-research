---
name: source-authority-discovery
description: Build an evidence-backed inventory of existing implementations, callers, registrations, state/default consumers, caches, tests, worktrees, and competing plans before proposing or implementing non-trivial changes.
---

# Source Authority Discovery

Use this skill before planning, reviewing, or implementing work that could
change an existing capability, hook, skill, plugin, entrypoint, default,
state format, lifecycle, worktree, or orchestration path.

## Required workflow

1. Read applicable `AGENTS.md`, `CLAUDE.md`, package handoffs, and current
   operating documents.
2. Run the bundled audit with explicit scopes and target tokens. On Windows,
   use PowerShell and the workspace Python runtime:

   ```powershell
   python P:\.agents\skills\source-authority-discovery\scripts\discovery_audit.py `
     --scope P:\.claude `
     --scope P:\packages\.claude-marketplace\plugins\cc-skills-sdlc `
     --scope P:\.agents `
     --scope P:\docs `
     --target go_safe `
     --target orchestrate `
     --target worktree `
     --target active-plan `
     --target GO_WORKTREE_ROOT `
     --output P:\tmp\source-discovery.json `
     --fail-on-conflict
   ```

3. Read every matching implementation, caller/registration, test, cache or
   generated copy, active plan, and worktree record reported by the audit.
4. For every proposed new file, prove that no existing file already owns the
   same role. For every proposed default change, inspect every reader and
   writer of that value, including lifecycle and cleanup consumers.
5. Classify each copy as canonical source, runtime state, cache, generated
   output, worktree, fixture, or historical artifact.
6. If the audit returns `needs_review` or `blocked`, do not create files,
   change defaults, delete compatibility code, or declare a plan ready. First
   resolve the overlap or report the specific blocker.
7. Include the discovery report path, revision, scopes, conflicts, and
   intentionally uninspected areas in the review or plan packet.
8. Re-run the audit at implementation start and before completion. Compare
   the source, active-plan, worktree, and cache findings with the first report.

## Hard stops

- Do not infer absence from a filename or one-root search.
- Do not create a wrapper or replacement until all similarly named entrypoints
  and their contracts are mapped.
- Do not change one occurrence of a default until all occurrences and lifecycle
  consumers are classified.
- Do not proceed when an active plan overlaps the proposed files or behavior;
  reconcile ownership first.
- Do not treat a plan, handoff, cache, test result, or another model's review
  as proof of runtime activation or source completeness.

## Output contract

Report a compact table with:

`artifact | classification | owner/caller | state/default consumers | tests | cache/generated copies | conflict | evidence`

Separate verified facts, measured results, inferences, hypotheses, and
unknowns. The audit is a discovery gate, not permission to modify production
configuration or to discard concurrent work.
