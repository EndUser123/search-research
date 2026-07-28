---
thread_id: 926c0c13-78b0-41bd-990e-a42eed23c0f4
parent_handoff_path: P:/docs/handoffs/keep-smaller-copy-session-continue-20260728/HANDOFF.md
current_session_id: 019fa94d-5608-7b21-b8d7-dbe609f92df3
current_terminal_id: console_38b8d474-5cd0-4bf1-a306-6a77
produced_at: 2026-07-28T17:07:11Z
status: closed
handoff_type: investigation
accurate_as_of_head: e1d7c9c14786252ed9b63e235261441ee0e91ca8
assigned_to: grok
assigned_at: 2026-07-28T17:07:11Z
assigned_by: 019fa94d-5608-7b21-b8d7-dbe609f92df3
---

# Wire vulture into “full verification” (`/check` + policy)

## Objective

Make **vulture** (Python dead-code detection) part of the fleet verification path so sessions that run “full verification” are not limited to ruff F-rules + pyright + pytest; update skill + wiki so the gap that session 019fa94d hit does not recur.

## Status

READY_FOR_REVIEW — implemented in /check Step 0.9 (advisory). See Revision 1.

## Producing context

- **Date:** 2026-07-28  
- **Session:** `019fa94d-5608-7b21-b8d7-dbe609f92df3`  
- **Operator question (verbatim):** `why didn't we do vulture on the full verification?`  
- **Trigger app:** Keep-Smaller-Copy TUI (sample Textual codebase with dynamic handlers)

## Read-first list

1. `P:/.data/wiki/concepts/dead-code-detection-workflow.md` — recommendations; now includes `/check` Step 0.9 as **not-yet-wired** + Textual FP note (updated 2026-07-28)  
2. `C:\Users\brsth\.grok\skills\check\SKILL.md` (or `P:/.grok/skills/check` if present) — Step 0.9 deterministic pre-check (ruff + pyright today)  
3. Sample: `D:/.code/Keep-Smaller-Copy/app.py` — unfiltered vulture is noisy on Textual  
4. Adjacent design stream: `P:/docs/handoffs/verification-protocol-design-20260728/HANDOFF.md` — align tier placement if multi-tier verification lands  

## Related wiki concepts

- [[dead-code-detection-workflow]] — primary authority for this stream  
- [[verification-before-completion-principle]]  
- [[ai-agent-verification-orchestration-best-practices-2026]]  

## Verified facts

- [FACT] Session “full verification” used pytest, ruff E/F, pyright, `/check`, `/review` — **not** vulture.  
- [FACT] `/check` Step 0.9 contract (skill text): ruff + pyright on changed `.py`; no vulture.  
- [FACT] Wiki historically recommended vulture for `/close`, `/aar`, pre-push only; 2026-07-28 update added `/check` as recommended-but-unwired.  
- [FACT] `vulture` is installed on this host; `vulture D:\.code\Keep-Smaller-Copy\app.py --min-confidence 60` reports large numbers of Textual framework false positives (`compose`, `@on` handlers, `watch_*`, BINDINGS, CSS).  
- [FACT] Ruff F401 catches unused imports, not unused methods/classes generally — different detector class from vulture.  
- [INFERENCE] Fail-closed vulture without whitelist will burn trust on Textual and other dynamic frameworks.

## Current state

| Component | State |
|-----------|--------|
| Wiki gap documented | Yes |
| `/check` Step 0.9 runs vulture | No |
| Framework whitelist policy | Not formalized |
| Operator expectation | “Full verification” should consider dead code |

## Task packets

### VULT-01 — Policy decision: advisory vs fail

- **goal:** Choose whether vulture blocks `/check` or is advisory.  
- **options:** (a) advisory always; (b) fail ≥80 confidence with whitelist; (c) only on `/close`.  
- **lead:** **(a)** for `/check`, **(b)** for pre-push once whitelist exists.  
- **acceptance:** decision written in skill + wiki with criterion.  
- **verification level required:** STATIC_INSPECTION  

### VULT-02 — Implement Step 0.9 vulture pass

- **goal:** After VULT-01, add vulture to `/check` deterministic pre-check for changed `.py` files.  
- **in scope:** check skill body, optional helper script under skill `__lib/`.  
- **out of scope:** rewriting all Textual apps.  
- **acceptance:**  
  1. Skill documents command + soft-fail if vulture missing.  
  2. Smoke on one plain module + one Textual file shows no false fail on `compose`.  
  3. Wiki table marks `/check` as wired (or still advisory with measured FP notes).  
- **falsifier:** Textual project always fails `/check` on framework methods; or skill still silent after “done.”  
- **verification level required:** LIVE_BEHAVIOR (run pre-check)  

### VULT-03 — Whitelist / allowlist for dynamic frameworks

- **goal:** Document or ship a default allowlist pattern for Textual (`compose`, `watch_*`, `@on`, BINDINGS) and plugin dynamic dispatch.  
- **acceptance:** documented path; Keep-Smaller-Copy sample run is interpretable.  
- **verification level required:** STATIC_INSPECTION + sample vulture command  

## Open decisions

1. Advisory vs blocking (see VULT-01).  
2. Own skill path: `~/.grok/skills/check` vs `P:/.grok/skills/check` — use whichever is actually loaded on Grok Build (verify before edit).

## Hard constraints

- Do not delete Textual handlers based on raw vulture output.  
- Soft-skip if `vulture` not installed (same fail-open pattern as other optional tools).  
- Coordinate with `verification-protocol-design` handoff if changing verification tiers broadly.

## Cross-reference couplings

- Wiki [[dead-code-detection-workflow]] → must stay consistent with skill after implement.  
- Sibling `/tp` stream may **rank** this item but does not own implementation: `P:/docs/handoffs/tp-workflow-efficiency-incomplete-20260728/HANDOFF.md`.  
- Product app is sample only: `P:/docs/handoffs/keep-smaller-copy-product-close-20260728/HANDOFF.md`.  
- Superseded combined handoff: `keep-smaller-copy-session-continue-20260728`.

## Explicit non-goals

- Do not use vulture as a substitute for `/review` logic bugs.  
- Do not fail the Keep-Smaller-Copy product stream solely because unfiltered vulture is noisy.

## Resumption protocol

1. Read wiki concept + check SKILL Step 0.9.  
2. Decide VULT-01.  
3. Implement VULT-02 with VULT-03 allowlist.  
4. Smoke: plain package + `D:\.code\Keep-Smaller-Copy\app.py`.  

## Suggested next invocation

```text
Read P:/docs/handoffs/vulture-in-check-verification-20260728/HANDOFF.md.
Implement advisory vulture in /check Step 0.9 with soft-fail if missing,
plus Textual-aware allowlist policy. Update wiki dead-code-detection-workflow
to mark /check as wired. Smoke on Keep-Smaller-Copy without false-failing compose.
```

## Last user message (verbatim)

> shouldn't those be three different handoff?

## Dependencies

- **Requires:** nothing for design; implementation needs skill path resolution  
- **Blocks:** nothing  
- **Non-blocking to:** product-close, incomplete `/tp`  

## Falsifier (handoff obsolete)

`/check` Step 0.9 runs (or explicitly declines with measured rationale) vulture; wiki table matches reality; Textual sample does not fail on framework methods.

---

## Revision 1 — 20260728T173000Z (session 019fa94d)

**Trigger:** /go do wire vulture into standard verification.

**What changed:**
- Implemented `P:/.grok/skills/check/__lib/vulture_precheck.py` (advisory, soft-skip, Textual/decorator FP filter)
- Updated `P:/.grok/skills/check/SKILL.md` Step 0.9 to run vulture + merge into deterministic-check.json
- Wiki [[dead-code-detection-workflow]] marked /check as **wired**
- Tests: `tests/test_vulture_precheck.py` (5 tests)
- Smoke: Keep-Smaller-Copy app.py at conf 60 → 0 remaining / 56 framework FP filtered; preprocessor still flags real unused import

**Status update:** READY_FOR_REVIEW / implement complete — operator may close this handoff after acceptance.

**Policy locked:** VULT-01 (a) advisory for /check; does not alone fail CHECK.
