---
thread_id: recommendation-validation-design
parent_handoff_path: none
current_session_id: 019fd698-f697-7212-af73-19143fd58dcd
current_terminal_id: console_a8dfe293-484b-49d1-8c12-b6d7
produced_at: 2026-08-07T13:00:00Z
status: in-progress
handoff_type: investigation
accurate_as_of_head: ee3b1bf
source_transcript: ~/.grok/sessions/P%3A%5C/019fd698-f697-7212-af73-19143fd58dcd/chat_history.jsonl
---

# Handoff: Recommendation validation capability — design + implementation

## Goal

Design and implement a reusable skill-graph component that validates
architectural recommendations against external evidence before persisting
them. Any skill that produces recommendations (/tp, /go, /design, /refine,
/plan-writer) should be able to invoke it.

## 1. Operator's verbatim request

> "It should be a reusable component in the skill graph that any skill can invoke when useful."

Then:

> "/go do them all please, plus /check and /review" (referring to Option A + Option B + the 5 consumer skills)

Then:

> "/design" (to produce the formal design doc)

## 2. What was done

### Design doc produced (reviewer + critical friend + cross-model critique)

The design went through the full /design loop:
- Writer (inline after subagent stalled)
- Reviewer round 1: 18 findings (3 critical, 7 major, 6 minor, 2 nit)
- Revision: all criticals + majors addressed
- Re-review: 1 partial critical resolved + minor path inconsistencies fixed
- Critical friend: REVISE — 3 strong challenges accepted
- Cross-model critique (/tp {5}): DeepSeek REVISE + GPT-5.6 REVISE + 2 lenses failed (Cohere rate-limited, OpenRouter slug changed)

### Design doc location

**`P:\docs\handoffs\recommendation-validation-design-20260807\grok-design-doc.md`**

(Copied from temp: the original is at `C:\Users\brsth\AppData\Local\Temp\grok-design-f50ad782\grok-design-doc-f50ad782.md`)

### Wiki concept written

`P:/.data/wiki/concepts/reasoning-first-search-never-claim-without-checking.md`
— documents the 5 instances that motivated the design, with receipts and
the structural fix path.

## 3. Key decisions

- **Three-layer architecture:** shared library (Layer 1) + /tp auto-fire gate (Layer 2, deferred) + Stop hook backstop (Layer 3, primary enforcement)
- **Keyword-based detection, not LLM-based:** deterministic, testable, fast (<10ms)
- **Unit 0 split into 0a + 0b:** 0a tests detection accuracy (TP/FP/FN over labeled corpus), 0b tests /www value (retrodiction). Both must pass before Unit 1.
- **Structured validation receipts** instead of proximity-based URL checks (from GPT-5.6 codex lens)
- **Negative keyword list** for the "hook/gate" poison problem (from DeepSeek lens)

## 4. Evidence

- Design doc: `P:\docs\handoffs\recommendation-validation-design-20260807\grok-design-doc.md`
- Review: `C:\Users\brsth\AppData\Local\Temp\grok-design-f50ad782\grok-design-review-f50ad782.md`
- Re-review: `C:\Users\brsth\AppData\Local\Temp\grok-design-f50ad782\grok-design-rereview-f50ad782.md`
- Critical friend: `C:\Users\brsth\AppData\Local\Temp\grok-design-f50ad782\grok-design-critique-f50ad782.md`
- DeepSeek lens output: subagent 019fdc2d-d997-71f0-88d1-6b38596b0cb5
- GPT-5.6 codex lens output: task 019fdc2e-2dd2-72b0-8c78-afa22d1dd198
- Wiki concept: `P:/.data/wiki/concepts/reasoning-first-search-never-claim-without-checking.md`
- /www research on pre-commit gates: IMTI, CircleCI, pydevtools, ianymu (sources in wiki concept `grok-build-grpc-web-billing-endpoint.md`)

## 5. Open items — implementation units

| Unit | What | Disposition | Gate |
|---|---|---|---|
| 0a | Detection accuracy test (20-item labeled corpus, TP/FP/FN) | **DONE** — FP=0%, FN=0% | PASS |
| 0b | Value retrodiction (/www on true positives from 0a) | **DONE** — 2 cases changed | PASS |
| 1 | `needs_external_validation.py` shared library | **DONE** — 7/7 tests pass | — |
| 2 | /tp auto-fire gate (Step 5.1 in SKILL.md) | DEFERRED | Layer 2 is convenience, not enforcement |
| 3 | Stop hook backstop (`Stop_validate_recommendations.py`) | **DONE — ADVISORY MODE** — 10/10 tests pass | Promote to blocking after measurement gate (see Rollout) |
| 4-7 | Consumer skill wiring (/go, /design, /refine, /plan-writer) | DEFERRED | One skill at a time |
| 8 | `check_wiki_before_claim.py` pre-claim wiki check | HANDOFF | Addresses broader "claim without checking" pattern |
| 9 | Stop hook extension for unsupported negative claims | DEFERRED | Extends Unit 3 |

## 6. Next steps (for a fresh session)

1. **Units 0a, 0b, 1, 3 are DONE.** The shared library and Stop hook are
   implemented, tested, and committed. **The hook runs in ADVISORY mode**
   (surfaces findings without blocking), per the
   `advisory-vs-blocking-enforcement-decision-2026` decision.
2. **Measurement phase (promotion gate for blocking):** collect ≥50 natural-use
   detections across real sessions. Label a subset. Compute Wilson 95% CI on
   the FP rate. Promote to blocking only if upper bound ≤30% FP.
3. **Deferred risk Cluster B (model-name FP):** bare model names ("deepseek",
   "nvidia", "mimo") in `external_tools` trigger on routine fleet-routing
   recommendations. Needs suppression logic: if model name appears alongside
   fleet-routing vocabulary ("lane", "pool", "quota", "routing", "spawn"),
   suppress. Design and implement after the measurement phase has data.
4. **Unit 2** (/tp auto-fire gate): add Step 5.1 to `/tp` SKILL.md when ready.
5. **Units 4-7** (consumer wiring): wire `needs_external_validation()` into
   `/go`, `/design`, `/refine`, `/plan-writer` — one skill at a time.
6. **Unit 8** (`check_wiki_before_claim.py`): implement the pre-claim wiki
   grep function for the broader "claim without checking" pattern.

## 7. Read first (for a fresh session)

- `P:\docs\handoffs\recommendation-validation-design-20260807\grok-design-doc.md` — the design
- `P:/.data/wiki/concepts/reasoning-first-search-never-claim-without-checking.md` — the problem this solves
- `P:/.data/wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md` — the enforcement principle
- `P:/.data/wiki/concepts/grok-build-grpc-web-billing-endpoint.md` — the session that triggered the need (pre-commit gate recommendation without /www)

## 8. Cross-reference couplings

- `fleet_quota.py` `check_grok()` — the session work that produced the unvalidated recommendation
- `/tp` SKILL.md Step 5.1 — where Unit 2 would be inserted
- `~/.grok/docs/user-guide/10-hooks.md` — Stop hook input schema (`lastAssistantMessage` field)
- `~/.grok/config.toml` — where the Stop hook would be registered

## Other outstanding streams

- The quota dashboard fixes (SEC-6, SEC-7, CORR-1) are DONE and verified
- The skill script defect cleanup (86→14) is DONE
- The wiki concepts (grok-build-grpc-web-billing-endpoint, grok-headless-slash-command-routing-gotcha, reasoning-first-search-never) are written and committed

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-08-07 | grok (019fd698) | Initial handoff — design doc complete, implementation pending Unit 0a |
| 2026-08-07 | grok (019fdc43) | Units 0a+0b+1+3 DONE: corpus (FP=0%, FN=0%), retrodiction (2 changed), shared library (7/7 tests), Stop hook (9/9 tests). Committed to ~/.grok. |
