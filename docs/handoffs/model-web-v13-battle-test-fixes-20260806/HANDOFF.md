---
thread_id: 019fd6f2-model-web-v13
parent_handoff_path: none
current_session_id: 019fd6f2-9d53-79a2-9382-b879dd4a74bf
parent_session: none
current_terminal_id: console-1
produced_at: 2026-08-06T12:45:00-06:00
last_updated_by: 019fd6f2-9d53-79a2-9382-b879dd4a74bf
last_updated_at: 2026-08-06T12:45:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 1339b4151a35b9de1d9b8e2fa7996b6d698ad149
---

# model-web v1.3 battle-test fixes — 15 LOW findings remaining

## Objective

Apply the remaining 15 LOW-severity findings from the `/tp` critique of model-web SKILL.md, completing the skill's first battle-test-driven update cycle.

## Status

OPEN

## Producing context

2026-08-06, session 019fd6f2, Grok Build. A live ensemble run against ChatGPT, DeepSeek, Qwen, and Kimi revealed 10 operational failures. A `/tp` fresh-subagent critique identified 32 findings total (8 CRITICAL, 9 MEDIUM, 15 LOW). The 8 CRITICAL + 4 MEDIUM were applied in v1.3 (commits `4718cc7`, `09737b7` on `~/.grok`). The 15 LOW findings remain.

## Read-first list

1. `C:\Users\brsth\.grok\skills\model-web\SKILL.md` — current state (v1.3, 1331 lines). Read the sections cited below.
2. `C:\Users\brsth\.grok\sessions\P%3A%5C\019fd6f2-9d53-79a2-9382-b879dd4a74bf\` — subagent output from the `/tp` critique (contains the full 32-finding list with specific line references)

## Verified facts

- [FACT] 12 edits were applied to SKILL.md in session 019fd6f2: decision tree, React race warning, SSE stale-parse recovery, IIFE syntax warning, claim semantics, session-ID fallback, ensemble tab mode, pre-send navigation, verify-after-submit retry, duplicate step fix, "legacy" rename, ChatGPT submit standardization (commits `4718cc7`, `09737b7`)
- [FACT] 15 LOW findings were identified but not applied — they are documented in the subagent output at the session path above
- [FACT] The wiki concept `[[browser-automation-failure-modes-llm-chat]]` was updated with all 8 failure modes (commit `5034033` on `P:/`)

## Current state

**Done:**
- v1.3 decision tree replaces flat priority list
- React `type_text(submitKey)` race condition documented
- SSE stale-parse recovery path added
- IIFE syntax warning added
- Claim semantics + session-ID fallback documented
- Ensemble tab-mode visibility note added
- Overlay dismissal step (3a.5) for Z.ai/MiniMax added
- Verify-after-submit retry advice corrected
- Wiki concept updated with 4 new failure modes

**Not done (15 LOW findings from the /tp critique):**

| ID | Finding | Section |
|---|---|---|
| F11 | Pre-submit verification checks DOM not framework state (Send button enabled check) | Step 3b |
| F13 | ChatGPT "MUST navigate first" duplicated in 4 places — consolidate to precondition block | Table + 3 locations |
| F14 | Verification dates inconsistent; no methodology documented (add `[F][E][R]` codes) | Verified table |
| F18 | No guidance when both SSE and DOM extraction fail | Step 5 |
| F19 | SSE shim file path not inline at point of use | Step 0.5 |
| F20 | Qwen/Grok per-site sections duplicate the verified table | Lines ~1230-1240 |
| F23 | "auto-browser registry.js" pattern referenced but not defined | Post-table note |
| F24 | `uid prefix` mechanism (`pageId_index` format) not explained | Step 1 |
| F25 | Pre-send uid prefix stability assumed (add fallback to conversation-order extraction) | Step 5 |
| F26 | `wait_for` timeout uniform — no per-site guidance | Step 4 |
| F27 | FUSION_BLAST_READY parser doesn't handle rapid double-click | Fusion portal Step 2 |
| F28 | Run-state schema lacks `extraction_method` and `sse_format_version` | Schema section |
| F29 | Per-site submit methods duplicated in 3 places (table, Step 3c, ensemble blast) | Multiple |
| F30 | Model-switch procedure documented but no `/model-web select-model` invocation | Model selectors section |
| F31 | Conversation selection doesn't say "next ask appends a turn to existing conversation" | Conversation selection protocol |

## Task packets

### MW-LOW-01: Consolidate ChatGPT navigation precondition
- **goal:** Move the "ChatGPT home page has no functional composer" warning to a single precondition block, replace 4 duplicate mentions with back-references
- **in scope:** Verified table row, post-table note, Step 3a, ensemble blast Step 2d
- **out of scope:** Non-ChatGPT sites
- **files:** `~/.grok/skills/model-web/SKILL.md`
- **acceptance:** ChatGPT navigation warning appears exactly once as a precondition block; other locations say "see ChatGPT precondition above"
- **falsifier:** any of the 4 original locations still contains the full warning text
- **verification level:** STATIC_INSPECTION

### MW-LOW-02: Add extraction-method tracking to run-state schema
- **goal:** Add `extraction_method`, `sse_chunk_count`, `sse_format_version` to the run-state JSON schema so stale SSE formats are diagnosable from run-state alone
- **in scope:** Schema section, run_state.py (if it validates the schema)
- **out of scope:** Changing the state machine
- **files:** `~/.grok/skills/model-web/SKILL.md` schema section; `~/.grok/skills/model-web/__lib/run_state.py`
- **acceptance:** Schema documents the 3 new fields; run_state.py accepts them without error
- **falsifier:** fields absent from schema or run_state.py rejects them
- **verification level:** STATIC_INSPECTION

### MW-LOW-03: Apply remaining 13 LOW findings
- **goal:** Apply the remaining 13 LOW findings (F11, F14, F18, F19, F20, F23, F24, F25, F26, F27, F29, F30, F31) as batch edits
- **in scope:** All sections cited in the findings table above
- **out of scope:** MW-LOW-01 and MW-LOW-02 (separate packets)
- **files:** `~/.grok/skills/model-web/SKILL.md`
- **acceptance:** Each finding's recommended change is present; no finding is missed
- **falsifier:** any finding's change is absent
- **verification level:** STATIC_INSPECTION

## Open decisions

None — the findings are documented and actionable. No user input needed.

## Hard constraints

- Do NOT rewrite sections — apply surgical patches to the specific lines cited in each finding
- Bump version to 1.4 after applying
- Commit each logical group separately (consolidation, schema, batch)

## Cross-reference couplings

- `~/.grok/skills/model-web/SKILL.md` → wiki concept `[[browser-automation-failure-modes-llm-chat]]` (they must stay in sync — failure modes documented in both)
- Run-state schema changes → `run_state.py` must accept the new fields

## Other outstanding streams

- **Morning Brief HTML improvements** — design suggestions from 3 web LLMs collected and synthesized, not yet implemented. Separate handoff: `morning-brief-html-improvements-20260806`.

## Explicit non-goals

- Do NOT add new sites to the verified table (requires live testing)
- Do NOT restructure the SKILL.md's section ordering (larger refactor, different session)
- Do NOT implement the "single source of truth" structural recommendation (R1 from the critique — making the table the sole authority for submit methods). That's an architectural change, not a LOW finding.

## Resumption protocol

1. Read the subagent output from session 019fd6f2 for the full 32-finding list with specific line references
2. Read the current SKILL.md to see what v1.3 already applied
3. Apply MW-LOW-01 (ChatGPT consolidation) first — it's the highest-impact LOW finding
4. Apply MW-LOW-02 (run-state schema) — requires reading run_state.py
5. Apply MW-LOW-03 (remaining 13 findings) as batch edits
6. Bump version to 1.4, commit, update skill catalog

## Suggested next invocation

```
Read the /tp subagent output from session 019fd6f2, then apply the 15 LOW findings to model-web SKILL.md. The findings are documented in the handoff at P:/docs/handoffs/model-web-v13-battle-test-fixes-20260806/HANDOFF.md.
```

## Last user message (verbatim)

> "/tp please update model-web to addressed any global or model specific errors, inefficiencies, improment ideas, etc."

## Epistemic labels

- [FACT] 12 edits applied in v1.3 (commits `4718cc7`, `09737b7`)
- [FACT] 15 LOW findings documented in subagent output
- [INFERENCE] The LOW findings are safe to batch-apply without testing — they are documentation improvements, not behavioral changes

## Suggested skills for next session

- `/skill-dev measure model-web` — after applying the fixes, measure the skill's quality score
- `/check` — verify the edits landed correctly

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-06T12:45 | 019fd6f2 | created |
