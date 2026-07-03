# HOOKS_AVAILABLE.md — improve-partner hook inventory & enable/refactor guide

> **Status (as shipped):** The 4 hooks are **present but inert and unwired**.
> `hooks/hooks.json` is `{"hooks": {}}` (dispatch invariant). The original
> upstream dispatch is preserved verbatim in `hooks/hooks.original.json`.
> The single gate is `__lib/router.py`, toggled by `config.json`
> `hooks.enabled` (default `false`). Nothing is registered in the global
> `P:/.claude/settings.json`.
>
> See tracker task **#1052** for the enable/refactor/delete decision.

## Posture: advisory by default

`/improve` and its hooks are **suggest-only by default**. This matches
`SKILL.md` `enforcement: advisory`:

- `/improve` itself never blocks actions; it produces review artifacts and
  recommendations.
- The hooks, **if ever enabled**, default to `config.json` `mode: "suggest"`
  (allow + emit a suggestion), not `force`. `allow_force_mode: true` exists but
  is gated by `force_only_when` (explicit opt-in only) — there is no path where
  they block without an explicit user action.
- No strict/blocking guard is warranted here because there is no deterministic
  safety or contract condition these hooks test. (`stop_review_gate.py`'s
  suggestion message is `/improve` self-promotion — flagged for cleanup as part
  of the #1052 decision, not enabled today.)

Hooks left inert (not wired, `hooks.enabled: false`) — see #1052 before
changing this. No active hook was removed in the hardening pass because none are
active.

## What ships live now
- `/improve` skill (`skills/improve/SKILL.md`) — manual improvement/thought-partner.
- 3 specialist agents (`agents/*.md`) — prompt, workflow, hook/plugin.

These reference **none** of the hook scripts; they are self-contained.

## The 4 hooks (present, gated off, NOT wired)
All route through `__lib/router.py <EventName>` and only fire when
`config.json` → `hooks.enabled: true`.

| Event | Script | What it does | Default posture |
|------|--------|--------------|-----------------|
| `UserPromptSubmit` | `scripts/user_prompt_signal.py` | Captures "review intent" from the prompt; accumulates session signal state. | Allow + record |
| `PostToolUse` | `scripts/capture_artifact_signal.py` | Extracts changed-file paths + error/timing signals from tool payloads; severity-weights hooks/config/skills/tests/source. | Allow + record |
| `Stop` | `scripts/stop_review_gate.py` | Evaluates accumulated signals; if threshold met (default 5), writes a review-request artifact under `.review-queue/` with `changed_files`, sampled `read_files`, `error_count`, deterministic `domain_hint`. Returns **allow+suggestion** (suggest mode) or block (force mode). | Suggest (allow+suggest) |
| `SubagentStop` | `scripts/subagent_stop_postprocess.py` | Stores delegated-review payloads for later inspection. | Allow + record |

Config knobs (`config.json`): `mode` (`suggest` | `queue-only` | `force`), `threshold` (5), `cooldown_seconds` (900), `max_files` (12), `allow_force_mode` (true).

## Overlap with the existing stack (the rationalization target)
This is why the hooks are inert pending review — they duplicate several live systems:

| improve-partner hook | Existing system that covers similar ground |
|---|---|
| `Stop` review gate | semantic-critic `Stop.py` aggregator; proposal-critique-gate (live blocking self-review); cc-aca-sdlc review gates; lazy-closure-debt Stop gate; cc-skills-sdlc review skills |
| `PostToolUse` artifact capture | cc-aca-observability PostToolUse router; read-tracker PostToolUse on Read |
| `UserPromptSubmit` intent capture | existing UserPromptSubmit injectors (8 UPS hooks per model-tier-gating) |
| `SubagentStop` postprocess | the built-in SubagentStop LLM evaluator + cc-aca-* SubagentStop routers |

## What is genuinely novel (not in the current stack)
Carry these into whichever decision the review reaches:
1. **Deterministic `domain_hint` classification** (`scripts/classify_domain.py`) — routes review by artifact domain without an LLM call.
2. **File-path severity weighting** (hooks/config/skills/tests/source) in `capture_artifact_signal.py`.
3. **Review-request artifact shape** — `changed_files` + sampled `read_files` + `error_count` + `domain_hint`, written to `.review-queue/`.
4. **Cooldown logic** to prevent Stop-hook re-loops (900s default).

## To ENABLE (after the #1052 review decides to)
Two steps:

**1. Flip the gate** in `config.json`:
```json
"hooks": { "enabled": true }
```

**2. Wire the router** into `P:/.claude/settings.json` (one entry per event, matching the snapshot/skill-guard convention). Add inside each event's `hooks` list:
```jsonc
// UserPromptSubmit
{ "type": "command", "command": "python \"P:/packages/.claude-marketplace/plugins/improve-partner/__lib/router.py\" UserPromptSubmit", "timeout": 5 }
// PostToolUse
{ "type": "command", "command": "python \"P:/packages/.claude-marketplace/plugins/improve-partner/__lib/router.py\" PostToolUse", "timeout": 5 }
// Stop
{ "type": "command", "command": "python \"P:/packages/.claude-marketplace/plugins/improve-partner/__lib/router.py\" Stop", "timeout": 10 }
// SubagentStop
{ "type": "command", "command": "python \"P:/packages/.claude-marketplace/plugins/improve-partner/__lib/router.py\" SubagentStop", "timeout": 8 }
```

Then `/reload-plugins` (or restart). The gate keeps them no-op until step 1 is done, so it is safe to wire the settings.json entries first and flip config later.

## Why not wired by default
`PostToolUse` fires on every tool call. Even a no-op Python startup (~30–50 ms on Windows) per call adds tax to an already-heavy hook stack for hooks that may be deleted after review. Zero-cost-until-decided wins. Revisit in task **#1052**.

## Rollback
Set `hooks.enabled: false` (instant) and/or remove the 4 settings.json entries (full uninstall of dispatch). The plugin's `/improve` skill + agents keep working either way.
