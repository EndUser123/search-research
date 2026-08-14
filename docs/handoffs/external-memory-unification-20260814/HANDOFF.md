---
title: "External memory unification & rationalization: rename + port work"
session: 019ffbf4-6734-77a3-bec3-ef4ae502814e
date: 2026-08-14
status: open
host: grok
tags: [memory, rename, port, episodic-memory, claude-mem-grok, grok-tool-mem, grok-chat-mem]
---

# Session handoff

## What this is

The operator directed a rename and rationalization of the two external memory
systems on this host to make their roles clear by name:

- **claude-mem-grok** → **grok-tool-mem** (captures tool actions, auto-injected)
- **episodic-memory** → **grok-chat-mem** (indexes session transcripts, searchable)

The rename is not just cosmetic — it exposes a functional gap: episodic-memory
does not currently index Grok Build sessions (`~/.grok/sessions/`). It only
reads from `~/.claude/projects/`, `~/.claude/transcripts/`, and
`~/.codex/sessions/`. Making the name "grok-chat-mem" accurate requires
adding Grok session transcript parsing to the indexing pipeline.

## What shipped (committed + pushed)

### This session's prior work (context for the rename)
1. **bun-runner.js stdin fix** — `readFileSync(0)` replaces broken async events
2. **Provider switch** — Gemini → Groq via OpenRouter base URL
3. **Hook timeout reduction** — PostToolUse 120→10s, Stop 120→30s
4. **Plugin re-enabled** in config.toml
5. **uncertainty_gate v3** — three-tier hedge detection (regex + structural + NLTK POS)
6. **scheduled_checks** — date check type + Groq deprecation reminder
7. **Wiki concept** — three-tier-hedge-detection-regex-structural-nltk
8. **Dream** — 2026-08-13 cross-session consolidation

## Open items (the actual work to do)

### 1. Rename claude-mem-grok → grok-tool-mem
- **Plugin directory:** `~/.grok/plugins/claude-mem-grok/` → `~/.grok/plugins/grok-tool-mem/`
- **plugin.json:** `"name": "claude-mem-grok"` → `"name": "grok-tool-mem"`
- **config.toml:** Update enabled list entry
- **hooks.json:** No change needed (uses `${GROK_PLUGIN_ROOT}`)
- **.mcp.json:** No change needed
- **settings.json:** No change needed (CLAUDE_MEM_* keys are read by worker, not tied to plugin name)
- **Commit message:** `refactor: rename claude-mem-grok → grok-tool-mem for clarity`
- **Risk:** Low. The plugin is identified by directory name + plugin.json name. No hardcoded references to "claude-mem-grok" in the worker code.

### 2. ✅ DONE — Grok session search via search-research CHS provider

**Resolution (2026-08-13):** the operator pointed out that the Claude-side
`search-research` plugin already had a full CHS (Chat History Search)
subsystem with a Provider Protocol designed for adding new sources. This was
dramatically better than any external repo surveyed in the /www research.

**What was done:**
1. **Restored source** — the `search-research` marketplace dir was empty
   (submodule `.git` deleted, pip editable install broken). Restored v0.1.123
   from Claude plugin cache (812 files), `git init`, committed.
2. **Wrote `grok_sessions.py` provider** — walks `~/.grok/sessions/`, parses
   `chat_history.jsonl` (5 message types: user, assistant, tool_result,
   system, reasoning). Registered alongside claude_code_raw, codex_desktop,
   claude_log. 328 lines.
3. **Wrote 23 tests** — all passing. Covers provider protocol, format parsing,
   content hash stability, session dir parsing.
4. **Wrote `reindex_grok.py` indexer** — permanent script in
   `core/chs/scripts/`. Indexes Grok sessions into CHS DB.
5. **Verified end-to-end** — 50 sessions → 6,748 messages → keyword search
   returns hits. Provider discovers 2,827 sessions total.
6. **Created `~/.grok/skills/chs/SKILL.md`** — Grok skill calling the same
   shared CLI.

**Architecture (neutral/shared, not Claude-only):**
```
P:/packages/.claude-marketplace/plugins/search-research/   ← shared source
  core/chs/providers/
    claude_code_raw.py    ← Claude Code history
    codex_desktop.py      ← Codex history
    claude_log.py         ← Claude transcripts
    grok_sessions.py      ← NEW: Grok Build sessions
  core/chs/scripts/
    reindex_grok.py       ← NEW: Grok indexer

~/.grok/skills/chs/SKILL.md    ← NEW: Grok skill entry point
P:/__csf/data/grok_chat_history.db  ← Grok session DB
```

**What episodic-memory is for now:** episodic-memory remains as-is for
Claude Code + Codex MCP search. The CHS system in search-research is a
superset — it has all three providers plus Grok, plus hybrid search,
multi-terminal isolation, and 13 skills. The rename to "grok-chat-mem" is
no longer needed because the functionality is provided by the shared
search-research package, not by a renamed episodic-memory.

**Remaining work:**
- Full index of all 2,827 Grok sessions (50 done as proof-of-concept)
- FTS5 index population for full-text search (currently using LIKE queries)
- Semantic embeddings (the schema supports it; daemon not yet wired for Grok DB)

### 3. Update wiki + handoff references
- Update `[[three-tier-hedge-detection-regex-structural-nltk]]` if it references claude-mem-grok
- Update any handoffs that reference the old names
- Update config.toml enabled list

## Decisions

- **Names chosen by operator:** grok-tool-mem and grok-chat-mem. These are more descriptive than the upstream names.
- **Renaming is not just cosmetic:** The episodic-memory rename exposes a functional gap (no Grok session indexing) that must be fixed for the name to be accurate.

## Constraints

- Episodic-memory is a TypeScript project with a build step (`npm run build`). Changes to `src/` require rebuilding `dist/`.
- The `remembering-conversations` skill and the `mcp-search` MCP server both depend on episodic-memory's DB and tools. Don't break the interface.
- Grok session transcripts use a different JSONL structure than Claude Code — the parser must handle both formats.

## Verification

After both renames + port:
1. `grok-tool-mem` plugin loads and captures observations (verify via DB query)
2. `grok-chat-mem` MCP server responds to search queries
3. `grok-chat-mem` sync includes Grok sessions (verify via `episodic-memory stats` showing Grok sessions indexed)
4. Both old names removed from config.toml
