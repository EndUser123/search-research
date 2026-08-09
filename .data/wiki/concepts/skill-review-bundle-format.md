---
title: "Skill Review Bundle Format"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, bundle]
summary: >
  A review bundle is a standardized artifact produced by the /review_bundle skill that documents a single Claude Code skill's structure, architecture, integration points, and quality assessment. The bundles cluster around a 'bundle-skill-file' concept, capturing per-skill metadata, execution flow, com
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 16dac687-5ab6-4bf4-8330-632b0e92d852" (Software Quality Assurance (SQA), synced 2026-08-09)
  - "NotebookLM source 0605c65a-67c7-48f9-ae34-b461b2cf8604" (review_bundle_diagnose_20260326.md, synced 2026-08-09)
  - "NotebookLM source 091ffd19-04d5-4c9b-bb5c-f0bb47bc293d" (7 Layer Practical Framework, synced 2026-08-09)
  - "NotebookLM source 236a4073-b5db-4f8e-98f1-eecf41bc2cba" (review_bundle_apply_safety_patterns_20260326.md, synced 2026-08-09)
  - "NotebookLM source 407f0af0-7a58-4198-8673-d1b1a948b5ce" (review_bundle_skills_2026-03-29.md, synced 2026-08-09)
  - "NotebookLM source 56fc9932-df61-497a-be24-905e38a8ee35" (review_bundle_meta-review_20260326.md, synced 2026-08-09)
  - "NotebookLM source 608bdc8f-5b7d-4a3b-9f24-1b24a340adc4" (review_bundle_gto_20260326.md, synced 2026-08-09)
  - "NotebookLM source 6410b150-22d6-427a-a374-dbd11bd4a04b" (review_bundle_catch-22-detection_20260326.md, synced 2026-08-09)
  - "NotebookLM source 7d8f188b-e400-4c02-9a2c-5fb8a8d5689c" (review_bundle_debugRCA_20260326.md, synced 2026-08-09)
  - "NotebookLM source 816fc089-f51c-403e-9c0b-a28f282c7f66" (review_bundle_tdd_20260326.md, synced 2026-08-09)
  - "NotebookLM source 97131653-af2f-4c59-b63f-f1acd4b65e73" (review_bundle_data-safety-vcs_20260326.md, synced 2026-08-09)
  - "NotebookLM source 9f28b78a-19b9-4b65-9f79-e37ee62de4ed" (review_bundle_adversarial-rca_20260326.md, synced 2026-08-09)
  - "NotebookLM source ae35f065-35b0-4fe2-9879-c93421460ba6" (review_bundle_perf_20260326.md, synced 2026-08-09)
  - "NotebookLM source f65e83f4-3977-4f67-bdec-99089fef85db" (review_bundle_harden_20260326.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: skill-review-bundle-format
    - level: notebook
      id: 16dac687-5ab6-4bf4-8330-632b0e92d852
      title: Software Quality Assurance (SQA)
      url: https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852
    - level: cluster
      id: 0
      name: bundle-skill-file
relations:
  - target: wiki/concepts/skill.md-frontmatter-schema.md
    type: related
  - target: wiki/concepts/claude-code-skill-system.md
    type: related
  - target: wiki/concepts/7-layer-quality-model.md
    type: related
---

# Skill Review Bundle Format

## Decision context

**Definition:** A review bundle is a standardized artifact produced by the /review_bundle skill that documents a single Claude Code skill's structure, architecture, integration points, and quality assessment. The bundles cluster around a 'bundle-skill-file' concept, capturing per-skill metadata, execution flow, component inventories, design intent, known issues, and an SQA quality verdict in a uniform layout.

Synthesized from **13 contributing transcripts** in NotebookLM notebook *Software Quality Assurance (SQA)*, clustered into the "bundle-skill-file" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Each bundle records metadata fields including Skill Name, Description, Category, Trigger, Domain & Purpose, Enforcement mode, Environment (OS, Shell, Primary Language), and Key Integration targets.
- Execution mode is classified by file count: single-agent for single-SKILL.md scopes, and 4-agent parallel execution for large skills exceeding a 50-file threshold.
- Bundles document a skill's architecture via ASCII diagrams, module/hook/test inventories, and execution flow tables describing phase order, subagent roles, and state transitions.
- Design intent sections enumerate Architectural Pillars (e.g., evidence-based diagnosis, self-verification, parallel delegation) and Things That Must NOT Change (e.g., convergence gate criteria, phase ordering, anti-bleed rules).
- Known Issues tables list confirmed problems with impact and workarounds, and observed duplicates/overlaps between skills (e.g., sqa-orchestrator duplicates sqa/, sp is alias for scratchpad/).
- SQA Assessment provides a uniform Quality Attributes table rating Test Coverage, Documentation, and category-specific capabilities, with relevance tier (HIGH/MEDIUM) and explanatory notes.
- Integration Points sections map skill-to-skill handoffs, external service integrations, hook integration points, and data exchange contracts in a consistent tabular form.
- Bundle scope is rooted at P:/.claude/skills/<skill-name>/ and excludes caches such as .mypy_cache, .pytest_cache, .evidence, and .git directories.

## Verifiable values

| Name | Value |
|---|---|
| Total files in P:/.claude/skills/ | `15,137 files` |
| SKILL.md file count | `206` |
| Skill directories | `~164` |
| Top-level entries | `203` |
| Symlinks at top level | `13` |
| 4-agent execution threshold | `50 files` |
| diagnose skill SKILL.md length | `196 lines` |
| apply-safety-patterns SKILL.md length | `126 lines` |
| meta-review SKILL.md length | `312 lines` |
| tdd skill SKILL.md length | `~989 lines` |
| tdd skill version | `2.25.0` |
| tdd hook files | `4 Python hook files` |
| tdd test files | `4 test files` |
| debugRCA skill version | `2.11.1` |
| debugRCA hook files | `9 Python hook files` |
| debugRCA test files | `20+ test files` |
| debugRCA SKILL.md length | `~1000 lines` |
| gto skill version | `3.4.0` |
| gto test files | `20+ test files` |
| gto hook files | `5 hook files` |
| catch-22-detection SKILL.md length | `68 lines` |
| data-safety-vcs SKILL.md length | `142 lines` |
| anti-bleed gate test count | `21 tests` |
| harden SKILL.md length | `131 lines` |
| perf SKILL.md length | `132 lines` |
| adversarial-rca SKILL.md length | `151 lines` |
| Solo-dev reliability target | `75-85%` |
| Hook observability block rate threshold | `< 5% expected` |
| Convergence gate confidence threshold | `>= 0.85` |
| Synthesis agent confidence ceiling boost | `90%` |

## Related concepts

- skill.md-frontmatter-schema — SKILL.md Frontmatter Schema
- claude-code-skill-system — Claude Code Skill System
- 7-layer-quality-model — 7-Layer Quality Model
- [[constitutional-knowledge-system-(cks)]] — Constitutional Knowledge System (CKS)
- hook-based-enforcement-pattern — Hook-Based Enforcement Pattern

## Citations (from contributing transcripts)

- **Claim:** Each bundle records metadata including Skill Name, Description, Category, Trigger, Domain, Enforcement, Environment, and Key Integration in a consistent layout.
  - Source: review_bundle_diagnose_20260326.md (`0605c65a-67c7-48f9-ae34-b461b2cf8604`)
  - Context: Bundle Metadata: Skill Name: diagnose; Description: Structured diagnostic protocol with hypothesis testing; Category: debugging; Trigger: /diagnose; Domain & Purpose; Environment; Key Integration
- **Claim:** Execution mode is selected by file count: single-agent for SKILL.md-only scopes and 4-agent parallel for large skills above a 50-file threshold.
  - Source: review_bundle_gto_20260326.md (`608bdc8f-5b7d-4a3b-9f24-1b24a340adc4`)
  - Context: Execution Mode: 4-agents (large skill) — File Count: ~50 files (excluding .evidence, .git)
- **Claim:** Bundles for the /diagnose skill require 3+ hypotheses listed before any testing begins, with each hypothesis marked RULED OUT or CONFIRMED.
  - Source: review_bundle_diagnose_20260326.md (`0605c65a-67c7-48f9-ae34-b461b2cf8604`)
  - Context: PROTOCOL ENFORCEMENT: This skill REQUIRES: 3+ hypotheses listed before any testing begins; Each hypothesis has test command with exact syntax; Each hypothesis marked RULED OUT or CONFIRMED
- **Claim:** Bundles document architecture via ASCII diagrams plus module, hook, and test inventories with execution flow tables.
  - Source: review_bundle_tdd_20260326.md (`816fc089-f51c-403e-9c0b-a28f282c7f66`)
  - Context: Architecture Overview: 6-Phase Cycle: DISCOVER→RED→GREEN→VERIFY→REGRESSION→REFACTOR with tdd-test-writer, tdd-implementer, tdd-refactorer PARALLEL × N
- **Claim:** SQA Assessment provides a uniform Quality Attributes table rating Test Coverage, Documentation, and category-specific capabilities with relevance tier (HIGH/MEDIUM).
  - Source: review_bundle_apply_safety_patterns_20260326.md (`236a4073-b5db-4f8e-98f1-eecf41bc2cba`)
  - Context: SQA ASSESSMENT Quality Attributes: Test Coverage N/A; Documentation GOOD 126-line SKILL.md with success rates; Safety Enforcement EXCELLENT Constitutional compliance; SQA Relevance HIGH — Safety validation skill
- **Claim:** Bundles explicitly distinguish prohibited behaviors such as jumping to solution before listing all hypotheses or claiming 'probably' without test output.
  - Source: review_bundle_diagnose_20260326.md (`0605c65a-67c7-48f9-ae34-b461b2cf8604`)
  - Context: PROHIBITED BEHAVIORS: Jump to solution before listing all hypotheses; Test only one hypothesis (need 3+); Claim "probably" or "likely" without test output; Skip documenting the diagnostic path; Accept first plausible explanation
- **Claim:** Bundle scope excludes caches such as .mypy_cache, .pytest_cache, .evidence, and .git directories.
  - Source: review_bundle_gto_20260326.md (`608bdc8f-5b7d-4a3b-9f24-1b24a340adc4`)
  - Context: Scope: P:/.claude/skills/gto/; File Count: ~50 files (excluding .evidence, .git)
- **Claim:** Bundles document design intent sections enumerating Architectural Pillars and Things That Must NOT Change.
  - Source: review_bundle_debugRCA_20260326.md (`7d8f188b-e400-4c02-9a2c-5fb8a8d5689c`)
  - Context: Things That Must NOT Change: Evidence tier tagging — Core to confidence calibration; Triple-collection framework — Prevents incomplete investigations; Convergence gate criteria — Prevents premature conclusions; DISCOVER before diagnose — Investigation order enforced
- **Claim:** Known Issues tables in bundles list confirmed problems with impact and workarounds, including environment-variable dependency and import path fragility.
  - Source: review_bundle_tdd_20260326.md (`816fc089-f51c-403e-9c0b-a28f282c7f66`)
  - Context: Issue 3: gap_loader terminal_id uses WT_SESSION env var; Workaround: Acceptable for current Windows-only environment
- **Claim:** Bundles map skill-to-skill handoffs and external service integrations in tabular form, e.g., planning/ → code/ via tasks.json handoff.
  - Source: review_bundle_skills_2026-03-29.md (`407f0af0-7a58-4198-8673-d1b1a948b5ce`)
  - Context: Skill-to-Skill Handoffs: From planning/ To code/ Mechanism Plan output → tasks.json → /code execution

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `16dac687-5ab6-4bf4-8330-632b0e92d852`
(cluster `bundle-skill-file`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Software Quality Assurance (SQA)](https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
