---
title: "Cross-session transcript mining for continuous improvement — ecosystem survey and workspace gap"
created: 2026-07-29
source: session-019fa276 (/www research on continuous improvement cycles)
sources:
  - external: https://github.com/giannimassi/agent-retro (giannimassi, 2026)
  - external: https://github.com/kayba-ai/recursive-improve (kayba-ai, 2026)
  - external: https://github.com/Dicklesworthstone/cass_memory_system (Dicklesworthstone, 2026)
  - external: https://github.com/bradtaylorsf/alpha-loop (bradtaylorsf, 2026)
  - external: https://addyosmani.com/blog/self-improving-agents/ (Osmani, Jan 2026)
  - external: https://www.langchain.com/blog/improving-agents-is-a-data-mining-problem (LangChain, 2026)
  - external: https://www.langchain.com/blog/introducing-langsmith-engine (LangChain, 2026)
  - external: https://arxiv.org/abs/2310.01798 (Huang 2024, "LLMs Cannot Self-Correct Reasoning Yet")
  - external: https://lilianweng.github.io/posts/2026-07-04-harness/ (Weng 2026, harness engineering)
  - external: https://www.typedef.ai/resources/extract-insights-chat-logs-conversations-using-semantics (Typedef, 2026)
tags: [transcript-mining, continuous-improvement, self-improvement, session-chain, obligation-tracking, agent-retro, cass-memory, recursive-improve, harness-engineering, survey]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  The ecosystem has converged on a 3-layer architecture for agent
  self-improvement: episodic (raw transcripts) → working (summaries/friction
  reports) → procedural (rules/obligations/playbooks). Four repos implement
  parts of this pipeline: agent-retro (single-session friction analysis),
  recursive-improve (trace mining + overnight improvement loop), cass-memory
  (cross-session/cross-agent 3-layer memory system), and alpha-loop (learn→improve
  step in dev loop). NO tool walks the full session chain to extract all open
  action items and unrealized opportunities. Our workspace has all three layers
  (transcripts at ~/.grok/sessions/, /aar for analysis, /harvest for obligations)
  but no automated pipeline connecting them across sessions. The gap: a
  cross-session transcript scanner that extracts obligations and feeds them to
  harvest. Critical caveat from Huang 2024: any mining loop must ground on
  mechanical signals, not LLM self-assessment.
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/llm-dreaming-memory-consolidation.md
    type: related
  - target: wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Cross-session transcript mining for continuous improvement

## Decision context

**The problem:** the operator asked what skill goes through session chain
transcripts and identifies all open action items and realizable opportunities.
The answer: none. This research surveyed what exists in the ecosystem, what
the converging architecture looks like, and what specifically is missing in
our workspace.

**Why this matters:** the workspace has 50+ session transcripts containing
diagnosed bugs, operator requests, diagnosed root causes, and unrealized
improvement opportunities. Most of these are silently lost because no tool
extracts them — they exist only in transcripts that nobody re-reads. /harvest
persists obligations, but only for items manually added. /aar analyzes one
session. No tool walks the chain.

## The converging 3-layer architecture

The ecosystem has independently converged on the same architecture for agent
self-improvement, described by LangChain as "improving agents is a data mining
problem" and by Lilian Weng (2026) as "harness engineering."

```
Layer 1 — EPISODIC (what happened)
  Raw session transcripts, trace logs, tool call records.
  Source: the agent runtime's native logging.
  Format: JSONL conversation history, structured traces.

Layer 2 — WORKING (what it means)
  Summaries, friction reports, root-cause analyses, opportunity scans.
  Produced by: post-session analysis tools (retros, trace miners).
  Format: structured markdown with friction patterns, cost breakdowns.

Layer 3 — PROCEDURAL (what to do about it)
  Rules, obligations, playbooks, skill edits, AGENTS.md updates.
  Produced by: curation from working layer + human approval.
  Format: confidence-scored rules, lifecycle-tracked obligations.
```

The pipeline: **Layer 1 → extract signals → Layer 2 → curate → Layer 3 →
inject at session start → improved Layer 1 → ...** This is the continuous
improvement cycle.

## Ecosystem survey — four repos

### 1. agent-retro (giannimassi) — closest functionally

**What:** `/agent-retro` reads Claude Code JSONL transcripts and produces a
structured retrospective: conversation arc, token costs, tool waste detection,
friction analysis (user corrections, redirects, abandoned approaches), root
cause tracing, and specific edit proposals to skills/rules/config.

**Architecture:** Python extraction script (`scripts/extract.py`) streams JSONL
line-by-line (never loads full file). Captures: session metadata, token totals,
tool call counts, agent dispatches, skill invocations, git operations, file
reads/writes, full conversation arc, tool result sizes. Output: markdown retro
+ interactive approval walkthrough.

**Strengths:** Token-efficient extraction (50MB transcript → ~30KB output).
Full conversation arc preserved. Concrete edit proposals (not vague advice).
Streaming, stdlib-only Python.

**Limitation:** Single session only. No cross-session chain traversal. Claude
Code transcript format only (roadmap for others).

**Relevance to us:** This is what our /aar does, but with better extraction
mechanics. The streaming JSONL approach and tool-waste detection are worth
studying. GitHub: https://github.com/giannimassi/agent-retro

### 2. recursive-improve (kayba-ai, ~236 stars) — trace mining + overnight loop

**What:** Closes the self-improvement loop for any agent. Captures LLM call
traces via `ri.patch()` (patches OpenAI/Anthropic/LiteLLM SDKs) or session
context manager. Then `/recursive-improve` analyzes traces for failure patterns
and missed opportunities, measures with detectors, plans code/prompt fixes,
applies them on a branch, benchmarks before/after, and supports autonomous
overnight "ratchet" loops (improve → run → eval → keep/revert).

**Architecture:** Pipeline: build context → analyze traces → measure → plan →
review → fix. Dashboard for before/after metrics. Tracing is non-invasive (SDK
patch, not agent rewrite).

**Strengths:** Explicit "missed opportunities" extraction. Autonomous overnight
loop with automatic keep/revert. Benchmark-driven (not vibes). Framework-
agnostic tracing.

**Limitation:** Focused on code/prompt improvement, not obligation tracking.
Trace capture requires instrumentation (ri.patch) — doesn't mine existing
session transcripts post-hoc.

**Relevance to us:** The "missed opportunities" concept maps to our unrealized-
value gap. The overnight ratchet loop is the Toyota Improvement Kata (Gap 1 in
[[self-improving-agent-systems-techniques-and-workspace-gaps]]) made mechanical.
GitHub: https://github.com/kayba-ai/recursive-improve

### 3. cass-memory (Dicklesworthstone) — closest architecturally

**What:** 3-layer memory system for AI coding agents. Transforms scattered
session histories (from Claude Code, Cursor, Codex, Aider, Gemini, etc.) into
persistent, cross-agent memory.

**Architecture:**
- **Episodic layer:** raw session logs indexed by `coding_agent_session_search`
  (companion tool for unified search across agent histories)
- **Working layer:** structured diary summaries produced by post-session
  reflection/curation
- **Procedural layer:** playbook of rules/anti-patterns with confidence scoring,
  half-life decay, evidence validation. Agents query `cm context "task"` before
  starting work.

**Strengths:** Cross-session AND cross-agent (works across different tools).
Confidence-scored rules with scientific validation against history. Anti-
pattern inversion (stores what NOT to do). MCP server + CLI. Active development.

**Limitation:** Memory system, not obligation tracker — doesn't lifecycle-
track specific open items. Procedural rules are general patterns, not specific
action items with acceptance criteria.

**Relevance to us:** This is the architectural template. Our /harvest is the
procedural layer; our transcripts are the episodic layer; /aar is the working
layer. What's missing is the automated episodic → working → procedural pipeline
that runs across ALL sessions. GitHub:
https://github.com/Dicklesworthstone/cass_memory_system

### 4. alpha-loop (bradtaylorsf) — learn→improve in dev loop

**What:** End-to-end agent development loop: Plan → Build → Test → Review →
Verify → Ship → **Learn → Improve**. The Learn step extracts accumulated
learnings from the session; the Improve step mines them for prompt/skill/config
updates.

**Strengths:** Explicit learn→improve step in the standard dev loop. Simple
integration pattern.

**Limitation:** Single session/issue scope. Not cross-session chain traversal.

**Relevance to us:** The Learn→Improve step is what /aar → /harvest does
manually. The pattern of making it a standard loop step (not an afterthought)
is the right framing. GitHub: https://github.com/bradtaylorsf/alpha-loop

### 5. Addy Osmani's compound learning loop (blog, not repo)

**What:** The simplest implementation: AGENTS.md (persistent handbook of
discoveries, conventions, gotchas) + progress.txt (chronological journal of
attempts/successes/failures). After each task, append learnings. At session
start, re-inject relevant context.

**Relevance:** This is what we already do (AGENTS.md + wiki + handoffs). The
insight: the compound learning loop is the minimum viable self-improvement
system, and we're past it. The next step is automating the extraction, not
adding more manual append.

Source: https://addyosmani.com/blog/self-improving-agents/

## LangChain's "data mining" framing

LangChain's LangSmith Engine (May 2026, public beta) is the most production-
成熟 implementation. It's a continuous agent that mines production traces on a
schedule (every 6 hours):

1. **Screen** for signals (errors, evaluator failures, anomalies, negative
   feedback)
2. **Cluster** into named issues with severity + evidence traces
3. **Diagnose** root causes (optionally against connected source code)
4. **Propose** PRs/fixes, custom evaluators, and dataset examples
5. **Update** an "Agent Overview" memory document

This is the commercial version of the cross-session mining pipeline. Key
insight: **hierarchical processing** — compact trajectory summaries for
screening, full context for investigation. And: **specialized cheap models** as
"trace judges" that can outperform frontier LLMs on narrow tasks at far lower
cost.

Source: https://www.langchain.com/blog/improving-agents-is-a-data-mining-problem

## What nobody has built (including us)

**The cross-session chain scanner that extracts specific open action items
and feeds them to an obligation tracker.**

| Capability | agent-retro | recursive-improve | cass-memory | alpha-loop | Our workspace |
|---|---|---|---|---|---|
| Transcript extraction | ✅ | ✅ (via patch) | ✅ (via search) | ❌ | ✅ (analyze_session_patterns) |
| Single-session analysis | ✅ | ✅ | ✅ | ✅ | ✅ (/aar) |
| Cross-session chain | ❌ | ✅ (traces) | ✅ (memory) | ❌ | ❌ |
| Friction detection | ✅ | ✅ | ❌ | ❌ | ✅ (/tp session) |
| Obligation lifecycle | ❌ | ❌ | Partial (rules) | ❌ | ✅ (/harvest) |
| Automated pipeline | ❌ | ✅ (overnight) | Partial | ❌ | ❌ |

The gap: nobody connects transcript extraction → obligation identification →
lifecycle tracking → session-start surfacing as a single automated pipeline
that runs across the full session chain.

## The critical caveat (validated)

**Huang 2024** ("LLMs Cannot Self-Correct Reasoning Yet", 600+ citations):
pure intrinsic self-correction fails without external signal. Any transcript
mining loop must ground on mechanical signals — exit codes, tool failures,
operator corrections, git diffs — not LLM self-assessment of "what went well."

This is already documented in our wiki at
[[enforcing-kb-consultation-before-action-methods]] and
[[self-improving-agent-systems-techniques-and-workspace-gaps]]. The practical
implication: a transcript scanner should look for:

- **Mechanical signals:** non-zero exit codes, tracebacks, permission denials,
  hook blocks, timeout auto-backgrounding
- **Operator signals:** corrections ("no, do X"), redirects ("I wasn't looking
  for implementing"), explicit feedback ("you are an overconfident liar")
- **Outcome signals:** uncommitted work, unreviewed code, unwritten handoffs

NOT: the LLM's own assessment of session quality.

## What this means for our workspace

The pipeline we need, mapped to existing components:

```
~/.grok/sessions/*//chat_history.jsonl    (Layer 1 — EXISTS)
        │
        │  MISSING: cross-session scanner
        │  (generalize analyze_session_patterns.py)
        ▼
Extract: friction signals, open decisions, unrealized value,
         diagnosed-but-unfixed bugs, operator requests not done
        │
        │  MISSING: deduplication + clustering
        ▼
Feed to: P:/.data/harvest/pending/        (Layer 3 — EXISTS)
        │
        │  EXISTS: /harvest doctor discovers pending items
        ▼
Surface at: session start via /todo       (Layer 3 output — EXISTS)
```

**Generalizing `analyze_session_patterns.py`** is the lowest-effort path. It
already walks multiple session transcripts. Extending it from "routing failures
only" to "all open obligations" (exit codes, operator corrections, uncommitted
work, diagnosed-but-unfixed bugs, unrealized value) would fill the gap without
new infrastructure.

## Honest trade-offs

**Like:** the 3-layer architecture is validated by 4 independent repos and
LangChain's commercial product. Our workspace already has all three layers —
the gap is the pipeline between them, not new components. The mechanical-
signal approach (Huang 2024) is already our design philosophy.

**Dislike:** cross-session mining produces volume — 50+ sessions × dozens of
friction signals each = hundreds of items. Without aggressive deduplication
and clustering, this overwhelms rather than informs. cass-memory's confidence
decay is the right idea; our /harvest doesn't have it yet. Also: the research
community warns that post-hoc analysis without external grounding yields weak
insights — the scanner must extract mechanical signals, not ask the LLM to
judge session quality.

## Falsifier

This survey is wrong if:
- An existing tool (that I missed) already does cross-session transcript
  mining for action items — then we should adopt it, not build our own
- The volume of extracted items overwhelms the system and /harvest becomes
  a graveyard of unactionable noise — then the mining loop needs better
  filtering, not more extraction
- The operator's actual need is simpler than "mine all transcripts" — a
  weekly /aar + /harvest routine might achieve 80% of the value at 10% of
  the complexity (the improvement kata from Gap 1)

## Receipts

- agent-retro README: https://github.com/giannimassi/agent-retro (read via
  web_fetch, 2026-07-29)
- recursive-improve: https://github.com/kayba-ai/recursive-improve (~236 stars)
- cass-memory: https://github.com/Dicklesworthstone/cass_memory_system
- alpha-loop: https://github.com/bradtaylorsf/alpha-loop
- LangChain "data mining" framing:
  https://www.langchain.com/blog/improving-agents-is-a-data-mining-problem
- LangSmith Engine: https://www.langchain.com/blog/introducing-langsmith-engine
- Huang 2024: https://arxiv.org/abs/2310.01798
- Lilian Weng harness engineering: https://lilianweng.github.io/posts/2026-07-04-harness/
- Addy Osmani: https://addyosmani.com/blog/self-improving-agents/
- Typedef semantic extraction: https://www.typedef.ai/resources/extract-insights-chat-logs-conversations-using-semantics
