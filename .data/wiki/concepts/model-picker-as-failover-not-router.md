---
title: "Model picker as failover, not router"
created: 2026-07-21
source: session-2026-07-21
tags: [architecture, routing, failover, model-selection, fleet, grok-build, ccr]
summary: >
  When deciding where the failover decision gets made for LLM calls, the
  Grok model picker (interactive, intelligent per-failure) and CCR (automatic,
  client-agnostic) solve different problems. The picker is the right default
  for interactive hybrid use because it has no single point of failure
  between the user and the model, and the routing decision can be intelligent
  per-failure rather than rule-based. CCR earns its place for batch,
  cross-client, or automatic failover — not as the interactive default.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/exemption-logic-as-conflict-signal
    type: related
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/gemini-google-api-models-2026-07
    type: related
  - target: wiki/concepts/llm-council-and-model-fusion
    type: related
---

# Model picker as failover, not router

## The architectural stance

When a model call fails — timeout, 429, provider outage, unexpected empty
response — something has to decide which model to try next. Two places that
decision can live:

| Layer | Mechanism | Failure mode it handles | Failure mode it doesn't |
|---|---|---|---|
| **Router (CCR)** | Code-based rules in a proxy between client and providers | Automatic failover; works for any client; deterministic | **Cannot route around itself** — if CCR is down, everything downstream breaks |
| **Model picker (Grok native)** | Human or LLM switches model per call via `/model` or per-spawn `model=` | Works when the router itself is the problem; routing decision can be intelligent per-failure | Manual for non-subagent calls; client-specific (Grok only) |

The stance: **for interactive hybrid use, the model picker is the primary
failover mechanism.** CCR is the right tool for batch, cross-client
routing, and automatic failover at scale — but not as the default for a
solo operator working in Grok Build who wants local + cloud hybrid.

## Why the picker wins for interactive use

Three reasons grounded in the actual workflow:

1. **No single point of failure between the user and the model.** A router
   is one more thing that can be down, misconfigured, or itself the source
   of the failure. The model picker is built into the client; if the client
   is up, the picker is up.

2. **The routing decision is often stateful in ways static rules can't
   capture.** "Nemotron just timed out on this specific prompt — try
   Inkling instead because it handles this kind of reasoning better" is a
   judgment call. It depends on what just happened, what the prompt is,
   and what the alternatives are. A rule-based router can express "if
   Nemotron 5xx, fall back to GLM-5.2," but not "if Nemotron timed out on
   a reasoning task, try Inkling; if it timed out on a code task, try
   Ornith."

3. **The call volume doesn't justify the infrastructure.** Code-based
   routing earns its cost at scale (10,000s of calls/min). At interactive
   volumes (tens of calls per session), the overhead of maintaining router
   rules exceeds the value of automatic failover. A `/model` switch when
   something breaks is cheap.

## Where CCR still earns its place

The picker doesn't replace CCR. CCR wins when:

- **Cross-client routing matters.** Claude Code, Codex, and Grok all
  hitting the same provider pool want one routing layer, not three
  per-client pickers.
- **Batch work needs automatic failover.** A 100-call batch can't wait for
  a human to notice one failure and switch models.
- **Cost optimization across many calls** benefits from a central ledger
  that sees all traffic. Per-client pickers can't reason about aggregate
  spend.
- **The routing rules are genuinely static.** "Sensitive data never leaves
  local" is a rule, not a judgment call — it belongs in code, not in a
  picker that could forget.

## The decision criterion

When deciding where to put a failover decision:

> **Is the routing rule stateful and per-failure, or static and universal?**

- **Stateful / per-failure** → model picker. Examples: "this prompt just
  failed on Nemotron, try Inkling"; "this is a multimodal task, route to
  Inkling"; "NVIDIA is slow today, route to local Ornith."
- **Static / universal** → router (CCR). Examples: "PII never leaves
  local"; "spend cap per workflow"; "round-robin across providers for
  load balancing."

## Worked example (2026-07-21 session)

Operator goal: use local Ornith + NVIDIA DiffusionGemma as much as
practical, failover when they don't work. The model proposed extending
`ccr-custom-router.js` with failover rules. Operator pushed back:
prefers Grok's model picker because if there's a failure, they can
dynamically pick a different model and use it without needing CCR.

The operator's stance wins because:
- The failures being guarded against include "CCR is the problem."
- The number of calls per session is small.
- The routing decision depends on what just failed and why — a judgment
  call, not a rule.

## What this means for skill design

Skills should *recommend* models per task type, not *route* them through
a central proxy. Specifically:

- **`/go` spawn recipes** should recommend a **model lane**, not invent a
  router (Grok Build ≥ v0.2.98 `model` on `spawn_subagent`). Authority:
  `~/.grok/skills/go/SKILL.md` § Spawn recipe — quality–latency Pareto
  with quality floor; two lanes (Reasoning vs Code/else); free local +
  NVIDIA first when they clear the floor; subscription escalate after.
  Multimodal is a capability filter. Fusion/MoA panel+judge is optional
  async verification only. Orchestrator honors lane picks; transport
  failure goes to the picker, not a second automatic router.
- **Do not** build a parallel router inside the skill. The skill's job is
  to express preferences; the picker's job is to handle failure.
- **CCR stays** for the cases above (cross-client, batch, static rules).
  It is not the interactive default.

## Anti-pattern: router-as-default

Treating CCR (or any router) as the default failover for interactive work
is an anti-pattern when:

- The operator is solo and present — they can make the per-failure call
  themselves.
- The router is the only path between client and providers — its failure
  takes everything down.
- The routing decisions are genuinely judgment calls that don't
  generalize into rules.

The structural fix: push the routing decision to the layer closest to
the failure (the interactive picker), and reserve the router for the
cases where its specific advantages (cross-client, automatic, aggregate
visibility) actually apply.

## Falsifier

If, in practice, the operator finds themselves repeatedly making the same
per-failure routing decisions ("Ornith timed out again, switch to
DiffusionGemma"), the decision has become static and belongs in a rule.
At that point, promote it to CCR. The picker is the right default *until
the pattern repeats enough to encode* — not forever.

## Related

- `P:/.claude/provider-configs/ccr-custom-router.js` — the existing CCR router
- `~/.grok/config.toml` `[model.*]` entries — the picker's model catalog
- Grok Build v0.2.98 changelog (2026-07-12) — `spawn_subagent` accepts `model` parameter
- [[exemption-logic-as-conflict-signal]] — adjacent pattern: don't gate what the layer above gates. The picker is "the layer above" relative to CCR for interactive routing.

## Auto-related

- [[exemption-logic-as-conflict-signal]]
- [[solo_operator_adr_best_practices]]
- [[operator-collaboration-style-and-leverage]]

## Sources

- Session 2026-07-21 — operator stance on picker vs CCR for interactive hybrid use
- Grok Build changelog v0.2.98 (2026-07-12) — `model` parameter on `spawn_subagent`
- SitePoint "Hybrid Cloud-Local LLM Architecture Guide" (2026-04-22) — three-pillar routing pattern; corroborates the router-vs-picker distinction for different workload shapes
