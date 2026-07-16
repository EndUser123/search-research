# Bridge Implementation — Restart Document

**Fresh session: read this file first, then `docs/bridge-corrected-design-20260715.md`.
Do NOT read the session transcript (27 MB JSONL) — everything you need is below.**

Generated 2026-07-15. This replaces the verbal handoff. All facts below were
verified by tool call in this session (see "Evidence" at the bottom).

---

## What is being built

A bidirectional bridge between a ChatGPT browser tab and Claude Code, built on
the existing `tools/ai_lane_controller/` lane-controller library. Two endpoint
daemons (ChromeEndpoint via CDP, ClaudeCodeEndpoint via Agent SDK) poll lane
messages and relay them across the boundary. The lane controller provides the
filesystem-backed mutex/claim/routing substrate.

Full corrected design: `docs/bridge-corrected-design-20260715.md` (5 ADRs
resolving 16 red-team BLOCK findings).

## Verified current state

| Item | Status | Evidence |
|------|--------|----------|
| Milestone 3A (liveness binding) | **committed** `fcd7016` | `git log fcd7016` |
| Corrected design doc | **committed** `a46a8f3` (HEAD) | `git log -1` |
| Milestone 4 code (terminal_id, session_id, workspace_id, fencing_epoch, atomic writes) | **modified, uncommitted** in `tools/ai_lane_controller/claim.py` | `git diff HEAD -- tools/ai_lane_controller/claim.py` |
| Milestones 1–2 source files | **untracked** in `tools/ai_lane_controller/` | `git status` |
| Tests (10 files, 113 functions) | **untracked** in `tests/ai_lane_controller/` | `pytest` → 113 passed |
| Red-team specialist findings | **copied** to `docs/red-team-bridge-20260715/` (also remain in `.artifacts/...`) | `ls docs/red-team-bridge-20260715/` |

### Test breakdown (verified, not estimated)
```
test_claim.py          15    test_message_routing.py  11
test_claim_routing.py   5    test_multilane.py        16
test_durability.py      6    test_mutex.py             6
test_fencing.py        18    test_recovery.py          7
test_lane_identity.py  19    test_liveness.py         10
                              TOTAL                  113
```

## What needs to happen (in order)

### 1. Commit Milestone 4 + tests (blocker for ADR-1)
M4 changes sit uncommitted in `claim.py`. ADR-1 (`identity_token` on `LaneClaim`)
also modifies `claim.py`, so M4 must land first to avoid a messy merge.

⚠️ **Multi-terminal constraint**: a stale `.git/index.lock` (0 bytes, no git
process) was present at handoff time. Verify it's gone before committing:
`ls .git/index.lock` — if it exists and `ps aux | grep git` shows nothing,
it's stale and safe to `rm`. If a git process IS running in another terminal,
wait.

Stage bridge files only (the working tree has ~78 changed files, mostly
unrelated bifrost cleanup and plugin churn — do NOT `git add -A`):
```
git add tools/ai_lane_controller/ tests/ai_lane_controller/ \
        docs/red-team-bridge-20260715/ docs/bridge-corrected-design-20260715.md \
        docs/bridge-handoff-restart-20260715.md
```
Verify staged set before commit: `git diff --cached --name-only` must list
ONLY bridge files. Then commit M4.

### 2. Implement ADR-1 (identity_token)
Per corrected design §ADR-1:
- Add `identity_token: str` (optional) to `LaneClaim`; `pid` becomes `int | None`.
- `_acquire_lock` records `identity_token` (or `pid`); reclamation checks
  `_process_exists(pid)` only when pid set, else token-liveness via heartbeat.
- Fencing epoch remains the authority for superseded-writer detection.
- **Invariant**: every claim has exactly one identity — OS PID *or*
  identity_token, never both empty.

Testable in isolation against the existing 113 tests; they must stay green.
Add new tests for the token path.

### 3. Then, per corrected design
Endpoint daemons (`tools/ai_lane_controller/endpoints/`), security model
(HMAC signing, OS keyring, `--remote-debugging-pipe`), CDP connection manager,
lane-phase state machine (ADR-5), and the endpoint test suite + HTML fixtures.

## CDP probe result (verified evidence)

The probe that de-risked the whole approach: Chrome DevTools Protocol attach
to chatgpt.com works. `navigator.webdriver=true` is detectable but ChatGPT
loaded normally — **no block page, no CAPTCHA, no Cloudflare challenge**.
Textarea value was set via `Runtime.evaluate` and read back successfully.

⚠️ The corrected design's ADR-2 changes injection to use `arguments[0]`
parameter passing — the probe's string-interpolation form is a confirmed RCE
risk (SEC-1) and must not be replicated.

Full per-specialist reasoning is in `docs/red-team-bridge-20260715/*.json`.

## What this repo's working tree also contains (context, not your concern)

`git status` shows ~78 changed files. Most are unrelated: bifrost provider-config
cleanup (deletions), plugin marketplace churn, ornith-server logs, search-research
plugin edits. None of these block the bridge. Leave them for their own workstreams.
**Only touch `tools/ai_lane_controller/`, `tests/ai_lane_controller/`, and
`docs/` files listed above.**

## Evidence (tool calls this session)
- `git log fcd7016` → M3A confirmed
- `git log a46a8f3` → corrected design at HEAD
- `pytest tests/ai_lane_controller/` → **113 passed in 6.58s**
- `git diff --cached --name-only` → empty (nothing staged — the original
  handoff's "staged" claim was false)
- `grep -c "^def test_" tests/ai_lane_controller/*.py` → counts above
- `ls .git/index.lock` → stale lock present at handoff
- `git diff HEAD -- tools/ai_lane_controller/claim.py` → M4 changes confirmed
