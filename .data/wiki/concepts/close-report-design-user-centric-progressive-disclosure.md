---
title: "Close report design: user-centric progressive disclosure over gate walls"
created: 2026-07-26
source: session-2026-07-26 (/www research on close report design + progressive disclosure)
sources:
  - https://www.uxtigers.com/post/progressive-disclosure
  - https://ardalis.com/optimizing-ai-agents-with-progressive-disclosure/
  - https://www.mindstudio.ai/blog/progressive-disclosure-ai-agent-skill-design
  - https://thedecisionlab.com/reference-guide/psychology/cognitive-load-theory
  - https://www.lauragast.com/cognitive-load-theory/
  - https://fraukeseewald.com/design-for-trust/
  - https://www.glitter.io/blog/knowledge-sharing/lessons-learned-retrospective
  - https://medium.com/@todd.dsm/why-progressive-disclosure-works-for-ai-agents-a-theory-of-motivated-retrieval-665a9d1ea23a
  - https://aipositive.substack.com/p/progressive-disclosure-matters
  - https://blog.logrocket.com/product-management/lessons-learned-project-management-template/
tags: [close, report-design, progressive-disclosure, cognitive-load, user-experience, report-psychology]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 3
summary: >
  Session close reports should lead with the answer (safe to close? what
  shipped? what's next?) using progressive disclosure, not with a wall of
  gate statuses. Research from progressive disclosure, cognitive load theory,
  and narrative psychology converges on the same conclusion: outcome-first,
  detail-on-request. The current /close format is scanner-centric (14 gates
  first, answer buried). Users want value-centric (what shipped, what
  learned, what's next, then details if requested).
---

# Close report design: user-centric progressive disclosure over gate walls

## Decision context

**Why this research was needed:** the /close report emitted a 14-gate wall with 8 ⚠️ flags, but only 1 was genuinely actionable (the rest were false positives, concurrent-session noise, or format mismatches). The user asked: "is this what people who want to make sure all value is optimally captured and lessons noticed want to see?"

## The load-bearing finding

**[HIGH confidence — 5+ independent sources agree across progressive disclosure, cognitive load theory, and narrative psychology]**

Session close reports should be structured as **outcome-first, detail-on-request** — the opposite of the current format (gates-first, outcome-buried).

### Three convergent research streams

**1. Progressive disclosure** (UX Tigers 2026, Ardalis 2026, MindStudio 2026, Towards AI 2026, Substack 2026)

Level 1 should be "the outcome plus any decision-critical action awaiting approval" (UX Tigers). For a close report, Level 1 = "Safe to close? What shipped? What's next?" The current format's Level 1 is a 14-row gate table — that's Level 3 detail.

The Coherence Cascade theory (Todd Thomas, Medium 2026) explains why: layered awareness creates coherence-seeking drives. Presenting the answer first triggers the user to seek detail on demand; presenting detail first forces the user to mentally construct the answer from fragments.

**2. Cognitive load theory** (Sweller via Decision Lab; LauraGast; Springer)

Extraneous load (poor information design) impairs comprehension. The 14-gate list with 8 ⚠️ flags creates extraneous load — the user must mentally triage each flag ("is this mine? is this real? is this actionable?"). Most aren't actionable. This is the definition of extraneous load: processing effort spent on formatting rather than content.

**3. Narrative psychology** (Bruner via LauraGast)

"Narratives are up to 22x more memorable than facts alone." The gate list is a fact dump. A 3-line narrative ("You shipped 9 items. Key lesson: default-selection bias is structural. Two evidence-gated items remain.") is more memorable and actionable than 14 gate rows.

**4. Trust design** (Frauke Seewald)

"Visual clarity builds trust by helping users feel smart and in control." The gate wall makes the user feel like they need to investigate 8 yellow flags — the opposite of control. A clear "safe to close: yes" with supporting detail builds trust.

**5. Lessons learned vs retrospectives** (Glitter.io 2026)

These are different documents serving different purposes. The close report tries to be all three (checklist + retrospective + lessons-learned). It should be **a close decision report** — "can I safely stop?" The AAR handles retrospectives; the wiki handles lessons learned.

## Recommended structure

### Layer 1 — The answer (always shown, ≤5 lines)

> Session shipped: N items across repos (key commits). Safe to close: **yes/no**. N items remain (evidence-gated/blocking). Action required: **none** / **list**.

### Layer 2 — Value captured (shown by default, collapsible)

- What shipped (commit list with one-line descriptions)
- Lessons captured (wiki concepts, AAR patterns, session-observation insights)
- Decisions made (with rationale pointers)

### Layer 3 — Gate details (on request or when blocking)

- The current 14-gate scanner output
- Only shown when: user asks, a gate genuinely blocks close, or all gates aren't pre-satisfied
- Per-session attribution (separate "my work" from "concurrent sessions")

## What the current format gets wrong

| Problem | Research basis | Fix |
|---|---|---|
| 8/14 gates ⚠️ but only 1 actionable | Cognitive load: extraneous load from false positives | Lead with answer, not gates |
| "1031 uncommitted files" alarm | Cognitive load: irrelevant information | Per-session attribution or suppress |
| ACCOUNTING + NEXT buried after gates | Progressive disclosure: outcome is Level 1 | Invert the order |
| No narrative — just statuses | Narrative psychology: 22x memorability | 2-3 sentences of narrative |
| Tries to be checklist + retrospective + lessons | Different documents, different audiences | Close report = decision only |

## When the full gate list IS appropriate

- Regulated environments where the audit trail must be visible
- When the user explicitly asks "show me everything"
- When a gate genuinely blocks close (then the detail is decision-critical)
- First-time users who haven't learned to trust the scanner

## Falsifier

This design is wrong if:
- Users consistently skip the Layer 1 answer and jump to gates (they don't trust the summary)
- The scanner produces false "safe to close: yes" when gates genuinely block (false negative)
- Users prefer the current format after seeing the alternative

## Sources

- [Progressive Disclosure: From Training Wheels to Week-Long AI Agents](https://www.uxtigers.com/post/progressive-disclosure) — UX Tigers, 2026
- [Optimizing AI Agents with Progressive Disclosure](https://ardalis.com/optimizing-ai-agents-with-progressive-disclosure/) — Ardalis (Steve Smith), 2026
- [Progressive Disclosure in AI Agent Skill Design](https://www.mindstudio.ai/blog/progressive-disclosure-ai-agent-skill-design) — MindStudio, 2026
- [The Coherence Cascade for AI](https://medium.com/@todd.dsm/why-progressive-disclosure-works-for-ai-agents-a-theory-of-motivated-retrieval-665a9d1ea23a) — Todd Thomas, Medium, 2026
- [Progressive Disclosure Matters: Applying 90s UX Wisdom to 2026 AI Agents](https://aipositive.substack.com/p/progressive-disclosure-matters) — AI Positive, Substack, 2026
- [Cognitive Load Theory](https://thedecisionlab.com/reference-guide/psychology/cognitive-load-theory) — The Decision Lab
- [Cognitive Load & Information Communication](https://www.lauragast.com/cognitive-load-theory/) — LauraGast (narrative 22x finding)
- [Design for Trust: Insights from Psychology on Credibility](https://fraukeseewald.com/design-for-trust/) — Frauke Seewald, 2025
- [Lessons Learned vs Retrospective: Complete Guide 2026](https://www.glitter.io/blog/knowledge-sharing/lessons-learned-retrospective) — Glitter.io
- [Lessons Learned in Project Management: Template and Guide](https://blog.logrocket.com/product-management/lessons-learned-project-management-template/) — LogRocket, 2023
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
