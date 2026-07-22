---
title: "Grok permission deny rules as cross-host protection"
created: 2026-07-20
source: session-2026-07-20
tags: [permission, deny-rules, config-toml, grok-build, cross-host, host-surface, config-pattern, fleet-coordination]
summary: >
  Grok Build's native permission system supports path-glob `deny` rules in
  `~/.grok/config.toml` `[permission]` section. `deny` always wins — even in
  `always-approve` permission mode, even against a more-specific `allow`.
  This makes it the correct layer for cross-host protection on a multi-host
  workspace: deny rules on `P:/.claude/**`, `~/.claude/**`, and
  `P:/packages/.claude-marketplace/**` prevent the Grok agent from editing
  Claude Code's infrastructure while preserving read access for context.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
relations:
  - target: wiki/concepts/host-surface-boundary
    type: refines
    reciprocal: related
  - target: wiki/concepts/grok-build-disabled-hooks-per-hook-layer
    type: related
---

# Grok permission deny rules as cross-host protection

## Summary

Grok Build has a native permission system with three rule actions on path
globs: `deny`, `ask`, `allow`. For cross-host protection (stopping the Grok
agent from editing Claude Code's tree), `deny` is the only correct choice
because it's the only action that reliably blocks in `always-approve` mode.
`ask` rules are silently skipped for Edit/Write tools in always-approve.

## The mechanism

```toml
# ~/.grok/config.toml
[permission]
deny = [
    "Edit(P:/.claude/**)",
    "Edit(C:/Users/brsth/.claude/**)",
    "Edit(P:/packages/.claude-marketplace/**)",
]
```

Source documentation: `~/.grok/docs/user-guide/22-permissions-and-safety.md`.

## Why `deny`, not `ask`

Counter-intuitive but critical: `ask` looks like the "prompt for permission"
UX most operators want, but it requires switching off `always-approve` mode —
which means **every edit I make everywhere** starts prompting the operator.
Fleet-wide friction for a `.claude/`-scoped concern.

| Action | Works in `always-approve`? | Requires mode change? | UX when triggered |
|---|---|---|---|
| `deny` | **Yes** — always wins | No | I see "denied" and stop |
| `ask` | No — silently skipped for Edit/Write | Yes (switch to `default`) | Operator prompted per-action |
| `allow` | Yes | No | Approved silently |

`deny` is the surgical tool. I try to edit `.claude/`, hard-blocked, I adapt
and route the proposal through the operator. Normal workflow is untouched.

## What the deny rules catch

- `search_replace` and `write` tool calls on any file under the three trees
- **Bash commands that write to files in those trees** — per the docs,
  `Read` and `Edit` deny rules additionally apply to file paths that shell
  commands touch. `python -c "Path('P:/.claude/...').write_text(...)"` is
  blocked by the same rule. No indirect-write bypass.
- All Claude plugin source, version-keyed cache, and marketplace paths
  (covered by the three globs)

## What the deny rules do NOT catch

- **Reads.** `read_file`, `grep`, `list_dir` still work on protected trees —
  only writes are blocked. The Grok agent can still load `.claude/CLAUDE.md`
  for context, read `.claude/rules/*.md` for guidance, inspect `.claude/hooks/`
  to understand Claude's enforcement. Read-only observation remains.
- **MCP tool writes.** If an MCP server can write to `.claude/` paths, the
  `Edit(...)` deny rule may not catch it — MCP tools have their own rule
  namespace (`MCPTool(...)`). No current MCP server has filesystem write
  access, so this is theoretical as of 2026-07-20.
- **Symlink traversal edge cases.** Shell-level path check resolves symlinks;
  direct tool check does not. Low risk on Windows where symlinks are rare.

## How to lift for a specific edit

Two workflows when the operator genuinely wants a Grok session to make a
Claude-side edit:

1. **Operator makes the edit directly** (lowest friction for one-line fixes)
2. **Narrow `allow` rule, I edit, operator removes it:**
   ```toml
   [permission]
   allow = ["Edit(P:/.claude/hooks/Some_File.py)"]
   deny = [
       "Edit(P:/.claude/**)",
       "Edit(C:/Users/brsth/.claude/**)",
       "Edit(P:/packages/.claude-marketplace/**)",
   ]
   ```
   Per the docs, `deny` wins over `allow` except when the `allow` is more
   specific — the narrow path-specific allow overrides the broad tree deny
   for that one file. Two operator turns total (add allow, remove allow).

## Why not a hook

A natural proposal: `PreToolUse` hook that blocks edits to `.claude/` paths.
Wrong for two reasons:

1. **Hooks fail open.** Per `~/.grok/docs/user-guide/10-hooks.md`: "if a hook
   script crashes, times out, or is missing, the tool call proceeds as if
   the hook had allowed it." Permission deny rules are evaluated before
   hooks and don't fail open.
2. **The permission system is the right layer.** Path-glob deny rules are
   purpose-built for "never let this tool touch this tree." A hook is for
   dynamic decisions (e.g., "block chained commands containing `rm -rf`");
   static path protection belongs in declarative config.

## Tamper-resistance caveat

The rules live in `~/.grok/config.toml` — which is the Grok agent's own
surface. The agent could theoretically edit the config to remove a deny
rule. That would be:
- Immediately visible in the transcript
- A clear "agent is bypassing the guardrail" signal
- An action the operator would see and could revert

Not cryptographic protection. Converts a silent violation into a loud one.

For true tamper-resistance, the docs say rules can also live in
`/etc/grok/requirements.toml` (root-owned, outside the user home dir).
Requires admin elevation to edit. Overkill for a single-user Windows host
where the operator is watching the transcript.

## Load timing — critical caveat

From `~/.grok/docs/user-guide/22-permissions-and-safety.md`:

> "Permission rules from every source are read once, when a session starts.
> Changes apply to the next session."

Mid-session edits to `config.toml` apply to the next session, not the
current one. The operator should be aware: if deny rules are added during
session N, session N can still technically violate them. Session N+1 onward
is protected. The agent should not exploit this gap — if asked to make a
cross-tree edit in session N after the rules are added, route it through
the operator as if the rules were already active.

## Cross-host symmetry (informational, not prescriptive)

The same pattern applies in reverse: Claude Code sessions on this workspace
should not edit `~/.grok/` or `P:/.grok/`. The `P:/AGENTS.md` host-runtime
table encodes this but it's advisory. A symmetric deny rule in Claude's
`settings.json` would provide the same mechanical guard:

```json
{
  "permissions": {
    "deny": [
      "Edit(C:/Users/brsth/.grok/**)",
      "Edit(P:/.grok/**)"
    ]
  }
}
```

Claude-side setup is the operator's call. This page documents the Grok-side
implementation; the Claude-side analog is noted for symmetry.

## Falsifier

If the deny rules cause a legitimate workflow to break — e.g., a shared
artifact that legitimately lives under `.claude/` and both hosts need to
write — the boundary is drawn too tightly. As of 2026-07-20, shared
artifacts live under `P:/docs/` and `P:/.data/wiki/`, not under `.claude/`.

If a Grok session finds a way to write to a protected tree despite the
rules (e.g., via an MCP server, via a Bash redirect the path check doesn't
catch, via symlink traversal), the rule globs or the path-checker need
tightening. Report the bypass vector in this page's next revision.

If `always-approve` mode is ever changed such that `deny` rules no longer
win (would be a breaking change to the documented semantics), the entire
approach collapses and an alternative layer is needed (sandbox, OS-level
ACLs, or a wrapper around the agent runtime).

## Sources

- Documentation: `~/.grok/docs/user-guide/22-permissions-and-safety.md`
- Documentation: `~/.grok/docs/user-guide/10-hooks.md` (fail-open semantics)
- Implementation: `~/.grok/config.toml` `[permission]` section (added 2026-07-20)
- Companion concept: [[host-surface-boundary]] — the mental model this
  guard enforces mechanically

## Related

- [[host-surface-boundary]] — the mental model; this page is the mechanical
  implementation for the Grok side
- [[grok-build-disabled-hooks-per-hook-layer]] — adjacent config pattern
  (hook-level disable vs path-level deny; different mechanisms, same layer)

## Auto-related

- [[host-surface-boundary]]
- [[grok-build-disabled-hooks-per-hook-layer]]
- [[grok-build-cc-aca-actually-enabled]]
- [[grok-build-runtime-docs-divergence]]
- [[grok-build-plan-mode-structured-thinking]]

