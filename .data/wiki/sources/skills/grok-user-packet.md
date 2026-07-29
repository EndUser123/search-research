---
type: skill-reference
scope: grok-user
skill_name: packet
source_path: C:/Users/brsth/.grok/skills/packet/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: packet

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/packet/SKILL.md`

Export a filtered, tool-simplified view of a Grok session conversation into a markdown file another LLM can read cold for review. Filters to topic-relevant turns, collapses tool I/O to filename+path, redacts secrets by default, and produces two files: _sig.md (turn index) and _full.md (full conversation). Use when the user says /packet, wants to export a conversation for review, wants to hand a topic discussion to another LLM, or wants to extract a filtered transcript.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
