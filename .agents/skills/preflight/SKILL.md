---
name: preflight
description: Build an evidence-backed inventory of existing implementations, callers, registrations, state/default consumers, caches, tests, worktrees, and competing plans before proposing or implementing non-trivial changes.
provides: [evidence-backed-inventory]
domain: discovery
---

# Preflight

(Formerly `source-authority-discovery`; renamed 2026-07-20 per ADR-009 follow-on. Skill identity is unchanged — same audit, same contract, same outputs.)

Use this skill before planning, reviewing, or implementing work that could
change an existing capability, hook, skill, plugin, entrypoint, default,
state format, lifecycle, worktree, or orchestration path.

## Required workflow

1. Read applicable `AGENTS.md`, `CLAUDE.md`, package handoffs, and current
   operating documents.
2. Run the bundled audit with explicit scopes and target tokens. On Windows,
   use PowerShell and the workspace Python runtime:

   ```powershell
   python P:\.agents\skills\preflight\scripts\discovery_audit.py `
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
4. **Constraint audit (the step that catches "read-only"-class oversights).**
   For each neighboring plan, doc, skill, ADR, or `CLAUDE.md`/`AGENTS.md` the
   inventory surfaced in steps 2–3, read its declared **constraints / invariants
   / global-constraints / self-review checklist / "must remain X" rules**. Do
   NOT skip constraint blocks to reach task-level content — constraint blocks
   are often above the section you're cross-referencing for edit overlap, and
   skipping them is the failure mode this step exists to prevent.

   For each declared constraint, check whether the proposed change:
   - **violates** it (direct conflict — e.g., adding a write path to something declared "read-only")
   - **stresses** it (expands the surface the constraint bounds)
   - **ambiguates** it (makes the constraint's wording misleading)

   Surface conflicts as findings in the discovery packet, NOT as silent
   hand-edits to the neighboring artifact. Each conflict entry carries:
   - `citing_artifact` (path + line)
   - `constraint_text` (verbatim quote)
   - `proposed_change` (one-line summary)
   - `conflict_class` (`violation | stress | ambiguity`)
   - `resolution_options` (≥2, e.g., "fix constraint wording," "narrow the change," "explicit exception")

   **Anti-pattern this step exists to prevent** (session 2026-07-19): the
   orchestrator remediated a `/red-team` silent-no-write incident by adding
   `__lib/incidents.py` write paths (FM-4) and a host-boundary doc. The
   neighboring plan at `docs/superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md`
   declared a global constraint "`/red-team` remain read-only." The orchestrator
   read the plan's Task 4 Step 4 to check for edit overlap, skipped the
   constraint block four lines above, and shipped changes that expanded
   `/red-team`'s write surface. The conflict was invisible until the user
   asked "do specialists have to be able to write files?" A constraint audit
   at discovery time would have surfaced it before any code landed.
5. For every proposed new file, prove that no existing file already owns the
   same role. For every proposed default change, inspect every reader and
   writer of that value, including lifecycle and cleanup consumers.
6. Classify each copy as canonical source, runtime state, cache, generated
   output, worktree, fixture, or historical artifact.
7. If the audit returns `needs_review` or `blocked`, do not create files,
   change defaults, delete compatibility code, or declare a plan ready. First
   resolve the overlap or report the specific blocker. **A constraint
   conflict counts as `blocked` until resolved** — pick a resolution option
   and either apply it or surface it to the operator before proceeding.
8. Include the discovery report path, revision, scopes, conflicts, constraint
   audit findings, and intentionally uninspected areas in the review or plan
   packet.
9. Re-run the audit at implementation start and before completion. Compare
   the source, active-plan, worktree, and cache findings with the first report.

## Hard stops

- Do not infer absence from a filename or one-root search.
- Do not create a wrapper or replacement until all similarly named entrypoints
  and their contracts are mapped.
- Do not change one occurrence of a default until all occurrences and lifecycle
  consumers are classified.
- Do not proceed when an active plan overlaps the proposed files or behavior;
  reconcile ownership first.
- **Do not skip a neighboring artifact's constraint/invariant block to reach
  its task or file-map content.** Constraint blocks are the highest-signal
  part of the artifact for discovery purposes — they declare what the change
  must NOT break. If the artifact has a "Global Constraints," "Invariants,"
  "Self-review checklist," or equivalent section, read it before any other
  section.
- Do not treat a plan, handoff, cache, test result, or another model's review
  as proof of runtime activation or source completeness.

## Output contract

Report a compact table with:

`artifact | classification | owner/caller | state/default consumers | tests | cache/generated copies | conflict | evidence`

Plus a **constraint audit table** (new — required when neighboring plans/docs/ADRs were inventoried):

`citing_artifact | constraint_text (verbatim) | proposed_change | conflict_class (violation/stress/ambiguity) | resolution_options | evidence`

If no constraints were found in any neighboring artifact, say so explicitly:
`Constraint audit: no declared constraints found in <list of artifacts inspected>.`

Separate verified facts, measured results, inferences, hypotheses, and
unknowns. The audit is a discovery gate, not permission to modify production
configuration or to discard concurrent work.
