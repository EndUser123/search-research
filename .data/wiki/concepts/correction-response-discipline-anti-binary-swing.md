---
title: "Correction-response discipline: resist binary swing when corrected"
created: 2026-08-04
updated: 2026-08-04
tags: [behavioral-rule, correction, over-correction, capitulation, hook-response, epistemic-labeling, binary-swing, disposition-matrix, CRITIC, external-evidence]
host: both
agent: grok
verification: researched-validated-2026-08-04
cognitive_load: 2
summary: >
  When a hook, operator, or reviewer corrects output, the failure mode is
  binary swing — capitulate (walk back everything) or entrench (defend
  everything). The correct response is to classify the correction type, then
  choose from a 5-outcome disposition matrix (relabel / revise / withdraw /
  stop / ask) — NOT default to "keep everything." Relabeling requires external
  evidence (CRITIC principle, Gou et al. ICLR 2024). Validated by /tp critique
  (2/2 lenses REVISE) and /www research (CRITIC, Med-Stress, Silicon Mirror,
  SAGE-Agent).
---

# Correction-response discipline (anti-binary-swing)

## The pattern

When a correction fires — from a hook, the operator, a reviewer, or a
subagent — the model has three response modes:

| Mode | What happens | When it's wrong |
|------|-------------|----------------|
| **Capitulation** | Walk back the entire action, drop all related suggestions, question whether the action was needed at all | When the correction was narrow but the walk-back was broad |
| **Entrenchment** | Defend the original output unchanged, perform decomposition to justify keeping everything | When the correction had a valid kernel that needs fixing |
| **Decompose + relabel** (correct) | Identify the narrow valid kernel, separate it from the scope the correction claims to invalidate, keep the proactive layer with fixed epistemic status | — |

The failure mode is **binary swing**: treating a correction as all-or-nothing.
The model either yields entirely or defends entirely. The third path — partial
yield with precise scoping — is the one that preserves both correctness and the
proactive layer.

## Decomposition protocol

**Step 1 — Identify the narrow valid kernel.** Most corrections are partially
right. Identify the specific claim or action that is legitimately challenged.

**Step 2 — Separate the kernel from the overreach.** Does the correction imply
you should drop the entire action, or just fix one aspect?

**Step 3 — Choose a disposition from the matrix (not a single default):**

| Correction type | What it means | Correct response |
|-----------------|---------------|------------------|
| **Evidence/status** (grounding unconfirmed) | The idea may be valuable but the evidence basis wasn't verified | Relabel: `Maybe:` + confidence level + `[INFERENCE]`. Keep the suggestion. |
| **Factual error** (claim is wrong) | The specific claim is incorrect | Revise: fix the claim, keep the surrounding analysis if it holds. |
| **Relevance/scope** (wrong context) | The suggestion doesn't apply to this workspace/task | Withdraw: drop it, state why. |
| **Safety/authority** (violates invariant) | The suggestion contradicts a workspace rule | Stop immediately. Do not relabel — withdraw. |
| **Operator preference** (operator says drop it) | The operator doesn't want this | Withdraw. Do not decompose when the operator explicitly says drop. |

**External evidence required for relabeling (CRITIC principle):** a relabel
from confident → `Maybe:` must cite an external receipt (hook citation, test
failure, operator quote, file:line). A relabel without a receipt is intrinsic
self-correction, which the literature shows *degrades* reasoning (Gou et al.,
ICLR 2024 — "Self-Correction Requires External Tool Feedback"). Do not relabel
from internal reasoning alone.

**Differentiate correction sources:**
- **Hook corrections** fire on pattern matches (high false-positive rate on keyword presence). Treat as signal, not authority. Verify the hook's claim before acting.
- **Operator corrections** are intent-based (high signal-to-noise). When the operator says drop, drop — do not decompose.
- **Reviewer/subagent corrections** are evidence-based but may share framing. Verify against session evidence before adopting.
   - Don't defend it unchanged (the evidence basis was genuinely unconfirmed)
   - Relabel it: `Maybe:` + confidence level, or `[INFERENCE]` with stated
     uncertainty, and keep it

## When NOT to decompose

**False-positive hook fires.** When a hook triggers on keyword presence rather
than detecting an actual recommendation (e.g., the word "over-engineering"
appearing in a description of what ponytail-audit does, not in a recommendation
to over-engineer), there is no correction to decompose. State the false
positive clearly ("the hook is pattern-matching on the keyword, not the
semantics") and move on. Performing the decomposition ritual when there's no
actual recommendation is theater.

**Operator explicitly confirms the original output.** If the operator says
"that was a good idea" after a hook fires, the hook was a false positive from
the operator's perspective — BUT note that operator approval validates
*usefulness*, not *grounding*. The hook may still be correct that the evidence
basis was unconfirmed. These are orthogonal dimensions. Do not conclude "hook
was wrong" from "operator liked the idea" alone.

## Relationship to existing rules

- **`Maybe:` mechanism (AGENTS.md § mechanism 3):** surfaces uncertain signals
  proactively. This rule extends it to *retroactive* use — when a correction
  fires on something you already stated, downgrade to `Maybe:` rather than
  deleting.
- **Evidence-first default (AGENTS.md):** provides provisional conclusions
  before asking. This rule governs what happens *after* you've already provided
  conclusions and they're challenged.
- **Behavioral correction tracking (Layer 2):** measures correction patterns
  across sessions. This rule governs the in-the-moment response to a single
  correction.
- **`receiving-code-review` skill (superpowers):** "technical rigor, not
  performative agreement or blind implementation." Closest in spirit, but
  scoped to code review feedback. This rule generalizes to all correction
  sources.
- **`[[theatrical-contrition-and-over-apologetic-response-patterns]]`:** the
  sycophancy/apology pole of the same RLHF-learned pattern. This rule addresses
  the correction-response pole.
- **`[[evidence-first-default-and-needless-confirmation]]`:** the
  empowerment-over-prohibition principle that underlies this rule's disposition
  matrix.
- **`[[false-choices-parallel-branch-framing]]`:** a sibling pattern — both
  address decision deferral under pressure, with the same ~50% prose-rule ceiling.

## Falsifier

This rule has become theater if the model performs the decomposition ritual ≥3
times in one session on unambiguous corrections where the correct response is
simple withdrawal. Track: if every decomposition concludes "I was basically
right, just relabel," the rule is entrenchment with extra steps. If the model
cannot name a case where withdrawal was the correct disposition in the last 5
corrections received, the matrix isn't being used — only the relabel row.

## Prose-rule-decay acknowledgment

This rule IS a prose rule for a response pattern — the exact category
documented as "What does NOT work" in `[[theatrical-contrition-and-over-
apologetic-response-patterns]]` (line 131: "Prose rule in AGENTS.md ('don't
apologize') — Self-critique shares producer bias; rules decay under closure
pressure"). The structural fix would be an EGDP-style template enforced at the
system-prompt level. Until that structural fix is built, this rule is a
workaround that will decay under pressure (~50% compliance ceiling per
`[[evidence-first-default-and-needless-confirmation]]`).

## Research validation (2026-08-04 /www)

External research confirms the pattern is real and RLHF-rooted. Key findings:

| Source | What it found | Relevance |
|--------|--------------|-----------|
| **CRITIC** (Gou et al., ICLR 2024) | Intrinsic self-correction degrades reasoning; external tool feedback required | Relabeling must cite external evidence — a receiptless relabel makes things worse |
| **Med-Stress** (Xiao et al., ACL 2026) | "Knowledge-robustness gap" — models abandon correct answers under pressure | The capitulation failure mode is documented across 9 frontier LLMs |
| **Silicon Mirror** (Shah, Apr 2026) | Dynamic anti-sycophancy gating: 85.7% reduction (9.6% → 1.4%) | The only system with a per-turn measurable metric for this pattern |
| **SAGE-Agent** (Suri et al., Nov 2025) | EVPI-based decision protocol: 1.5-2.7× fewer unnecessary questions | A Correction Value of Information gate could separate high-value from low-value corrections |
| **obra/superpowers** receiving-code-review | 6-step protocol with source-differentiation (human vs external reviewer) | The source-differentiation principle is directly portable |
| **TACL 2024** self-correction survey | Intrinsic self-correction fails without oracle labels | Confirms CRITIC: model-driven capitulation is statistically worse than no correction |

**Field gap:** no production AI agent framework has a published correction-
decomposition protocol. The workspace's rule is ahead of the field — but the
structural enforcement (EGDP template or output validator) is what would make
it durable.

## What this means for our workspace

1. The AGENTS.md rule now has a 5-outcome disposition matrix instead of a single
   "keep proactive layer" default — this prevents retention bias.
2. The CRITIC principle (external evidence required for relabeling) is the
   structural insight that turns the prose rule into something enforceable: "you
   may relabel only with a cited external receipt."
3. The ~50% compliance ceiling means this rule will not fire every time. The
   durable backstop is an output validator hook (see handoff
   `false-choice-validator-hook-20260804`).

## Reference failure (2026-08-04)

**Setup:** operator asked what skills exist like `improve-codebase-architecture`.
The model provided a thorough inventory, then volunteered three forward-looking
recommendations (use the mattpocock trio, port ponytail-audit, flag gaps).

**Hook fire:** MINIMAL_BIAS_GATE correctly flagged "port ponytail-audit" as an
ungrounded recommendation — plausible reasoning, not confirmed workspace need.

**Over-correction:** the model dropped ALL suggestions entirely, questioned
whether the operator needed any of them, and framed the entire proactive layer
as inappropriate.

**Operator pushback:** "I thought the suggestions were a good idea, how you
volunteered them. That was very thoughtner-ish."

**Correct response would have been:** acknowledge the hook's kernel (the
evidence basis was unconfirmed), keep the suggestion, relabel as:

> Maybe: ponytail-audit is the inverse lens (find over-engineering to remove,
> not shallow modules to deepen) and doesn't exist on the Grok side.
> Confidence: LOW — no evidence of a confirmed gap. A concrete pain point
> would confirm whether it's worth porting.

**Lesson:** the fix was the label, not the silence.

## Receipts

- AGENTS.md rule: `C:/Users/brsth/.grok/AGENTS.md` lines 1050-1110 (correctation-response discipline section, revised 2026-08-04)
- /tp critique: session 019fcb54, critique log ID `90b2c79d8ee6` — 2/2 lenses REVISE
- /www research: session 019fcb54, subagent `019fcd06-2b8c` — 10 findings across 6 research streams
- CRITIC paper: https://arxiv.org/abs/2305.11738 (Gou et al., ICLR 2024)
- Med-Stress paper: https://arxiv.org/abs/2605.23932 (Xiao et al., ACL 2026)
- Silicon Mirror: https://arxiv.org/abs/2604.00478 (Shah, Apr 2026)

## Auto-related

- [[recurring-thinking-errors]]
- [[operator-correction-as-highest-density-signal]]
- [[scope-matching-verification-discipline]]
- [[theatrical-contrition-and-over-apologetic-response-patterns]]
- [[cdp-network-interception-and-sse-capture-for-llm-chat]]

