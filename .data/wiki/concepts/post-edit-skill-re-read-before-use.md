---
title: "Post-Edit Skill Re-read Before Use"
created: 2026-08-02
source: session-019fa8f8
tags: [agent-rule, skill-protocol, edit-then-verify, chronic-pattern]
summary: >
  After editing a SKILL.md (or its __lib/ scripts) in the same session,
  re-read the skill body before invoking it. The skill body IS the
  implementation; the prior in-context version is stale by definition
  once an edit lands. Failure mode: agent treats its own edit as
  successful, runs a procedure that no longer matches the code, and
  narrates a wrong result. Distinct from Skill cache validation (which
  handles stale caches from sibling sessions).
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - session-019fa8f8 friction raw evidence, segment 003
  - Operator correction cluster 2026-08-02
relations:
  - target: wiki/concepts/skill-usability-audit-cold-read-critique.md
    type: complements
  - target: wiki/concepts/skill-cache-validation-rule.md
    type: extends
---

# Post-Edit Skill Re-read Before Use

## The pattern

When you edit a SKILL.md or its implementation files (`__lib/*.py`,
`scripts/*.py`) during a session, **the skill body you have in context
is now stale.** You edited it. The version that matches the
filesystem is the version you have not yet read.

The failure mode:

1. Agent edits `/model-quota` SKILL.md to add new flags / coverage.
2. Same session, agent invokes `/model-quota`.
3. Agent uses the OLD procedure (from the cached in-context version),
   not the new procedure (which now mandates a different script call).
4. Operator: "you didn't use /model-quota properly. read the skill."
5. Agent: *now reads the skill*, sees the new code, runs it correctly.
6. Operator (already frustrated): "the fucking skill you edited had
   the fucking code." / "are you stupid???"

The correction is not "edit carefully." The correction is "after you
edit, **read what you produced** before you use it."

## Why this is distinct from Skill cache validation

`~/.grok/AGENTS.md` Skill cache validation handles **sibling-session
cache staleness** — another session edits the skill, your cached
version is stale, check `(Get-Item).LastWriteTime` before invoking.

This new rule handles **self-inflicted staleness within the same
session.** You are the editor. There is no sibling to blame. The
check is mechanical: did *I* write to the skill in this session? If
yes, re-read before invoking. No `LastWriteTime` check needed — the
edit just happened.

## The rule (proposed for AGENTS.md)

> After editing a SKILL.md or its `__lib/` / `scripts/` files in the
> same session, **re-read the skill body before invoking it in any
> response where the procedure matters.** The skill body IS the
> implementation; the prior in-context version is stale by definition
> once an edit lands. Self-edits bypass the sibling-cache check because
> the editor and the invoker are the same agent.

## Why the existing AGENTS.md rules didn't fire

Three existing rules touch this neighborhood but don't catch it:

| Rule | Catches | Misses |
|------|---------|--------|
| Edit-then-verify (file-operations.md) | Edit did not persist | Edit persisted; agent uses old procedure |
| Skill cache validation | Sibling session edit | Same-session self-edit (no mtime race) |
| Meta-checkpoint Q2 (cold-read critique) | Edit shipped without usability audit | Edit shipped, agent used wrong version |

None of these trigger on "agent edited a skill, then used the
pre-edit version of the skill in the same session." The gap is
specifically the **identity** of the editor and invoker.

## When NOT to apply

- The skill edit was a typo fix in frontmatter only (description,
  argument-hint). The procedure didn't change.
- The skill was edited by a sibling session, not by you — Skill cache
  validation already covers this.
- You're about to invoke a skill you have NOT edited in this session.

## Applies to

Any skill where the procedure matters more than the description:
`/model-quota`, `/tp`, `/wiki`, `/handoff`, `/friction`, `/check`,
`/close`, `/ship`, `/capture`. Routine skills like `/recap-grok` and
`/slc` are lower-risk (procedure is more stable).

## Reference failure

Session 019fa8f8, compaction segment 003 (2026-08-02). Operator
corrections cluster:

- "wtf. why didn't you use the skill properly and output the results
  as per the code?"
- "you need to read the skill you failed again."
- "did you read the skill now?"
- "the fucking skill you edited had the fucking code"
- "are you stupid??? the fucking skill you edited had the fucking code"
- "what does that fucking code do?"

Underlying trace: agent edited `/model-quota/SKILL.md` (added new
provider coverage table, OpenRouter opencode-quota fix section), then
ran the skill using the pre-edit procedure (run `opencode-quota` only,
ignore new `fleet_quota.py` direct calls). Output missed the entire
direct-API tier (OpenRouter, Mistral, SerpAPI, Tavily, Firecrawl,
GitHub, ElevenLabs).

## What this would look like mechanically

Add to `~/.grok/AGENTS.md` after the Skill cache validation rule:

```markdown
#### Self-edit re-read (post-edit verification, 2026-08-02)

Distinct from sibling cache validation: if YOU edited a SKILL.md
(or its `__lib/` / `scripts/`) in this session, re-read the skill
body before invoking it in any response where the procedure matters.
The in-context version is stale the moment your edit lands — there
is no `LastWriteTime` race to check, you are the editor. Self-edits
bypass the cache rule because the editor and invoker are the same
agent.
```