---
thread_id: c5622127-df8a-4fd7-b888-ffadbf2189ad
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console
produced_at: 2026-07-22T15:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
assigned_to: unassigned
---

# Handoff: Deploy file editing protocol v2

## 1. Objective

Deploy the reviewed file editing protocol (v2) to AGENTS.md, CLAUDE.md, and P:/AGENTS.md.

## 2. Status

**Reviewed, not deployed.**

The v2 draft is at `P:/tmp/file-editing-protocol-for-review-019f819a-7619-7cb3-a6a4-480ff1c916ce.md`.

## 3. Key changes from v1

| Change | Why |
|--------|-----|
| Removed absolute Write ban | Contradicts windows-filesystem.md (Write works as of 2026-01-20) |
| Added cross-agent tool name mapping (Grok/Claude/Codex) | v1 used Grok-only names but claimed "all LLMs" |
| Reframed Python atomic write from "persistence fix" to "batch convenience" | Persistence not broken post-2026-01-20 |
| Replaced edit-count threshold with collision-risk model | File type, not edit count, determines risk |
| Labeled evidence claims as `[INFERENCE]` | v1 presented incidents as fact without receipts |
| Added post-edit-chain regression diff | From existing CLAUDE.md rule |

## 4. Deployment steps

1. Review the v2 draft at the path above
2. Extract the rules that go to AGENTS.md (behavioral rules)
3. Deploy to `~/.grok/AGENTS.md`, `~/.claude/Claude.md`, `~/.codex/AGENTS.md`
4. Add cross-link from `P:/AGENTS.md` pointing to the global version
5. Do NOT put in wiki (these are behavioral rules, not findings)

## 5. What NOT to deploy

The v2 includes "review questions" and "proposed implementation locations" sections — those are review artifacts, not rules. Extract only the actual rules (sections 1-5 of the protocol).
