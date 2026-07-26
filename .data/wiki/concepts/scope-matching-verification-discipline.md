---
title: "Scope-matching verification discipline — the literature on why self-verification has a structural ceiling"
created: 2026-07-26
revised: 2026-07-26
source: session-20260726 (/www research on LLM verification scope-matching; revised after /tp critique go-mimo-v2-5)
tags: [verification, scope-matching, self-verification, external-verification, llm-agents, hallucination, process-reward-models, claim-grounding, research]
summary: >
  Research on LLM verification converges on one finding: self-verification doesn't work reliably regardless of how disciplined the scope-matching is, because a single agent shares its own training-data blind spots. The literature distinguishes process verification (check each step/scope item) from outcome verification (check the final answer) — our Option B (scope-matching discipline) is the claim-side analog of process verification. REVISED 2026-07-26 after /tp critique: all 5 session near-misses were layer-1 failures (scope-matching would have caught each one), not layer-2 as originally classified. The operator IS the structural external verifier for non-file claims — the gap is not absence of layer 2 but failure to systematize operator catches. The Brilliant (2026) structural ceiling applies to autonomous systems; in a human-directed system, the operator breaks the ceiling by having different training data, blind spots, and incentives. The originally-recommended "scope-receipt block" was rejected — it is the model-authored-ledger anti-pattern from [[best-practices-enforcement-mechanism-grok-build]].
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://pub.towardsai.net/how-multi-agent-self-verification-actually-works-and-why-it-changes-everything-for-production-ai-71923df63d01 (Towards AI, 2026)
  - https://www.preprints.org/manuscript/202601.0892 (Brilliant 2026, information-theoretic limits of self-correction)
  - https://arxiv.org/html/2507.11662v2 (Andrade et al., agreement bias in MLLM verifiers)
  - https://futureagi.com/blog/understanding-llm-hallucination-2025/ (FutureAGI, 2026 hallucination landscape)
  - https://openreview.net/forum?id=A6Y7AqlzLW (Setlur et al., Process Advantage Verifiers, 304 citations)
  - https://www.researchgate.net/publication/389855859_SagaLLM_Context_Management_Validation_and_Transaction_Guarantees_for_Multi-Agent_LLM_Planning (SagaLLM, multi-agent echo effects)
  - https://medium.com/@Micheal-Lanham/self-correcting-agents-are-not-what-you-think-they-are-d19398186373 (self-correction failure modes)
relations:
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: refines
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: related
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: related
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: related
---

# Scope-matching verification discipline

> **Revision note (2026-07-26):** This concept was revised after a /tp critique (go-mimo-v2-5, subagent `019f9f94-138e-78e2-b4db-0b4c68b3217d`) found three problems with the original recommendations: (1) all 5 session near-misses were misclassified as layer-2 failures when they are layer-1 failures, (2) the recommended "scope-receipt block" is the model-authored-ledger anti-pattern prohibited by [[best-practices-enforcement-mechanism-grok-build]], and (3) the "structural ceiling" argument was applied to a human-directed system where the operator IS the external verifier. The research synthesis (Findings 1-4, misconceptions, receipts) is preserved as-is; only the interpretation, mapping table, and recommendations were revised. Revised sections are marked [REVISED].

## Decision context

**Why this research was needed:** session 019f9bfe produced 5 near-miss instances where the model made confident claims or shipped code edits that were wrong or unverified — despite documented rules against exactly this pattern. The `/why` RCA proposed three fix options (A: pre-claim gate, B: verifier-scope discipline, C: Stop-hook extension). The operator asked for thorough research on the topic space before committing to a fix.

The gap in knowledge: is the proposed Option B (enumerate scope → match checks to scope) supported by the broader literature on LLM verification? Or is it another plausible-sounding self-applied technique that the field has already shown doesn't work?

## What the literature says

### Finding 1: Self-verification has a structural ceiling — it cannot be fixed by better discipline alone

The most consistent finding across 2025-2026 research: **a single LLM cannot reliably verify its own outputs**, and this is structural, not fixable by better prompting or scope-matching.

- **Brilliant (2026, "Limits of Self-Correction in LLMs: An Information-Theoretic Analysis"):** "A single agent evaluating its own outputs faces elevated risk of correlated error: sharing training data, inductive biases, and blind spots creates the failure." This is the information-theoretic formalization of the bias blind spot — the agent's errors and its verification of those errors are correlated because they come from the same model.
- **SagaLLM (2025):** "Without external verification, agents can reinforce shared errors, creating echo effects that inflate confidence in wrong conclusions, and small inaccuracies accumulate over repeated cycles."
- **Towards AI (2026):** "A single LLM can't reliably verify its own outputs — the structural reasons for this are well understood."
- **Medium (2026, "Self-Correcting Agents Are Not What You Think They Are"):** identifies three NEW failure modes that correction loops introduce: sycophantic correction (agreeing with the original output), judge bias (the verifier shares the generator's priors), and hallucinated verification (the check itself is wrong).

**Implication for Option B:** scope-matching discipline (enumerate scope -> match checks) improves the QUALITY of self-verification but cannot escape the structural ceiling. The model will still share blind spots with its own verifier. Option B is necessary (catches easy cases) but not sufficient (misses the correlated-error class).

**Why this matters for our workspace specifically:** our 5 near-misses this session confirm the pattern empirically. The crawl4ai upgrade claim was wrong because the model shared its own blind spot about "upgrade = good" without checking for version-specific blockers. The /close-/aar gap was wrong because the model shared its own blind spot about "grep returned results = thorough check." In both cases, a self-applied scope-matching check would have asked "did I check the right thing?" — and the model would have answered "yes" because it shares the blind spot that made the original claim wrong. External verification (the operator, /check) caught what self-verification structurally could not. This is the information-theoretic argument from Brilliant (2026) made concrete: the errors and the error-checking are correlated because they come from the same model with the same training priors. No amount of scope-matching discipline breaks that correlation.

### Finding 2: Process verification (per-step) outperforms outcome verification (final-answer-only)

- **Setlur et al. (Process Advantage Verifiers, 304 citations, 2025):** process reward models that verify EACH STEP of reasoning outperform outcome reward models that only check the final answer. The per-step verification catches errors at the point they occur, before they propagate.
- **FutureAGI (2026):** "hallucination is a metric problem, not a model problem. The fix is grounding plus runtime detection plus per-mode reporting. Wire traces. Gate the response on the judge."

**Implication for Option B:** scope-matching discipline IS process verification applied to claims. Enumerating scope items and verifying each one is the claim-side analog of per-step reasoning verification. This validates the approach — but only as the first layer, not the only one. This connects to [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — that concept covers reading the source before claiming mechanism; this concept covers matching verifier scope to claim scope before claiming verification. Same root cause (sufficiency illusion), different surface form.

### Finding 3: Agreement bias — verifiers tend to over-validate

- **Andrade et al. (2025, "Mitigating Agreement Bias in MLLMs with Self-Grounded Verification"):** verifiers exhibit a "strong tendency to over-validate agent behavior" — they agree with the original output more than accuracy warrants. This is the `/tp` same-model-collapse pattern documented at scale: even a separate "verifier" model can share the generator's agreement bias if they're from the same family.

**Implication for our workspace:** the `/check` subagent verifiers we spawn are susceptible to agreement bias, especially when using parent-inherited or same-family models. The cross-family spawning discipline (from `/tp`'s pool table) is the structural defense — but it's fragile (quota failures, serialization errors push back to parent-inherited). This is the same vulnerability documented in [[blind-spot-detection-methods]] under devil's advocate: the technique fails when the advocate isn't genuinely independent. It's also the same failure class as [[fabricated-causal-chain-receipt-required]] — the model's own check feels sufficient but shares the original error's blind spot.

### Finding 4: External verification is the consensus structural fix

Every source converges on the same recommendation: **external verification (not self-verification) is the durable answer.**

- **Towards Long-Horizon Agents (survey, 2026):** "self-checking alone is not a trustworthy guarantee" — recommends external acceptance tests and red-team suites.
- **FutureAGI (2026):** "gate the response on the judge" — runtime external judges, not self-checks.
- **VeriGuard (2025):** verified code generation via external tools, not model self-checks.
- **SagaLLM (2025):** transaction guarantees with external validation, not agent self-checks.

**Implication for our three options:** the literature says Option C (structural external gate) is the one that actually works. Options A and B are process improvements that help but don't escape the ceiling. The question is whether Option C is feasible for the specific class of non-file claims (crawl4ai upgrade recommendation, /close-/aar gap claim) where we have no structural external gate today.

## How this connects to the workspace's existing enforcement patterns

The workspace already implements the two-layer defense the literature recommends — partially. [[best-practices-enforcement-mechanism-grok-build]] documents the pattern: behavioral rules fire at the moment of dismissal; review gates detect violations mechanically. The scope-matching concept extends this from code review to claim verification.

Layer 1 (self-verification) exists in /check's verifier protocol (enumerate checklist items, verify each). Layer 2 (external verification) exists in the Stop hook (file-state) and /check verifiers (code + contract). The gap is that neither layer covers non-file prose claims — the class where 3 of 5 near-misses occurred.

The existing [[causal-mechanism-claims-require-source-receipts-before-durable-write]] concept covers reading the source before claiming mechanism. This concept adds: matching verifier scope to claim scope before claiming verification, AND recognizing that even scope-matched self-verification has a structural ceiling that only external verification can break.

## How this maps to our workspace [REVISED]

| Layer | What we have | What the literature says we need |
|---|---|---|
| **Self-verification (process)** | Option B: enumerate scope → match checks. Partially implemented in /check verifier protocols. | Necessary but not sufficient — catches easy cases, misses correlated-error class |
| **External verification (runtime)** | Stop hook (file-state class); /check verifiers (code + contract class); **operator (non-file claims — STRUCTURAL, not "non-structural")** | The consensus durable fix. The operator IS the external verifier for non-file claims — different training data, different blind spots, different incentives from the LLM. |
| **Cross-model verification** | /tp two-lens pool; /aar cross-model audit; /check model-tiered verifiers | Partially implemented; agreement bias is the residual risk |

**[REVISED] The 5 near-misses this session were ALL layer-1 failures.** The original concept misclassified the 3 non-file claims as layer-2 failures to justify the scope-receipt block. The correct classification (verified by /tp critique, go-mimo-v2-5, 2026-07-26):

- **crawl4ai upgrade claim (non-file):** model recommended upgrading 0.7.8→0.9.2 without checking wiki for version blockers. A scope-matching check ("what evidence supports this upgrade? enumerate: compatibility, blocker history, known issues") would have surfaced the wiki-documented lxml blocker. **Layer-1 failure — didn't check at all.**
- **/tp quick misrecommendation (non-file):** model recommended /tp quick for verifying /design changes without checking the skill definition. A scope-matching check ("is /tp quick the right tool? enumerate: what /tp quick does vs. what I need") would have caught that /tp quick is same-agent dialogue, not an external verifier. **Layer-1 failure — didn't check at all.**
- **/close-/aar gap (non-file):** model claimed /close doesn't auto-invoke /aar using vocabulary-mismatch grep (searched "blind|gap|filter" but the mechanism uses "retrospective"). A scope-matching check ("did I check the actual mechanism, not just grep for my vocabulary?") would have required reading close SKILL.md directly. **Layer-1 failure — checked the wrong scope.**
- **wiki_search.py add_document bug (file):** model passed `markdown_file=<path>` without checking qmd 0.1.2's actual API signature (`add_document(document_id, markdown, metadata)`). A scope-matching check ("what's the actual function signature?") would have caught the mismatch. **Layer-1 failure — didn't check the API.**
- **wiki_search.py list_documents bug (file):** model used `getattr(d, "document_id", d.get(...))` without checking that qmd returns `list[str]`. A scope-matching check ("what does list_documents actually return?") would have caught the type mismatch. **Layer-1 failure — didn't check the return type.**

**All 5 were caught by external verification (operator or /check) — layer 2 worked as designed.** None were layer-2 failures (where the model checked but shared the blind spot). The original concept's classification of instances 1-3 as layer-2 was the error that unjustified the scope-receipt block recommendation.

## The operator as structural external verifier [REVISED — new section]

The Brilliant (2026) information-theoretic argument — that self-verification shares the generator's weights and therefore its errors — is correct **for autonomous systems**. It does NOT apply unchanged to human-directed systems where the operator is in the loop. The operator has:

- **Different training data** (human cognition, not LLM weights)
- **Different blind spots** (the operator's blind spots are not correlated with the LLM's blind spots — they're independent error structures)
- **Different incentives** (the operator wants correctness; the LLM is biased toward closure and helpfulness)

This is the **solve-verify asymmetry** made structural: verifying a claim is in a different complexity class than generating it, and the operator's verification does not share the LLM's error-correlation structure. The operator catching 5/5 near-misses this session is not luck — it's the structural property working as designed. (The classic framing: Pólya's distinction between generation and verification as separate phases; the complexity-theory framing: NP-generation vs. polynomial-time verification when the verifier is genuinely independent.)

**What this reframing means:** the workspace does NOT lack layer 2 for non-file claims. The operator IS layer 2 for non-file claims. The real gaps are operational, not structural:

1. **Operator catches are expensive** — they consume operator attention, the scarcest resource in the system. Every layer-1 failure that reaches the operator is a tax on operator time.
2. **Operator catches aren't systematized** — each catch is a one-off correction; the specific blind spot that caused it isn't automatically fed back into layer-1 as a named check that prevents recurrence.
3. **Operator catches depend on operator vigilance** — if the operator is tired, distracted, or trusts the model's confidence, the catch fails. This is the residual risk, not the absence of a gate.

**The fix is NOT to build a structural gate that replaces the operator** (that was the rejected scope-receipt block — a model-authored ledger, which is the anti-pattern documented in [[best-practices-enforcement-mechanism-grok-build]]: "the model can silently drop requirement C at write time"). **The fix is to systematize the operator catch** so that each one reduces the probability of the next:

- Track operator-caught near-misses in AAR Q11 (already wired — "operator-flagged items without resolution")
- Feed each catch back into layer-1 as a named scope-matching check (e.g., "before claiming version upgrade, check wiki for blockers"; "before recommending a skill mode, check the skill definition")
- Use /tp two-lens for non-file claims that warrant a second lens before the operator sees them (claim-type routing — cheaper than operator attention for high-stakes prose claims)

## Receipts (workspace mechanism claims)

- **Stop hook catches "file modified after verification" class** — [OBSERVED] session 019f9bfe: two Stop hook blocks (continuations 6c63b501, 34877404) fired when wiki_search.py and close_accounting.py were modified after their last verification tool call. The hook's required-verification-scope message names the specific files. Inspected this session.
- **/check verifiers catch code and contract issues** — [OBSERVED] /check subagent 019f9d00 found the `list_documents` AttributeError bug in wiki_search.py; /check subagent 019f9f57-a508 found the `markdown_file` kwarg bug in crawl_to_qmd.py. Both were external verifiers (cross-family spawns) that caught what self-verification missed.
- **Operator catches non-file claims** — [OBSERVED] session 019f9bfe: operator caught crawl4ai upgrade claim (wiki documented lxml blocker), /tp quick misrecommendation (wrong skill mode), /close-/aar false gap (close SKILL.md line 123 contradicts). [REVISED: the operator IS the structural external verifier for this claim class — different training data, different blind spots from the LLM. The original framing ("caught only by operator attention, non-structural") was wrong; the operator is structural.]
- **All 5 near-misses were layer-1 failures** — [REVISED, DERIVED from per-instance analysis above] each near-miss had a specific scope-matching check that would have caught it. None were layer-2 failures (checked but shared blind spot). The original "3 were layer-2" classification was the error that unjustified the scope-receipt block.
- **5 near-misses this session** — [OBSERVED] session transcript: each near-miss documented in the /why RCA with receipt (who caught it, what was claimed vs. what was true).

## What people get wrong about LLM self-verification

Three common misconceptions the research corrects:

**Misconception 1: "Better prompting will fix self-verification."** The information-theoretic argument (Brilliant 2026) is fundamental, not prompt-level. The verifier shares the generator's training data, which means its errors and the original errors are correlated at the weight level, not the prompt level. No prompt technique breaks weight-level correlation. The fix is external verification (different model, different tool, human review) — not a better self-check prompt.

**Misconception 2: "A separate verifier model solves it."** Andrade et al. (2025) show agreement bias persists even with different models if they're from the same family. Two GPT-4 instances checking each other share more blind spots than GPT-4 + Claude. The workspace's /tp pool table (cross-family spawning) is the right instinct; same-family spawning is the failure mode the operator caught this session (glm-5-2 on glm-5-2 parent).

**Misconception 3: "If the verifier passes, the claim is verified."** Hallucinated verification (Medium 2026) is when the check itself is wrong — the verifier confidently reports "PASS" for a claim it didn't actually validate. This is the _has_code_writes incident: the syntax check "passed" (it was a real pass), but the claim ("detects .md files") was not within the syntax check's scope. The verifier wasn't wrong; the scope-mapping was. This is why scope-matching discipline matters even when the verifier is external — the scope-mapping step determines what the verifier is actually checking.

## What this means for our recommendation [REVISED]

The /why RCA recommended "Option B, reinforced by Option A, defer Option C." The research and the /tp critique modify this:

- **Option B (scope-matching discipline): ADOPT as layer 1 — this is the highest-leverage fix.** All 5 near-misses were layer-1 failures; scope-matching would have caught each one. The Setlur et al. process-verifier research validates the per-step/per-scope-item approach. Add it to AGENTS.md as a named workflow step: before any completion claim, enumerate the claim's scope as a checklist, then verify each scope item has a matching check. This is what worked for the wiki_search.py verifier (6 enumerated items, all checked) vs. what failed for the 5 near-misses (scope not enumerated).
- **Option A (pre-claim labeling): ADOPT as layer 1 reinforcement.** Label unverified claims [INFERENCE] / [UNVERIFIED]. No claim ships as [FACT] without scope-matching receipt. The literature's agreement-bias finding (Andrade et al.) warns that even the model's own confidence in "I checked this" is unreliable — so the labeling must be mechanical (did a scope-matching check run?) not judgmental (does the model feel confident?).
- **Option C (scope-receipt block): REJECT — contradicts the workspace's own anti-pattern list.** The original concept recommended a model-authored "scope-receipt block" (claim → verifier → scope covered) that the Stop hook would check for presence. This is exactly the "Model-authored requirement ledger" anti-pattern documented in [[best-practices-enforcement-mechanism-grok-build]]: "Actor-authored metadata; per Disguise 5, the model can silently drop requirement C at write time." The /tp critique (go-mimo-v2-5, 2026-07-26) caught this contradiction. The scope-receipt block reproduces the failure it's meant to detect — the model can game it by listing a verifier without actually running it, or by dropping inconvenient scope items. The original concept's own disconfirmation ("even if gameable, it makes scope legible at emission time") does not overcome the anti-pattern: legibility that the actor controls is not verification.
- **Operator-catch systematization: the actual layer-2 fix for non-file claims.** The operator IS the structural external verifier. The fix is systematization, not gate-building: (1) AAR Q11 tracks operator catches, (2) each catch feeds back into layer-1 as a named scope-matching check (closing the loop so the same blind spot doesn't recur), (3) /tp two-lens for high-stakes non-file claims before the operator sees them (claim-type routing — cheaper than operator attention).

**[REVISED] The key insight:** the question is not "behavioral vs. structural" — it's "which layer catches which failure class, and is each layer doing its job." Layer 1 (scope-matching) catches the "didn't check at all" class — which is what all 5 near-misses were. Layer 2 (external verification via operator + /check + Stop hook) catches the "checked but shared the blind spot" class — which is what zero near-misses were this session, but remains the residual risk the literature warns about. The original concept's claim that "instances 1, 2, 3 were layer-2 failures" was the misclassification that unjustified the scope-receipt block. The corrected picture: layer 1 is underinvested (adopt scope-matching discipline), layer 2 is working (operator caught 5/5) but expensive (systematize via AAR Q11 feedback loop).

## What this means for our workspace [REVISED]

- **Adopt scope-matching as a named AGENTS.md workflow step (Option B).** Before any completion claim, enumerate the claim's scope as a checklist, verify each scope item has a matching check. This is layer 1 and the highest-leverage fix given that all 5 near-misses were layer-1 failures.
- **Systematize operator catches via AAR Q11 feedback loop.** The AAR blind-spot sub-check already flags "operator-flagged items without resolution." Extend it to require a layer-1 feedback item for each catch: "what named scope-matching check would have caught this?" This closes the loop — each operator catch becomes a layer-1 improvement that prevents recurrence. This is the systematization the operator-as-external-verifier framing demands.
- **Claim-type routing for non-file claims.** For high-stakes non-file claims (version recommendations, skill-mode recommendations, gap claims about workspace capabilities), route through /tp two-lens before the operator sees them. This catches the easy layer-1 cases before they consume operator attention, reserving operator time for the genuine layer-2 class.
- **Do NOT build the scope-receipt block.** It is the model-authored-ledger anti-pattern from [[best-practices-enforcement-mechanism-grok-build]]. The /tp critique caught this contradiction; the original recommendation is retracted.
- **Extend the receipt-before-write handoff trigger to count all near-miss instances.** The existing `receipt-before-write-workflow-and-hook-20260726` handoff tracks the pattern. Its trigger (3 recurrences in 10 sessions) should count ALL near-miss instances — including non-file claims caught by the operator, not just wiki writes. But the structural fix it points to is layer-1 discipline + operator-catch systematization, NOT the scope-receipt block.
- **Track near-miss rate across sessions.** The falsifier for the two-layer defense: if near-miss rate drops after adopting layer 1 (scope-matching discipline), layer 1 is doing its job. If it stays high, the AAR Q11 feedback loop isn't translating catches into layer-1 improvements — strengthen the feedback loop, don't add a gate.

## Falsifier

This research synthesis is wrong if, within 12 months:
- **A technique emerges that makes LLM self-verification reliable without external checks** — disconfirming the structural-ceiling finding. Counter: the information-theoretic argument (Brilliant 2026) is fundamental; a technique would need to break the correlation between generator and verifier errors.
- **Agreement bias is solved by a prompting technique** — making same-model verification sufficient. Counter: Andrade et al. tested mitigation techniques; agreement bias persisted.
- **The workspace's layer-2 coverage (Stop hook + /check + operator) proves sufficient without layer 1** — meaning scope-matching discipline adds no marginal value. Test: adopt layer 1, measure near-miss rate over 20 sessions, compare to baseline.
- **[REVISED] The operator-as-external-verifier framing is wrong if operator catch rate drops below ~80% on layer-1 failures** — meaning the operator is not actually a reliable external verifier (tired, distracted, or trusts model confidence). Counter: the operator caught 5/5 this session. Test: track operator catch rate in AAR Q11 over 20 sessions. If catch rate falls, the systematization (feedback loop into layer 1) must reduce the load on operator attention, not replace the operator with a gate.

## Sources

- [How Multi-Agent Self-Verification Actually Works](https://pub.towardsai.net/how-multi-agent-self-verification-actually-works-and-why-it-changes-everything-for-production-ai-71923df63d01) (Towards AI, 2026) — "a single LLM can't reliably verify its own outputs"; four verification architectures. Contributed: the structural impossibility argument and the taxonomy of verification approaches.
- [Limits of Self-Correction in LLMs](https://www.preprints.org/manuscript/202601.0892) (Brilliant, 2026) — correlated error between generator and verifier. Contributed: the information-theoretic formalization explaining WHY scope-matching can't break the ceiling. [REVISED applicability: applies to autonomous systems; in human-directed systems the operator breaks the ceiling.]
- [Mitigating Agreement Bias in MLLMs](https://arxiv.org/html/2507.11662v2) (Andrade et al., 2025) — verifiers over-validate. Contributed: the cross-family requirement for external verification; same-family verification shares agreement bias.
- [LLM Hallucination 2026](https://futureagi.com/blog/understanding-llm-hallucination-2025/) (FutureAGI, 2026) — "gate the response on the judge." Contributed: the framing that hallucination is a metric/gate problem, not a model problem; runtime judges as the structural fix.
- [Process Advantage Verifiers](https://openreview.net/forum?id=A6Y7AqlzLW) (Setlur et al., 2025) — process > outcome verification. Contributed: validates scope-matching (per-item) as the right approach for layer 1.
- [SagaLLM](https://www.researchgate.net/publication/389855859) (2025) — echo effects without external checks. Contributed: the multi-agent reinforcement-of-shared-errors pattern.
- [Self-Correcting Agents Are Not What You Think](https://medium.com/@Micheal-Lanham/self-correcting-agents-are-not-what-you-think-they-are-d19398186373) (Medium, 2026) — three new failure modes. Contributed: "hallucinated verification" — the verifier itself can be wrong.
- [Towards Long-Horizon Agents: A Survey](https://www.preprints.org/frontend/manuscript/1c2bdfc61b6dd77da822024ed82315ef/download_pub) (2026) — external acceptance tests needed. Contributed: the survey-level confirmation that self-checking alone is insufficient across the field.
