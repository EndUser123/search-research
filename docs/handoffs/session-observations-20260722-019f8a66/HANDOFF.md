---
thread_id: obs-019f8a66
parent_handoff_path: P:/docs/handoffs/skill-consolidation-20260722/HANDOFF.md
current_session_id: 019f8a66-ce7a-71c3-8655-8d6ee4d2ee4d
current_terminal_id: console
produced_at: 2026-07-22T16:20:00Z
status: closed
handoff_type: session_observations
---

# Session observations — 2026-07-22 (019f8a66)

## Observations

1. **cc-* plugins disabled on Grok Build is a constraint, not a bug.** The
   active-surface snapshot confirms all 18 cc-* plugins are in
   `~/.grok/config.toml [plugins] disabled`. Skills are discoverable via
   `claude.skills: ON` compat flag, but hooks/routers/scripts are inactive.
   This means any plan that depends on plugin infrastructure (cache rebuild,
   version bump, router dispatch) is wrong for this host. Plan consolidation
   work must happen at the `~/.grok/skills/` layer.

2. **The DEPRECATED-description convention is the established pattern for
   retiring Grok-native skills.** Both `check-work` and `code-review` at
   `~/.grok/skills/` use `DEPRECATED — use /X instead` in their frontmatter
   description. This is simpler and safer than Move-Item archiving (no Windows
   lock risk, no scanner-exclusion issues). Future skill retirements should
   follow this convention unless there's a specific reason not to.

3. **`claude -p` CLI is Claude Code only, absent on Grok Build.** The
   description-optimization backend in skill-write's `run_loop.py` depends on
   `claude -p`. Any skill consolidation that claims "description optimization
   captured" must mark it `pending + DEFERRED` on Grok Build, not `captured`.

4. **`index_skills.py` has no path-exclusion logic.** Confirmed by grep: the
   scanner doesn't exclude any directory. Archiving skills to a subdirectory
   without updating the scanner would leave them visible in the catalog. The
   DEPRECATED-description approach sidesteps this entirely.

## Seeds for future work

- The /tp subagent (17 tool calls, parent-inherited model) produced a
  high-quality critique of the skill consolidation plan. The parent-inherited
  model limitation was disclosed but the critique still caught 3 load-bearing
  issues. Consider whether cross-model /tp (using `/agy` or `/codex`) would
  add value for architectural plan reviews, or whether the fresh-context
  property alone is sufficient.
