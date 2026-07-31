---
title: "Execution Path Comparison: spawn_subagent vs OpenCode vs PI vs CLI tools"
created: 2026-07-30
source: session-20260730
tags: [execution-path, spawn, opencode, pi, agy, codex, mmx, model-selection, reference]
summary: >
  Four execution paths for offloading work from the orchestrator, each with
  different model control, overhead, and capability profiles. The orchestrator
  should pick the path based on task type, not default to spawn_subagent.
  PI has full tool support (read, bash, edit, write) — earlier claim that it
  "can't chain operations" was wrong.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Operator directive, session 20260730
  - ~/.grok/AGENTS.md Nemotron routing policy
relations:
  - target: wiki/concepts/role-by-role-delegation-orchestrator-vs-subagent.md
    type: complements
  - target: wiki/concepts/delegation-decision-rule-context-dependency.md
    type: extends
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: extends
---

# Execution Path Comparison: spawn_subagent vs OpenCode vs PI vs CLI tools

## Decision context

Session 20260730 explored why and when to use each execution path for
delegating work off the orchestrator. The operator corrected several
assumptions (PI can chain operations; Zen is a provider not a model; the
difference between paths is overhead + model access, not capability).

## The four paths

| Path | Model control | Context overhead | Tools | MCP | Best for |
|------|--------------|-------------------|-------|-----|----------|
| `spawn_subagent` | Explicit `model=` param | ~26K AGENTS.md injection | All Grok tools | No (MCP not inherited) | Read-only exploration, research with DDG/grep |
| `opencode run --model=X` | `--model` flag | Owns context management | read, bash, edit, write + MCP | Yes (full MCP) | Write-capable implementation, tool-rich tasks |
| `pi` (PI CLI) | Model group config (`groupOrder`) | ~200 tokens system prompt | read, bash, edit, write | No (not documented) | Mechanical/reasoning one-shots, minimal overhead |
| `agy` / `codex` / `mmx` | Per-CLI config | Per-CLI own context | Per-CLI toolset | Per-CLI | Cross-model second opinions (diversity is the product) |

## PI vs OpenCode — the real tradeoff

| Factor | PI CLI | OpenCode CLI |
|--------|--------|-------------|
| System prompt overhead | ~200 tokens | ~26K tokens |
| Tools | read, bash, edit, write (full chain capability) | read, bash, edit, write + MCP |
| Models | NVIDIA (Nemotron, DiffusionGemma) + MiniMax, GLM, Mimo via group config | Multi-provider (Zen, Go, MiniMax, Z.ai, any OpenAI-compatible) |
| Built-in routing | `groupOrder` cascade (minimax → zai → nvidia-nim) | WorkWeave-compatible |
| MCP servers | Not documented in help | Full MCP support |
| Best for | Pure inference passes, mechanical bulk, one-shot reasoning | Multi-step implementation with tool access |

**Correction from this session:** PI CAN chain operations. It has read, bash,
edit, write tools plus sessions (`--continue`, `--resume`, `--session`). The
earlier claim "PI can't chain operations" was wrong — I conflated "lighter
system prompt" with "can't do sequential operations."

## When to use each path

| Task type | Path | Why |
|-----------|------|-----|
| Read-only exploration (search, scan, summarize) | spawn_subagent (explore type) | Fast, native, no context overhead for read-only |
| Write-capable implementation (write code, edit files) | opencode run or codex | Avoids serde bug, full model choice, tool access |
| Cross-model second opinion | /agy, /codex, /mmx skills | Already built, model-aware, separate quota |
| Mechanical bulk (format, extract, classify) | pi or mmx text chat | Minimal overhead, free-tier models |
| Deep reasoning / critique | spawn_subagent with reasoning pool | Needs full Grok context for /tp-style work |

## Operator directive (from AGENTS.md)

> Nemotron routing policy: preference order is PI CLI or opencode CLI →
> OpenRouter (last resort). For model-routing spawns: PI preferred (~200
> tokens system-prompt overhead, faster). For tool-rich spawns: opencode
> preferred (broader features).

## What this means for our workspace

- Don't default to spawn_subagent reflexively. Pick the path based on task type.
- PI is the lowest-overhead path for mechanical work (200 tokens vs 26K).
- OpenCode is the right path when tools or MCP servers are needed.
- CLI tools (agy, codex, mmx) are for cross-model diversity, not general delegation.
- The spawn gate covers spawn_subagent only — CLI tool model selection is governed by their respective skills and the operator directive.

## Falsifier

This comparison is wrong if:
- PI's lower overhead doesn't translate to measurably better outcomes for
  mechanical tasks (the 200 vs 26K token difference may not matter at PI's
  task scale)
- OpenCode's MCP support proves unreliable on Windows for the tasks we
  actually delegate to it

## Receipts

- PI help output: `pi --help` confirms read, bash, edit, write tools + `--continue`, `--resume`, `--session` flags (session 20260730)
- OpenCode help: `opencode --help` confirms v1.2.27 available (session 20260730)
- AGENTS.md: Nemotron routing policy section (read during session 20260730)
- Operator correction: "PI can't chain operations" was wrong (session 20260730)

## Related concepts

- [[role-by-role-delegation-orchestrator-vs-subagent]] — which roles delegate and which stay on orchestrator
- [[delegation-decision-rule-context-dependency]] — when to delegate at all (context-dependency rule)
- [[execution-path-based-model-routing-grok-build]] — the three-layer quota-aware architecture
