---
title: "I'm working on a textual python app.  I'm not really happy with the design the LLM is coming up with.  Are there agentic"
date: "2026-07-24"
mode: "COPILOT"
uuid: "8097a5d3-60aa-4cef-8336-c4e68e7a43b2"
entry_count: 1
---

## Human

I'm working on a textual python app.  I'm not really happy with the design the LLM is coming up with.  Are there agentic skills or repos that would help the LLM be better at design?

## Assistant

Yes — but the best help is usually **Textual-specific design guidance plus curated example repos**, not a generic “UI design” skill. For a Textual Python app, you’ll get better results by giving the LLM strong layout heuristics from Textual’s own docs and a small set of high-quality Textual repos to imitate, because Textual’s design constraints are terminal-first and differ from web UI patterns.[1][2]

## What helps most

Textual’s own layout guidance recommends starting with a sketch, designing from the outside in, docking fixed elements like headers and footers, using `fr` units for flexible regions, and relying on containers for scrollable areas. Those rules are directly useful as “agentic design constraints” because they turn vague UI generation into a repeatable composition process the LLM can follow.[1]

A curated Textual project list is also useful because it exposes the model to real patterns for file browsers, markdown viewers, SQL tools, log viewers, and widget libraries built with Textual rather than generic dashboard clichés. The community list includes a broad set of third-party Textual apps and widgets such as Harlequin, Toolong, Frogmouth, Kupo, Select, Datepicker, and Terminal, which are good reference points for concrete interaction patterns.[2]

## Best repos to feed it

I’d prioritize these sources, in this order:

- [Textual repo](https://github.com/textualize/textual) for canonical architecture, examples, and framework-native patterns.[2]
- [Textual tutorial](https://textual.textualize.io/tutorial/) for official example flows and docs-linked sample apps.[3]
- [Design a Layout](https://textual.textualize.io/how-to/design-a-layout/) for layout heuristics you can convert into prompt rules.[1]
- [Widget gallery](https://textual.textualize.io/widget_gallery/) for concrete widget vocabulary and composition ideas during design.[4]
- [awesome-textualize-projects](https://github.com/oleksis/awesome-textualize-projects) for real-world community apps and widget libraries to imitate selectively.[5][2]

## What to tell the LLM

A generic web-design skill can improve taste around hierarchy, spacing, and avoiding template-like layouts, but it will also push the model toward web tropes that don’t map cleanly to terminal interfaces. The safer approach is to create a small “Textual design skill” or rules file that forces the model to reason in terminal layout primitives first: panes, docking, scroll regions, focus flow, keyboard-first interactions, width constraints, and sparse color usage.[1]

Use constraints like these:

- Start with a terminal sketch before writing code.[1]
- Build outside-in: shell, header, footer, sidebar, then content.[1]
- Distinguish fixed vs scrollable regions explicitly.[1]
- Prefer 1–2 primary panes, not busy multi-panel dashboards unless the task truly needs them.[1]
- Reuse existing Textual widgets before inventing custom ones. The official framework and gallery already provide a strong widget vocabulary.[4][2]
- Borrow patterns from real Textual apps, not from random web dashboards.[2]

## A practical setup

For your workflow, I’d create a repo-local design pack with three artifacts:

- `AGENTS.md` or `DESIGN_RULES.md`: “Textual-first” rules distilled from the official layout doc.[1]
- `references/`: screenshots or links to 3–5 Textual apps from the awesome list that match your app type.[2]
- `design-brief.md`: one-page spec covering app purpose, key workflows, pane structure, keyboard actions, and what must stay visible vs scroll. This aligns with Textual’s sketch-first guidance.[1]

FACT: the strongest evidence-backed resources here are the official Textual repo/docs and the curated awesome list.[3][2][1]

CONSENSUS: LLMs design better when you narrow the pattern space with framework-native examples and explicit constraints rather than asking for “better design” in the abstract. This is also consistent with broader agent-engineering advice emphasizing strong rules, modular context, and explicit planning.[6]

SPECULATION, medium confidence: if your current model keeps producing weak layouts, the main issue is probably not missing “design talent” but insufficiently opinionated inputs. A small Textual-specific skill file will likely outperform a large generic design repo for this use case.[2][1]

## Recommended next step

Build a **Textual UI design skill** from the official layout article plus 3–5 reference apps from the awesome list, and make your coding agent read that before generating screens. If you want, paste your current app structure and I’ll draft a compact `AGENTS.md` / design-rules file tailored to Textual.
