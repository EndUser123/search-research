---
title: "directory_policy.json reconciliation: fix-as-doc vs Grok-side enforcement"
status: OPEN
created: 2026-08-08
session: 019fe3ff-afbc-71c1-b2a3-3cfbccfd2bc7
assignee: unassigned
---

# directory_policy.json reconciliation

## Problem

`P:/.claude/hooks/config/directory_policy.json` (v3.2.0, 1010 lines) has drifted from reality:
- `_meta.enforced_by` points to a non-existent file (`PreToolUse_directory_policy.py` — missing)
- `_meta.validated_by` points to wrong path (`path_validator.py` — actual is `__lib/path_validator.py`)
- `_meta.semantic_routing` points to a missing file (`semantic_file_router.py`)
- Allowlist lists 11 dirs; root has 37 non-standard dirs
- `csf_nip_directory.allowed_subdirectories` is aspirational (lists dirs that don't exist in `__csf/`)
- Policy is unenforced on Grok Build (config.toml has zero references)
- `/maintain` re-implements its own blocklist instead of consuming the policy

## Two paths (operator decision needed)

### Path A — Fix as documentation (~30-60 min, reversible)
- Remove or correct the three false `_meta` claims
- Add header: "documentation only — no live enforcement on Grok Build"
- Reconcile `csf_nip_directory` block with actual `__csf/` layout
- Delete dead `semantic_routing` block
- Make `/maintain` consume `ignored_cache_directories` + `blocked_root_patterns`
- Write or remove dangling wiki concept references

### Path B — Actually enforce on Grok Build (~half day, needs design)
- Build a Grok-side PreToolUse hook in config.toml that consults the policy
- Advisory mode recommended (AGY's finding: strict validation creates runtime friction → bypass)
- Collapse the 1010-line file to ~300 lines (drop aspirational entries)
- Converge `/maintain` to read the same file
- Must use session-scoped snapshot or advisory mode (not deny on live shared state — violates multi-terminal isolation invariants)

## Acceptance criteria
- [ ] Operator decides Path A or B
- [ ] If A: all `_meta` paths resolve correctly; header documents the role
- [ ] If B: hook registered in config.toml; back-tested FP rate <15%

## Evidence
- /tp critique (spawn + AGY, session 019fe3ff): both lenses converged on REVISE
- /www research: wiki concept `narrative-sufficiency-awareness-enforcement-gap-2026.md` confirms L3 output scanning has limits; L4 is where durable fixes live
- /risk scan: deny-mode hook on live shared state violates multi-terminal isolation invariants
