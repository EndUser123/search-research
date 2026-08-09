---
title: "GitHub Repository File Structure Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, file]
summary: >
  This concept describes the organizational patterns observed across multiple GitHub repositories, particularly those implementing linting, policy enforcement, AI guardrails, and static analysis tools. These repositories share common structural conventions for source code, documentation, configuration
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
      id: github-repository-file-structure-patterns
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
  - target: wiki/concepts/open-policy-agent.md
    type: related
  - target: wiki/concepts/semgrep-static-analysis.md
    type: related
  - target: wiki/concepts/ai-guardrails.md
    type: related
---

# GitHub Repository File Structure Patterns

## Decision context

**Definition:** This concept describes the organizational patterns observed across multiple GitHub repositories, particularly those implementing linting, policy enforcement, AI guardrails, and static analysis tools. These repositories share common structural conventions for source code, documentation, configuration, and testing artifacts.

Synthesized from **24 contributing transcripts** in NotebookLM notebook *Claude Code - Skills: Agentic Coding and Prompt Engineering*, clustered into the "file-github-json" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Standard repository root files typically include LICENSE, README.md, CONTRIBUTING.md, and security-related files such as SECURITY.md
- Go-based projects commonly include go.mod and go.sum files for dependency management
- Python projects frequently use pyproject.toml for project configuration and requirements.txt for dependencies
- Source code is organized into subdirectories such as dir cli/, dir src/, dir cmd/, dir internal/, and dir vulture/
- Documentation is commonly placed in docs/ directories with API reference, guides, and conceptual documentation
- Testing artifacts appear in test/ or tests/ directories, with test configuration files like pytest.ini and pyrightconfig.json
- Agent configuration files such as AGENTS.md appear across multiple repositories to define AI agent behaviors
- Build artifacts include Dockerfiles, Makefiles, and configuration files like buf.yaml
- Examples and demo content are stored in example/, examples/, or demo_repo/ directories

## Related concepts

- open-policy-agent — Open Policy Agent
- semgrep-static-analysis — Semgrep Static Analysis
- ai-guardrails — AI Guardrails
- protocol-buffer-build-tools — Protocol Buffer Build Tools
- event-catalog-architecture — Event Catalog Architecture

## Citations (from contributing transcripts)

- **Claim:** Standard repository root files include LICENSE, README.md, and CONTRIBUTING.md
  - Source: open-policy-agent-opa-part-1.md (`2770d0e5-3267-4875-bb06-a92a440a6e22`)
  - Context: file LICENSE, file README.md, file CONTRIBUTING.md
- **Claim:** Go-based projects include go.mod and go.sum files
  - Source: open-policy-agent-opa-part-1.md (`2770d0e5-3267-4875-bb06-a92a440a6e22`)
  - Context: file go.mod, file go.sum
- **Claim:** Python projects use pyproject.toml for configuration
  - Source: guardrails-ai-guardrails-part-1.md (`c28b6434-de0d-407e-84fd-96b97153ae99`)
  - Context: file pyproject.toml, file pyrightconfig.json
- **Claim:** Source code is organized into subdirectories like cli/, src/, and internal/
  - Source: returntocorp-semgrep-part-1.md (`b32e53ac-9295-4027-a148-0109b2e7a226`)
  - Context: dir cli/, dir cli/src/, dir cli/src/semdep/
- **Claim:** Documentation is placed in docs/ directories with API reference content
  - Source: guardrails-ai-guardrails-part-2.md (`4eebb88e-6058-494b-86aa-71a858ce7720`)
  - Context: dir docs/api_reference/, file actions.md, file errors.md, file formatters.md
- **Claim:** Testing artifacts are stored in test/ or tests/ directories
  - Source: jendrikseipp-vulture.md (`8e55fe84-8e15-405c-8213-bad25963a545`)
  - Context: dir tests/, py test_confidence.py, py test_config.py, py test_encoding.py
- **Claim:** Agent configuration files appear across repositories
  - Source: event-catalog-eventcatalog-part-1.md (`a227f5c0-5aa8-479b-9f2e-d3cc41801fa4`)
  - Context: file AGENTS.md, file CLAUDE.md
- **Claim:** Build artifacts include Dockerfiles and Makefiles
  - Source: open-policy-agent-opa-part-3.md (`198edffc-7d15-4acd-b0bc-ba6527ecc6b0`)
  - Context: file Dockerfile, file Makefile, file buf.yaml
- **Claim:** Examples and demo content are stored in example/ or demo_repo/ directories
  - Source: duriantaco-vouch.md (`52db9ded-2319-4d01-857c-a876f5233f26`)
  - Context: dir demo_repo/, file CODEOWNERS, file README.md

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
