---
title: "Friction in Computing Systems"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, windows]
summary: >
  A pattern observed across modern computing environments where improvements in hardware and software do not translate into proportional gains in user experience or system efficiency, resulting in unnecessary resource consumption and cognitive load on users.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook fff42c44-d4ba-474a-93f7-7384bd536a1b" (WL: Health & Weight Loss, synced 2026-07-27)
  - "NotebookLM source 19411285-2b20-491a-803b-f6493f68800f" (You NEED to STOP Using Windows 11 Right Now, synced 2026-07-27)
  - "NotebookLM source 8964526e-ba1a-47b5-ae2a-8256218cb2cd" (The Invisible Bloat Ruining Our Computers, synced 2026-07-27)
  - "NotebookLM source 8d5fc915-bac7-4f6f-92d8-c39a045effec" (8 Common MISTAKES That Make Your Windows PC Slower!, synced 2026-07-27)
  - "NotebookLM source 96b5d092-3eda-4bba-94c5-e12009a2d346" (Why Productivity Apps FAIL ADHD (and How I Fixed It), synced 2026-07-27)
  - "NotebookLM source b4f06f6b-da3a-4de9-a3e0-3fee437f18b1" (The Key to Exercise When You Have ADHD, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: friction-in-computing-systems
    - level: notebook
      id: fff42c44-d4ba-474a-93f7-7384bd536a1b
      title: WL: Health & Weight Loss
      url: https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b
    - level: cluster
      id: 9
      name: windows-adhd-have
relations:
  - target: wiki/concepts/software-efficiency-optimization.md
    type: related
  - target: wiki/concepts/operating-system-independence.md
    type: related
  - target: wiki/concepts/thermal-management-in-computing-hardware.md
    type: related
---

# Friction in Computing Systems

## Decision context

**Definition:** A pattern observed across modern computing environments where improvements in hardware and software do not translate into proportional gains in user experience or system efficiency, resulting in unnecessary resource consumption and cognitive load on users.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *WL: Health & Weight Loss*, clustered into the "windows-adhd-have" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Software complexity has grown disproportionately to hardware improvements, with modern applications consuming hundreds of megabytes of RAM for basic operations that previously required kilobytes.
- The Gendarmerie Nationale replaced Windows across 103,000 machines (97% of its desktop fleet) with a custom Linux build, reducing costs by 40% while maintaining operational capability.
- Physical maintenance of computing hardware affects performance; dust accumulation causing inadequate cooling leads to thermal throttling that degrades system speed.
- Productivity applications designed for individuals with ADHD often fail at a single friction point—a microdecision step involving folder navigation, file creation, or template access—that disrupts task initiation.
- The time required to complete small microdecisions in software interfaces can cause thought processes to shift for users with ADHD, preventing consistent engagement with productivity tools.

## Verifiable values

| Name | Value |
|---|---|
| Desktop fleet migrated to Linux | `97% (103,000 machines)` |
| Cost reduction from migration | `40%` |
| Dust cleaning interval (dusty environment) | `3-6 months` |
| Dust cleaning interval (normal environment) | `6-12 months` |
| Original Windows Task Manager size | `85 kilobytes` |
| Modern Task Manager memory footprint | `tens of megabytes` |

## Related concepts

- software-efficiency-optimization — Software Efficiency Optimization
- operating-system-independence — Operating System Independence
- thermal-management-in-computing-hardware — Thermal Management in Computing Hardware
- accessibility-in-productivity-software — Accessibility in Productivity Software

## Citations (from contributing transcripts)

- **Claim:** France's Gendarmerie Nationale migrated 97% of its desktop fleet (103,000 machines) to a custom Linux build, achieving 40% cost reduction
  - Source: You NEED to STOP Using Windows 11 Right Now (`19411285-2b20-491a-803b-f6493f68800f`)
  - Context: Today, more than 103,000 of those machines now run a custom Linux build. That's 97% of the entire desktop fleet. Costs dropped by 40%
- **Claim:** Modern applications consume significantly more resources than legacy software for equivalent functionality
  - Source: The Invisible Bloat Ruining Our Computers (`8964526e-ba1a-47b5-ae2a-8256218cb2cd`)
  - Context: the original Windows Task Manager was 85 kilobytes the whole program today's version loads tens of megabytes into RAM just to show you a list of running processes
- **Claim:** Dust accumulation leading to inadequate cooling causes thermal throttling that degrades PC performance
  - Source: 8 Common MISTAKES That Make Your Windows PC Slower! (`8d5fc915-bac7-4f6f-92d8-c39a045effec`)
  - Context: this will result in your PC not being properly cooled overheating can cause thermal throttling making your PC slower
- **Claim:** Productivity apps fail for ADHD users at a single friction point requiring microdecisions during task initiation
  - Source: Why Productivity Apps FAIL ADHD (and How I Fixed It) (`96b5d092-3eda-4bba-94c5-e12009a2d346`)
  - Context: they all fail in exactly the same spot and that's just the one maintenance step that all of these have is that one minute where you have to find the folder or like make a new file
- **Claim:** The time required for microdecisions in software interfaces can cause thought processes to shift for users with ADHD
  - Source: Why Productivity Apps FAIL ADHD (and How I Fixed It) (`96b5d092-3eda-4bba-94c5-e12009a2d346`)
  - Context: the time it takes you to make those two microdecisions your thoughts like kind of gone it's somewhere else

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `fff42c44-d4ba-474a-93f7-7384bd536a1b`
(cluster `windows-adhd-have`). No claims are made
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

- NotebookLM notebook [WL: Health & Weight Loss](https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
