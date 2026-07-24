---
thread_id: session-2026-07-24-keep-smaller-copy
current_session_id: 019f91d3-2741-7f83-af68-211796180474
parent_handoff_path: none
assignee: grok
status: CLOSED
created: 2026-07-24
---

# Session observations — Keep-Smaller-Copy TUI

## Observations

1. **Confirmation dialog is the #1 missing safety feature.** The app performed destructive file operations (move/copy/delete) with no confirmation gate. The operator experienced "many errors" and couldn't tell what happened because there was no transaction log until late in the session. A confirmation dialog was identified by the red-team audit as CRITICAL but was NOT implemented.

2. **Stop hook stale-verification receipts are a recurring pattern.** The Stop hook fired 3 times this session because I deleted test harnesses after running them, invalidating the verification receipt. The pattern: write harness → run test → delete harness → claim done. The fix should be: either keep the harness until the next behavioral test, or run a final syntax check as the last verification before cleanup.

3. **The `/go` H3 wiki query enhancement works.** Adding the wiki library query to `/go`'s discovery phase was a small, clean change (~25 lines). The principle extends: any skill that touches code should check the wiki for library knowledge before implementing. Source: session ID 019f91d3, turn where we added wiki query to `/go`.

4. **Advisory vs mandatory is the wrong default for safety features.** When I proposed advisory triggers for `/www` proactive use cases, the operator pushed back: "why advisory instead of mandatory?" The governance model's established pattern is mandatory structural enforcement for things that prevent documented failure classes. Advisory reproduces the preflight failure (rule existed in prose, didn't fire, 5 failures resulted).

5. **Textual 8.0.2 has breaking changes from 0.x that aren't well-documented.** `App.action_quit` became async, `Static.renderable` became `Static.content`. These hit us at runtime. A `/www` pre-adoption research run would have caught these before coding.

6. **The app's "no results" diagnostic text was the right call.** Adding the breakdown ("0 to move (src=199 tgt=10; 10 not smaller)") saved significant debugging time. Without it, the user would have seen an empty table with no explanation. This pattern (explain WHY, not just WHAT) should be standard for all empty-state displays.

## Seeds for future work

- **Confirmation dialog for Keep-Smaller-Copy** — the #1 unfinished item from the red-team audit
- **Swap Source/Target button** — trivial to implement, prevents the #1 user error
- **Progress counter during scan/move** — user asked for this directly, still missing
- **Dynamic button labels** (Move→Delete when Delete switch is ON)
- **Column sorting** in the results DataTable
- **Wiki health audit script** — quarterly staleness/coverage/orphan scan
- **`/www` proactive trigger design** — 3 mandatory, 5 advisory, 1 scheduled (the design from the /tp discussion)
