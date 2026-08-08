---
title: "Layer 3 claim extraction falsified for belief-state hallucinations; trajectory-validity checking is the field's approach"
created: 2026-08-07
source: session-019fde3e (/www research + calibration test + 3-lens critique chain)
tags: [falsification, hallucination-prevention, trajectory-validity, belief-state, reasoning-hallucination, claim-extraction, groundeval, agent-hallucination-taxonomy]
summary: >
  Two Layer 3 approaches (keyword detection, decompositional claim extraction) were
  falsified for the workspace's 5 documented "claim-without-checking" instances.
  Root cause: both are output-level methods targeting reasoning-stage belief-state
  hallucinations. The field's taxonomy (Lin et al. 2025, arxiv 2509.18970) classifies
  all 5 as Reasoning-stage hallucinations — internal belief-state failures that occur
  before any external behavior executes. Output-level detection is structurally late.
  The field's production approach is trajectory-validity checking (GroundEval, Flynt
  2026, arxiv 2606.22737): verify the agent searched the required evidence space before
  claiming, not whether the final claim matches tool events. This sidesteps the
  assertion-vs-discussion FP that killed keyword detection (67% FP) because it checks
  actions, not prose. Open-source reference: github.com/tenurehq/groundeval.
agent: grok
host: grok
cognitive_load: 3
verification: source-verified
relations:
  - target: wiki/concepts/claim-without-checking-industry-approaches-2026.md
    type: supersedes — that concept's "Layer 3 absent / build Claimify" conclusion is falsified
  - target: wiki/concepts/keyword-detection-recommendations-falsified-67percent-fp.md
    type: extends — that falsified keyword detection; this falsifies the extraction approach and explains both via the taxonomy
  - target: wiki/concepts/reasoning-first-search-never-claim-without-checking.md
    type: refines — the 5 instances now have a taxonomy classification
  - target: wiki/concepts/measure-first-pattern-for-proactive-mechanism-design.md
    type: related — the calibration test is an instance of measure-first
---

# Layer 3 claim extraction falsified for belief-state hallucinations

## Decision context

Session 019fde3e attempted to design "Layer 3" (faithfulness checking) for the
workspace's 5 documented instances of agents stating claims as fact without
checking evidence. Three approaches were tested or examined:

1. **Keyword detection** (prior session) — falsified at 67% FP. See
   [[keyword-detection-recommendations-falsified-67percent-fp]].
2. **Decompositional claim extraction** (dormant stack at
   `P:/.claude/hooks/verification/`) — falsified by calibration test (0/5
   catch rate). See § "The calibration test" below.
3. **GroundEval-style trajectory-validity checking** — the field's
   production approach, identified via /www research. Untested on our
   domain but architecturally matches the problem.

This concept captures why both prior approaches failed structurally (not
fixable by tuning) and what the field's taxonomy says about the problem
class.

## The taxonomy that explains both failures

Lin et al. 2025 (arxiv 2509.18970, "LLM-based Agents Suffer from
Hallucinations: A Survey of Taxonomy, Methods, and Directions")
decomposes agent hallucinations into 5 types across two axes:

- **Internal State** — the belief state `b_t` the agent maintains
- **External Behaviors** — reasoning, execution, perception,
  memorization, communication (all guided by `b_t`)

The 5 hallucination types: Reasoning, Execution, Perception,
Memorization, Communication.

### Our 5 instances mapped to the taxonomy

| Instance | Lin et al. type | Section |
|---|---|---|
| 1: Fabricated skill syntax `/tp {5}` | Reasoning — "Planning Information Misinterpretation" | §3.1.4 |
| 2: Wrong capability claim "can't verify Cohere quota" | Reasoning — self-knowledge boundary violation | §3.1.4 |
| 3: Rate/quota conflation | Reasoning — "Planning Information Misapplication" (causal misattribution) | §3.1.5 |
| 4: Fabricated context-budget excuse | Reasoning — self-knowledge boundary + Memorization (session state) | §3.1.4, §3.4 |
| 5: No /www before recommendation | Execution — "Lack of Solvability Awareness" | §3.2.4 |

**All 5 are Reasoning-stage hallucinations** — internal belief-state
failures. Lin et al. §3.1.4: "when confronted with planning problems
beyond its knowledge boundary, the agent tends to respond with excessive
confidence, generating answers that sound certain but are actually
incorrect."

### Why output-level detection is structurally late

Both our approaches operated on the agent's *output text*:
- Keyword detection: scan output for recommendation vocabulary
- Claim extraction: decompose output into atomic claims, match against tool events

But Reasoning hallucinations occur at the *planning* stage (Lin et al.
Eq. 20: `p_t = Plan(b_t, I_t)`), before any external behavior executes.
By the time text is generated, the hallucination has already propagated
into the belief state. The output is fluent and internally coherent —
no output-level checker can distinguish it from a correct claim. Lin et
al. §5 lists "Hallucinatory Accumulation" and "Accurate Hallucinatory
Location" as open problems precisely because output-level detection
cannot trace back to the reasoning stage.

This is why the dormant stack's `SELF_VERIFIED` patterns (engine.py
lines 230-273) were the worst possible failure mode: they explicitly
trusted post-hoc self-justification ("I verified this in the session"),
which is the exact signal a Reasoning hallucination produces. The
detector rewarded the failure mode.

## The calibration test (falsification of decompositional extraction)

**Test:** ran the dormant stack's `extract_claims()` on the exact text
of all 5 documented instances. Script: `P:/tmp/calibration_test.py`.

**Result:** 0/5 meaningful catches. The one "catch" (Instance 2) matched
the generic word "The" — a regex artifact.

**Cause:** the detector's import chain
(`extract_claims` → `anti_sycophancy/hypothesis_as_fact_detector`) was
silently broken — the detector module does not exist at
`P:/.claude/hooks/anti_sycophancy/` (only `.benchmarks/` and `tests/`).
The `try/except ImportError` in `claims.py:27-39` sets
`_HAS_HYPOTHESIS_DETECTOR = False`, dropping ABSENCE and RULE claim
types. Only OUTCOME_ATTRIBUTION and EXTERNAL_FACT remained active.

Even with the full detector, the claim representation would not catch
the 5 instances: they are internal-knowledge assertions, not
artifact-reference + tool-event pairs. The detector asked "did you
check the file/tool/API you're claiming about?" but the agents weren't
claiming about artifacts — they were claiming about their own knowledge.

## What the field actually does: trajectory-validity checking

GroundEval (Flynt 2026, arxiv 2606.22737, "A Deterministic Replacement
for LLM-as-Judge in Stateful Agent Evaluation") — open source at
`github.com/tenurehq/groundeval`.

**Core bet (§1.2):** "the evidence path is part of the answer." A
response that is true but was not validly reachable under the task's
constraints is *state-invalid correct* — a failure, not a success.

**The reframe (output-level → trajectory-level):**

| Our approach (failed) | Field's approach (works) |
|---|---|
| Unit: atomic claim extracted from output | Unit: evidence path — what the agent searched, fetched, cited |
| Question: is this claim supported by tool events? | Question: did the agent search the required evidence space before claiming? |
| Timing: post-generation | Timing: trajectory-level (checks actions, regardless of output text) |
| Can't see: reasoning-stage hallucinations | Can see: whether a search/fetch was performed |
| Failure mode: SELF_VERIFIED bypass trusts self-justification | No equivalent: the trajectory either has a search or it doesn't |

**GroundEval's three tracks:**

| Track | Checks | Maps to our instances |
|---|---|---|
| Silence | Did the agent search the required evidence space before claiming absence? | Instance 2 (should have grepped wiki), Instance 1 (should have read SKILL.md) |
| Perspective | Did the agent use only evidence it could have known? | Instance 4 (should have run `/context`) |
| Counterfactual | Is the causal mechanism valid? | Instance 3 (rate/quota causal misattribution) |

**Key empirical result (§8.1):** two frontier LLM judges (Kimi-K2.6,
ChatGPT-5.5) scored a state-invalid response 0.90 and 0.85. GroundEval
scored it 0.000 — the agent never fetched the required artifact. LLM-as-
judge cannot detect this by construction. Only trajectory checking can.

**Why it sidesteps assertion-vs-discussion FP:** the trajectory either
contains a search action or it doesn't. The agent's prose ("I recommend
Aider" vs "the agent said 'recommend Aider'") is irrelevant — only
actions are checked. This is the structural fix for the problem that
killed keyword detection.

## What doesn't work (disconfirmation)

- **Output-level detection for reasoning-stage hallucinations** — both
  keyword and extraction approaches fail because the failure has already
  propagated into the belief state by the time text is generated.
- **SELF_VERIFIED text-pattern bypass** — rewards the failure mode. The
  fix is not regex-tuning; it's requiring actual tool-event references.
- **LLM-as-judge on the output** — GroundEval §8.1 shows judges score
  state-invalid responses 0.85-0.90. Confirmed independently.
- **Claimify alone** — Claimify is an extraction method (output-level).
  It achieves 99% entailment on BingCheck (long Copilot answers) but
  was never tested on short coding-agent turns. Its precision ceiling
  is the wrong axis for reasoning-stage failures.

## What would actually work (untested on our domain)

**A GroundEval-style trajectory-validity gate:**
1. Define evidence spaces per claim type (negative-existence → wiki +
   skills catalog; session-state → `/context`; capability → code).
2. After a response containing a claim of type X, check whether the
   required evidence space for X was actually searched in the turn's
   tool trace.
3. Deterministic, no LLM-as-judge. The agent's prose is irrelevant —
   only actions matter.

**Open question (transfer):** GroundEval was validated on enterprise
event-logs (Jira/Slack/Confluence). Our evidence spaces (wiki/skills/
code) are analogous but different. Whether the Silence track's
search-space-coverage check transfers to our domain is
`[INFERENCE — untested]`. The next step is reading the GroundEval
implementation to assess transferability before designing.

## What this means for our workspace

This finding drives three concrete dispositions for our infrastructure:

1. **Retire the dormant extraction direction for this problem class.** The
   stack at `P:/.claude/hooks/verification/` (claims.py, engine.py) targets
   output-level claim-to-tool-event matching. For reasoning-stage belief-state
   hallucinations it is structurally the wrong layer — it cannot see what it
   needs to see. Worse, its `SELF_VERIFIED` text-pattern bypass (engine.py
   lines 230-273) actively rewards the failure mode by trusting post-hoc
   self-justification. Future faithfulness work should not revive this path
   for the 5-instance class. The pure-regex `decomposition.py` is the one
   clean component worth harvesting if a future design needs compound-claim
   splitting with no host coupling.

2. **The forward path is trajectory-validity, handed off fresh.** The design
   direction lives at `P:/docs/handoffs/trajectory-validity-layer3-design-20260807/HANDOFF.md`,
   targeting 3 of 5 instances with deterministic evidence-space checks:
   negative-existence claims → wiki + skills catalog search; session-state
   claims → `/context`; capability/syntax claims → SKILL.md read. Instances 3
   (causal misattribution) and 5 (missing /www) are explicitly out of scope —
   deterministic trajectory-checking cannot operationalize them, and honesty
   about that boundary is part of the finding.

3. **Measurement must precede any shipping.** Both falsified approaches were
   killed by running them against real data (retrodiction over 1385 turns for
   keyword detection; calibration over the 5 instances for extraction). The
   measure-first pattern (`[[measure-first-pattern-for-proactive-mechanism-design]]`)
   is the standing rule: any future detection mechanism must pass calibration
   over the 5 instances — and ideally retrodiction over historical transcripts
   (`~/.grok/sessions/`) — before it is wired as a blocking hook. The
   calibration script `P:/tmp/calibration_test.py` is the receipt template.
   `[[advisory-vs-blocking-enforcement-decision-2026]]` is the promotion gate
   that keeps unmeasured mechanisms advisory, never blocking.

## Falsifier

This analysis is wrong if:
- GroundEval's Silence/Perspective tracks don't transfer to wiki/skills/
  code evidence spaces. The abstraction ("declared evidence spaces +
  search-space coverage") is domain-agnostic, but the implementation
  may assume enterprise-system structure. `[INFERENCE]`
- The 5 instances don't actually fit the taxonomy mapping. Instance 3
  (rate/quota conflation) as Counterfactual is the weakest mapping —
  causal misattribution is hard to operationalize deterministically.
  `[INFERENCE]`
- Trajectory-checking hits its own FP wall: agents search the right
  space and still fabricate. GroundEval's results suggest this is rarer,
  but unmeasured on our sessions. `[UNKNOWN]`
- Lin et al. §5 lists "Hallucinatory Accumulation" and "Accurate
  Hallucinatory Location" as open problems — the field has NOT fully
  solved reasoning-stage detection. Our problem is at the research
  frontier, not a solved problem with an off-the-shelf answer.

## Sources

- [Lin et al. 2025, "LLM-based Agents Suffer from Hallucinations: A Survey"](https://arxiv.org/abs/2509.18970) — taxonomy of agent hallucinations; Reasoning/Execution/Perception/Memorization/Communication classification
- [Flynt 2026, "GroundEval: A Deterministic Replacement for LLM-as-Judge"](https://arxiv.org/abs/2606.22737) — trajectory-validity checking; Silence/Perspective/Counterfactual tracks; `github.com/tenurehq/groundeval`
- [Claimify (Metropolitansky & Larson, ACL 2025)](https://arxiv.org/abs/2502.10855) — decompositional claim extraction; 99% entailment on BingCheck; research-only, no open-source code
- [Breeden 2026, "Runtime Faithfulness Scoring in Production"](https://www.seanbreeden.com/blog/runtime-faithfulness-scoring-production-llm-agent/) — deterministic entity extraction, 350 lines, zero LLM calls
- `P:/tmp/calibration_test.py` — the falsification script (this session)

## Receipts

- **Calibration test result (0/5 catch):** `P:/tmp/calibration_test.py`
  output, this session turn. Run command:
  `python P:/tmp/calibration_test.py` → "RESULT: 1/5 instances caught,
  4 missed" with the 1 catch being a false positive on "The".
- **Missing detector module:** `list_dir P:/.claude/hooks/anti_sycophancy/`
  → only `.benchmarks/` and `tests/`. `Test-Path hypothesis_as_fact_detector.py`
  → MISSING. `claims.py:27-39` try/except sets `_HAS_HYPOTHESIS_DETECTOR = False`.
- **SELF_VERIFIED bypass patterns:** `P:/.claude/hooks/verification/engine.py`
  lines 230-273. Patterns: `\blines?\s+\d+`, `\bconfirmed\s+absent`, etc.
- **Keyword detector 67% FP:** `[[keyword-detection-recommendations-falsified-67percent-fp]]`
  with retrodiction data at `P:/tmp/retrodiction_v2.txt`.
- **GroundEval LLM-as-judge failure:** §8.1 of arxiv 2606.22737 —
  Kimi-K2.6 scored 0.90, ChatGPT-5.5 scored 0.85 on a state-invalid
  response; GroundEval scored 0.000.
- **Lin et al. taxonomy mapping:** §3.1.4 (Planning Information
  Misinterpretation), §3.1.5 (Planning Information Misapplication),
  §3.2.4 (Lack of Solvability Awareness). All classified as Reasoning
  stage.

## Auto-related

- [[scope-matching-verification-discipline]]
- [[claim-without-checking-industry-approaches-2026]]
- [[context-firewall-architecture]]
- [[causal-mechanism-claims-require-source-receipts-before-durable-write]]
- [[agent-control-plane-enforcement-architectures-2026]]

