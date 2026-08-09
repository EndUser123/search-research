---
title: "Self-Feedback Iterative Refinement"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Self-feedback iterative refinement is a prompting technique where a language model generates an initial output, evaluates that output against specified criteria, and then iteratively revises the output based on its own critique. This approach enables a single LLM to improve its responses without req
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook c12e5224-58b7-4b6d-a448-0b94631727e0" (Iterative AI Refinement and Multi-Agent Debate Frameworks, synced 2026-07-28)
  - "Self-Refine: Iterative Refinement with Self-Feedback" (https://selfrefine.info/, transcript synced 2026-07-28)
  - "LLM Temperature Settings: A Complete Guide for Developers - Tetrate" (https://tetrate.io/learn/ai/llm-temperature-guide, transcript synced 2026-07-28)
  - "NeurIPS Poster Self-Refine: Iterative Refinement with Self-Feedback" (https://neurips.cc/virtual/2023/poster/71632, transcript synced 2026-07-28)
  - "A prompt to avoid ChatGPT simply agreeing with everything you say - Reddit" (https://www.reddit.com/r/ChatGPT/comments/1ijr08f/a_prompt_to_avoid_chatgpt_simply_agreeing_with/, transcript synced 2026-07-28)
  - "Claude Code CLI: The Complete Guide - Blake Crosley" (https://blakecrosley.com/guides/claude-code, transcript synced 2026-07-28)
  - "Psychological Agency : Theory, Practice, and Culture" (https://library.uc.edu.kh/userfiles/pdf/8.Psychological%20agency.pdf, transcript synced 2026-07-28)
  - "NeurIPS Poster Multi-Agent Debate for LLM Judges with Adaptive Stability Detection" (https://neurips.cc/virtual/2025/poster/117644, transcript synced 2026-07-28)
  - "Advanced Prompting Techniques Guide - Instructor" (https://python.useinstructor.com/prompting/, transcript synced 2026-07-28)
  - "“I Felt Bad After We Ignored Her”: Understanding How Interface-Driven Social Prominence Shapes Group Discussions with GenAI - arXiv" (https://arxiv.org/html/2602.14407v1, transcript synced 2026-07-28)
  - "Introduction to Self-Criticism Prompting Techniques for LLMs" (https://learnprompting.org/docs/advanced/self_criticism/introduction, transcript synced 2026-07-28)
  - "Advanced Prompting Techniques for AI SEO - Dejan.ai" (https://dejan.ai/blog/advanced-prompting-techniques/, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: self-feedback-iterative-refinement
    - level: notebook
      id: c12e5224-58b7-4b6d-a448-0b94631727e0
      title: Iterative AI Refinement and Multi-Agent Debate Frameworks
      url: https://notebooklm.google.com/notebook/c12e5224-58b7-4b6d-a448-0b94631727e0
    - level: cluster
      id: 3
      name: https-self-github
    - level: source_url
      url: https://selfrefine.info/
      title: Self-Refine: Iterative Refinement with Self-Feedback
    - level: source_url
      url: https://tetrate.io/learn/ai/llm-temperature-guide
      title: LLM Temperature Settings: A Complete Guide for Developers - Tetrate
    - level: source_url
      url: https://neurips.cc/virtual/2023/poster/71632
      title: NeurIPS Poster Self-Refine: Iterative Refinement with Self-Feedback
    - level: source_url
      url: https://www.reddit.com/r/ChatGPT/comments/1ijr08f/a_prompt_to_avoid_chatgpt_simply_agreeing_with/
      title: A prompt to avoid ChatGPT simply agreeing with everything you say - Reddit
    - level: source_url
      url: https://blakecrosley.com/guides/claude-code
      title: Claude Code CLI: The Complete Guide - Blake Crosley
    - level: source_url
      url: https://library.uc.edu.kh/userfiles/pdf/8.Psychological%20agency.pdf
      title: Psychological Agency : Theory, Practice, and Culture
    - level: source_url
      url: https://neurips.cc/virtual/2025/poster/117644
      title: NeurIPS Poster Multi-Agent Debate for LLM Judges with Adaptive Stability Detection
    - level: source_url
      url: https://python.useinstructor.com/prompting/
      title: Advanced Prompting Techniques Guide - Instructor
    - level: source_url
      url: https://arxiv.org/html/2602.14407v1
      title: “I Felt Bad After We Ignored Her”: Understanding How Interface-Driven Social Prominence Shapes Group Discussions with GenAI - arXiv
    - level: source_url
      url: https://learnprompting.org/docs/advanced/self_criticism/introduction
      title: Introduction to Self-Criticism Prompting Techniques for LLMs
    - level: source_url
      url: https://dejan.ai/blog/advanced-prompting-techniques/
      title: Advanced Prompting Techniques for AI SEO - Dejan.ai
relations:
  - target: wiki/concepts/multi-agent-debate.md
    type: related
  - target: wiki/concepts/chain-of-thought-prompting.md
    type: related
  - target: wiki/concepts/role-based-prompting.md
    type: related
---

# Self-Feedback Iterative Refinement

## Decision context

**Definition:** Self-feedback iterative refinement is a prompting technique where a language model generates an initial output, evaluates that output against specified criteria, and then iteratively revises the output based on its own critique. This approach enables a single LLM to improve its responses without requiring external judges or additional training.

Synthesized from **11 contributing transcripts** in NotebookLM notebook *Iterative AI Refinement and Multi-Agent Debate Frameworks*, clustered into the "https-self-github" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The process follows a generate-evaluate-refine loop: the model produces an initial response, generates critique feedback identifying weaknesses, and then produces a revised version addressing those weaknesses
- Critique generation can be guided by specifying evaluation dimensions such as accuracy, coherence, or stylistic quality
- The technique allows a model to act as both generator and critic, distributing reasoning capacity across multiple passes
- Temperature settings during the refinement passes can influence how creatively the model addresses critique versus how faithfully it follows suggested corrections
- Complementary prompting approaches include assigning the model an adversarial role to provide stronger counterpoints and explicitly instructing the model not to simply affirm prior statements
- Role-based prompting can simulate a skeptical reviewer perspective during the critique phase

## Related concepts

- multi-agent-debate — Multi-Agent Debate
- chain-of-thought-prompting — Chain-of-Thought Prompting
- role-based-prompting — Role-Based Prompting

## Citations (from contributing transcripts)

- **Claim:** Self-Refine uses a generate-evaluate-refine approach where the model generates output, critiques it, and revises based on the critique
  - Source: Self-Refine: Iterative Refinement with Self-Feedback (`001706b8-725b-4d44-89e7-cf3daf75ff65`)
  - Context: Self-Refine is [an iterative refinement method]
- **Claim:** A Reddit prompt instructs ChatGPT to provide counterpoints, test reasoning, and analyze assumptions rather than simply agreeing
  - Source: A prompt to avoid ChatGPT simply agreeing with everything you say - Reddit (`559d9f44-1e24-4c07-9e7c-84106cfb5b80`)
  - Context: do not simply affirm my statements or assume my conclusions are correct. Your goal is to be an intellectual sparring partner
- **Claim:** Role-based prompting techniques assign the model a specific perspective during critique generation
  - Source: Advanced Prompting Techniques Guide - Instructor (`af3eb1c4-57a9-4328-aa1b-da52664a3a67`)
  - Context: Assign a Role
- **Claim:** Temperature settings influence the randomness and creativity of model outputs during iterative refinement
  - Source: LLM Temperature Settings: A Complete Guide for Developers - Tetrate (`220b0db3-a0ea-4fa5-a6fa-b95611c3f923`)
  - Context: LLM Temperature Settings: A Complete Guide for Developers
- **Claim:** Self-criticism prompting techniques enable models to evaluate and improve their own outputs
  - Source: Introduction to Self-Criticism Prompting Techniques for LLMs (`f95650b7-e300-48df-9d0e-da7322516500`)
  - Context: Introduction to Self-Criticism Prompting Techniques for LLMs

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `c12e5224-58b7-4b6d-a448-0b94631727e0`
(cluster `https-self-github`). No claims are made
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

- NotebookLM notebook [Iterative AI Refinement and Multi-Agent Debate Frameworks](https://notebooklm.google.com/notebook/c12e5224-58b7-4b6d-a448-0b94631727e0)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
