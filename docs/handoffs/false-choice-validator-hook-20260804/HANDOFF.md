---
# Chain header (mandatory — see references/core-fields.md)
chain_id: false-choice-validator
produced_at: 2026-08-04T18:00:00Z
produced_by: grok
current_session_id: 019fcb54-289a-7dd2-bf6b-5ef7847aa3e2
session_chain: [019fcb54-289a-7dd2-bf6b-5ef7847aa3e2]
accurate_as_of_head: 12217c2295fc4fbab0bbe45165bca71faf2ff1aa
source_transcript: ~/.grok/sessions/P%3A%5C/019fcb54-289a-7dd2-bf6b-5ef7847aa3e2/chat_history.jsonl
checkpoint: false
---

# Handoff: false_choice_validator.py — structural hook to prevent false-choices pattern

## 1. Objective

Build a Stop or PostToolUse hook (`false_choice_validator.py`) that scans the model's final output for false-binary patterns — framing independent, complementary actions as competing resource-allocation decisions requiring the operator to pick a subset. When detected, the hook rejects the output with a rewrite prompt.

This is the **structural backstop** that breaks the documented ~50% compliance ceiling for prose rules on response patterns (per `[[evidence-first-default-and-needless-confirmation]]` and `[[theatrical-contrition-and-over-apologetic-response-patterns]]`).

## 2. Status

CLOSED — implemented and committed (`fd8dfc7`).

**What was built:** `Stop_false_choice_validator.py` advisory gate registered in Stop.py dispatch chain as quality-class, priority 95, ADVISORY rollout mode. 12 tests pass (4 true positives, 6 true negatives, 1 edge case, 1 short-response bypass).

**Design decision:** started as advisory (systemMessage) rather than block to measure false-positive rate before promotion. This avoids the MINIMAL_BIAS_GATE noise problem documented in the handoff falsifier.

## 3. Motivation (why this work)

The operator said: "this behavior drives me crazy. How can we durably stop this?" — referring to the model presenting independent actions as "which subset would you like?" instead of just doing all of them.

The workspace has a prose rule (`AGENTS.md § "No false choices"`) but it has a documented ~50% compliance ceiling under session pressure. The `/www` research (2026-08-04) confirmed that:
- SAGE-Agent (Suri et al.): 1.5-2.7× reduction in unnecessary clarifications via structural decision protocols
- Empowerment-over-prohibition (dev.to): trigger→protocol pairs work better than prohibition
- Act-or-Escalate (DiSorbo & Ju): prompt-only interventions gain +0.2-1.9pp; structural enforcement is needed
- The most durable fix at the runtime layer is an output validator hook

## 4. Key decisions

- **Pattern:** same as existing `validate_pre_clarification_gate.py` — scan output, reject with rewrite prompt
- **Location:** Stop hook (scan final output before delivery to operator) OR PostToolUse on the response tool
- **Trigger patterns to detect:** (from research + session examples)
  - "which subset would you like" / "should I do A or B" where both have positive ROI
  - "shall I proceed with X, or Y, or both?" — the "or both" tells is the signal that they're independent
  - "would you like me to" + a menu of independent actions
  - Presenting N>1 independent actions as a numbered list asking the operator to pick, when all have positive ROI and none blocks the others

## 5. Acceptance criteria

1. Hook script exists at `P:/.claude/hooks/Stop_false_choice_validator.py` (or equivalent Grok Build hook path)
2. Registered in the hook dispatch chain (settings.json or equivalent)
3. Detects the four trigger patterns above in a test input
4. Does NOT fire on legitimate either/or questions (where the options genuinely compete — e.g., "should we use PostgreSQL or SQLite?" where only one can be chosen)
5. Rejects with a descriptive stderr message: "FALSE CHOICE DETECTED: these actions are independent and all have positive ROI. Do all of them, don't ask which subset."
6. Has at least 3 test cases (true positive, true negative, edge case)
7. Does not block on keyword false positives (same lesson as MINIMAL_BIAS_GATE — detect recommendation-shaped language, not just keywords)

## 6. Read-first

- `P:/.data/wiki/concepts/false-choices-parallel-branch-framing.md` — the full pattern + research
- `P:/.data/wiki/concepts/evidence-first-default-and-needless-confirmation.md` — the ~50% compliance ceiling finding
- `P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md` § "What does NOT work" — why prose rules decay
- `C:/Users/brsth/.grok/AGENTS.md` § "No false choices" (revised 2026-08-04 with parallel-branch framing)
- Existing hook pattern: `P:/.claude/hooks/Stop_*.py` for the dispatch chain shape

## 7. Evidence

- Session 019fcb54: operator asked "which subset?" correction after model presented 4 independent fixes as a menu
- `/www` research subagent (019fcd8f): 12 findings on structural vs behavioral enforcement for decision deferral
- `/tp` critique of correction-response rule: confirmed prose-rule-decay problem
- Commit `f7f820c`: AGENTS.md parallel-branch framing + cost-frame (the prose workaround this hook would backstop)

## 8. Suggested skills (grounded)

- `/go` to implement the hook script + register it + write tests
- `/skill-dev measure` after implementation to verify it fires correctly
- `/tp` on the hook design before implementing — the false-positive risk (detecting legitimate either/or questions) needs adversarial review

## 9. Falsifier

This hook is wrong if:
- It fires on legitimate either/or questions (false positive rate >10%)
- It misses false-choice patterns that don't use the trigger phrases (false negative rate >30%)
- It becomes another MINIMAL_BIAS_GATE — keyword-matching on "or" or "which" instead of detecting the structural pattern (independent actions framed as competing)
- The operator disables it because it's too noisy

## 10. Other outstanding streams from this session

All other work streams from session 019fcb54 are **complete and committed**:
- Correction-response discipline rule (created, /tp critiqued, revised, /www researched) — commits `af75b66`, `0b3bf2c`, `f7f820c`
- AGY headless failure documentation (diagnosed via /why, documented in tool-fallbacks + wiki, /tp dispatch enforced) — commits `005d623`, `f7f820c`
- /why → /www conditional bridge (Step 14a added) — commit `f7f820c`
- /www prompt enhancement (Phase 1 → Phase 2 context injection) — commit `f7f820c`
- False-choices parallel-branch framing (researched, AGENTS.md rule + wiki concept) — commits `f7f820c`, `005d623`

## 11. Last user message (verbatim)

"/user:handoff"
