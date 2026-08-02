---
title: "harvest CLI not on PATH — direct invocation via python -m"
created: 2026-08-01
source: session-019fbf02-d3dd-7f72-9ad2-4538790c0a82
tags: [harvest, path, python-m, friction, capture-gap, agent-obligation-tracking]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Chat transcript (harvest CLI fail sequence, session 019fbf02)
  - P:/.data/harvest/pending/ (1 file from prior session — tp-session-019fb926.json, 7/31/2026)
  - P:/.data/harvest/triaged/ (3 files from today's session)
  - P:/.data/harvest/events/ (5 JSON files modified 3:03-3:09 PM today)
relations:
  - target: wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md
    type: parallel (PowerShell `python -m` wrapper behavior)
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related
---

# harvest CLI not on PATH — direct invocation via python -m

## What happened

During session 019fbf02, attempting to invoke `harvest show --top 5` and `harvest scan-handoffs` produced:

```
harvest: The term 'harvest' is not recognized as a name of a cmdlet, function, script file, or operable program.
```

`where.exe harvest` returned `INFO: Could not find files.` Direct directory inspection confirmed the obligation store is intact (`P:/.data/harvest/{pending,triaged,events,claims}/`), but the **CLI driver** is not on PATH.

## Root cause

[UNKNOWN — to be verified] The harvest obligation-tracker CLI is installed as a Python module but its console-script entry point was either not registered on install or PATH was reset. Likely causes:

1. `pip install` ran without `--user` or the install target wasn't on PATH
2. The package was installed in a venv that wasn't activated for the shell that tried to invoke `harvest`
3. The console-script wrapper exists but in a non-PATH Scripts directory

The package code itself is **fine** — direct dir inspection of `P:/.data/harvest/` showed all expected files, recent dates, expected JSON schema. The CLI is just unreachable.

## Workaround (verified 2026-08-01)

When `harvest` is not on PATH, the CLI can be invoked via Python's `-m` flag targeting the package module:

```powershell
python -m harvest.cli show --top 5
python -m harvest.cli scan-handoffs
```

If the module isn't importable from CWD either, locate the package source and add it to PYTHONPATH or invoke from the package root:

```powershell
# from the package source dir
python -m cli show --top 5
```

## Why this matters

The `/harvest` lifecycle skill is one of the 5 sub-agents invoked by `close-check Phase 3` (Remediate). When the CLI is unreachable:

- **Obligation tracking silently degrades** — harvest events are still being written to `P:/.data/harvest/events/` (5 JSON files modified today), but `harvest show` and `harvest scan-handoffs` queries fail
- **Recurring-friction signal is invisible** — operators can't see "what am I being asked to do" via `harvest show --top 5`, the recommended pre-flight check from `AGENTS.md` Session Start
- **Cross-session obligations accumulate** — `P:/.data/harvest/pending/tp-session-019fb926.json` is 1 day old with 3 OPEN items from a prior session, and no agent has been able to query for it

This is a **chronic friction point** disguised as a one-off CLI typo.

## Applies to

Any Python tool installed via pip whose console-script entry point is missing. Specifically:
- `harvest` (obligation tracker) — verified broken 2026-08-01
- `mmx` (MiniMax CLI) — verify on this host
- `agy` / `codex` — installed as aliases, may be PATH-dependent

## Solution candidates

1. **Find and reinstall** — `pip install --user --force-reinstall <pkg>` to re-register the entry point
2. **Symlink** — locate the entry-point script and symlink it onto a PATH directory
3. **Wrapper alias** — `Set-Alias harvest 'python -m harvest.cli'` in `$PROFILE` as fallback
4. **Structural fix** — `/harvest` SKILL.md should detect CLI-not-on-PATH and use `python -m harvest.cli` automatically (preferred — agent shouldn't have to remember)

## Rule

When a CLI tool fails with "command not recognized" on this Windows host, **always try `python -m <package>` before declaring the tool broken.** Same pattern as the ruff-stdout bug: the tool works; the wrapper is the problem.

## Related

- `P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md` — same class (PowerShell wrapper / python -m invocation bug)
- `P:/.data/wiki/concepts/tool-fallbacks.md` — known-broken combinations registry (harvest CLI missing is a candidate row)
- `AGENTS.md` Session Start — `harvest show --top 5` is the recommended pre-flight
