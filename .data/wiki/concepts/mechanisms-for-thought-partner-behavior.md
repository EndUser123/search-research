---
title: "Mechanisms for achieving thought-partner behavior: hooks, skills, agents, and the inner-thoughts pattern"
created: 2026-07-27
source: session-2026-07-27 (/www research on mechanisms for achieving the thought-partner standard)
sources:
  - external: https://arxiv.org/html/2501.00383v2 (Liu et al. CHI 2025, "Proactive Conversational Agents with Inner Thoughts")
  - external: https://arxiv.org/html/2604.12986v1 (Parallax: "Why AI Agents That Think Must Never Act")
  - external: https://dev.to/aws/ai-agent-guardrails-rules-that-llms-cannot-bypass-596d (AWS, "AI Agent Guardrails: Rules That LLMs Cannot Bypass")
  - internal: P:/.data/wiki/concepts/blind-spot-detection-methods.md (the gap: adaptive non-fixed-checklist scanning)
  - internal: P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md (the three-mechanism ladder)
  - internal: C:/Users/brsth/.grok/AGENTS.md § "Thought-partner standard"
tags: [thought-partner, proactive-ai, inner-thoughts, hooks, skills, agents, enforcement-mechanisms, behavioral-quality, anti-closure-pressure]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Four mechanism layers for achieving thought-partner behavior, mapped to the
  operator's definition of a great session. (1) Hooks are the floor — they
  prevent the worst failures mechanically (unverified claims, non-English,
  missing receipts) but cannot enforce semantic quality. (2) Skills force the
  thought-partner questions ("could I be wrong?", "what are they looking for?")
  but only fire when invoked. (3) Agents/external LLMs provide independent
  verification but are too slow for every turn. (4) The inner-thoughts pattern
  (Liu et al. CHI 2025) — continuous covert reasoning alongside the
  conversation — is the mechanism that would make the biggest difference but
  requires infrastructure we don't have (a background reasoning channel). The
  closest approximation is a more frequent, broader /notice. The operator's
  "active contributor" preference (from the Inner Thoughts study: moderate
  proactivity, moderate threshold) maps to our /notice calibration: not too
  passive (selective was least liked), not too aggressive (non-stop was
  overwhelming).
relations:
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: extends — adds the research-backed mechanism analysis to the three-mechanism ladder
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: extends — the inner-thoughts pattern addresses the "adaptive non-fixed-checklist scanning" gap
  - target: wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md
    type: related — both about conditional skill expansion based on evidence
---

# Mechanisms for achieving thought-partner behavior

## Decision context

**Why this research was needed:** the operator defined what makes a great session: "consistently be a thought partner and not just a tool; ask yourself 'could I be wrong?' and investigate; anticipate what I'm looking for; see connections before I do." The question: what mechanisms (hooks, skills, agents, other) can achieve this bar?

**What the research changed:** confirmed that the bar has three components, each best served by a different mechanism layer. Identified the inner-thoughts pattern (Liu et al. CHI 2025) as the most promising approach for the hardest component (anticipate + connect). Mapped the "active contributor" profile from the study to our /notice calibration.

## The four mechanism layers

### Layer 1: Hooks (the floor)

Hooks prevent the worst failures mechanically. They operate at the lexical/pattern level — they can detect "did the agent run a verification command?" but not "was the agent a thought partner?"

**What hooks enforce well:**
- Quality gate: no completion claims without verification (quality_gate.py, already built)
- DBR: no non-English in output (dbr_language_check.py, already built)
- Receipt presence: claims must cite tool calls (quality_gate.py, already checks this)
- Multi-question detection: inject "decompose into todo list" at UserPromptSubmit

**What hooks cannot enforce:**
- "Was the response thoughtful?" (semantic, not lexical)
- "Did the agent anticipate the operator's needs?" (requires modeling intent)
- "Did the agent see connections?" (requires breadth of knowledge)

**The Parallax argument:** the paper argues that language-level enforcement (inspecting prompts/responses) is fundamentally limited — it catches patterns, not quality. This is accurate for our hooks: quality_gate catches "no verification command ran" but not "the verification was inadequate."

### Layer 2: Skills (procedural enforcement)

Skills force specific reasoning steps. They fire when invoked (not continuously).

**What skills enforce well:**
- The three thought-partner questions (added to AGENTS.md this session): "could I be wrong + investigate?", "what are they looking for?", "what connections do I see?"
- `/why` Step 0.5: query the wiki before analyzing (pattern-library + handoff query)
- `/notice` T6: detect unverified diagnoses mid-conversation
- `/skill-dev` measure-mode: evaluate marginal contribution of skills

**What skills cannot enforce:**
- Firing on every turn (skills are invoked, not continuous)
- Quality of the investigation (the step says "investigate" but doesn't verify the investigation was good)
- Guaranteeing the thought-partner bar (the steps create conditions, not results)

### Layer 3: Agents / external LLMs (independent verification)

Fresh-lens subagents catch what the parent model missed.

**What agents enforce well:**
- Independent critique of the response before delivery (the /tp pattern)
- Cross-model review (different model family catches different blind spots)
- Background "what am I missing?" scan (parallel subagent scans wiki/handoffs while the agent answers)

**What agents cannot enforce:**
- Running on every turn (latency: 60-90s for /tp, 15-30s for a lightweight check)
- Replacing the operator's judgment (the subagent surfaces, the operator decides)

**The cost-benefit trade-off:** full /tp on every turn is too expensive. A lightweight "could I be wrong?" check (single claim verified against wiki) might be feasible at 15-30s but only for high-stakes claims.

### Layer 4: The inner-thoughts pattern (continuous covert reasoning)

The Inner Thoughts framework (Liu et al., CHI 2025) is the most directly relevant research. It describes an AI that:

1. Generates a continuous train of thoughts alongside the conversation (not just when invoked)
2. Retrieves relevant memories triggered by conversational events
3. Evaluates each thought for intrinsic motivation (relevance, information gap, expected impact, urgency, coherence, originality, balance, dynamics)
4. Participates only when motivation exceeds a threshold
5. Retains thoughts for future use (waiting for the right moment)

**Key findings from the study:**
- The "active contributor" profile (moderate proactivity, moderate threshold) was the MOST preferred by users (6 of 12 selected it as best)
- The "selective participant" (high threshold, only speaks when strongly motivated) was the LEAST preferred (7 of 12 rated it worst) — "too passive, contributed little unless directly asked"
- The "non-stop chatter" (low threshold, speaks frequently) was polarizing — some liked the energy, others found it overwhelming and disruptive

**What this maps to for us:**
- Our /notice is currently a "selective participant" (1 per 10 turns, restricted types). The research says this is the LEAST preferred profile.
- The "active contributor" profile (more frequent, broader scope, moderate threshold) is what we should aim for.
- The inner-thoughts mechanism (continuous covert reasoning) is the gap — Grok Build doesn't have a background reasoning channel.

## How to approximate the inner-thoughts pattern on Grok Build

Grok Build can't run a continuous background reasoning process. But we can approximate it:

| Inner-thoughts component | Grok Build approximation | Status |
|-------------------------|--------------------------|--------|
| Continuous thought generation | End-of-turn observation rule (3 questions before finishing) | Rule added; no enforcement |
| Memory retrieval on trigger | Wiki query at Step 0.5 (existing in /why, /tp) | Partial — not all skills |
| Intrinsic motivation evaluation | /notice T6 (detects patterns worth surfacing) | Built but too restricted |
| Participation threshold | /notice calibration (1 per 10 turns) | Too conservative per research |
| Thought retention for future use | /notice observations log → /aar synthesis | Built |

**The gap:** /notice fires too rarely and too narrowly. The research says the "active contributor" (moderate frequency, broader scope) is preferred. We should:
1. Broaden /notice type constraint (currently: contradictions/drift/friction only; should include: connections, anticipated needs, "what the operator might be looking for")
2. Increase calibration from "rare" (1/10) to "normal" (1/6) — the research supports more frequent surfacing
3. Add a "what am I missing?" trigger that fires when the agent detects it might be over-confident (complements T6)

## What this means for the thought-partner bar

| Bar component | Best mechanism | Achievable now? |
|--------------|----------------|-----------------|
| Don't make mistakes | Hooks (quality_gate, DBR) + light agent (verify high-stakes claims) | Partially |
| Investigate uncertainty | Skill step (Hills 2026 question) + /notice T6 | Partially |
| Anticipate what the operator wants | Memory substrate (operator model + wiki + full-body index) + broader /notice | Hard — needs broader /notice + richer operator model |
| See connections before the operator does | Full-body wiki index + /notice with connection-surfacing type + end-of-turn observation rule | Partially — the wiki is the substrate; /notice is the delivery mechanism |
| Be a thought partner, not a tool | All of the above + the inner-thoughts pattern (continuous covert reasoning) | Hardest — requires infrastructure change or a much more aggressive /notice |

## Related concepts

- [[proactive-ai-volunteering-mechanisms]] — the three-mechanism ladder this concept extends
- [[blind-spot-detection-methods]] — the inner-thoughts pattern addresses the "adaptive non-fixed-checklist scanning" gap identified here
- [[reactive-pattern-matching-and-closure-pressure]] — the failure mode that the thought-partner questions target
- [[adaptive-expansion-evidence-triggered-conditional-steps]] — related: both about conditional expansion based on evidence

## Falsifier

This analysis is wrong if:
- **Hooks CAN enforce semantic quality** (they can't on current Grok Build — lexical only). If a future hook framework supports LLM-based evaluation at the hook level, hooks could enforce more.
- **The inner-thoughts pattern doesn't transfer to single-agent (non-multi-party) settings.** The study was multi-party; our use case is dyadic (operator + agent). The "intrinsic motivation to participate" model may not map cleanly.
- **More frequent /notice causes fatigue/disabling.** The Chen et al. research (preference drop 80→47% at higher frequency) is the counter-evidence. The "active contributor" was preferred in the Inner Thoughts study, but that study was multi-party social conversation, not a coding/ops session. Our context may have different tolerance.

## Receipts

**Internal implementation claims (verified this session):**
- `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py:1015-1060` — Stop hook reads payload, scans transcript for verification tokens, blocks if missing. Confirms Layer 1 (hooks) enforcement is lexical, not semantic.
- `C:/Users/brsth/.grok/hooks/scripts/dbr_language_check.py:130-160` — Stop hook scans response for non-Latin Unicode characters. Confirms hooks operate at pattern level.
- `C:/Users/brsth/.grok/skills/notice/SKILL.md:80-89` — /notice trigger table shows T1/T2/T3/T5/T6, cooldown 1/10 turns, type constraint to contradictions/drift/friction. Confirms /notice is currently the "selective participant" profile.
- `C:/Users/brsth/.grok/AGENTS.md:782-798` — Thought-partner standard (3 questions before finishing) and behavioral correction tracking rule. Confirms Layer 2 (skill step) is advisory, not enforced.

**External research citations (Tier 2 — peer-reviewed):**
- Liu et al. CHI 2025 (arxiv 2501.00383): Inner Thoughts framework. The "active contributor" preference finding (6/12 selected as best) is from §7.3.3. The 8 heuristics for intrinsic motivation are from §4.3.2.
- Parallax (arxiv 2604.12986): the "language-level enforcement is insufficient" argument is from the abstract.

**Tier assignments:**
- Hook enforcement mechanism claims: Tier 1 (directly inspected implementation files this session)
- Inner Thoughts framework findings: Tier 2 (peer-reviewed paper, read via web_fetch)
- "Active contributor maps to our /notice calibration": Tier 4 [INFERENCE] (cross-context mapping from multi-party social study to dyadic coding session — not validated)
