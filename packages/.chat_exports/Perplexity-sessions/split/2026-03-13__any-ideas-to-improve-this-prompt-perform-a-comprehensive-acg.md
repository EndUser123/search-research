---
title: "Any ideas to improve this prompt?
'Perform a comprehensive 🔍 ACG analysis of this material:

  **0. SOURCE ANALYSIS**"
date: "2026-03-13"
mode: "COPILOT"
uuid: "ae9121ad-1c38-47a0-95a4-57c55e782d06"
entry_count: 2
---

## Human

Any ideas to improve this prompt?
"Perform a comprehensive 🔍 ACG analysis of this material:

  **0. SOURCE ANALYSIS**
  First, review all sources to identify the main themes and topics present. What are
  the 2-3 most significant themes that emerge from these documents?

  **1. CONTRADICTION CHECK**
  Are there any contradictions or conflicting data points across my sources?

  **2. ANALYZE**
  For each major theme identified in Step 0, what are the key insights? Provide
  specific findings with citations.

  **3. CHALLENGE**
  A panel of experts is reviewing this analysis. What are the weakest assumptions
  across all themes? Which claims have the least supporting evidence?

  **4. GAP**
  What's missing from my sources that would make these analyses complete? List specific
   information gaps for each theme.

  **5. NEXT STEPS**
  Based on identified gaps, recommend: (a) what sources to upload next, or (b) which
  sources to verify/replace.

  For each section, provide specific, actionable findings with source citations.

  Example Output

  **0. SOURCE ANALYSIS**
  Based on 8 sources, I identify these themes:
  1. Competitive positioning (4 sources: competitor pages, market research)
  2. Pricing strategy (3 sources: market sizing, pricing benchmarks)
  3. User sentiment (1 source: beta survey data)

  **1. ANALYZE**
  [Proceeds with ACG for each theme...]"

## Assistant

Good — this prompt is already clear, structured, and well‑sequenced. It sets up a full “Analytical‑Challenge‑Gap” (ACG) loop. The main improvement opportunities are **precision**, **semantic clarity**, and **instructional robustness** — tightening the logic chain and reducing ambiguity about how each stage links to the next.  

Here’s a refined version with improvements:

***

> **Task:** Perform a comprehensive 🔍 **ACG Analysis** (Analyze → Challenge → Gap) of the provided materials, producing **evidence‑linked, expert‑level insights**.

> **General Rules**
> - Cite all claims explicitly (e.g., “(Src #3)” or “(Author 2025)”).
> - Note confidence levels (High / Medium / Low) where evidence is incomplete or inconsistent.
> - Be concise but specific: each bullet must convey a finding, not a summary phrase.
> - Where applicable, include both *factual evidence* and *interpretive reasoning*.

***

### **0. SOURCE SYNTHESIS**
- Review all inputs to extract **the 2–3 dominant recurring themes** (by frequency or importance).
- For each theme, list which sources contribute evidence.
- Note weakly supported or outlier topics that might not form a main theme.

### **1. CONTRADICTION & CONSISTENCY CHECK**
- Identify any **conflicting claims, data points, or definitions** across sources.
- Explain **which interpretation is more credible** and why (e.g., stronger evidence, newer data).

### **2. ANALYZE (Core Insight Extraction)**
- For each major theme:
  - Summarize key insights and supporting evidence.
  - Include specific data, quotes, or metrics where possible.
  - Note any underlying causal logic or trend identified.

### **3. CHALLENGE (Critical Testing)**
- As if reviewed by domain experts:
  - Point out **weak assumptions**, **overextended inferences**, or **bias risks**.
  - Highlight claims with **low evidential strength** or **out‑of‑scope extrapolation**.

### **4. GAP (Missing Evidence or Scope Limits)**
- For each theme, specify what **additional data or context** would make the analysis complete.
- Label gaps as *Empirical*, *Conceptual*, or *Comparative*.

### **5. NEXT STEPS**
- Recommend next actions:
  - (a) **New Sources to Add** — e.g., datasets, reports, expert analyses.  
  - (b) **Sources to Re‑verify or Replace** — due to inconsistency or bias.
- Prioritize by potential impact on overall confidence.

***

### Optional Enhancements You Can Add
- **Role framing:** “You are an expert research analyst preparing a synthesis for a cross‑disciplinary panel.”  
- **Output format control:** “Return results in Markdown with numbered subsections.”  
- **Compact mode switch:** Add `mode: "summary"` for shorter keyed outputs.  
- **Confidence metadata:** e.g., “(Confidence: 0.7 | Evidence: 3 sources | Bias risk: medium).”

***

Would you like me to make a **version optimized for LLM reasoning (prompted inside Claude or GPT tools)**, with tokens‑to‑structure efficiency and guardrails tuned for multi‑document synthesis?

## Human

yes please

## Assistant

Here’s a version tuned for LLMs doing multi‑doc synthesis in big contexts: minimal fluff, strong structure, and explicit reasoning hooks.

***

**SYSTEM INSTRUCTIONS (for the model)**  
You are an expert research analyst. Your job is to read multiple sources, extract themes, surface contradictions, challenge weak reasoning, and identify missing information. Your output must be concise, evidence‑linked, and structured.

Follow all instructions below exactly. Think step‑by‑step **internally**, but only output the requested sections.

***

### TASK

Perform a comprehensive 🔍 **ACG analysis** (Analyze → Challenge → Gap) of the provided materials.

Use this exact section structure:

1. SOURCE ANALYSIS  
2. CONTRADICTION CHECK  
3. ANALYZE (BY THEME)  
4. CHALLENGE  
5. GAP  
6. NEXT STEPS  

***

### GLOBAL RULES

- Treat each uploaded item as a **distinct source**.  
- When you reference a source, include an inline label (e.g., “(Src 3: survey)”).  
- Do not invent facts that are not in the sources. If something is unknown, say so explicitly.  
- Prefer **bullets with specific claims over vague summaries**.  
- When evidence is weak or conflicting, note **Confidence: High / Medium / Low**.

***

### 1. SOURCE ANALYSIS

Goal: map the terrain before reasoning.

- Briefly list all sources with a 1‑line description each (type, topic, timeframe if available).  
- Identify the **2–3 most important themes** that recur across sources.  
- For each theme, list which sources contribute (e.g., “Theme A: Src 1, 2, 5”).  
- Note any topics that appear only once (potential outliers or niche themes).

***

### 2. CONTRADICTION CHECK

Goal: enforce internal consistency.

- Identify **any conflicting claims or numbers** across sources for the same topic.  
- For each conflict:  
  - Describe the contradiction in 1–2 sentences.  
  - Briefly assess which source is more credible (e.g., recency, methodology, authority).  
  - Mark each conflict with **Confidence** in your judgment.

***

### 3. ANALYZE (BY THEME)

Goal: extract core insights per theme.

For each major theme from Step 1:

- Start with a 1‑sentence **theme summary**.  
- Then list **3–7 concrete insights** as bullets. Each bullet should:  
  - Make one specific claim.  
  - Include at least one source label.  
  - Include data points, examples, or user quotes where available.  
  - Optionally note **Confidence** if not obviously high.

Example bullet style:

- Pricing is positioned at the upper mid‑market tier compared to competitors, but without a clear value justification in user‑facing materials (Src 2: benchmark, Src 4: website, Confidence: Medium).

***

### 4. CHALLENGE

Goal: stress‑test the analysis as if by a critical expert panel.

- List the **weakest assumptions** you have made across all themes.  
- For each weak assumption:  
  - Explain why it might fail (missing data, sample bias, over‑generalization, time‑sensitivity, etc.).  
  - Point to the specific sources that make this assumption tempting but under‑supported.  
- Highlight any places where the analysis might be **over‑fitting to a small number of sources**.

***

### 5. GAP

Goal: make unknowns explicit.

For each major theme:

- List **specific missing information** that would materially improve the analysis.  
- Classify each gap as one of:  
  - Empirical (needs data, metrics, experiments)  
  - Conceptual (needs clearer definitions, frameworks, causal models)  
  - Comparative (needs competitor, benchmark, or historical comparison)  
- Phrase gaps as **questions you would ask** or **data you would request**.

Example:

- Empirical: We lack conversion‑rate data by segment after the latest pricing change; without this we cannot assess impact on high‑value cohorts.  

***

### 6. NEXT STEPS

Goal: turn gaps into an action plan.

Based on the gaps and contradictions:

- Recommend (a) **what sources to upload next**, with concrete examples (e.g., “recent NPS by segment, raw survey exports, 2024 competitor pricing pages”).  
- Recommend (b) **which existing sources to verify, update, or replace**, and why (e.g., “outdated by more than 18 months,” “small N user study,” “conflicts with newer market data”).  
- Order recommendations by **expected impact on decision quality**, from highest to lowest.

***

If anything in the materials is too ambiguous to classify, explicitly call it out under GAP rather than guessing.
