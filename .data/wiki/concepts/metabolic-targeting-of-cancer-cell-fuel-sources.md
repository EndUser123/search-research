---
title: "Metabolic Targeting of Cancer Cell Fuel Sources"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, cancer]
summary: >
  A therapeutic approach wherein various compounds are investigated for their ability to disrupt the metabolic pathways cancer cells rely upon for energy and survival, specifically targeting glucose and glutamine as primary fuel sources.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook b8a105cf-ada2-4343-88ce-184b1e7c9387" (WL: Health (ADHD/Sleep/Cancer), synced 2026-07-28)
  - "NotebookLM source 06a8c5eb-1e82-46e2-aef8-8d685aeeedec" (How Curcumin KILLS Cancer Cells: Blocks Cancer's BACKUP Fuel, synced 2026-07-28)
  - "NotebookLM source 0fc575d3-189f-4864-b96f-abc30feaf561" (I've Never Seen Anything Like This in Cancer Research, synced 2026-07-28)
  - "NotebookLM source 89afe8d9-20cf-4502-9612-a196de91c792" (Ivermectin and Mebendazole in cancer patients: usage patterns, adherence, and safety, synced 2026-07-28)
  - "NotebookLM source ab0d19d0-f3d0-473a-935a-64da42aa556d" (How Fenbendazole KILLS Cancer Cells: Choking Off Glucose, synced 2026-07-28)
  - "NotebookLM source ad345c91-41b5-4ffb-8f37-2fb4cb641de6" (Mebendazole and Cancer: How This Parasite Drug May Fight Tumors, synced 2026-07-28)
  - "NotebookLM source b349b346-49f6-43d4-83e9-c16b252faa99" (How Melatonin KILLS Cancer Cells: Glucose, Glutamine & Warburg Effect, synced 2026-07-28)
  - "NotebookLM source b34e5d9b-7a60-4710-a3ab-227734b5599b" (How Curcumin KILLS Cancer Cells: Starving Cancer of Sugar, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: metabolic-targeting-of-cancer-cell-fuel-sources
    - level: notebook
      id: b8a105cf-ada2-4343-88ce-184b1e7c9387
      title: WL: Health (ADHD/Sleep/Cancer)
      url: https://notebooklm.google.com/notebook/b8a105cf-ada2-4343-88ce-184b1e7c9387
    - level: cluster
      id: 5
      name: cancer-cells-kills
relations:
  - target: wiki/concepts/warburg-effect.md
    type: related
  - target: wiki/concepts/glutamine-addiction-in-cancer.md
    type: related
  - target: wiki/concepts/drug-repurposing-for-oncology.md
    type: related
---

# Metabolic Targeting of Cancer Cell Fuel Sources

## Decision context

**Definition:** A therapeutic approach wherein various compounds are investigated for their ability to disrupt the metabolic pathways cancer cells rely upon for energy and survival, specifically targeting glucose and glutamine as primary fuel sources.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *WL: Health (ADHD/Sleep/Cancer)*, clustered into the "cancer-cells-kills" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Cancer cells consume glucose at elevated rates—reportedly 10 to 30-fold higher than normal cell counterparts—making glucose metabolism a prominent target for therapeutic intervention
- Curcumin has been shown to interfere with multiple stages of glucose metabolism including uptake, glycolysis, lactate production, and HIF1-alpha signaling, as well as growth pathways such as PI3K-AKT-mTOR
- Curcumin suppresses glutamine transport, glutamine utilization, and glutamine-driven growth signaling while simultaneously weakening cancer antioxidant defenses (glutathione and thioredoxin systems)
- Melatonin has been studied for its capacity to influence mitochondrial function, inflammation, hypoxia signaling, and key metabolic pathways including HIF1-alpha, c-Myc, and PDK that enable cancer cell adaptation
- Mebendazole and fenbendazole belong to the benzimidazole drug family, members of which have been studied for their ability to disrupt cancer cell structure, metabolism, and survival
- Pre-clinical studies indicate mebendazole interacts with several systems cancer cells depend on for growth, invasion, blood supply formation, and resistance to cell death
- A 2024 study titled 'From Deworming to Cancer Therapy' examined benzimidazole effects at the cancer cell metabolic level
- Cancer cells possess glutamine as a critical backup fuel source when glucose becomes insufficient, with some researchers proposing glutamine may be equally or more important than glucose for driving cancer growth, survival, invasion, and metastasis
- Disrupting both glucose and glutamine metabolism may make cancer cells significantly more vulnerable to oxidative stress
- A retrospective analysis examined usage patterns, adherence, and safety of ivermectin and mebendazole in nearly 200 cancer patients with established diagnoses

## Verifiable values

| Name | Value |
|---|---|
| glucose consumption differential | `10 to 30-fold higher in cancer cells vs normal counterparts` |
| RAS mutation prevalence | `approximately 20% of all cancers` |
| KRAS-driven pancreatic cancers | `approximately 9 in 10` |
| five-year survival rate for pancreatic cancer | `fewer than 1 in 5 patients` |

## Related concepts

- warburg-effect — Warburg Effect
- glutamine-addiction-in-cancer — Glutamine Addiction in Cancer
- drug-repurposing-for-oncology — Drug Repurposing for Oncology
- mitochondrial-metabolic-disease-model-of-cancer — Mitochondrial Metabolic Disease Model of Cancer

## Citations (from contributing transcripts)

- **Claim:** Cancer cells consume glucose at 10 to 30-fold higher rates than normal cells
  - Source: How Curcumin KILLS Cancer Cells: Starving Cancer of Sugar (`b34e5d9b-7a60-4710-a3ab-227734b5599b`)
  - Context: cancer cells consume enormous amounts of glucose on the order of 10 to 30fold or 10 to 30x compared to their normal cell counterparts
- **Claim:** Curcumin interferes with glucose uptake, glycolysis, lactate production, HIF1-alpha signaling, and growth pathways including PI3K-AKT-mTOR
  - Source: How Curcumin KILLS Cancer Cells: Starving Cancer of Sugar (`b34e5d9b-7a60-4710-a3ab-227734b5599b`)
  - Context: curcumin can interfere with glucose uptake glycolysis lactate production HIF1 alpha signaling and even major growth pathways like the PI3K AKT mTor pathway
- **Claim:** Curcumin suppresses glutamine transport, utilization, and growth signaling while weakening glutathione and thioredoxin antioxidant defenses
  - Source: How Curcumin KILLS Cancer Cells: Blocks Cancer's BACKUP Fuel (`06a8c5eb-1e82-46e2-aef8-8d685aeeedec`)
  - Context: curcumin can suppress glutamine transport glutamine utilization glutamine driven growth signaling and even weaken two of the cancer's most important antioxidant defense systems glutathione and thorio redoxin
- **Claim:** Melatonin influences mitochondrial function, inflammation, hypoxia signaling, and metabolic pathways including HIF1-alpha, c-Myc, and PDK
  - Source: How Melatonin KILLS Cancer Cells: Glucose, Glutamine & Warburg Effect (`b349b346-49f6-43d4-83e9-c16b252faa99`)
  - Context: melatonin is much more interesting than that it has been studied for its ability to influence mitochondrial function inflammation hypoxia signaling and some of the major metabolic pathways cancer cells use to survive
- **Claim:** Benzimidazole family members have been studied for their ability to disrupt cancer cell structure, metabolism, and survival
  - Source: How Fenbendazole KILLS Cancer Cells: Choking Off Glucose (`ab0d19d0-f3d0-473a-935a-64da42aa556d`)
  - Context: several members of this family have been studied for their ability to disrupt cancer cell structure metabolism and survival
- **Claim:** Pre-clinical studies show mebendazole interacts with multiple systems cancer cells depend on for growth, invasion, blood supply, and cell death resistance
  - Source: Mebendazole and Cancer: How This Parasite Drug May Fight Tumors (`ad345c91-41b5-4ffb-8f37-2fb4cb641de6`)
  - Context: In pre-clinical studies membenazol appears to interact with several systems cancer cells depend on to grow invade build blood supply and resist cell death
- **Claim:** Glutamine may be equally or more important than glucose for driving cancer growth, survival, invasion, and metastasis
  - Source: How Curcumin KILLS Cancer Cells: Blocks Cancer's BACKUP Fuel (`06a8c5eb-1e82-46e2-aef8-8d685aeeedec`)
  - Context: some researchers believe glutamine may be just as important or even more important than glucose for driving cancer growth survival invasion and metastases
- **Claim:** A 2024 study titled 'From Deworming to Cancer Therapy' examined benzimidazole effects on cancer cell metabolism
  - Source: How Fenbendazole KILLS Cancer Cells: Choking Off Glucose (`ab0d19d0-f3d0-473a-935a-64da42aa556d`)
  - Context: The first paper we're going to look at was published in October of 2024 and it was titled from deworming to cancer therapy benzim
- **Claim:** A retrospective study examined ivermectin and mebendazole usage patterns, adherence, and safety in nearly 200 cancer patients
  - Source: Ivermectin and Mebendazole in cancer patients: usage patterns, adherence, and safety (`89afe8d9-20cf-4502-9612-a196de91c792`)
  - Context: they took 200 almost 200 cancer patients all of all of whom had established cancer already

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `b8a105cf-ada2-4343-88ce-184b1e7c9387`
(cluster `cancer-cells-kills`). No claims are made
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

- NotebookLM notebook [WL: Health (ADHD/Sleep/Cancer)](https://notebooklm.google.com/notebook/b8a105cf-ada2-4343-88ce-184b1e7c9387)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
