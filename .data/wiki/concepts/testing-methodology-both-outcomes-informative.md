---
title: "Testing methodology for AI agent verification: both-outcomes-informative tests"
created: 2026-07-21
source: session-2026-07-21 (/www compound research + session testing failures)
sources:
  - https://testrigor.com/blog/hypothesis-testing/
  - https://www.patronus.ai/llm-testing
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC2996198/
  - https://medium.com/@suyashmohta97/understanding-the-four-outcomes-in-hypothesis-testing-false-positive-false-negative-true-bb7f9975fdda
  - https://support.optimizely.com/hc/en-us/articles/4410282998541-Design-an-effective-hypothesis
  - P:/.data/wiki/concepts/skill-techniques-index.md
  - P:/.data/wiki/concepts/fabricated-causal-chain-receipt-required.md
tags: [testing, methodology, hypothesis-driven, verification, model-verification, layer-isolation, test-design, both-outcomes]
host: both
agent: grok
verification: web_sources_cited_plus_session_evidence
cognitive_load: 4
summary: "How to design tests for AI agent model/capability/integration verification where both positive and negative outcomes are informative and point to different next steps. Born from a session where trivial-echo tests passed but real-task tests failed, leading to wrong conclusions about model availability. Covers hypothesis structure, four-outcome model, layer isolation, dependency ordering, and the distinction between trivial and real tests."
---

# Testing methodology for AI agent verification: both-outcomes-informative tests

## The core principle

**A test where only one outcome is possible isn't a test — it's confirmation bias dressed as rigor.** Every test must have:
- A **positive outcome** that confirms the hypothesis AND tells you what to do next
- A **negative outcome** that refutes the hypothesis AND tells you what to investigate instead
- **Both outcomes must be distinguishable** — if you can't tell the results apart, it's not a test

This is the scientific method (hypothesis → experiment → observe → conclude) applied to AI agent verification. The key insight from statistics: every hypothesis test has four possible outcomes, not two:

| | Null hypothesis is TRUE | Null hypothesis is FALSE |
|---|---|---|
| **Reject null** | Type I error (false positive) | True positive ✅ |
| **Fail to reject null** | True negative ✅ | Type II error (false negative) |

Both errors matter. A test that only catches false positives but misses false negatives (or vice versa) is incomplete.

## The session incident that motivated this

On 2026-07-21, I tested DiffusionGemma for subagent reads:
1. **Test 1 (trivial echo):** spawned 3 subagents saying "return 'TEST N OK'" → all 3 passed → concluded "works for parallel fan-out"
2. **Test 2 (real read):** spawned subagent to read a file and summarize → 400 Bad Request, empty content → concluded "model fails on real tasks"

Both conclusions were wrong or premature:
- Test 1's positive outcome didn't test real capability — trivial echo doesn't exercise file reading, structured output, or tool use
- Test 2's negative outcome didn't isolate WHERE the failure was — model? gateway? framework? prompt format?

**The fix:** design tests where both outcomes are informative, then order them by dependency so each test's result determines what to test next.

## Do's

### 1. Structure every test as a hypothesis

Source: [Optimizely](https://support.optimizely.com/hc/en-us/articles/4410282998541), [testrigor](https://testrigor.com/blog/hypothesis-testing/)

Format: **If [CAUSE], then [EFFECT], because [RATIONALE].**

Example:
- **If** the gateway properly translates DiffusionGemma's diffusion output to standard chat completions format, **then** a direct curl to the endpoint will return non-empty content, **because** the curl bypasses Grok's agent framework and isolates the gateway translation layer.
- **If** thinking mode is causing the empty content error, **then** disabling thinking via `chat_template_kwargs: {"thinking": false}` will produce non-empty content, **because** the 35 output tokens were reasoning tokens routed to a separate field.

Both hypotheses have falsifiable predictions. Both have different investigation paths if refuted.

### 2. Design for both outcomes

Before running any test, write down:
- **If positive (hypothesis confirmed):** what does this tell me? What's the next test?
- **If negative (hypothesis refuted):** what does this tell me? What's the alternative hypothesis?

If you can't answer both questions, the test isn't designed yet.

Example (bad):
- Test: "spawn subagent with DiffusionGemma, see if it returns text"
- Positive: "it works" → next: use it
- Negative: "it doesn't work" → next: ??? (no isolation, no alternative hypothesis)

Example (good):
- Test: "direct curl to endpoint with simple prompt, capture full response"
- Positive: "endpoint returns valid content" → next: the problem is in Grok's agent framework or gateway; investigate message format compatibility
- Negative: "endpoint returns empty/error" → next: the problem is in the model or endpoint config; investigate auth, model availability, or endpoint configuration

### 3. Isolate layers before testing integration

Source: session 2026-07-21; [Patronus LLM testing](https://www.patronus.ai/llm-testing) model-centric vs application-centric distinction

When a system has multiple layers (model → inference provider → gateway → agent framework → subagent dispatch), test each layer in isolation before testing the full stack.

**Layer isolation test matrix:**

| Layer | Test method | What it isolates |
|---|---|---|
| Model + endpoint | Direct curl/API call to inference endpoint | Model capability, endpoint config, auth |
| Gateway translation | API call through gateway (not through agent framework) | Gateway's format translation |
| Agent framework | spawn_subagent with the model | Framework's message assembly, tool routing |
| Full integration | Real task through full stack | End-to-end behavior |

**The foundation test comes first.** If the direct curl fails, no amount of gateway/framework tweaking will help. If it succeeds, you know the problem is upstream.

### 4. Test real tasks, not just trivial tasks

Source: session incident (DiffusionGemma passed echo, failed real reads)

A trivial task (echo, "say hello") exercises:
- Basic request/response routing ✅
- Model availability ✅

It does NOT exercise:
- File reading and structured output ❌
- Tool use (read_file, grep, run_terminal_command) ❌
- Long context handling ❌
- Multi-turn conversation ❌
- The specific output format the framework expects ❌

**Rule:** a model that passes trivial tasks but fails real tasks is NOT "working." It's "reachable." Reachability ≠ capability.

### 5. Order tests by dependency

Source: session 2026-07-21 test matrix design

Tests should form a dependency graph where each test's result determines which test to run next:

```
T1 (isolation: direct curl)
  ├── PASS → T2 (capability: real read) → T3 (quality: blind comparison) → T4 (operationalization)
  └── FAIL → STOP. Different investigation path (endpoint config, auth, model availability).
```

Don't run T3 before T1. If the model doesn't even produce output at the endpoint level, quality comparison is meaningless.

### 6. Include negative tests alongside positive tests

Source: [testrigor](https://testrigor.com/blog/hypothesis-testing/) — "Positive and Negative Testing"

- **Positive test:** verify the system does what it should (e.g., "DiffusionGemma produces a correct summary")
- **Negative test:** verify the system handles what it shouldn't gracefully (e.g., "DiffusionGemma with an invalid model name returns a clear error, not silent empty output")

Negative tests catch the failure modes that positive tests miss: silent failures, empty responses, cached/templated responses that look like real output.

### 7. Enumerate assumptions before testing

Source: /tp mode 8 (hidden decision density); session 2026-07-21 assumptions audit

Before running a test, enumerate the assumptions baked into it:
- "The gateway passes through the parameter I'm testing" (assumption)
- "The model slug maps to the model I think it does" (assumption)
- "The trivial task actually exercised the model, not a cached response" (assumption)
- "Free local models are preferable to paid API models" (assumption)

Each assumption is a potential false-positive source. If the test passes but an assumption is wrong, the positive outcome is misleading.

## Don'ts

### 1. Don't accept the first positive outcome

Source: session incident (DiffusionGemma echo test → concluded "works")

A single positive result is necessary but not sufficient. Before concluding "works":
- Run a real-task test (not just trivial)
- Run a negative test (what happens when it SHOULD fail?)
- Run the isolation test (which layer produced the positive?)

### 2. Don't run tests without both outcomes designed

If you can't articulate what the negative outcome would tell you, you're not testing — you're confirming.

**Anti-pattern:** "Let me try spawning with this model and see what happens."
- This is exploration, not testing. Exploration is fine for discovery, but don't call the result "verified."

### 3. Don't skip layer isolation

Source: session incident (tested through spawn_subagent, couldn't tell if failure was model/gateway/framework)

Testing through the full stack without isolating layers means a failure could be anywhere. You'll spend N iterations guessing which layer is broken instead of 1 test that tells you directly.

### 4. Don't conflate trivial-task success with real-task capability

Source: session incident

"Returns 'TEST 1 OK' in 4 seconds" tells you the model is reachable and can produce short strings. It does NOT tell you the model can read files, use tools, produce structured output, handle long context, or survive multi-turn conversations.

### 5. Don't test capability without testing quality

Source: [Patronus](https://www.patronus.ai/llm-testing) — model-centric vs application-centric evaluation

A model that returns text but produces hallucinated, inaccurate, or low-quality summaries is not "working for our use case." Always include a quality comparison (blind A/B against a known-good model).

### 6. Don't ignore concurrency vs capability interaction

Source: session incident (concurrency test passed on trivial tasks; untested on real tasks)

Parallel trivial tasks succeeding doesn't mean parallel real tasks will succeed. Real tasks consume more compute per request; the inference endpoint may serialize under load even if it parallelizes trivial requests.

### 7. Don't test without enumerating assumptions

Source: /tp mode 8

Every test carries hidden assumptions about what the test exercises, what the gateway passes through, what the model actually is, and what "success" means. Enumerate them before running. Each unenumerated assumption is a potential false positive.

### 8. Don't draw conclusions beyond what the test actually tested

Source: [[fabricated-causal-chain-receipt-required]]

"DiffusionGemma fails on real tasks" was a conclusion drawn from a test that actually showed "spawn_subagent with DiffusionGemma returns 400 on file-reading tasks." The test didn't show the model fails — it showed the integration fails. The conclusion exceeded the evidence.

## The test design template

For any verification test, fill in this template before running:

```
## Test: <name>
Hypothesis: If [CAUSE], then [EFFECT], because [RATIONALE].
Layer tested: <model | gateway | framework | full-stack>
Task type: <trivial | real>
Assumptions:
  - A1: <assumption>
  - A2: <assumption>
Positive outcome: <what it means + next test>
Negative outcome: <what it means + alternative hypothesis>
Dependencies: <must run after T(N)>
```

## Relationship to existing techniques

- [[skill-techniques-index]] T21 (Concurrency test protocol) — needs strengthening: must include real-task test, not just trivial echo. The protocol should be: (1) 3 trivial tasks for parallelism, THEN (2) 1 real task for capability. Both must pass.
- [[skill-techniques-index]] T20 (Two-phase analysis) — the code breadth pass is a form of layer isolation: scan all artifacts mechanically before investing LLM depth-reads.
- [[fabricated-causal-chain-receipt-required]] — "DiffusionGemma fails on real tasks" was a fabricated causal chain. The receipt (400 error output) showed the integration failed, not the model. The conclusion exceeded the receipt.
- [[skill-techniques-index]] T10 (Spot-check gate) — the spot-check is a form of both-outcomes test: verify against evidence, flag if contradicted.
- [[deliberation-waste-re-deriving-same-answer]] — re-testing the same thing without new evidence is deliberation waste; the dependency graph prevents this.

## The four-outcome model applied to agent verification

From [statistical hypothesis testing](https://pmc.ncbi.nlm.nih.gov/articles/PMC2996198/):

| | Model/gateway actually works | Model/gateway actually broken |
|---|---|---|
| **Test passes** | True positive ✅ — correctly identified as working | False positive (Type I) — test passed but for wrong reason (cached response, trivial task, wrong layer) |
| **Test fails** | False negative (Type II) — test failed but model works (wrong prompt format, missing parameter, framework incompatibility) | True negative ✅ — correctly identified as broken |

Both error types have occurred in our session:
- **Type I:** DiffusionGemma trivial echo passed → concluded "works" → real task failed
- **Type II:** (not yet observed for DiffusionGemma, but the risk exists: gateway might work with the right parameters even though our test failed)

## Open questions

- Should the test design template be encoded as a technique (T23) in skill-techniques-index?
- Should /check and /verify skills reference this methodology when verifying model availability?
- Is there a standard set of layer-isolation tests for the Grok Build stack (model → CCR → gateway → Grok framework → subagent)?
- Should the concurrency test protocol (T21) be rewritten to require both trivial AND real-task tests?

## Sources (full list)

- [Hypothesis Testing: Driving Quality and Innovation](https://testrigor.com/blog/hypothesis-testing/) — testrigor, 2023-05-25. Source for: hypothesis structure (If/Then/Because), positive and negative testing, Type I and Type II errors, A/B testing methodology.
- [LLM Testing: The Latest Techniques & Best Practices](https://www.patronus.ai/llm-testing) — Patronus AI. Source for: model-centric vs application-centric evaluation, four testing dimensions (functionality, performance, security, alignment), nondeterministic outputs, context sensitivity, pointwise vs pairwise testing.
- [Hypothesis testing, type I and type II errors](https://pmc.ncbi.nlm.nih.gov/articles/PMC2996198/) — Banerjee et al., NIH/PMC. Source for: the four-outcome model, statistical foundations of hypothesis testing.
- [Design an effective hypothesis](https://support.optimizely.com/hc/en-us/articles/4410282998541) — Optimizely. Source for: the If/Then/Because hypothesis format.
- [Understanding the Four Outcomes in Hypothesis Testing](https://medium.com/@suyashmohta97/understanding-the-four-outcomes-in-hypothesis-testing-false-positive-false-negative-true-bb7f9975fdda) — Medium. Source for: clear visual explanation of true/false positive/negative matrix.

## Auto-related

- [[agent-oversight-rubber-stamping]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[operator-collaboration-style-and-leverage]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
