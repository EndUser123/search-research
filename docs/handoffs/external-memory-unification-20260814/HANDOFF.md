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

### 2. Port Grok session transcript parsing to episodic-memory → grok-chat-mem

**Research completed (2026-08-13):** see
`[[grok-chat-mem-candidate-repos-for-session-transcript-search]]` for the full
15+ repo survey. Key finding: **marcelocantos/mnemo** is the only tool that
already indexes Grok sessions out of the box, but it has 0 stars and 0 Windows
downloads (unvalidated on our platform). Three paths identified:

- **Path A (mnemo):** install the Windows installer, test if Grok indexing
  works. Zero code. Highest external risk (0-star single-author project).
- **Path B (extend episodic-memory):** write `parseGrokConversation()` using
  the existing AAR parser (`~/.grok/skills/aar/__lib/transcript_parser.py`)
  as reference. Lowest risk. We control the code. ~2-4 hours.
- **Path C (memory_mcp):** cleanest parser-extension architecture, but trades
  episodic-memory's test suite for a 12-commit codebase.

This is the real work. Episodic-memory currently parses:
- Claude Code JSONL format (`~/.claude/projects/`)
- Codex rollout JSONL (`~/.codex/sessions/`)

It needs to also parse:
- **Grok Build session format** at `~/.grok/sessions/<encoded-cwd>/<session-id>/`
  - `updates.jsonl` — tool calls and results
  - `chat_history.jsonl` — user/assistant messages
  - `summary.json` — session metadata

**Steps:**
1. Read the episodic-memory source at `C:\Users\brsth\.grok\installed-plugins\episodic-memory-479fd403\src\parser.ts` to understand the parser interface
2. Read the Grok session format (use `~/.grok/docs/user-guide/` and inspect actual session files)
3. Write a Grok transcript parser that extracts user-agent exchanges from `chat_history.jsonl`
4. Add `~/.grok/sessions/` to the sync source list in `src/sync.ts` / `src/index-cli.ts`
5. Build + test
6. Rename the plugin directory + plugin.json to `grok-chat-mem`

**Key files to read first:**
- `C:\Users\brsth\.grok\installed-plugins\episodic-memory-479fd403\src\parser.ts` — parser interface
- `C:\Users\brsth\.grok\installed-plugins\episodic-memory-479fd403\src\sync.ts` — sync source configuration
- `C:\Users\brsth\.grok\installed-plugins\episodic-memory-479fd403\CLAUDE.md` — build instructions
- `~/.grok/sessions/P%3A%5C/019ffbf4-6734-77a3-bec3-ef4ae502814e/chat_history.jsonl` — Grok session format sample

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
