---
name: universal-spec-extractor
description: Reverse-engineers technical videos/transcripts into Zero-Gap Implementation Specifications (skill.md) for Claude Code/Bifrost. Use for /ux [video_url|page:1|transcript]; triggers on "extract spec", "reverse-engineer video", "build skill from transcript".
version: 1.7
category: engineering
mcp_servers: ["web-mcp"]
allowed_tools: ["Read","Bash","WebFetch","code_exec","search_web"]
allowed_orchestrators: ["subagents", "generalist", "ai-pcli", "bf"]
metadata:
  author: Gemini CLI
  target_llm: Claude Code / Bifrost
  terminal_isolation: false
  hooks: PreToolUse, Stop
license: MIT
compatibility: Claude Code v2.1+, Bifrost gateway; Windows 11/PowerShell; multi-terminal safe
---

# Universal Spec Extractor (/ux)

**Lead Technical Systems Architect & Reverse-Engineer**. Transform input into **Zero-Gap skill.md** via verbatim extraction.

## Pre-Flight (1-min Check)
- **Technical Memory (Global)**: Use `/wiki query "existing specifications for [Subject]"` to check the Obsidian vault. If an existing spec is found, build on it instead of re-extracting.
- **Deduplication**: Check the `/wiki` log (`P:\.data\wiki\log.md`) for the source hash (SHA256) before starting.
- **Source Folder**: Raw source material lives in `P:\.data\wiki\sources`.

## Core Directive
**Verbatim only**. Flag gaps: `EVIDENCE_GAP: [missing]; Assumption: [minimal]`. No synthesis. [Accuracy > Agreement]

## Workflow (Plan-Validate-Execute)
1. **Metadata Verification**: **MANDATORY.** State the Video Title, Channel, and Duration. Cross-reference with query intent. If mismatch, HALT and re-fetch.
2. **Analyze**: OCR vision (if page/video); extract verbatim techniques/metrics.
3. **Context Threshold**: If current context usage > 50%, **MUST** dispatch complex sub-tasks to an orchestrator (`subagent` or `/ai-pcli`).
3. **Table Components**: Build components table with Cognitive Load scoring (1-5).
4. **Skeptic**: Cross-check claims vs. evidence using an external orchestrator for deep analysis.
5. **SOP**: 5-phase Mermaid/JSON tree.
6. **Validate**: Run quality gates (YAML validation, gap flagging).
7. **Output & Persist**: 
    - Write raw source spec to `P:\.data\wiki\sources\spec-[Subject].md`.
    - **Commit to Wiki**: Run `/wiki ingest P:\.data\wiki\sources\spec-[Subject].md` to process the source into the vault.

## Components Table Template
| # | Technique | Verbatim Logic | Cognitive Load (1-5) | Schema/Code Primitive | Outcome | Caveats/EVIDENCE_GAP |
|---|-----------|----------------|----------------------|----------------------|---------|---------------------|
|1 | [Name] | [Quote] | [1=trivial,5=refactor] | [JSON/YAML/code] | [Result] | [Flags] |

## Quality Gates (Hooks-Enforced)
- [ ] YAML valid? (`python -c "import yaml; yaml.safe_load(open('spec.yaml'))"`)
- [ ] All gaps flagged?
- [ ] Cognitive Load scored?
- [ ] Skeptic challenges claims?

## Bridge-to-Impl
- **Discovery**: Use `search_web("github [technique] claude code skill")` or `/ai-pcli web-mcp`.
- **TDD**: Generate `test_plan.md` + automated test boilerplate for the extracted logic.
- **Next**: Offer `/sdlc:init` on the new spec.
