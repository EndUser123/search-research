<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Which plan is better?

LLM_1:
"Here is a draft plan to refine:
Plan: Prevent "First Plausible Explanation" Anti-Pattern
Context
You've identified a persistent anti-pattern: investigations stop when they encounter the first plausible explanation, but this is often wrong. The good news: you already have several hooks that address this! The issue is they may not be configured optimally or used consistently.
Why this matters: First-plausible-explanation bias causes misdiagnosis, wasted effort on wrong fixes, and repeated incidents. The human brain seeks cognitive closure — we stop investigating once we find an explanation that "makes sense."
Current State: You Already Have Tools!
Existing Hooks That Address This Anti-Pattern
HookLocationWhat It DoesStatus
inversion_prompting
cognitive_enhancers.py
"What would make this fail?" - forces considering alternatives
✅ Active
devils_advocate
cognitive_enhancers.py
Stress-test proposals with counterarguments
✅ Active
sequential_thinking
StopHook_sequential_thinking.py
Generate → Critique → Improve loop (3 phases)
✅ Active
debug_rca profile
think_trigger.py
5-Whys root cause analysis template
✅ Active
adversarial_aggregator
adversarial_aggregator.py
Parallel adversarial subagent findings
✅ Active
RCA-Specific Hooks
HookLocationWhat It DoesGap
StopHook_rca_contract.py (lines 943-948)
Requires ≥2 hypothesis rows
Checks presence, not testing
❌ Gap
Stop_verification_gate.py (lines 81-84)
Blocks when only 1 hypothesis
Same gap
❌ Gap
Root Cause Analysis of the Anti-Pattern
The "first plausible explanation" problem has two dimensions:
Dimension 1: Cognitive Bias (Human/LLM tendency)
Problem: Brain seeks cognitive closure, stops at first "good enough" answer
Existing Solution: inversion_prompting + devils_advocate cognitive enhancers
Issue: May not trigger consistently on all investigation types
Dimension 2: Structural Enforcement (Hook validation)
Problem: Can list 5 hypotheses but only test 1, gates allow it
Existing Solution: StopHook_rca_contract.py single-hypothesis-lock check
Issue: Checks table format, not actual testing evidence
Recommended Approach: Three-Layer Enhancement
Layer 1: Optimize Existing Cognitive Enhancers (Low-Hanging Fruit)
Action: Enhance inversion_prompting and devils_advocate to trigger more reliably on investigation tasks.
Files to modify:
P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py
P:\.claude\hooks\cognitive_enhancers_config.json
Change: Add investigation-specific trigger patterns:

# Add to cognitive_enhancers.py

INVESTIGATION_TRIGGERS = [
r"investigat(?:e|ing)",
r"diagnos(?:e|ing|is)",
r"debug(?:ging|ger)?",
r"root cause",
r"why (?:does|is|did)",
r"not working",
r"stopped working",
]

Layer 2: Extend Sequential Thinking for Investigations (Medium Effort)
Action: Create investigation-specific sequential thinking mode that enforces:
Generate multiple hypotheses upfront
Test each systematically
Only declare root cause after ≥2 tested
Files to modify:
P:\.claude\hooks\StopHook_sequential_thinking.py
P:\.claude\hooks\UserPromptSubmit_modules\sequential_thinking.py
Add new mode: investigation (alongside existing critique and improvement)
Layer 3: RCA Contract Enhancement (High Precision)
Action: Add the previously described validators to StopHook_rca_contract.py for RCA-specific cases.
Files to modify:
P:\.claude\hooks\StopHook_rca_contract.py
P:\.claude\hooks\tests\test_StopHook_rca_contract.py
Three new validators:
premature-convergence - Block when <2 hypotheses tested
untested-alternatives - Each hypothesis needs falsification
confirmation-bias - Leading hypothesis needs adversarial test
Implementation Priority
Do in this order:
✅ Layer 1 (10 min) - Add investigation triggers to cognitive enhancers
✅ Layer 2 (30 min) - Add investigation mode to sequential thinking
✅ Layer 3 (60 min) - RCA contract enhancements (if needed after 1\&2)
Implementation Steps
Phase 1: Enhance Cognitive Enhancers (Layer 1)
File: P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py
Add investigation trigger detection to existing inversion_prompting and devils_advocate enhancers
These enhancers already exist — just need better trigger patterns for investigation contexts
Configuration: P:\.claude\hooks\cognitive_enhancers_config.json
{
"topics": {
"diagnostic": {
"enhancers": ["inversion_prompting", "devils_advocate", "calibrated_confidence"],
"max_enhancers": 3
}
}
}

Phase 2: Add Investigation Mode to Sequential Thinking (Layer 2)
File: P:\.claude\hooks\UserPromptSubmit_modules\sequential_thinking.py
Add new investigation mode:
_INVESTIGATION_INSTRUCTIONS = {
"hypotheses": (
"Generate 3+ alternative hypotheses BEFORE testing:\n"
"1. H1: [most likely explanation]\n"
"2. H2: [alternative cause]\n"
"3. H3: [less likely but possible]\n\n"
"For each hypothesis, state:\n"
"- What evidence would CONFIRM it\n"
"- What evidence would FALSIFY it\n"
"- How to test it"
),
"testing": (
"Test each hypothesis systematically:\n"
"- Use verification tools (Read, Grep, Bash)\n"
"- Document actual results (not assumptions)\n"
"- Mark each as CONFIRMED, FALSIFIED, or INCONCLUSIVE"
),
"conclusion": (
"Only declare root cause when:\n"
"- ≥2 hypotheses have been tested\n"
"- Leading hypothesis has supporting evidence\n"
"- Leading alternative has been falsified\n"
"- State remaining uncertainty with [UNVERIFIED] if present"
),
}

File: P:\.claude\hooks\StopHook_sequential_thinking.py
Add iteration logic for investigation mode (3 iterations: hypotheses → testing → conclusion).
Phase 3: RCA Contract Enhancement (Layer 3 - If Needed)
Only implement if Layer 1 and Layer 2 are insufficient.
File: P:\.claude\hooks\StopHook_rca_contract.py
Add _count_tested_hypotheses() helper
Add _validate_premature_convergence() validator
Add _validate_all_alternatives_tested() validator
Add _validate_adversarial_testing() validator
Wire into validation pipeline
Test file: P:\.claude\hooks\tests\test_StopHook_rca_contract.py
test_premature_convergence_blocks_single_test
test_premature_convergence_allows_two_tests
test_untested_alternatives_detects_missing_falsifier
test_confirmation_bias_requires_falsification
test_regression_existing_rca_still_passes
Verification
Layer 1 (Cognitive Enhancers):
Test with investigation query: "investigate why the hook isn't firing"
Verify inversion_prompting and devils_advocate appear in context
Check response includes alternative hypotheses
Layer 2 (Sequential Thinking):
Test with: "debug the intermittent test failure"
Verify investigation mode triggers
Check 3 iterations occur: hypotheses → testing → conclusion
Layer 3 (RCA Contract):
pytest P:\.claude\hooks\tests\test_StopHook_rca_contract.py -v -k "hypothesis"

Integration test: Run a real debugging scenario to verify all layers work together.
Rollback Plan
If Layer 1 or 2 causes issues:
Disable specific enhancers in cognitive_enhancers_config.json
Set SEQUENTIAL_THINKING_ENABLED=false
If Layer 3 causes issues:
Set RCA_MULTI_HYPOTHESIS_ENABLED=false
Adjust RCA_MIN_TESTED_HYPOTHESES from 2 to 1
Configuration
No new config needed for Layer 1 (uses existing cognitive_enhancers_config.json).
For Layer 3, add to P:\.claude\settings.json:
{
"env": {
"RCA_MULTI_HYPOTHESIS_ENABLED": "true",
"RCA_MIN_TESTED_HYPOTHESES": "2",
"RCA_HYPOTHESIS_DEBUG": "false"
}
}

Related Files
Cognitive \& Reasoning:
P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py — 11 enhancers including inversion/devils_advocate
P:\.claude\hooks\UserPromptSubmit_modules\sequential_thinking.py — Generate → Critique → Improve loop
P:\.claude\hooks\StopHook_sequential_thinking.py — Iteration management
P:\.claude\hooks\UserPromptSubmit_modules\think_trigger.py — Auto-detects reasoning profiles
P:\.claude\hooks\cognitive_enhancers_config.json — Configuration
RCA-Specific:
P:\.claude\hooks\StopHook_rca_contract.py — Main RCA contract validator
P:\.claude\hooks\tests\test_StopHook_rca_contract.py — Test suite
P:\.claude\hooks\stop\Stop_verification_gate.py — Related verification gate
Adversarial:
P:\.claude\hooks\adversarial_aggregator.py — Parallel adversarial subagent aggregation"

LLM_2:
" Plan: Multi-Explanation Gate Hook

Context

Problem: We stop investigations at the first plausible explanation, often wrong.

Why this happens: Current hooks enforce Hypothesis → Evidence → Conclusion structure,
but don't require ruling out alternatives. Finding one explanation that fits creates
a false sense of completion.

Synergies with Existing System

The cognitive_enhancers already inject frameworks at UserPromptSubmit time:

- devils_advocate: "stress-test this proposal by finding counterarguments"
- comparative_analysis: "Generate 2-3 diverse approaches first (don't commit to first
idea)"

Gap: These frameworks are enforced at input, but no Stop hook verifies they were
actually applied at output. The model generates a definitive answer without showing
alternatives were considered.

Approach

Add a Stop hook that detects definitive conclusions and verifies alternatives were
addressed.

Detection patterns (definitive conclusion language):

- "the problem is", "the root cause is", "it turns out"
- "so it's actually", "the issue is"
- "definitely", "clearly", "obviously" (confidence markers)

Requirements to unblock (any one):

1. Explicit alternatives considered: "alternatives: X, Y were ruled out because..."
2. Tentative language: "likely", "probably", "one possibility", "appears to be"
3. Multiple tool events showing investigation of different paths
4. Pattern matching showing multiple hypotheses explored

Integration with existing hooks:

- Extend Stop_hypothesis_as_fact_gate.py verification engine (already has claim
extraction and evidence matching)
- Use existing evidence_store for tool event lookup
- Follow same architecture pattern as Stop_hypothesis_enforcement.py

Files to Modify

1. New file: P:/.claude/hooks/Stop_alternatives_required.py

- Detects definitive conclusion patterns
- Checks for evidence of alternative consideration
- Uses verification engine from Stop_hypothesis_as_fact_gate.py

2. Registration: P:/.claude/hooks/Stop_router.py (add to HOOK_SEQUENCE and
ACTIVE_RUNTIME_HOOKS)
3. Settings: P:/.claude/settings.json (add env var
STOP_ALTERNATIVES_REQUIRED_ENABLED=true)

Key Design Decisions

- Default: warn mode - Don't block, warn that alternatives should be considered
- Blocking upgrade via env var for RCA/debug turns
- Tentative language is exempt - "likely", "probably" signals awareness of
alternatives
- Tool evidence exemption - If tool outputs show investigation of multiple paths,
allow

Verification

1. Run existing hook tests: pytest P:/.claude/hooks/tests/ -v
2. Create test cases: "the root cause is X" + no alternatives → WARN
3. Create test cases: "the root cause is X" + "alternatives Y ruled out" → ALLOW"

LLM_1's layered enhancement plan is superior for preventing the "first plausible explanation" anti-pattern in Claude Code hooks.[^1_1][^1_2]

## Core Strengths

LLM_1 leverages 5 existing active hooks (e.g., inversion_prompting, sequential_thinking, adversarial_aggregator) via low-effort optimizations like trigger patterns, minimizing new code risk. It enforces structural changes: ≥2 hypotheses tested with falsification evidence, directly countering confirmation bias where investigators fixate on one path. Sequential thinking extension adds investigation mode (hypotheses → testing → conclusion), aligning with proven debiasing via Type 2 analytical overrides.[^1_3][^1_1][^1_4][^1_5][^1_2]

## LLM_2 Weaknesses

LLM_2 proposes a single new Stop hook detecting definitive language ("the root cause is"), but relies on fuzzy checks like "tentative language" or tool events, which evadeable (e.g., model adds "likely" without testing). Lacks hypothesis generation/testing enforcement; defaults to non-blocking "warn," per user advisory preferences but insufficient for production guardrails. No integration with existing cognitive enhancers or RCA contracts.[^1_2]

## Comparison Table

| Dimension | LLM_1 (Layered) | LLM_2 (New Gate) |
| :-- | :-- | :-- |
| Effort/Risk | Low-med (optimize existing, 10-90min) | Med (new file, registration) |
| Enforcement | Hard: ≥2 tested + falsified | Soft: patterns/language, warn default |
| Coverage | Cognitive + structural + adversarial | Output patterns only |
| Testability | Phased pytest + integration scenarios | Basic pytest cases |
| Bias Counter | Multi-hypothesis + inversion | Alternatives mention (weak)[^1_1] |

## Implementation Priority

Start Layer 1: Add INVESTIGATION_TRIGGERS to cognitive_enhancers.py; test "investigate why hook fails." If insufficient (measure via review_investigation_loops.py), proceed Layer 2. Skip LLM_2 unless pattern detection gaps persist post-Layer 2 (low likelihood).[^1_6]

Confidence: High (90%); assumes existing hooks unchanged per history—verify file timestamps first. Next: Run `pytest P:\.claude\hooks\tests\ -k cognitive` post-Layer 1.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3786658/

[^1_2]: https://incident-prevention.com/blog/7-secrets-of-root-cause-analysis/

[^1_3]: https://en.wikipedia.org/wiki/Confirmation_bias

[^1_4]: https://fastmcp.me/skills/details/3/sequential-thinking

[^1_5]: https://www.verywellmind.com/cognitive-biases-distort-thinking-2794763

[^1_6]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^1_7]: https://research.ibm.com/blog/debugging-AI-bias

[^1_8]: https://www.newline.co/@zaoyang/how-to-debug-bias-in-deployed-language-models--3cffd01b

[^1_9]: https://nickcanzoneri.com/nfs/elasticsearch/cognitive-bias/2017/01/03/the-problem-on-the-other-server.html

[^1_10]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10993686/

[^1_11]: https://www.decodesfuture.com/articles/sequential-thinking-in-claude-code

[^1_12]: https://arxiv.org/abs/2005.13652

[^1_13]: https://www.labxchange.org/library/pathway/lx-pathway:b5eff0ba-7c2d-4df0-b6e9-44b910570ea5/items/lb:LabXchange:16fe9b19:html:1/178814

[^1_14]: https://www.reddit.com/r/programming/comments/1ots577/the_root_cause_fallacy_systems_fail_for_multiple/

[^1_15]: https://lgallardo.com/2025/07/09/beyond-cursor-claude-code-sequential-thinking/


---

# Complete anti-pattern prevention plan — biases, steps, and code hooks

​
How to implement Type 2 analytical processing to counter this anti-pattern

Compare SOBER statistical debugging to manual hypothesis testing

A complete prevention plan needs three layers: cognitive debiasing, enforced investigation phases, and concrete Claude hooks that make Type 2-style analysis the path of least resistance.[^2_1][^2_2][^2_3][^2_4][^2_5]

## 1. Biases Behind “First Plausible Explanation”

Key biases driving this anti-pattern in debugging/RCA:

- **Anchoring**: Latching onto the first hypothesis and adjusting too little even when new evidence appears.[^2_6]
- Confirmation bias: Selectively seeking evidence that supports the current hypothesis, ignoring disconfirming data.[^2_3][^2_7]
- Premature closure / satisficing: Stopping once an explanation “seems to fit,” instead of testing alternatives.[^2_4][^2_8]
- Availability \& representativeness: Overweighting familiar failure modes or recent incidents as “the cause.”[^2_3][^2_6]

In practice, this shows up as: “log looks like X → must be race condition” → single read, one fix attempt, no alternative hypotheses, no negative test. This matches your earlier concerns about overfitting to the first plausible explanation and not re-grounding after codebase changes.

## 2. Type 2 Analytical Processing: What to Implement

Type 2 processing is slow, deliberate, rule-based, and triggered when intuitive Type 1 judgments are likely biased. For your environment, that translates to three concrete design moves:[^2_2][^2_3]

1. **Trigger**: Detect “high‑risk” debug/RCA contexts and force an override of the intuitive guess.
2. **Structure**: Impose explicit phases and rules (hypotheses, tests, evidence, conclusion) with gates.
3. **Verification**: Require evidence and alternative testing before allowing a decisive conclusion.

### 2.1 Triggering Type 2 Mode

Use situational cues to decouple from Type 1 processing. For you:[^2_2][^2_3]

- Detection layer (UserPromptSubmit):
    - Regex triggers for investigation/diagnostic intents (as in the LLM_1 plan):
        - `investigat(e|ing)`, `diagnos(e|is|ing)`, `debug(ging)?`, `root cause`, `why .*`, `not working`, `stopped working`.
- When any trigger fires:
    - Activate “investigation profile” in think_trigger and sequential_thinking.[^2_5]
    - Auto-attach cognitive enhancers: inversion_prompting, devils_advocate, calibrated_confidence, comparative_analysis on those turns.

Effect: the system automatically switches from “answer mode” to “analysis mode” whenever a prompt looks like RCA/debug, implementing the “executive override” debiasing step.[^2_2][^2_3]

### 2.2 Structured Investigation Phases

Map System 2 to explicit phases aligned with your /debugRCA work:[^2_9][^2_10]

1. Phase I – Investigation (facts only)
2. Phase II – Pattern analysis / clustering
3. Phase III – Hypotheses generation (3+ alternatives)
4. Phase IV – Hypothesis testing (targeted tool runs)
5. Phase V – Conclusion \& residual uncertainty

You already use this pattern conceptually in your phase-based debugging discussions; the missing piece is strict enforcement.[^2_10][^2_9]

Implementation pattern:

- Represent phases in a YAML/JSON investigation object carried in context, e.g.:

```yaml
phase: hypotheses
hypotheses:
  - id: H1
    claim: ...
    evidence_for: []
    evidence_against: []
    status: untested
```

- Guardrails:
    - No edits or “root cause is X” language allowed before Phase IV is partially complete.
    - Conclude only after at least 2 hypotheses reached tested status (confirmed/falsified), with explicit evidence.[^2_1][^2_4]


## 3. Concrete Claude Hook Design

Below is a minimal “stack” that implements Type 2 behavior in your hooks ecosystem.

### 3.1 UserPromptSubmit cognitive_enhancers

Goal: inject debiasing prompts when investigation triggers fire.

- In `cognitive_enhancers.py` (already present):
    - Add an INVESTIGATION profile:
        - inversion_prompting: “What would make this explanation fail? List 2 alternative causes.”
        - devils_advocate: “Provide counterarguments and specific disconfirming tests.”
        - comparative_analysis: “Generate 2–3 distinct approaches; do not commit yet.”
- In `cognitive_enhancers_config.json`:
    - New topic “diagnostic” with those enhancers and a max_enhancers cap of 3 (to reduce prompt bloat, as in LLM_1).

This is **pure Type 2 trigger**: it nudges the model into generating multiple hypotheses and explicit tests before it even sees tools.

### 3.2 Sequential Thinking “investigation” Mode

Extend your existing sequential_thinking skill into a 3-step investigation loop, effectively making System 2 the default for debug tasks.[^2_5]

- In `UserPromptSubmit_modules/sequential_thinking.py`:
    - Add `_INVESTIGATION_INSTRUCTIONS` (hypotheses → testing → conclusion) exactly as in the LLM_1 plan, with explicit fields:
        - 3+ hypotheses; for each: evidence that would confirm, evidence that would falsify, tests to run.
        - Testing step must reference concrete tools (Read, Grep, Bash, tests).
        - Conclusion step must:
            - Reference test outcomes.
            - Mark at least one alternative as falsified.
            - Include residual uncertainty flag `[UNVERIFIED]` where appropriate.
- In `StopHook_sequential_thinking.py`:
    - Add logic: when investigation mode is active, enforce 3 iterations and reject early exits (e.g., “jump to conclusion” in iteration 1).

This implements “slow, rule-based, conscious” processing and decouples from the intuitive answer by forcing a plan–test–conclude loop.[^2_3][^2_2]

### 3.3 RCA Contract and Alternatives Gate

You already have an RCA contract and verification gate skeleton. Extend them to enforce “no first plausible explanation” structurally:

- In `StopHook_rca_contract.py`:
    - `_count_tested_hypotheses(table)`: count hypotheses with test rows marked run.
    - `_validate_premature_convergence()`:
        - If RCA_MULTI_HYPOTHESIS_ENABLED = true and tested count < RCA_MIN_TESTED_HYPOTHESES (default 2), block with clear message.
    - `_validate_all_alternatives_tested()`:
        - If at least one alternative remains untested while a root cause is declared, block.
    - `_validate_adversarial_testing()`:
        - Require at least one disconfirming/negative test (e.g., “we tried scenario where H1 would fail, but it did not”) before marking H1 confirmed.
- Optional complementary gate (LLM_2 idea, but tightened):
    - `Stop_alternatives_required.py`:
        - Detect “definitive conclusion language” patterns.
        - Require either:
            - Explicit alternatives list with “ruled out because [evidence],” or
            - Investigative phase artifact showing ≥2 hypotheses tested.
        - In advisory mode for general use; blocking only when RCA profile is active.
- Tests in `test_StopHook_rca_contract.py`:
    - `test_premature_convergence_blocks_single_test` etc., mirroring LLM_1.

This layer transforms the Type 2 “rules” into actual enforcement: the model cannot end in a high-confidence single explanation without competing hypotheses and tests.

### 3.4 Advisory \& Observability

To match your prior investigation loop work:

- Start all new validators in advisory mode (warnings with logging into `failure_recorder_hook`/investigation logs).
- Add a `review_investigation_loops.py`-style analyzer for “premature convergence” events:
    - Count how often a root cause is claimed with only 1 tested hypothesis.
    - Feed these cases back into prompt/skill tuning.

Env switches (settings.json):

```json
"env": {
  "INVESTIGATION_LOOP_ADVISORY": "true",
  "RCA_MULTI_HYPOTHESIS_ENABLED": "true",
  "RCA_MIN_TESTED_HYPOTHESES": "2",
  "RCA_HYPOTHESIS_DEBUG": "false",
  "STOP_ALTERNATIVES_REQUIRED_ENABLED": "true"
}
```


## 4. Step-by-step Implementation Plan

**Phase 0 – Inventory \& Safety**

- Confirm current versions of: cognitive_enhancers, sequential_thinking, StopHook_rca_contract, Stop_verification_gate, evidence_store.
- Ensure investigation logging is active (you already log read-only ops and failures).

**Phase 1 – Cognitive \& Triggers (Low risk)**

1. Add investigation regex triggers in `"diagnostic"` profile.
2. Wire cognitive enhancers to fire on triggers only for debug/RCA-style turns.
3. Smoke test: manual prompts like “investigate why this test is flaky”—check injected frames.

**Phase 2 – Sequential Investigation Mode**

1. Implement investigation mode with 3-phase instructions.
2. Update StopHook_sequential_thinking to enforce 3 iterations for investigation turns.
3. Functional tests:
    - Prompt “debug intermittent test failure”; verify hypotheses → testing → conclusion appears and uses tools.

**Phase 3 – RCA contract validators**

1. Add hypothesis count and validation helpers.
2. Add tests around premature convergence, untested alternatives, and adversarial testing.
3. Run `pytest` with RCA tests; keep validators advisory initially.

**Phase 4 – Alternatives gate**

1. Implement `Stop_alternatives_required` in warn mode for general profile.
2. For `/debugRCA` and similar profiles, allow blocking when:
    - strong conclusion language AND
    - only one hypothesis AND
    - no explicit “alternatives ruled out” evidence.

**Phase 5 – Ratchet Up Strictness**

- After collecting data from advisory logs across several sessions, selectively enable blocking for:
    - `/debugRCA`, high-impact branches, or when tests are flaky/critical.
- Keep relaxed behavior elsewhere to avoid user-friction.


## 5. SOBER vs Manual Hypothesis Testing

SOBER is a statistical debugging technique that uses hypothesis testing over predicates to localize faults from many runs. Your manual hypothesis testing is per-incident reasoning with a human/LLM in the loop.[^2_11][^2_1]

### 5.1 What SOBER Does

- Models each predicate’s evaluation pattern across correct vs incorrect runs.[^2_1][^2_11]
- Null hypothesis: “predicate behavior is the same in passing and failing runs”; computes a test statistic with approximate normal distribution to quantify divergence.[^2_11][^2_1]
- Ranks predicates by “fault relevance”; in Siemens benchmarks, examining ≤10% of code surfaces 68/130 faults, better than earlier methods.[^2_12][^2_11]

This is automated Type 2-style inference: it aggregates many runs and does rigorous hypothesis testing over predicates.

### 5.2 Manual Hypothesis Testing (Your Pattern)

- Human/LLM proposes discrete hypotheses H1, H2, H3 for a particular failure.[^2_9]
- Designs targeted tests (reads, greps, unit/integration tests) to confirm/falsify each.
- Uses qualitative evidence and limited quantitative checks; usually per-incident, not over large corpora.


### 5.3 Comparison Table

| Aspect | SOBER statistical debugging | Manual hypothesis testing (with hooks) |
| :-- | :-- | :-- |
| Level | Program predicates across many runs | Single incident / session |
| Data | Large corpus of pass/fail executions | A handful of ad-hoc tools and tests |
| Inference | Formal hypothesis test; numeric fault relevance score | Qualitative reasoning + some unit test outcomes |
| Output | Ranked predicates / locations | Narrative root cause + targeted fix |
| Strength | Scales, surfaces non-obvious fault locations | Rich context, handles design/requirement issues |
| Weakness | Needs many runs \& instrumentation | Vulnerable to cognitive bias without guardrails |
| Ideal use | Guide where to look | Decide what’s actually broken and why |

### 5.4 How to Combine Them

- Use SOBER-like techniques (or existing statistical fault localization tools) to generate a short list of highly suspicious locations.[^2_13][^2_1][^2_11]
- Feed those into your investigation phase as candidate hypotheses H1–Hk (e.g., “predicate P at line L is faulty”), then run your System 2 investigation loop with hooks to confirm/falsify them.
- Over time, log which SOBER-suggested predicates actually became confirmed causes; this forms a historical prior for future investigations.

***

Assumptions \& uncertainty:

- Assumes your current hooks match earlier descriptions (sequential_thinking, RCA contract, evidence_store); if they drifted, the integration points may need adjustment (medium risk, but straightforward to check).
- SOBER integration in your stack is conceptual here; wiring a full predicate-level profiler into your Windows/Claude workflow would require additional design work (moderate effort).[^2_1][^2_11]

Concrete next step: implement Phase 1 and Phase 2 (investigation triggers + sequential investigation mode), then run your existing `/debugRCA` scenarios and inspect how often the new gates prevent single-hypothesis convergence before enabling stricter RCA validators.
<span style="display:none">[^2_14][^2_15][^2_16][^2_17]</span>

<div align="center">⁂</div>

[^2_1]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^2_2]: https://www.linkedin.com/pulse/cognitive-debiasing-1-origins-bias-theory-ben-hutchinson

[^2_3]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3786658/

[^2_4]: https://incident-prevention.com/blog/7-secrets-of-root-cause-analysis/

[^2_5]: https://www.decodesfuture.com/articles/sequential-thinking-in-claude-code

[^2_6]: https://www.verywellmind.com/cognitive-biases-distort-thinking-2794763

[^2_7]: https://en.wikipedia.org/wiki/Confirmation_bias

[^2_8]: https://www.reddit.com/r/programming/comments/1ots577/the_root_cause_fallacy_systems_fail_for_multiple/

[^2_9]: https://www.perplexity.ai/search/f3f91e0c-d312-4770-9241-a76e6d58865e

[^2_10]: https://www.perplexity.ai/search/7b00466b-d4b2-4c95-a759-3fac97678b2d

[^2_11]: https://www.scribd.com/document/460920309/Tse06-Sober

[^2_12]: https://www.scitepress.org/PublishedPapers/2008/17646/

[^2_13]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Holmes20-20Effecitve20Statistical20Debugging20via20Efficient20Path20Profiling.pdf

[^2_14]: https://ieeexplore.ieee.org/document/1717474/

[^2_15]: https://www.diva-portal.org/smash/get/diva2:829253/FULLTEXT01.pdf

[^2_16]: https://www.sciencedirect.com/science/article/abs/pii/S0164121211000045

[^2_17]: https://www.semanticscholar.org/paper/Statistical-Debugging-of-Programs-written-in-:-RUBY-Akhter-Azhar/27c49d5172b276f801bf97e6c69e395239cf1c68


---

# How to integrate SOBER predicates into Python debugging code

Examples of Type 2 processing checklists for AI bias detection
SOBER vs HOLMES statistical debugging comparison
Code hooks for triggering Type 2 analysis in LLM pipelines

SOBER-style predicates can feed into your Python tooling as an automated “where to look” signal, while Type 2 checklists and LLM hooks govern “how to think” once you’re there.[^3_1][^3_2][^3_3][^3_4][^3_5][^3_6][^3_7]

## 1. Integrating SOBER Predicates into Python Debugging

SOBER instruments predicates, logs their outcomes on passing/failing runs, then uses hypothesis tests to rank which predicates are most fault-relevant. In Python you can approximate this without reimplementing the full paper.[^3_8][^3_2][^3_9][^3_1]

### 1.1 Instrumenting Predicates

Pattern:

- Define “interesting” predicates as small boolean lambdas over state.
- Log per-run evaluations with a run id and outcome (pass/fail).
- Post-process logs to compute a score for each predicate (e.g., SOBER-like “relevance”).

Example scaffolding:

```python
# predicates.py
from typing import Callable, Dict, Any, List, Tuple
import uuid
import time

Predicate = Callable[[Dict[str, Any]], bool]

PREDICATES: Dict[str, Predicate] = {}

def predicate(name: str):
    def decorator(fn: Predicate):
        PREDICATES[name] = fn
        return fn
    return decorator

@predicate("user_is_anonymous_and_has_cart")
def p1(ctx: Dict[str, Any]) -> bool:
    return (ctx.get("user_id") is None) and bool(ctx.get("cart_items"))

@predicate("checkout_flag_set_without_items")
def p2(ctx: Dict[str, Any]) -> bool:
    return ctx.get("checkout_flag") and not ctx.get("cart_items")
```

```python
# run_predicates.py
import json
from pathlib import Path
from typing import Dict, Any
from predicates import PREDICATES

LOG_PATH = Path("output/predicate_log.jsonl")

def log_predicates(ctx: Dict[str, Any], outcome: str, run_id: str):
    records = []
    for name, fn in PREDICATES.items():
        val = bool(fn(ctx))
        records.append({
            "run_id": run_id,
            "predicate": name,
            "value": int(val),
            "outcome": outcome,  # "pass" or "fail"
        })
    LOG_PATH.parent.mkdir(exist_ok=True, parents=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

def execute_with_predicates(fn, *args, **kwargs):
    run_id = str(uuid.uuid4())
    ctx: Dict[str, Any] = {}
    outcome = "fail"
    try:
        result, ctx = fn(*args, **kwargs)  # fn returns (result, ctx)
        outcome = "pass"
        return result
    finally:
        log_predicates(ctx, outcome, run_id)
```

This mirrors SOBER’s per-run predicate logging: for each run you store predicate evaluations and whether the run passed or failed.[^3_2][^3_1]

### 1.2 Ranking Predicates SOBER-Style

SOBER compares true/false evaluation patterns across passing and failing runs and uses a statistic whose distribution is approximated as normal to rank predicates. You can approximate with a simpler but aligned metric like difference in failure rates conditioned on predicate true vs false:[^3_9][^3_1][^3_2]

```python
# analyze_predicates.py
import json
from collections import defaultdict
from pathlib import Path
from math import sqrt

LOG_PATH = Path("output/predicate_log.jsonl")

def load_records():
    with LOG_PATH.open() as f:
        for line in f:
            yield json.loads(line)

def compute_scores():
    counts = defaultdict(lambda: {
        "true_fail": 0, "true_pass": 0,
        "false_fail": 0, "false_pass": 0
    })
    for rec in load_records():
        name = rec["predicate"]
        v = rec["value"]
        fail = rec["outcome"] == "fail"
        if v:
            if fail: counts[name]["true_fail"] += 1
            else:    counts[name]["true_pass"] += 1
        else:
            if fail: counts[name]["false_fail"] += 1
            else:    counts[name]["false_pass"] += 1

    scores = []
    for name, c in counts.items():
        tf, tp = c["true_fail"], c["true_pass"]
        ff, fp = c["false_fail"], c["false_pass"]

        # Add small epsilon to avoid div-by-zero
        eps = 1e-6
        n_true = tf + tp + eps
        n_false = ff + fp + eps

        p_fail_true = tf / n_true
        p_fail_false = ff / n_false

        # Simple z-like score for difference in proportions
        p_pool = (tf + ff) / (n_true + n_false)
        se = sqrt(p_pool * (1 - p_pool) * (1/n_true + 1/n_false)) or eps
        z = (p_fail_true - p_fail_false) / se

        scores.append({
            "predicate": name,
            "z_score": z,
            "p_fail_true": p_fail_true,
            "p_fail_false": p_fail_false,
            "counts": c,
        })

    return sorted(scores, key=lambda r: -abs(r["z_score"]))

if __name__ == "__main__":
    for s in compute_scores():
        print(s)
```

This is not the exact SOBER formula, but the pattern (predicate profiles + hypothesis test over pass/fail distributions) is faithful. Top-ranked predicates become candidate hypotheses for your RCA or LLM investigation loop.[^3_1][^3_2][^3_9]

## 2. Type 2 Processing Checklists for AI Bias

Cognitive debiasing work emphasizes explicit, rule-based checklists to trigger Type 2 processing when bias risk is high. For AI bias detection, a practical checklist is structured across data, model, and decision use:[^3_6][^3_7]

### 2.1 High-level Type 2 Checklist (Bias Audit)

Trigger this when: model affects humans, fairness/regulatory constraints apply, or outputs show group asymmetry.

**Data \& Representation**

- Have protected attributes (or strong proxies) been identified and documented?
- Is there a distribution comparison of key features and labels across groups?
- Are data origins and transformations documented (datasheets, lineage) for auditability?[^3_10]

**Model Behavior**

- Are performance metrics (accuracy, FPR, FNR, calibration) broken down by group?
- Has an independent bias toolkit (e.g., AI Fairness 360, Fairlearn) been run with documented outcomes?[^3_10]
- Are there adversarial or counterfactual tests showing how outputs change when only group attributes are flipped?

**Decision \& Governance**

- Are human overrides documented, and is there a process to investigate overrides for systemic bias?
- Is there a clear explanation policy (what can be explained, to whom, at what fidelity)?
- Are there documented threshold policies and justification for different thresholds across groups, if any?[^3_10]

This checklist forces deliberate checks instead of “looks OK on global accuracy,” which is the Type 1 shortcut.[^3_7][^3_6][^3_10]

## 3. SOBER vs HOLMES Statistical Debugging

SOBER and HOLMES are both statistical debugging techniques but with different units of analysis.[^3_3][^3_4][^3_2][^3_1]

- SOBER: instruments predicates (branches, conditions) and ranks them by how much their true/false patterns differ between passing and failing runs.[^3_2][^3_9][^3_1]
- HOLMES: instruments execution paths; it does path profiling and ranks paths that correlate with failure, with an adaptive variant that progressively zooms into suspicious regions.[^3_4][^3_3]


### Comparison

| Dimension | SOBER | HOLMES |
| :-- | :-- | :-- |
| Unit of analysis | Predicates (boolean conditions) | Path profiles (execution paths) |
| Data | Counts of true/false per run | Which paths executed per run |
| Statistic | Difference in predicate evaluation patterns | Correlation between paths and failure |
| Context captured | Local condition behavior | Broader control-flow context |
| Strength | Simple; interpretable “faulty condition” | Higher precision; scalable, adaptive |
| Limitation | Struggles with rare/nested predicates | Path explosion if not carefully profiled |
| Reported results | Good on single-bug, Siemens benchmarks | Root-caused 24/45 bugs <10% code examined |

HOLMES’s path-based view can reduce ambiguity and increase localization precision, especially in larger systems where many predicates participate. SOBER is simpler to mimic inside your Python debug framework, but HOLMES-like ideas (paths as hypotheses) map nicely onto step-level traces from your tools.[^3_3][^3_4]

## 4. Hooks for Triggering Type 2 Analysis in LLM Pipelines

You can use SOBER-style outputs and risk cues to switch an LLM pipeline into a “System 2” mode, similar to the reasoning-driven pipelines that gate progress on explicit AND/OR steps.[^3_5][^3_11]

### 4.1 Trigger Conditions

Common triggers:

- Task type: prompts containing `debug`, `root cause`, `investigate`, `bias`, `fairness`, etc.
- Context: logs showing multiple failures, flaky tests, or high-impact decisions.
- SOBER/HOLMES signal: top predicate/path score above a threshold or “uncertain” region.


### 4.2 Example Hook Skeletons

**a) UserPromptSubmit hook – mark high-risk turns**

```python
# hooks/UserPromptSubmit_modules/type2_trigger.py
import re

INVESTIGATION_RE = re.compile(r"(debug|root cause|investigat|diagnos|not working|stopped working)", re.I)
BIAS_RE = re.compile(r"\b(bias|fairness|disparate impact|protected class)\b", re.I)

def detect_type2_context(user_prompt: str, extra_meta: dict) -> dict:
    flags = []
    if INVESTIGATION_RE.search(user_prompt):
        flags.append("investigation")
    if BIAS_RE.search(user_prompt):
        flags.append("bias")

    # Optionally: include SOBER top score
    sober_score = extra_meta.get("sober_top_z", 0.0)
    if abs(sober_score) > 2.0:
        flags.append("suspicious_predicate")

    return {
        "type2_required": bool(flags),
        "type2_flags": flags,
    }
```

This hook annotates the session metadata; downstream hooks can require Type 2 behavior when `type2_required` is true.

**b) Reasoning profile / sequential thinking hook**

- When `type2_required` is set, automatically:
    - Switch to sequential_thinking “investigation” mode (hypotheses → tests → conclusion).
    - Attach cognitive enhancers like devils_advocate, inversion_prompting, and calibrated_confidence.
    - In bias-related contexts, swap templates to the bias checklist (Section 2) as explicit steps.

**c) Stop hook – enforce completion of Type 2 steps**

Example logic for a stop hook:

- Check that the assistant output includes:
    - At least N hypotheses or alternatives.
    - Explicit tests or evidence for top hypotheses.
    - For bias tasks: explicit group-wise metrics, checklist answers, and remaining uncertainty.

Pseudo-structure:

```python
# hooks/stop/Stop_type2_enforcement.py
def validate_type2_completion(assistant_output: str, session_meta: dict):
    if not session_meta.get("type2_required"):
        return {"allow": True}

    # Simple structural checks, refined over time
    has_hyp = "Hypotheses" in assistant_output or "H1:" in assistant_output
    has_tests = "Test" in assistant_output or "Evidence" in assistant_output
    has_uncert = "[UNVERIFIED]" in assistant_output or "residual uncertainty" in assistant_output

    if has_hyp and has_tests and has_uncert:
        return {"allow": True}
    else:
        return {
            "allow": False,
            "message": (
                "Type 2 analysis required: please list multiple hypotheses, "
                "document tests/evidence for each, and state remaining uncertainty."
            ),
        }
```

This matches the approach in reasoning-driven pipelines that enforce explicit AND/OR decomposition and validation before advancing, just adapted to your Claude hooks context.[^3_11][^3_5]

***

**Concrete next steps:**

1. Add the SOBER-style predicate logger and analyzer around a flaky Python test suite, and verify you can produce a ranked list of suspicious predicates.[^3_1][^3_2]
2. Wire the resulting “top predicate score” into your Claude session metadata and use it as an additional trigger flag for Type 2 investigation mode.
3. Implement the Type 2 stop hook skeleton and gradually tighten its conditions on `/debugRCA` and bias-related flows, starting in advisory mode.
<span style="display:none">[^3_12][^3_13]</span>

<div align="center">⁂</div>

[^3_1]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^3_2]: https://libraopen.lib.virginia.edu/downloads/cn69m416c

[^3_3]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Holmes20-20Effecitve20Statistical20Debugging20via20Efficient20Path20Profiling.pdf

[^3_4]: https://dl.acm.org/doi/10.1109/ICSE.2009.5070506

[^3_5]: https://www.emergentmind.com/topics/reasoning-driven-llm-based-pipeline

[^3_6]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3786658/

[^3_7]: https://www.linkedin.com/pulse/cognitive-debiasing-1-origins-bias-theory-ben-hutchinson

[^3_8]: https://dl.acm.org/doi/10.1145/1273463.1273467

[^3_9]: https://www.scirp.org/journal/paperinformation?paperid=69863

[^3_10]: https://www.artech-digital.com/blog/checklist-for-reducing-ai-bias

[^3_11]: https://www.perplexity.ai/search/4fdfe841-f3f2-4567-a14a-f41b35391f16

[^3_12]: https://pages.cs.wisc.edu/~liblit/issta-2007/issta-2007.pdf

[^3_13]: http://ieeexplore.ieee.org/document/5070506/


---

# Python code example instrumenting predicates with SOBER

SOBER limitations with nested or rarely observed predicates
Adaptive HOLMES vs non-adaptive for debugging efficiency
Tarau 2023 reasoning pipeline for debugging AI models

Python predicate instrumentation can approximate SOBER’s core idea (predicate profiles + hypothesis testing), but SOBER struggles with rare/nested predicates; HOLMES’ adaptive path profiling improves efficiency by focusing instrumentation where failures occur, and recent reasoning pipelines use structured routing + verification to debug AI models.[^4_1][^4_2][^4_3][^4_4][^4_5][^4_6][^4_7]

## Python SOBER-style predicate instrumentation

Below is a self-contained example that:

- Defines predicates over a runtime context.
- Logs their evaluations for passing/failing runs.
- Computes a SOBER-like score to rank suspicious predicates via difference in failure rates and an approximate z-statistic, mirroring the hypothesis-testing spirit.[^4_4][^4_5][^4_6]

```python
# predicates.py
from __future__ import annotations
from typing import Callable, Dict, Any

Predicate = Callable[[Dict[str, Any]], bool]
PREDICATES: Dict[str, Predicate] = {}

def predicate(name: str):
    def decorator(fn: Predicate):
        PREDICATES[name] = fn
        return fn
    return decorator

@predicate("p_user_anonymous_with_cart")
def p_user_anonymous_with_cart(ctx: Dict[str, Any]) -> bool:
    return ctx.get("user_id") is None and bool(ctx.get("cart_items"))

@predicate("p_checkout_without_items")
def p_checkout_without_items(ctx: Dict[str, Any]) -> bool:
    return ctx.get("checkout_flag") and not ctx.get("cart_items")

@predicate("p_high_total_low_items")
def p_high_total_low_items(ctx: Dict[str, Any]) -> bool:
    return ctx.get("order_total", 0.0) > 100 and len(ctx.get("cart_items", [])) <= 1
```

```python
# runner.py
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, Callable
from predicates import PREDICATES

LOG_PATH = Path("output/predicate_log.jsonl")

def log_predicates(ctx: Dict[str, Any], outcome: str, run_id: str):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        for name, fn in PREDICATES.items():
            val = bool(fn(ctx))
            rec = {
                "run_id": run_id,
                "predicate": name,
                "value": int(val),
                "outcome": outcome,  # "pass" or "fail"
            }
            f.write(json.dumps(rec) + "\n")

def execute_with_predicates(
    fn: Callable[..., Tuple[Any, Dict[str, Any]]],
    *args,
    **kwargs
):
    run_id = str(uuid.uuid4())
    ctx: Dict[str, Any] = {}
    outcome = "fail"
    try:
        result, ctx = fn(*args, **kwargs)  # fn returns (result, ctx)
        outcome = "pass"
        return result
    finally:
        log_predicates(ctx, outcome, run_id)
```

```python
# analyze.py
import json
from collections import defaultdict
from math import sqrt
from pathlib import Path

LOG_PATH = Path("output/predicate_log.jsonl")

def load_records():
    with LOG_PATH.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def compute_sober_like_scores():
    counts = defaultdict(lambda: {
        "true_fail": 0, "true_pass": 0,
        "false_fail": 0, "false_pass": 0,
    })
    for rec in load_records():
        name = rec["predicate"]
        v = rec["value"]
        fail = (rec["outcome"] == "fail")
        if v:
            if fail: counts[name]["true_fail"] += 1
            else:    counts[name]["true_pass"] += 1
        else:
            if fail: counts[name]["false_fail"] += 1
            else:    counts[name]["false_pass"] += 1

    scores = []
    for name, c in counts.items():
        tf, tp = c["true_fail"], c["true_pass"]
        ff, fp = c["false_fail"], c["false_pass"]
        eps = 1e-6

        n_true = tf + tp + eps
        n_false = ff + fp + eps

        p_fail_true = tf / n_true
        p_fail_false = ff / n_false

        # pooled proportion for a simple difference-in-proportions z
        p_pool = (tf + ff) / (n_true + n_false)
        se = sqrt(max(p_pool * (1 - p_pool) * (1 / n_true + 1 / n_false), eps))
        z = (p_fail_true - p_fail_false) / se

        scores.append({
            "predicate": name,
            "z_score": z,
            "p_fail_true": p_fail_true,
            "p_fail_false": p_fail_false,
            "counts": c,
        })

    return sorted(scores, key=lambda s: -abs(s["z_score"]))

if __name__ == "__main__":
    for s in compute_sober_like_scores():
        print(s)
```

Top-ranked predicates become candidate “where to look” hypotheses you can feed into your RCA / LLM investigation loop.

## SOBER limitations: nested \& rare predicates

Empirical and follow-on work notes several limitations for predicate-based statistical debugging in realistic programs:[^4_5][^4_6][^4_4]

- **Rare predicates**: predicates that are almost always false (or true) have too little data to support reliable hypothesis tests; their estimated failure rates have high variance and unstable scores.[^4_6][^4_5]
- Nested/complex predicates: faults that manifest only under specific combinations or nested conditions may not be captured by a single predicate; compound predicate variants improve this but increase dimensionality and instrumentation cost.[^4_8][^4_9][^4_5]
- Multiple-fault and interacting-fault scenarios: SOBER’s model is strongest for single-bug settings; when multiple faults interact, predicate-failure correlations can become noisy or misleading.[^4_6]
- Control-flow context loss: predicates are local; they do not encode which path through the program produced the problematic combination, making localization coarser than path-based methods.[^4_7][^4_1]

In practice, this means SOBER is excellent for “clean” benchmarks and many single-bug cases, but less effective when the failure depends on rare, path-specific interactions or multiple concurrent issues.[^4_4][^4_5][^4_6]

## Adaptive HOLMES vs non-adaptive

HOLMES generalizes statistical debugging from predicates to path profiles and offers both non-adaptive and adaptive variants.[^4_1][^4_7]

- **Non-adaptive HOLMES**:
    - Instruments the program with path profiling from the start (e.g., Ball–Larus-style).
    - Runs many passing and failing executions, then applies Liblit-style statistical debugging on paths instead of predicates.[^4_7][^4_1]
    - Uses an importance measure combining sensitivity (how often path appears in failing runs) and specificity (how rarely it appears in passing runs), ranking paths as predictors of failure.[^4_1]
- **Adaptive HOLMES**:
    - Observes that only small program regions are relevant for a given bug; full instrumentation is costly.[^4_7][^4_1]
    - Starts with light/no instrumentation; when failures appear, iteratively and selectively instruments “suspicious” parts of the program (e.g., functions or regions linked to bug reports).[^4_10][^4_1]
    - Refines predictors by moving from coarse to more detailed profiles, strengthening weak predictors by focusing richer profiling on their functions.[^4_1]

Efficiency implications:

- Non-adaptive: simpler, but incurs higher overhead due to global path profiling; suitable when test budgets are smaller and overhead acceptable.[^4_7][^4_1]
- Adaptive: better scalability and debugging efficiency in large, real systems—less time and space overhead while still enabling programmers to root-cause a high fraction of bugs by examining <10% of the code.[^4_1][^4_7]

For your use, the HOLMES idea maps well onto selectively instrumenting “hot” modules and paths (e.g., failing services or tests) instead of globally instrumenting your entire Python stack.

## Tarau-style reasoning pipeline for debugging AI models

Recent practice around reasoning pipelines for LLMs mirrors what you want for debugging: structured routing, constrained reasoning paths, and verification/auto-correction.[^4_2][^4_3]

A typical pipeline (e.g., Tarau 2023–style / community reasoning pipelines) has these stages:[^4_3][^4_2]

1. **Intent classification / routing**
    - Classifier (small model or rules) detects whether the request is explanation, coding/debugging, planning, or bias/safety.
    - Debugging or reasoning-heavy intents are routed into a “System 2” path with stricter structure.
2. **Structured reasoning paths**
    - For problem-solving/debugging, the pipeline enforces:
        - Hypothesis generation (multiple alternatives).
        - Plan of evidence-gathering steps (e.g., logs, tests, ablations).
        - Tool-assisted investigation (code search, test runs, traces).[^4_3]
    - Reasoning is serialized into explicit steps (similar to ToT / tree-of-thoughts or plan-and-solve) instead of a single monolithic answer.[^4_3]
3. **Verification and automatic correction**
    - Generated answers are checked using:
        - External signals (e.g., tests, external search, SOBER/HOLMES-style metrics).
        - Internal consistency checks and self-critique.
    - When checks fail, the pipeline automatically triggers a refinement pass, often with a reason-aware prompt.[^4_2][^4_3]

This matches the Reddit description: intent understanding → structured execution paths per mode → verification and automatic correction for small models. For debugging AI models, you can overlay this on your current Claude hooks by:[^4_2]

- Routing `/debugRCA` or “why is the model wrong?” prompts into a dedicated debug pipeline.
- Requiring explicit hypotheses and test plans (e.g., targeted evals, ablations, data slices) before allowing a root-cause claim.
- Running those tests via tools and feeding results into a verification hook that either accepts or demands another pass.

If you want, the next step can be a concrete Claude-hook-friendly reasoning pipeline sketch that pulls SOBER-style signals into the routing/verification stages.
<span style="display:none">[^4_11][^4_12][^4_13][^4_14][^4_15][^4_16]</span>

<div align="center">⁂</div>

[^4_1]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Holmes20-20Effecitve20Statistical20Debugging20via20Efficient20Path20Profiling.pdf

[^4_2]: https://www.reddit.com/r/MachineLearning/comments/1p69kww/d_i_built_a_reasoning_pipeline_that_boosts_8b/

[^4_3]: https://milvus.io/ai-quick-reference/how-do-i-debug-reasoning-errors-in-ai-models

[^4_4]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^4_5]: https://libraopen.lib.virginia.edu/downloads/cn69m416c

[^4_6]: https://www.scirp.org/journal/paperinformation?paperid=69863

[^4_7]: https://dl.acm.org/doi/10.1109/ICSE.2009.5070506

[^4_8]: https://dl.acm.org/doi/10.1145/1273463.1273467

[^4_9]: https://pages.cs.wisc.edu/~liblit/issta-2007/issta-2007.pdf

[^4_10]: https://afariha.github.io/projects/synthesis_project.pdf

[^4_11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3034737/

[^4_12]: http://www.goodmath.org/blog/2011/02/11/another-crank-comes-to-visit-the-cognitive-theoretic-model-of-the-universe/

[^4_13]: https://epub.uni-regensburg.de/10310/1/DissertationHolgerSaurenbach.pdf

[^4_14]: https://ohadnachtomy.com/wp-content/uploads/2015/05/units_of_selection-11.pdf

[^4_15]: https://csd.cmu.edu/sites/default/files/phd-thesis/CMU-CS-22-109.pdf

[^4_16]: https://plato.stanford.edu/archives/spr2012/entries/natural-kinds/


---

# How to implement HOLMES path profiling in Python

Tarau 2023 full paper on reasoning pipeline
Benchmarks comparing adaptive vs non-adaptive HOLMES
Real-world examples of SOBER in AI debugging
Integration of HOLMES with SOBER predicates

HOLMES-style path profiling in Python can be approximated by logging compact path IDs per run and then doing SOBER-like statistics over paths; Tarau-style reasoning pipelines add a structured, multi-step control layer that can consume both SOBER predicates and HOLMES paths.[^5_1][^5_2][^5_3][^5_4][^5_5][^5_6]

## HOLMES-style path profiling in Python

HOLMES uses efficient path profiling (e.g., Ball–Larus) to collect path IDs on each execution, then applies statistical debugging to find paths that correlate with failure. In Python you can emulate the idea (without low-level CFG instrumentation) using lightweight path IDs.[^5_2][^5_7][^5_1]

### Minimal path-ID instrumentation

Pattern:

- Maintain a `path_id` integer in thread-local/request-local context.
- At key “edges” (e.g., function entries, important branches), update `path_id = path_id * P + K` (P a small prime, K a site constant).
- On run completion, log `path_id` plus outcome (pass/fail).
- Later, compute statistics over path IDs similar to predicate-based SOBER.[^5_3][^5_4][^5_1]

Example:

```python
# path_profiler.py
from __future__ import annotations
from contextvars import ContextVar
from pathlib import Path
import json
import uuid
from typing import Callable, Any, Dict

PATH_ID: ContextVar[int] = ContextVar("PATH_ID", default=1)
LOG_PATH = Path("output/path_profiles.jsonl")
P = 131  # small prime

def reset_path_id():
    PATH_ID.set(1)

def record_edge(edge_id: int):
    curr = PATH_ID.get()
    PATH_ID.set(curr * P + edge_id)

def log_path(outcome: str, extra: Dict[str, Any] | None = None):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": str(uuid.uuid4()),
        "path_id": PATH_ID.get(),
        "outcome": outcome,
        "extra": extra or {},
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def profiled(fn: Callable[..., Any]):
    def wrapper(*args, **kwargs):
        reset_path_id()
        outcome = "fail"
        try:
            result = fn(*args, **kwargs)
            outcome = "pass"
            return result
        finally:
            log_path(outcome, extra={"fn": fn.__name__})
    return wrapper
```

Use it:

```python
# app.py
from path_profiler import profiled, record_edge

@profiled
def process_order(order):
    if order.total > 100:
        record_edge(1)
        # ...
    else:
        record_edge(2)
        # ...
    if order.expedited:
        record_edge(3)
    else:
        record_edge(4)
    # ...

    # normal return
    return True
```

Analysis (SOBER-like over paths):

```python
# analyze_paths.py
import json
from collections import defaultdict
from math import sqrt
from pathlib import Path

LOG_PATH = Path("output/path_profiles.jsonl")

def load_records():
    with LOG_PATH.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def compute_path_scores():
    counts = defaultdict(lambda: {"fail": 0, "pass": 0})
    for rec in load_records():
        pid = rec["path_id"]
        outcome = rec["outcome"]
        counts[pid][outcome] += 1

    scores = []
    for pid, c in counts.items():
        tf = c["fail"]; tp = c["pass"]
        eps = 1e-6
        n = tf + tp + eps
        p_fail = tf / n
        # Assume global failure rate is known or estimate from all runs
        # Here, compute simple z comparing path failure rate vs global
        scores.append({
            "path_id": pid,
            "fail": tf,
            "pass": tp,
            "p_fail": p_fail,
        })

    # You’d refine this with a proper z/statistic; this is scaffold.
    return sorted(scores, key=lambda s: -s["p_fail"])

if __name__ == "__main__":
    for s in compute_path_scores():
        print(s)
```

This mirrors HOLMES’ “collect path profiles, then rank paths that correlate with failure,” though it is far less precise than full CFG-based profiling.[^5_7][^5_1][^5_2]

## Tarau-style reasoning pipeline (2023+)

Recent work by Tarau and others on reasoning pipelines for AI emphasizes:

- Chaining LLM calls as a logic program or structured reasoning graph.
- Recursion on LLM queries, casting intermediate steps into a formal representation and iterating with verification.[^5_8][^5_5][^5_6]

A Tarau-style pipeline for debugging AI models typically has:

- A **router** that classifies the task (bug localization, explanation, etc.).[^5_6]
- A **logic-like plan** where each node is a subgoal (e.g., “collect failing examples,” “generate hypotheses,” “run focused tests”), often represented in a declarative structure.[^5_8][^5_6]
- Iterative refinement: outputs of one step are fed back as structured input to the next, with checks (consistency, tests, constraints) gating progress.[^5_5][^5_6][^5_8]

For your purposes, the key takeaway is: reason as a multi-step program with explicit subgoals + verification, not as a single free-form completion—exactly what your hooks and investigation phases are pushing toward.

## Benchmarks: adaptive vs non-adaptive HOLMES

HOLMES was evaluated on the SIR benchmark suite and large real-world apps; path profiles improved precision, and adaptive profiling reduced overhead:[^5_9][^5_10][^5_1][^5_2]

- Effectiveness: with path-based predictors, developers could root-cause 24 of 45 bugs examining <10% of code, versus 14/45 with predicate-based predictors.[^5_1]
- Overheads: adaptive HOLMES maintains low execution-time and space overhead by only profiling previously identified “hot” regions, making it more scalable than non-adaptive full-path profiling.[^5_10][^5_9][^5_1]
- Conceptually, non-adaptive = one round of full instrumentation; adaptive = iterative cycles of profiling → statistical analysis → static analysis → re-instrument only suspicious regions.[^5_1]

This makes adaptive HOLMES the better fit for real systems (and large Python services), where full-path profiling everywhere would be prohibitive.

## SOBER in AI / ML debugging

Published SOBER case studies focus on traditional software (e.g., grep 2.2, bc 1.06) and Siemens benchmarks, where SOBER even found a previously unreported fault in bc 1.06. Direct “SOBER on ML models” papers are sparse; instead, similar statistical techniques are used for:[^5_3]

- **Log-based** RCA in large-scale systems (e.g., LogSage uses clustering and GNNs over logs with LLM summarization).[^5_11]
- Statistical debugging for real-world systems combining coverage/log features with failure labels.[^5_10]

So, SOBER’s pattern—feature (predicate) profiles + hypothesis testing—is conceptually used in AI debugging, but often in the form of learned models over logs/traces rather than literal SOBER implementation.

## Integrating HOLMES paths with SOBER predicates

HOLMES and SOBER are complementary: predicates give local condition views; paths provide richer execution context.[^5_4][^5_2][^5_3][^5_1]

A practical integration pattern for your stack:

- Collect both predicate logs (SOBER-style) and path profiles (HOLMES-style) for each run.
- Run SOBER-like scoring over predicates and HOLMES-like scoring over paths.
- Combine signals:
    - Use path scores to identify suspicious regions (functions/paths).
    - Within those regions, rank predicates with SOBER; treat “predicate within highly suspicious path” as higher-priority candidates.
- Feed combined candidates into your LLM investigation pipeline:
    - Map each top path and predicate into explicit hypotheses (e.g., “Path P plus predicate Q is faulty”).
    - Have the LLM’s Type 2 mode select tests (reads, unit tests, ablations) targeting those specific sites.

This gives you:

- HOLMES for **where** (which paths/regions).
- SOBER for **what condition** within those paths.
- LLM + hooks for **why** and **how to fix**, under Type 2 constraints.
<span style="display:none">[^5_12]</span>

<div align="center">⁂</div>

[^5_1]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Holmes20-20Effecitve20Statistical20Debugging20via20Efficient20Path20Profiling.pdf

[^5_2]: https://dl.acm.org/doi/10.1109/ICSE.2009.5070506

[^5_3]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^5_4]: https://libraopen.lib.virginia.edu/downloads/cn69m416c

[^5_5]: https://www.reddit.com/r/MachineLearning/comments/1p69kww/d_i_built_a_reasoning_pipeline_that_boosts_8b/

[^5_6]: https://milvus.io/ai-quick-reference/how-do-i-debug-reasoning-errors-in-ai-models

[^5_7]: https://software-lab.org/teaching/winter2020/pa/slides_path_generalization.pdf

[^5_8]: https://ceur-ws.org/Vol-3799/paper11PEG2.0.pdf

[^5_9]: https://www.microsoft.com/en-us/research/publication/holmes-effective-statistical-debugging-via-efficient-path-profiling-2/

[^5_10]: https://misailo.cs.illinois.edu/papers/axprof-icse19.pdf

[^5_11]: https://nkcs.iops.ai/wp-content/uploads/2025/10/LogSage.pdf

[^5_12]: https://www.microsoft.com/en-us/research/video/automated-debugging-using-holmes/


---

# Python library for efficient path profiling like HOLMES

How does adaptive HOLMES reduce profiling overheads
SOBER vs HOLMES comparison for fault localization
Real-world bugs fixed using HOLMES path profiling
Integrate HOLMES profiling with SOBER predicates in Python

For Python, there is no mainstream library that directly implements HOLMES end-to-end; the closest practical building blocks are `coverage.py` branch/arc measurement, the stdlib `trace`/`profiling.tracing` modules, and compiler-level CFG/branch tools like `gcovr` for native extensions. HOLMES itself reduces overhead by turning on instrumentation only after failures appear and then profiling only suspicious functions, branches, and paths, so bug-free runs incur no profiling cost and failing systems avoid global full-path profiling.[^6_1][^6_2][^6_3][^6_4][^6_5][^6_6]

## Python library options

There is no canonical “HOLMES for Python” package in the standard ecosystem, so the realistic approach is to assemble one from lower-level tracing primitives. The best fit today is `coverage.py` with branch measurement because it already captures source→destination branch transitions, which are close to the edge data needed for lightweight path reconstruction.[^6_2][^6_7][^6_3][^6_1]

Practical options:

- `coverage.py --branch`: best starting point for Python-only code; records branch transitions with relatively low overhead and good tooling.[^6_7][^6_2]
- `sys.monitoring`/new profiling APIs: promising for lower-overhead event capture in newer Python versions, though still more primitive than a ready-made HOLMES implementation.[^6_1][^6_7]
- `trace` module: useful for prototyping statement/line tracing, but generally too noisy/heavy for production-grade adaptive profiling.[^6_3]
- `gcovr`/compiler arcs: relevant only if part of the stack is native C/C++; it works at CFG arc level, not Python bytecode level.[^6_5]


## Adaptive overhead reduction

Adaptive HOLMES works by profiling in stages rather than everywhere from the start. The paper describes a loop where the program initially runs without instrumentation, collects bug reports and stack traces, computes suspicious code regions from those failures plus static analysis, then redeploys with profiling only inside selected functions/branches/paths.[^6_4][^6_6]

That reduces both time and space overhead in three ways:

- No cost on bug-free programs or pre-failure runs.[^6_4]
- Smaller profile volume because only suspicious regions emit path data, not the full program.[^6_6][^6_4]
- Fewer runs needed once full local profiles are collected in the narrowed region, improving debugging efficiency versus sparse random sampling.[^6_6][^6_4]


## SOBER vs HOLMES

SOBER localizes faults using predicate profiles, while HOLMES uses richer path profiles that preserve more execution context. In HOLMES’ evaluation, path profiles improved bug isolation precision and explanation quality relative to predicate-based approaches.[^6_8][^6_4][^6_6]


| Aspect | SOBER | HOLMES |
| :-- | :-- | :-- |
| Signal unit | Boolean predicates.[^6_8] | Execution paths.[^6_6] |
| Context richness | Local condition only.[^6_8] | Control-flow context across a path.[^6_6] |
| Interpretability | Often easier to explain as a condition.[^6_8] | Better localization, but path IDs need decoding.[^6_4] |
| Overhead | Lower/simpler instrumentation.[^6_8][^6_9] | Higher if non-adaptive; lower if adaptive.[^6_4][^6_6] |
| Best use | Quick suspicious-condition ranking.[^6_8] | Precise root-cause narrowing in larger systems.[^6_4][^6_6] |

A good working rule is: use SOBER when you want simple, explainable condition-level suspicion; use HOLMES when ambiguity from local predicates is too high and path context matters.[^6_8][^6_4]

## Real-world bug evidence

HOLMES was evaluated not just on SIR benchmarks but also on “large, real-world applications,” and the authors report that developers could root-cause 24 of 45 bugs by examining less than 10% of the code, compared with 14 of 45 for predicate-based predictors in the same study context. The paper summary available here does not enumerate each bug in the search snippet, so the quantitative result is solid but the individual named bug examples are not visible from the retrieved sources.[^6_4][^6_6]

For SOBER, the primary paper reports results on Siemens benchmarks and on real utilities such as `grep 2.2` and `bc 1.06`, including discovery of a previously unreported fault in `bc 1.06`. That is the clearest “real-world bug fixed/found” evidence from the sources retrieved here.[^6_8]

## Python integration pattern

The most practical Python design is hybrid: reconstruct lightweight path signatures from branch transitions, then combine them with SOBER-style predicate scores. That gives HOLMES-like path context without requiring a full compiler-style path profiler.[^6_2][^6_7][^6_8]

Recommended architecture:

1. Use `coverage.py` branch events or `sys.monitoring` to collect branch/edge transitions per run.[^6_7][^6_1][^6_2]
2. Derive a compact path signature per function/request, for example a rolling hash over edge IDs.
3. Log pass/fail outcome for each run.
4. In parallel, evaluate explicit predicates on runtime state and log those too, SOBER-style.[^6_8]
5. Rank:
    - paths by failure correlation,
    - predicates by failure correlation,
    - then prioritize predicates that occur inside highly suspicious paths.[^6_4][^6_8]

Conceptually:

```python
run_result = {
    "outcome": "fail",
    "path_signatures": {"checkout.process": 18273645},
    "predicates": {
        "cart_empty_and_checkout_flag": True,
        "discount_negative": False,
    },
}
```

Then score with two analyzers:

- Path analyzer: HOLMES-like, ranks suspicious path signatures.[^6_6][^6_4]
- Predicate analyzer: SOBER-like, ranks suspicious conditions.[^6_8]

Final candidate ranking can be something like:

$$
score = 0.6 \cdot z_{\text{path}} + 0.4 \cdot z_{\text{predicate}}
$$

That weighting is a design choice, not from the papers, so treat it as a heuristic rather than a published formula. The key idea is to use path scores for **where** and predicate scores for **what condition**.[^6_4][^6_8]

## Recommendation

For Python today, start with `coverage.py --branch` plus custom runtime predicates; that is the highest-leverage approximation of HOLMES+SOBER without building a bytecode or AST-level profiler from scratch. If overhead becomes an issue, add adaptive gating: collect stack traces on failures first, then enable branch/path capture only inside the implicated modules, which mirrors HOLMES’ core overhead reduction strategy.[^6_2][^6_7][^6_6][^6_4][^6_8]

Uncertainty: there may be niche research or GitHub implementations of HOLMES-like Python profilers, but none appeared in the retrieved authoritative sources, so I would not assume a maintained drop-in library exists. A concrete next step is to prototype branch-based path signatures on one flaky subsystem and compare whether suspicious-path ranking beats predicate-only ranking on your existing failing tests.[^6_3][^6_1][^6_2][^6_4]
<span style="display:none">[^6_10][^6_11][^6_12]</span>

<div align="center">⁂</div>

[^6_1]: https://docs.python.org/3.15/library/profiling.tracing.html

[^6_2]: https://coverage.readthedocs.io/en/7.11.3/branch.html

[^6_3]: https://www.cs.unb.ca/~bremner/teaching/cs2613/books/python3-doc/library/trace.html

[^6_4]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Holmes20-20Effecitve20Statistical20Debugging20via20Efficient20Path20Profiling.pdf

[^6_5]: https://gcovr.com/en/7.2/faq.html

[^6_6]: https://dl.acm.org/doi/10.1109/ICSE.2009.5070506

[^6_7]: https://nedbatchelder.com/blog/202408/coverage_branches_instead_of_arcs

[^6_8]: https://sites.cs.ucsb.edu/~xyan/papers/tse06_sober.pdf

[^6_9]: https://libraopen.lib.virginia.edu/downloads/cn69m416c

[^6_10]: https://developers.arcgis.com/python/latest/guide/itemgraph-and-remap-data/

[^6_11]: https://www.eficode.com/blog/fix-mystery-bugs-through-problem-solving-like-sherlock-holmes

[^6_12]: https://ceur-ws.org/Vol-2951/paper8.pdf

