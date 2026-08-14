---
title: "Extract key takeaways"
date: "2026-02-14"
mode: "COPILOT"
uuid: "a9d662e5-0abc-4b53-aba3-71163fae5351"
entry_count: 3
---

## Human

Extract key takeaways

## Assistant

Answer skipped.

## Human

[https://www.youtube.com/watch?v=lZrhWGc2xJk&t=4s](https://www.youtube.com/watch?v=lZrhWGc2xJk&t=4s)

## Assistant

This link is a 9‑minute YouTube tutorial titled “I Used Graph To Automate Prompt Knowledge and It Blew My Mind” by Gao Dalie, showing how to use an evolutionary graph optimization prompt (EGO‑Prompt) pipeline to build a graph‑based agent chatbot.[1, {ts:0}]

The video explains how traditional chain‑of‑thought and basic RAG are limited because they rely on static or unstructured knowledge, then introduces semantic causal graphs where nodes are domain concepts (like “diabetes” or “low blood sugar”) and edges are natural‑language causal relations between them.[1, {ts:64}][1, {ts:277}]

It walks through the EGO‑Prompt idea from Johns Hopkins: start with an expert‑made but imperfect causal graph, use one model as an “analyst” to select relevant causal chains for each case, then a “decision‑maker” model to answer using those targeted chains plus the original case.[1, {ts:187}][1, {ts:139}]

When the decision‑maker’s prediction is wrong, a stronger “mentor” model generates an improvement report, and the system automatically edits the graph and prompts (adding/deleting nodes, modifying descriptions) in a loop so the graph and prompts evolve over time.[1, {ts:237}][1, {ts:224}]

Later, the author skims the actual code: setting up OpenAI engines, loading train/val/test datasets (e.g., a pandemic dataset), wrapping prompts, initializing causal and non‑causal models plus optimizers, then running multi‑threaded prompt‑optimization experiments where multiple workers try different random restarts and keep the best F1 score.[1, {ts:444}][1, {ts:331}][1, {ts:380}]

## Human

are there repos for this?

## Assistant

Yes. There is an official implementation plus related code you can dig into.[1][2]

### Core EGO‑Prompt repo

- EGO‑Prompt (Evolutionary Graph Optimization for Prompting), from the Johns Hopkins authors:  
  `https://github.com/miemieyanga/EGO-Prompt`[1]
  This repo implements the semantic causal graph construction, guidance generation, and the evolutionary optimization loop described in the paper, including scripts for the public health and transportation tasks.[2][1]

### Paper and context

- Arxiv / PDF for the method:  
  `https://arxiv.org/html/2510.21148v1` and `https://arxiv.org/pdf/2510.21148v1.pdf`[3][2]
  These describe the algorithm, datasets, and experimental setup that the repo code follows.

### Related prompt‑optimization code

- Microsoft EvoPrompt (not graph‑based but closely related prompt‑evo baseline):  
  `https://github.com/microsoft/EvoPrompt`[4]

If you want, I can outline how to adapt the EGO‑Prompt repo to your own domain (e.g., building SCGs from your internal knowledge base and swapping in OpenRouter/Anthropic endpoints).
