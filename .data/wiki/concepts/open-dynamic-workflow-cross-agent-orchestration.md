---
title: "Open Dynamic Workflows (ODW): cross-agent workflow portability beyond vendor-locked runtimes"
created: 2026-08-04
updated: 2026-08-04
source: session-2026-08-04 (/www research)
sources:
  - https://github.com/xz1220/open-dynamic-workflows (94★, 117 commits, MIT, v0.4.0)
  - https://xz1220.github.io/open-dynamic-workflows/
  - https://github.com/lswank/grok-workflows (2★, Grok-specific variant)
  - https://github.com/travisliu/open-dynamic-workflow (alternative ODW)
  - https://github.com/ChaosRealmsAI/open-dynamic-workflow (third ODW reimplementation)
  - https://github.com/anthropics/claude-code/issues/66023 (cost: 46 Opus subagents = ~3M tokens)
  - https://www.mindstudio.ai/blog/how-to-control-token-costs-claude-code-dynamic-workflows
  - https://code.claude.com/docs/en/workflows
  - https://x.ai/news/workflows
  - https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/
  - https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost
tags: [workflow, dynamic-workflow, orchestration, fan-out, cross-agent, portability, codex, claude-code, gemini, qwen, kimi, grok-build]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Open Dynamic Workflows (ODW) is a TypeScript CLI runtime that makes Claude
  Code's dynamic-workflow dialect (JavaScript scripts with `agent()`,
  `parallel()`, `pipeline()`) portable across multiple coding-agent CLIs —
  Codex, Claude Code, Gemini, Qwen, Kimi, and custom agents. Three independent
  reimplementations exist (xz1220, travisliu, ChaosRealmsAI); xz1220 is the
  most mature (94★, 275 tests, web dashboard with live DAG visualization).
  ODW's value proposition is cross-agent portability: write once, run on any
  CLI. For Grok Build, which already has native Rhai workflows, ODW is
  complementary (not redundant) when orchestrating across mixed-agent fleets.
---

# Open Dynamic Workflows: cross-agent orchestration portability

## What it is

Open Dynamic Workflows (ODW) is an open-source TypeScript CLI runtime that
takes Claude Code's dynamic-workflow dialect — JavaScript scripts that
orchestrate subagents via `agent()`, `parallel()`, `pipeline()` — and makes
them **portable** across multiple coding-agent CLIs. A script written for
Claude Code runs unchanged on Codex, Gemini, Qwen, Kimi, or any custom CLI.

The core problem ODW solves: Claude Code's dynamic workflows are locked to
Claude Code's private runtime. They only execute inside Claude Code sessions,
for Claude Code itself. ODW makes the **same scripts** standalone artifacts
that can be versioned, shared, and run on any agent CLI — in the background,
with live observability.

## Decision context: why this research was needed

The operator's fleet uses multiple coding agents (Grok Build native workflows,
Claude Code workflows, Codex, etc.). The question: is there a unified workflow
runtime that lets workflow scripts be **portable** across these agents rather
than locked to each one's proprietary runtime? This matters because:

1. **Script portability** — a workflow written for Claude Code should be
   reusable when the operator switches to Codex or Grok Build
2. **Cross-agent orchestration** — the ability to have different agents
   (Codex implements, Claude reviews, Gemini verifies) in a single workflow
3. **Observability** — live DAG visualization of in-flight runs, independent
   of any host agent's TUI

## The three ODW implementations

| Project | Stars | Language | Key differentiator | Status |
|---------|-------|----------|-------------------|--------|
| **`xz1220/open-dynamic-workflows`** | 94 | TypeScript/Node | Web dashboard, Chat Host, `validate()` primitive, 275 tests | Most mature; v0.4.0 (2026-06-11) |
| `travisliu/open-dynamic-workflow` | — | — | "Turns repeatable agent tasks into workflow scripts" | Alternative implementation |
| `ChaosRealmsAI/open-dynamic-workflow` | — | — | Feature-for-feature Claude Code match + git-worktree isolation, deterministic resume | Third reimplementation |

Plus a related Grok-specific project:

| `lswank/grok-workflows` | 2 | JavaScript (dependency-free) | 9 ready harnesses, built on Grok headless mode | Small; last push 2026-06-07 |

**xz1220/open-dynamic-workflows is the reference implementation.** The rest
of this concept focuses on it.

## Architecture

```
odw (CLI) → runtime (background worker + run directory)
              └─ loads & transforms → workflow script (.js, Claude dialect)
                                      └─ injected primitives → scheduler (async cap + agent backstop)
                                          agent() → bridge → adapters → real CLI subprocess
                                                      ├─ workspace (isolation + diff)
                                                      └─ schema (validate / retry)
```

**Key design decisions:**
- **No threads** — the engine is async TypeScript. `parallel()` is `Promise.all`,
  `pipeline()` is per-item async chains. Concurrency cap: `min(16, cpus-2)`.
- **Zero runtime dependencies** — the binary is self-contained (~110MB on disk,
  ~35MB gzipped download). Build-only deps are esbuild + postject.
- **Adapter pattern** — each coding-agent CLI is an adapter (Codex, Claude Code,
  Gemini, Qwen, Kimi, custom). Switching agents = switching adapters.
- **Claude Code dialect complete** — `export const meta` + injected `agent` /
  `parallel` / `pipeline` / `phase` / `log` / `args` / `budget` / `workflow`
  globals (nested workflows included), with top-level `await` and `return`.
  Scripts written for Claude Code run here as-is and vice versa.

## The primitives

| Primitive | Role |
|-----------|------|
| `agent(prompt, opts?)` | Run one coding agent on a subtask. Returns text or validated object (when `opts.schema` set). |
| `parallel(thunks)` | Run batch concurrently, wait for all (barrier). Failed thunk → `null`. |
| `pipeline(items, ...stages)` | Stream items through stages independently (no barrier). |
| `phase(title)` / `log(msg)` | Group progress / emit progress line. |
| `schema` (JSON Schema) | Typed output contract for `agent`; validated and retried until conformant. |
| `args` | Workflow input, injected verbatim. |
| `budget` | `{ total, spent(), remaining() }` — scale depth to token target. |
| `workflow(ref, args?)` | Run another workflow inline (one level deep). **ODW extension** beyond Claude Code. |
| `validate(source)` | Compile-check a candidate workflow without executing it. **ODW extension**. |

## How ODW differs from existing approaches

| Feature | Claude Code Workflows | Grok Build Workflows | ODW |
|---------|----------------------|---------------------|-----|
| Scripting language | JavaScript | **Rhai** | JavaScript (Claude dialect) |
| Agent lock-in | Claude Code only | Grok Build only | **Any CLI (Codex, Claude, Gemini, Qwen, Kimi, custom)** |
| Background runs | Yes (in-session) | Yes (native tool) | Yes (detached worker + run directory) |
| Live DAG dashboard | No (TUI only) | No (TUI + `/workflows` panel) | **Yes (`odw serve` web dashboard)** |
| Cross-agent review | No | No | **Yes (codex-claude-loop.js pattern)** |
| Schema validation | No | No | **Yes (JSON Schema validate + retry)** |
| Zero dependencies | No (Claude Code) | No (Rhai runtime) | **Yes (zero runtime deps)** |
| Resume | Partial | Yes (journaling) | Roadmap (v1.5+) |
| Worktree isolation | No | No | No (roadmap) |

## Applicability to our workspace

### What ODW would give us that we don't have

1. **Cross-agent orchestration** — run a single workflow where Codex implements,
   Claude reviews, and Gemini verifies. Currently each agent's workflow system
   is siloed to that agent.
2. **Live web dashboard** — `odw serve` provides real-time DAG visualization
   with per-agent cards showing adapter + elapsed time. Neither Grok Build nor
   Claude Code offer a web-based live view.
3. **Schema-validated agent outputs** — JSON Schema contracts on `agent()`
   calls with automatic retry until conformant. This eliminates the "agent
   returned malformed JSON" failure mode.
4. **Portable workflow artifacts** — workflows as `.js` files that can be
   version-controlled, shared across teams, and run by any agent.

### What ODW does NOT replace

1. **Grok Build native workflows** — for Grok-only work, Rhai workflows are
   the native, lower-overhead path. ODW shells out to CLIs; native Rhai
   workflows have tighter integration with the Grok Build session lifecycle.
2. **Our skill system** — `/go`, `/tp`, `/review`, etc. are Grok-native
   orchestration. ODW is a general-purpose workflow runtime, not a
   reasoning-layer skill system.
3. **Single-agent interactive work** — ODW is for batch fan-out, not
   interactive coding sessions.

### Applicability gate (Round 3.25)

| Dimension | Research context | Our context | Applies? |
|-----------|-----------------|-------------|----------|
| System openness | Cross-CLI orchestration | Multi-agent fleet (Grok + Codex + Claude) | **Yes** — we already run mixed-agent fleets |
| Model homogeneity | Designed for mixed agents | We have multiple coding-agent CLIs installed | **Yes** — PI, OpenCode, Codex CLI all configured |
| Evidence type | Batch-fan-out workflows | Our /go, /review patterns are batch-shaped | **Partially** — some work is interactive, not batch |
| Ground truth | Schema-validated outputs | We use structured outputs (JSON, markdown) | **Yes** — schema validation would help |
| Task domain | Code migration, research, review | Same domains | **Yes** |

**Verdict:** ODW applies to our cross-agent orchestration needs (4/5 dimensions
align). The partial mismatch (interactive vs batch) is inherent to any workflow
system — it doesn't invalidate ODW's value for batch work.

## Known limitations and pain points

### Cost (the dominant constraint)

Cost scales linearly with parallelism. Each `agent()` call invokes a full
coding-agent CLI session. Reported costs:

- **46 Opus subagents in one invocation = ~3M tokens** ([GitHub Issue #66023](https://github.com/anthropics/claude-code/issues/66023))
- "Dynamic workflows is awesome but crazy expensive" — Reddit r/ClaudeCode
- System prompts are charged as input tokens on every call: a 2,000-token
  system prompt repeated across 20 agent calls = 40,000 tokens overhead alone
- Running 10 parallel agents consumes token quota 10× faster than a normal session

**Implication for our fleet:** ODW's value is highest when using **free-tier**
models (NIM, Zen, OpenRouter free) or **dedicated-key** providers (Cohere,
NVIDIA) that don't share the main session's quota. This aligns with our
[[dedicated-quota-first-dispatch-routing]] strategy — the models with
separate quota buckets are exactly the ones that make ODW cost-effective.

### Open issues (practitioner signal)

| Issue | Description | Impact |
|-------|-------------|--------|
| [#23](https://github.com/xz1220/open-dynamic-workflows/issues/23) | Codex adapter cannot reliably run MCP write workflows requiring tool approval | Cross-agent workflows involving MCP tools may fail on Codex |
| [#24](https://github.com/xz1220/open-dynamic-workflows/issues/24) | Ultra-mode research runs difficult to recover from when lanes stall | Long-running research workflows can hang |
| [#31](https://github.com/xz1220/open-dynamic-workflows/issues/31) | Feature request: `runCmd`/`shell` primitive for direct command execution | Currently workflows can only dispatch agents, not shell commands |
| [#6](https://github.com/xz1220/open-dynamic-workflows/issues/6) | Clarify Claude workflow primitive compatibility gaps | Not all Claude Code primitives are documented as implemented |

### Missing features (vs. mature systems)

- **No resume/journaling** — a crashed run can't be resumed from where it left
  off (roadmap for v1.5+)
- **No git-worktree isolation** — agents share the working directory unless
  manually isolated
- **No deterministic replay** — no `Date.now`/`Math.random` sandbox for
  reproducibility (roadmap)

## Disconfirmation pass

**Claim: ODW makes workflows truly portable across agents.**
- ⚠️ **Qualified:** portability works for the workflow *script*, but each
  adapter has different capabilities (e.g., Codex can't reliably do MCP write
  workflows). "Same script runs everywhere" is aspirational, not guaranteed.
- **Source:** GitHub Issue #23, #6.

**Claim: ODW is better than Claude Code's built-in workflows.**
- ⚠️ **Contested:** ODW adds portability + observability + schema validation,
  but loses in-session integration and adds a CLI installation dependency.
  For Claude-only work, the built-in tool is simpler. ODW's advantage is
  *only* relevant when cross-agent orchestration is needed.

**Claim: ODW solves the cost problem of dynamic workflows.**
- ❌ **Refuted:** ODW does not address cost. Cost is linear with the number
  of agent calls, regardless of runtime. The cost issue is inherent to the
  parallel-subagent pattern, not to the runtime. ODW's zero-runtime-deps
  claim refers to the *engine's* dependencies, not the agent API costs.

## Relationship to existing wiki

- [[grok-build-workflows-rhai-orchestration]] — Grok Build's native Rhai-based
  workflow system. ODW is complementary: use Rhai for Grok-native work, ODW
  when cross-agent orchestration is needed.
- [[claude-code-dynamic-workflows]] — Claude Code's built-in dynamic workflows.
  ODW reimplements this dialect for cross-agent portability.
- [[dedicated-quota-first-dispatch-routing]] — our dispatch routing strategy.
  ODW's cost profile makes dedicated-quota models the right choice for
  fan-out workflows.
- [[subprocess-run-timeout-deadlock-windows]] — ODW's async engine handles
  subprocess timeout internally, but Windows-specific subprocess issues may
  still surface in adapters.

## Falsifier

This concept is wrong if:
1. ODW's adapter compatibility gaps prove unfixable (Claude dialect ≠ truly
   portable across agents in practice)
2. Cross-agent orchestration is never needed in practice — if each agent's
   native workflow system is sufficient and cross-agent work is always done
   manually
3. The cost of CLI-per-agent overhead makes ODW impractical compared to
   direct API calls for all but trivial workflows

## Recommendations

1. **Evaluate ODW for cross-agent research workflows.** When `/tp` or `/review`
   needs multi-model perspectives, ODW's `codex-claude-loop.js` pattern (two
   rival CLIs in turn-based review) is directly applicable. Confidence: MEDIUM.
2. **Do NOT replace Grok Build native workflows.** Rhai workflows have tighter
   session integration for Grok-only work. ODW adds a CLI dependency without
   adding value for single-agent runs. Confidence: HIGH.
3. **Use ODW's schema-validation pattern as inspiration.** The JSON Schema
   contract on `agent()` calls with automatic retry is a pattern our own
   skill system could adopt for structured outputs from subagents. Confidence: HIGH.
4. **Monitor ODW's resume/journaling roadmap.** If implemented, ODW becomes
   viable for long-running migrations (hours), which neither Grok Build nor
   Claude Code handle well today. Confidence: MEDIUM.
