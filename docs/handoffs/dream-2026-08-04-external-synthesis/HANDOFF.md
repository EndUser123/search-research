---
thread_id: dream-2026-08-04-external-synthesis
parent_handoff_path: P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md
current_session_id: 019fd01e-7831-7ac3-baeb-a4a57d06c771
current_terminal_id: grok-main
produced_at: 2026-08-04T22:45:00-06:00
last_updated_by: 019fd01e-7831-7ac3-baeb-a4a57d06c771
last_updated_at: 2026-08-04T22:45:00-06:00
status: closed
handoff_type: investigation-followup
accurate_as_of_head: 2e342077212641649ff62ba98fcf0820f330681c
---

# Handoff — /dream 2026-08-04 unresolved proposals (external synthesis follow-on)

## 1. Objective

Route the unresolved proposals from `/dream` run 2026-08-04 (output: `P:/docs/dreams/2026-08-04-dream-external-synthesis.md`) to a durable handoff so a future session can pick them up without re-discovering the corpus.

**Scope:** 4 deferred Pass 1 candidates + 1 Pass 2 contradiction + 1 Pass 5 partial-trigger note. Total: 6 items.

## 2. Status

CLOSED — all items resolved 2026-08-04 by session 019fce56:

- **Contradiction 1 (/all retirement):** RESOLVED — reframed as forward-looking guardrail (option 1). Commit `d2eb172`.
- **Candidate 1 (cross-model routing):** ALREADY CAPTURED in `chatgpt-web-searching-cross-platform-research-runtime.md` (Downloads) + `research-system-novel-ideas-external-synthesis.md` (wiki). No standalone concept needed.
- **Candidate 2 (browser adapter):** ALREADY CAPTURED in `chatgpt-deep-research-help.md` (Downloads) + `/model-web` SKILL.md (live skill). No standalone concept needed.
- **Candidate 3 (compostable skill graph):** ALREADY CAPTURED in `perplexity-compostable-skill-graph-improvement-cycle.md` (Downloads) + `sdlc-command-cognitive-jobs-taxonomy.md` (wiki). No standalone concept needed.
- **Candidate 4 (kbask/Graphify):** ALREADY CAPTURED in `perplexity-kb-designing-unified-knowledge-research-system.md` (Downloads) + `persistent-kb-architecture-model-sunset-survivability.md` (wiki). No standalone concept needed.
- **Pass 5 (SKILL.md cognitive-job descriptions):** DEFERRED — high-touch edit (80+ files), not actionable in this session.

## 3. Producing context

- **Dream invocation session:** 019fd01e-7831-7ac3-baeb-a4a57d06c771 (the session running this `/dream`)
- **Source handoff:** `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md` (the sibling session that wrote the 3 wiki concepts in commit `2e5476e`)
- **Workspace state at write time:** git HEAD `2e342077212641649ff62ba98fcf0820f330681c` on `P:/`
- **Dream output:** `P:/docs/dreams/2026-08-04-dream-external-synthesis.md` (228 lines, written 2026-08-04)

## 4. Proposals (copied verbatim from dream output)

### 4.1 — Candidate 1: Cross-model second-opinion routing policy (Pass 1, DEFERRED)

**Pattern:** when primary research providers (ChatGPT, Perplexity web search) fail or rate-limit, the research pipeline should fail open to Grok Build's local fleet rather than aborting. Converts provider outages from hard stop to graceful degradation.

**Receipts:**
- `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md:107`
- `P:/.data/www-ledger/deep-research-systems.md:18`
- `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md:47`

**Status:** below 2-instance floor. Needs 1+ independent handoff referencing cross-model research failover to clear auto-promotion.

### 4.2 — Candidate 2: Browser adapter architecture (Pass 1, DEFERRED)

**Pattern:** three viable approaches (Chrome DevTools MCP, headless browser with isolated profile, direct browser extension) for browser-based research adapters. Choice has survivability and detection-evasion implications.

**Receipts:**
- `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md:108`
- `P:/.data/wiki/concepts/chrome-acp-grok-build-agentic-clis.md`
- `P:/.data/wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md`

**Status:** below 2-instance floor. Two related concepts cover sub-areas; a synthesis concept would merge or extract a "when to use which adapter" decision rule.

### 4.3 — Candidate 3: Compostable skill graph lifecycle (Pass 1, DEFERRED)

**Pattern:** extend `build_skill_graph.py` to a semantic capability graph with explicit improvement-cycle contract (stale capabilities trigger re-research, dead capabilities get composted).

**Receipts:**
- `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md:109`
- `P:/.data/wiki/concepts/capability-node-architecture.md`
- `P:/.data/wiki/concepts/design-graphs-solution-graphs-value-for-ai-agent-fleet.md:64`

**Status:** below 2-instance floor.

### 4.4 — Candidate 4: kbask / Graphify toolchain evaluation (Pass 1, DEFERRED)

**Pattern:** benchmark kbask and Graphify against current `qmd` + `build_skill_graph.py` + FTS5 stack. High-confidence-but-unsourced claims from NotebookLM transcripts.

**Receipts:**
- `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md:110`
- `P:/docs/handoffs/agentmemory-evaluation-20260727/HANDOFF.md` (method template)
- `P:/.data/wiki/concepts/claude-code-automation-capabilities.md:23` (Graphify claims, 5+ unsourced NotebookLM sources)

**Status:** below 2-instance floor. Structural fix: run the `agentmemory-evaluation-20260727` method against kbask/Graphify; positive signal becomes the second receipt.

### 4.5 — Contradiction 1: `/all` retirement recommendation (Pass 2)

**Issue:** `sdlc-command-cognitive-jobs-taxonomy.md:105` recommends retiring `/all`. No `/all` command exists in the catalog or in `~/.grok/skills/`. The recommendation targets a non-existent command.

**Resolution options:**
1. Treat as a forward-looking guardrail — keep recommendation, add frontmatter note that `/all` does not currently exist
2. Soften the language — change "should be retired" to "should not be introduced"
3. Drop the recommendation entirely

**Recommendation:** option 1 (forward-looking guardrail with frontmatter note).

### 4.6 — Pass 5 partial-trigger note: cognitive-job definitions in SKILL.md descriptions

**Trigger:** `sdlc-command-cognitive-jobs-taxonomy.md:113-114` recommends that "the cognitive job definitions should appear in SKILL.md descriptions so the `/ask` router can match user intent to the right cognitive job."

**Status:** partial trigger — single wiki concept cites this technique, no AAR or /tp notice reinforces it, the change requires reviewing all 80+ SKILL.md files (high-touch edit), operator did not flag as priority.

**Routed to handoff for operator decision** rather than proposing a specific edit.

## 5. Acceptance criteria

A future session picks up this handoff. Operator decides:

- For each Pass 1 candidate (4 items): **wait for independent corroboration** OR **promote as exception** OR **drop as out-of-scope**
- For Pass 2 Contradiction 1: choose resolution option 1, 2, or 3 (recommended: 1)
- For Pass 5 partial-trigger: **decline** (defer the SKILL.md description update to a dedicated session) OR **commission a sweep session** to add cognitive-job definitions to all SKILL.md descriptions

## 6. Hard constraints

- **Auto-promotion forbidden.** All 4 Pass 1 candidates are below the 2-instance floor. Promotion requires either operator explicit authorization OR a new handoff referencing the same idea as independent corroboration.
- **Contradiction 1 resolution is a wiki edit.** Operator decides; the change should preserve the cognitive-job taxonomy (the load-bearing claim) while fixing the `/all` retirement recommendation.
- **Pass 5 SKILL.md sweep is high-touch.** A single sweep could touch 80+ files. Operator should not authorize without scoping the change (which skills first, which cognitive job definitions, how to detect drift).

## 7. Cross-reference couplings

- **Source handoff:** `P:/docs/handoffs/downloads-kb-research-conversations-extracted-20260804/HANDOFF.md` (§11 enumerates these 4 discretionary items)
- **Dream output:** `P:/docs/dreams/2026-08-04-dream-external-synthesis.md` (this handoff's source document)
- **Operator-named concepts (already in wiki, not deferred):**
  - `P:/.data/wiki/concepts/persistent-kb-architecture-model-sunset-survivability.md`
  - `P:/.data/wiki/concepts/sdlc-command-cognitive-jobs-taxonomy.md`
  - `P:/.data/wiki/concepts/research-system-novel-ideas-external-synthesis.md`

## 8. Resumption protocol

When a future session picks this up:

1. Read `P:/docs/dreams/2026-08-04-dream-external-synthesis.md` in full to understand the dream output context.
2. Read each candidate's source handoff line + source conversation reference to ground the proposal.
3. For Pass 1 candidates: check whether any new handoffs in the meantime reference the same idea (would push the candidate over the 2-instance floor). If yes, run `/wiki write` to promote. If no, surface the choice to the operator again.
4. For Pass 2 Contradiction 1: apply the operator's chosen resolution via direct edit to `sdlc-command-cognitive-jobs-taxonomy.md`.
5. For Pass 5: if operator commissions the SKILL.md sweep, write a separate design handoff that scopes which skills to update first and how to detect drift.

## 9. Suggested next invocation

`/wiki update sdlc-command-cognitive-jobs-taxonomy.md` (to apply the chosen resolution for Contradiction 1) OR `/handoff review dream-2026-08-04-external-synthesis` (to triage the 4 deferred candidates).

## 10. Changelog

- 2026-08-04T22:45Z — Initial handoff written by /dream run 2026-08-04 (this session).
- 2026-08-05T05:10Z — CLOSED by session 019fce56. All 4 deferred candidates already captured in Downloads files + wiki concepts. Contradiction 1 resolved (commit d2eb172). Pass 5 deferred.