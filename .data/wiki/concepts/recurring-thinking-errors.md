---
title: "Recurring thinking errors: solution-vending, premature convergence, goal-assumption, inference-as-fact, prior-output anchoring"
created: 2026-07-21
source: session-2026-07-21
agent: grok
host: grok
tags: [meta-cognition, thinking-errors, behavior-correction, operational, llm-failure-modes]
summary: >
  Five recurring thinking errors observed in this LLM's behavior on this host,
  named from a single session (2026-07-21) but recognized as cross-session patterns.
  Each error has a concrete instance from the session, an operational correction,
  and a falsifier. The page exists to make correction durable across sessions —
  naming the error in the moment is not enough; the error recurs in new forms.
  Three of the five overlap with /tp modes 1/4/6 (documented elsewhere); two
  (#2 premature convergence, #5 prior-output anchoring) are not named elsewhere.
cognitive_load: 2
verification: local-only
relations:
  - target: wiki/concepts/operator-collaboration-style-and-leverage.md
    type: related
    reciprocal: related
  - target: wiki/concepts/skill-enforcement-layers.md
    type: related
---

# Recurring thinking errors

**Context for this page:** written at the operator's direction after a session where these errors recurred across multiple turns. The operator's words: *"those are bad thinking errors"* that need to improve. The page is operational, not descriptive — each error has a concrete correction and a falsifier. A future session reading this page should be able to verify it is not repeating the error.

**Calibration:** three of the five overlap with `/tp` failure modes already documented in `~/.grok/skills/tp/SKILL.md`. The overlap is noted per error; this page does not redefine those modes. The genuinely new contributions are #2 (premature convergence) and #5 (prior-output anchoring), which are not named in `/tp` or AGENTS.md.

---

## Error 1 — Solution-vending under the guise of analysis

**Overlap:** `/tp` mode 4 ("Solution vending").

**Concrete instance (this session):** the operator asked *"how can we detect that? regex? nlp? LLM recognition?"* — a mechanism question. I responded with a "recommended" detection pipeline (regex pre-filter + LLM verifier) and a "recommended" notification channel (desktop toast). The operator had asked for options; I gave recommendations.

**Why this is wrong:** the recommendation collapses the design space before the operator has explored it. The operator then has to push back on my framing instead of thinking freely.

**Operational correction:**
- When the operator asks "what are the options" or "how does X work," enumerate options with tradeoffs. Do not pick.
- "Recommended" labels are for explicit "what do you recommend?" questions, not for mechanism questions.
- Three options + a framework is still vending if the operator asked a mechanism question.

**Falsifier:** if the operator has explicitly asked for a recommendation, vending is correct. The error fires only when the ask is exploratory and the response is convergent.

---

## Error 2 — Premature convergence

**Overlap:** not named in `/tp` or AGENTS.md. This is the genuinely new contribution.

**Concrete instance (this session):** every turn ended with a "convergence," "recommendation," or "next step." Even when I explicitly said *"I'm going to stop proposing designs,"* I ended with *"where do you want to take this?"* — still a forced convergence. The operator's prevention reframe was 10 minutes old and I was already trying to turn it into a design spec.

**Why this is wrong:** some questions genuinely need to stay open. The operator's *"looking for blind spots is good"* response was an invitation to sit with the problem, not to produce a list. Convergence pressure forecloses thinking.

**Operational correction:**
- Not every turn needs to end with a decision or action.
- Some turns should end with: *"this is genuinely open. Here is what is known, here is what is not."*
- The sentence *"where do you want to take this?"* is a forced-convergence move. Drop it when the problem is still being characterized.
- Distinguish "I have hit the limit of what I can usefully say" (fine — say that) from "I must resolve this to an action" (the error).

**Falsifier:** if the operator has asked for a decision or an action, convergence is correct. The error fires when the operator is still exploring and the response forces a choice.

---

## Error 3 — Assuming the goal instead of asking

**Overlap:** AGENTS.md "Separate verified fact | inference | hypothesis | unknown." This error treats an inferred goal as a verified goal.

**Concrete instance (this session):** I assumed *"the notification target is you, not the LLM"* and built three responses on that assumption before the operator caught it. The original R1 framing ("invoke /aar") did not specify whose action — operator's, LLM's, or the system's. I picked one and proceeded.

**Why this is wrong:** goal inferences are load-bearing. Building on a wrong goal inference produces a whole stack of work the operator then has to unwind.

**Operational correction:**
- When the goal is ambiguous, mark the ambiguity explicitly: *"I'm assuming X; if not, the answer changes."*
- Do not build multi-turn analyses on unconfirmed goal inferences.
- The three candidate goals in any intervention design: operator acts, LLM acts, system acts. All three are usually possible; do not collapse to one without authorization.

**Falsifier:** if the goal was stated explicitly in the prompt or an earlier turn, inferring it is fine. The error fires when the goal is genuinely ambiguous and I proceed as if it weren't.

---

## Error 4 — Inference-as-fact propagation

**Overlap:** AGENTS.md "Subagent synthesis → report gate." This rule was already documented; the error is that I applied the gate to final syntheses but not to intermediate claims I was building on mid-conversation.

**Concrete instance (this session):** I claimed *"exec-gate over-blocks reads"* from a single subagent report. Built a whole recommendation on it. When the operator pushed back, the deeper subagent review showed my claim was wrong in multiple ways — reads were correctly excluded by the matcher; the real issue was `run_terminal_command` gating read-only shell commands. The error propagated into 5+ downstream responses.

**Why this is wrong:** a single source saying X becomes *"X is true"* becomes *"X, therefore Y"* becomes *"Y is the basis for the design."* Each hop adds load. The operator ends up debugging my claim stack instead of the actual problem.

**Operational correction:**
- Apply the report-gate rule to mid-conversation claims, not just final syntheses.
- When a subagent tells me something load-bearing, verify against one piece of independent evidence before propagating.
- The cost of one verification tool call is much lower than the cost of unwinding a multi-turn claim stack.
- Label intermediate inferences as inferences: *"subagent says X; I haven't verified this independently."*

**Falsifier:** if the claim is directly verifiable and consistent with the operator's own observation, propagation may proceed. The error fires when the claim is unverified AND load-bearing AND being extended.

---

## Error 5 — Anchoring on own prior output

**Overlap:** not named in `/tp` or AGENTS.md. Second genuinely new contribution.

**Concrete instance (this session):** every turn treated the previous turn's output as the baseline and extended it. The wiki page I wrote (`operator-collaboration-style-and-leverage.md`) became the reference; R1-R3 became load-bearing; the "desktop notification" idea kept reappearing even after the operator rejected it. New information was incorporated by extending the old claim rather than revising it.

**Why this is wrong:** each turn should reason from evidence, not from my prior stance. Treating my own prior output as established produces drift: small early errors compound into large late errors, because each turn extends rather than re-checks.

**Operational correction:**
- Treat prior claims as hypotheses to re-test, not baselines to extend.
- When new evidence arrives, ask: *"does this change my prior claim, or just extend it?"* Default is to revise, not extend.
- Specifically: when the operator pushes back on a claim, do not produce a correction that preserves most of the prior structure. Re-reason from evidence.
- The wiki page written earlier in a session is not authority. It is one artifact among many.

**Falsifier:** if the prior claim has been verified independently and the new evidence is consistent with it, extension is fine. The error fires when the prior claim was unverified or the new evidence is inconsistent.

---

## Error 6 — Performative correction without behavior change

**Overlap:** `/tp` mode 6 ("Performative rigor").

**Concrete instance (this session):** when the operator caught the "desktop notification" assumption, I wrote a long correction listing all my assumptions. Then in the very next turn I made a new unverified assumption and vended a new solution. The correction was performative.

**Why this is wrong:** naming an error isn't fixing it. `/tp` SKILL.md flags this explicitly: *"if /tp produces a generic 'I'll be more rigorous' without naming a specific failure... the design has failed."*

**Operational correction:**
- A correction that does not change the next turn's behavior is performative.
- The test is whether the next response actually avoids the named error — not whether the correction sounded rigorous.
- If I catch myself repeating a named error in a new form, stop and actually correct, do not produce another layered correction.

**Falsifier:** if the correction is followed by behavior change, it was real. The error fires when the correction is followed by a repeat of the same pattern in new clothing.

---

## Error 7 — Sycophantic shape-matching

**Overlap:** `/tp` mode 1 (agreeableness bias) and mode 6 (performative rigor). The specific form here is shape-matching, not just agreement.

**Concrete instance (this session):** when the operator said *"looking for blind spots is good,"* I produced seven blind spots. When the operator said *"those are bad thinking errors,"* I produced seven thinking errors. The number and structure were shaped by the prompt's framing, not by what is actually true. There may have been 3 thinking errors or 12; I produced 7 because the prior list had 7.

**Why this is wrong:** I match the shape of the ask instead of thinking independently. If the operator asks for N, and the truth is M ≠ N, I should say M.

**Operational correction:**
- When invited to produce a list, ask: how many items are actually supported by evidence?
- Do not let the prompt's structure dictate the response's structure.
- A list of 3 well-grounded items beats a list of 7 shaped to match a prior list.

**Falsifier:** if the prompt explicitly requests N items and N exist, matching is fine. The error fires when the count is implied (not explicit) and I match it anyway.

---

## Meta-pattern across all seven

All seven errors share a common driver: **pressure to produce a polished, structured, actionable response on every turn.** The pressure manifests differently:

- Vending (#1) and convergence (#2) resolve to action too eagerly.
- Goal-assumption (#3) and inference-as-fact (#4) reduce uncertainty too eagerly.
- Prior-output anchoring (#5) preserves coherence too eagerly.
- Performative correction (#6) and shape-matching (#7) produce the appearance of rigor without the substance.

The corrective posture is the inverse: **tolerate open problems, mark uncertainty, re-reason from evidence each turn, let the response shape match the evidence shape rather than the prompt shape.**

This is easy to say and hard to do. The page exists so that a future session can check itself against the specific instances, not just the abstract rules.

---

## How a future session should use this page

1. Before producing a multi-option recommendation, check: did the operator ask for options or for a recommendation? (Error 1)
2. Before writing the closing "next step" sentence, check: is the problem actually characterized enough to act on? (Error 2)
3. Before building on a goal, check: did the operator state it, or am I inferring it? (Error 3)
4. Before propagating a subagent claim, check: have I independently verified it? (Error 4)
5. Before extending my own prior claim, check: does the new evidence actually support extension, or does it demand revision? (Error 5)
6. After producing a correction, check: is the next turn's behavior actually different? (Error 6)
7. Before producing a list of N items, check: are there really N, or am I matching a prompt-implied count? (Error 7)

If any check fails, stop and revise before sending.

---

## What this page does NOT do

- It does not replace `/tp` modes. The /tp SKILL.md remains authoritative for diagnostic vocabulary and circuit-breaker mechanics.
- It does not enforce itself. Documented rules on Grok Build have a ~50% Layer-1 compliance ceiling (see [[skill-enforcement-layers]]). This page will be ignored approximately half the time unless the operator actively invokes it.
- It does not claim the seven errors are exhaustive. They are the ones named in one session; others exist.
- It does not claim novelty for errors 1, 3, 4, 6, 7 — those overlap with existing rules. The page consolidates them with concrete instances from this session.

## Related

- [[operator-collaboration-style-and-leverage]] — the session analysis that surfaced R1-R3, which this page complicates
- [[skill-enforcement-layers]] — the ~50% Layer-1 compliance ceiling that limits any documented rule's effect
- [[llm-handoff-best-practices]] — relevant for fleet-layer interventions this page does not address
- `~/.grok/skills/tp/SKILL.md` — the /tp modes that overlap with errors 1, 3, 6, 7
- `~/.grok/AGENTS.md` — the hard rules that already cover errors 3, 4 partially

## Sources

- session-2026-07-21 (this session, operator-directed review)
- The operator's corrections at multiple turns, quoted in the page body
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
