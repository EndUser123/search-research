---
thread_id: handoff-claim-subcommand-20260721
parent_handoff_path: P:/docs/handoffs/handoff-v02-aar-integration-20260720/HANDOFF.md
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T00:00:00Z
status: open
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: `/handoff claim` subcommand

## 1. Objective (one sentence)

Build a `/handoff claim <path>` subcommand that automates handoff frontmatter population — generating thread_ids, resolving session/terminal IDs, setting timestamps, and running validators — saving ~15k characters per handoff write.

## 2. Status

**Not started.** Identified as highest-projected token savings during session 019f821c.

## 3. What it does

`/handoff claim <path>` automates the mechanical parts of handoff creation:

1. **Generate thread_id** — UUID4
2. **Resolve current_session_id** — from `summary.json` in the session directory
3. **Resolve current_terminal_id** — from env vars (`GROK_SESSION_ID`, `CLAUDE_TERMINAL_ID`, etc.)
4. **Set produced_at** — current ISO8601 timestamp
5. **Set accurate_as_of_head** — from `git rev-parse HEAD` at `P:/`
6. **Set source_transcript** — `chat_history.jsonl` path for the resolved session
7. **Run validators** — check all 15 mandatory fields are populated
8. **Write the YAML frontmatter** to the target path

The user provides: topic, parent_handoff_path (if any), handoff_type, and the body content. The command fills in everything else.

## 4. Why it matters

Current `/handoff new` process requires the agent to manually resolve 8 frontmatter fields per handoff. Each field lookup is a tool call or env var read. Across multiple handoffs in a session (this session wrote 4), that's ~32 manual field operations. The `claim` subcommand does them in one Python script call.

Projected savings: ~15k characters per handoff (field resolution reasoning + manual YAML assembly).

## 5. Resumption protocol

1. Read `P:/.grok/skills/handoff/SKILL.md` — the current skill spec with all subcommands
2. Read `P:/.grok/skills/handoff/references/core-fields.md` — the 15 mandatory fields + chain header schema
3. Read `P:/.grok/skills/handoff/__lib/list_handoffs.py` — existing CLI pattern to follow
4. Read `P:/.grok/skills/handoff/__lib/validators.py` — existing validator to reuse
5. Create `P:/.grok/skills/handoff/__lib/claim_handoff.py`
6. Update `P:/.grok/skills/handoff/SKILL.md` to document the new subcommand
7. Test with a real handoff

## 6. Related artifacts

- SKILL.md: `P:/.grok/skills/handoff/SKILL.md`
- Core fields: `P:/.grok/skills/handoff/references/core-fields.md`
- Existing CLIs: `list_handoffs.py`, `verify_handoff.py`, `migrate_handoff.py`
- ROADMAP: `P:/.grok/skills/handoff/ROADMAP.md` (v0.2 planning)
- Related handoff: `handoff-v02-aar-integration-20260720` (broader v0.2 scope)

## 7. Open questions

- Should `claim` also generate the body skeleton (15 mandatory field headers)?
- Should it support `--parent <path>` to auto-set `parent_handoff_path` and inherit `thread_id`?
- Should it auto-run `/handoff verify` after writing?
