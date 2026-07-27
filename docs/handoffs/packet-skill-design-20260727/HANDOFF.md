---
thread_id: packet-skill-design-20260727
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T12:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 916400f20303869c2ab4ede6b50c95fddb1114c2
---

# `/packet` skill — design complete, build not started

## Objective

Build `/packet`, a skill that exports a filtered, tool-simplified view of a Grok session's conversation into a markdown file another LLM can read cold for review. The design is fully documented in the wiki concept; the build is ~2-3 hours of code work awaiting operator "go."

## Status

OPEN — design complete, build not started. All architectural decisions resolved (see Decision section). Awaiting operator authorization to implement.

## Problem

The operator wants to hand the full conversation on a single topic (e.g., a wiki/skill design discussion) to a different LLM for review — without dumping the entire session (which contains unrelated turns, giant tool outputs, and system noise). The skill must: (1) filter a Grok session down to turns relevant to a topic, (2) simplify verbose tool I/O to just filename/path, (3) write a clean markdown file another model can read cold.

## Decision (all resolved this session)

All five design decisions are documented in `P:/.data/wiki/concepts/conversation-distillation-review-packet-export.md`:

1. **Filter strategy:** orchestrator-side semantic expansion (NOT regex). The orchestrating LLM expands the topic phrase to a term set (~20-30 terms) using session context. Bias toward recall. Operator rejected regex as "impossible to enumerate all patterns."
2. **Two-file output:** `<name>_sig.md` (turn index, one-line summaries) + `<name>_full.md` (full verbatim filtered conversation). Operator confirmed two-file split is required.
3. **Redaction:** default-on regex redaction of secrets (sk-, ghp_, xoxb-, Bearer, API_KEY=, etc.). Opt-out via `--no-redact`. Operator confirmed external web-hosted LLMs will receive packets, so redaction is blocking.
4. **Domain placement:** Domain 8 (Knowledge/Memory), sibling to `/handoff`.
5. **Architecture:** standalone skill importing the AAR transcript parser (`~/.grok/skills/aar/__lib/transcript_parser.py`). Follows `/gitpack`'s code-vs-LLM-split pattern (deterministic code owns extraction; `--overview` placeholder for LLM-generated orientation).

## Read first

- **`P:/.data/wiki/concepts/conversation-distillation-review-packet-export.md`** — the complete design doc with code patterns, decisions, and falsifier
- `P:/.data/wiki/concepts/skill-domain-map.md` — Domain 8 placement context
- `~/.grok/skills/aar/__lib/transcript_parser.py` — the reusable parser (parse_transcript → Transcript)
- `~/.grok/skills/aar/__lib/event_model.py` — Event/ToolCall/Role/Transcript types
- `P:/packages/.claude-marketplace/plugins/search-research/skills/gitpack/SKILL.md` — the design-pattern source (code-vs-LLM split, two-file output, --overview placeholder)

## Skill skeleton (from the wiki concept)

```
~/.grok/skills/packet/
  SKILL.md            # /packet [session] [--topic <phrase>] [--llm-filter] [--no-filter] [--no-redact]
  __lib/
    filter.py         # is_relevant(ev, terms), select_with_context(events, terms) — semantic term-set filter
    render.py         # summarize_tool_call(tc), render_packet() — PATH_KEYS lookup + two-file renderer
    redact.py         # redact_secrets(text) — regex patterns, [REDACTED:type] masking
    cli.py            # parse_transcript() reuse → expand terms → filter → redact → render → write
  scripts/
    export.py         # entrypoint
```

## Acceptance criteria

1. `/packet auth` on a session containing auth discussions produces two files (`_sig.md` + `_full.md`) at `P:/.claude/.artifacts/` with only auth-relevant turns
2. Tool calls are collapsed to `ToolName(short/path)` via the PATH_KEYS lookup table
3. Secrets matching common patterns (sk-, ghp_, etc.) are masked as `[REDACTED:type]` by default
4. `_sig.md` contains a turn index with one-line summaries; `_full.md` contains the verbatim filtered conversation
5. The packet header shows: source session, topic phrase, expanded term set, kept/excluded counts, redaction count
6. `--no-filter` exports the whole session (escape hatch)
7. `--no-redact` disables redaction for trusted-local cases

## Next steps

1. **Implement `/packet`** per the wiki concept (~2-3 hours). Start with `filter.py` and `render.py` (code patterns are in the concept); wire up `cli.py` with the AAR parser import; add `redact.py`; write SKILL.md.
2. **PATH_KEYS refinement** (build-time): add `url_keys` column for `web_fetch`/`web_search`/MCP dispatch tools (refinement #5 from the /tp critique — the 9/25 current coverage is sufficient for v1).
3. **Test on this session's transcript** — `/packet packet` should produce a packet documenting the /packet design discussion itself (dogfooding).

## Dependencies

- **Requires:** nothing — all design decisions resolved, all code patterns drafted
- **Blocks:** nothing
- **Non-blocking to:** none

## Evidence

- Wiki concept written + validator-passed: `P:/.data/wiki/concepts/conversation-distillation-review-packet-export.md`
- `/tp` critique run (subagent `019fa498-a9fe-7cb2-96d8-f367b4ff7be9`, 11 tool calls, REVISE verdict → all revisions addressed)
- AAR parser reuse verified: read this session, 312 lines, handles all 5 role types
- PATH_KEYS coverage verified: 9/25 Grok tools covered (the 16 "missing" mostly carry no path args)

## Last user message (verbatim)

> /handoff

## Falsifier

This handoff is wrong if:
- The wiki concept's design decisions are overturned before build (re-open the design)
- The AAR parser's API changes (breaks the reuse contract)
- A Grok session format change makes the filter/render logic obsolete

## Other outstanding streams

- **Cross-transport model matrix testing** (`cross-transport-model-matrix-20260726`) — would extend the Nemotron serde finding to all models × all transports. Independent of `/packet`.

---

## Revision 1 — 2026-07-27T22:10:00Z (session 019fa48a)

**Trigger:** /packet skill was BUILT after the original handoff was written. The handoff says "build not started" — that's now stale. /review found 4 bugs that need fixing.

**What changed since the original:**
- /packet skill built at `~/.grok/skills/packet/` (filter.py, render.py, redact.py, export.py, SKILL.md)
- Smoke-tested successfully on this session (695/703 turns kept, both _sig.md and _full.md produced)
- /review run produced 20 findings: 4 bugs, 8 risks, 4 suggestions, 2 nits
- FINDINGS.md at `P:/.artifacts/grok-build-terminal/grok-review/packet/20260727-154541/FINDINGS.md`

**Updated status:** OPEN — skill built and smoke-tested, but 4 bugs need fixing before production use.

**New open items:**
- CORR-001 (bug, conf 0.92): render_full_turn dumps full tool_result text — fix: gate on role
- CORR-002 (bug, conf 0.88): dead redaction loop double-counts — fix: use count_redactions() instead
- CORR-003 (bug, conf 0.90): resolve_transcript_path crashes if sessions dir missing — fix: guard iterdir
- CORR-004 (bug, conf 0.86): TranscriptParseError not caught — fix: wrap in try/except
- 8 risks (CORR-005/006/007/008, MAINT-001/002/003/004/005/006) — documented in FINDINGS.md

**Updated evidence:**
- Skill registered: system-reminder shows `/packet` in the skill catalog
- Smoke test: `packet-019fa48a_sig.md` and `packet-019fa48a_full.md` at `P:/.claude/.artifacts/`
- /review run_dir: `P:/.artifacts/grok-build-terminal/grok-review/packet/20260727-154541/`
