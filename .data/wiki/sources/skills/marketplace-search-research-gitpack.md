---
type: skill-reference
scope: marketplace
plugin: search-research
skill_name: gitpack
source_path: P:/packages/.claude-marketplace/plugins/search-research/skills/gitpack/SKILL.md
indexed_date: 2026-07-21
---

# Skill: gitpack

**Scope:** marketplace (plugin: search-research)
**Path:** `P:/packages/.claude-marketplace/plugins/search-research/skills/gitpack/SKILL.md`

Pack a code or markdown directory (or a scattered set of files) into compact LLM-context files using only stdlib — AST for Python, regex signatures for JS/TS/HTML/CSS/SQL/YAML/JSON/PowerShell, and heading+frontmatter extraction for Markdown. Deterministic, no external deps. Emits <name>_sig.md (signatures + indexes) and <name>_full.md (+ full source appendix) to .claude/.artifacts/. Use when preparing a focused code or skill context for an LLM.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
