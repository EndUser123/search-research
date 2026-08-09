---
title: "Bundle Skill Approach"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, bundle]
summary: >
  A review bundle is a structured documentation pattern generated for individual Claude Code skills, capturing project context, execution directives, workflows, and an SQA assessment in a consistent Markdown format. Each bundle scopes a single skill under P:/.claude/skills/<skill>/ and consolidates it
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 16dac687-5ab6-4bf4-8330-632b0e92d852" (Software Quality Assurance (SQA), synced 2026-08-09)
  - "NotebookLM source 01b8e838-5683-428d-88e2-ed8eef0abbc1" (review_bundle_artifact-audit_20260326.md, synced 2026-08-09)
  - "NotebookLM source 128baa2a-0701-48e7-bfe9-f8132385f6dc" (review_bundle_docs-validate_20260326.md, synced 2026-08-09)
  - "NotebookLM source 17d002c6-fefd-47d9-95f7-11dbc22f3731" (review_bundle_hook-inventory_20260326.md, synced 2026-08-09)
  - "NotebookLM source 3e0150f9-5de2-4cc7-88b2-4407eb86a86e" (review_bundle_verify_20260326.md, synced 2026-08-09)
  - "NotebookLM source 41e6396f-1d41-425c-bcb3-1879261f4443" (review_bundle_evidence-tiers_20260326.md, synced 2026-08-09)
  - "NotebookLM source 5ac6ca17-a531-465b-8468-a94692e552cf" (review_bundle_evidence-applicability_20260326.md, synced 2026-08-09)
  - "NotebookLM source 5ec4e7a2-8b97-4fc8-bd81-6f692b3434ef" (review_bundle_my-test-skill_20260326.md, synced 2026-08-09)
  - "NotebookLM source 8a5a5be3-65d8-4fd5-9ae6-f36df7336e39" (review_bundle_artifact-done_20260326.md, synced 2026-08-09)
  - "NotebookLM source c1f6daf1-0009-4ce4-83e0-7adbebe41738" (review_bundle_hook-audit_20260326.md, synced 2026-08-09)
  - "NotebookLM source f26ee980-788e-46c9-b1ca-987f9dee7737" (review_bundle_code-analyzer-eval0_20260326.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: bundle-skill-approach
    - level: notebook
      id: 16dac687-5ab6-4bf4-8330-632b0e92d852
      title: Software Quality Assurance (SQA)
      url: https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852
    - level: cluster
      id: 1
      name: bundle-skill-hook
relations:
  - target: wiki/concepts/evidence-tiers.md
    type: related
  - target: wiki/concepts/evidence-applicability.md
    type: related
  - target: wiki/concepts/4-tier-verification.md
    type: related
---

# Bundle Skill Approach

## Decision context

**Definition:** A review bundle is a structured documentation pattern generated for individual Claude Code skills, capturing project context, execution directives, workflows, and an SQA assessment in a consistent Markdown format. Each bundle scopes a single skill under P:/.claude/skills/<skill>/ and consolidates its metadata, configuration, validation rules, and quality attributes into one reviewable artifact.

Synthesized from **10 contributing transcripts** in NotebookLM notebook *Software Quality Assurance (SQA)*, clustered into the "bundle-skill-hook" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Every bundle includes a PROJECT CONTEXT section listing Skill Name, Description, Version, Category, Triggers, Aliases, Environment (OS, Shell, Primary Language), and Key Integration points
- Bundles classify skills by category such as tracking, quality, observability, verification, and analysis
- Execution directives are specified as explicit shell commands (often python scripts under P:/.claude/skills/<skill>/resources/scripts/) so reviewers can reproduce skill behavior
- Skills that emit documentation quality validation define configuration options including mode (suggestive, blocking, off), severity_threshold (low, medium, high), and auto_validate (true, false)
- An automatic validation design fires a PostToolUse_documentation_validator.py design on Write/Edit operations against .md files in skills directories, returning a warning dict or permissionDecision=deny
- An intelligent mode-selection design recommends modes based on issue counts: 3+ HIGH issues → blocking, 1-2 HIGH or 5+ MEDIUM → suggestive, fewer → off
- A evidence tier design assigns confidence ceilings per tier: Tier 1 = 95% (execution artifacts), Tier 2 = 85% (official docs), Tier 3 = 75% (static analysis), Tier 4 = 50% (unverified claims), with mixed tiers taking the lowest ceiling
- A 4-tier verification pipeline is documented with explicit durations and evidence requirements: Tier 0 checklist (~0.3s, fast-fail) → Tier 1 component (pytest) → Tier 2 integration (event chain) → Tier 3 e2e (actual invocation)
- Verification prohibits claiming 'verified' without running all 4 tiers in real-time mode, or without TSR >= 95% threshold in post-hoc mode
- An evidence-applicability design checks four alignment dimensions: Temporal (present-state evidence for present-tense claims), Scope (same system/branch/project), Authority (canonical, not draft/deprecated), and Identity (the actual entity, not similar-named)
- Skill triggers are enumerated as slash commands and natural-language phrases (e.g., /artifact-audit, 'artifact audit', 'pending documentation'), with aliases for shorthand invocation
- An SQA Assessment section rates each skill across Quality Attributes (Test Coverage, Documentation, Error Handling, plus skill-specific attributes) using GOOD/EXCELLENT/MEDIUM/HIGH/LOW/N/A ratings
- Hook classification categories from /hook-inventory include DIRECT_REGISTERED, ROUTER_DISPATCHED, UTILITY_MODULE, ROUTER_FILE, TEST_FILE, ARCHIVE_OBSOLETE, CONFIRMED_DEAD, FILE_NOT_FOUND, POSSIBLE_UTILITY, and SUBCOMPONENT
- An enforcement timeline in artifact tracking uses three severity levels: Critical (5 min warn, 30 min block), Standard (30 min warn, 2 hours block), Low (never warn, never block)
- Validation rules include explicit prohibited actions and required output formats (e.g., 'NEVER claim clean without scanning', 'NEVER hide critical items', 'Group by severity level')

## Verifiable values

| Name | Value |
|---|---|
| Evidence Tier 1 ceiling | `95%` |
| Evidence Tier 2 ceiling | `85%` |
| Evidence Tier 3 ceiling | `75%` |
| Evidence Tier 4 ceiling | `50%` |
| TSR threshold for post-hoc verified status | `>= 95%` |
| Tier 0 checklist duration | `~0.3 seconds` |
| Critical severity warn threshold | `5 min` |
| Critical severity block threshold | `30 min` |
| Standard severity warn threshold | `30 min` |
| Standard severity block threshold | `2 hours` |
| Stub file line threshold | `under 50 lines` |
| Blocking mode trigger (HIGH issues) | `3+ HIGH issues` |
| Suggestive mode trigger (MEDIUM issues) | `5+ MEDIUM issues` |
| Verify skill test file count | `15+ test files` |
| Docs-validate SKILL.md length | `468-line SKILL.md` |

## Related concepts

- [[evidence-tiers]] — Evidence Tiers
- [[evidence-applicability]] — Evidence Applicability
- [[4-tier-verification]] — 4-Tier Verification
- [[artifact-audit]] — Artifact Audit
- [[artifact-done]] — Artifact Done
- [[hook-inventory]] — Hook Inventory
- [[hook-audit]] — Hook Audit
- [[docs-validate]] — Docs Validate
- [[code-analyzer-eval0]] — Code Analyzer Eval0
- [[my-test-skill]] — My Test Skill

## Citations (from contributing transcripts)

- **Claim:** Review bundles are generated with timestamps and scope a single skill directory under P:/.claude/skills/
  - Source: review_bundle_artifact-audit_20260326.md (`01b8e838-5683-428d-88e2-ed8eef0abbc1`)
  - Context: Review Bundle: /artifact-audit Skill
Generated
: 2026-03-26T19:30:00Z

Scope
: P:/.claude/skills/artifact-audit/

File Count
: 1 file (SKILL.md only)
- **Claim:** Each bundle contains PROJECT CONTEXT, EXECUTION DIRECTIVE, and SQA ASSESSMENT sections
  - Source: review_bundle_verify_20260326.md (`3e0150f9-5de2-4cc7-88b2-4407eb86a86e`)
  - Context: 1. PROJECT CONTEXT
2. ARCHITECTURE OVERVIEW
3. EXECUTION AND DATA FLOW
4. COMPONENT INVENTORY
5. DESIGN INTENT AND NON-NEGOTIABLES
6. KNOWN ISSUES
7. INTEGRATION POINTS
8. SQA ASSESSMENT
- **Claim:** Evidence tiers impose confidence ceilings: Tier 1=95%, Tier 2=85%, Tier 3=75%, Tier 4=50%
  - Source: review_bundle_evidence-tiers_20260326.md (`41e6396f-1d41-425c-bcb3-1879261f4443`)
  - Context: 1
95%
Execution artifacts, logs, test output
2
85%
Official docs, specs, peer-reviewed
3
75%
Static analysis, logical derivation
4
50%
Comments, unverified claims, speculation
- **Claim:** The /verify skill uses a 4-tier verification pipeline with explicit tier durations and fast-fail behavior
  - Source: review_bundle_verify_20260326.md (`3e0150f9-5de2-4cc7-88b2-4407eb86a86e`)
  - Context: Tier 0: Checklist Verification (Fast-Fail)
Duration
: ~0.3 seconds
Purpose
: Catch configuration and structural issues before expensive tests
- **Claim:** Post-hoc verification requires TSR >= 95% before claiming 'verified'
  - Source: review_bundle_verify_20260326.md (`3e0150f9-5de2-4cc7-88b2-4407eb86a86e`)
  - Context: Claim 'verified' without TSR >= 95% threshold (post-hoc mode)
- **Claim:** Documentation validation defines mode, severity_threshold, and auto_validate configuration options
  - Source: review_bundle_docs-validate_20260326.md (`128baa2a-0701-48e7-bfe9-f8132385f6dc`)
  - Context: mode
 (default: 
suggestive
):
severity_threshold
 (default: 
medium
):
auto_validate
 (default: 
true
)
- **Claim:** An automatic validation design fires PostToolUse_documentation_validator.py on Write/Edit of .md files in skills directories
  - Source: review_bundle_docs-validate_20260326.md (`128baa2a-0701-48e7-bfe9-f8132385f6dc`)
  - Context: PostToolUse Hook
: 
PostToolUse_documentation_validator.py
Trigger
: Write/Edit operations on 
.md
 files in skills directories
- **Claim:** Intelligent mode selection recommends blocking at 3+ HIGH issues and suggestive at 1-2 HIGH or 5+ MEDIUM issues
  - Source: review_bundle_docs-validate_20260326.md (`128baa2a-0701-48e7-bfe9-f8132385f6dc`)
  - Context: Condition
Recommended Mode
3+ HIGH issues
blocking
1-2 HIGH issues
suggestive
5+ MEDIUM issues
suggestive
Fewer issues
off
- **Claim:** Evidence-applicability checks four alignment dimensions: Temporal, Scope, Authority, Identity
  - Source: review_bundle_evidence-applicability_20260326.md (`5ac6ca17-a531-465b-8468-a94692e552cf`)
  - Context: Temporal
Is this current enough for a present-tense claim?
Scope
Is this from the same system/branch/project?
Authority
Is this canonical, not draft/deprecated?
Identity
Is this the actual entity, not similar-named?
- **Claim:** Present-tense claims require present-state evidence; historical evidence supports 'was' claims only
  - Source: review_bundle_evidence-applicability_20260326.md (`5ac6ca17-a531-465b-8468-a94692e552cf`)
  - Context: Present-tense claims require present-state evidence. Historical evidence supports 'was' claims, not 'is' claims.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `16dac687-5ab6-4bf4-8330-632b0e92d852`
(cluster `bundle-skill-hook`). No claims are made
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
