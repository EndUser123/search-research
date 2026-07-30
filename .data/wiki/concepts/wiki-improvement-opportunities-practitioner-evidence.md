---
title: "Wiki improvement opportunities: practitioner evidence for agent knowledge bases"
created: 2026-07-29
source: session-019fb177 (/www research)
tags: [wiki, knowledge-base, pkm, agent-memory, improvement, practitioner-evidence, second-brain, rot, staleness]
summary: >
  Research across PKM practitioners, AI agent memory engineers, and Obsidian/Logseq
  GitHub issues reveals five dominant failure modes for agent knowledge bases:
  capture-without-reflection, abandonment cycles, knowledge rot, data-loss, and
  scale breakdown. The highest-signal finding is that LLM-generated context files
  measurably hurt agent performance (-3%), while even human-written ones give
  only marginal benefit (+4%). Optimal design is small, stable-content-only,
  deterministic-curated. Specific improvements for our wiki: front-matter tier
  tagging, periodic prune pass, promotion discipline from concept→AGENTS.md,
  and encoding staleness detection as deterministic tooling.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://arxiv.org/abs/2602.11988 (Evaluating AGENTS.md, 2026 — the disconfirming finding)
  - https://news.ycombinator.com/item?id=47034087 (HN thread on the paper, 232 points)
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (Karpathy LLM-wiki pattern)
  - https://news.ycombinator.com/item?id=44402470 (HN: "I deleted my second brain," 598 points)
  - https://news.ycombinator.com/item?id=17892731 (HN: "Ask HN: How to organize personal knowledge?")
  - https://donaldmucci.com/2026/05/10/rot-is-eating-your-knowledge-base/ (ROT framework)
  - https://www.gb-advisors.com/blog/knowledge-base-governance-why-it-decays-and-how-to-fix-it (KB governance)
  - https://zylos.ai/en/research/2026-06-08-agent-memory-consolidation-selective-retention-forgetting/ (Agent memory survey)
  - https://www.augmentcode.com/guides/agent-memory-vs-context-engineering (Persistence matrix)
  - https://www.langchain.com/blog/how-to-give-your-agent-memory (LangChain cognitive architecture)
relations:
  - target: wiki/concepts/agent-memory-systems.md
    type: extends
  - target: wiki/concepts/capability-wiki-write.md
    type: complements
  - target: wiki/concepts/capability-wiki-query.md
    type: complements
---

# Wiki improvement opportunities: practitioner evidence for agent knowledge bases

## Decision context

**Why this research was needed:** the operator asked "can we improve /wiki? What do people like and don't like?" The wiki (`P:/.data/wiki/concepts/`, ~400 concept files) is the workspace's durable knowledge store for a fleet of AI agents. The question is whether the current design — markdown files, frontmatter, `validate_wiki_entry.py`, manual `/wiki` invocation — aligns with what practitioners have learned about knowledge base design, or whether there are structural improvements grounded in real-world evidence.

This is NOT a "should we rebuild the wiki" question. The existing design is sound on multiple axes (see "What we already do right" below). The question is: what specific, evidence-backed improvements would make the content it captures better, the use of the system better, and the results better?

## What practitioners LIKE (patterns that work)

### 1. Atomic, densely-linked notes (Evergreen Notes / Zettelkasten)
One idea per note, written in your own words, linked to ≥2 other notes. Andy Matuschak's framework and Luhmann's 90,000-slip Zettelkasten are the canonical proof points. The structural cost is low (titles emerge from ideas) while retrieval compounds over time. **Our wiki already implements this** — `validate_wiki_entry.py` enforces ≥3 `[[wikilinks]]`.

### 2. Local-first plain-text + git (Karpathy's LLM-wiki pattern)
"The wiki is just a git repo of markdown files — you get version history, branching, and collaboration for free." Two reviewers contrasted this with Notion's export pain and Roam's missing features. **Our wiki already does this** — markdown + git commits after every write.

### 3. LLM as bookkeeper, not thinker (Karpathy)
"The tedious part of maintaining a knowledge base is not the reading or thinking — it's the bookkeeping. Humans abandon wikis because maintenance grows faster than value. LLMs don't get bored, don't forget cross-references, and can touch 15 files in one pass." **Our wiki's `/wiki` auto-link + `/skill-prune` pattern already implements this** — the agent does the bookkeeping.

### 4. Inbox-first capture with deferred processing
Dump everything to a single inbox with no decisions, then process later. Capture takes ≤5 seconds; processing happens in a calmer mindset. **Our `WIKI:` marker pattern (added this session) partially implements this** — markers accumulate during work, `/wiki` runs at session boundaries.

### 5. Schema files as wiki protocol (CLAUDE.md / AGENTS.md / SCHEMA.md)
A single document defines structure, conventions, and workflows. "It's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot." **Our `SCHEMA.md` + SKILL.md already implement this.**

### 6. Three-type memory taxonomy (semantic / episodic / procedural)
LangChain's cognitive architecture maps: semantic = facts/knowledge, episodic = past interactions, procedural = instructions/workflows. Their design note: "Many of the most visible improvements in agent behavior come from procedural memory" — i.e., turning "agent formats wrong" into a clearer rule or skill. **Our wiki structure maps 1:1**: `concepts/` ≈ semantic, `log.md` ≈ episodic, `skills/` + `handoffs/` ≈ procedural.

## What practitioners DON'T LIKE (failure modes and abandonment reasons)

### 1. Capture-without-reflection (the dominant PKM failure)
From HN (598 points, "I deleted my second brain"): "In trying to remember everything, I outsourced the act of reflection. I didn't revisit ideas. I didn't interrogate them. I filed them away and trusted the structure. The more my system grew, the more I deferred the work of thought to some future self who would sort, tag, distill, and extract the gold. That self never arrived."

The mechanism: capture feels productive but isn't — it's deferred thinking. The system grows without compounding. **Risk for our wiki:** if `/wiki` fires on every session without quality gating, the concepts directory fills with thin summaries that no one re-reads.

### 2. Knowledge rot (ROT: Redundant / Outdated / Trivial)
Enterprise research shows 30–60% of KB content is ROT. "Content accumulates indefinitely because nothing is ever reviewed, archived, or disposed." For AI-augmented retrieval, this is newly critical: "AI doesn't distinguish between current and outdated, approved and draft, authoritative and redundant. If 40% of your content is ROT, roughly 40% of what AI finds is noise."

**Risk for our wiki:** with ~400 concept files and no active retirement process, concepts from early sessions may describe states the operator has since abandoned. The retirement check in `/wiki` is manual and runs per-write, not periodically across the whole corpus.

### 3. The AGENTS.md paper — context files measurably hurt performance (the disconfirming finding)
The most directly relevant research: arXiv 2602.11988 evaluated AGENTS.md files across multiple coding agents and LLMs. Findings: "developer-provided files only marginally improve performance compared to omitting them entirely (+4% average), while LLM-generated context files have a small negative effect (-3%)." Practitioner commentary on HN (47034087): "Every single LLM-generated AGENTS.md I've seen wrote about the obvious things — the literal opposite of what you want" and "If it's longer than 200 lines, you're certainly doing it wrong."

**Implication for our wiki:** the content that helps most is **non-obvious constraints that can't be inferred from code** — not summaries of what the code does. If our wiki concepts describe "how the system works" (redundant with the code), they add noise. If they describe "why we chose X over Y" or "this looks like X but is actually Y" (non-obvious), they help.

### 4. Abandonment cycles (started-and-stopped, repeatedly)
From r/secondbrain: "I have a graveyard of abandoned second-brain projects: Notion (abandoned after 3 weeks), Obsidian + 20 plugins (1 month, then overwhelming)." From HN: "Organizing your notes doesn't become a goal itself... focus on the content and linking, not on the tools themselves." From r/artificial: "I eventually realized the vault isn't a second brain, it's just a staging area for the first one."

**Risk for our wiki:** `/skill-prune` exists but is rarely run. The wiki grows monotonically without active pruning. At some scale threshold (~3,500 nodes per the Logseq issues), retrieval degrades.

### 5. Scale breakdown (~3,500-node ceiling)
Logseq GitHub issue #2089: unusable at 3,500 markdown nodes — graph view hangs, Chromium pegged at >1 CPU. Obsidian handles the same count fine because it's file-based without a graph parser. **Our wiki uses grep + directory walk, which scales better than graph-based tools**, but the principle holds: at some size, unpruned growth degrades retrieval quality.

### 6. Wrong-layer placement
Augment Code's persistence matrix catalogs the anti-pattern: feature decisions in AGENTS.md (file grows past 200 lines, adherence drops); team conventions in personal memory only (teammates don't see them); evolving feature intent in static files (spec rot); full chat history as memory (mostly noise). **Risk for our wiki:** if concepts that should be rules in AGENTS.md stay as wiki concepts, the agent may not consistently apply them. The promotion path (concept → AGENTS.md rule) is currently ad hoc.

## What this means for our workspace — specific improvements

### Improvement 1: Encode a "non-obvious" quality gate (addresses capture-without-reflection + AGENTS.md paper)

The AGENTS.md paper's key finding: obvious content hurts. The current `validate_wiki_entry.py` checks line count, frontmatter, and link density — but not whether the content is non-obvious.

**Proposed:** add a validator check that scans for "obvious content" signals — e.g., a concept that merely restates what the code does (no decision, no rationale, no falsifier). This is heuristic, not deterministic, but a warning-level check would surface thin concepts for review.

### Improvement 2: Periodic prune pass with staleness scoring (addresses knowledge rot)

The wiki has no automated staleness detection. Concepts accumulate without retirement.

**Proposed:** a `/wiki --prune` pass that computes a staleness score per concept: `last_verified_age × (1 / backlink_count) × importance_weight`. Surface the bottom quartile for retirement review. This mirrors the Knowledge Freshness Index (KFI) pattern from KB governance literature and the importance-scoring formula from Park et al. 2023.

Connects to [[adaptive-expansion-evidence-triggered-conditional-steps]] — the prune pass should fire when the concept count exceeds a threshold or when `/skill-prune` surfaces stale entries, not on every invocation.

### Improvement 3: Front-matter tier tagging (addresses retrieval quality)

Production memory systems use tiered lifecycle: HOT (session-loaded), WARM (on-demand), COLD (append-only historical).

**Proposed:** add a `tier: hot|warm|cold` field to concept frontmatter. HOT = always-relevant identity/invariant concepts (read at session start). WARM = domain-specific concepts (read on-demand). COLD = historical context (rarely re-read). This makes the retrieval target explicit rather than implicit.

### Improvement 4: Promotion discipline from concept → AGENTS.md (addresses wrong-layer placement)

When a concept is genuinely team-wide and stable (read every session, never changes), it belongs in AGENTS.md, not in `concepts/`. The current promotion path is ad hoc.

**Proposed:** when `/skill-prune` or `/wiki --prune` finds a concept that (a) has been read in ≥5 sessions, (b) hasn't changed in ≥30 days, and (c) contains a rule rather than a finding, suggest promotion to AGENTS.md. This is the Augment Code "promotion path" pattern.

### Improvement 5: Capture trigger taxonomy (addresses capture noise)

The `WIKI:` marker currently fires on "durable finding or architectural decision." The research suggests a more explicit taxonomy: corrections, design decisions, recurring failure patterns, transferable techniques, non-obvious constraints.

**Proposed:** enumerate the trigger types in the wiki SKILL.md so the agent doesn't fire on every finding indiscriminately. Each trigger type has a different quality bar: a correction needs evidence it was applied; a design decision needs a steelman and falsifier.

### Improvement 6: Conflict resolution schema (addresses version divergence)

The research highlights "three versions of the same policy with different content — which is authoritative?" The wiki has `superseded_by` in retirement checks but doesn't enforce it.

**Proposed:** make `superseded_by:` a first-class frontmatter field that the query path respects — when retrieving concepts, skip superseded ones unless explicitly requested. This is Mem0's ADD/UPDATE/DELETE/NOOP model applied to markdown.

## What we already do right (don't fix these)

The research validated several existing design choices:

- **Boring schema (markdown + grep) over vector stores.** "SQLite or Postgres is usually enough when memory count is modest and you care about correctness." Our design is correctly boring.
- **Atomic writes (git commit after every concept write).** Prevents the data-loss failure mode that plagues Logseq sync.
- **Manual `/wiki` invocation with quality gate.** Better than auto-capture without review.
- **Cognitive taxonomy (concepts/log/skills).** Maps to the semantic/episodic/procedural split that LangChain validated.
- **SCHEMA.md as protocol.** Aligns with the "schema files as wiki protocol" pattern.
- **File-based, not graph-based.** Scales better than Logseq's graph parser at 3,500+ nodes.
- **`validate_wiki_entry.py` as deterministic check.** Aligns with the HN practitioner rule "prefer deterministic checks over prose rules."

## Receipts

- `validate_wiki_entry.py` — enforces ≥3 `[[wikilinks]]`, ≥50 non-empty lines, frontmatter fields. (source: ran on this entry, PASS on structure)
- `SCHEMA.md` §4 — quality gate for findings and decisions. (source: read during `/wiki` skill invocation this session)
- `/skill-prune` SKILL.md — exists but rarely run per AGENTS.md maintenance reminders. (source: `P:\.agents\skills\skill-prune\SKILL.md`, listed in session skill catalog)
- `P:/.data/wiki/concepts/` — ~400 concept files, no automated retirement process. (source: `Get-ChildItem` during wiki query phase)
- [INFERENCE] The `WIKI:` marker auto-capture pattern added this session (`~/.grok/AGENTS.md` "Wiki auto-capture") partially addresses the inbox-first capture pattern but has not been validated across multiple sessions yet.

## Falsifier

These improvements are wrong if:
1. The wiki's current retrieval quality (grep + directory walk) is already sufficient for the agent's needs — adding tiers and staleness scores would add ceremony without improving results.
2. The concept count stays below the scale threshold (~3,500) — pruning is unnecessary until growth becomes a retrieval problem.
3. The `WIKI:` marker auto-capture pattern (added this session) already solves the capture-without-reflection problem — the quality gate is the right place to enforce non-obviousness, not a new validator check.

The specific observation that would disconfirm this entry: if a future session reports that grep-based retrieval over ~400 concepts finds the right concept within 2-3 reads every time, the improvements (tiers, prune, promotion) are premature optimization.

## Sources

- [Evaluating AGENTS.md (arXiv 2602.11988)](https://arxiv.org/abs/2602.11988) — the disconfirming finding: context files give only marginal benefit (+4%) and LLM-generated ones hurt (-3%)
- [HN: "I deleted my second brain" (598 points)](https://news.ycombinator.com/item?id=44402470) — capture-without-reflection failure mode
- [HN: "Ask HN: How to organize personal knowledge?"](https://news.ycombinator.com/item?id=17892731) — search > taxonomy, organization-as-goal is the anti-pattern
- [HN: Evaluating AGENTS.md thread (232 points)](https://news.ycombinator.com/item?id=47034087) — practitioner commentary on the paper
- [Karpathy LLM-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the file-based agent wiki pattern
- [ROT is eating your knowledge base](https://donaldmucci.com/2026/05/10/rot-is-eating-your-knowledge-base/) — 30-60% ROT in enterprise KBs
- [KB governance: why it decays](https://www.gb-advisors.com/blog/knowledge-base-governance-why-it-decays-and-how-to-fix-it) — event-driven review, category ownership
- [Agent memory consolidation survey](https://zylos.ai/en/research/2026-06-08-agent-memory-consolidation-selective-retention-forgetting/) — importance scoring, differential decay, tiered lifecycle
- [Augment Code: agent memory vs context engineering](https://www.augmentcode.com/guides/agent-memory-vs-context-engineering) — three-layer persistence, wrong-layer placement
- [LangChain: how to give your agent memory](https://www.langchain.com/blog/how-to-give-your-agent-memory) — cognitive taxonomy, procedural memory is highest-leverage
- Related: [[agent-memory-systems]] — prior wiki coverage of agent memory architectures
- Related: [[capability-wiki-write]] — the wiki-write capability design
- Related: [[capability-wiki-query]] — the wiki-query capability design
