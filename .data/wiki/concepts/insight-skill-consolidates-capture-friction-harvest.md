# Insight Skill Consolidates Capture, Friction, Harvest

**Decision date:** 2026-08-07
**Session:** 019fc927 → 019fd820
**Status:** ACTIVE — consolidation implemented

## Context

Improvement-finding was fragmented across 4+ skills with overlapping scope:

| Skill | What it found | Problem |
|-------|-------------|---------|
| `/capture` | 9 categories of session improvement opportunities | The largest body; deeply embedded in `/close` pipeline |
| `/friction` | Interaction + workflow friction markers | Categories 1-2 of `/capture` already covered this; `/friction`'s markers were more detailed but redundant |
| `/harvest` | Cross-session obligation tracking | CLI was non-functional (never on PATH); concept was sound but implementation absent |
| `/skill-dev` | Skill-level improvement from MEC measurement | Different lifecycle phase (skill optimization, not session improvement) |
| `/dream` | Cross-session pattern synthesis (90 days) | Different architecture (batch synthesis vs session scanning) |

The operator had to know which skill to invoke when. The `/ask` skill router couldn't recommend the right one — it presented multiple overlapping options.

## Decision

Create `/insight` — a single **mode router** skill that absorbs the improvement-finding functions of `/capture`, `/friction`, and `/harvest` into four modes:

| Mode | Replaces | Time scale |
|------|----------|-----------|
| Default | `/capture` + `/friction` | This session (9 categories + friction markers + scoring) |
| `--skills` | lightweight `/skill-dev measure` | One skill or all active skills |
| `--fleet` | `/harvest` (non-functional CLI) | 90 days (lightweight grep scan) |
| `--coverage` | `/capture` coverage check | This session only |

## Alternatives considered

- **Option A: Status quo (keep all three)** — rejected because the operator had to know which to invoke when, and the router couldn't disambiguate.
- **Option B: Rename `/capture` to `/insight` and fold friction in** — rejected because `/capture`'s 9-category structure would be confused by adding skill measurement. The mode router keeps concerns separate while unifying the entry point.
- **Option C: Consolidate all five (including `/skill-dev` and `/dream`)** — rejected because different architectures (batch synthesis, full measurement lifecycle) don't fit a session-scanning mode router. They co-exist.

## What was preserved

1. `/capture`'s 9 categories and dual-stream routing — all moved to `/insight` default mode
2. `/friction`'s detailed pattern markers and scoring rubric — enriched into categories 1-2
3. `/harvest`'s cross-session obligation concept — absorbed as `--fleet` mode (lightweight implementation, since the CLI never worked)
4. The close pipeline integration — `/close` and `/close-check` now call `/insight` instead of `/capture`

## What was deprecated (not deleted)

`/capture` and `/friction` SKILL.md files get DEPRECATED notices at the top pointing to `/insight`. Files are kept for reference.

## Falsifier

This consolidation is wrong if:
- `/insight` default mode produces fewer or lower-quality findings than `/capture` + `/fr` did separately (absorption lost signal)
- `/close` fails to find the improvement-capture step because it's looking for `/capture` not `/insight` (migration broke the pipeline)
- The operator still has to remember which mode to invoke (the 4-mode router is no simpler than 3 separate skills)
- `/harvest`'s obligation-tracking concept was needed and `--fleet` doesn't cover it

## Open decisions (deferred)

1. **`/insight --fleet` vs `/dream`**: currently co-exist (lightweight scan vs deep synthesis). If the lightweight scan proves sufficient, `/dream` could be deprecated.
2. **`/insight --skills` vs `/skill-dev measure`**: currently co-exist (quick triage vs deep measurement). If the quick assessment produces the same quality, absorb fully.

## Related

- `[[proactive-improvement-opportunity-scanner]]` — the original `/capture` concept
- `[[skill-graph]]` — dependency graph (auto-regenerates from frontmatter)
- Handoff: `P:/docs/handoffs/insight-skill-consolidation-019fc927-20260807/HANDOFF.md`
