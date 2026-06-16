# Hook Routing Contract

This environment treats settings-level hook commands as the runtime source of truth.

## Active Registration

Authoritative always-on hooks must be reachable from one of these settings files:

- `C:\Users\brsth\.claude\settings.json`
- `P:\.claude\settings.json`

Plugin hooks that need to run in every session should be registered through a settings command, normally a package-owned router:

```json
{
  "type": "command",
  "command": "python P:/packages/.claude-marketplace/plugins/<plugin>/__lib/router.py <Event>"
}
```

The router may dispatch to package-owned hook files. The router dispatch table, not `hooks/hooks.json`, is the active plugin hook contract until upstream plugin hook loading is reliable again.

## Non-Authoritative Declarations

Do not infer that a hook is active only because a plugin contains `hooks/hooks.json`.

The current upstream issue is that external plugin `hooks.json` files can fail to load or execute. Keep those files empty, generated, or clearly treated as packaging declarations unless the hook is also settings-routed or validated with `/hooks` and debug logs.

## Skill-Scoped Hooks

Skill hooks are only appropriate when the behavior is scoped to that skill or agent lifecycle. They should live in the relevant skill or agent frontmatter, not in global project governance. Global safety, authority, routing, session, and evidence hooks belong in settings-routed routers.

## Enforcement Classes

Use the narrowest effective hook phase:

- `PreToolUse`: blocking safety, authority, file/path, command-intent, and permission decisions.
- `UserPromptSubmit`: prompt classification, routing hints, and request-shape capture.
- `SessionStart` / `SessionEnd`: setup, cleanup, state reconciliation, and health checks.
- `PostToolUse`: observation, validation, telemetry, and feedback; do not rely on it to prevent already-completed actions.
- `Stop` / `SubagentStop`: final response gates, closure checks, and handoff cleanup.

Classify each hook as one of `safety`, `authority`, `routing`, `workflow`, `telemetry`, or `advisory`. Blocking behavior should be limited to `safety` and `authority` hooks unless there is a documented exception.

## Validation Gate

Before claiming a hook is active or inactive, run:

```powershell
python P:\.claude\hooks\active_hook_inventory.py
python P:\.claude\hooks\active_hook_inventory.py --json
```

Then confirm runtime state with `/hooks` or current Claude Code debug logs when the question is whether Claude Code itself loaded the hook in this session.

## Current Known Declarations Outside The Router Path

As of the latest local inventory, there should be no non-empty `hooks.json` declarations outside the settings-router contract.

Historical migrations:

- `cc-aca-safety`, `cc-aca-sdlc`, `prompt-enhancer`, and `search-research` are registered through package-owned routers in `C:\Users\brsth\.claude\settings.json`.
- `cc-lazy-closure-debt` is intentionally local-wrapper owned through `P:\.claude\hooks\Stop_lazy_closure_debt.py` and `P:\.claude\hooks\UserPromptSubmit_modules\lazy_closure_debt.py`; its plugin `hooks.json` is empty to avoid duplicate execution if plugin hook loading starts working again.

If a future inventory reports non-authoritative declarations again, treat them as migration candidates, not confirmed inactive hooks. A hook can still be active through a local wrapper or monolith, so inspect the settings command and wrapper import path before changing behavior.
