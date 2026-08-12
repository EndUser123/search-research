# Handoff: Wiki broken wikilinks + orphan concept pruning

**Created:** 2026-08-12
**Session:** 019fe3ff-afbc-71c1-b2a3-3cfbccfd2bc7
**Status:** OPEN
**Priority:** LOW (LATER)
**Assignee:** unassigned

## Objective

Fix broken wikilinks, prune orphan concepts, and improve the wiki link checker accuracy.

## Findings from /go batch (2026-08-12)

### Broken wikilinks (reported as 195, actual ~30)

Ran `P:/tmp/check_wikilinks.py` against 1361 files. Results:

| Category | Count | Action needed |
|----------|-------|---------------|
| Wiki-yt ingest artifacts (research questions parsed as wikilinks) | 74 refs | Fix checker to reject slugs with apostrophes/spaces |
| Template placeholders in code blocks (`<concept>`, `<concept-slug>`, `page`, `x`) | 20+ refs | Fix checker to skip code blocks |
| Path-style references (`wiki/concepts/slug`) | 30 refs | Fix checker to resolve path-style refs |
| Genuine missing concepts | ~30 | Investigate and create or fix |

**Root cause:** the checker regex `\[\[(.+?)\]\]` over-matches. It should:
1. Skip code blocks (between ``` markers)
2. Skip template placeholders (`<...>`)
3. Validate slug format (`^[a-z0-9][a-z0-9-]*$`)
4. Resolve `wiki/concepts/slug` path-style references

### Orphan concepts (reported as 476)

1153 total concepts. ~476 have no inbound links. These need per-concept review:
- Some are wiki-yt ingest outputs that could be merged
- Some are genuinely orphaned decisions that could be archived
- Some are load-bearing concepts that just lack inbound links (not a problem)

**Cannot be done mechanically.** Needs `/skill-prune` with careful review.

### Scanner improvement needed

The wiki link checker at `P:/tmp/check_wikilinks.py` (quick implementation) needs to replace or improve whatever `/maintain`'s fleet_health uses. The improvement:
1. Skip code blocks
2. Validate slug format
3. Resolve path-style refs
4. Report separately: "genuine broken" vs "scanner artifact"

## Scope

1. **Improve wiki link checker** — fix regex to produce accurate counts
2. **Fix ~30 genuine broken wikilinks** — create missing concepts or update links
3. **Run `/skill-prune`** — review and archive/merge orphan concepts
4. **Re-run `/maintain`** — verify the broken-wikilink count is accurate

## Acceptance criteria

- Wiki link checker reports ≤10 genuine broken wikilinks (not 195)
- `/skill-prune` has been run with dispositions for the top 50 orphans
- `/maintain` fleet health score improves (broken wikilinks no longer CRITICAL)

## Files

- Checker script: `P:/tmp/check_wikilinks.py` (quick implementation, needs improvement)
- Wiki concepts: `P:/.data/wiki/concepts/` (1153 files)
- Fleet health checker: `C:/Users/brsth/.grok/skills/maintain/__lib/fleet_health.py`
