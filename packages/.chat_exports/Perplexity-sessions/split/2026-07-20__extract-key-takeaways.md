---
title: "Extract key takeaways"
date: "2026-07-20"
mode: "COPILOT"
uuid: "8c67ddbf-fc1f-4c8d-b28c-df1a2330d835"
entry_count: 2
---

## Human

Extract key takeaways

## Assistant

Hormozi’s method is: stop ad‑hoc prompting and instead build a simple “AI asset” system with three folders—business context, data, and prompts—and treat learning AI as a top business priority.[1]

## Core system: three folders

- Business context  
Create a **Business** Context folder containing a single markdown file that explains who you are, what you sell, who you sell to, your offer, how you think, brand voice, business model, goals/constraints, positioning/differentiation, and rules/principles/preferences. Claude (or any LLM) is then always grounded in your specific business instead of fabricating from generic internet data, which moves outputs from “mediocre” to 2–3× better.[1]

- Data (your own work)  
Create a Data folder per workflow (e.g., newsletters, Instagram reels, YouTube scripts, sales calls) and fill each with your past work in simple markdown files. For newsletters, Hormozi uses ~120 past emails so Claude can learn his tone, cadence, formatting, and subtle patterns that humans don’t even consciously notice, which yields outputs that feel like his own writing, often ~10× better than generic AI content.[1]

- Prompts (as reusable skills)  
Create a Prompts folder per workflow containing long, highly detailed prompts stored as `.md` files. These prompts follow a structure of raw input, task, rules, and desired output, and function like reusable “Claude skills” you can call on-demand rather than rewriting or copy‑pasting prompts every time.[1]

## How the structure actually works

- Shared business context, per‑workflow data/prompts  
The Business Context folder is shared across everything in the same business, while Data and Prompts are specific to each workflow (newsletters vs reels vs sales, etc.). In any Claude/Code session, you plug in the context folder plus the relevant workflow’s data and prompt, so the system stays modular and reusable.[1]

- Result: AI indistinguishable from your own writing  
When Claude has business context, rich data, and a strong prompt, it produces newsletters that are effectively indistinguishable from Hormozi’s handwritten work; in the example, all three sample newsletters shown were actually written by AI. The big idea is: “Don’t sound like generic AI, sound like this”—your own historic work.[1]

## How to implement on your desktop

- Set up the AI Assets root  
Create an **AI** Assets folder on your desktop. Inside it, create three subfolders: Business Context, Data, and Prompts.[1]

- Fill each folder  
In Business Context, answer Hormozi’s 12 questions in a simple `.md` file. In Data, pull in all past work for the chosen workflow (e.g., all newsletters or all Instagram scripts) so the model can index and reference them. In Prompts, use Hormozi’s style of long, specific prompts as inspiration to craft and save your own per‑workflow prompts.[1]

- Start with one workflow, then expand  
Begin with a single high‑leverage workflow (like newsletters) and get the system working end‑to‑end before you expand to other areas like short‑form content, YouTube videos, sales calls, DMs, or conversion funnels.[1]

## Strategic takeaway: AI mastery as top priority

- Learning AI is the top business skill  
Hormozi argues that learning how to use AI should be your number one priority as a business owner, and in fact your number one, two, three, and ten priorities. He spends half of a 14‑hour workday—about 7 hours—studying and implementing AI in his business.[1]

- Why he treats it this way  
He believes AI will never again be worse than it is right now and that the cost of intelligence and labor will effectively go to zero. Businesses that master AI first will deliver the same or better results with fewer people, lower costs, and far higher profit, gaining a durable competitive advantage.[1]

Assumption: I’ve treated the transcript at face value and focused on operational points you can implement directly; confidence high that this reflects the actual content of the video.[1]

What’s the first workflow in your business (or projects) where you’d want to set up this three‑folder system—newsletters, code generation, content, or something else?

## Human

Can the video content be turned into a resuable skill that can be used across a range of use cases?

## Assistant

Yes—this video basically *is* a reusable skill pattern, and you can generalize it across many workflows, not just “write me a newsletter.”[1]

## What the underlying skill actually is

At its core, the video is teaching a reusable **AI operating pattern**:

- Always provide persistent business context so the model knows who you are, what you do, for whom, and with what constraints.[1]
- Attach rich, domain‑specific data (your historic artifacts) so the model learns your tone, formats, and patterns by example.[1]
- Use long, explicit prompts that define input, task, rules, and output format, saved as callable “skills” rather than ad‑hoc instructions.[1]

That pattern doesn’t care whether the workflow is newsletters, code generation, sales calls, or YouTube scripts; it’s a general design for how to talk to AI with assets instead of one‑off prompts.[1]

## How to turn it into a reusable skill

You can distill the video into a single, reusable skill spec along these lines:

1. **Business context asset**  
   - Maintain a `business_context.md` answering Hormozi’s questions: who you are, what you sell, who you sell to, offer, brand voice, model, goals/constraints, positioning/differentiators, rules/principles/preferences.[1]
   - This file is injected into *every* AI workflow so you never have to re‑explain your environment.[1]

2. **Workflow data asset**  
   - For each workflow (e.g., “long‑form thought leadership,” “internal tooling code,” “short‑form video”), maintain a `data/WORKFLOW_NAME/` folder containing your past examples in markdown.[1]
   - The canonical instruction becomes: “Don’t sound like generic AI, **sound like this**, using the attached examples as style and pattern references.”[1]

3. **Workflow prompt asset (skill definition)**  
   - For each workflow, maintain a `prompts/WORKFLOW_NAME.md` file that encodes:  
     - Raw input format (what you will paste or describe)  
     - Task (what the model must do)  
     - Rules (constraints, style requirements, do/don’t)  
     - Output (structure, sections, formatting, quality bar)[1]
   - That file is the “skill” you call, the same way Hormozi saves his newsletter prompt as an MD file and reuses it.[1]

As long as your tools (Claude Code, other LLM IDEs, custom routers) can consistently load these three assets per workflow, you have a generalized skill that is reusable anywhere you need high‑quality, non‑generic output.

## Range of use cases this can cover

This skill structure can be applied across a wide range of use cases by swapping the workflow folder:

- Content: newsletters, blogs, LinkedIn posts, short‑form scripts, YouTube outlines.[1]
- Sales: call scripts, objection handling templates, DM responses, follow‑up sequences.[1]
- Product: feature specs, change logs, release notes, internal docs.[1]
- Code: code review style, internal library usage patterns, CLI conventions—using your past repos and PRs as the “data.” (Not in the video, but follows the same pattern.)  
- Operations: SOPs, onboarding emails, reporting templates, meeting summaries.[1]

The *skill* is: “Given shared business context + workflow‑specific examples + a high‑specificity prompt, generate outputs indistinguishable from my own work, at 10× speed.” That is broadly reusable.[1]

## Where the video’s pattern has limits

FACT (from transcript): The video shows the pattern for content workflows (newsletters, reels, YouTube) and mentions sales calls and DMs, all based on static markdown assets + a good prompt.[1]

CONSENSUS (my reading, high confidence):  
- This pattern works best for generative, pattern‑based tasks (writing, scripting, templated interactions) where “tone and style” matter.[1]
- It is less complete for tasks that need live tools (APIs, DB queries) or tight feedback loops, because it doesn’t cover function/tool calls, environment state, or evaluation.

SPECULATION (medium confidence):  
- You can still adapt it to code and research workflows by treating the “data folder” as your prior work + reference docs and the “prompt folder” as a library of task‑specific instructions (e.g., “refactor per house style,” “write tests using our patterns”).  
- For multi‑agent systems or routers, this pattern becomes the standard “skill artifact” each agent loads: context + corpus + task spec.

## One concrete next step

If you want to actually operationalize this as a reusable skill beyond this video:

1. Pick one workflow you care about most (e.g., “long‑form technical explainer posts” or “CLI tool code stubs”).  
2. Create:
   - `ai_assets/business_context.md` (12 questions answered).  
   - `ai_assets/data/WORKFLOW_NAME/` with 20–50 of your best, representative artifacts.  
   - `ai_assets/prompts/WORKFLOW_NAME.md` as a detailed skill definition following the four‑part structure from the video.[1]
3. Wire your main LLM entry point (Claude Code, routing layer, or PowerShell helper script) to always load these three assets when you choose that workflow, so the “skill” is a menu item, not a one‑off prompt.

If you tell me your highest‑leverage workflow (e.g., “code generation for internal tools” vs “YouTube scripts”), I can draft a concrete `WORKFLOW_NAME.md` skill file in your preferred language (TypeScript or Python) style.  
