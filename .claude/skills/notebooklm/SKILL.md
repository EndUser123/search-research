---
name: notebooklm
description: Thin wrapper. delegates CLI operations to nlm. Uses nlm --ai for comprehensive reference, and notebooklm-expert for methodology. Use /notebooklm trigger. Note /research, /search, /cks
version: 1.0.0
status: stable
category: productivity
triggers:
  - '/notebooklm'
aliases:
  - '/notebooklm'
---

# NotebookLM (Thin Wrapper)

This skill is a thin wrapper that delegates to nlm for for comprehensive CLI/MCP documentation.



## CLI Reference

 For full command reference, run `nlm --ai` in the terminal to get comprehensive, up-to-date documentation:
  ```bash
  nlm --ai
  ```

  ## Authentication (CRITICAL)

  Skip auth check. run `nlm login` directly:
  ```bash
  nlm login
  ```
  This opens Chrome for authentication. If already authenticated, completes instantly.

 Session lifetime ~ ~20 minutes.


  For project-specific workflow improvements see `nlm` SKILL.md.

  ## Methodology
  For building high-quality notebooks with the 4-step ACG framework (Analyze, Challenge, Gap) see `notebooklm-expert` skill.


  ## Memory
  - nlm is managed upstream by `nlm skill install` — run `nlm skill update` to refresh. Do not manually edit this file.

