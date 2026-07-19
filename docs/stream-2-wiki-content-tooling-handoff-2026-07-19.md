# Stream 2: Wiki content + tooling handoff

| Field | Value |
|---|---|
| **Stream** | Wiki content ingestion + contradiction scan + QMD syntax fix |
| **Priority** | HIGH — content is underdeveloped relative to governance; contradiction scan is novel |
| **Status** | Not started; design complete, implementation pending |
| **Effort** | ~2 hours (two parallel subagents) |
| **Delegation** | Subagent A (QMD fix + contradiction scan); Subagent B (ADR ingest) |

## Goal

Three deliverables: (1) fix QMD CLI syntax errors in docs, (2) build a contradiction-scan script that runs after every wiki page write, (3) ingest existing ADRs into the wiki as discoverable concept pages.

## Background

### QMD syntax error

SCHEMA.md §11 and the handoff at `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md` both reference `qmd update --collection wiki`. The `update` subcommand does NOT accept `--collection`; correct syntax is `qmd update` (no args, updates default) or `qmd update wiki` (positional). The `--collection` flag works for `search` and `status` but NOT for `update`. This was discovered by another LLM session running `/wiki` ingest.

### Contradiction scan

From the session's research: nobody in the PKM ecosystem has active contradiction detection at ingest time. The `@contradicts` typed wikilink exists in SCHEMA.md §7 but nothing detects contradictions automatically. The scan would be the first of its kind in our vault.

### ADRs → wiki

Architectural Decision Records live at `P:/docs/adrs/` (and possibly `P:/.claude/arch_decisions/`). These are durable architectural decisions — exactly what the wiki is for. Currently invisible to QMD search.

## Deliverables

### 1. QMD syntax fix (~5 min)

**Files to fix:**
- `P:/.data/wiki/SCHEMA.md` §11 — replace `qmd update --collection wiki` with `qmd update`
- `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md` — same fix
- Any other doc referencing `qmd update --collection`

**Verify:** `rg 'qmd update --collection' P:/.data/wiki P:/docs` returns zero hits after fix.

### 2. Contradiction scan script (~100 lines Python)

**File:** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_contradiction_scan.py`

**Design:**
1. Takes a page path as input
2. Extracts key claims from `## Summary` and `## Key Findings` sections (regex on bullet points)
3. Extracts the page's `tags:` frontmatter
4. QMD-searches the wiki for pages with overlapping tags: `qmd search --collection wiki "<tag1> <tag2>"`
5. For each overlapping page (top 5), compares claims for semantic opposition using heuristics:
   - Negation patterns: "X is true" vs "X is false" / "X is broken" vs "X is fixed"
   - Supersession patterns: "X was fixed in v1.2" vs "X is broken"
   - Version-drift patterns: "requires v2.1" vs "works on v1.0"
6. If contradiction detected: inject `[[page]]@contradicts` into `## Related` + print warning
7. Best-effort: no-op if no overlaps or no contradictions

**Integration:** Called alongside `wiki_after_write.py` in SCHEMA.md §10 Ingest step 6.

**External review:** `/agy` reviews the script design: "Is deterministic claim-extraction + tag-overlap the right approach for contradiction detection, or should it use embedding similarity? What are the false-positive risks?"

### 3. ADR ingest (~30 min)

**Source:** `P:/docs/adrs/` — list files, ingest each as a concept page.

**Format:** Each ADR becomes a wiki page with:
- `title:` from the ADR header
- `tags: [adr, architecture, decision]` + topic-specific tags
- `source:` pointing to the original `P:/docs/adrs/<file>`
- Body: Summary + Key Findings (the decision + rationale + alternatives rejected)
- `## Related` cross-links to other ADRs or concept pages

**Dedup:** Check `P:/.data/wiki/concepts/` for existing pages that already cover the same decision (grep for ADR title or key terms).

**Post-ingest:** Run `qmd update` (correct syntax!) to index the new pages. Run auto-link on each.

## Dependencies

- QMD syntax fix MUST happen before ADR ingest (so the post-ingest QMD update step uses correct syntax).
- Contradiction scan is independent; can be built in parallel.

## Verification criteria

1. `rg 'qmd update --collection' P:/.data/wiki P:/docs` returns 0 hits
2. `wiki_contradiction_scan.py` exists, runs without error on a test page, and produces sensible output (either "no contradictions" or flagged contradictions with wikilinks)
3. ADR pages exist in `P:/.data/wiki/concepts/` with `type: adr` or `adr` tag
4. `qmd search --collection wiki "<adr-topic>"` returns the new pages

## Source references

- `P:/.data/wiki/SCHEMA.md` — canonical conventions (§7 typed wikilinks, §10 Ingest procedure)
- `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md` — Q2 closure section
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_after_write.py` — existing auto-link script (pattern to follow for the contradiction scan)
- `P:/docs/adrs/` — ADR source directory
