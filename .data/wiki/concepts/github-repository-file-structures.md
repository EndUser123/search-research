---
title: "GitHub Repository File Structures"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, file]
summary: >
  GitHub repositories in this collection share common patterns in how they organize project files, with root-level configuration files, directories for source code, documentation, and agent-related support files, and branching strategies that use main as the primary branch.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 29bbaa7b-965f-40b5-a404-76b4d2e7308c" (Claude Code - Skills: Agentic Coding and Prompt Engineering, synced 2026-07-27)
  - "NotebookLM source 054e4ea0-7888-45aa-b776-fe0ac14b12f9" (review_bundle_pre-mortem_2026-03-29.md, synced 2026-07-27)
  - "NotebookLM source 198edffc-7d15-4acd-b0bc-ba6527ecc6b0" (open-policy-agent-opa-part-3.md, synced 2026-07-27)
  - "NotebookLM source 2770d0e5-3267-4875-bb06-a92a440a6e22" (open-policy-agent-opa-part-1.md, synced 2026-07-27)
  - "NotebookLM source 3c69f0e2-675b-4134-a05c-57823b95b9a4" (bufbuild-buf.md, synced 2026-07-27)
  - "NotebookLM source 46656598-78e5-4dd5-9144-2acebaabda02" (fluxcd-flux-schema.md, synced 2026-07-27)
  - "GitHub - fluxcd/flux-schema: Flux CLI plugin for Kubernetes manifests validation against JSON Schemas and CEL rules · GitHub" (https://github.com/fluxcd/flux-schema, transcript synced 2026-07-27)
  - "NotebookLM source 4eebb88e-6058-494b-86aa-71a858ce7720" (guardrails-ai-guardrails-part-2.md, synced 2026-07-27)
  - "NotebookLM source 52db9ded-2319-4d01-857c-a876f5233f26" (duriantaco-vouch.md, synced 2026-07-27)
  - "NotebookLM source 5c93e9ac-e325-4117-b930-acb160d790a1" (github-spec-kit.md, synced 2026-07-27)
  - "NotebookLM source 6fc6795d-082f-45d0-95ca-5bf4ce7cf86a" (open-policy-agent-conftest.md, synced 2026-07-27)
  - "NotebookLM source 7b064db2-0839-4d71-91e3-0fe69b67b858" (returntocorp-semgrep-part-2.md, synced 2026-07-27)
  - "NotebookLM source 8357bb81-5329-4c8a-a440-190978d3029d" (open-policy-agent-opa-part-2.md, synced 2026-07-27)
  - "NotebookLM source 8cdb25ef-8856-4420-a521-a057501176d5" (event-catalog-eventcatalog-part-2.md, synced 2026-07-27)
  - "NotebookLM source 8e55fe84-8e15-405c-8213-bad25963a545" (jendrikseipp-vulture.md, synced 2026-07-27)
  - "NotebookLM source a227f5c0-5aa8-479b-9f2e-d3cc41801fa4" (event-catalog-eventcatalog-part-1.md, synced 2026-07-27)
  - "NotebookLM source acb34fa9-eead-49a2-aa92-8a41e2e9eb9c" (NVIDIA-NeMo-Guardrails-part-2.md, synced 2026-07-27)
  - "NotebookLM source b32e53ac-9295-4027-a148-0109b2e7a226" (returntocorp-semgrep-part-1.md, synced 2026-07-27)
  - "NotebookLM source b5f09b7d-c324-48e7-bedb-44eaae976a1a" (seddonym-import-linter.md, synced 2026-07-27)
  - "NotebookLM source c28b6434-de0d-407e-84fd-96b97153ae99" (guardrails-ai-guardrails-part-1.md, synced 2026-07-27)
  - "NotebookLM source c3990c34-54bf-4baf-a912-fe6b73b8dadb" (Fission-AI-openspec-part-1.md, synced 2026-07-27)
  - "NotebookLM source c39928df-9a10-4b23-ad3f-5cc705b3e408" (returntocorp-semgrep-part-3.md, synced 2026-07-27)
  - "NotebookLM source c6038cfd-b65a-48fa-af0a-c4bac83840aa" (Fission-AI-openspec-part-2.md, synced 2026-07-27)
  - "NotebookLM source d7c4993a-abc8-4734-9396-10a1cc0f1f2d" (paul-gauthier-aider.md, synced 2026-07-27)
  - "NotebookLM source da72023d-3bfb-4a89-a794-d5b802b8fef6" (NVIDIA-NeMo-Guardrails-part-1.md, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: github-repository-file-structures
    - level: notebook
      id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
      title: Claude Code - Skills: Agentic Coding and Prompt Engineering
      url: https://notebooklm.google.com/notebook/29bbaa7b-965f-40b5-a404-76b4d2e7308c
    - level: cluster
      id: 1
      name: file-github-json
    - level: source_url
      url: https://github.com/fluxcd/flux-schema
      title: GitHub - fluxcd/flux-schema: Flux CLI plugin for Kubernetes manifests validation against JSON Schemas and CEL rules · GitHub
relations:
  - target: wiki/concepts/repository-agent-configuration.md
    type: related
  - target: wiki/concepts/policy-as-code-repositories.md
    type: related
  - target: wiki/concepts/ai-development-tooling.md
    type: related
---

# GitHub Repository File Structures

## Decision context

**Definition:** GitHub repositories in this collection share common patterns in how they organize project files, with root-level configuration files, directories for source code, documentation, and agent-related support files, and branching strategies that use main as the primary branch.

Synthesized from **24 contributing transcripts** in NotebookLM notebook *Claude Code - Skills: Agentic Coding and Prompt Engineering*, clustered into the "file-github-json" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Repositories use root-level metadata files including CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, LICENSE, README.md, and SECURITY.md
- Source code is organized in directories such as dir ast/, dir cli/src/, dir cmd/, dir vulture/, dir docs/, dir aider/, dir catalog/, dir api/
- Agent-related configuration files appear across repositories: AGENTS.md files are present in open-policy-agent/opa, returntocorp/semgrep, event-catalog/eventcatalog, NVIDIA/NeMo-Guardrails, github/spec-kit, and Fission-AI/openspec
- Documentation is typically organized in /docs/ directories with subdirectories for guides, reference materials, examples, and walkthroughs
- Python projects use pyproject.toml for configuration, while Go projects use go.mod and go.sum
- Build artifacts and tests are separated into dedicated directories: tests/, test/, dir benchmark/, dir tests/toml/
- Examples and demo content appear in examples/ or demo_repo/ directories
- Configuration formats include YAML (buf.yaml, action.yaml, .yml files), TOML (pyproject.toml, ruff.toml), JSON (builtin_metadata.json, capabilities.json), and Markdown documentation files
- All repositories in the collection use main as their primary branch

## Verifiable values

| Name | Value |
|---|---|
| Repositories examined | `24 GitHub repositories` |
| Common root files | `CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, LICENSE, README.md, SECURITY.md` |
| Primary branch | `main (all repositories)` |
| Agent support files | `AGENTS.md (found in 6+ repositories)` |
| Documentation structure | `dir docs/ with subdirectories for guides, reference, examples, walkthroughs` |

## Related concepts

- repository-agent-configuration — Repository Agent Configuration
- policy-as-code-repositories — Policy-as-Code Repositories
- ai-development-tooling — AI Development Tooling

## Citations (from contributing transcripts)

- **Claim:** Repositories contain AGENTS.md files for agent configuration
  - Source: open-policy-agent-opa-part-3.md (`198edffc-7d15-4acd-b0bc-ba6527ecc6b0`)
  - Context: dir ast/ file builtins.go file capabilities.go file check.go file compile.go file compile_test.go
- **Claim:** Documentation is organized in /docs/ directories with reference, examples, and walkthroughs subdirectories
  - Source: github-spec-kit.md (`5c93e9ac-e325-4117-b930-acb160d790a1`)
  - Context: dir docs/ file README.md file docfx.json file index.md file installation.md file local-development.md file quickstart.md file toc.yml file upgrade.md dir docs/community/ file bundles.md file extensions.md
- **Claim:** Repositories use standard metadata files at root level
  - Source: open-policy-agent-opa-part-1.md (`2770d0e5-3267-4875-bb06-a92a440a6e22`)
  - Context: file ADOPTERS.md file AGENTS.md file CHANGELOG.md file CODE_OF_CONDUCT.md file COMMUNITY_GUIDELINES.md file CONTRIBUTING.md file Dockerfile file GOVERNANCE.md file LICENSE
- **Claim:** All repositories use main as their primary branch
  - Source: open-policy-agent-opa-part-3.md (`198edffc-7d15-4acd-b0bc-ba6527ecc6b0`)
  - Context: Branch: main | Source: https://github.com/open-policy-agent/opa
- **Claim:** Python projects use pyproject.toml while Go projects use go.mod
  - Source: guardrails-ai-guardrails-part-2.md (`4eebb88e-6058-494b-86aa-71a858ce7720`)
  - Context: file CLAUDE.md file CONTRIBUTING.md file LICENSE file Makefile file README.md file SECURITY_ADVISORY.md file pyproject.toml file pyrightconfig.json
- **Claim:** Source code is organized in cmd/, src/, and library-specific directories
  - Source: duriantaco-vouch.md (`52db9ded-2319-4d01-857c-a876f5233f26`)
  - Context: dir cmd/vouch/ file main.go dir demo_repo/ dir docs/ dir internal/vouch/ file artifacts.go
- **Claim:** Tests are separated into dedicated test directories
  - Source: jendrikseipp-vulture.md (`8e55fe84-8e15-405c-8213-bad25963a545`)
  - Context: dir tests/ py test_conditions.py py test_confidence.py py test_config.py py test_encoding.py py test_errors.py py test_format_strings.py
- **Claim:** Examples and demo content appear in examples/ directories
  - Source: event-catalog-eventcatalog-part-1.md (`a227f5c0-5aa8-479b-9f2e-d3cc41801fa4`)
  - Context: dir examples/default/ file Dockerfile file eventcatalog.config.js file eventcatalog.styles.css

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `29bbaa7b-965f-40b5-a404-76b4d2e7308c`
(cluster `file-github-json`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Claude Code - Skills: Agentic Coding and Prompt Engineering](https://notebooklm.google.com/notebook/29bbaa7b-965f-40b5-a404-76b4d2e7308c)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
