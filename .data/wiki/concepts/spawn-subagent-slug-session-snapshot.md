---
title: "spawn_subagent slug list is session-start-snapshotted"
created: 2026-07-21
source: session-2026-07-21
tags: [grok-build, subagent, spawn_subagent, config, gotcha, operational]
summary: >
  Grok Build's `spawn_subagent` validates the `model` parameter against a slug
  list captured at session start. Adding new `[model.*]` entries to config.toml
  mid-session does not make them valid slugs until Grok restarts. The picker
  (`grok models` / Ctrl+M) reads config fresh each call and sees the new entries,
  but `spawn_subagent` rejects them as "Unknown Task.model slug." This split
  between picker and spawn validation is the gotcha.
agent: grok
host: grok
cognitive_load: 1
verification: single-source-verified
---

# spawn_subagent slug list is session-start-snapshotted

## The gotcha

You add a new model entry to `~/.grok/config.toml` mid-session:

```toml
[model.my-new-model]
model = "some-model-id"
base_url = "https://api.example.com/v1"
api_key = "sk-..."
```

You verify the picker sees it:

```powershell
grok models
# → - my-new-model          ✓ visible
```

You try to route a subagent to it:

```python
spawn_subagent(model="my-new-model", ...)
# → Error: Unknown Task.model slug 'my-new-model'. Valid model slugs: [list of 22 entries from session start]
```

The picker accepts it; `spawn_subagent` rejects it. Same config file, same session, different validation results.

## Root cause

The valid-slug list for `spawn_subagent` is **captured at session start** from the current state of config.toml. It is not refreshed mid-session. The picker (`grok models`, Ctrl+M) reads config fresh on each invocation, which is why it sees entries added after session start.

This was verified empirically (2026-07-21): four `[model.*]` entries added mid-session were invisible to `spawn_subagent` but visible to `grok models`. After a Grok restart, all four became valid slugs.

## The fix

**Restart Grok after adding new `[model.*]` entries to config.toml.** There is no mid-session refresh mechanism for the slug list. This is the only reliable fix.

## What NOT to do (investigated dead ends)

- **Changing `env_key` to literal `api_key`** does not help — the slug list is captured at session start regardless of the entry's auth method.
- **Grok's `load_envrc = true` setting** does not solve this either. It loads environment variables, not model slugs. And on Windows it requires `direnv` to be installed (the loader calls `direnv export json`, not a standalone bash parser).
- **Renaming the binary or shadowing with a wrapper** does not affect the slug list — the snapshot happens inside the Grok process at startup.

## How to recognize this hit it

The error message is distinctive:

```
Unknown Task.model slug '<your-slug>'. Valid model slugs: <comma-separated list>.
Omit `model` to inherit the parent model.
```

The valid-slugs list in the error will be shorter than what `grok models` shows. The entries missing from the error list but present in `grok models` are the ones added after session start.

## Practical implication for skill routing

Skills that use `spawn_subagent` with a `model` parameter (shipped in Grok Build v0.2.98, 2026-07-12) should not reference model slugs that were added to config.toml in the same session as the skill edit. The safe sequence is:

1. Add `[model.*]` entries to config.toml
2. Restart Grok
3. Verify with a probe: `spawn_subagent(model="new-slug", prompt="reply PROBE_OK")`
4. Then edit skills to reference the new slug

Skipping step 2 means the skill edit references a slug that `spawn_subagent` will reject at runtime.

## Related

- [[model-picker-as-failover-not-router]] — the picker is the failover mechanism; this gotcha explains why picker and spawn validation can diverge mid-session
- Grok Build v0.2.98 changelog (2026-07-12) — `spawn_subagent` accepts optional `model` parameter

## Sources

- Session 2026-07-21 — empirical verification: 4 entries added mid-session, all rejected by `spawn_subagent`, all accepted after restart
- Grok Build binary analysis — `envrc.rs` module + session-start config snapshot pattern

## Auto-related

- [[i'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[grok-build-cc-aca-actually-enabled]]
- [[python-behavior-tree-framework-for-autonomous-llm-agents--technical-specificatio]]
- [[wiki-lifecycle-state-file]]

