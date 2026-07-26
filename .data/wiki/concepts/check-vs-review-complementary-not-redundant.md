---
title: "/check and /review are complementary, not redundant"
created: 2026-07-22
source: session-2026-07-21
tags: [verification, code-review, check-skill, review-skill, edge-case-testing, complementary-verification, failure-mode]
summary: >
  /check verifies "did you do what you said" (trace review against session
  claims). /review asks "what bugs exist" (fresh-eyes code inspection with
  hand-crafted edge cases). The two are complementary: 4 critical bugs passed
  160 tests + 3 /check verifiers but were caught by 2 /review specialists.
  Running /check alone gives false confidence; running /review alone misses
  session-correctness issues. Run both for load-bearing work.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/tool-use-protocol-subagent-critical-friend
    type: related
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: related
---

## Summary

`/check` and `/review` answer different questions. Conflating them leads to false confidence: tests pass, /check passes, but critical bugs ship.

## The distinction

| Skill | Question it answers | Method | What it catches | What it misses |
|---|---|---|---|---|
| `/check` | "Did the session do what it said?" | Trace review: verify session claims against actual files, tests, state | Missing actions, incomplete work, unverified claims, test failures | Edge-case bugs that pass tests; logic errors in new code |
| `/review` | "What bugs exist in this code?" | Fresh-eyes code inspection: read the diff, hand-craft edge cases, probe boundaries | Logic errors, edge-case failures, missing validation, security issues | Whether the session completed its stated goals |

## The evidence (session 2026-07-21)

Two new CLI scripts (`verify_handoff.py`, `migrate_handoff.py`) had 4 critical bugs:

1. **Silent migration failure** — `re.sub` matched nothing but `changes.append()` claimed success
2. **SHA whitespace corruption** — whitespace-padded SHAs produced duplicate `accurate_as_of_head:` fields
3. **No provenance** — `--update` silently rewrote SHAs without recording who/when
4. **Non-atomic writes** — `Path.write_text()` without `.tmp + os.replace`

All 4 passed:
- 160 existing tests (`pytest tests/ -q`)
- 3 /check verifiers (skills PASS, CLIs PASS, handoffs FAIL-but-pre-existing)

All 4 were caught by:
- 2 /review specialists (correctness + integrity lenses) via hand-crafted edge-case inputs

The /check verifiers ran the test suite and confirmed the CLIs worked on canonical inputs. They did NOT write adversarial test cases (e.g., "what if the SHA has whitespace?", "what if handoff_type is missing?"). The /review specialists did.

## Why this happens (the mechanism)

`/check` is session-grounded: it verifies the agent's claims against reality. If the agent said "migrate adds accurate_as_of_head" and the field IS present on canonical inputs, /check passes. The bug only manifests on non-canonical inputs (no `handoff_type:` anchor) that the agent never tested.

`/review` is code-grounded: it reads the code and asks "what inputs would break this?" The specialist writes a hand-crafted test with the edge case, runs it, observes the failure. This is independent of what the session claimed.

The two methods are structurally different: trace verification vs adversarial probing. Neither subsumes the other.

## When to run which

| Scenario | Run /check? | Run /review? |
|---|---|---|
| Session touched hooks, plugins, schemas, contracts | Yes | Yes (auto-triggered by /check) |
| Session wrote new code (CLIs, scripts, modules) | Yes | **Yes** (critical — /check won't catch edge-case bugs) |
| Session edited docs only | Yes | Optional |
| Session was Q&A / research only | Skip | Skip |
| Session made config changes | Yes | Optional |

**The /check → /review auto-escalation** (in the /check skill) fires when load-bearing surfaces are touched. This is the right default. But for new code specifically, /review is needed even without the auto-trigger.

## Related

- [[tool-use-protocol-subagent-critical-friend]] — the /review specialists' tool use protocol; same principle (independent evidence > shared framing)
- [[external-state-cross-check-as-structural-fix]] — /review's edge-case testing is an instance of external-state cross-check (the code's actual behavior is external to the session's claims)

## EVIDENCE_GAP

Single-session evidence (2026-07-21). The 4-bug catch rate may not generalize — it could be an outlier. More sessions with both /check and /review run on the same code would calibrate the expected catch rate.

## Auto-related

- [[claude-code-verify-builtin-skill]]

