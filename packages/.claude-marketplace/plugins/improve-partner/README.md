# improve-partner plugin

Improvement partner plugin with `/improve` as the central manual workflow and hooks that mostly suggest, queue, and surface evidence rather than force behavior.

> **Local-fork status (Option A′):** `/improve` + 3 specialist agents are live.
> The 4 hooks ship **inert + unwired**, gated by `config.json` `hooks.enabled`
> (default `false`) and dispatched via `__lib/router.py` (NOT registered in the
> global `settings.json` yet). To enable, refactor, or delete the hooks, see
> **HOOKS_AVAILABLE.md** and tracker task **#1052**. The upstream dispatch is
> preserved verbatim in `hooks/hooks.original.json`.


## Included
- `.claude-plugin/plugin.json`
- `config.json`
- `skills/improve/SKILL.md`
- `hooks/hooks.json`
- `scripts/classify_domain.py`
- `scripts/capture_artifact_signal.py`
- `scripts/user_prompt_signal.py`
- `scripts/stop_review_gate.py`
- `scripts/subagent_stop_postprocess.py`
- `scripts/external_review_adapter.py`
- `agents/prompt-specialist.md`
- `agents/workflow-specialist.md`
- `agents/hook-plugin-specialist.md`

## Behavior
- `/improve` is the primary improvement/thought-partner interface.
- `UserPromptSubmit` captures review intent.
- `PostToolUse` captures artifact and error/timing signals.
- `Stop` evaluates the session, writes a review request artifact when warranted, and by default returns an **allow + suggestion** decision instead of blocking.
- `SubagentStop` stores delegated-review payloads for later inspection.

## Default posture
This version defaults to **suggest mode**.
That means hooks help notice meaningful work and recommend review, but they do not take control away from the user.

## Configuration
`config.json` controls the posture:
- `mode: "suggest"` -> allow stop, emit suggestion, queue artifact.
- `mode: "queue-only"` -> allow stop, queue artifact, minimal messaging (future easy extension).
- `mode: "force"` -> block stop and require follow-on review.

Current default:
```json
{
  "mode": "suggest",
  "threshold": 5,
  "cooldown_seconds": 900,
  "max_files": 12,
  "allow_force_mode": true
}
```

## Hardening retained
- Changed-file extraction from tool payloads.
- File-path severity weighting for hooks/config/skills/tests/source changes.
- Cooldown logic to avoid repeated Stop-hook loops.
- Review request artifacts include `changed_files`, sampled `read_files`, `error_count`, and deterministic `domain_hint`.
- Review is not triggered only because improvement language appeared; meaningful changed artifacts still matter.
