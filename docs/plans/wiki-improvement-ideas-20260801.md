# Wiki Improvement Ideas — Session 2026-08-01

Source: Karpathy LLM Wiki gist, Google OKF v0.2 spec, Cole Medin KB repo, /www research.
Critique: /tp fresh-lens subagent review (subagent_id: 019fbe80).

## All 20 ideas with positive ROI

### Architecture and organization

1. **Entity/concept separation** — split concepts/ into concepts/ (ideas) + entities/ (tools/products) or add type: entity frontmatter
   - /tp: RESHAPE — `entities/` folder already exists (4 pages). Add `type:` frontmatter field instead.

2. **OKF typed concept hierarchy** — add type: frontmatter field to drive typed queries
   - /tp: RESHAPE — use operator's ontology (concept/decision/directive/reference/entity), not OKF's

3. **Auto-generated index.md** — regenerate index on every ingest
   - /tp: AGREE (already done) — SCHEMA.md §10 already specifies `/wiki index`. Verify it runs.

### Trust and freshness

4. **stale_after: frontmatter field** — date when time-sensitive research concepts expire
   - /tp: AGREE — pair with lint Phase 3 surfacing

5. **Per-source credibility signals** — tag each source URL with credibility
   - /tp: DISAGREE — bureaucracy for solo operator. verification: field already encodes trust.

6. **generated and verified timestamps** — track last-verified date
   - /tp: RESHAPE — created: and verification: already exist. Add last_verified: for liveness.

### Operations

7. **Proactive query filing** — persist multi-paragraph chat answers into wiki pages
   - /tp: AGREE — /tp suggests hook, but I argue /capture at session boundary is better

8. **Structured lint pass** — contradiction detection + gap-filling
   - /tp: RESHAPE (mostly done) — wiki_contradiction_scan.py already runs. Wire audit_buried_facts into lint.

9. **Lint generates research suggestions**
   - /tp: AGREE (already done) — SCHEMA.md §10 Phase 3 mandates this. Verify it fires.

10. **OKF "Cited by" backlinks** — compute reverse link graph
    - /tp: AGREE — highest-leverage addition. Build wiki_backlinks.py.

### Content quality

11. **Progressive tabular synthesis** — intermediate tables before prose in wiki-yt
    - /tp: AGREE (scoped to wiki-yt)

12. **Synthesis-mode prompts** — "synthesize transferable principle" not "extract key concepts"
    - /tp: AGREE (1-line change) — DONE this session

13. **Content-type filter prompts** — skip filler/sponsorship/CTAs
    - /tp: DISAGREE — basic hygiene, already in PRE_SUMMARY_PROMPT

### Inter-source connections

14. **Cross-source synthesis** — ingesting one source should fan out updates to related pages
    - /tp: RESHAPE — targeted propagation, not mass rewrite. Use wiki_after_write.py's existing top-5 similarity.

15. **Contradiction flagging during ingest** — check new source against existing concepts
    - /tp: AGREE (v2 scope) — v1 already runs at post-write. Write v2 spec for supersession patterns.

### Visualization and navigation

16. **Interactive HTML graph visualizer** — force-directed graph of concepts
    - /tp: DISAGREE — over-engineered for solo operator. Ripgrep already answers the questions.

17. **Marp slide generation** — slide decks from wiki content
    - /tp: DISAGREE — wrong tool. Wiki is durable memory; slides are ephemeral.

18. **Dataview-style frontmatter queries** — query script for dynamic views
    - /tp: AGREE — build wiki_query.py once type: and stale_after: are stable

### Pipeline improvements

19. **Re-sync high-value notebooks** — re-run wiki-yt with fixed pipeline
    - /tp: AGREE (one-shot) — discrete task, not an ongoing feature

20. **Canonicalization pass** — detect semantic duplicate concepts
    - /tp: RESHAPE — start cheap (title + first-para Jaccard), escalate only if precision is bad

## /tp missing ideas (not in the original 20)

1. **Wiki ↔ handoffs cross-link integration** — two institutional memory stores that don't know about each other
2. **Frontmatter drift lint** — pages missing verification:, tier:, host: fields
3. **Wiki health snapshot at session start** — like active-surface.last.md for wiki
4. **Capture-from-session hook** — surface WIKI: marker candidates mid-conversation
5. **Thin-concept flag** — pages <300 chars or zero outbound links
6. **Backup strategy** — wiki is gitignored; if host dies, 790 pages die with it
7. **Bidirectional capture from /tp /aar /harvest** — their completion doesn't fire WIKI: markers
8. **Topic-cluster navigation** — group index.md by topic prefix
9. **Cold-start bootstrap view** — top 10 concepts a fresh agent should read
10. **Citation accuracy check** — verify source citations on synthesized pages are intact

## Summary

- 4 already done (#3, #8 partial, #9, #12 done this session)
- 4 rejected (#5, #13, #16, #17)
- 10 with positive ROI remaining
- 10 missing ideas surfaced by /tp critique
- Total actionable: 20 items
