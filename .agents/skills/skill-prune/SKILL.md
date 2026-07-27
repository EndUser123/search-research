---
name: skill-prune
description: >
  Knowledge hygiene for skills and wiki concepts — detect stale, duplicate,
  and drifted entries. Proposes merges, archives, and promotions. Use when
  the skill catalog is cluttered, after bulk skill additions, or monthly.
  Adapted from Claude-side "garden" for Grok Build (qmd + index_skills.py
  as the inventory layer instead of CKS).
host: both
---

# /skill-prune — Skill and wiki knowledge hygiene

Keep the skill catalog and wiki vault clean and high-signal by detecting
stale, duplicate, and drifted entries. Proposes actions; applies only on
operator confirmation.

## When to use

- Monthly maintenance cadence
- After bulk skill additions (e.g., marketplace installs, session builds)
- When skill catalog exceeds growth threshold (currently 976 skills)
- When wiki search returns stale/duplicate results

## When NOT to use

- Mid-task (this is maintenance, not development)
- Single-skill addition (no clutter to prune)

## Pipeline (5 phases, each with STOP)

```
PHASE 1: INVENTORY
  ── index_skills.py (catalog) + qmd search (wiki)
  ── list all skills with grok_enabled/claude_enabled state
  ── list wiki concepts with age + tag distribution
  ↓ STOP: present inventory before analysis

PHASE 2: ISSUE DETECTION
  ── duplicate skills: same name across scopes (catalog shows 3+ nlm-to-wiki)
  ── stale wiki concepts: >6 months old, never cited in qmd search results
  ── disabled skills still indexed: grok_enabled=false or claude_enabled=false
  ── orphan skills: SKILL.md references scripts/files that don't exist
  ── drifted concepts: wiki content contradicts current code/state
  ↓ STOP: present findings before proposing actions

PHASE 3: ACTION PROPOSALS
  ── duplicate skills → propose canonical (prefer .agents/skills/ over plugin caches)
  ── stale concepts → propose archive (mark status: archived, don't delete)
  ── disabled skills → propose removal from catalog (hide, don't delete source)
  ── orphan skills → propose fix or retirement
  ↓ STOP: await operator confirmation

PHASE 4: APPLY (operator-confirmed actions only)
  ── merge duplicates, archive stale, hide disabled, fix orphans
  ── reindex after changes

PHASE 5: VERIFY + SUMMARY
  ── re-scan to verify changes applied
  ── summary: N merged, N archived, N hidden, N fixed
```

## Inventory sources (Grok-specific)

| Source | What it provides | Command |
|---|---|---|
| `index_skills.py` | Full skill catalog with scope + enable state | `python P:/.data/wiki/scripts/index_skills.py` |
| qmd search | Wiki concept coverage + staleness | `qmd search --collection wiki "<topic>" --top-k N` |
| `audit_buried_facts.py` | Decision-time facts buried in longer pages | `python P:/.data/wiki/scripts/audit_buried_facts.py` |
| `validate_wiki_entry.py` | Wiki entries that fail the quality gate | `python ~/.grok/skills/wiki/scripts/validate_wiki_entry.py <path>` |

## Duplicate detection

The skill catalog (`skill-catalog.md`) already shows duplicates by name.
Common patterns:
- Plugin cache + marketplace source + `.agents/skills/` (e.g., `nlm-to-wiki` appears 3x)
- Versioned plugin caches (`plugin/1.0.7/` vs `plugin/1.0.8/`)

**Rule:** prefer `.agents/skills/` > marketplace source > plugin cache. The
cross-agent scope is the canonical location; caches are derived.

## Staleness detection

A wiki concept is stale if:
- Not referenced by any qmd search result in the last 90 days (requires search-log analysis)
- Frontmatter `created:` is >12 months old AND `updated:` is absent or >6 months old
- Content references file paths that no longer exist

**Action:** mark `status: archived` in frontmatter. Do NOT delete — archived
concepts may still have value for historical context.

## Operational notes

- **Grok Build, not Claude Code.** No CKS (Constitutional Knowledge System).
  The inventory layer is `index_skills.py` + qmd, not CKS search.
- **No `/rewind` or checkpoints.** Recovery is via git + transcripts
  (see `/recover` skill). Pruning is additive (archive, not delete).
- **Multi-agent filesystem.** Other sessions may be reading the catalog
  during pruning. Atomic writes only; no full-file overwrites on shared
  files (per AGENTS.md file editing protocol).

## References

- `P:/.data/wiki/scripts/index_skills.py` — the catalog indexer
- `P:/.data/wiki/scripts/audit_buried_facts.py` — buried-fact detector
- `wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md` —
  why AGENTS.md reminders (not skill-body detail) trigger maintenance
- Adapted from Claude-side `garden` skill (cc-skills-architect)
