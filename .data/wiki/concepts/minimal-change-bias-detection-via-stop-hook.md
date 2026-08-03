---
title: "Minimal-change bias detection via Stop hook"
created: 2026-08-03
updated: 2026-08-03
source: session 019fc0a7
tags: [hooks, behavioral-enforcement, minimal-bias, stop-hook, structural-fix]
host: grok
agent: grok
verification: tested-2026-08-02
cognitive_load: 2
summary: >
  Behavioral rules in AGENTS.md don't fire under task pressure. A Stop hook
  that scans the agent's output for minimal-change language in architectural
  contexts is the structural fix — it forces re-examination against the
  operator's stated preference (optimal long-term, transition effort
  irrelevant) before the response ships.
---

## Decision context

Session 019fc0a7 (2026-08-01): the agent produced five minimal verdicts (SIMPLIFY_EXISTING, EXTEND_EXISTING, BLOCKED_PENDING_EVIDENCE, CLARIFY_EXISTING, NO_CHANGE) for a system redesign review, despite AGENTS.md explicitly stating "Optimal long-term solution (not minimal fix)" and "Transition effort is not a selection criterion." The rule was active, read, and acknowledged — but didn't fire under the pressure of producing a comprehensive review.

The operator caught this and asked: "Should we make a hook?" The answer was yes — this is the same failure class documented in `[[mechanical-enforcement-over-behavioral-reminder]]`: behavioral rules don't fire under pressure; structural enforcement does.

## The pattern

**Failure class:** AGENTS.md rule exists → agent reads it → rule doesn't fire under task pressure → agent defaults to minimal recommendations.

**Structural fix:** Stop hook scans `lastAssistantMessage` for three conditions:
1. Minimal-change language ("minimal change", "extend existing", "over-engineering", etc.)
2. Architectural/verdict language ("verdict", "recommendation", "should we build")
3. Absence of explicit justification ("minimal IS optimal because...")

If all three fire, the hook blocks (exit 2) with a framing question that forces re-examination. The agent must either justify the minimal recommendation or revise it.

**Key design decisions:**
- Review-context suppressor: code-review output with line-number references (`L123: simplify the existing...`) doesn't trigger the gate — these are legitimate review findings, not architectural disposition.
- Escape hatch: output containing "minimal IS optimal because" or "transition effort is not a factor" passes through — the agent has consciously justified the recommendation.
- Trivial-context skip: typos, single-line fixes, import errors bypass the gate entirely.
- Fail-open on any error (same pattern as `close_enforcement_gate.py`).

## Falsifier

The hook is wrong if, within 6 months:
- It fires so often on false positives that the operator disables it (tune the regexes)
- It never fires on real minimal-bias (the detection patterns are too narrow)
- The escape hatch is so broad that agents learn to game it (add "because" to everything)
- The 8-continuation cap means the gate is overridden after 8 blocks anyway (accepted limitation)

## Sources

- Hook script: `~/.grok/hooks/scripts/minimal_bias_gate.py` (commit `0e867ae`, fixes `faf5c8f`)
- Registration: `~/.grok/hooks/minimal-bias-gate.json`
- Test suite: 12/12 cases pass (including 4 false-positive cases)
- Reference: `[[mechanical-enforcement-over-behavioral-reminder]]`
- Reference: `~/.grok/AGENTS.md` § "Optimal long-term solution (not minimal fix)"

## What this does NOT do

- Does not check "is the problem real?" — only checks "is minimal optimal?" The companion check (problem-existence) is a separate concern.
- Does not enforce on non-architectural work (code fixes, typo corrections, task instructions).
- Does not block permanently — the 8-continuation cap means the gate can be overridden by repeated attempts.
