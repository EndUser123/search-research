# AGENTS.md

## Search Topology (read before any existence/absence claim)

`P:\` is a multi-root workspace. Code for one subsystem is split across these
roots - a search scoped to only one of them proves nothing:

| Root | What lives there |
|------|------------------|
| `P:\.claude\hooks\` | User-level hooks (dispatched from `~/.claude/settings.json`) |
| `P:\.claude\scripts\` | Maintenance/audit scripts (e.g. `hooks_audit.py`) |
| `P:\packages\.claude-marketplace\plugins\<name>\` | Plugin SOURCE (canonical). Plugin hooks live in per-plugin `hooks/` or `scripts/` dirs and dispatch via the plugin's `__lib/router.py` |
| `~\.claude\plugins\cache\` | Version-keyed plugin CACHE - generated, never edit; may lag source |
| `P:\.claude\worktrees\`, `P:\worktrees\`, `P:	mp\` | Stale copies/experiments - exclude from truth claims |

**Absence rule:** never claim a file, hook, or module "does not exist" until you
have searched BOTH live roots. Canonical command:

```
rg --files -g "*<name>*" P:/.claude/hooks P:/.claude/scripts P:/packages/.claude-marketplace/plugins
```

(`rg` respects .gitignore, so node_modules/.venv noise is excluded automatically.)
For hook ground truth, prefer running the audit over searching by hand:
`python P:/.claude/scripts/hooks_audit.py --packages P:/packages/.claude-marketplace/plugins`

If a spec names a file you can't find in one root, check the other root before
concluding the spec is wrong.

## Workspace Routing

This `P:\` workspace contains multiple packages. Before acting on a package, read
that package's local instruction files and treat them as the governing guidance
for work under that path.

For `yt-is` work under `P:\packages\yt-is`, read:

- `P:\packages\yt-is\CLAUDE.md`
- `P:\packages\yt-is\AGENTS.md`
- `P:\packages\yt-is\HANDOFF.md`

Do not rely on a parent-workspace prompt or chat summary when package-local
instructions, handoffs, or operation docs exist.

## Review Discipline

For non-trivial analysis, proposals, mechanism investigations, benchmark
interpretations, or decision packets, separate verified facts, measured metrics,
inferences, hypotheses, historical context, and unsupported claims.

Do not promote an inference or hypothesis into an implementation decision, live
run authorization, or `ready_for_parent_review` handoff. If a new explanation is
only inferred, the next allowed action is evidence gathering.
