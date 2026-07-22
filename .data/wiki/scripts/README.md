# Wiki scripts

Maintenance scripts for the wiki vault at `P:/.data/wiki/`. Run these from the workspace root.

## Indexing & catalog

### `index_skills.py` — regenerate skill catalog and stubs

```bash
python P:/.data/wiki/scripts/index_skills.py
```

Scans all 6 skill directories (user-grok, project-grok, agents, bundled, installed-plugins, marketplace), writes lightweight stubs to `wiki/sources/skills/` for qmd semantic search, and regenerates `wiki/concepts/skill-catalog.md`.

**When to run:**
- After adding or removing any skill
- After renaming a skill directory
- When the catalog's `updated:` date is stale relative to known skill changes
- Before relying on `qmd search` for skill discovery if you suspect new skills aren't appearing

**What it does:**
1. Clears all existing stubs in `wiki/sources/skills/*.md`
2. Re-scans all 6 directories for `SKILL.md` files
3. Writes a stub per skill (frontmatter: name, description, path, scope, plugin)
4. Rewrites `wiki/concepts/skill-catalog.md` with the full index

**Stubs are pointers, not copies.** They contain only frontmatter and a one-line description. The source of truth stays in the actual SKILL.md file. This prevents drift.

**Runtime:** ~5 seconds for 248 skills. (Now scans 24 directories across Grok/Claude/Codex — ~968 skills in ~5s.)

### `scan_techniques.py` — technique indicator scan

```bash
python P:/.data/wiki/scripts/scan_techniques.py
```

Scans all SKILL.md files for technique indicator patterns (phase gates, falsifiers, evidence tiers, self-consistency, etc.). Produces `P:/tmp/technique-scan.json` and `P:/tmp/technique-scan.md` with per-skill technique density rankings.

**When to run:**
- Before deep-reading skills (identifies high-density subset to prioritize)
- After adding new techniques to the indicator list
- As the code breadth pass (Tier 0) in the 4-tier model analysis pattern

**Runtime:** ~17 seconds for 968 skills.

### `diffusiongemma_read.py` — DiffusionGemma direct-API file reader

```bash
python P:/.data/wiki/scripts/diffusiongemma_read.py <file>                    # single pass
python P:/.data/wiki/scripts/diffusiongemma_read.py <file> --enhanced         # multi-perspective fan-out
python P:/.data/wiki/scripts/diffusiongemma_read.py <dir> --batch             # batch 20-50 files
python P:/.data/wiki/scripts/diffusiongemma_read.py <dir> --batch --json      # JSON output
```

Reads files via DiffusionGemma (Google model, Nvidia inference) direct API. Bypasses `spawn_subagent` (which fails with empty-content errors). Three modes: single (~1-2s), enhanced 3-perspective parallel fan-out (~2.4s, 20/20 quality), batch (~6.5s for 20 files using 256K context).

**When to use:** mechanical file reads where throughput matters more than peak quality. See `P:/.data/wiki/concepts/diffusiongemma-4-tier-integration.md` for the full 4-tier model routing strategy.

### `append_log.py` — atomically append to wiki log

```bash
python P:/.data/wiki/scripts/append_log.py "Entry title" "source" "agent" "notes" "page-path"
```

Appends a log entry to the top of `P:/.data/wiki/log.md` atomically via Python. **Use this instead of `search_replace` for log edits.** The `search_replace` pattern causes sequential edit collisions when multiple log edits target the same anchor (`# Vault Log\n\n`) — later edits silently revert earlier ones.

**When to use:** every time you add a wiki concept. Run after `wiki_after_write.py`.

**Why this exists:** session 2026-07-21 lost all 13 log entries because each `search_replace` call used the previous entry as its anchor, and later edits' `old_string` matched earlier file states, silently reverting insertions. The fix: use a Python script that reads-modifies-writes atomically, never relying on the previous edit's output.

---

## Other wiki scripts (canonical locations)

These scripts live in the `cc-skills-sdlc` plugin, not here. They're documented at `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SKILL.md`.

| Script | Path | Purpose |
|---|---|---|
| `wiki_after_write.py` | `cc-skills-sdlc/skills/wiki/scripts/` | Auto-link a new wiki concept to its neighbors (run after every wiki write) |
| `wiki_state.py` | `cc-skills-sdlc/skills/wiki/scripts/` | Lifecycle state machine (init, mark, status, check). Mandatory for wiki completeness |
| `wiki_manifest.py` | `cc-skills-sdlc/skills/wiki/scripts/` | Bulk-ingest manifest generator for multi-file sources |
| `wiki_health_check.py` | `cc-skills-utils/skills/main/scripts/` | Vault health check (`--json`, `--fix`, `--stale` modes) |
| `wiki_signal_*.py` (4 scripts) | `cc-skills-sdlc/skills/wiki/scripts/` | Signal-extraction pipeline for noisy bulk sources |

---

## Adding a new script to this directory

If you add a script to `P:/.data/wiki/scripts/`, document it here with:
- One-line purpose
- Invocation command
- When to run
- What it writes (and to where)
- Runtime estimate

Keep this README as the single index for wiki maintenance scripts.
