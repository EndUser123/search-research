---
title: "Structured behavioral memory architecture: episodic, semantic, procedural memory for agent fleets"
created: 2026-08-05
source: session-2026-08-05 (/www research on self-improving agent patterns we don't have)
sources:
  - external: https://arxiv.org/abs/2607.13091 (Accumulated Behavioral Rules, Aggarwal & Ghalaty, ICE 2026)
  - external: https://arxiv.org/abs/2502.12110 (A-MEM: Agentic Memory, NeurIPS 2025)
  - external: https://arxiv.org/abs/2512.13564 (Memory in the Age of AI Agents survey, Dec 2025)
  - external: https://github.com/letta-ai/letta (Letta/MemGPT)
  - external: https://arxiv.org/abs/2309.02427 (CoALA: Cognitive Architectures for Language Agents, Sumers 2023)
  - external: https://arxiv.org/abs/2604.09588 (Persistent Identity in AI Agents, 2026)
  - external: https://hidekazu-konishi.com/entry/ai_agent_memory_design_guide.html (Memory Design Guide, Jun 2026)
  - external: https://zylos.ai/research/2026-04-05-ai-agent-memory-architectures-persistent-knowledge/ (Zylos survey, Apr 2026)
  - external: https://github.com/mem0ai/mem0 (Mem0, 48K stars)
tags: [behavioral-memory, memory-architecture, episodic-memory, semantic-memory, procedural-memory, accumulated-behavioral-rules, forgetting, memory-bloat, agent-memory, letta, mem0]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  The dominant memory taxonomy in 2025-2026 agent research (CoALA, A-MEM,
  Letta, Mem0, Zep) organizes agent memory into three tiers: episodic (what
  happened), semantic (what is known), and procedural (how to do things). Each
  tier has a distinct lifecycle, storage substrate, and forgetting mechanism.
  The workspace already has all three tiers but they are unstructured: session
  handoffs (episodic), wiki concepts (semantic), AGENTS.md/skills (procedural).
  The gap is that these are not formally distinguished, managed with different
  lifecycles, or connected through a retrieval mechanism. The Accumulated
  Behavioral Rules paper (arXiv 2607.13091) demonstrates 0% recurrence rate
  across 9 tracked error classes with 74 cumulative post-rule exposures — the
  workspace's ~15KB of AGENTS.md corrections is an unstructured version of this
  pattern. Key risk: memory bloat → agent degradation (mem0 production issue:
  97.8% junk; ACL 2026 confirms memory management matters).
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/llm-dreaming-memory-consolidation.md
    type: related
  - target: wiki/concepts/cross-session-transcript-mining-continuous-improvement.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Structured behavioral memory architecture: episodic, semantic, procedural memory for agent fleets

## Decision context

**Why this research was needed:** the operator identified "accumulated behavioral data" as a pattern the workspace doesn't formally have. The workspace accumulates corrections in AGENTS.md (prose rules) and logs detections in behavioral-check-log.jsonl, but there is no structured behavioral data store with a formal memory taxonomy, lifecycle management, or retrieval mechanism.

**Core question:** how should a coding-agent CLI workspace structure the behavioral data it accumulates from operator corrections, session transcripts, and hook detections?

## Key Findings

### Three-tier memory taxonomy (the industry standard)

| Memory type | Cognitive analog | Agent implementation | Workspace equivalent | Lifecycle |
|-------------|-----------------|---------------------|---------------------|-----------|
| **Episodic** | "What happened" (Tulving) | Conversation logs, tool traces, structured episodes | Session handoffs, JSONL transcripts | Days-months (TTL) |
| **Semantic** | "What is known" | Facts, preferences, entity knowledge, domain rules | Wiki concepts (244+) | Long-lived, staleness-checked |
| **Procedural** | "How to do it" | System prompt rules, playbooks, skills, runbooks | AGENTS.md + skills (244+) | Long-lived, versioned |

Sources: CoALA (Sumers 2023), A-MEM (NeurIPS 2025), "Memory in the Age of AI Agents" survey (arXiv 2512.13564), Zylos 2026 survey.

**The workspace already has all three tiers.** The gap is that they are not formally distinguished, managed with different lifecycles, or connected through a unified retrieval mechanism.

### Accumulated Behavioral Rules: the formalized pattern

The Accumulated Behavioral Rules paper (arXiv 2607.13091, ICE IEEE/ITMC 2026) demonstrates what the workspace's AGENTS.md does informally:

- Every accepted human review comment → codified as a persistent behavioral rule
- Rule set grows monotonically (ratchet effect — error classes expand over time)
- Agents load the instruction file as system context at session start
- **Result: 0% recurrence rate across 9 tracked error classes, 74 cumulative post-rule session exposures**
- Review effort shifted from mechanical correctness (14% of comments) to design-level concerns (66%)

**The workspace's AGENTS.md is an unstructured version of this pattern.** The gap: no rule schema, no provenance tracking (which correction produced which rule), no automated validation.

### Letta/MemGPT: LLM-managed memory paging

Letta implements a three-tier memory hierarchy with LLM-controlled paging:
- **Core memory** — always in-context (the workspace's AGENTS.md equivalent)
- **Archival memory** — external vector store, searched on demand (the workspace's wiki equivalent)
- **Recall memory** — pageable conversation log (the workspace's transcript equivalent)

The LLM itself controls all tiers via function calls (`core_memory_replace`, `archival_memory_search`). Inspired by OS virtual memory paging.

**Workspace gap:** the workspace's agent doesn't dynamically decide what to load into context and what to page out. The context firewall architecture [[context-firewall-architecture]] achieves isolation but not dynamic paging.

### Forgetting by design

Three mechanisms for memory management (Konishi, "AI Agent Memory Design Guide," Jun 2026):

| Mechanism | How it works | Workspace equivalent |
|-----------|-------------|---------------------|
| **TTL** | Raw episodes expire on a timer | /dream reads 90 days of handoffs (implicit TTL) |
| **Usage-based decay** | Retrieval scores combine similarity + recency + reinforcement | None |
| **Staleness detection** | Facts verified against `validity_basis` before use | None (wiki concepts have `verification:` field but no automated staleness check) |

**The #1 unsolved problem:** an agent that never forgets accumulates contradictions and retrieves noise. The mem0 production issue (97.8% junk memories) demonstrates that unmanaged memory growth degrades agent performance.

**Workspace relevance:** the workspace's AGENTS.md has grown to ~15KB. The wiki has 244+ concepts. Neither has formal TTL or staleness detection. The `/skill-prune` skill is a manual pruning tool, but there's no automated decay mechanism.

### Structured memory records

Every memory record should carry an envelope of metadata:

```json
{
  "memory_id": "unique-id",
  "type": "procedural | semantic | episodic",
  "namespace": "auth | hooks | skills | ...",
  "source": {"episode": "session-2026-07-20", "correction": "operator-pushback"},
  "confidence": 0.85,
  "written_at": "2026-07-20T14:30:00Z",
  "last_confirmed_at": "2026-08-01T10:00:00Z",
  "expires_at": null,
  "supersedes": "previous-rule-id"
}
```

**Workspace gap:** AGENTS.md rules have implicit provenance (the reference incidents cited in comments) but no machine-readable metadata envelope. Wiki concepts have frontmatter but lack `confidence`, `last_confirmed_at`, and `expires_at` fields.

### Correction logs as training data

The key insight from the Accumulated Behavioral Rules paper: **39% of rules came from PR reviewers** — human review feedback is the highest-quality signal for rule generation. Each correction must be classified: is it a one-off typo or a generalizable class of mistake? If generalizable, it becomes a persistent behavioral rule.

**Workspace mapping:** `scan_corrections.ps1` already clusters corrections by pattern. The gap is converting clusters into persistent structured rules with provenance and validation gates.

## Honest trade-offs

**Like:** the three-tier taxonomy is well-established and maps naturally to what the workspace already has; formalized rules demonstrably reduce error recurrence (0% in the paper); structured records enable principled forgetting and staleness detection; no model fine-tuning needed — this is all harness engineering.

**Dislike:** memory bloat is the #1 failure mode — unstructured accumulation degrades performance; formal schemas add overhead to every rule addition; staleness detection requires ongoing maintenance; the Letta-style LLM-managed paging adds operational complexity that may not be justified for a single-user workspace; forgetting by design risks losing useful knowledge.

## Falsifier

This concept is wrong if, within 6 months:
- Structured rules are added but error recurrence rates don't decrease (the structure doesn't help)
- The forgetting mechanism discards rules that are still needed (premature forgetting)
- Memory bloat continues despite the taxonomy (the taxonomy doesn't prevent accumulation)
- A vendor ships a memory layer that makes manual structuring obsolete

## What this means for our workspace

**Current state: all raw materials exist, no formal architecture.**

| Raw material | Current form | Memory tier | Gap |
|-------------|-------------|-------------|-----|
| AGENTS.md corrections | ~15KB prose | Procedural | No schema, no provenance, no validation gate |
| behavioral-check-log.jsonl | Detection logs | Episodic | No TTL, no clustering |
| scan_corrections.ps1 | Pattern clustering | Reflection layer | Doesn't produce persistent rules |
| Wiki concepts (244+) | Markdown with frontmatter | Semantic | No staleness check, no confidence field |
| Skills (244+) | SKILL.md files | Procedural | No promotion gate from episodic to procedural |
| Session handoffs | Markdown files | Episodic | No TTL, no retrieval mechanism |
| /dream | 90-day consolidation | Forgetting | Primitive; no decay scoring |

**Recommended approach:**

1. **Add provenance metadata to AGENTS.md rules** — each rule should cite the session, correction, and date that produced it. This is the minimum structure that makes rules traceable. (The workspace already does this informally via "Reference incident" citations — formalize it.)

2. **Add `last_confirmed_at` to wiki concepts** — extend the existing frontmatter schema with a date field tracking when the concept was last verified against current state. The `/skill-prune` skill can flag concepts where `last_confirmed_at` is >180 days old.

3. **Formalize the correction → rule pipeline** — when `scan_corrections.ps1` identifies a cluster, automatically propose an AGENTS.md rule addition with provenance. The operator reviews and accepts/rejects. Accepted rules get a rule ID and schema metadata.

4. **Add confidence scoring** — new rules start at `confidence: 0.5`. Each session where the rule fires and isn't violated increments confidence. Each violation decrements it. Low-confidence rules are candidates for review.

5. **Implement staleness detection for wiki** — a periodic scan (`/maintain` check) that flags concepts where the cited sources may have changed (e.g., library docs >12 months old, tool comparison >6 months).

**What NOT to do:** don't implement Letta-style LLM-managed paging — it's operational overhead the workspace doesn't need. The workspace's needs are better served by the simpler accumulated-rules pattern with structured metadata.

## Related

- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@extends — this concept extends the survey with the formal memory taxonomy
- [[llm-dreaming-memory-consolidation]]@related — /dream is the closest existing implementation of forgetting/consolidation
- [[cross-session-transcript-mining-continuous-improvement]]@related — transcript mining as the data source for episodic memory
- [[mechanical-enforcement-over-behavioral-reminder]]@related — structured rules are the mechanical enforcement layer
- [[trace-eval-improve-loops-for-agent-fleets]]@related — behavioral data feeds the eval suite
- [[context-firewall-architecture]]@related — context isolation as the working memory boundary

## Sources

**Accumulated rules:**
- Accumulated Behavioral Rules (arXiv 2607.13091) — https://arxiv.org/abs/2607.13091

**Memory architectures:**
- A-MEM: Agentic Memory (NeurIPS 2025) — https://arxiv.org/abs/2502.12110
- Memory in the Age of AI Agents survey — https://arxiv.org/abs/2512.13564
- CoALA: Cognitive Architectures for Language Agents — https://arxiv.org/abs/2309.02427

**Frameworks:**
- Letta (MemGPT) — https://github.com/letta-ai/letta
- Mem0 — https://github.com/mem0ai/mem0
- Zep / Graphiti — https://github.com/getzep/graphiti

**Design guides:**
- Konishi: AI Agent Memory Design Guide — https://hidekazu-konishi.com/entry/ai_agent_memory_design_guide.html
- Zylos AI Memory Architecture Survey — https://zylos.ai/research/2026-04-05-ai-agent-memory-architectures-persistent-knowledge/

**Identity persistence:**
- Persistent Identity in AI Agents — https://arxiv.org/abs/2604.09588

**Research method:** /www pipeline, parallel or-ling-3-flash-free subagent, 28+ sourced findings synthesized.
