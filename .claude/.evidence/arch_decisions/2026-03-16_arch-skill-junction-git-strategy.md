# ADR: arch skill — Windows junction git tracking strategy

**Date:** 2026-03-16
**Status:** Accepted
**Deciders:** Session discussion (human + Claude)

---

## Context

`packages/arch` is the source package for the `/arch` Claude skill. It is intended for
publication on GitHub as a standalone package. The Claude Code runtime loads skills from
`.claude/skills/<name>/`, so during local development we need the skill files to be
immediately available at `.claude/skills/arch/`.

A Windows junction was created: `.claude/skills/arch/` → `packages/arch/skill/`

This caused three concrete problems:

1. **Dual git tracking** — git tracked the same physical inodes under two paths
   (`.claude/skills/arch/*` AND `packages/arch/skill/*`), bloating the index and
   creating confusing `git log` output where the same change appeared twice.

2. **ruff-format config divergence** — ruff walks up the directory tree for config.
   The `.claude/skills/arch/` path found a root-level config with `line-length = 100`.
   The `packages/arch/skill/` path found `packages/arch/pyproject.toml` first, which
   had no `[tool.ruff]` section and fell back to the default `line-length = 88`.
   Result: ruff-format kept reformatting the same files in a loop.
   Workaround applied: added `[tool.ruff] line-length = 100` to `packages/arch/pyproject.toml`.

3. **Pre-commit stash conflicts** — pre-commit's stash/restore cycle interacted badly
   with files that appeared modified under both tracked paths.

## Decision

**Source of truth: `packages/arch/skill/`**

- Git tracks files only via `packages/arch/skill/` (the package source).
- `.claude/skills/arch/` is added to `.gitignore` — it is a *derived dev artifact*,
  not a tracked source.
- The Windows junction remains in place for live-edit convenience (edits to
  `packages/arch/skill/` are immediately reflected at `.claude/skills/arch/` with
  zero reinstall friction).

## Consequences

**Good:**
- Single git path per file — no duplicate index entries, clean `git log`.
- ruff config inheritance works correctly — only `packages/` path is checked by pre-commit.
- Pre-commit stash conflicts from arch files are eliminated.
- `pyproject.toml`'s `shared-data` intent ("junction target = deployment target") is
  now architecturally consistent with git tracking.

**Accepted tradeoff:**
- The main repo's `git log` no longer shows changes under `.claude/skills/arch/` paths.
  All arch skill history is under `packages/arch/skill/` paths. This is correct — the
  skill files belong to the package, not to the project that uses it.

## Future state: standalone GitHub repo

When `packages/arch` is ready for its own GitHub repo:

1. **Preferred: `git subtree split`** to extract history with arch commits only:
   ```bash
   git subtree split --prefix=packages/arch --branch arch-standalone
   # push arch-standalone to new GitHub repo
   ```
2. Add to main repo's `.gitignore` under "Standalone packages":
   `.claude/skills/arch/` is already there.
3. Optionally add as a git submodule if the main repo needs to pin a version:
   ```bash
   git submodule add https://github.com/you/arch packages/arch
   ```
   Note: submodules have significant Windows friction — evaluate whether
   `pip install -e packages/arch` workflow is simpler.

## What NOT to do

- **Don't re-add `.claude/skills/arch/` to git tracking** — the junction means any
  commit through that path duplicates changes already tracked via `packages/arch/skill/`.
- **Don't remove the junction** — it's the live-dev bridge. Remove it only if you move
  to a proper install-based workflow (`pip install -e packages/arch`).
- **Don't add other `packages/` Claude plugin junctions to git tracking** — apply the
  same pattern: track via `packages/<name>/skill/`, ignore the junction target.

## Related

- `packages/arch/pyproject.toml` — `[tool.ruff]` section added to fix ruff idempotency
- `packages/arch/pyproject.toml` — `shared-data` install mechanism (confirms junction
  target is meant to be a deployment artifact, not a dev source)
- `.gitignore` line ~566 — "Standalone packages" section where `.claude/skills/arch/`
  is ignored
