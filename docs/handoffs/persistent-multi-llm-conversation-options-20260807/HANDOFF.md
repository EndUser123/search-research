---
title: "Persistent multi-LLM conversation state: investigate options for cross-model dialogue with memory"
created: 2026-08-07
status: ready-to-implement
assigned_to: unassigned
assigned_at: ""
assigned_by: ""
priority: medium
tags: [multi-llm, conversation-persistence, model-web, cross-model, architecture, research]
---

# Persistent multi-LLM conversation state: investigate options

## Goal

The operator identified a structural limitation: when orchestrating a design dialogue between multiple LLMs (like the `/tp` 3-lens panel or the Codex/Grok design exchange this session), each LLM starts stateless. Previous turns must be manually re-packed and re-sent. This works but is friction-heavy and loses conversational flow. The operator wants to investigate options for making multi-LLM conversations state-persistent so each model can remember prior turns.

## Context

This session demonstrated the problem concretely. The operator asked Codex to critique a model-selection proposal, then asked Grok to critique Codex's critique, then asked Grok again to synthesize. Each exchange required manually passing the previous turn's output as context. If either LLM could maintain conversation history across turns, the dialogue would flow naturally.

The `/model-web` skill already solves part of this: browser-hosted LLMs (ChatGPT, Gemini, Claude) maintain their own conversation history. The `/tp` ensemble protocol uses this — each lens keeps its conversation thread. But the cross-LLM orchestration layer (Grok as orchestrator talking to Codex/Gemini via CLI) is stateless per-turn.

## What was done this session

1. `/tp {3}` panel: spawn lens kept its own state; codex and agy were one-shot (no memory)
2. Codex/Grok design exchange: 3 turns, each manually passed previous turn's content
3. Operator identified this as a structural gap worth solving

## Options identified (research needed to evaluate)

### Option A: `/model-web` conversation persistence (existing capability)

`/model-web` already maintains conversation state in browser-hosted LLMs. Each tab (ChatGPT, Gemini, Claude) keeps its own history. The fusion portal protocol (`fusion2.html`) sends prompts and collects responses from persistent conversations.

**Pros:** already built; uses web subscription quota (free); browser handles state natively.
**Cons:** sequential (not parallel); depends on Chrome DevTools MCP; agy lens is currently broken (jetski permission issue, handed off separately).

**What would need to change for cross-LLM dialogue:** the fusion portal would need a "relay mode" where the orchestrator sends model A's response to model B as a follow-up prompt, maintaining a shared conversation thread across tabs. Currently the portal does one-shot blast/collect, not multi-turn relay.

### Option B: CLI session resume (Codex/agy native capability)

Both Codex and agy support session resume:
- Codex: `codex --resume <session-id>` continues a previous conversation
- agy: sessions are resumable via conversation IDs

**Pros:** native to the CLIs; no new infrastructure; each model remembers its own history.
**Cons:** each model has its OWN conversation memory — they don't share. Model A can't see model B's previous response unless the orchestrator injects it. This solves per-model memory but not cross-model dialogue.

### Option C: API-level relay with persistent conversation store

A relay/proxy that sits between the orchestrator and the models, maintaining a shared conversation store. Each turn from any model is appended to a shared history. When a new model is queried, the relay includes relevant prior turns as context.

Candidate tools (from web research, need evaluation):
- **LiteLLM** — proxy that routes to multiple providers; has conversation memory features
- **llm-relay** (github/ArkNill) — "unified LLM usage management, API proxy, session diagnostics, multi-CLI orchestration" with session history browser
- **RelayFreeLLM** (github/msmarkgu) — RESTful API with persistent conversation history, routes to multiple providers
- **OmniRoute** (github/diegosouzapw) — MIT gateway, 290+ providers, one endpoint

**Pros:** shared conversation state across all models; API-level (stable, not DOM-dependent); works with any OpenAI-compatible provider.
**Cons:** uses API quota (not web subscriptions); new infrastructure to deploy; the "shared history" model can be confusing (model B sees model A's internal reasoning, which may not be desirable).

### Option D: Orchestrator-managed context relay (packet-based)

The orchestrator (Grok) maintains a running "dialogue transcript" file. Each turn:
1. Orchestrator sends prompt to model A with the dialogue-so-far appended
2. Model A responds
3. Orchestrator appends model A's response to the transcript
4. Orchestrator sends prompt to model B with the updated transcript
5. Repeat

This is what happened manually this session. The `/packet` skill already does conversation compression and export.

**Pros:** no new infrastructure; full control over what each model sees; works with any model/CLI/API.
**Cons:** context grows linearly (token cost); manual orchestration; the orchestrator is the bottleneck (sequential by nature).

### Option E: Shared workspace artifact (file-based shared memory)

Both Grok and Codex have filesystem access. A shared markdown file acts as the "conversation memory":
1. Each model reads the file before responding
2. Each model appends its response after responding
3. The file is the persistent state

This is essentially what the `/tp` context-packing does, but made explicit and persistent.

**Pros:** dead simple; both models already have file access; no infrastructure; survives across sessions.
**Cons:** race conditions if both models read/write simultaneously; context grows unboundedly; no automatic compression.

### Option F: GitHub issue / PR as conversation medium

Use a GitHub issue or PR as the shared conversation thread. Each model posts its analysis as a comment. All models read all comments.

**Pros:** persistent, structured, auditable; works async; both models can read/write via `gh` CLI.
**Cons:** heavyweight; GitHub API rate limits; public visibility concerns; not real-time enough for tight design dialogue.

## What needs to happen

1. **Evaluate the candidate tools** (Option C) for fit: do they support the providers we use (OpenAI-compatible, Gemini, MiniMax)? Do they handle conversation state the way we need? Are they deployable on this host?

2. **Prototype a relay-mode extension to `/model-web`** (Option A): the fusion portal already does blast/collect. Adding a "relay" mode that sends model A's response to model B as a follow-up prompt would enable multi-turn cross-LLM dialogue using web subscriptions.

3. **Prototype Option D (orchestrator-managed relay)** as the zero-infrastructure fallback: formalize the manual context-passing into a `/tp relay` mode that maintains the dialogue transcript automatically.

4. **Compare on these axes:**
   - State persistence (does each model remember prior turns?)
   - Cross-model visibility (can model B see model A's responses?)
   - Cost (API quota vs web subscription)
   - Infrastructure required (none / local service / external dependency)
   - Latency (real-time vs async)
   - Context management (compression, summarization, selective inclusion)

## Acceptance criteria

- [ ] Research report comparing Options A-F with tradeoffs and recommendation
- [ ] Prototype of at least one option beyond the current manual approach
- [ ] Recommendation for which option(s) to integrate into `/tp` and `/model-web`

## Evidence

- This session's `/tp {3}` panel: spawn kept state, codex/agy were one-shot
- This session's Codex/Grok design exchange: 3 manual context-passing turns
- Wiki: `[[multi-llm-aggregator-landscape]]` — existing aggregator research
- Wiki: `[[llm-council-and-model-fusion]]` — MoA/fusion patterns
- Web search results: LiteLLM, llm-relay, RelayFreeLLM, OmniRoute (need evaluation)
- `/model-web` SKILL.md: fusion portal protocol (blast/collect, not relay)
- `/packet` SKILL.md: conversation compression and export capability
