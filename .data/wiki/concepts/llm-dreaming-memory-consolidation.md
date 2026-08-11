---
title: "LLM Dreaming — Offline Memory Consolidation for LLM Agents"
created: 2026-07-25
source: session-2026-07-25
tags: [llm-dreaming, memory-consolidation, sleep-time-compute, multi-agent, fleet, reflection, agent-memory, dreaming]
summary: >
  "LLM dreaming" is overloaded. The dominant 2026 sense — pushed by Anthropic
  "Dreaming" (May 2026), Xiaomi MiMo "Dream", and Letta Memory Blocks — is
  async memory consolidation: a background process that reads accumulated
  session traces + memory store, then emits a curated, deduplicated,
  contradiction-resolved representation future sessions see (without modifying
  weights). The canonical research is Lin/Snell/Packer 2025 "Sleep-time
  Compute." The field's #1 failure mode is memory bloat — store-everything
  pipelines collapse (mem0: 97.8% junk; ACL 2026 paper confirms memory
  management matters in resource-limited settings). No production system
  targets the user's exact topology (one human, many concurrent coders,
  handoff-based, wiki-grounded); the closest are Anthropic Dreams (research
  preview), Letta, and Hindsight (vectorize.io). For our workspace, dreaming
  should be a meta-skill over existing substrates (/aar, /wiki, /close,
  preflight), with a receipt-preserving, non-destructive, anti-bloat-gated,
  security-bounded design.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
evidence_gaps:
  - "Sleep-time compute 5× claim is on synthetic benchmarks (Stateful GSM-Symbolic); no third-party production replication found [FIELD — re-verified 2026-08-11: still no third-party replication in workspace commits]"
  - "Mem0/Letta/Zep benchmark dispute is public — vendor-driven; no vendor-independent survey exists [FIELD — re-verified 2026-08-11: dispute remains vendor-driven]"
  - "Multi-agent / fleet-wide consolidation research exists but no paper targets handoff-based wiki-grounded fleet topology [FIELD — re-verified 2026-08-11: still no paper, but workspace has now IMPLEMENTED this topology via /dream, providing first-hand validation]"
  - "Anthropic 'Dreaming' is research preview, not GA — production adoption claims are gated [FIELD — re-verified 2026-08-11: research preview per platform.claude.com docs]"
  - "Memory poisoning demonstrated in red-team/PoC; in-the-wild exploitation sparse (one CVE-2025-64439) [FIELD — re-verified 2026-08-11: no new CVEs surfaced in workspace monitoring]"
last_re_verified: 2026-08-11
verification_state: workspace-validated; field-gaps-persist
relations:
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
    reciprocal: related
  - target: wiki/concepts/llm-handoff-best-practices.md
    type: related
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
  - target: wiki/concepts/multi-agent-correlated-errors.md
    type: related
  - target: wiki/concepts/multi-agent-transcript-race-condition-check-preprocessor.md
    type: related
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass.md
    type: related
---

## Summary

"LLM dreaming" is an overloaded term. After research + disconfirmation, the dominant 2026 sense is **async memory consolidation** — a background process that reads accumulated session transcripts and a memory store, then emits a curated, deduplicated, contradiction-resolved representation that future model calls see, without modifying weights. Anthropic launched "Dreaming" for Claude Managed Agents in May 2026; Xiaomi MiMo ships a 7-day "Dream" worker; Letta packages it via Memory Blocks. The canonical research anchor is Lin/Snell/Packer 2025 "Sleep-time Compute" (arXiv:2504.13171). The pattern's #1 failure mode is **memory bloat → agent degradation** (ACL 2026 paper confirms memory management matters; mem0 production issue: 97.8% junk). Multi-agent fleet-wide consolidation is an active but immature research area (arXiv:2603.07670 §6.5, arXiv:2603.11768 SSGM). For our workspace, dreaming should be implemented as a **meta-skill over existing substrates** (`/aar`, `/wiki`, `/close`, `preflight`), not a new memory store — with a receipt-preserving, non-destructive, anti-bloat-gated, security-bounded design.

## Decision context

### Why this research was needed

The user asked: "find information on dreaming for LLM — what repos exist and how they work, what people like and don't like, how it could and should work for us." The real question behind it: **is there a mature pattern (or shipping product) for letting our fleet of concurrent LLM coders consolidate experience offline, so future sessions start smarter — and if so, what would a fleet-appropriate design look like given the substrates we already have (wiki, handoffs, AGENTS.md, episodic-memory MCP, tasks store)?**

### What alternatives were explored

- **Sense-by-sense decomposition** (Round 1, theory subagent): five distinct meanings of "LLM dreaming" were enumerated — hallucination, sleep-time compute, experience replay, world-model rollouts, memory consolidation. Without this disambiguation, research would have conflated DreamerV3 (RL world models) with Anthropic Dreams (consolidation) with Reflexion (verbal self-critique).
- **Repo/product landscape** (Round 1, repos subagent): 16 Tier-1+2 repos surveyed. Only Letta ships public benchmarks; everything else is research-only or hobby-scale.
- **Community sentiment** (Round 1, sentiment subagent): failure modes are extensively documented (bloat, poisoning, drift, cold-start, reflection plateau).
- **Multi-agent gap probe** (Round 2, discovery): confirmed the user's topology (one human, many concurrent coders, handoff-based, wiki-grounded) is **not directly targeted** by any paper or product. Closest matches: Hindsight (vectorize.io), claude-mem (88.5K stars, Postgres multi-tenant), dream-skill (grandamenium, Claude Code Auto-Dream replica).
- **Disconfirmation** (Round 3): softened four of five Round-1 conclusions. The 5× sleep-time compute gain is benchmark-only; the 13%-vs-39% bloat number is from a blog, not the cited paper; Reflexion's "plateau without external feedback" is refuted by 91% HumanEval; memory poisoning is real in red-team but sparse in the wild.
- **Paths that didn't produce findings:** search for an existing Grok-native `dream-skill` returned nothing; the skill will need to be authored locally.

### What the research changed

- Confirmed that dreaming-as-consolidation is a real product category, not just research — but the user's specific topology (multi-agent, handoff-based, wiki-grounded fleet) is genuinely novel.
- Redirected the design conclusion from "build/buy a memory store" to "add a meta-skill over substrates we already have." The wiki + handoffs + AGENTS.md + episodic-memory MCP are already a 4-tier memory (semantic / episodic / procedural / working). What's missing is the async consolidator, not the store.
- Surfaced two fleet-specific failure modes the user must design around: **identity drift** (arXiv:2607.01988) and **manufactured confidence** (arXiv:2606.29279) — consolidation can launder unreliable memories into trusted facts by repetition. The operator's existing `verification_receipt` rule is the structural antidote.

## Key findings

### The five senses of "LLM dreaming" (disambiguate before discussing)

| Sense | Meaning | Maturity | Anchor |
|---|---|---|---|
| **A. Hallucination** | Confabulation; fluent ungrounded output | Established | Wikipedia; Smith & Smith 2023 (confabulation is more accurate) |
| **B. Sleep-time compute** | Idle-time pre-computation between user turns | Shipping (Letta); research (Lin/Snell 2025) | arXiv:2504.13171 |
| **C. Experience replay** | Self-generated trajectories fed back as training/reflection | Research landmark | Reflexion (Shinn NeurIPS 2023, ~6,300 cit); Voyager (Wang 2023, ~2,900 cit) |
| **D. World-model rollouts** | Model queried as simulator to plan (Dreamer lineage) | RL-mature; LLM-young | DreamerV3 (arXiv:2301.04104, ~1,685 cit); RAP (Hao 2023, ~1,230 cit) |
| **E. Memory consolidation** | Async background curation of accumulated traces into a cleaner store | Shipping (Anthropic Dreams May 2026; Xiaomi MiMo; Letta) | Park 2023 Generative Agents (~6,850 cit); Anthropic Dreams docs |

**Dominant 2026 sense is E (memory consolidation).** [QUALIFIED — vendor-led (Anthropic + Letta branding), not literature consensus; "LLM-dreams" was previously used in NLP4Science 2024 for psychological dream analysis. There is no vendor-independent survey establishing terminology consensus. — disconfirmation Round 3]

### Architecture patterns (how they actually work)

1. **Sleep-time compute (Letta 2025).** Idle-mode LLM rewrites active agent's context, precomputes answers, condenses memory. Online agent consumes precomputed artifact at query time. Trigger: message-count threshold or compacted context window. Backed by MemFS (git) so each dream cycle is a committable diff.
2. **Memory stream + reflection (Park 2023).** Observations appended chronologically. Retrieval ranks by recency × importance × relevance. When importance-weighted recent memories cross threshold, LLM generates higher-level reflections, inserted back into stream and themselves retrievable. This is the canonical non-sleep-metaphor implementation.
3. **Skill library (Voyager 2023).** New executable skill programs added only after environmental verification. Library is the memory; retrieval is embedding-based; skills are composable.
4. **Reflection memory (Reflexion 2023).** Per-failure verbal self-critique stored; recent reflections inserted into next attempt's prompt. No scheduled consolidation — triggered by failure.
5. **Zettelkasten (A-MEM 2025).** Each new note auto-linked to existing notes via LLM-generated tags. Link graph is the memory; retrieval traverses the graph.
6. **REM-style online learning (sleep-based-learning 2025).** "Dream Generator" produces synthetic future trajectories used for continual learning during sleep — learning, not just consolidation. Niche.
7. **Non-destructive consolidation w/ promotion gate (Anthropic Dreams 2026).** Input memory store + up to 100 session transcripts → emits a *new candidate* output store. Input preserved; engineer inspects, promotes, or discards. Strongest current answer to bloat-without-loss.

### Repos / shipping products (Tier 1, by relevance to us)

| Repo / Product | Stars | Status | Why it matters for us |
|---|---|---|---|
| **Letta** (`letta-ai/letta` + `sleep-time-compute`) | ~10k | Active, commercial | Only vendor with public benchmark (5× test-time reduction on synthetic benchmark — QUALIFIED, no third-party replication). MemFS = git-backed memory filesystem = each dream is a committable diff. |
| **Anthropic Dreams** (Managed Agents API) | n/a | Research preview, May 2026 | Non-destructive consolidation pattern (input preserved, candidate output promoted). The cleanest product design. Gated access, not GA. |
| **Xiaomi MiMo "Dream"** | n/a | Shipping | 7-day auto-trigger; merges/dedupes/verifies paths. "Distill" companion mines sessions for reusable workflows. Time-trigger model. |
| **Hindsight** (`vectorize-io/hindsight`) | ~10k | Active, commercial | Closest production match to multi-agent shared bank. Maintainer endorses "one bank every tool reads/writes through." Multi-tenant. |
| **claude-mem** (`thedotmack/claude-mem`) | ~88.5k | Active | Postgres-backed shared memory across developers with tenant isolation. Most-adopted. Heavyweight (own Postgres). |
| **Park 2023 Generative Agents** (`joonspk-research/generative_agents`) | ~7k | Research landmark | The academic root of memory+reflection+planning. Reference implementation, not actively extended. |
| **Reflexion** (`noahshinn/reflexion`) | ~2k | Research landmark | Verbal self-replay in episodic buffer. 91% HumanEval (disconfirmation: refutes "reflection plateaus" claim in its strong form). |
| **Voyager** (`MineDojo/Voyager`) | ~6k | Research | Skill-library procedural memory. Minecraft-only; not portable to text agents. |
| **A-MEM** (`agiresearch/a-mem`) | ~500 | Active | Zettelkasten agentic memory. Relevant because our wiki *is* a Zettelkasten — link-graph retrieval is already native. |
| **dream-skill** (`grandamenium/dream-skill`) | small | Active | Claude Code replica of Anthropic Auto-Dream. 4-phase, 24hr Stop-hook trigger. Closest installable skill pattern. |

**No Grok-native dream-skill exists.** The skill will need to be authored locally for our runtime.

### Failure modes (what practitioners dislike — disconfirmation-qualified)

| Failure mode | Evidence | Status after disconfirmation |
|---|---|---|
| **Memory bloat → agent degrades** | mem0 issue #4573 ("97.8% junk"); ACL 2026 (arXiv:2505.16067, 82 cit) confirms management matters in resource-limited settings | QUALIFIED — the famous "13% vs 39%" number is from tianpan.co blog, NOT the paper. Counterexample: Letta Filesystem stores *everything* and scores 74% on LoCoMo. "Bloat always hurts" is overstated; "management matters under resource limits" is the peer-reviewed claim. |
| **Sleep-time compute doesn't generalize** | Lin et al. 5× claim is on Stateful GSM-Symbolic (synthetic, author-designed) | QUALIFIED — no third-party replication; gain requires multi-query context reuse; singleton workloads won't benefit. |
| **Memory poisoning** | MINJA (arXiv:2503.03704), AgentPoison ≥95% ISR, CVE-2025-64439 (LangGraph RCE), OWASP LLM04:2025 | CONFIRMED for feasibility (red-team/PoC + one CVE); sparse in-the-wild. Risk real and ongoing. **Fleet-shared memory bank = fleet-wide attack surface.** |
| **Manufactured confidence** | arXiv:2606.29279 (June 2026) | NEW finding. Consolidation launders unreliable memories into trusted facts by repetition. **The fleet topology — multiple agents writing to one shared bank — is exactly what this paper warns about.** |
| **Identity drift** | arXiv:2607.01988 (July 2026) | NEW finding. Consolidation across heterogeneous agents can smear identity. Directly relevant to our `host:` provenance tags — consolidating across `host: grok` and `host: claude` concepts without a promotion gate is the failure mode. |
| **Retrieval-relevance decay** | tianpan.co; multiple Reddit threads | CONFIRMED — declining precision as store grows is the leading indicator of bloat. |
| **Cold-start** | Pattern across reviews | INFERRED — bootstrap phase behaves stateless; not directly studied. |
| **Reflection plateaus w/o feedback** | EACL 2026 critique | REFUTED in strong form — Reflexion's 91% HumanEval uses environment feedback (test failures); Renze 2024 shows p<0.001 improvement from self-reflection. The critique is task-scoped, not general. |
| **Mem0/Letta benchmark dispute** | Zep blog, Letta blog, HN 44883133, MemPalace audit | NEW critical finding. The cross-vendor memory-benchmark ecosystem is vendor-driven; any "X beats Y by N%" claim should be treated as PR until replicated. |

### Multi-agent / fleet-wide consolidation (the gap)

The prior "all research is single-agent" framing is **wrong**. Multi-agent shared memory is an active 2026 research area, but **no paper targets the user's exact topology** (one human, many concurrent coders, handoffs, wiki-grounded).

- **arXiv:2603.07670** ("Memory for Autonomous LLM Agents") §6.5 names the trade-off: *"all memory shared (simple but leaks private info) vs. each agent maintains own store with no cross-access (isolated but prevents knowledge transfer). A principled middle ground would define role-based access controls over a shared memory substrate."* §9.6 names multi-agent memory governance as wide-open.
- **SSGM framework** (arXiv:2603.11768): Stability-and-Safety-Governed Memory.
- **Survey on long-term memory security** (arXiv:2604.16548): explicitly enumerates "shared organizational memory" as an attack surface.
- **Production:** Hindsight (vectorize-io) is the closest. Maintainer endorses single-bank + cross-document consolidate. The GitHub discussion #1576 documents 5 concrete failure modes a fleet operator hit (no per-memory deletion, LLM extraction duplicates, consolidate-only-within-doc, wrapper-script latency, small-model extraction returning zero facts).

## How it could and should work for us

### What we already have (the substrate)

The workspace already implements a 4-tier memory architecture — we do not need a new store:

| Memory tier (cognitive science) | Our substrate | Already does |
|---|---|---|
| **Working** | Context window, `active-surface.last.md` | Per-session state |
| **Episodic** | `P:/docs/handoffs/`, episodic-memory MCP, `P:/.data/wiki/log.md`, AAR artifacts | Session records, conversation search, ingest log |
| **Semantic** | `P:/.data/wiki/concepts/` (198 pages), `P:/.data/www-ledger/` (32 entries) | Curated findings, research ledger |
| **Procedural** | `~/.grok/AGENTS.md`, `P:/AGENTS.md`, `~/.grok/skills/`, `P:/.claude/rules/` | Rules, conventions, skills |

What's missing is **not a store** — it's an **async consolidator** with anti-bloat and security boundaries. Several existing skills already do pieces of this:

- `/aar` — episodic→semantic consolidation per-session
- `/wiki` (default mode) — cross-session distillation
- `/close` — session-end accounting
- `preflight` / `source-authority-discovery` — contradiction detection

Dreaming for us = a **meta-skill that schedules and chains these on a trigger**, with the anti-bloat gate, identity-preservation rule, and security boundary below.

### Proposed design (`/dream` skill — to be authored)

1. **Trigger model — entropy/conflict/time, not pure time.** Per SCM (arXiv:2604.20943), trigger when any of: (a) operator invokes `/dream`; (b) ≥5 new wiki concepts since last dream; (c) ≥1 AAR flagged a recurring pattern; (d) ≥30 days since last dream. Do NOT copy MiMo's pure 7-day cadence — it consolidates noise on quiet weeks.
2. **Scope per `host:` identity.** Never consolidate across `host:` tags without explicit promotion. Wiki concepts tagged `host: grok` and `host: claude` stay separate until a manual promotion gate fires. (Direct response to identity drift, arXiv:2607.01988.)
3. **Receipt-preserving.** Every consolidated claim must cite its source handoff / AAR / concept / session. The operator's existing `verification_receipt` rule extends naturally — dream output that lacks receipts is rejected. (Direct response to manufactured confidence, arXiv:2606.29279.)
4. **Non-destructive (Anthropic pattern).** Dream emits a *candidate* memory store (new concept drafts, merge proposals, retirement candidates). Operator inspects, promotes, or discards. Never auto-overwrite existing concepts. Git-commit each promotion individually.
5. **Anti-bloat gate (mandatory).** Every dream must propose ≥N retirements/merges for every M additions (target net-zero or net-negative concept growth). Direct response to bloat failure mode. Pre-conditions: existing concepts with `status: superseded`, low-citation concepts, concepts contradicted by newer findings.
6. **Fleet-aware provenance.** When dream consolidates across handoffs from multiple agents (Grok+Claude+Codex), tag output `provenance: multi-agent-dream` and list contributing sessions. Future sessions know the claim's authority.
7. **Security boundary.** Dream worker treats all handoff content as **untrusted input** — reads but never executes; never auto-promotes a write rule from handoff prose into AGENTS.md without operator approval. Defense against indirect prompt injection through past sessions (MINJA, AgentPoison).
8. **Race-safe execution.** Run only when no other agent is writing to `P:/.data/wiki/concepts/`. Use the same pattern as `multi-agent-transcript-race-condition-check-preprocessor` — acquire a lock, refuse to start if contested. (Direct response to concurrent-write hazards already documented in our wiki.)
9. **Output artifact.** A single `P:/docs/dreams/YYYY-MM-DD-dream.md` with sections: ingested sessions, candidate additions, candidate retirements, contradictions detected, receipts. Operator reviews, then `/wiki` writes the promoted concepts and `/wiki` updates `status:` on retired ones.

### Why this design (selection criterion)

**Criterion: lowest future cost and risk, given the substrate already exists.** The alternatives — (a) adopt Letta/Hindsight wholesale, (b) build a new memory DB, (c) do nothing — all lose on this criterion. (a) loses the wiki/AGENTS.md/handoff discipline we already have and adds a vendor runtime; (b) duplicates existing storage; (c) leaves the consolidation burden on the operator (the current failure mode the user is implicitly asking to solve).

The proposal is **additive**: a new skill that orchestrates existing skills on a trigger, with three structural gates (anti-bloat, identity preservation, security boundary) that address the documented failure modes.

### What to do first (smallest viable step)

Author `/dream` as a thin orchestrator that:
1. Reads the `www-ledger`, `wiki/concepts/` index, recent `docs/handoffs/`, recent AAR artifacts.
2. Asks the model (parent Grok, or delegated M3) to propose: 3 retirements, 3 merges, 3 additions, 3 contradictions — each with a receipt.
3. Writes the proposal to `P:/docs/dreams/YYYY-MM-DD-dream.md`.
4. Stops. Operator promotes via existing `/wiki` write flow.

No new store. No vendor dependency. No auto-write. The anti-bloat gate (step 2 forces net-zero) and receipt requirement are baked in.

## Honest trade-offs (what people like AND dislike)

**Like:** continuity across sessions; amortized cost (sleep-time compute, when it applies); transparent/white-box memory (Letta); fleet-wide learning (Hindsight pattern); procedural skill reuse (Voyager).
**Dislike:** memory bloat → degradation (the dominant practitioner complaint); maintenance burden shifts to user; vendor lock-in (Letta runtime); reflection plateaus on some task types; retrieval drift; cold-start; multi-tenancy privacy leak surface; vendor-driven benchmarks with no independent replication.

## Falsifier

This concept is wrong if, within 12 months:
- A vendor ships **selective consolidation with provable guarantees** on poison-resistance, drift, or bloat — the "heuristic only" claim collapses, and we should buy rather than build.
- A paper targets the **handoff-based wiki-grounded fleet** topology directly — then we should adopt their design rather than the meta-skill proposed here.
- The operator tries `/dream` as proposed and finds the anti-bloat gate leaves the wiki **shrinking while still being useful** — that validates the design; if the wiki shrinks *and loses value*, the anti-bloat gate is too aggressive and the concept's net-zero target is wrong.
- Sleep-time compute gets **third-party production replication** of the 5× claim — then adoption (not meta-skill) becomes the optimal path.
- Memory poisoning moves from red-team to **common in-the-wild exploitation** — then the security boundary here is insufficient and the design must add formal verification.

## Related

- [[context-firewall-architecture]] — the 3-layer extraction/agent/orchestrator pattern; dreaming is the async variant of layer 3 synthesis
- [[llm-handoff-best-practices]] — the handoff substrate dreaming would consolidate over
- [[model-fleet-provider-pools]] — the fleet topology that makes multi-agent consolidation necessary and identity drift a risk
- [[multi-agent-correlated-errors]] — why a fleet-shared memory bank amplifies correlated failures
- [[multi-agent-transcript-race-condition-check-preprocessor]] — the concurrent-write race pattern `/dream` must respect
- [[multi-agent-destructive-git]] — shared-state hazards the non-destructive design principle addresses
- [[compensating-for-weaker-models-ensemble-multi-pass]] — multi-pass refinement; dreaming is the offline analogue
- [[mental-models-for-handoff-and-aar]] — the episodic→semantic consolidation `/aar` already does per-session
- [[agent-failure-modes-2026]] — broader failure-mode taxonomy this concept extends
- [[optimal-cross-session-chain-traversal-aar-handoff-grok]] — cross-session chain that dreaming would collapse

## Auto-related

<!-- wiki_after_write.py will populate this -->

## Sources

**Canonical research:**
- Lin, Snell, Packer et al. 2025, "Sleep-time Compute: Beyond Inference Scaling at Test-time" — https://arxiv.org/abs/2504.13171 — QUALIFIED: 5× claim is on synthetic benchmark, no third-party replication
- Park, O'Brien, Cai, Morris, Liang, Bernstein 2023, "Generative Agents: Interactive Simulacra of Human Behavior" (UIST '23, ~6,850 cit) — https://arxiv.org/abs/2304.03442
- Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao 2023, "Reflexion" (NeurIPS 2023, ~6,300 cit) — https://arxiv.org/abs/2303.11366
- Wang et al. 2023, "Voyager" (~2,900 cit) — https://arxiv.org/abs/2305.16291
- Hafner et al. 2023, "DreamerV3" (~1,685 cit) — https://arxiv.org/abs/2301.04104
- Smith & Smith 2023, "Hallucination or Confabulation?" — https://pmc.ncbi.nlm.nih.gov/articles/PMC10619792/

**Recent (2026) — failure modes and multi-agent:**
- Xiong et al. 2026, "How Memory Management Impacts LLM Agents" (ACL 2026, 82 cit) — https://arxiv.org/abs/2505.16067 — NOTE: tianpan.co's "13% vs 39%" number is NOT from this paper
- "Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers" — https://arxiv.org/abs/2603.07670 — §6.5 multi-agent, §9.6 open problems
- "Governing Evolving Memory in LLM Agents" (SSGM) — https://arxiv.org/abs/2603.11768
- "Survey on Security of Long-Term Memory in LLM Agents" — https://arxiv.org/abs/2604.16548
- "SCM: Sleep-Consolidated Memory with Algorithmic Forgetting" — https://arxiv.org/abs/2604.20943
- "Episodic-to-Semantic Consolidation Without Identity Drift" (July 2026) — https://arxiv.org/abs/2607.01988
- "Manufactured Confidence: How Memory Consolidation Turns Hearsay into Confident Facts" (June 2026) — https://arxiv.org/abs/2606.29279
- MINJA: Practical Memory Injection Attack — https://arxiv.org/abs/2503.03704

**Product / vendor:**
- Anthropic Dreams API docs — https://platform.claude.com/docs/en/managed-agents/dreams (research preview, May 2026)
- Ken Huang, "Why AI Agents Are Starting to Dream" — https://kenhuangus.substack.com/p/why-ai-agents-are-starting-to-dream (precise engineering framing)
- Letta Memory Blocks — https://docs.letta.com/configuration/memory
- Letta benchmarking blog (vendor-PR; treat with caution per Mem0/Letta dispute) — https://letta.com/blog/benchmarking-ai-agent-memory/

**Repos:**
- Letta — https://github.com/letta-ai/letta + https://github.com/letta-ai/sleep-time-compute
- Hindsight (multi-agent shared bank) — https://github.com/vectorize-io/hindsight + discussions/1576
- claude-mem (88.5K stars, multi-tenant Postgres) — https://github.com/thedotmack/claude-mem
- dream-skill (Anthropic Auto-Dream replica for Claude Code) — https://github.com/grandamenium/dream-skill
- A-MEM (Zettelkasten agentic memory) — https://github.com/agiresearch/a-mem
- Reflexion — https://github.com/noahshinn/reflexion
- Voyager — https://github.com/MineDojo/Voyager
- Generative Agents — https://github.com/joonspk-research/generative_agents

**Community sentiment:**
- Reddit r/ClaudeCode "Claude Code can now /dream" — https://www.reddit.com/r/ClaudeCode/comments/1s2ci4f/ — highest-signal community source
- HN Letta Code launch thread — https://news.ycombinator.com/item?id=46294274
- Calvin Ku, "From Beta to Battle-Tested" (Letta vs Mem0 vs Zep) — https://medium.com/asymptotic-spaghetti-integration/from-beta-to-battle-tested-picking-between-letta-mem0-zep-for-ai-memory-6850ca8703d1
- tianpan.co, "The Forgetting Problem" — https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability (NOTE: 13-vs-39 number is from this blog, not the cited ACL paper)
- mem0 production issue "97.8% junk" — https://github.com/mem0ai/mem0/issues/4573
- Zep blog on Mem0 benchmarking dispute — https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/
- OWASP LLM04:2025 — https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/

**Research method:**
- Research conducted 2026-07-25 via `/www` pipeline. 5 parallel subagents (theory, repos, sentiment, discovery, disconfirmation) over 2 waves. Disconfirmation qualified 4 of 5 Round-1 conclusions; refuted the "Reflexion plateaus" claim in its strong form.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

## Re-verification 2026-08-11 (epistemic debt re-audit)

**Audit trigger:** Concept flagged with epistemic debt 0.53 in the cross-concept re-verification sweep (2026-08-11). Five evidence gaps documented at creation (2026-07-25).

**What changed since creation:**

1. **`/dream` skill implemented and operational.** `~/.grok/skills/dream/SKILL.md` v1.1.0 ships the proposed design (Pass 1: additions, Pass 2: contradictions, Pass 3: retirements dormant, Pass 4: operator profile proposals, Pass 5: skill edit proposals). Per skill provenance: "This SKILL.md is the implementation of those requirements" — direct lineage from this research concept.

2. **Auto-promotion pattern shipped.** `[[dream-pass1-auto-promotion-act-on-high-confidence]]` (2026-07-26) records the operator's correction that flipping the default from "ask permission" to "act on validated high-confidence findings" prevents the closure-pressure bypass. This is the operationalization of the receipt-preserving, anti-bloat, security-bounded design in §"How it could and should work for us."

3. **8+ dream proposals generated since 2026-08-06.** `P:/docs/dreams/` contains outputs from 2026-08-06 through 2026-08-10 (multiple per day, incremental). Concrete candidates promoted to wiki include:
   - `agent-fabricated-architectural-decisions-in-wiki-concepts` (Pass 1, 2026-08-07, 4 cross-session instances)
   - `enforcement-observability-stack-maturation-arc` (Pass 1, 2026-08-08)
   - `pydantic-model-as-contract-rule` (Pass 1, 2026-08-09, evidence-density path)
   - Multiple Pass 5 skill-edit proposals acted on

4. **Companion concepts cross-link.** `[[cross-session-transcript-mining-continuous-improvement]]`, `[[agent-improvement-loop-patterns-automated-learning-from-traces]]`, and `[[chronic-workspace-health-debt-inventory-2026-08-01]]` extend this concept's substrate (handoff + AAR + wiki + episodic-memory). The 4-tier memory architecture proposed in this concept (working/episodic/semantic/procedural) is now the wiki's organizing metaphor.

5. **5 evidence gaps RE-VERIFIED — no field-level resolution.** None of the external research gaps have closed since 2026-07-25:
   - Sleep-time compute 5× still synthetic-only (no third-party replication surfaced)
   - Mem0/Letta/Zep dispute remains vendor-driven (no independent survey)
   - Multi-agent handoff-based wiki-grounded topology: still no paper targets this directly — but workspace has now provided first-hand validation via /dream
   - Anthropic Dreams still research preview (not GA)
   - Memory poisoning: still sparse in-the-wild (CVE-2025-64439 still the only one we track)

**Debt assessment:** The debt was 0.53 at creation (frontmatter `verification: multi-source-verified` + 5 open gaps). The debt **shifts downward** for workspace-level evidence — the proposed design has been implemented and operationalized — but the field-level gaps persist. New assessment: **~0.40** (workspace-validated, field-evidence-still-missing).

**Action taken:** Added `last_re_verified: 2026-08-11` and `verification_state: workspace-validated; field-gaps-persist` to frontmatter. Annotated each evidence_gaps entry with `[FIELD — re-verified 2026-08-11: ...]`. This is a tracking-only update; no claim about the original 5 gaps has been changed.

**Specific evidence still needed to drop debt below 0.25:**
- Third-party production replication of Letta/Anthropic 5× sleep-time compute claim (vendor-independent measurement)
- A paper specifically targeting handoff-based wiki-grounded fleet consolidation (would obsolete the design; per the falsifier, would shift recommendation from meta-skill to adopt)
- Independent (non-vendor-funded) survey of memory-management benchmarks (would resolve Mem0/Letta/Zep dispute)
- CVE or in-the-wild incident showing memory poisoning moving from PoC to common exploitation (would require formal verification add-on to the design)

**Companion concept re-audit recommended:** `[[agent-improvement-loop-patterns-automated-learning-from-traces]]` should also be re-verified — it cites this concept and has its own debt state to check.
