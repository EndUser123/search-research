---
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: 019fb933-040b-7720-a257-e364f5df726f
last_updated_at: 2026-08-01T13:10:46.831448
parent_session: none
produced_at: 2026-08-01T13:10:46.831448
status: open
handoff_type: investigation
---
# HANDOFF: Ensemble Refactoring Test + /model-web Skill Development

## Status: IN PROGRESS

## Objective
Test the `/model-web` browser-LLM ensemble by sending a real refactoring problem to multiple web LLMs, ranking their responses by quality, and deciding whether to implement the refactoring on `fetch_transcript_chain`.

## What was done this session

### Skill built: `/model-web` (committed)
- SKILL.md at `~/.grok/skills/model-web/SKILL.md`
- `__lib/run_state.py` with 15 passing tests
- `launcher.html` — dark-themed launcher page with two columns (No Login / Login Required)
- 18 web LLM sites catalogued (4 verified, 14 unverified)
- Blast/collect ensemble protocol documented
- Per-site input methods (fill vs click+type_text) documented
- Verify-after-submit step (Step 3.5) added
- Known failure modes section with practitioner solutions
- Chrome `--autoConnect` + `RemoteDebuggingAllowed` enterprise policy configured

### Wiki concepts written (4)
1. `chrome-autoconnect-for-authenticated-cdp-sessions` — Chrome 136+ blocks default-profile debugging
2. `tool-fallbacks-as-index-not-authority` — Groq exclusion gap, restructured fallback table
3. `browser-automation-failure-modes-llm-chat` — 4 failure types, verify-after-submit principle
4. `parallel-cdp-mcp-servers-openchrome` — OpenChrome as parallel ensemble upgrade path

### Ensemble test: partially collected
Sent refactoring prompt to 6 LLMs. ChatGPT response collected and excellent. 3 more responses in browser tabs (Gemini, Perplexity, HuggingChat) — need collection. Duck.ai and Qwen tabs were closed. Grok blocked by login.

## Resume here

### Immediate next actions
1. **Collect remaining 3 responses** — select pages 23 (Gemini), 21 (Perplexity), 26 (HuggingChat), take_snapshot each, extract the refactoring plan text
2. **Rank all responses** by: correctness, conciseness, actionability, depth of reasoning
3. **Decide: implement the refactoring?** If the plans converge on similar extractions, yes
4. **If yes: create implementation handoff** with the merged plan

### The refactoring target
**File:** `P:/packages/yt-is/csf/transcript.py` (2322 lines)
**Function:** `fetch_transcript_chain` at line 1835 (~200 lines)

**5 problems to solve:**
1. 5 nested closures trap pure logic + side-effecting functions inside the orchestrator
2. Mutable global `_WHISPER_ENABLED` read/written inside loop body (race condition risk)
3. Duplicated success handling between NLM path and generic path (~20 lines)
4. Mixed concerns (validation, logging, caching, rate-limiting, translation, orchestration)
5. 3 inline special cases in the fallback loop (Whisper admission, NLM language override, expensive fallback gating)

**ChatGPT's plan (the strongest so far):**
- Extract `_classify_failure` → `classify_transcript_failure()` with `FailureReason` enum
- Extract `_none_result` → `build_failed_transcript_result()` with typed args
- Extract `_stage_started/_stage_completed` → `StageExecution` dataclass + context manager
- Extract `_archive_failed_result` → `finalize_failed_transcript_fetch()` service
- Introduce `TranscriptCandidate` intermediate type — stages return this, one `finalize_successful_transcript()` handles translation + caching
- Orchestrator becomes: iterate stages → execute → if success, finalize → if fail, classify → return

### Ensemble test status

| Model | Prompt sent? | Response collected? | Tab open? |
|---|---|---|---|
| ChatGPT | ✅ | ✅ Excellent | Page 20 |
| Gemini | ✅ | ❌ NEEDS COLLECTION | Page 23 |
| Perplexity | ✅ | ❌ NEEDS COLLECTION | Page 21 |
| HuggingChat | ✅ | ❌ NEEDS COLLECTION | Page 26 |
| Duck.ai | ✅ | ❌ | CLOSED |
| Qwen | ✅ | ❌ | CLOSED |
| Grok | ❌ Blocked | ❌ | Login wall |

### Files changed this session
- `~/.grok/skills/model-web/SKILL.md` (committed, multiple revisions)
- `~/.grok/skills/model-web/__lib/run_state.py` (committed)
- `~/.grok/skills/model-web/tests/test_run_state.py` (committed)
- `~/.grok/skills/model-web/launcher.html` (committed)
- `~/.grok/tool-fallbacks.md` (committed — restructured as wiki index)
- `~/.grok/hooks/UserPromptSubmit_quota_availability.py` (committed — _display list fix)
- `~/.grok/installed-plugins/chrome-devtools-mcp-2df60288/.claude-plugin/plugin.json` (runtime — --autoConnect + --experimentalIncludeAllPages)
- `P:/.data/wiki/concepts/` — 4 new wiki concepts (committed)
- `P:/docs/handoffs/ensemble-refactor-test/ensemble-results.md` (this file)

### Constraints
- Chrome must be running with Remote Debugging enabled (`chrome://inspect/#remote-debugging`)
- Chrome DevTools MCP must be connected via `--autoConnect`
- The `--experimentalIncludeAllPages` flag is also set (doesn't hurt, doesn't help side panels)
- The launcher.html at `~/.grok/skills/model-web/launcher.html` has the current site list
- `RemoteDebuggingAllowed` enterprise policy is set in registry (permanent)
- The operator confirmed EULA compliance for ChatGPT browser automation

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T13:10 | 019fb933-040... | backfilled session_id from transcript scan |
