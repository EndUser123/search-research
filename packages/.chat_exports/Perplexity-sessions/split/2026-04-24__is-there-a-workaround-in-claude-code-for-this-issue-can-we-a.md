---
title: "Is there a workaround in claude code for this issue?
'
❯ can we add a command to the plugin that invokes the skill, and"
date: "2026-04-24"
mode: "COPILOT"
uuid: "b07f2778-9702-4cc2-9b74-f4a3b1f4304d"
entry_count: 1
---

## Human

Is there a workaround in claude code for this issue?
"
❯ can we add a command to the plugin that invokes the skill, and after a reload-plugins will that be visable?

● Yes. The skill approach gives you /reason_openai_v4.0:reason_openai_v4.0 (double-qualified). A commands/ entry gives you the bare
  /reason_openai_v4.0 you want.

  The plugin already has skills/reason_openai_v4.0/SKILL.md. Adding commands/reason_openai_v4.0.md as a legacy-format command will
  expose /reason_openai_v4.0 directly.

  Let me create it:

  Listed 1 directory (ctrl+o to expand)

● No — adding a commands/ directory won't help. Here's why:

  Plugin skills at skills/<name>/SKILL.md become /plugin-name:skill-name (e.g. /reason_openai_v4.0:reason_openai_v4.0), not bare
  /skill-name. That's a plugin architecture constraint, not a discovery issue.

  A commands/<name>.md file is the legacy equivalent of a skill and works the same way — the slash command would still be
  namespaced.

  What the skill file already gives you:
  - After /reload-plugins, the skill is registered
  - It should be invokable as /reason_openai_v4.0:reason_openai_v4.0

  The confirmed bug (GitHub #21125, #17271): plugin skills don't appear in autocomplete, but they should still be directly invokable
   if you type the full path.

  To test, run this directly:
  /reason_openai_v4.0:reason_openai_v4.0

  If that works but /reason_openai_v4.0 alone doesn't appear in autocomplete suggestions, it's the known bug — not a configuration
  problem with your plugin."

## Assistant

No reliable workaround exists for bare `/reason_openai_v4.0` invocation from plugins in Claude Code, as plugin skills are architecturally namespaced to `/plugin:skill` to avoid conflicts.[1][2]

## Core Issue
Plugin skills in `skills/<name>/SKILL.md` register as `/reason_openai_v4.0:reason_openai_v4.0` post-`/reload-plugins`, per design for namespace isolation across personal/project/plugin scopes. This prevents autocomplete and direct bare-name matching, confirmed as a bug in issues like #21125 (skills missing from autocomplete despite working when fully typed) and #17271 (no autocomplete for plugin skills).[3][2][1]

Legacy `commands/<name>.md` files also namespace under plugins, as both formats merged into the skills system (v2.1.3+), inheriting the prefix constraint. No config or frontmatter (e.g., `name`, `user-invocable`) overrides plugin namespacing; docs explicitly state "Plugin skills use a `plugin-name:skill-name` namespace."[2][4]

## Confirmed Behaviors
- Full path `/reason_openai_v4.0:reason_openai_v4.0` invokes successfully after reload, bypassing autocomplete bug.[5][1]
- Autocomplete omission persists across restarts, updates (e.g., v2.1.110), and cache cleans; `/reload-plugins` updates model context but skips slash index rebuild (#37862).[6]
- Non-plugin skills (e.g., `~/.claude/skills/`) allow bare `/name`, but plugins cannot.

| Location | Namespace | Autocomplete | Post-Reload Visibility |
|----------|-----------|--------------|------------------------|
| Personal/Project | Bare `/skill` | Yes (usually) | Yes |
| Plugin | `/plugin:skill` | Buggy/No[1][7] | Full path only[1] |

## Workarounds Evaluated
**Cache/symlink cleanup**: Fixes duplicates (#29520) but not autocomplete/namespace.[8]
**Restart/full reinstall**: Temporary for some (#21125), but bug recurs; no bare-name fix.[9][1]
**Natural language**: Invoke via "use reason_openai_v4.0 skill" – works globally since skill loads in context, sidestepping slash entirely.
**Custom alias script**: No built-in; external bash wrapper (e.g., alias `/reason_openai_v4.0` → full path) untested/unsupported in CLI.

No evidence of bare-name hack; docs/GitHub emphasize full path as intended UX. File bug if unfiled, or request namespace opt-out (#19445 stale).[8][2]

Next step: Test `/reason_openai_v4.0:reason_openai_v4.0 arg` directly; if works, use it or natural invocation. Uncertainty: Latest unreleased fix possible (issues active Apr 2026).[9]
