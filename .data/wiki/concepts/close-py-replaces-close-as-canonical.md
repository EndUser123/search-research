---
title: "close-py replaces /close as canonical session close skill"
created: 2026-08-12
tags: [decision, architecture, close-py, close, skill-replacement]
host: both
agent: grok
verification: observed
---

# close-py replaces /close as canonical session close skill

## Decision

On 2026-08-11/12, `/close-py` replaced `/close` as the canonical session close skill. `/close`'s SKILL.md was deprecated (`user-invocable: false`). The old `/close/__lib/` scanners were consolidated into `close-py/__lib/_scanners/` by a sibling session.

## Selection criterion

Optimal long-term: the Python orchestrator in close-py controls the pipeline loop deterministically — the LLM cannot skip phases because the script drives each step. This closes the enforcement gap documented in `[[agentic-sdlc-lifecycle-validated-end-to-end]]` where `/close`'s internal gates could be bypassed under closure pressure.

## Rejected alternatives

- **Option B (move __lib/ into close-py, delete close/ entirely)** — rejected because 7+ consumers import from the old path. ~30+ files would need import changes. High regression risk.
- **Option C (rename: /close-py becomes /close)** — rejected because wiki/handoffs reference the old prose behavior. Confusing for ~2 weeks. Medium risk.

Option A (retire prose SKILL.md, keep __lib/ as shared library) was chosen because it achieves the goal without touching any imports. A sibling session later consolidated __lib/ into close-py/__lib/_scanners/, which is the structural version of Option B done correctly with import path updates.

## Known issues

1. **close_enforcement_gate.py compatibility** — the Stop hook's `is_close_context()` initially did not recognize close-py output format (no old section headers). Fixed 2026-08-12 by adding state-file-based detection (Path 2).

2. **AAR receipt session binding** — close-py's retrospective gate validates AAR receipts by exact session ID match. AAR operates on session chains, but the gate is single-session. Design decision needed on chain-aware validation.

3. **Ship-py check phase scope** — `build_diff_summary()` used `HEAD~1..HEAD` (1-commit range) instead of session-scoped range. Fixed 2026-08-12 by using `_get_session_start_time()` to find all session commits.

## Relations

- [[agentic-sdlc-lifecycle-validated-end-to-end]]
- [[no-question-theater]]
- [[close-pipeline-completeness-vs-priority-gap]]
