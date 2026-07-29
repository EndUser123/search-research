---
title: "Skill per Hour"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, https]
summary: >
  A metric for evaluating educational content creators based on the practical skill development a viewer gains per unit of time invested, prioritizing depth of understanding and hands-on applicability over audience size.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 1e46600b-fabe-4cd5-aeed-b5884401a257" (WebSync: Watch Later - YouTube, synced 2026-07-27)
  - "NotebookLM source 06d11a1d-698f-4000-b7c9-cc3e9cca201b" (2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source 36cf86fb-1f01-4807-88c0-004a22a2c215" (2026-07-25 https://www.youtube.com/watch?v=fSm7KXPJ3Gk&list=WL&index=1367&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source 3cd157d2-db8b-493f-95e5-6a71265a0edb" (2026-07-25 https://www.youtube.com/watch?v=9Y3yaoi9rUQ&list=WL&index=1452&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source 8d7c078e-6db6-4eea-8ba8-39d97a7dc729" (2026-07-25 https://www.youtube.com/watch?v=60grBIXuhjo&list=WL&index=1404&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source b3bf380d-26b4-4584-a64d-770bdfa0c313" (2026-07-25 https://www.youtube.com/watch?v=ShWMQurrbGI&list=WL&index=1502&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source be6f6078-916d-483e-b71f-2ab9d8c74044" (2026-07-25 https://www.youtube.com/watch?v=ge9h2ZbsuIk&list=WL&index=1488&pp=iAQBsAgC, synced 2026-07-27)
  - "NotebookLM source e6b6ff83-249d-44c4-9905-3ca6591b738e" (2026-07-25 https://www.youtube.com/watch?v=yzd6R7UrscQ&list=WL&index=1443&pp=iAQBsAgC, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: skill-per-hour
    - level: notebook
      id: 1e46600b-fabe-4cd5-aeed-b5884401a257
      title: WebSync: Watch Later - YouTube
      url: https://notebooklm.google.com/notebook/1e46600b-fabe-4cd5-aeed-b5884401a257
    - level: cluster
      id: 8
      name: https-youtube-watch
relations:
  - target: wiki/concepts/depth-of-understanding.md
    type: related
  - target: wiki/concepts/hands-on-learning.md
    type: related
  - target: wiki/concepts/educational-content-quality.md
    type: related
---

# Skill per Hour

## Decision context

**Definition:** A metric for evaluating educational content creators based on the practical skill development a viewer gains per unit of time invested, prioritizing depth of understanding and hands-on applicability over audience size.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *WebSync: Watch Later - YouTube*, clustered into the "https-youtube-watch" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Channels are scored on two axes: depth (whether viewers understand what happens under the hood) and hands-on capability (whether viewers can build something immediately after watching)
- The rarest and most valuable channels score highly on both axes simultaneously
- Most AI learning channels primarily sell hype or ephemeral news rather than lasting knowledge
- The channel Hyper Automation Labs is identified as the creator's own channel and ranked tenth
- Channels are positioned as unsuitable for certain audiences; what suits a total beginner differs from what suits someone shipping models
- Traditional subscriber count is rejected as a meaningful ranking criterion

## Verifiable values

| Name | Value |
|---|---|
| ranking_position_own_channel | `10 (tenth)` |

## Related concepts

- [[depth-of-understanding]] — Depth of Understanding
- [[hands-on-learning]] — Hands-On Learning
- [[educational-content-quality]] — Educational Content Quality

## Citations (from contributing transcripts)

- **Claim:** A metric called skill per hour measures how much viewers can genuinely do after watching a channel
  - Source: 2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC (`06d11a1d-698f-4000-b7c9-cc3e9cca201b`)
  - Context: i went through more than a hundred of them and ranked the 10 that actually make you better not by subscriber count by something I call skill per hour how much can you genuinely do after watching
- **Claim:** Channels are evaluated on depth (understanding under the hood) and hands-on (ability to build)
  - Source: 2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC (`06d11a1d-698f-4000-b7c9-cc3e9cca201b`)
  - Context: i scored every channel on two things depth do you actually understand what's happening under the hood and hands-on can you go build the thing today the best channels are strong on one axis the rare ones are strong on both
- **Claim:** Most AI channels sell hype or forgettable news rather than lasting skill
  - Source: 2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC (`06d11a1d-698f-4000-b7c9-cc3e9cca201b`)
  - Context: there are thousands of channels promising to teach you AI almost all of them are selling you hype or news you'll forget by Friday
- **Claim:** The creator's own channel is ranked tenth with disclosure of bias
  - Source: 2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC (`06d11a1d-698f-4000-b7c9-cc3e9cca201b`)
  - Context: number 10 and the only one I'm biased about is this channel Hyper Automation Labs it's the newco
- **Claim:** Different channels suit different skill levels; beginners and model shippers need different resources
  - Source: 2026-07-25 https://www.youtube.com/watch?v=j9_kOtXMhQ0&list=WL&index=1399&pp=iAQBsAgC (`06d11a1d-698f-4000-b7c9-cc3e9cca201b`)
  - Context: i also stayed honest about who each channel is wrong for because the right channel for a total beginner is the wrong one for someone shipping models

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `1e46600b-fabe-4cd5-aeed-b5884401a257`
(cluster `https-youtube-watch`). No claims are made
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

- NotebookLM notebook [WebSync: Watch Later - YouTube](https://notebooklm.google.com/notebook/1e46600b-fabe-4cd5-aeed-b5884401a257)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
