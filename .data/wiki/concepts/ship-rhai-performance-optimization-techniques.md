---
title: "Ship-rhai performance optimization: reducing agent dispatch overhead in Rhai workflows"
created: 2026-08-06
source: session-019fd9ae (/www research on ship-rhai performance optimization)
sources:
  - external: https://genta.dev/resources/ai-agent-orchestration-patterns-llm-vs-code-driven
    title: "AI Agent Orchestration: LLM vs Code-Driven Patterns"
    quality: 9
    primary_source: true
  - external: https://www.abdelaziznotes.com/posts/stop-letting-llms-orchestrate-your-ai-agents
    title: "Stop Letting LLMs Orchestrate Your AI Agents"
    quality: 10
    primary_source: true
  - external: https://gianlucamazza.it/en/blog/langgraph-workflow-orchestration
    title: "State as the API: LangGraph After Three Rewrites"
    quality: 9
    primary_source: true
  - external: https://dev.to/samuvelp/i-built-a-langgraph-agent-that-audits-android-projects-heres-the-architecture-53jh
    title: "DroidDoctor: LangGraph Agent — The LLM Never Scans Files"
    quality: 8
    primary_source: true
  - external: https://github.com/scottgl9/skelm
    title: "skelm — code(), llm(), agent() tripartite step taxonomy"
    quality: 7
    primary_source: false
  - external: https://github.com/AbdelazizMoustafa10m/orchcore
    title: "orchcore — reusable headless multi-agent orchestration engine"
    quality: 8
    primary_source: false
  - external: https://github.com/dgenio/ChainWeaver
    title: "ChainWeaver — deterministic MCP tool flows, no LLM calls between steps"
    quality: 6
    primary_source: false
  - external: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
    title: "Azure Architecture Center — AI Agent Design Patterns"
    quality: 8
    primary_source: false
  - external: https://github.com/redis-developer/reduce-llm-calls-with-vector-search
    title: "Reduce LLM calls with vector search"
    quality: 6
    primary_source: false
  - internal: P:/.data/wiki/concepts/command-wrapper-pattern-for-workflows.md
    title: "Command wrapper pattern for workflows (Rhai's env/filesystem constraint)"
  - internal: P:/.data/wiki/concepts/agent-consolidation-in-parallel-workflows.md
    title: "Agent consolidation: group by capability, not topic"
  - internal: P:/.data/wiki/concepts/pre-packed-evidence-pattern-for-workflow-subagents.md
    title: "Pre-packed evidence pattern for workflow subagents"
  - internal: P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md
    title: "Grok Build workflows: Rhai-orchestrated subagent fan-out"
  - internal: P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    title: "Code-orchestrates-model-judges at the skill scale"
tags: [ship-rhai, workflow-performance, agent-dispatch, rhai-limitation, code-orchestrates-model-judges, optimization, hybrid-pipeline, orchestration, deterministic-vs-llm]
host: grok
agent: grok
verification: multi-source-verified
cognitive_load: 3
relations:
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration.md
    type: extends — adds performance optimization layer to the workflow orchestration concept
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: applies — the code/LLM boundary is where the performance fix lives
  - target: wiki/concepts/command-wrapper-pattern-for-workflows.md
    type: depends — the Rhai constraint (no subprocess/filesystem) is the root cause
  - target: wiki/concepts/agent-consolidation-in-parallel-workflows.md
    type: applies — consolidation reduces agent count
  - target: wiki/concepts/pre-packed-evidence-pattern-for-workflow-subagents.md
    type: applies — pre-packing eliminates redundant tool calls per agent
  - target: wiki/concepts/ship-pipeline-enforcement-field-solutions-2026.md
    type: refines — adds the performance dimension to the ship pipeline enforcement analysis
summary: >
  Ship-rhai is slow (21-minute runs documented) because it delegates ALL pipeline
  phases — including deterministic git/file operations — to full agent dispatches.
  Rhai's fundamental constraint (no subprocess, no filesystem, no env vars — all
  external interaction goes through agent() calls) means every git command, every
  script execution costs a full model spin-up. Five optimization techniques are
  applicable within Rhai's constraints: (1) pre-compute deterministic work in the
  command wrapper before workflow launch, (2) consolidate agents by capability,
  (3) pre-pack evidence into agent prompts, (4) tier models (fast for mechanical,
  reasoning for judgment), (5) conditional phase skipping. The architectural
  alternative — ship-py's Python orchestrator — is structurally superior for this
  use case because Python can do deterministic work directly via subprocess,
  eliminating the Rhai constraint entirely. The field consensus across 7+ independent
  sources confirms "code orchestrates, LLM judges" as the production pattern.
---

# Ship-rhai performance optimization: reducing agent dispatch overhead

## Decision context

**Why this research was needed:** the operator noted ship-rhai is "so slow
it's unusable." The `ship-py-hardening` handoff (Finding 8) documented a
**21-minute ship-rhai-3 runaway** that required elevating review agents from
read-only to execute capability just to get it to finish. The operator asked:
what's the best way to optimize ship-rhai performance, and are there skills
or repos that help?

**What alternatives were explored:** five in-Rhai optimization techniques
(pre-compute, consolidate, pre-pack, model-tier, skip), plus the architectural
alternative (Python orchestrator). External tooling was surveyed (orchcore,
skelm, ChainWeaver, DroidDoctor pattern). The Rhai constraint (no subprocess/
filesystem) was confirmed as the root cause limiting in-Rhai optimization.

**What the research changed:** confirmed that the performance problem is
structural (Rhai can only interact through agent() calls), not incidental.
The optimization path within Rhai can reduce runtime by ~40-60% but cannot
eliminate the fundamental overhead. The architectural alternative (Python
orchestrator doing deterministic work directly) is the field-consensus
production pattern.

## The root cause: Rhai's agent-only interaction model

Rhai has no subprocess, no filesystem listing, no env var access, and no
arbitrary shell execution ([[command-wrapper-pattern-for-workflows]]). The
ONLY Rhai primitives for external interaction are:

- `agent(prompt, options)` — dispatch a subagent (full model spin-up)
- `parallel(jobs)` — dispatch N subagents concurrently
- `write_scratch_file(name, content)` — write to scratch directory
- `pause()` / `await_user()` — pause for human input

This means **every git command, every script execution, every file
read in ship-rhai goes through a full agent dispatch.** The detect phase
spawns an agent to run `git rev-parse` and `git status`. The verify phase
spawns an agent to run `ship_receipt.py`. The merge phase spawns an agent
to run `git merge`. None of these require LLM reasoning — they are
deterministic operations routed through the most expensive possible
execution path.

Compare with ship-py's Python orchestrator, which runs `ship_receipt.py`
directly via `subprocess.run()` (orchestrator line 510) and git commands
via `_git()` (line 48). Zero model tokens on deterministic work.

This is the same diagnosis the field makes. Abdelaziz Abdelrasol, who
built four multi-agent orchestration systems before extracting the pattern:

> "When orchestration logic lives in an LLM's reasoning, you're asking a
> probabilistic system to behave deterministically. These are not bugs
> that will be fixed next quarter. They're inherent to the architecture."

Source: [abdelaziznotes.com](https://www.abdelaziznotes.com/posts/stop-letting-llms-orchestrate-your-ai-agents)

## Five optimization techniques (within Rhai's constraints)

### 1. Pre-compute deterministic work in the command wrapper (biggest win)

The SKILL.md file already runs `pick_model.py` before launching the workflow.
It can also run git commands and pass results as workflow args. This
eliminates the detect-phase agent entirely (~2-3 min saved).

```powershell
# In SKILL.md, before /workflow launch:
$gitState = git -C P:/ status --short
$gitLog = git -C P:/ log --oneline -10
$gitDiff = git -C P:/ diff --stat
# Pass as workflow args
/workflow ship-rhai {"session_id": "...", "git_state": "$gitState", ...}
```

The workflow then uses `args.git_state` directly in the detect phase instead
of spawning an agent to discover it. This is the [[command-wrapper-pattern-for-workflows]]
pattern applied to performance.

**Estimated savings:** 1 full agent dispatch (~2-3 min).

### 2. Consolidate agents by capability

From [[agent-consolidation-in-parallel-workflows]]: group by what agents
need (mechanical: run commands + parse output; judgment: reason about
context), not by topic. Ship-rhai's current 5-phase, 6+ agent design can
collapse to 3 agents:

| Current | Consolidated | Why |
|---------|-------------|-----|
| Detect agent (runs git) | Pre-computed in command wrapper | No agent needed |
| Parent review agent | Review agent 1 | Judgment work |
| Specialist review agent | Review agent 2 | Judgment work |
| Fix agent + recheck agent | Fix-and-verify agent (one agent fixes, self-checks) | Both need write + read; one context |
| Verify agent (runs ship_receipt.py) | Merge with fix-and-verify or make conditional | Mechanical — run script, report output |
| Merge agent | Conditional — skip if health-check mode | Mechanical |

**Estimated savings:** 2-3 agent dispatches (~4-6 min).

### 3. Pre-pack evidence into agent prompts

From [[pre-packed-evidence-pattern-for-workflow-subagents]]: pass git diff,
file list, and prior-phase results into agent prompts so they don't waste
5-10 tool calls discovering what the workflow already knows.

Ship-rhai's review agents currently each independently run `git merge-base`,
`git diff`, and `read_file` on changed files. If the command wrapper
pre-computes the diff and passes it as an arg, each review agent starts
with the diff in its prompt and goes straight to analysis.

**Estimated savings:** 5-10 tool calls per agent (~1-2 min per agent).

### 4. Tier models — fast for mechanical, reasoning for judgment

The detect, verify, and merge phases don't need reasoning models. Use the
fastest free-tier model for these. Reserve reasoning-capable models for
review and fix phases only.

Ship-rhai already has `FREE_A`/`FREE_B`/`FREE_C` model slots, but all are
used for different agents, not tiered by task complexity. A `minimax-m3`
detect agent that just runs git commands is wasting a dispatch on a model
that could be doing review work.

**Estimated savings:** faster model load for mechanical phases (~30s-1min per phase).

### 5. Conditional phase skipping (partially implemented)

Ship-rhai already skips the fix phase when `all_bugs.len() == 0`. Extend
this to the merge phase (skip in health-check mode — already partially done)
and the verify phase (if no work detected, skip to a lightweight report).

**Estimated savings:** 1-2 agent dispatches when conditions are met.

### Combined estimate

| Technique | Agents saved | Time saved |
|-----------|-------------|-----------|
| Pre-compute detect | 1 | ~2-3 min |
| Consolidate fix+verify+merge | 2-3 | ~4-6 min |
| Pre-pack evidence | 0 (fewer tool calls) | ~2-4 min |
| Model tiering | 0 (faster models) | ~1-2 min |
| Conditional skipping | 1-2 | ~2-4 min (conditional) |
| **Total** | **4-6 fewer dispatches** | **~11-19 min → ~5-8 min** |

This would bring ship-rhai from ~21 min to ~5-8 min — usable but still
slower than ship-py's Python-direct approach.

## The architectural alternative: Python orchestrator

The research strongly supports the conclusion that ship-py's architecture
is structurally superior for this use case. Every source converges on
"code orchestrates, LLM judges" as the production pattern:

| Source | Key claim |
|--------|-----------|
| [genta.dev](https://genta.dev/resources/ai-agent-orchestration-patterns-llm-vs-code-driven) | "Code orchestrates the pipeline, LLMs execute the steps within it" — the recommended production pattern |
| [Abdelaziz](https://www.abdelaziznotes.com/posts/stop-letting-llms-orchestrate-your-ai-agents) | "Orchestration is a code problem, not a prompting problem" — 40% output retrieval failure for interactive subagents vs 0% for headless |
| [Microsoft Azure Architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) | "Use the lowest level of complexity" — start code-driven, add LLM routing only when needed |
| [DroidDoctor](https://dev.to/samuvelp/i-built-a-langgraph-agent-that-audits-android-projects-heres-the-architecture-53jh) | "The LLM never scans files. Each analysis node is deterministic Python code. The LLM only receives a structured JSON summary at the end." |
| [Gianluca Mazza](https://gianlucamazza.it/en/blog/langgraph-workflow-orchestration) | "I checkpoint around side effects and LLM calls, then skip cheap deterministic transforms when safe" |
| [GitHub Agentic Workflows](https://github.github.com/gh-aw/guides/deterministic-agentic-patterns/) | Official GitHub pattern: combine deterministic computation with AI reasoning |
| [skelm](https://github.com/scottgl9/skelm) | "Three step kinds: code() for deterministic logic, llm() for single inference calls, agent() for full multi-turn loops" |

The DroidDoctor pattern is the most directly applicable reference. Its
7-node state machine has 6 deterministic nodes (Python: regex, XML parsing,
HTTP checks) and 1 LLM node (synthesizes findings into a prioritized report).
It even has `--no-llm` mode that changes the graph topology at build time,
skipping the LLM entirely for CI pipelines. This is exactly the hybrid
ship-py was designed to be — Python does detect/verify directly, agents
do review/fix.

Python's advantage over Rhai for this specific use case:

| Capability | Rhai | Python (ship-py) |
|-----------|------|-----------------|
| Run git commands | Must go through agent() | `subprocess.run()` directly |
| Run ship_receipt.py | Must go through agent() | `subprocess.run()` directly |
| File read/write | `write_scratch_file()` only | Full filesystem access |
| Env var access | None | `os.environ` |
| Conditional routing | Native (`if`/`else`) | Native (`if`/`else`) |
| Agent dispatch | `agent()` — the only external interaction | `spawn_subagent` — one of many tools |

The fundamental insight: **Rhai can ONLY orchestrate agent calls. Python
can orchestrate both deterministic work AND agent calls.** For a pipeline
where 3 of 5 phases are deterministic, the tool that can do deterministic
work directly is structurally faster.

## External tools and repos

### orchcore — headless multi-agent orchestration engine

[GitHub: AbdelazizMoustafa10m/orchcore](https://github.com/AbdelazizMoustafa10m/orchcore) |
[PyPI: orchcore](https://pypi.org/project/orchcore/)

Built by Abdelaziz Abdelrasol after building 4 multi-agent systems. The
60-70% of orchestration code that was identical across projects — subprocess
management, stream parsing, rate-limit recovery, stall detection, resume
logic — extracted into a reusable library.

Key features relevant to ship-rhai:
- **AgentRegistry**: zero-config support for Claude, Codex, Gemini, Copilot,
  OpenCode. New agents via TOML.
- **4-Stage Stream Pipeline**: normalizes 5 agent CLI formats into unified
  events. `StreamFilter` drops ~95% of JSONL noise before parsing.
- **Phase-level resume**: skip completed phases on re-run after failure.
- **RateLimitDetector + ResetTimeParser**: timezone-aware cooldown parsing.
- **DAG-based phase execution**: validates dependencies, supports parallel
  with `asyncio.Semaphore`-gated concurrency.

[INFERENCE] — orchcore is designed for headless CLI orchestration (launching
agent binaries as subprocesses), not for Grok Build's Rhai workflow engine.
It would be directly applicable to ship-py's Python architecture but would
require adaptation for the Rhai context. [UNTESTED] on this workspace.

### skelm — tripartite step taxonomy

[GitHub: scottgl9/skelm](https://github.com/scottgl9/skelm)

"Three step kinds, none wrapping another: `code()` for deterministic logic,
`llm()` for single inference calls, `agent()` for full multi-turn loops."

This is the cleanest formulation of the hybrid pattern. Every pipeline step
is explicitly typed as deterministic, single-inference, or full-agent. This
prevents the ship-rhai failure mode where everything is an `agent()` call
regardless of whether it needs multi-turn reasoning.

[INFERENCE] — skelm is a framework, not a library we'd install. The value
is the pattern: explicitly classifying each pipeline step as code/llm/agent
and using the cheapest sufficient execution mode.

### DroidDoctor — "the LLM never scans files" reference architecture

[GitHub: samuvelp/droiddoctor](https://github.com/samuvelp/droiddoctor) |
[DEV Community article](https://dev.to/samuvelp/i-built-a-langgraph-agent-that-audits-android-projects-heres-the-architecture-53jh)

A LangGraph state machine for Android project auditing. 6 deterministic
nodes (Python: regex, XML parsing, HTTP version checks) feed 1 LLM node
(synthesizes prioritized report). `--no-llm` flag changes the graph topology
at build time.

The key design principle stated directly: "Deterministic nodes + LLM
synthesis beats giving the LLM raw files. Early prototype: I fed
build.gradle content directly to Claude and asked it to find issues. It
hallucinated dependency versions. It missed the version catalog indirection.
The current architecture is: code does the scanning (correctly, every
time), LLM does the reasoning about what matters most."

This is the reference implementation for ship-py's intended architecture.

### ChainWeaver — no LLM calls between steps

[GitHub: dgenio/ChainWeaver](https://github.com/dgenio/ChainWeaver)

"ChainWeaver makes one specific trade-off — no LLM calls between steps,
enforced at the framework level — and aligns the rest of the design
(Pydantic-validated I/O, file-serializable flows, no server) around it."

Extreme version of the pattern: the framework itself prevents inter-step
LLM calls. [UNTESTED] — may be too restrictive for ship-rhai's review/fix
phases which DO need LLM judgment.

## Field consensus: the LLM-driven vs code-driven boundary

The most important finding from this research is that the field has
converged on a specific answer to the question "where should the LLM-driven
vs code-driven boundary sit?":

> **Code orchestrates the pipeline; LLMs execute the steps within it.**

The decision framework from genta.dev provides the clearest heuristic:

> "If you can write the routing logic as a decision tree and it fits on one
> page, write it in code. If you can't, and the branching is fundamentally
> semantic rather than structural, that's a candidate for LLM-driven routing."

Applied to ship-rhai's phases:

| Phase | Routing logic | Code or LLM? |
|-------|--------------|--------------|
| Detect | "has_work = files_changed or status" | **Code** (decision tree, fits on one line) |
| Review | "find bugs in this diff" | **LLM** (semantic, requires judgment) |
| Fix | "fix these specific bugs" | **LLM** (code generation) |
| Verify | "run ship_receipt.py, report exit code" | **Code** (deterministic) |
| Merge | "if verdict == SHIP DONE: git merge" | **Code** (decision tree) |

3 of 5 phases should be code, not LLM. In Rhai, "code" still means "agent
dispatch" (the constraint). In Python, "code" means "subprocess.run()".

## What this means for our workspace

1. **ship-rhai SKILL.md** — add pre-compute step in the invocation section
   (run git commands before `/workflow` launch, pass as args). This is the
   single highest-ROI change.
2. **ship-rhai.rhai workflow** — consolidate fix+verify+merge into fewer
   agent dispatches. The detect phase can be removed entirely if the
   command wrapper pre-computes git state.
3. **ship-py orchestrator** — SHIPPED. The Python orchestrator is the
   production architecture. `cmd_fix`, `cmd_merge`, and the state-machine
   gate are all implemented. ship-rhai is deprecated (the .rhai workflow
   file was deleted). Remaining work consolidated in
   `ship-pipeline-open-work-20260809`.
4. **orchcore evaluation** — install and evaluate for the Python path.
   Provides phase-level resume, stream monitoring, and rate-limit recovery
   out of the box. [UNTESTED] — needs evaluation session.
5. **Retire the "both skills are active — under development" framing**
   — the research provides the decision criterion: ship-py's architecture
   is the production pattern; ship-rhai should either be optimized within
   its constraints (interim) or deprecated in favor of the Python path
   (long-term).

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| Rhai has no subprocess/filesystem/env access | `command-wrapper-pattern-for-workflows.md` documents: "Rhai has no `ls`/`glob`/`opendir`", "Rhai has no `getenv`" | [OBSERVED] — workspace wiki |
| ship-rhai delegates all phases to agents | `~/.grok/workflows/ship-rhai.rhai` lines 129-143 (detect), 369-370 (verify), 447-458 (merge) — all use `agent()` | [OBSERVED] — code read this session |
| ship-py runs ship_receipt.py via subprocess directly | `ship_orchestrator.py` line 510: `subprocess.run(cmd, ...)` | [OBSERVED] — code read this session |
| 21-minute ship-rhai-3 runaway | Historical: ship-py-hardening-20260805 handoff (deleted; consolidated into ship-pipeline-open-work-20260809) Finding 8 | [OBSERVED] — handoff |
| Agent consolidation reduced close-check from 9→3 agents | `agent-consolidation-in-parallel-workflows.md` Receipts table | [OBSERVED] — workspace wiki |
| Pre-packed evidence reduced close-check remediation from 15→5 min | `pre-packed-evidence-pattern-for-workflow-subagents.md` summary | [OBSERVED] — workspace wiki |
| orchcore exists and provides headless orchestration | [GitHub repo](https://github.com/AbdelazizMoustafa10m/orchcore), PyPI package `orchcore` | [INFERENCE] — not tested on this workspace |
| ~5-8 min estimated post-optimization runtime | Calculated from per-agent cost estimates (~2-3 min each × remaining dispatches) | [INFERENCE] — not measured |
| 40% background output retrieval failure for interactive subagents | Abdelaziz article, citing GitHub issues #18352, #25413, #23620 | [INFERENCE] — secondary source, not independently verified |
| DroidDoctor "LLM never scans files" pattern | [DEV Community article](https://dev.to/samuvelp/...) — read in full this session | [OBSERVED] — primary source read |

## Recommendation

**For immediate optimization within Rhai (ship-rhai):** apply techniques
1-5 to reduce runtime from ~21 min to ~5-8 min. The biggest single win is
pre-computing the detect phase in the command wrapper.

**For structural fix (ship-py path):** DONE. ship-py's Python orchestrator
implements phase ordering, gates, cmd_fix, cmd_merge, and the state-machine
gate. ship-rhai is deprecated (the .rhai workflow was deleted). The Rhai
constraint is eliminated. Remaining ship-py work is consolidated in
`ship-pipeline-open-work-20260809`.

**For external tooling:** orchcore is the most directly applicable library
for the Python orchestrator path, providing phase-level resume, stream
monitoring, and rate-limit recovery out of the box. [UNTESTED] on this
workspace — would need evaluation before adoption.

## Workspace-counterexample check

- **Pre-compute technique:** no counterexample found. The
  [[command-wrapper-pattern-for-workflows]] concept already documents this
  pattern for Rhai's constraint.
- **Agent consolidation:** validated by [[agent-consolidation-in-parallel-workflows]]
  (9→3 agents eliminated rate-limit collisions). No counterexample.
- **Python orchestrator path:** the /ship-py-mandatory-step-gate handoff
  documents the LLM-skip-phase problem (LLM ran detect, jumped to SHIP DONE).
  This is a counterexample for the *enforcement* dimension, not the
  *performance* dimension. The performance advantage of Python-direct
  subprocess is not contested. The enforcement gap needs the state-machine
  gate (TP-01 in the handoff), which is independent of the performance fix.

## Falsifier

This analysis is wrong if:
- The 21-minute runtime was caused by a transient issue (quota exhaustion,
  model outage) rather than structural over-delegation — the handoff
  documents it as a "runaway," which suggests a structural issue, but the
  exact wall-clock breakdown per phase has not been measured.
- Rhai gains subprocess/filesystem access in a future update, eliminating
  the constraint — currently not on any roadmap.
- The pre-compute and consolidation techniques introduce correctness
  regressions (stale git state, race conditions between pre-compute and
  workflow launch) — mitigated by computing state immediately before launch.

## Epistemic debt

- Confidence: 0.82/1.0
- Unverified claims: the ~5-8 min runtime estimate is [INFERENCE] based on
  per-agent cost estimates, not measured. The orchcore applicability is
  [INFERENCE] — not tested on this workspace.
- Downstream dependents: [[ship-pipeline-enforcement-field-solutions-2026]],
  [[grok-build-workflows-rhai-orchestration]], [[code-orchestrates-model-judges-skill-scale]]
- Status: VERIFIED (techniques are field-consensus; estimates are inferred)
