---
title: "Skill path resolution gotcha: Grok skills can live in multiple scopes"
created: 2026-07-21
source: session-2026-07-21
tags: [path-resolution, multi-scope, grok-skills, silent-failure, edit-validation, multi-host, tooling]
summary: >
  Grok skills on a multi-host setup can be loaded from multiple filesystem
  locations (user home + workspace root + bundled defaults), but the system
  reminder that tells an agent where the canonical copy lives does not always
  match where Grok Build actually loads from at runtime. Editing at the path
  the reminder cites may write to a location that another agent's commit
  reverts, or to a non-canonical path that doesn't propagate. Always verify
  the path exists AND has your edits after every skill edit; treat path
  choice as a category decision (Grok skill vs project skill vs bundled
  default), not a path-of-least-resistance choice.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/context-file-deduplication-agents-md-as-source
    type: related
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: refines
---

## Summary

Grok Build loads skills from multiple filesystem scopes (user home at `~/.grok/skills/`, workspace at `P:/.grok/skills/`, bundled at `~/.grok/bundled/skills/`). When the system reminder reports a skill's "absolute path," that path is **the path the reminder was generated from**, not necessarily the path Grok Build uses at runtime. Editing at the reminder's path can result in:

1. **Silent overwrite** — your edits get overwritten by another agent's commit on a different copy.
2. **Dead writes** — you edit a file that the runtime never loads.
3. **Split brain** — two copies exist with divergent content; future sessions read whichever the loader picks first.

The fix: verify path exists before editing, verify edits persisted after editing, and treat path choice as a category decision — Grok skills belong at user scope; project-domain tools belong at workspace scope.

## The failure mode (with receipts)

**Incident 2026-07-21:** A session edited `/handoff` SKILL.md at the path cited by the system reminder (`P:\.grok\skills\handoff\SKILL.md`). The edit reported success. Subsequent verification found the file at that path had reverted to its HEAD-aligned version. Two factors:

1. The file was git-tracked. Another agent's commit (`4216107` "scope drift re-anchor rule...") had landed between the edit and the verification, overwriting uncommitted solo-edits.
2. The path the system reminder cited was correct as a Grok Build reference, but the canonical copy for *this user's* setup was at `C:\Users\brsth\.grok\skills\handoff\SKILL.md` (home). The workspace copy was a stale project-specific override that should never have contained `/handoff` in the first place.

**Diagnostic signature:** edit reports success; `git diff <path>` shows no changes (because someone else's commit reset the working tree); OR the edit is visible at path A but not visible to Grok Build sessions that load from path B.

## The rules

### 1. One location per skill, by category

| Skill class | Canonical location | Examples |
|---|---|---|
| **Grok skills** (meta-tools for working with Grok) | `C:\Users\brsth\.grok\skills/<name>/SKILL.md` | `/handoff`, `/tp`, `/plan`, `/go`, `/design`, `/review`, `/aar`, `/wiki`, `/web` |
| **Project-domain tools** (depend on `P:/packages/<x>/` code) | `P:\.grok\skills/<name>/SKILL.md` | A hypothetical `/yt-is-foo` that requires `P:/packages/yt-is/` |
| **Bundled defaults** (shipped with Grok Build) | `C:\Users\brsth\.grok\bundled\skills/<name>/SKILL.md` | Default for skills not customized |

The categorical rule: **Grok skills ALWAYS live at user scope.** If you find yourself putting `/handoff` at workspace scope, you have the wrong scope. Workspace scope is for project-domain skills, not Grok skills.

### 2. Before editing, verify path exists

```
Test-Path "$path"   # PowerShell
ls "$path"          # bash / zsh
```

If the path doesn't exist, you have the wrong scope. Search both home and workspace:
- `~/.grok/skills/<name>/`
- `~/.grok/bundled/skills/<name>/`
- `P:\.grok\skills\<name>/`

Pick the one that matches the categorical rule above. **Never** create a new copy just because the system reminder said so — that's how split-brain starts.

### 3. After editing, verify edits persisted

```
git diff <path>                                       # if tracked
Get-Content <path> | Select-String -Pattern <signature>  # always
```

This catches three failure modes:
1. **Concurrent agent commits** that overwrote your edit between write and verify.
2. **Windows persistence glitches** where the tool reported success but the file wasn't actually written.
3. **Path-resolution mismatches** where you edited the wrong file.

### 4. If a skill exists in two scopes, fix it once

When you discover a skill has been mistakenly placed in two scopes (e.g., `/handoff` at both home and workspace), one canonical choice is required:

1. Decide which scope is canonical per the categorical rule.
2. **Copy** from the stale scope to the canonical scope (preserves any unique edits in the stale one).
3. **Verify** the canonical copy has all the expected content.
4. **Remove** the stale scope. If it's git-tracked, use `git rm` + commit; otherwise just delete the directory.
5. **Document** the canonical location in the skill's own SKILL.md under a "Canonical location" section so future agents don't re-create the duplication.

## Related patterns

- **[[context-file-deduplication-agents-md-as-source]]** — the broader problem: multi-tool workspaces accumulate duplicate context files (AGENTS.md, CLAUDE.md, bundled copies). Same fix: single-source-of-truth.
- **[[external-state-cross-check-as-structural-fix]]** — applied here: derive path-existence from `Test-Path` (external state), not from the system reminder (the orchestrator's bundle). The reminder is internal to the orchestrator; the filesystem is external.

## Adoption

Verified in session 2026-07-21:

- All Grok skills (`/tp`, `/plan`, `/go`, `/design`) at `C:\Users\brsth\.grok\skills\`.
- `/handoff` confirmed to live at `C:\Users\brsth\.grok\skills\handoff\` (canonical); the workspace copy at `P:\.grok\skills\handoff\` was deleted with user authorization per the categorical rule.
- `~/.grok/skills/handoff/SKILL.md` now contains a "Canonical location" section pointing future agents at the right path.

The pattern is host-specific (Grok Build's multi-scope loader) but the principle generalizes: **path-choice is a category decision, not a path-of-least-resistance decision.** Always verify path before and after editing, and treat any "I edited but it didn't persist" outcome as a path-resolution symptom until proven otherwise.
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
