---
current_session_id: 019fba6f-bfc9-7900-a5e8-7cb4ea3a01da
last_updated_by: 019fba6f-bfc9-7900-a5e8-7cb4ea3a01da
last_updated_at: 2026-07-31T17:09:29.134955
parent_session: none
produced_at: 2026-07-31T17:09:29.134955
status: open
handoff_type: investigation
---
# qmd replacement: grep fallback pattern

## What changed

qmd is being removed. Skills that call `qmd search --collection wiki` need a filesystem grep fallback. The pattern:

```bash
# Before (qmd):
qmd search --collection wiki "<query>" --limit 10

# After (grep fallback):
rg -l -i "<query>" P:/.data/wiki/concepts/ 2>$null
# or more broadly:
rg -l -i -g "*.md" "<query>" P:/.data/wiki/ 2>$null
```

## Skills to update (8 files)

1. `~/.grok/skills/wiki/SKILL.md` — retirement check (§Quick reference)
2. `~/.grok/skills/www/SKILL.md` — Phase 1 wiki query
3. `~/.grok/skills/design/SKILL.md` — pre-flight wiki query
4. `~/.grok/skills/dream/SKILL.md` — Pass 4 concept coverage check
5. `~/.grok/skills/handoff/SKILL.md` — auto-update wiki concept check
6. `~/.grok/skills/notice/SKILL.md` — contradiction check
7. `~/.grok/skills/debrief/SKILL.md` — Phase 0 session-shape search
8. `~/.grok/skills/model-benchmark/SKILL.md` — model degradation check

## Scripts to update

- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_after_write.py` — auto-link pipeline uses qmd search to find wikilink candidates. Needs grep fallback.
- `P:/.data/wiki/scripts/scan_techniques.py` — may reference qmd

## Approach

For each skill, replace `qmd search --collection wiki "<query>" --limit N` with a two-step pattern:
1. Try qmd if available: `qmd search --collection wiki "<query>" --limit N 2>$null`
2. Fall back to grep: `rg -l -i "<keywords>" P:/.data/wiki/concepts/ --max-count 1`

The grep fallback is keyword-only (no semantic matching), but it's reliable and has no dependencies.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-31T17:09 | 019fba6f-bfc... | backfilled session_id from transcript scan |
