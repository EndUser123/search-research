# Review instructions (Grok `/review` + Claude Code Review compat)

This file is **review-only** policy. Grok’s `/review` skill injects it as
highest-priority guidance (same role as Anthropic’s `REVIEW.md` for Claude Code
Review). Keep it short so rules stay high-signal.

**Location:** `P:/.grok/REVIEW.md` (not repo root — keep the root clean).

## What Important / bug means here

Reserve **bug** (blocking) for findings that would break behavior, corrupt data,
leak secrets/PII, break multi-agent isolation, or block rollback:

- Incorrect logic or fail-open auth
- Data integrity bugs (wrong identity keys, silent overwrite, claim theft)
- Security (injection, path traversal, secret leakage)
- Migrations / promote paths that can destroy live state

Style, naming, and optional refactors are **nit** or **suggestion** at most.

## Cap the nits

Report at most **five** nits inline. If there are more, say “plus N similar
items” in the summary. If everything is a nit, lead with **“No blocking issues.”**

## Do not report (CI / noise)

- Pure lint/format/type issues CI already enforces (unless CI is known broken)
- Generated lockfiles, vendored trees, `node_modules`, large binary artifacts
- Style-only churn with no correctness impact

## Always check on PRs and package reviews

- New shared defaults: every reader/writer and lifecycle consumer
- Concurrent git / staged foreign work not destroyed by “cleanup”
- Hooks/plugins: single dispatch path (no double-fire)
- Identity and provenance: no invented session/run IDs
- Tests: behavior, not only schema/presence

## Verification bar

- Behavior claims need `file:line` evidence in source, not inference from names
- Scope-completeness claims need repo-wide search, not a single named file
- After the first review on a PR: prefer **new bugs only**; suppress fresh nits
  unless the user asked for thorough style

## Handoffs, multi-terminal, stale data

Canonical rules live in `P:/.grok/skills/review/SKILL.md` (Step 0):

- **Path-only** child prompts (packets under `run_dir/packets/`; no dossier paste)
- **Run root:** `P:/.artifacts/<terminal_id>/grok-review/<slug>/<ts>/`
  (not shared `tmp`; not package `docs/` until durable step)
- **Isolation key:** terminal id from env (session id in metadata only if present)
- **No shared fixed critique dirs** across terminals
- **Stale immunity:** other run_dirs are not live input without user resume + HEAD match
- **Never invent** session/terminal IDs for isolation metadata
- **External second opinion** (`--second-opinion`): opt-in, path-only packets under
  `run_dir`, soft-skip if BYOK models unavailable — see skill Step 5.5

## Summary shape

Open the review body with a one-line tally, e.g. `bugs: 2, risks: 1, nits: 3`.
When bugs=0, lead with **No blocking issues.**
