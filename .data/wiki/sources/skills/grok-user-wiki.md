---
type: skill-reference
scope: grok-user
skill_name: wiki
source_path: C:/Users/brsth/.grok/skills/wiki/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: wiki

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/wiki/SKILL.md`

Persistent knowledge base for durable findings AND design decisions. Default (/wiki with no args): distill the current session's unique, non-obvious findings AND architectural decisions (choices with rationale, alternatives, selection criterion, and falsifier) into wiki pages at P:/.data/wiki/concepts/. Also supports query (/wiki query <question>), lint (/wiki lint), and update (/wiki update). Use when: the user says /wiki, "save this to the wiki", "what does the wiki say about", "remember th...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
