---
title: "Config disabled-list bare-name collision kills native skills"
created: 2026-08-04
source: session-2026-08-04
tags: [config, skill-collision, grok-build, disabled-skills, plugin-migration, structural-hazard, bare-name]
summary: >
  Grok Build's [skills] disabled list uses bare skill names that match globally.
  When a native skill shares a name with a plugin skill, disabling the plugin
  version also kills the native. This caused two incidents in one session:
  "handoff" killed the native fleet-grade handoff (intended to suppress the
  Pocock duplicate), and "grill-me" + "diagnosing-bugs" would have killed newly-
  created native skills. The fix: never use bare names in the disabled list for
  skills that have native equivalents. Use the [skills] ignore path-scoped
  mechanism for plugin skills, or accept that native skills take catalog priority.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Git commit fc4731d (config: enable mattpocock-skills plugin, disable 7 duplicate skills — caused the handoff kill)
  - Git commit 9a24ade (cleaned disabled list — caught grill-me/diagnosing-bugs collision before damage)
  - Grok Build docs: ~/.grok/docs/user-guide/08-skills.md lines 39-49 (ignore vs disabled semantics)
relations:
  - target: wiki/concepts/agent-config-directory-taxonomy.md
    type: refines — that concept documents dedup failure; this adds the disabled-list active-kill variant
  - target: wiki/concepts/plugin-skill-migration-port-absorb-retire.md
    type: related — both surfaced during the same plugin migration
  - target: wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md
    type: related — the collision is a closure-pressure failure mode (agent adds bare name without checking native scope)
---

# Config disabled-list bare-name collision kills native skills

## Decision context

**Why this matters:** when migrating skills from a plugin to native `~/.grok/skills/`, the operator may add the plugin skill's name to `[skills] disabled` to suppress the duplicate. But Grok Build's disabled list matches by bare name globally — it doesn't distinguish plugin scope from native scope. A single `"handoff"` entry kills both the Pocock plugin version AND the native fleet-grade handoff. The operator sees the qualified plugin form in the skill picker, not the native one — the native skill silently disappears.

## The mechanism

```
[skills]
disabled = [
    "handoff",       # INTENDED: suppress Pocock plugin handoff
                     # ACTUAL: kills native ~/.grok/skills/handoff/ too
]
```

Per Grok Build docs (08-skills.md line 48): "`disabled` takes skill names." Names, not paths. The match is global across all discovery roots. There is no plugin-scoped disable mechanism in the disabled list.

The `ignore` mechanism (line 46) takes filesystem paths and could theoretically target a specific plugin skill, but in practice it doesn't work for plugin-bundled skills because they're loaded by a separate plugin loader that bypasses the skill scanner (confirmed via `/www` research, 2026-08-04).

## Two incidents in one session

### Incident 1: handoff killed (2026-08-04, detected by operator)

Commit `fc4731d` added `"handoff"` to the disabled list to suppress the Pocock plugin version. The native `~/.grok/skills/handoff/` (fleet-grade, 39,921 bytes, 24 callers in skill graph) was killed instead. The operator saw `mattpocock-skills:handoff` in the picker but not the native `/user:handoff`. Root cause: bare name match. Fix: removed `"handoff"` from the disabled list entirely (native takes catalog priority by resolution rules).

### Incident 2: grill-me + diagnosing-bugs near-miss (2026-08-04, caught before damage)

After porting skills from the Pocock plugin to native, the disabled list still contained `"grill-me"` and `"diagnosing-bugs"` — names of the newly-created native skills. These would have killed the native versions on next session. Caught during config cleanup before the plugin was disabled. Fix: removed both from the disabled list.

## The pattern

This is a structural hazard of the bare-name disabled-list design. It fires whenever:
1. A native skill and a plugin skill share a name
2. The operator adds the name to the disabled list (intending to suppress the plugin version)
3. The bare match kills both

The hazard is invisible at write time — you add one name, you think you're disabling one skill. The failure surfaces later when the native skill doesn't appear in the catalog.

## What this means for our workspace

1. **Never use bare names in the disabled list for skills that have native equivalents.** If a native skill exists at `~/.grok/skills/<name>/`, don't put `<name>` in `[skills] disabled`.
2. **Native skills win by resolution priority.** Per docs (08-skills.md line 204): "A plugin skill of the same name does not override a native skill; it stays available under its qualified `plugin:name` form." So the qualified form showing in the picker is expected behavior — you don't need to disable the plugin version.
3. **During plugin migrations:** clean the disabled list BEFORE creating native skills with the same names. The disabled list from the pre-migration era will contain names that are about to become native skill names.
4. **The disabled list should only contain names of skills you genuinely want suppressed globally** — not names you're using to manage plugin duplicates.

## Falsifier

This hazard does NOT apply when the disabled-list name is unique to one scope (e.g., `"ask-matt"` only exists in the Pocock plugin, no native equivalent). In that case, the bare-name match is correct — it disables the only skill with that name. The hazard fires only when a name exists in both native and plugin scopes.

## Receipts

- **Grok Build docs:** `~/.grok/docs/user-guide/08-skills.md` lines 39-49 — `disabled` takes skill names (bare), `ignore` takes paths
- **Git commit fc4731d:** the commit that added `"handoff"` to the disabled list and caused Incident 1
- **Git commit 9a24ade:** the commit that cleaned the disabled list and caught Incident 2
- **`grok inspect` output:** confirmed both handoff entries (user + plugin:mattpocock-skills) with the native one showing `[disabled]`

## Related concepts

- [[agent-config-directory-taxonomy]] — documents the dedup-failure class across scan roots
- [[plugin-skill-migration-port-absorb-retire]] — the migration methodology that surfaced this hazard
- [[adaptive-expansion-evidence-triggered-conditional-steps]] — the collision is a form of premature closure (adding bare name without checking native scope)

## Auto-related

- [[skill-graph]]
- [[portable-ai-brain-pattern]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[skill-catalog]]
- [[government-debt-and-fiscal-policy]]

