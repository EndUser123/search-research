---
title: "Agent Stop Conditions"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, researchgate]
summary: >
  Agent stop conditions define the criteria that determine when an LLM coding agent terminates its execution loop, based on verification outcomes and loop specifications.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d" (Deep Research Prompts, Methods, Examples, synced 2026-07-28)
  - "Integrity: Finding Integer Errors by Targeted Fuzzing - ResearchGate" (https://www.researchgate.net/publication/347837974_Integrity_Finding_Integer_Errors_by_Targeted_Fuzzing, transcript synced 2026-07-28)
  - "A Deterministic Control Plane for LLM Coding Agents | Request PDF - ResearchGate" (https://www.researchgate.net/publication/408106373_A_Deterministic_Control_Plane_for_LLM_Coding_Agents, transcript synced 2026-07-28)
  - "The anatomy of a loop specification. A trigger starts the agent - ResearchGate" (https://www.researchgate.net/figure/The-anatomy-of-a-loop-specification-A-trigger-starts-the-agent-the-agent-executes-by_fig2_408341189, transcript synced 2026-07-28)
  - "Stop Paying AI to Pretend It Worked - Gamma" (https://gamma.app/docs/Stop-Paying-AI-to-Pretend-It-Worked-mwdm89kgxhmsfut, transcript synced 2026-07-28)
  - "Dominant verification level across the fifty loops. Half verify... | Download Scientific Diagram - ResearchGate" (https://www.researchgate.net/figure/Dominant-verification-level-across-the-fifty-loops-Half-verify-deterministically-level_fig3_408341189, transcript synced 2026-07-28)
  - "Stop Paying AI to Pretend It Worked - Gamma" (https://gamma.app/docs/Stop-Paying-AI-to-Pretend-It-Worked-mwdm89kgxhmsfut, transcript synced 2026-07-28)
  - "(PDF) Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - ResearchGate" (https://www.researchgate.net/publication/408341189_Stop_Hand-Holding_Your_Coding_Agent_Engineering_the_Loops_that_Replace_Step-by-Step_Prompting, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: agent-stop-conditions
    - level: notebook
      id: 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
      title: Deep Research Prompts, Methods, Examples
      url: https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
    - level: cluster
      id: 5
      name: researchgate-agent-stop
    - level: source_url
      url: https://www.researchgate.net/publication/347837974_Integrity_Finding_Integer_Errors_by_Targeted_Fuzzing
      title: Integrity: Finding Integer Errors by Targeted Fuzzing - ResearchGate
    - level: source_url
      url: https://www.researchgate.net/publication/408106373_A_Deterministic_Control_Plane_for_LLM_Coding_Agents
      title: A Deterministic Control Plane for LLM Coding Agents | Request PDF - ResearchGate
    - level: source_url
      url: https://www.researchgate.net/figure/The-anatomy-of-a-loop-specification-A-trigger-starts-the-agent-the-agent-executes-by_fig2_408341189
      title: The anatomy of a loop specification. A trigger starts the agent - ResearchGate
    - level: source_url
      url: https://gamma.app/docs/Stop-Paying-AI-to-Pretend-It-Worked-mwdm89kgxhmsfut
      title: Stop Paying AI to Pretend It Worked - Gamma
    - level: source_url
      url: https://www.researchgate.net/figure/Dominant-verification-level-across-the-fifty-loops-Half-verify-deterministically-level_fig3_408341189
      title: Dominant verification level across the fifty loops. Half verify... | Download Scientific Diagram - ResearchGate
    - level: source_url
      url: https://www.researchgate.net/publication/408341189_Stop_Hand-Holding_Your_Coding_Agent_Engineering_the_Loops_that_Replace_Step-by-Step_Prompting
      title: (PDF) Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - ResearchGate
relations:
  - target: wiki/concepts/deterministic-control-plane.md
    type: related
  - target: wiki/concepts/verification-patterns-in-agent-loops.md
    type: related
  - target: wiki/concepts/loop-specification-design.md
    type: related
---

# Agent Stop Conditions

## Decision context

**Definition:** Agent stop conditions define the criteria that determine when an LLM coding agent terminates its execution loop, based on verification outcomes and loop specifications.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *Deep Research Prompts, Methods, Examples*, clustered into the "researchgate-agent-stop" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Loop specifications include a trigger that initiates agent execution and stopping criteria that conclude the loop
- Verification approaches vary across loops, with some implementing deterministic verification to confirm task completion
- Half of studied loops employ deterministic verification levels, indicating a significant design pattern for agent termination
- Agent termination replaces step-by-step prompting, allowing autonomous loop control without continuous user guidance
- Loop specifications define both execution behavior and termination conditions within the same structure

## Related concepts

- [[deterministic-control-plane]] — Deterministic Control Plane
- [[verification-patterns-in-agent-loops]] — Verification Patterns in Agent Loops
- [[loop-specification-design]] — Loop Specification Design

## Citations (from contributing transcripts)

- **Claim:** Loop specifications include a trigger that initiates agent execution and stopping criteria that conclude the loop
  - Source: The anatomy of a loop specification. A trigger starts the agent - ResearchGate (`2c5d815d-6418-499f-b149-e957d906abaa`)
  - Context: The anatomy of a loop specification. A trigger starts the agent
- **Claim:** Verification approaches vary across loops, with some implementing deterministic verification to confirm task completion
  - Source: Dominant verification level across the fifty loops. Half verify... | Download Scientific Diagram - ResearchGate (`6265eaf4-5685-45be-afb2-3fb9022c8fe5`)
  - Context: Dominant verification level across the fifty loops. Half verify...
- **Claim:** Half of studied loops employ deterministic verification levels
  - Source: Dominant verification level across the fifty loops. Half verify... | Download Scientific Diagram - ResearchGate (`6265eaf4-5685-45be-afb2-3fb9022c8fe5`)
  - Context: Half verify-deterministically-level
- **Claim:** Agent termination replaces step-by-step prompting, allowing autonomous loop control without continuous user guidance
  - Source: (PDF) Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - ResearchGate (`efe213fe-275c-407a-b23b-c7ea3b118e97`)
  - Context: Engineering the Loops that Replace Step-by-Step Prompting
- **Claim:** Loop specifications define both execution behavior and termination conditions within the same structure
  - Source: A Deterministic Control Plane for LLM Coding Agents | Request PDF - ResearchGate (`240a4b3f-fb62-4ae0-81ca-26b6a40f0cde`)
  - Context: A Deterministic Control Plane for LLM Coding Agents

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `590ac9fd-01f0-4b85-97ff-7d49bd5ed78d`
(cluster `researchgate-agent-stop`). No claims are made
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

- NotebookLM notebook [Deep Research Prompts, Methods, Examples](https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
