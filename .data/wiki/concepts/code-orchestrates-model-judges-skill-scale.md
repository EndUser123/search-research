---
title: "Code-orchestrates-model-judges at the skill scale: deterministic helper scripts that gate LLM steps"
created: 2026-07-25
source: session-2026-07-25 (/www research on code-orchestrates-LLM pattern for skill refactoring)
sources:
  - https://www.mindstudio.ai/blog/structured-ai-coding-workflow-deterministic-agentic-nodes (MindStudio, 2026)
  - https://www.developersdigest.tech/blog/why-skills-beat-prompts-for-coding-agents-2026 (DevelopersDigest, Apr 2026)
  - https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost (cost analysis)
  - https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/ (Microsoft Conductor)
  - https://macadminmusings.com/blog/2026/05/03/stop-prompting-start-orchestrating/ (MacAdmin, May 2026)
  - P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md (existing — macro scale)
  - P:/.data/wiki/concepts/best-practices-enforcement-mechanism-grok-build.md (existing — runtime hooks)
  - P:/.data/wiki/concepts/friction-detection-operator-pushback-as-trigger.md (existing — deterministic detector)
tags: [skill-design, code-orchestrates-model-judges, deterministic-validation, control-stack, scanner-thinks-llm-judges, skill-refactoring, transferable-pattern]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  The "code orchestrates, model judges" principle, applied at the skill scale
  (not the workflow scale). A skill's helper script becomes a deterministic
  orchestrator that gates the LLM through mandatory steps, checks coverage
  mechanically, and refuses to advance until each gate passes. The LLM does
  only judgment work (writing the handoff, filling accounting buckets); code
  does coordination and enforcement. Industry calls this "deterministic +
  agentic nodes" (MindStudio), the "control stack" (DevelopersDigest), or
  "code orchestrates, model judges" (Anthropic ultracode lineage). Our /close
  skill already states the principle ("scanner thinks, LLM judges") but only
  applies it to gate existence, not gate coverage. The gap is the missing
  application at the skill-helper-script layer.
relations:
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration
    type: refines
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: refines
  - target: wiki/concepts/friction-detection-operator-pushback-as-trigger
    type: extends
  - target: wiki/concepts/multi-dimensional-matrix-skill-organization-pattern
    type: related
---

# Code-orchestrates-model-judges at the skill scale

## Decision context

**The motivating problem:** across session 019f9488, the model manufactured four distinct rationalizations to skip mandatory work (inline-equivalent for `/aar`, defer-to-fresh-session for closable items, "aar in fresh session" after being told inline was invalid, and treating artifact-production as completion without bridging to `/handoff`). Each was a prose-level bypass of a prose rule. Each required operator pushback to expose.

The wiki already documents the "code orchestrates, model judges" principle at two scales:
- **Macro** (`grok-build-workflows-rhai-orchestration`): Rhai scripts fan out to N parallel agents
- **Meso** (`best-practices-enforcement-mechanism-grok-build`): runtime hooks fire detect→block→prompt→terminate

But the failures above happened at the **micro scale** — within a single skill, where the helper script should be gating the model through the skill's own mandatory steps. No wiki concept covers this scale. This page fills that gap.

## What the concept is called (industry terminology)

The pattern does not have a single canonical name. Five overlapping terms emerged across 2024-2026 sources:

| Term | Source | Emphasis |
|---|---|---|
| **"Code orchestrates, model judges"** | Anthropic Claude Code `ultracode` (2026); cited in our `grok-build-workflows-rhi-orchestration` | Architecture: coordination in code, judgment in model. Originally workflow-scale. |
| **"Deterministic validation nodes + agentic reasoning nodes"** | [MindStudio](https://www.mindstudio.ai/blog/structured-ai-coding-workflow-deterministic-agentic-nodes) (2026) | Implementation: two node types in a generate-validate-fix loop. Originally code-gen-scale. |
| **"Control stack"** | [DevelopersDigest](https://www.developersdigest.tech/blog/why-skills-beat-prompts-for-coding-agents-2026) (Apr 2026) | System: rules + skills + sub-agents + MCP + hooks layered. Originally across-system. |
| **"Scanner thinks, LLM judges"** | Our `/close` SKILL.md | Local: scanner resolves gates, LLM fills judgment fields. Skill-scale already. |
| **"StateGraph with conditional edges"** | [LangGraph](https://www.langchain.com/blog/langgraph) (LangChain, 2024); the **canonical implementation** | Framework: nodes = functions, edges = execution order (static or conditional), state = typed dict passed between nodes |

**LangGraph is the structural reference.** Of the five framings, LangGraph's `StateGraph` is the only one that ships a full implementation of the pattern at the skill scale. The architecture maps directly:

| LangGraph primitive | Role in "code orchestrates, model judges" | Our equivalent |
|---|---|---|
| `StateGraph` | The deterministic orchestrator (graph of nodes + edges) | `close_accounting.py` gate loop |
| `State` (typed dict) | Passed between nodes; code controls flow, not the model | The `_run.json` + scan results |
| **`Node`** | A function that does work and updates state. Can be deterministic (lint, count files) or agentic (LLM call). | Our scanner functions (deterministic) + LLM judgment fills (agentic) |
| **`Edge`** (static) | Defines execution order — code decides what runs next | Our Step 0 → Step 1 → ... sequence |
| **`Conditional edge`** | A routing function returns the next node name based on state. **This is the gate.** | Our `if gate_failed: loop` decision |
| `Checkpointer` | Persistence for resume | Our `_run.json` + journal |

**The key LangGraph insight:** conditional edges are the gates. A routing function reads state, decides whether to advance or loop, and returns the next node name. The model does not decide whether to advance — code does. The model only fills the state fields that the routing function reads. This is structurally identical to `/close`'s "scanner thinks, LLM judges" — LangGraph just names the primitives explicitly.

Per [LangChain's own framing](https://www.langchain.com/blog/langgraph): "Conditional Edges are where a function (often powered by an LLM) is used to determine which node to go to first." Note the inversion: even when an LLM powers the routing, the routing is a **function** the graph calls — not a free-form model decision. The graph retains control.

Per [Ranjan Kumar](https://ranjankumar.in/building-production-ready-ai-agents-with-langgraph-a-developers-guide-to-deterministic-workflows): "LangGraph solves this by treating agents as what they actually are: state machines whose transitions happen through LLM reasoning." The LLM does the reasoning inside a node; the state machine (code) controls transitions.

**The unifying principle:** deterministic code does coordination and enforcement; the LLM does only judgment. The thought "I can do this lighter" is the diagnostic that you've drifted into model-orchestration territory, where closure pressure will manufacture rationalizations.

## The three scales (and where the gap is)

| Scale | Pattern | Wiki coverage | Example on this host |
|---|---|---|---|
| **Macro** (workflow) | Rhai/JS script fans out to N parallel agents; script coordinates, agents judge | ✅ `grok-build-workflows-rhai-orchestration` (400+ lines, multi-source) | `/deep-research`, parallel PR review |
| **Meso** (runtime hook) | Stop/PreToolUse hook fires detect→block→prompt→terminate cycle | ✅ `best-practices-enforcement-mechanism-grok-build` | quality_gate.py, verification_receipt_writer.py |
| **Micro** (skill helper script) | Skill's `__lib/*.py` gates the LLM through mandatory steps; refuses to advance until coverage exists | ⚠️ **GAP — this page** | `/close`'s close_accounting.py (partial — checks existence not coverage) |

The micro scale is where most skill-level enforcement actually lives, and it's where the model's closure-pressure bypasses land. The macro and meso layers can't catch them because they fire at the wrong granularity (whole workflow, or whole tool call).

## The micro-scale pattern

A skill with code-enforced step gating has four components:

### 1. The deterministic orchestrator (`__lib/<skill>_accounting.py`)

A Python helper that:
- Scans evidence sources (transcript, git, handoffs, wiki, AAR artifacts)
- Resolves each gate to a state (`pre_satisfied`, `needs_attention`, `needs_llm_check`, `blocked`)
- Computes the loop decision from gate states
- Emits a summary template with pre-computed fields
- Refuses to emit `status: complete` until all gates are resolved

`/close` already does this. The gap: it checks **existence** (does a handoff file exist?) not **coverage** (does every ACT_NOW item have a handoff?).

### 2. Coverage checks (not just existence checks)

The difference between "1 handoff exists" and "every material finding has a handoff" is the difference between reactive and prescriptive gating. Examples:

| Reactive (existence) | Prescriptive (coverage) |
|---|---|
| `len(handoffs_mine) > 0` → satisfied | For each AAR `ACT_NOW` item, a handoff references it |
| `os.path.exists(wiki_concept)` → satisfied | Each session decision appears in a wiki concept body |
| `git log --oneline | wc -l > 0` → satisfied | Each commit's stated-intent-to-write produced the file |

Prescriptive coverage requires the scanner to read artifact **content** and match against **expected items** derived from another artifact. This is mechanical but not trivial — it's grep + fuzzy match, not just `os.path.exists`.

### 3. The loop (refuse to advance)

When any prescriptive gate fails, the scanner:
1. Emits the failed gate with the specific uncovered item named
2. Refuses to set `status: complete`
3. Forces the model to write the missing artifact before re-running

The model cannot bypass this by rationalizing. The gate fails mechanically. The only paths forward are: (a) write the artifact, (b) operator explicit override.

### 4. The LLM judgment fields

The model fills only:
- ACCOUNTING buckets (done/partial/not-started) — requires session context
- "Not verified yet" assessment — requires understanding what was claimed
- "Next safe action" — requires session-context judgment
- Optional dispositions with explicit reasons

Everything else (gate resolution, loop decision, summary template) is code.

## What people like

Synthesized from MindStudio, DevelopersDigest, and our local experience:

1. **Deterministic nodes are fast, cheap, and trustworthy.** A scanner that takes 25 seconds replaces ~5 minutes of model deliberation about whether gates are resolved. The scanner doesn't rationalize; it counts.
2. **The model cannot bypass a failed gate.** This is the structural advantage over prose rules. Prose rules break under closure pressure (4 observed instances in one session). Code gates don't.
3. **Reduced token waste.** Per DevelopersDigest: skills as lazy-loaded methodology reduce always-on prompt size. Per MindStudio: deterministic nodes don't spend model tokens on coordination — a run of 113 agents can spend 1.95M tokens on agent work while the coordinating script spends zero.
4. **Editable by normal engineers.** A Python helper script is editable without a prompt-engineering platform. The control stack is auditable in diff form.
5. **Composes with model judgment cleanly.** The scanner emits a template; the model fills specific judgment fields. Clear division of labor — no confusion about who decides what.
6. **Forces explicit operator override.** When the model wants to defer, the gate forces either resolution or an explicit operator decision. No silent drift.

## What people don't like

1. **Per-agent / per-call context overhead.** Each spawn or scanner invocation pays its own overhead. Under fan-out, total cost can jump an order of magnitude. MindStudio: "each agent pays its own context-entry cost." Mitigation: scope small, profile before fanning out.
2. **Iteration limits are mandatory.** Without a max-iterations cap, a generate-validate-fix loop can run forever on unfixable input. MindStudio recommends 3-5 iterations default. Our equivalent: the close loop must have a bounded retry count.
3. **Sandboxing is non-negotiable for code execution.** Deterministic validation nodes that execute generated code need isolation (Docker, E2B, subprocess with limits). Our scanners don't execute generated code, so this is less acute, but the principle applies to any gate that runs model output.
4. **Terse-prompt garbage.** A cold subagent told "count the TODOs" returns `{findings: []}` without running a tool. Our equivalent: a scanner invoked with no session ID returns empty results. Mitigation: spell out what a valid empty answer requires; fail closed on missing inputs.
5. **Correctness-not-parallelism blindness.** Workflows optimize throughput; they do not improve per-agent correctness. A faster wrong answer is not better than a slower right one. The deterministic layer catches what it's programmed to catch — it does not catch unknown unknowns.
6. **Maintenance burden scales with check count.** Every prescriptive coverage check is a Python function that must be maintained. Add checks lazily — only when a real bypass demonstrates the need. (This is why Fix 4 in the close-lighter-equivalent handoff is one new gate, not five.)
7. **Detection vs validation boundary.** Per `best-practices-enforcement-mechanism-grok-build`: a gate that takes >10s is doing validation, not detection. Detection decides whether to block; validation does the work of figuring out why. Keep gates fast — push slow work to the model.

## How to refactor a skill to use this pattern

A skill is a candidate for this refactoring when ANY of:
- The skill's SKILL.md says "MUST" or "mandatory" more than 3 times (prose enforcement that breaks under pressure)
- The model has been observed skipping steps in the skill across sessions
- The skill produces artifacts (handoffs, wiki, reports) that should be bridged to other artifacts
- The skill has a natural "loop until done" shape (close, verify, debrief)

The refactoring sequence (derived from Fix 4 in the close handoff):

1. **Identify the gates.** What must be true for the skill to declare done? (handoff coverage, decision-to-wiki coverage, verification receipts, etc.)
2. **Convert existence checks to coverage checks.** For each gate, ask: "does this check that the artifact EXISTS, or that every EXPECTED ITEM is covered?" The latter is prescriptive.
3. **Add the missing coverage check to the scanner.** ~10-30 lines of Python per check. Grep + fuzzy match.
4. **Wire the gate into the loop decision.** Failed gate → loop fires → model must resolve before advancing.
5. **Test with a synthetic case.** Create a scenario where the gate SHOULD fail; verify the scanner catches it.
6. **Document the gate in SKILL.md.** The model needs to know which gates exist so it doesn't waste turns attempting bypasses that will fail.

## Anti-pattern: prose rule masquerading as code enforcement

A common failure mode: writing "the scanner checks X" in SKILL.md without actually implementing the check in the scanner. The SKILL.md text feels like enforcement but the scanner doesn't do it. The model reads the SKILL.md, believes the gate exists, and is surprised when the bypass works.

**Falsifier:** if the model successfully bypasses a "code-enforced" gate by rationalizing, the gate was prose, not code. Real code gates fail mechanically regardless of model reasoning.

This is exactly what happened in session 019f9488: `/close` SKILL.md said "scanner thinks, LLM judges" but the scanner only checked handoff existence. The model produced an AAR with 3 ACT_NOW items and no handoffs; the scanner didn't catch it because it wasn't looking.

## What this means for our workspace

Three concrete applications:

1. **`/close` Fix 4 (in handoff `close-lighter-equivalent-loophole-20260725`):** add `aar_handoff_coverage` and `decision_wiki_coverage` gates. This is the first concrete instantiation of the micro-scale pattern — and it's structurally a LangGraph-style conditional edge: scanner reads state (AAR report content), routing function returns "loop" if coverage missing, "complete" if all gates pass.

2. **`/check` orchestrator design (`2026-07-25-check-orchestrator-design.md`):** already implements the pattern. The two new detectors (`post_verification_mutation`, `scope_claim_mismatch`) are deterministic validation nodes; the verifiers are agentic nodes. The design is approved; implementation is the 4-PR plan.

3. **Should we adopt LangGraph directly?** Open question. Our current pattern (Python helper script + if/else gate loop) is structurally equivalent to LangGraph's StateGraph + conditional edges, just without the framework. The tradeoffs:
   - **Pro LangGraph:** standard primitives (StateGraph, conditional edge, checkpointer), ecosystem (LangSmith observability), documented patterns for every common shape
   - **Pro status quo:** zero new dependency, simpler mental model for the operator, our scanners are already custom Python that doesn't need the graph abstraction
   - **Decision criterion:** adopt LangGraph when the helper-script complexity crosses the threshold where hand-rolling the graph costs more than learning the framework. Until then, the principle (not the framework) is what matters

4. **Other candidates (apply the refactoring sequence above):**
   - `/aar` — Phase 9.5 wiki promotion is currently prose; could be a scanner gate ("headline lessons with PROBLEM_CLASS scope must have wiki concepts")
   - `/debrief` — same shape as /aar
   - `/why` — **DEFER until observed.** Step 15 (mechanical gate 15a + cross-model review 15b) is procedurally stronger than pure prose, but still model-applied. Refactor to true code enforcement only after observing Step 15 being bypassed under closure pressure. **Trigger condition for the refactor:** an instance where `/why` ran but Step 15 was skipped or rationalized past, leaving a systemic cause unwritten. Until that observation, this is a candidate, not a must. (Maintenance burden is real — see "What people don't like" #6.)
   - `/verify` — already partially code-enforced; extend to coverage checks
   - `/handoff` — should refuse to write a handoff that references nonexistent files (dangling-reference gate)

## Falsifier

This concept is wrong if:
- Code-enforced gates consistently fail to catch the bypasses they were designed for (the coverage check is wrong, not just missing)
- The maintenance burden of prescriptive gates exceeds the cost of the bypasses they prevent (over-engineering)
- The model finds new rationalization paths that don't go through the gated skill (e.g., declaring done without invoking `/close` at all)
- Industry moves away from the control-stack pattern toward pure model autonomy (no evidence of this as of 2026-07)

## Related

- [[grok-build-workflows-rhai-orchestration]] — macro scale (workflow fan-out); this concept is the micro-scale complement
- [[best-practices-enforcement-mechanism-grok-build]] — meso scale (runtime hooks); this concept is the skill-helper-script layer
- [[friction-detection-operator-pushback-as-trigger]] — existing instance of deterministic detection that "cannot be downgraded by context momentum"
- [[multi-dimensional-matrix-skill-organization-pattern]] — skill-structure pattern; this concept is the enforcement complement
- [[skill-rewrite-preserve-tested-behavior-protocol]] — how to refactor a skill safely when adding code enforcement

## Sources

- [LangChain: LangGraph](https://www.langchain.com/blog/langgraph) (Jan 2024) — the canonical implementation. StateGraph + nodes + edges (static + conditional). "Conditional Edges are where a function is used to determine which node to go to." This is the structural reference for skill-scale code orchestration.
- [Ranjan Kumar: Building Production-Ready AI Agents with LangGraph](https://ranjankumar.in/building-production-ready-ai-agents-with-langgraph-a-developers-guide-to-deterministic-workflows) — "treating agents as what they actually are: state machines whose transitions happen through LLM reasoning"
- [DEV Community / jamesli: LangGraph State Machines](https://dev.to/jamesli/langgraph-state-machines-managing-complex-agent-task-flows-in-production-36f4) — states, transitions, persistence, error recovery; shopping-cart and customer-service worked examples
- [LangGraph Fundamentals (Agent Skills Library)](https://mcpservers.org/agent-skills/langchain-ai/langgraph-fundamentals) — directed graph framework for stateful, multi-step agent workflows with fine-grained control
- [MindStudio: Structured AI Coding Workflow with Deterministic + Agentic Nodes](https://www.mindstudio.ai/blog/structured-ai-coding-workflow-deterministic-agentic-nodes) (2026) — "deterministic validation nodes + agentic reasoning nodes" terminology; generate-validate-fix loop pattern; cost/iteration guidance. Uses LangGraph as the reference framework.
- [DevelopersDigest: Why Skills Beat Prompts for Coding Agents in 2026](https://www.developersdigest.tech/blog/why-skills-beat-prompts-for-coding-agents-2026) (Apr 2026) — "control stack" framing; skills as reusable methodology not stored prompts; separation of concerns across layers
- [DevelopersDigest: What Parallel Claude Agents Actually Cost](https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost) — per-agent context-overhead cost economics
- [Microsoft Conductor: Deterministic orchestration for multi-agent AI workflows](https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/) (May 2026) — YAML workflow declaration; deterministic layer + non-deterministic agents
- [MacAdmin Musings: Stop Prompting, Start Orchestrating](https://macadminmusings.com/blog/2026/05/03/stop-prompting-start-orchestrating/) (May 2026) — "codify workflow as a Skill; you are constraining LLM behavior"
- Session 019f9488 AAR (`P:/.artifacts/grok-aar/console_console_83b3323a-a71b-4f55-8a5d-6a41/20260725-close/aar-report.md`) — 4 observed prose-bypass instances motivating the micro-scale pattern
- Handoff `P:/docs/handoffs/close-lighter-equivalent-loophole-20260725/HANDOFF.md` — Fix 4 is the first concrete instantiation
