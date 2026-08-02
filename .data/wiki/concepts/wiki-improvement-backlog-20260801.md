---
title: "Wiki Improvement Ideas — 2026-08-01 Backlog"
created: 2026-08-01
source: session-20260801
tags: [backlog, wiki-improvement, ideas, reference, okf, karpathy]
summary: >
  20 wiki improvement ideas sourced from Karpathy's LLM Wiki gist, Google's
  OKF v0.2 spec, Cole Medin's KB repo, and /www research — plus 10 additional
  ideas surfaced by /tp critique. Each idea has a verdict (AGREE/DISAGREE/
  MERGE/RESHAPE) and status (DONE/REJECTED/REMAINING). This is the durable
  backlog for wiki improvement work. Future sessions asking "what should we
  improve in the wiki?" should start here.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (Karpathy LLM Wiki)
  - https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf (OKF v0.2)
  - https://github.com/coleam00/cole-medin-knowledge-base (Cole Medin KB)
  - session-20260801 /www research (3 parallel agents on map-reduce synthesis)
relations:
  - target: wiki/concepts/llm-wiki-knowledge-pattern.md
    type: extends
  - target: wiki/concepts/open-knowledge-format-okf.md
    type: extends
  - target: wiki/concepts/lint-as-forward-looking-research-source.md
    type: related
  - target: wiki/concepts/completeness-over-curation-recommendation-discipline.md
    type: related
---

# Wiki Improvement Ideas — 2026-08-01 Backlog

## Decision context

**Why this backlog exists:** During session 019fbdfb (2026-08-01), three knowledge-base sources were ingested (Karpathy LLM Wiki, OKF v0.2, Cole Medin KB) and a /www research run investigated synthesis pipeline best practices. These produced 20 concrete improvement ideas for our wiki. A /tp fresh-lens critique found 10 additional missing ideas. This page is the durable backlog so future sessions don't re-derive what was already evaluated.

This extends the [[llm-wiki-knowledge-pattern]] and [[open-knowledge-format-okf]] concepts by translating their architectural principles into actionable improvements for our specific vault. The [[lint-as-forward-looking-research-source]] concept (idea #9, implemented) and [[completeness-over-curation-recommendation-discipline]] (rule that ensured all 30 ideas are listed, not curated) are both outputs of this backlog session.

## All ideas with positive ROI

### Architecture and organization

1. **Entity/concept separation** — split concepts/ into concepts/ (ideas) + entities/ (tools/products) or add `type: entity` frontmatter
   - /tp: RESHAPE — `entities/` folder already exists (4 pages). Add `type:` frontmatter field instead.
   - Status: REMAINING

2. **OKF typed concept hierarchy** — add `type:` frontmatter field to drive typed queries
   - /tp: RESHAPE — use operator's ontology (concept/decision/directive/reference/entity), not OKF's
   - Status: REMAINING

3. **Auto-generated index.md** — regenerate index on every ingest
   - /tp: AGREE — SCHEMA.md §10 already specifies `/wiki index`. Verify it runs.
   - Status: VERIFY

### Trust and freshness

4. **`stale_after:` frontmatter field** — date when time-sensitive research concepts expire
   - /tp: AGREE — pair with lint Phase 3 surfacing
   - Status: REMAINING

5. **Per-source credibility signals** — tag each source URL with credibility
   - /tp: DISAGREE — bureaucracy for solo operator. `verification:` field already encodes trust.
   - Status: REJECTED

6. **`generated` and `verified` timestamps** — track last-verified date
   - /tp: RESHAPE — `created:` and `verification:` already exist. Add `last_verified:` for liveness.
   - Status: REMAINING

### Operations

7. **Proactive query filing** — persist multi-paragraph chat answers into wiki pages
   - /tp: AGREE — /capture at session boundary is better than a mid-conversation hook
   - Status: REMAINING

8. **Structured lint pass** — contradiction detection + gap-filling
   - /tp: RESHAPE (mostly done) — `wiki_contradiction_scan.py` already runs. Wire `audit_buried_facts.py` into lint.
   - Status: REMAINING (wire audit_buried_facts)

9. **Lint generates research suggestions**
   - /tp: AGREE — DONE. SCHEMA.md §10 Phase 3 mandates this.
   - Status: DONE

10. **OKF "Cited by" backlinks** — compute reverse link graph
    - /tp: AGREE — highest-leverage addition. Build `wiki_backlinks.py`.
    - Status: REMAINING (HIGH PRIORITY)

### Content quality

11. **Progressive tabular synthesis** — intermediate tables before prose in wiki-yt
    - /tp: AGREE (scoped to wiki-yt)
    - Status: REMAINING

12. **Synthesis-mode prompts** — "synthesize transferable principle" not "extract key concepts"
    - /tp: AGREE — DONE this session (PRE_SUMMARY_PROMPT updated).
    - Status: DONE

13. **Content-type filter prompts** — skip filler/sponsorship/CTAs
    - /tp: DISAGREE — already in PRE_SUMMARY_PROMPT
    - Status: DONE (pre-existing)

### Inter-source connections

14. **Cross-source synthesis** — ingesting one source should fan out updates to related pages
    - /tp: RESHAPE — targeted propagation via `wiki_after_write.py`'s top-5 similarity, not mass rewrite
    - Status: REMAINING

15. **Contradiction flagging during ingest** — check new source against existing concepts
    - /tp: AGREE (v2 scope) — v1 runs at post-write. Write v2 spec for supersession patterns.
    - Status: REMAINING (v2)

### Visualization and navigation

16. **Interactive HTML graph visualizer** — force-directed graph of concepts
    - /tp: DISAGREE — over-engineered for solo operator. Ripgrep already answers the questions.
    - Status: REJECTED

17. **Marp slide generation** — slide decks from wiki content
    - /tp: DISAGREE — wrong tool. Wiki is durable memory; slides are ephemeral.
    - Status: REJECTED

18. **Dataview-style frontmatter queries** — query script for dynamic views
    - /tp: AGREE — build `wiki_query.py` once `type:` and `stale_after:` are stable
    - Status: REMAINING

### Pipeline improvements

19. **Re-sync high-value notebooks** — re-run wiki-yt with fixed pipeline
    - /tp: AGREE (one-shot) — discrete task, not ongoing feature
    - Status: REMAINING

20. **Canonicalization pass** — detect semantic duplicate concepts
    - /tp: RESHAPE — start cheap (title + first-para Jaccard), escalate only if precision is bad
    - Status: REMAINING

## Missing ideas (from /tp critique, not in original 20)

21. **Wiki ↔ handoffs cross-link integration** — two institutional memory stores that don't know about each other. Build `wiki_link_handoffs.py`.
    - Status: REMAINING (HIGHEST LEVERAGE)

22. **Frontmatter drift lint** — pages missing `verification:`, `tier:`, `host:` fields. Mechanical, zero-LLM.
    - Status: REMAINING

23. **Wiki health snapshot at session start** — like `active-surface.last.md` for wiki. 10 lines in `wiki_health_check.py`.
    - Status: REMAINING

24. **Thin-concept flag** — pages <300 chars or zero outbound links. Pruning signal.
    - Status: REMAINING

25. **Backup strategy** — wiki is gitignored; if host dies, 790+ pages die with it.
    - Status: REMAINING

26. **Bidirectional capture from /tp /aar /harvest** — their completion doesn't fire WIKI: markers.
    - Status: REMAINING

27. **Topic-cluster navigation** — group index.md by topic prefix or tags.
    - Status: REMAINING

28. **Cold-start bootstrap view** — top 10 concepts a fresh agent should read.
    - Status: REMAINING

29. **Citation accuracy check** — verify source citations on synthesized pages are intact.
    - Status: REMAINING

30. **Batch-add completeness-over-curation pointer to output skills** — /tp, /www, /review, /todo, /capture, /aar, /skill-prune, /harvest, /friction, /check.
    - Status: PARTIALLY DONE (/tp done this session; 10 remaining)

## Summary

| Category | Count |
|---|---|
| DONE (implemented this session) | 4 (#9, #12, #13, #30 partial) |
| REJECTED | 3 (#5, #16, #17) |
| VERIFY (already exists, check if running) | 1 (#3) |
| REMAINING (positive ROI, not yet implemented) | 22 |

**Highest leverage remaining:** #10 (backlinks), #21 (wiki↔handoffs), #22 (frontmatter lint), #23 (wiki snapshot), #25 (backup).

## What this means for our workspace

This backlog is the single source of truth for wiki improvement work. When a future session asks "what should we improve?" or `/todo` surfaces wiki-related work, this page provides the pre-evaluated list with verdicts. Pick items from the REMAINING set, implement, then update the status here.

The 4 DONE items (#9, #12, #13, #30-partial) were completed in session 019fbdfb. The 3 REJECTED items (#5, #16, #17) were evaluated and dismissed with reasoning — don't re-propose them. The 22 REMAINING items are the actionable backlog, ordered by leverage in the summary table above.

## Falsifier

If this backlog is not referenced by any future session within 6 months, the ideas are either all implemented or no longer relevant. At that point, run `/skill-prune` to archive or retire this page.

## Receipts

- `P:/.data/wiki/SCHEMA.md` §10 Lint Phase 3 — idea #9 (research suggestions) implemented here
- `P:/.agents/skills/wiki-yt/scripts/synthesize_subtopics.py` PRE_SUMMARY_PROMPT — idea #12 (synthesis-mode prompt) implemented here
- `P:/.agents/skills/wiki-yt/scripts/synthesize_subtopics.py` `split_with_overlap()` — idea #13 (content filter) grounding rules already present
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — idea #30 (/tp completeness pointer) implemented here
- `P:/docs/dreams/2026-08-01-dream.md` — /tp critique subagent ID 019fbe80 produced the 10 missing ideas
- Original `P:/docs/plans/wiki-improvement-ideas-20260801.md` — now superseded by this wiki concept (which is discoverable via grep)

## Sources

- [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the pattern that launched the LLM wiki movement
- [OKF v0.2 spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) — Google's universal knowledge format
- [Cole Medin KB](https://github.com/coleam00/cole-medin-knowledge-base) — reference implementation of channel-to-KB pipeline
- /www research session 2026-08-01 — 3 parallel agents on map-reduce, context windows, video synthesis
- /tp critique subagent 019fbe80 — fresh-lens review of all 20 ideas

## Auto-related

- [[skill-graph]]
- [[wiki-improvement-opportunities-practitioner-evidence]]
- [[skill-catalog]]
- [[dynamic-wiki-driven-skill-configuration]]
- [[improvement-surfacing-fleet-fragmentation-routing-and-meta-improvement]]

