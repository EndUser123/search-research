# Critical Review — "Use a `type: "agent"` Stop hook" proposal
**Recorded at:** 2026-07-18
**Scope:** determine whether the proposal describes something we already have, versus something we'd need to build.

## TL;DR (factual comparison, not advocacy)

| Proposal asks | What we already have | What's missing |
|---|---|---|
| `type: "agent"` Stop hook as primary mechanism | **No** — `type: "agent"` does not appear anywhere in `P:/.claude/settings.json` hooks; only `type: "command"` is registered. Docs say it exists in CC 2.1.214 but it is **experimental and unwired locally**. | Pilot wiring required. |
| `type: "prompt"` Stop hook as cheap classifier | **No** in settings.json; same experimental/unwired status as agent. | Pilot wiring required. |
| LLM-based reasoning review of the proposed response | **Yes** — `epistemic_validator.py` (cc-aca-epistemic plugin) is wired through `Stop.py`; **but** it operates in `warn` mode (per `~/.claude/settings.json`: `EPISTEMIC_CAUSAL_MODE: warn`, `EPISTEMIC_COMPARATIVE_MODE: warn`, `EPISTEMIC_CONTRACT_MODE: warn`). | Mode promotion to advisory-continuing (not block); calibration first. |
| External LLM challenge | **Yes, partial** — `anti_dodge_judge.py` exists as an LLM-based external judge for hook answers (per `MECHANISM INVENTORY` at top of this session). Specifics of when it actually fires are not verified in this turn. | Active routing — currently disabled (`ANTI_DODGE_JUDGE_ENABLED: true` flag is on; fail-open policy confirmed by memory `hook_quality_vs_policy_severity`). Verify it's invoking a non-CCR provider. |
| Cross-model independence claim | **Not yet earned** | Same blocker as the v2 falsification experiment. |

## Verification evidence for the table

1. `claude --version` → `2.1.214 (Claude Code)`. WebFetch on `https://code.claude.com/docs/en/hooks` confirms five hook handler types including `agent` and `prompt`; `agent` is marked **experimental**, `prompt` is not. Version-when-introduced: **not specified in the docs**.
2. `grep "\"type\"" P:/.claude/settings.json` returns only `"type": "command"`. No `agent` or `prompt` lines in the *active* settings file.
3. `grep -r "semantic_critic|anti_dodge_judge|epistemic_validator" P:/.claude` returns hits in `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/` — these capabilities exist as code. They are reached via `Stop.py` (verified: `P:/.claude/hooks/Stop.py:1219` imports `anti_sycophancy.overconfidence_detector`, lines 1229-1303 wire the detectors into `Stop` output).
4. `P:/.claude/settings.json` line 70-73 set `EPISTEMIC_CAUSAL_MODE: warn`, `EPISTEMIC_COMPARATIVE_MODE: warn`, `EPISTEMIC_CONTRACT_MODE: warn`. **All three are warn, not block.** The proposal explicitly says: "begin as a measured pilot rather than an irreversible production dependency" — that maps to the existing `warn`-mode posture, which is already in place.

## What the proposal gets right

- **The behavior the proposal targets is real.** The Grok / Stale-PATH / "fixed" closure incidents all happened at the **output-stage, after commitment**. A `Stop` hook that asks "is this conclusion earned?" is the right boundary. The proposal's targeted question is materially better than the existing `hypothesis_template` structure-check in epistemic_validator: the proposal asks about **support**, the existing detectors ask about **shape**.

- **The "experimental" qualifier is correct.** Per the docs, `type: "agent"` is experimental and may change. Per the prompt's existing gate-discrimination memory `feedback_gate_discrimination_rule`, anything that becomes blocking needs measured TP/FP on a real corpus before promotion. The proposal's Phase 1 shadow + Phase 2 continue-on-block + Phase 3 escalation sequencing is consistent with that discipline.

- **The seven questions the proposal puts to the agent hook are good.** "What observations support the conclusion? Does a credible alternative predict the same observations? Was a test actually performed? Does the conclusion stay within what the test proves?" — these are exactly the items the v2 §4.2 ephemeral proxy failed to discriminate. If the agent hook answers these, it materially reduces the prior experiment's failure mode.

- **The "routing caveat" is correct and important.** The proposal explicitly says: "The `model` field on prompt and agent hooks does not solve your CCR problem by itself … requested identity is not proof of consumed identity." This is the exact conclusion the v2 falsification experiment reached via the four 429s from `provider(minimax,MiniMax-M3[1m])`. The proposal correctly refuses to over-claim. The user is reading the same constraint that the v2 experiment surfaced.

- **Routing-investigation is not a precondition.** The proposal correctly says: "Do not wait for a perfect cross-model experiment before using the hook." This is the conclusion the entire investigation arrived at: `NO_FALSIFICATION_INTERVENTION_YET_EARNED` plus parallel infrastructure blockers. The proposal operationalizes the result by **skipping the cross-model layer entirely** as a precondition for the agent hook itself, and treating external escalation as the only path where genuine independence matters.

## What the proposal gets wrong or risks

1. **It understates what's already wired but mis-named.** The LLM-based reasoning review (`epistemic_validator`, `overconfidence_detector`, `unverified_stance`, `cross_validator`, `fabrication_detector`) **is already in the Stop path**. The proposal's question — "is this conclusion earned?" — maps onto the *combined output* of those detectors more than onto a single new feature. **Before building a new agent hook from scratch, the cheaper experiment is: take the existing `Stop_aggregator`-collected detector output, score it against the v2 corpus, and measure whether the existing detectors' union *already* catches the cases the proposal would target.** If yes, mode-promotion (`warn` → `block`) on the union is the smallest possible intervention — no new hook required.

2. **`type: "agent"` is experimental; the proposal glosses over the cost of discovering what it actually does under CCR routing.** A `type: "agent"` Stop hook that asks a model "is this conclusion earned?" — what model is that? The proposal acknowledges the routing caveat but doesn't propose a concrete guard. A failed/wrong agent-hook decision is **catastrophic** because Stop is the last gate: if it returns `{ok:false}` based on a hallucinated counterargument, the agent reworks the entire answer needlessly; if it returns `{ok:true}` when the answer is unsupported, the user sees the unrevised bad answer. **The proposal needs a concrete output-contract test, not just a behavior contract**, before any pilot. (Memory `blocking_stderr_standard.md` is directly relevant: Stop output contract is strict — block is `{"decision":"block","reason":"..."}`; allow is emit `{}` or nothing. The proposal's `{"ok":true}` shape must be reconciled with that contract before any pilot, OR the proposal needs to be routed through the agent hook output contract rather than the standard Stop output contract.)

3. **It conflates two distinct failure modes.** The proposed question "did the session perform a test that distinguishes them?" is a *reasoning*-quality check. The existing detector stack catches *output-shape* claims (overconfidence, unverified stance, fabrication). The proposal wants reasoning-quality checks; the existing detectors mostly check text shape. These do not substitute for each other. The proposal implicitly assumes the agent hook can do reasoning checks that the current detectors do not do. **That assumption needs measurement, not assertion.** Specifically: an agent hook running on the v2 corpus needs to show TP>>0 on at least one of C01/C03/C05/C08/C09/C10, FP=0 on C04 (mechanical), and not regress U-preservation on C05.

4. **The "low-cost shadow evaluator" framing risks installing a shadow that never sees production data.** The proposal's Phase 1 says "evaluate ~20–50 real turns." The repo has evidence that `Stop_fake_done_detector` already exists and has had FP-tuning done (task #1089: "Fix Stop-hook FP: UNVERIFIED PERFORMANCE ATTRIBUTION matches ROI prose" — completed). That tells us calibration matters **and** the fix wasn't enough — task #1122 is still `[in_progress]` for "Stop-hook Part C.1 false positive (autonomous/background misfire)." An agent hook with similar FP risk needs calibration telemetry from day one, not just shadow data collection.

5. **The proposed "Stop prompt → Stop agent → external LLM" layering assumes each layer can fall open safely.** The proposal says external review "fails open" for ordinary work. But the agent hook's `{ok:false, reason}` is a *Block* on Stop — fail-open means "if no agent decision, allow Stop." That's the right default. But it means a misconfigured agent hook produces no protection at all. **The fail-open posture is itself the unknown**: every previous gate-discrimination memory in this repo records the same lesson (3 non-discrimination cases; semantic_critic inadequate at 0/40). The proposal does not address this directly. A `warn`-mode adversary check on the agent hook's own behavior — "did the agent-hook fire AND return ok=false correctly?" — needs to be added before the agent hook becomes blocking.

## A sharper version of the proposal that accounts for the existing code

The smallest productive next step is **not** "wire a new agent hook." It is:

1. **Measure first** — take the existing `Stop_aggregator`'s collected output for the v2 corpus (C01-C10) and score it against the rubric. Estimate the current detectors' coverage of the failure mode.
2. **If coverage is insufficient, propose a discriminating feature for the epistemic stack** (e.g., a `mechanism_citation_gate.py` that compares a stated mechanism against the file:line of code it claims) rather than a new agent hook. The reasoning the proposal wants is precisely the **mechanism-citation-class** check that `overconfidence_detector` already does at 863 lines — extending that stack costs one file, no new hook event, and no new experimental surface.
3. **If coverage is sufficient, mode-promote** `EPISTEMIC_CAUSAL_MODE` from `warn` to `block` *after corpus measurement*. This is the smallest-friction path to the same behavioral improvement.
4. **Pilot `type: "agent"` only if step 2 doesn't reach the bar.** The experimental-status warning in the docs is a real cost: docs may change, agent-hook semantics may shift between CC versions, and the agent hook's own model-identity is subject to the same CCR caveat. Treat it as a fallback, not a primary mechanism.
5. **In all cases, capture actual consumed-identity evidence for the agent hook's verifier** — the proposal is correct that requested identity is not consumed identity. Build the evidence-capture into the agent-hook dispatcher from day one; don't retrofit it later.

## Critical review of the "Save 99% reliability with this single wiring" optimism

The proposal implicitly assumes that adding an agent hook at Stop will materially improve outcomes because "the agent has a different role, fresh task framing, and permission to challenge." That assumption has not been measured. The same assumption is what motivated the v2 falsification experiment, and the v2 experiment showed:

- Same-model agent verifiers with **zero additional discriminating tests run** across 10 calibration cases (Condition B produced R=0 because the model named tests in the schema but did not actually call the tools).
- The "different role, fresh framing" framing produced only **schema satisfaction**, not behaviour change.

The proposal's Phase 1 ("shadow") is the right mitigation — measure before promoting. But the proposal should acknowledge that a shadow agent hook that **also produces R=0 with no actual tool calls** is itself a failure mode to detect, not just a tool to deploy. The shadow should log whether the agent hook called `Read`/`Grep`/`Glob`; if not, the agent hook is producing schema — and that should be the first failure we treat, not the second.

## What exists, and what's missing, as a final map

| Capability | Status |
|---|---|
| LLM-based reasoning review at Stop | **EXISTS** (epistemic_validator etc., `warn` mode). |
| External-model challenge hook for review | **PARTIAL** (anti_dodge_judge code exists; active routing not verified in this session). |
| `type: "agent"` Stop hook | **DOCS-SUPPORTED, LOCALLY UNWIRED**. Experimental in CC 2.1.214. Not in `settings.json`. |
| `type: "prompt"` Stop hook | **DOCS-SUPPORTED, LOCALLY UNWIRED**. Not in `settings.json`. |
| Corpus-calibrated measurement infrastructure | **EXISTS** (`P:/.data/evals/`, `tests/`, gold-corpus per `report-contracts.md` §"Feedback Loop Addendum"). Underused. |
| Independent-model consumed-identity evidence | **NOT YET** — that is the same blocker as the v2 experiment. |

## Decision record

The proposal is a **good architectural direction** with a **weak starting step**. The starting step should be:

1. Audit the existing Stop-aggregator output on a small real-investigation corpus (~5 cases) and report detection coverage.
2. If coverage is insufficient, extend the existing detector stack before wiring new hook events.
3. If coverage is sufficient, mode-promote existing detectors to `block` (after corpus TP/FP measurement per `feedback_gate_discrimination_rule.md`).
4. **Reserve `type: "agent"` hooks for high-consequence paths only**, behind an explicit fail-open guard that captures consumed-identity evidence.

The proposal's `Phase 1: Shadow agent hook` is the right *eventual* design but is not the right *first* step given that the existing detector stack has not been measured against this rubric.

## What the proposal author got right that I should not dismiss

- **"Failure to distinguish 'agent has permission to challenge' from 'agent will challenge usefully'."** That is correct; an agent hook with the same model identity will at best produce structured contradiction, not independent evidence. The proposal's "do not claim the agent hook is independent if it routes to the same provider" is the load-bearing honest sentence.
- **"Continue-on-block as a measured pilot, not a permanent block."** That maps to the existing `warn`-mode posture and the `feedback_gate_discrimination_rule` discipline. The proposal honors the repo's own gate promotion rule.
- **"Don't force visible decision-integrity templates into every response."** This directly addresses one of the v2 experiment's negative findings — that the 7-field contract produces schema satisfaction, not falsification work. The proposal explicitly avoids that pitfall by asking *about* the conclusion rather than *requiring* the schema.
