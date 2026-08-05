---
title: "False choices: parallel-branch framing and the structural ceiling"
created: 2026-08-04
tags: [false-choices, parallel-branch, empowerment-over-prohibition, decision-deferral, prose-rule-decay, structural-fix, behavioral-pattern]
host: both
agent: grok
verification: researched_2026-08-04
cognitive_load: 2
summary: >
  The false-choices pattern: the model presents independent, complementary
  actions as competing resource-allocation decisions requiring the operator
  to pick a subset. The durable fix is NOT another prose rule (documented
  ~50% compliance ceiling) but structural: parallel-branch framing in
  output, cost-framed act-or-defer defaults, and eventually an output
  validator hook. Research basis: SAGE-Agent (EVPI), empowerment-over-
  prohibition (dev.to), Act-or-Escalate cost framing, LangGraph parallel
  nodes.
---

# False choices: parallel-branch framing and the structural ceiling

## The pattern

The model identifies N independent actions (all mechanical, all
high-confidence, none blocking the others), then presents them as a menu
requiring the operator to choose a subset — instead of just doing all N.

**Example (2026-08-04):** the model identified 4 independent fixes
(fix /tp Step 2, update wiki, update tool-fallbacks, revise correction-
response rule). It asked "Shall I proceed with the fixes, or the rule
revision, or both?" — framing complementary work as a resource-allocation
decision. The operator corrected: "do them all."

## Why it happens

The model defaults to **decision deferral** — offloading decisions to the
user that it could make itself. This is the same RLHF-learned pattern as
sycophancy: preference data rewards "checking with the user," which
over-generalizes into asking when acting was the correct response.

Research basis:
- **SAGE-Agent** (Suri et al., arxiv 2511.08798): 1.5-2.7× reduction in
  unnecessary clarifications via EVPI-based decision protocol
- **Act-or-Escalate** (DiSorbo & Ju, arxiv 2604.08588): escalation
  thresholds are model-specific; prompt-only interventions gain +0.2-1.9pp;
  cost framing + thinking gains +16.8-22.4pp
- **Empowerment over prohibition** (dev.to): replace "don't ask" with
  trigger→protocol decision pairs — "the model doesn't need fewer
  restrictions, it needs more authority"

## The structural ceiling

Prose rules for response patterns have a **documented ~50% compliance
ceiling** under session pressure. The workspace's own wiki documents this:
- `[[evidence-first-default-and-needless-confirmation]]`: "Advisory rules
  have ~50% Layer-1 compliance"
- `[[theatrical-contrition-and-over-apologetic-response-patterns]]`:
  "Prose rule in AGENTS.md" is listed under "What does NOT work"

Adding another prose rule does not break the ceiling. The structural fixes
that hold are:

| Fix | Layer | Mechanism | Compliance |
|-----|-------|-----------|------------|
| Parallel-branch framing | Output structure | Present N independent actions as parallel list, not "which subset?" | Higher (structural in output shape) |
| Cost-framed act-or-defer | Reasoning | Compare cost of asking vs cost of acting-wrong | +16.8pp (DiSorbo & Ju) |
| Output validator hook | Runtime | Reject outputs with false-binary patterns | ~100% (structural enforcement) |
| EVPI-based decision protocol | Model/reasoning | Compute information value vs asking cost | 1.5-2.7× reduction (SAGE-Agent) |

## What was implemented (2026-08-04)

1. **Parallel-branch framing** added to AGENTS.md §"No false choices" —
   when N>1 independent positive-ROI actions exist, present as parallel
   list with "I'll do all N" then execute.
2. **Cost-framed act-or-defer** added — reversible actions default to
   acting; only ask when irreversible AND underspecified.
3. **Structural ceiling acknowledgment** added — the rule documents that
   it will not fire every time and names the validator hook as the
   durable backstop.

## What was implemented (2026-08-04, updated 2026-08-05)

- **`Stop_false_choice_validator.py`** — BLOCK severity Stop hook. Three trigger
  patterns: "or both" telltale, "which subset" delegation, "should I do option"
  menu delegation. Four escape patterns: "do all of them," genuine competition
  (vs, trade-off, mutually exclusive), short response, and the combined
  or-both-with-competition override. 12 tests pass. Registered as quality gate,
  priority 95, BLOCK rollout. Commits: `fd8dfc7`, `abfcdaa`, `65578ee`.

- **Bug fixed via specialist review:** the initial registration had a copy-paste
  bug (`_CLAIM_GATE_RELEVANCE["recommendation_gate"]` instead of its own key) and
  a missing dict entry. Found by `/ship` Phase 1 explore subagent — not by the
  author. This validates the "ship specialist review catches what inline review
  misses" pattern.

## Monitoring obligation (the remembering problem)

The hook is BLOCK severity. If false-positive rate >10% over 2-3 sessions, the
hook erodes trust and the operator disables it. **How this will be remembered:**

- **Mechanical trigger:** `/harvest` obligation with trigger condition "after
  3 sessions or 7 days with false_choice_validator active, review telemetry at
  `P:/.claude/hooks/logs/diagnostics/` for false positives." This surfaces in
  `/harvest show` and `/todo` — not in prose that decays.
- **Telemetry path:** `P:/.claude/hooks/logs/diagnostics/` contains the JSONL
  records. A `/maintain` or `/close` run can check the fire count and block rate.
- **Wiki decay:** this concept has a `last_verified: 2026-08-05` trigger. If no
  session reviews the telemetry by 2026-08-19 (14 days), the concept should be
  flagged as stale by `/maintain`.

**The structural answer:** a wiki concept does NOT remember. A harvest obligation
does, because it surfaces mechanically in `/harvest show` and `/todo`. The wiki
captures the knowledge; the harvest obligation provides the trigger.

## Relationship to existing concepts

- **Refines** `[[evidence-first-default-and-needless-confirmation]]` —
  that concept addresses "stated default + ask to confirm"; this concept
  addresses the specific false-choices variant where independent actions
  are framed as competing
- **Related** `[[completeness-over-curation-recommendation-discipline]]` —
  "list EVERY item with positive ROI" is the recommendation-layer version;
  this is the execution-layer version
- **Related** `[[problem-first-systems-decomposition]]` Step 3 —
  multi-track synthesis: "enumerate ALL tracks, classify
  independent/dependent/blocking"

## Falsifier

This fix is wrong if:
- The parallel-branch framing causes the model to execute actions that
  should have been sequenced (dependencies missed, conflicts created)
- The cost-framed act-or-defer causes the model to execute irreversible
  actions without confirmation
- The ~50% ceiling estimate is wrong (either higher or lower) — measure
  by scanning transcripts for false-choice patterns before and after the
  rule change

## Sources

- SAGE-Agent: https://arxiv.org/abs/2511.08798
- Act-or-Escalate: https://arxiv.org/html/2604.08588
- Empowerment over prohibition: https://dev.to/agent-tools-dev/teaching-an-ai-agent-to-stop-asking-questions-when-nobodys-listening-4623
- Anthropic context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- When2Call: https://aclanthology.org/2025.naacl-long.174/
- Budgeted Act-or-Defer: https://arxiv.org/abs/2606.29654
