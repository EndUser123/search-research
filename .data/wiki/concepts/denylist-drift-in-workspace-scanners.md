---
title: "Denylist drift: workspace scanners must use allowlist classification, not denylist"
created: 2026-08-09
source: session-2026-08-09
tags: [scanners, classification, denylist, allowlist, workspace, preflight, root-cause, pattern]
summary: >
  Workspace file scanners that classify paths via a denylist of known
  derived/state directories always drift: tooling creates new derived dirs
  (caches, session stores, venvs) faster than denylists are maintained.
  Each unlisted derived dir becomes a false authority candidate,
  manufacturing phantom conflicts. The durable fix is an allowlist model
  where the default is "derived" and source roots are opt-in, plus a
  dot-prefix backstop that catches future tooling dirs without enumeration.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
tier: warm
confidence: 0.95
last_verified: 2026-08-09
half_life_days: 365
relations:
  - target: wiki/concepts/inference-chains-bare-numbers-destructive-write
    type: related
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write
    type: related
---

## Summary

Any scanner that walks a multi-agent workspace and classifies files as
"source" vs "derived" using a **denylist** (a fixed list of known
non-authoritative directories) will drift. The workspace proliferates
derived directories — venvs, caches, session stores, lock dirs, benchmark
output — faster than any denylist can track. Each unlisted derived dir
silently becomes a false authority candidate, manufacturing phantom
conflicts and causing every broad-scope scan to return blocked or noisy
results.

## Key Findings

- **The failure class is structural, not incidental.** In a 2-month-old
  workspace, a denylist of 10 entries missed 25+ derived directories
  (`.session`, `sessions/`, `.venv`, `site-packages`, `worktrees/`,
  `.benchmarks`, `.locks`, `memtrace`, `marketplace-cache`,
  `relocations`, `plugin-data`, `implement-memory`, etc.). Each one was
  classified as `candidate_source` and could manufacture phantom conflicts.

- **The dot-prefix backstop is the durable fix.** Hidden directories
  (dot-prefixed) that are NOT known workspace scope roots
  (`.claude`, `.grok`, `.agents`, `.data`) are derived by default. This
  catches future tooling-introduced dirs (`.cache`, `.nox`, `.newtool`)
  without per-dir maintenance — the dotted-derived family is stable and
  large, while dotted-source-roots are a fixed set of 5.

- **Non-dotted derived dirs need enumeration** — `sessions/`, `state/`,
  `logs/`, `worktrees/`, `vendor/`, `exports/`, `site-packages/`,
  `node_modules/`. These are a finite set that changes slowly.

- **Two bugs from one root cause.** The preflight `discovery_audit.py`
  had BOTH (a) phantom conflicts from misclassified session-ledger JSON
  and (b) silent inventory loss from unpruned venv/worktree dirs. Both
  stemmed from the same denylist approach — one in classification, one
  in walking. Unifying them on a single `_is_derived_component()` rule
  fixed both with one change and prevented future drift between the two
  checks.

- **Other scanners may have the same latent bug.** `close_accounting.py`,
  `coverage_scan.py`, and any script that walks `P:\.claude\` or
  `~/.grok\` to inventory files could hit the same denylist drift. The
  pattern generalizes: any workspace walker that doesn't default to
  "derived unless proven source" will eventually misclassify new
  runtime dirs as authoritative.

## Pattern detection (when to apply this)

A scanner is vulnerable if it:
1. Walks workspace directories recursively
2. Classifies files into "authoritative" vs "non-authoritative" buckets
3. Uses a fixed list of patterns to exclude (denylist) rather than a
   fixed list of patterns to include (allowlist)

The vulnerability is invisible until a new tool creates a new derived
directory under the scan scope. The symptom is phantom conflicts, false
positives, or silent inventory loss (file cap exhausted before reaching
real source).

## The durable rule

**Denylist classification of workspace files always drifts.** Default
to "derived" and allowlist source roots. Specifically:

```python
def is_derived_component(part: str) -> bool:
    if part in ENUMERATED_DERIVED:  # sessions, state, logs, worktrees, etc.
        return True
    if part.startswith(".") and part not in WORKSPACE_SCOPE_ROOTS:
        return True  # dot-prefix backstop
    return False
```

This is a classification analog to the allowlist security principle
("default deny, explicitly allow") applied to filesystem authority.

## Falsifier

This pattern is wrong if workspace source code regularly lives in
dot-prefixed directories that are NOT in the known scope-root set. In
this workspace, all hand-authored source lives under `.claude/hooks/`,
`.claude/scripts/`, `.agents/skills/`, `.grok/skills/`, or
`packages/*/` — all of which are covered by the scope-root allowlist.
If future source code is authored in e.g. `.newframework/src/`, the
backstop would wrongly classify it as derived. Mitigation: add new
source roots to `_DOT_SCOPE_ROOTS` when they appear; the set is small
and stable.

## Related

[[inference-chains-bare-numbers-destructive-write]] — the broader pattern
of unverified assumptions causing silent failures in workspace tooling.

[[causal-mechanism-claims-require-source-receipts-before-durable-write]] —
the receipt-before-claim principle that applies to any diagnostic about
"why does this scanner fail."

## Sources

- Session 2026-08-09: preflight discovery_audit.py false-positive diagnosis and fix (commit `1166b27` on P:/ main)
- File: `P:\.agents\skills\preflight\scripts\discovery_audit.py` — `_classification()` and `_is_derived_component()`
- Test file: `P:\.agents\skills\preflight\tests\test_discovery_audit.py` — 7 regression tests guarding the pattern
- Fresh-lens /tp critique (subagent 019fe66e): independently confirmed 10+ unhandled derived directories under the workspace scopes
