---
type: concept
title: "LLM-to-LLM handoff best practices and anti-patterns"
created: 2026-07-20
sources:
  - https://arxiv.org/abs/2503.13657
  - https://www.mindstudio.ai/blog/context-rot-ai-agents-session-handoff-fix
  - https://www.mindstudio.ai/blog/context-rot-ai-coding-agents-how-to-prevent
  - https://dev.to/gabrielanhaia/the-5-failure-modes-of-multi-agent-systems-nobody-warns-you-about-2fml
  - https://semiherdogan.medium.com/handoff-a-better-way-to-run-autonomous-development-loops-00e97e62d470
  - https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/
tags:
  - handoff
  - multi-agent
  - context-management
  - session-continuity
summary: "External research on what makes LLM-to-LLM handoffs succeed or fail, for a solo director operating a fleet of AI coders."
host: both
---

# LLM-to-LLM handoff best practices and anti-patterns

**Context for this page:** the user is a solution architect operating solo as the director of a fleet of AI coders on Windows. Handoffs happen between sessions, between agents in one orchestration, and across compact boundaries. "Solo" describes decision authority (single approver, no committee), not system simplicity — the fleet is a real distributed system with coordination, isolation, and stale-data problems. This page consolidates external research so our `/handoff` skill is grounded in the field, not just our own incidents. Calibrate explanations to an architect audience: name patterns by their standard names (event sourcing, single-writer, CQRS, typed ownership), don't derive them from first principles.

## Sources (with credibility tier)

- **MAST taxonomy / Cemri et al. 2025** (arxiv 2503.13657, 517 citations, NeurIPS) — 14 failure modes across 3 categories from 1600+ annotated traces. Highest credibility.
- **dev.to "5 Failure Modes"** (Gabriel Anhaia, April 2026) — code-level patterns with OTel signals. Practitioner credibility.
- **MindStudio "Context Rot"** (June 2026) — accessible synthesis of "lost in the middle" research with named design patterns. Practitioner credibility.
- **MindStudio "Context Rot in Coding Agents"** (April 2026) — Claude Code-specific prevention strategies. Practitioner credibility.
- **Semih Erdogan `handoff` tool** (Feb 2026) — production CLI built around handoff discipline. Practitioner credibility.
- **Towards Data Science "How Agent Handoffs Work"** (Dec 2025) — taxonomy of handoff patterns. Practitioner credibility.

## Best practices (Do's)

### 1. Make handoffs structured, not conversational
MindStudio: "the solution is careful handoff design: structured summaries, explicit inclusion criteria, and testing that validates continuity across handoffs." Free-form prose summaries lose information; structured state objects survive.

### 2. Use the rolling-summary or phase-based pattern
- **Rolling summary** (MindStudio Pattern 1): append concise summary every N turns to a persistent memory object; on handoff, that becomes the seed.
- **Phase-based handoffs** (MindStudio Pattern 2): for work with distinct phases (gather requirements → plan → execute → verify), hand off at phase transitions. Each new session starts with structured outputs from the prior phase, not the full conversation within it.
- **Phase-based fits solo director fleet better** — your work has natural phase boundaries (investigation, plan, implement, verify).

### 3. Use a separate summarizer agent when possible
MindStudio Pattern 3: a lightweight secondary agent handles summarization. Main task agent calls it, receives structured output, passes to new session. Keeps summarization logic consistent and independently improvable. Use a cheaper model for the summary step.

### 4. Use a persistent state object for action-taking agents
MindStudio Pattern 4: maintain a structured JSON object throughout the session, updating as facts are established. On handoff, pass the object directly. "Most reliable pattern for agents that take actions, because the state object can be explicitly structured to include everything the agent needs to continue safely." This is the snapshot plugin's approach.

### 5. Be proactive, not reactive
Trigger handoffs before quality degrades, not after. "Most production agent systems combine both approaches: proactive triggers with a minimum token threshold, plus reactive detection for high-stakes workflows."

### 6. Pair handoffs with lean prompts and external memory
- Keep system prompts lean — every token in system prompt loads into every session
- Use external memory for static facts (user profiles, catalogs) — don't jam into context
- Structure context intentionally — summarize tool results rather than appending raw API responses
- Monitor token usage in production — log context size across sessions

### 7. Test with long sessions, not short ones
"Most agent testing happens in short sessions where context rot doesn't show up. Build tests that simulate realistic session lengths — 50, 100, 200 turns — and evaluate output quality at each stage. You'll find failure modes that never appear in a 5-turn demo."

### 8. Split files by purpose (Erdogan `handoff`)
Each file has one job:
- `FEATURE.md` — intent
- `SPEC.md` — what must be true
- `DESIGN.md` — how to approach it
- `DECISIONS.md` — why durable choices were made
- `STATE.md` — what is being done right now + evidence for completed steps
- `SESSION.md` — what the next session must know

### 9. Attach evidence to completed steps
Erdogan: turn the loop from `Task -> "done"` into `Task -> code -> evidence`. Record: changed files, commands/tests run, result, notes/remaining risks.

### 10. Drift audit before closing
Before calling work done, compare implementation against intent/spec/decisions. Erdogan's `handoff drift` generates a structured audit prompt — not an automatic verdict.

### 11. Use skills to contain task scope
Keep skill files under 200 lines. Point to reference documents instead of pasting them inline. "Bloated skill files load unnecessary tokens every single time the skill runs, and that overhead compounds across a session."

### 12. Use sub-agents to isolate context
Spawn focused sub-agents for context-heavy tasks (reading large codebases, analyzing errors). Main agent never sees raw scan; only sees clean output. The Scout Pattern: pre-screen large files before deciding relevance.

### 13. Use `/compact` at natural task boundaries
Not mid-task — that loses in-progress context. Best after completing a feature, resolving debugging, finishing a planning phase.

## Anti-patterns (Don'ts)

### 1. Loop-of-loops (compound retries across agents)
Each agent has its own retry policy; none know about each other. "A flaky API blips once and the planner's three retries each spawn the worker's three retries, each of which retries the LLM three times. One blip, 27 LLM calls." Fix: one retry policy per turn, enforced by a step counter that every agent increments through.

### 2. Ownership ambiguity
When the orchestrator is an LLM, "which agent owns this query" becomes a probability, not a contract. Result: two agents act on the same task, user gets two outputs, one is wrong. Fix: make ownership a typed field, updated atomically, any agent that acts without ownership raises.

### 3. Shared-state race
Two agents writing to the same memory store interleave; half the data disappears. "Nobody reproduces it locally because the timing only goes wrong under load." Fix: single-writer rule — one agent owns each region of state; others get read-only views.

### 4. Infinite handoff ping-pong
Agent A hands to B; B hands back; loop until something kills it. "Neither agent is wrong inside its own turn; the loop is in the topology." Fix: handoff counter, hard cap (4 is generous), topology rule forbidding reverse edges. "If your design genuinely needs A → B → A, add a critic between them with a terminal 'approve/reject' output."

### 5. Cost runaway
Orchestrator spawns sub-agents; each spawns helpers; fan-out is unbounded because every layer decides in isolation and no layer sees the total. Documented case: $47K bill in 11 days. Fix depends on billing model:

**Per-token API billing:** total dollar budget cap at the run level, decremented by every agent and tool.

**Subscription billing (our fleet):** the cost is not dollars — it's rate limits, concurrency slots, wall-clock latency, fair-use throttles, and accelerated context-window pollution. Same structural fix (single ceiling at run level), different unit:
- **Step counter per run** — max LLM calls per orchestration (e.g., 12). Every agent increments the same counter.
- **Concurrency cap per run** — max parallel agents (e.g., 3-4). Prevents fan-out multiplication.
- **Daily fleet quota tracker** — across all terminals, surfaces "60% of today's likely quota used by 10am" so you can throttle.
- **Context window budget per orchestration** — nested-agent transcripts bloat parent context; cap nesting depth or aggregate transcript size.

### 6. Trusting summarizers to reframe intent
From ADR-006 in our own workspace, confirmed by MindStudio's handoff patterns: summarizers promote discussion topics to "outstanding work items," conflating questions with directives. Fix: preserve verbatim user messages; don't let summarizers classify turn intent.

### 7. Relying on context window size
Larger windows don't prevent context rot — they delay it. "Models perform significantly worse when relevant information is placed in the middle of a long context — even when that information is technically within the window" (Stanford 2023, "Lost in the Middle"). Signal-to-noise ratio matters more than raw capacity.

### 8. Treating handoff as only a summarization problem
Erdogan: the deeper problem is that intent, requirements, decisions, current progress, and validation evidence are scattered. Just summarizing conversation history loses structure. Each must be captured separately.

### 9. Bloated skill files
Skill files that contain full code examples, extensive background context, and detailed explanations "don't just fail to prevent context rot — they cause it." They load unnecessary tokens every time the skill runs.

### 10. Failing to persist decisions outside chat
Erdogan: "In long-running work, the more expensive loss is often decision history." If decisions live only in conversation, they're lost at session boundary.

### 11. Vague "done" claims
The default execution loop ending with "done" is insufficient. Must record evidence: changed files, commands run, test results, remaining risks.

### 12. Silent drift before closing
A feature can have a good spec, reasonable plan, and passing tests while still missing part of the original intent. Without an explicit drift audit, the gap is invisible.

### 13. Letting agents default to broken internal APIs
From our own wiki (Session-Chain-Optimization source): if simply asked to "read session history," the agent will default to broken libraries. Handoffs must explicitly forbid known-broken paths with reasoning.

## The 14 MAST failure modes (Cemri et al. 2025)

The taxonomy clusters 14 failure modes into 3 categories. Useful as a checklist when designing or auditing a handoff:

**Category 1 — System design issues (specification):**
- Insufficient context / missing information
- Ambiguous or incomplete task specification
- No common ground / shared understanding
- Poor role assignment

**Category 2 — Inter-agent misalignment (coordination):**
- Cascading errors across agents
- Information loss between agents
- Format mismatch / interface incompatibility
- Conflicting actions or decisions
- Redundant or useless actions

**Category 3 — Task verification (validation):**
- Lack of verification
- Unverified outputs
- Untracked dependencies
- Hidden side effects
- Premature termination

(See arxiv 2503.13657 for full definitions and inter-annotator agreement methodology.)

## Implications for a solo director with an AI fleet

Several patterns recur specifically in the solo-fleet context:

### 1. Phase-based handoffs fit naturally
Solo fleet work typically has clean phase boundaries (investigation → plan → implement → verify → ship). Each boundary is a natural handoff point. Don't carry exploratory conversation across boundaries — carry only the phase output.

### 2. Single-director means ownership is always clear
Enterprise MAS struggles with ownership ambiguity because multiple stakeholders direct multiple agents. Solo director means you are the single authoritative owner. Use this — your handoffs can hard-code you as the approval gate, eliminating one whole MAST failure category.

### 3. Cost runaway is asymmetric risk for fleet operators
A single runaway session is annoying. A fleet pattern that produces runaway sessions is existential (the $47K case). Per-conversation caps 1-2 orders of magnitude smaller than daily fleet cap. A $0.50 cap on a normal turn stops a runaway at $0.50 instead of blowing through the daily fleet cap.

### 4. Decision logs are more valuable than conversation history
Solo operators make 100+ decisions per year and forget them in 6-12 months (from solo_operator_adr_best_practices). Decision durability matters more than conversation fidelity. Handoffs must prioritize durable decisions over exploratory chat.

### 5. Multi-terminal state contamination is fleet-specific
Solo director running parallel terminals shares `history.jsonl`, session indices, file locks. Standard MAS literature doesn't address this because it assumes isolated agents. Our handoffs must terminal-scope state writes and reads explicitly.

### 6. Drift audit before close is non-negotiable
Fleet work ships changes faster than a single developer can review. Silent drift — passing tests but missing intent — is the highest-risk failure mode because it's invisible until production. Every handoff ending implementation work must include or trigger a drift audit.

## What this changes about our `/handoff` skill design

From the external research, our skill should:

1. **Detect handoff type** (phase-based vs rolling vs decision-only) — different types need different templates
2. **Require a persistent state object**, not free-form summary text (MindStudio Pattern 4)
3. **Require decision log separate from state** (Erdogan's `DECISIONS.md` split)
4. **Require evidence for "done"** — changed files, commands run, results, risks (Erdogan's loop change)
5. **Require drift audit before close** on implementation handoffs (Erdogan's `handoff drift`)
6. **Preserve verbatim user messages** — don't let summarizers reframe intent (ADR-006)
7. **Terminal-scope state writes** explicitly (our workspace's multi-terminal reality)
8. **Require budget/step caps** on any handoff that delegates to sub-agents (dev.to failure mode 5)
9. **Require ownership typed field** on multi-agent handoffs (dev.to failure mode 2)
10. **Forbid infinite handoff ping-pong** with hard cap and topology rule (dev.to failure mode 4)
11. **Keep skills lean** — under 200 lines, point to references instead of inlining (MindStudio strategy 1)
12. **Use sub-agents for context-heavy inspection** — main handoff context never sees raw scans (MindStudio strategy 4 / Scout Pattern)
13. **Test handoffs with long sessions** (50-200 turns), not 5-turn demos (Mindstudio best practice)
14. **Map handoff design against the 14 MAST failure modes** as a pre-flight checklist

## What our existing handoffs already do well

Comparing this session's handoffs (`grok-cross-model-skills`, `exploration-failure`, prior `auto-commit`, `ccr-fleet`) against the research:

- ✅ Structured state objects over prose (mostly)
- ✅ Task packets with bounded scope (auto-commit is the model)
- ✅ Explicit non-goals
- ✅ Falsifiers per task packet
- ✅ Reference paths with read order
- ✅ Terminal-scoped output paths (under `.artifacts/<termSafe>/` or `docs/`)

## What our existing handoffs miss (against the research)

- ❌ Decision log as a separate file (we conflate decisions with state)
- ❌ Evidence requirement for "done" (we accept narrative claims)
- ❌ Drift audit before close (we don't have this step)
- ❌ Verbatim last-user-message preservation (ADR-006 not enforced)
- ❌ MAST 14-mode pre-flight checklist (we don't audit against known failure modes)
- ❌ Sub-agent isolation for context-heavy inspection (we let main context bloat)
- ❌ Long-session testing (we test handoffs by writing them, not by simulating 100-turn use)
- ❌ Cost/step budgets on delegating handoffs (we don't cap)
- ❌ Ownership typed field for multi-agent handoffs (we don't have multi-agent handoffs yet, but will)

## Handoff vs plan vs status — the architecture

A `/handoff` skill needs three artifacts, not one. Mixing them conflates lifecycles and breaks multi-terminal isolation. Each artifact has one writer pattern, one update cadence, one purpose.

| Artifact | Purpose | Update cadence | Writer pattern | Storage |
|---|---|---|---|---|
| **Handoff** | Context, decisions, "what's next at high level" | When context shifts, decision made, phase boundary, terminal handoff | Single-writer (one session owns the handoff at a time) | `docs/handoffs/<topic>/HANDOFF.md` |
| **Plan structure** | Ordered task items, acceptance criteria, scope, falsifiers | When items added/removed, scope changes, criteria refined | Single-writer per plan (structure changes slowly) | `docs/handoffs/<topic>/PLAN.md` |
| **Plan status** | Per-item state: pending / in_progress / blocked / done | Every work step (fast, multi-writer across terminals) | Append-only event log per terminal | `.artifacts/<termSafe>/plan-<planId>/status.jsonl` |

**Why three, not one:**
- Handoff and plan structure are durable-ish, single-writer, semi-stable. Status is volatile, multi-writer, fleet-wide.
- Tracking status inside the handoff forces constant updates that break reader trust (other sessions can't rely on the handoff as stable context).
- Tracking plan structure inside the status log forces readers to replay history to know what's in scope (no current-state view).

**Not every handoff needs a plan.** Three shapes:
- Single-shot investigation → handoff only, no plan
- Single implementation task → handoff + short plan (3-5 items)
- Multi-stream program → handoff + plan + per-terminal status files

**Promotion paths (when durable material graduates to the wiki):**
- Handoff decision → ADR in wiki (when it crystallizes as architectural)
- Plan structure → wiki page (when items stabilize, scope isn't changing)
- Plan status → never promoted (always operational; archived, not wikified)

**Multi-terminal status: the four options assessed**

| Option | Pattern | Tradeoff |
|---|---|---|
| A. Single-writer rule | One terminal owns the plan; others read-only | Simple, blocks parallelism — defeats fleet purpose |
| B. Append-only event log per item | Terminals append events; status derived by replay | True multi-writer, stale-data immune, needs derivation step |
| **C. Per-terminal status files** | `.artifacts/<termSafe>/plan-<planId>/status.jsonl`; reader aggregates all terminals' files | Matches `/aar` convention, authority bound at claim time, multi-writer without coordination, fits fleet model |
| D. File locks with TTL | One lock per plan; terminal acquires, writes, releases | Serialized multi-writer; lock expiry fragile |

**Selected for our fleet: Option C.** Matches existing `P:/.artifacts/<termSafe>/` convention; authority is bound at claim time (`session_id + run_id + path list`), not re-derived from dirty state; multi-writer without coordination; a reader that wants fleet-wide status aggregates all terminals' files.

## Implications for a solution architect operating a fleet

The patterns above are familiar distributed-systems concepts applied to a new substrate (LLM sessions). Calibration notes for designing or auditing a handoff skill in this context:

1. **"Solo" describes decision authority, not system simplicity.** The fleet is a real distributed system with coordination, isolation, and stale-data problems. Design it as one.
2. **Single-director eliminates the ownership-ambiguity MAST category** — you are always the authoritative owner. Use this; your handoffs can hard-code you as the approval gate.
3. **Terminal isolation is the hard constraint.** Every component — handoff, plan structure, plan status, decision logs — must be multi-terminal isolated and stale-data immune by construction, not by convention.
4. **Authority bound at claim time, not re-derived from "whatever is dirty now."** The `(session_id, run_id, path list)` triple is the lease. State writes outside the lease are rejected.
5. **Event sourcing for status, single-writer for structure.** Status is append-only event log per terminal (Option C above); structure is single-writer per topic.
6. **Subscription economics, not per-token.** Cost caps become step/concurrency/quota caps, not dollar caps. The structural fix is the same; the unit differs.
7. **Decision logs persist outside chat.** The most expensive loss in long-running work is decision history, not conversation history. `DECISIONS.md` or equivalent, promoted to ADRs when durable.
8. **Design at full architecture; collapse when work is small.** An architect can collapse the three artifacts into one when the work doesn't warrant separation. A junior can't expand one into three when the work grows. Default to the full architecture; allow opt-in collapse.

- [[handoff-pre-compact-problems]] — our workspace's prior analysis of compact-handoff misframing
- [[auto-commit-authority-isolation]] — concrete fleet handoff with the task-packet pattern
- [[solo_operator_adr_best_practices]] — solo-specific decision documentation
- ADR-006 at `P:\docs\adrs\ADR-006-compact-handoff-verbatim-field.md` — verbatim-message preservation
- `P:\packages\.claude-marketplace\plugins\snapshot\scripts\models.py` — the 27-field HandoffCheckpoint schema
