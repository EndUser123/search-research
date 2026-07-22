---
title: "Optimal cross-session chain traversal for /aar and /handoff under compaction (Grok Build)"
created: 2026-07-21
source: session-2026-07-21, /www research
tags: [handoff, aar, cross-session, compaction, chain-traversal, grok-build, session-state, durability, do's-and-dont's]
summary: >
  How /aar and /handoff should work under Grok Build to extract insights
  across session chains with compaction. Research base: five-layer handoff
  protocol (dev.to 2026), durable execution for LLM agents (vadim.blog
  2026), cross-session awareness (Medium 2026). The current skills handle
  within-session compaction correctly; cross-session chain traversal is
  the v0.2 gap. The optimal design uses three principles: (1) compress
  along multiple dimensions (facts, narrative, decisions, priorities,
  warnings — not just data dumps), (2) test with real restarts, not
  simulated loads, (3) make handoffs human-readable, not machine-optimized.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/handoff-pre-compact-problems
    type: related
  - target: wiki/concepts/llm-handoff-best-practices
    type: refines
---

# Optimal cross-session chain traversal for /aar and /handoff under compaction (Grok Build)

## Current state (what works, what doesn't)

| Capability | /handoff v0.1 | /aar |
|---|---|---|
| Within-session compaction recovery | ✅ reads `compaction/segment_*.md` via `INDEX.md` | ✅ reads `chat_history.jsonl` + `compaction_checkpoints/*.json`; classifies as `SOURCE_PARTIAL` |
| Cross-session chain traversal | ❌ v0.2 — structural support exists (`parent_handoff_path`, `thread_id`) but no traversal machinery | ❌ binds to one session only |
| Code-backed preprocessing | partial — `list_handoffs.py`, `verify_handoff.py` for drift detection | ✅ full pipeline — `full_preprocessor.py` (22 KB) with 18 Python modules producing 11 packet artifacts |
| Fresh-session actionability | ✅ — the 15 mandatory fields are designed for a cold-start agent | ✅ — the report is written for a reviewer who wasn't present |

**The gap:** both skills handle compaction *within one session*. Neither traverses *across sessions* in a chain. The `parent_handoff_path` field exists structurally but nothing walks it.

## Research base (external evidence)

### The five-layer handoff protocol (dev.to, aureus_c, Jan 2026)

The most actionable framework found. Defines five layers that every handoff should have, drawn from production experience with multi-session AI agents:

1. **State snapshot** — raw facts, typed and validated (current variables, task status)
2. **Narrative context** — 3-5 sentences human-readable, explaining what happened and why
3. **Decision log** — what was decided, deferred, and traded off (prevents re-litigating resolved questions)
4. **Priority queue** — what the next session should do first, second, third (removes cold-start paralysis)
5. **Warnings and gotchas** — institutional knowledge that exists nowhere except in the previous session's working memory

**Mapping to /handoff v0.1:** the 15 mandatory fields cover layers 1-4 well. Layer 5 (warnings/gotchas) is partially captured in "Open questions" and "Risk" but not as a first-class section. **Recommendation: elevate warnings to a mandatory field in v0.2.**

### Four handoff anti-patterns (dev.to, same source)

| Anti-pattern | Symptom | Does /handoff v0.1 avoid it? |
|---|---|---|
| **The Data Dump** | 47KB of nested JSON; next session gets everything and understands nothing | ✅ — 15 mandatory fields enforce structure; agent authors the narrative, not a serializer |
| **The Pointer** | Just a file path, no summary | ⚠️ — `parent_handoff_path` in v0.1 is exactly this (a pointer with no summary). v0.2 must include a narrative excerpt alongside the pointer |
| **The Optimist** | No handoff at all, "the framework handles continuity" | ✅ — /handoff is explicitly invoked; framework doesn't handle continuity |
| **The Archaeologist** | "Check the logs from 14:00-14:30 for context" | ✅ — /handoff cites `event_id`s and `file:line`, but the `source_transcript` field creates archaeology risk if the transcript path goes stale |

### Durable execution patterns (vadim.blog, Jul 2026)

Two approaches to state persistence, relevant to how `/aar`'s preprocessor should evolve:

- **Snapshot checkpointing** (what `/aar` does now): save full context after each event. Simple, low-overhead for short runs. On resume, pick up from the last snapshot. **Current /aar uses this approach via `full_preprocessor.py`.**
- **Journal replay** (event sourcing): record every event, replay the history to rebuild state. More space-efficient for long runs. Requires deterministic replay — which breaks for LLMs (non-deterministic). **Not suitable for /aar unless LLM responses are memoized.**

**Relevant finding for chain traversal:** snapshot checkpointing works for within-session recovery (what /aar does now) but does NOT solve cross-session continuity. For cross-session, the handoff document IS the snapshot — but it must be authored (compressed) rather than mechanically captured.

**Key quote:** "The handoff is where engineering meets epistemology. You're not just passing data — you're passing *understanding*."

### Cross-session awareness (Medium, Jensen Loke, Feb 2026)

Identifies the core architectural constraint: "An LLM agent isn't a traditional program with shared memory. Its 'state' is the context window, built from workspace files at session start. There's no IPC between sessions."

**Two audiences** need cross-session awareness:
1. **Scripts/code** — can query databases, need structured state queries ("what changed since timestamp X?")
2. **The LLM agent** — reads files, needs human-readable context

**Mapping to Grok Build:** `/aar` serves audience 1 (code queries via preprocessor). `/handoff` serves audience 2 (human-readable context for the LLM). The optimal design keeps both — they serve different consumers and should not be merged.

## Do's and don'ts (distilled from research + current implementation)

### Do's

1. **DO compress along multiple dimensions.** The five-layer protocol works because facts, narrative, decisions, priorities, and warnings each capture something the others miss. /handoff's 15 fields cover 4 of 5 layers well; add explicit warnings as a first-class field in v0.2.

2. **DO make handoffs human-readable, not machine-optimized.** JSON with clear keys and plain-language narrative. When something goes wrong (and it will), you want to `cat` the handoff and immediately understand the last known state. The /handoff v0.1 design is correct here — it's Markdown for an LLM, not a binary blob.

3. **DO test with real restarts.** Write the handoff. Start a fresh session. Did the fresh agent pick up where the prior left off? Not "did it load the file" — did it actually *continue the work* correctly? Most handoff bugs only surface under real restart conditions (stale file handles, cached state, race conditions between write and next-session read). The /handoff falsifier captures this: "if a fresh session cannot act on it without re-deriving, the design failed."

4. **DO version your schema.** /handoff v0.1.1 already does this (`accurate_as_of_head`, `source_transcript` added via `/handoff migrate`). Continue versioning — the format WILL evolve, and a version field prevents silent misinterpretation.

5. **DO use redundancy for continuity.** Primary: structured handoff. Secondary: state.json or wiki concepts. Tertiary: human-readable journal. If any one channel fails, others provide enough to recover. /handoff + /wiki + /aar's durable artifacts form a three-channel system. Don't collapse them into one.

6. **DO keep /aar's code-backed preprocessor.** The 18-module deterministic pipeline is the right architecture. Code handles facts, counts, ordering; the LLM handles causal interpretation. This separation prevents the LLM from fabricating claims about what happened in the transcript.

7. **DO label source completeness honestly.** /aar's `SOURCE_PARTIAL` classification under compaction is correct. Don't upgrade to `SOURCE_COMPLETE` just because the segments are available. The segments are recovery-grade, not primary-grade.

### Don'ts

1. **DON'T treat `parent_handoff_path` as chain traversal.** It's a pointer. Without narrative context alongside it, it's "The Pointer" anti-pattern. v0.2 must include a narrative excerpt or summary when following the pointer.

2. **DON'T collapse /aar and /handoff into one skill.** They serve different audiences (code vs. LLM) and different time horizons (retrospective vs. forward-looking). The research is clear: two channels for two consumers beats one channel trying to serve both.

3. **DON'T rely on transcript paths for durability.** /handoff's `source_transcript` field is convenience, not load-bearing. Transcripts get compacted, cleaned, or moved. The handoff's content must stand on its own without the transcript resolving forever. (Already documented in /handoff SKILL.md — this is correct.)

4. **DON'T build cross-session chain traversal as a single mega-pipeline.** The durable-execution research shows that snapshot + handoff is simpler and less error-prone than journal replay for the scale we're at (single-node, single-operator, sessions of hours not days). Don't reach for Temporal-like machinery until the simple version breaks.

5. **DON'T use session length or compaction count as proxies for data quality.** This mirrors the "fabricated session-state constraints" rule. A compacted session's data is recovery-grade (`SOURCE_PARTIAL`), but that's a statement about evidence quality, not about whether the session was "too long." Don't refuse to AAR a long session because "it's probably degraded" — run the preprocessor and let it classify.

6. **DON'T silently fail handoff loading.** The dev.to research: "The most dangerous failure mode isn't a crash — it's a loader that runs without errors but doesn't actually populate the agent's context." /handoff v0.1 doesn't have a loader (the agent reads the file directly), but v0.2 chain traversal MUST verify that the prior session's context actually landed in the new session's working memory. The test: "did the agent explicitly reference handoff data in its first action?"

7. **DON'T optimize handoff size prematurely.** The dev.to research: "Redundancy beats optimization." Three small files (handoff + wiki concept + state snapshot) beat one compressed file. The cost of a confused agent re-doing work far exceeds the cost of writing three small files.

## Recommended v0.2 design (for /handoff chain traversal)

Based on the research, the optimal v0.2 design for cross-session chain traversal:

1. **`/handoff continue <path>`** reads the prior handoff, extracts its five layers (state, narrative, decisions, priorities, warnings), and presents them to the new session as structured context.

2. **The prior handoff's `source_transcript` is followed ONLY if:**
   - The transcript path still resolves
   - The new session needs detail beyond what the handoff captures
   - The operator explicitly authorizes transcript reading (it's expensive)

3. **A "handoff chain health check"** verifies at chain-follow time:
   - `accurate_as_of_head` of each link vs current HEAD (drift detection)
   - File paths cited in each link still exist (citation verification)
   - The chain is acyclic (no infinite loops)

4. **The new session's first action** must explicitly reference the inherited handoff context. If it doesn't, the load failed silently (the dev.to anti-pattern).

5. **/aar integration:** when `/aar` runs on a session that has a `parent_handoff_path`, it reads the prior handoff as additional evidence context — but labels it as `from_prior_session: true` to prevent treating it as current-session evidence.

## Source

- `/www` research run, session 2026-07-21
- dev.to "Building Reliable State Handoffs Between AI Agent Sessions" (aureus_c, Jan 2026) — five-layer protocol, four anti-patterns, five production lessons
- vadim.blog "Durable Execution for LLM Agents: The Complete Guide" (Jul 2026) — snapshot vs journal, idempotency, park-run pattern, decision framework by agent type
- Medium "Cross-Session Awareness for LLM Agents" (Jensen Loke, Feb 2026) — two-audience problem (code vs LLM), no IPC between sessions
- Existing wiki: [[handoff-pre-compact-problems]] (skill routing, not chain traversal — different topic but related)
- Existing wiki: [[llm-handoff-best-practices]] (refines with the five-layer protocol)

## Auto-related

- [[exemption-logic-as-conflict-signal]]
- [[handoff-pre-compact-problems]]
- [[grok-build-plan-mode-structured-thinking]]
- [[llm-handoff-best-practices]]

