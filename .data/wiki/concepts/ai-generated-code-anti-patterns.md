---
title: "AI-Generated Code Anti-Patterns"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Recurring problematic patterns observed in AI-generated source code that systematically undermine software quality, maintainability, and security at scale, as identified in research examining AI-assisted development workflows.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 22aa6821-f3d5-4ff6-8c62-a1cd7d1c8182" (Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA, synced 2026-07-28)
  - "Position: Humans are Missing from AI Coding Agent Research - Zora Wang" (https://zorazrw.github.io/files/position-haicode.pdf, transcript synced 2026-07-28)
  - "Army of Juniors: The AI Code Security Crisis" (https://www.ox.security/wp-content/uploads/2025/10/Army-of-Juniors-The-AI-Code-Security-Crisis.pdf, transcript synced 2026-07-28)
  - "Position: Humans are Missing from AI Coding Agent Research - Zora Wang" (https://zorazrw.github.io/files/position-haicode.pdf, transcript synced 2026-07-28)
  - "Army of Juniors: The AI Code Security Crisis" (https://www.ox.security/wp-content/uploads/2025/10/Army-of-Juniors-The-AI-Code-Security-Crisis.pdf, transcript synced 2026-07-28)
  - "Effective RCA2 Checklist" (https://www.nepatientsafety.org/file_download/ebc8ac97-ecf9-4711-b756-6f72c60e8ce6, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: ai-generated-code-anti-patterns
    - level: notebook
      id: 22aa6821-f3d5-4ff6-8c62-a1cd7d1c8182
      title: Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
      url: https://notebooklm.google.com/notebook/22aa6821-f3d5-4ff6-8c62-a1cd7d1c8182
    - level: cluster
      id: 3
      name: https-research-code
    - level: source_url
      url: https://zorazrw.github.io/files/position-haicode.pdf
      title: Position: Humans are Missing from AI Coding Agent Research - Zora Wang
    - level: source_url
      url: https://www.ox.security/wp-content/uploads/2025/10/Army-of-Juniors-The-AI-Code-Security-Crisis.pdf
      title: Army of Juniors: The AI Code Security Crisis
    - level: source_url
      url: https://www.nepatientsafety.org/file_download/ebc8ac97-ecf9-4711-b756-6f72c60e8ce6
      title: Effective RCA2 Checklist
relations:
  - target: wiki/concepts/ai-coding-agent-human-oversight.md
    type: related
  - target: wiki/concepts/root-cause-analysis-in-software-development.md
    type: related
  - target: wiki/concepts/code-quality-metrics.md
    type: related
---

# AI-Generated Code Anti-Patterns

## Decision context

**Definition:** Recurring problematic patterns observed in AI-generated source code that systematically undermine software quality, maintainability, and security at scale, as identified in research examining AI-assisted development workflows.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA*, clustered into the "https-research-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Research by OX Research (October 2025) identifies 10 critical anti-patterns in AI-generated code affecting software security at scale
- One documented anti-pattern is 'Comments Everywhere', characterized by excessive inline comments with minimal explanatory value
- Another anti-pattern involves 'Avoidance of Refactors', where generated code lacks the self-documenting quality that would prompt future developers to question or improve it
- Over-Specification represents a third anti-pattern, where AI generates verbose, overly detailed implementations rather than focused solutions
- These anti-patterns emerge from AI systems that prioritize speed and apparent completeness over code quality judgment
- Security implications arise when these patterns combine, creating attack surfaces or logic flaws at scale across AI-assisted codebases

## Verifiable values

| Name | Value |
|---|---|
| Documented anti-patterns | `10 (identified by OX Research)` |

## Related concepts

- [[ai-coding-agent-human-oversight]] — AI Coding Agent Human Oversight
- [[root-cause-analysis-in-software-development]] — Root Cause Analysis in Software Development
- [[code-quality-metrics]] — Code Quality Metrics

## Citations (from contributing transcripts)

- **Claim:** Research identifies 10 critical anti-patterns in AI-generated code
  - Source: Army of Juniors: The AI Code Security Crisis (`ed6274eb-28a3-42ce-ad70-b5146c98b6c0`)
  - Context: How 10 critical anti-patterns in AI-generated code are systematically undermining software security at scale
- **Claim:** Comments Everywhere is identified as a specific anti-pattern
  - Source: Army of Juniors: The AI Code Security Crisis (`ed6274eb-28a3-42ce-ad70-b5146c98b6c0`)
  - Context: Comments Everywhere | Note to Future AI Self
- **Claim:** Avoidance of Refactors is identified as a specific anti-pattern
  - Source: Army of Juniors: The AI Code Security Crisis (`ed6274eb-28a3-42ce-ad70-b5146c98b6c0`)
  - Context: Avoidance of Refactors | The Missing 'Who Wrote This Sh*t?' Reflex
- **Claim:** Over-Specification is identified as a specific anti-pattern
  - Source: Army of Juniors: The AI Code Security Crisis (`ed6274eb-28a3-42ce-ad70-b5146c98b6c0`)
  - Context: Over-Specification | Dispose-After-Use Code

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `22aa6821-f3d5-4ff6-8c62-a1cd7d1c8182`
(cluster `https-research-code`). No claims are made
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

- NotebookLM notebook [Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA](https://notebooklm.google.com/notebook/22aa6821-f3d5-4ff6-8c62-a1cd7d1c8182)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
