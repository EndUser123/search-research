---
type: skill-reference
scope: grok-user
skill_name: model-discover
source_path: C:/Users/brsth/.grok/skills/model-discover/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: model-discover

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/model-discover/SKILL.md`

Alias for `model-benchmark --discover`. Discovers available models from inference providers (NVIDIA, Google, Groq, OpenRouter, Cerebras, Mistral, HuggingFace, GLM, MiniMax, OpenCode/Zen) by querying each provider's catalog endpoint, then verifies reachability with a minimal probe prompt. Catches the known /v1/models lie pattern (models listed but non-functional at chat time). Use when the user says /model-discover, "what models are available", "discover models", "what can I use from provider ...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
