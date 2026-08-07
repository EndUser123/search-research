---
thread_id: wiki-search-mcp-infra-20260806
parent_handoff_path: none
current_session_id: 019fd8dc-dc0c-7e23-8a5d-d293c819833e
current_terminal_id: grok-main
produced_at: 2026-08-06T23:30:00Z
last_updated_at: 2026-08-06T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Wiki Search MCP Server + Fleet Infrastructure

## Objective

Build and deploy wiki_search MCP server as pull-based knowledge retrieval,
fix Stop hook false-positive loop, evaluate /adhd skill, reduce fleet
script defects from 149→8, and propagate wiki_search into /www and /tp.

## What now works

- **wiki_search MCP server** live and verified: 990 concepts, FTS5, <10ms queries, model calls it proactively
- **SessionStart auto-refresh**: index rebuilds if stale >24h or concept count changed
- **Stop hook nonce-gap fixed**: `_check_obligation_satisfied` returns specific rejection reason (NONCE_MISMATCH, SCOPE_NOT_COVERED, etc.) instead of generic NO_COVERING_RECEIPT
- **`/www` Phase 1**: 4 wiki query steps swapped from inline grep to wiki_search
- **`/tp` Step 0.5**: swapped from inline grep to wiki_search
- **`/adhd` skill**: evaluated, Rules 4+10 overridden, testing results in wiki concept
- **Fleet script defects**: 149→8 (94.6% reduction)
- **Go F-05**: phase placeholders shortened
- **updatedInput falsifier**: re-verified (Grok Build still doesn't support it)
- **Model delegation research**: wiki concept documenting cheap-model allocation

## Status

OPEN — infrastructure shipped, 5 skills at 0 defects, remaining work is adoption + edge cases.

## Key decisions

### Decision 1: Pull-based (MCP) over push-based (hook injection)

**Choice:** wiki_search MCP tool (pull) over UserPromptSubmit hook (push).

**Why:** Grok Build ignores stdout on passive events (UserPromptSubmit, SessionStart). Verified 3 times + confirmed by 4 community projects (sqlew, cartograph, ai-memory, grok-turn-index). The `.claude/settings.local.json` compat path was also tested and confirmed passive.

**Steelman (rejected):** PreToolUse gate on web_search. Rejected because the fleet uses DDG/firecrawl/subagents for research, not web_search. Gating the wrong tool.

**Falsifier:** if model never calls wiki_search proactively after 5 sessions, tool description isn't sufficient.

### Decision 2: Fix scanner false positives instead of fixing scripts

**Choice:** improve script_scan.py to suppress false positives (dynamic dict access, output template strings, scanner self-references) rather than fixing individual scripts.

**Why:** 42 of 62 close-skill findings were scanner false positives. Fixing the scanner eliminated them across all 10 skills simultaneously.

## Task packets

### AC-01: Remaining 8 script defects (low priority)

- **ship-py (1):** CROSS-SKILL-DEP on ship-rhai — documented
- **tp (1):** scanner self-reference — by-design
- **packet (1):** NO-WIKI-PERSISTENCE — design discussion needed
- **todo (4):** 1 craft + 1 SILENT-NO-OP + 2 deps — individual fixes
- **close (1):** CROSS-SKILL-DEP on aar — documented

### AC-02: wiki_search adoption monitoring

- Monitor whether model calls wiki_search proactively over next 5 sessions
- If not: consider PreToolUse gate or stronger tool description
- Update [[wiki-search-mcp-server-pull-based-knowledge-retrieval]] with adoption data

### AC-03: Remaining skill integrations

- `/check` — no wiki query to swap (verification skill, not knowledge retrieval)
- `/close` coverage scan — could use wiki_search for pattern matching
- `/handoff` — could use wiki_search for related-concept discovery

## Commits this session

### ~/.grok repo

- `7968234` — fix(go): shorten phase placeholders F-05
- `499f04d` — fix(skill-dev): suppress 42 false positives in script_scan.py
- `e183f27` — feat: wiki context injector hook (UserPromptSubmit) — *deprecated, doesn't work*
- `5725ec0` — fix: update hook output format + tests + lint cleanup
- `ed6eb2f` — feat: wiki search MCP server
- `db81a91` — feat(www): swap 4 wiki query steps to wiki_search
- `793b65b` — feat(adhd): add workspace overrides for Rules 4+10
- `b843551` — fix(quality_gate): return specific rejection reason in obligation check
- `b016746` — feat(tp): swap Step 0.5 wiki query to wiki_search
- `05cf355` — feat: SessionStart hook for wiki index auto-refresh
- `aec43ac` — fix(close): partial defect fixes — 20→14 findings
- `03fa550` — fix(close): document cross-skill AAR dependency
- `2725ec0` — fix: update hook output format + tests
- `a217183` — fix: resolve remaining 13 script defects fleet-wide

### P:/ repo

- `deaf30b` — wiki: model delegation research
- `7079061` — plan: wiki context injector hook
- `fba2169` — wiki: re-verify updatedInput falsifier (2026-08-06)
- `c17d6ab` — plan: wiki search MCP server
- `cd0d6f4` — plan: tick all checkboxes
- `7e08ced` — plan: update with /tp review fixes
- `a1443af` — plan: tick tasks 1-3
- `2cb4e51` — plan: task 4 complete
- `8693e9b` — wiki: add /adhd live testing results
- `35d32ed` — wiki: Stop hook false-positive loop root cause
- `5e16ef6` — docs: update defect cleanup handoff — 149→14
- `6ff0329` — wiki: wiki_search MCP server design decision

## Suggested skills

- `/check` after next session to verify wiki_search adoption
- `/tp` to challenge whether remaining 8 defects are worth fixing vs documenting
