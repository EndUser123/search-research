---
title: "AAR skill install scope: user (~/.grok), not workspace (P:/.grok)"
created: 2026-07-26
source: session-20260726
tags: [skill-scope, install-convention, aar, path-bug, documentation-drift]
summary: >
  The AAR skill lives at USER scope (~/.grok/skills/aar/), not workspace scope
  (P:/.grok/skills/aar/). The AAR is a personalization — it applies to all
  projects for this Grok installation, not project-specific work. Early AAR
  SKILL.md commands referenced P:/.grok/skills/aar/__lib/ (which does not
  exist), causing Errno 2 on every fresh /aar invocation that followed the
  documented commands. Fixed 2026-07-26 in commit 236204c. This concept
  captures the install-scope convention so future skill authors do not repeat
  the path-convention error.
agent: grok
host: grok
cognitive_load: 1
verification: observed
relations:
  - target: wiki/concepts/skill-host-applicability-convention.md
    type: complements
---

# AAR skill install scope: user (~/.grok), not workspace (P:/.grok)

## Decision context

**Why this knowledge was needed:** Session 019f8b39 ran the updated `/aar` skill end-to-end for the first time. Every documented command in the SKILL.md and its `run-directory-and-preprocessing.md` reference referenced `P:/.grok/skills/aar/__lib/`, but the actual files live at `~/.grok/skills/aar/__lib/`. The path `P:/.grok/skills/aar/` does not exist on this host (verified: `Get-Item P:/.grok` shows no `skills/aar` subdirectory). Every fresh `/aar` invocation that followed the documented commands hit `Errno 2: No such file or directory`.

The bug was discovered while running the AAR's own deterministic preprocessor (Step 0.5 of the SKILL.md). The AAR's own opportunity-discovery (O1, disposition ACT_NOW) identified it as a process weakness — and the AAR then fixed it in the same session (commit `236204c`).

## The install-scope convention

Per `~/.grok/AGENTS.md` § "Skill locations (one scope per skill — never duplicate)":

| Scope | Path | Purpose |
|------|------|---------|
| User (default) | `~/.grok/skills/<name>/SKILL.md` | Grok skills and personalizations |
| Workspace | `P:/.grok/skills/<name>/SKILL.md` | Project-only skills that depend on `P:/packages/` |

The AAR is a **personalization** — it applies to all projects for this Grok installation, not project-specific work. It has no dependency on `P:/packages/`. Therefore it belongs at **user scope** (`~/.grok/skills/aar/`), not workspace scope.

The path bug arose because the SKILL.md and reference docs were written with `P:/.grok/skills/aar/__lib/` paths — likely copy-pasted from a workspace-scope convention or written before the skill was moved to user scope. The documented commands were broken for every session that invoked `/aar` from the SKILL.md instructions.

## The fix

Commit `236204c` corrected all path references:

- `SKILL.md` line 70: `python P:/.grok/skills/aar/__lib/reference_loader.py` → `python ~/.grok/skills/aar/__lib/reference_loader.py`
- `SKILL.md` rule 21: `P:/.grok/skills/aar/SKILL.md` → `~/.grok/skills/aar/SKILL.md`
- `references/run-directory-and-preprocessing.md`: `sys.path.insert(0, "P:/.grok/skills/aar/__lib")` → `sys.path.insert(0, os.path.expanduser("~/.grok/skills/aar/__lib"))`
- `references/run-directory-and-preprocessing.md` CLI form: `python P:/.grok/skills/aar/__lib/full_preprocessor.py` → `python ~/.grok/skills/aar/__lib/full_preprocessor.py`

The fix uses `~` (shell expansion) for shell commands and `os.path.expanduser()` for Python, so the paths resolve regardless of where `HOME` points.

## Falsifier check (verified)

The AAR's O1 opportunity named a falsifier: "if a junction exists at `P:/.grok/skills/aar` resolving to `~/.grok/skills/aar`, documented paths are correct."

Verified 2026-07-26:
```
Get-Item P:/.grok | Select-Object Name, LinkType, Target
# Name  LinkType Target
# ----  -------- ------
# .grok          {}        ← no LinkType (not a junction/symlink)

P:/.grok/skills/aar does NOT exist
```

No junction exists. The workspace-scope path is genuinely wrong, not a missing indirection.

## What this means for our workspace

**For skill authors:** when writing SKILL.md commands that reference the skill's own `__lib/` or `scripts/` directory, use the scope-appropriate path:
- User-scope skills: `~/.grok/skills/<name>/...` (shell) or `os.path.expanduser("~/.grok/skills/<name>/...")` (Python)
- Workspace-scope skills: `P:/.grok/skills/<name>/...`

**For reviewers:** when reviewing a SKILL.md, check that documented paths match the skill's actual install scope. The path-convention error is silent — commands fail with Errno 2 on fresh sessions, but work on the authoring session (which has the path in context).

**For the AAR specifically:** the skill is at user scope. Any future path reference in SKILL.md or references/ that uses `P:/.grok/` is wrong and should be corrected to `~/.grok/`.

## Complements the skill-host-applicability convention

[[skill-host-applicability-convention]] covers the `host: grok | claude | both` frontmatter tag — which host a skill was written for. This concept **complements** that one by covering the orthogonal dimension: **install scope** (user vs workspace). A skill can be `host: grok` AND user-scope (like AAR), or `host: both` AND workspace-scope (like a project-specific integration skill). Both dimensions matter for path correctness.

Related: [[premature-synthesis-without-reading-existing-capability]] — the AAR's own episode E13 (this path bug) was caught by the AAR's opportunity-discovery, and the fix was tracked as O1 (ACT_NOW). The path-convention error here is an instance of documentation drift: the paths were written when the skill may have lived at workspace scope, and never updated when it moved to user scope. See also [[narrative-as-signal-anti-dismissal-rule]] for the general pattern of plausible narratives substituting for verification — "the paths look right, so they must be right" is the narrative that kept this bug latent.

## Falsifier

This concept is wrong or obsolete when:
- The AAR skill moves to workspace scope (then `P:/.grok/skills/aar/` paths would be correct), OR
- A junction is created at `P:/.grok/skills/aar` → `~/.grok/skills/aar` (then both paths resolve, but the convention is still to use the canonical scope).

Until then, user-scope paths (`~/.grok/skills/aar/`) are correct for this skill.

## Receipts

- AAR report: `P:/.artifacts/aar/019f8b39-95e3-7121-a8de-4e3f117e511a/aar-report.md` — episode E13, opportunity O1.
- Path-error receipt: `chat_history-L000013-S000012` (reference_loader.py Errno 2 on `P:/.grok/` path).
- Falsifier check: `Get-Item P:/.grok` showing no junction, `P:/.grok/skills/aar` does not exist.
- Fix commit: `236204c` in `~/.grok` repo.

## Sources

- Session 019f8b39 AAR (internal, 2026-07-26) — O1 opportunity with falsifier.
- `~/.grok/AGENTS.md` § "Skill locations" — the install-scope convention table.
