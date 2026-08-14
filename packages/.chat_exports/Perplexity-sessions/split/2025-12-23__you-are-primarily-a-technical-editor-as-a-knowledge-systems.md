---
title: "You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insi"
date: "2025-12-23"
mode: "COPILOT"
uuid: "f75bd879-343f-4423-92c8-817c8b81b606"
entry_count: 1
---

## Human

You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insights.

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and repeated points. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works.

Produce a rewritten version of the thread that:

Keeps every distinct insight, workflow, or configuration detail.

Preserves all mentions of tools, agents, actions, and integrations (e.g., GitHub actions, zen-mcp, codex, Copilot, MCP, hooks, CLAUDE.md, pre-commit, etc.) and what people actually do with them.

Removes repeated restatements of the same idea unless they add a new nuance.

After the rewrite, add a section called “Operational patterns and setups” where you explicitly list:

Multi-model review flows (e.g., “I use zen-mcp and have all 3 review the code, then have Claude consolidate and apply fixes”).

Automation patterns (GitHub auto-review actions, agents/skills triggered at the end of each dev phase, hooks that detect ‘fallback’/‘backwards compatible’ code, pre-commit checks referencing code-patterns.md).

Guardrail artifacts (CLAUDE.md, .claude/development-principles.md, code-patterns.md) and the key rules they encode.

Add a final section “Practical recommendations” that distills the most useful advice into concrete steps another developer could implement (e.g., “Set up zen-mcp with three reviewers and a Claude consolidation agent”, “Add a hook to block ‘fallback’ code paths”, “Configure codex or similar as a PR reviewer only, not auto-fixer”).

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow or recommendation from the conversation.

## Assistant

Most commenters agree that **structure matters more than XML itself**, and they describe several concrete ways they use XML, Markdown, and templated prompts to make Claude and related tools behave more reliably and stay “on rails.”[1]

***

## Core ideas about structure

- XML/JSON/Markdown prompting helps mainly because it forces the human to break messy concepts into small, clearly labeled units, which in turn improves LLM understanding and intent alignment.[1]
- Several people report that once they learned to encode their thoughts in a more structured form, they could drop XML and get similar or better results with highly structured prose or Markdown, which allows more nuance while retaining clarity.[1]
- Multiple users observe that **any** clear, consistent structure (XML, Markdown, JSON, YAML, even capitalizing key phrases) beats an unstructured wall of text; the precise syntax matters less than the presence of recognizable patterns and relationships.[1]

***

## What Anthropic actually says

- Anthropic’s own prompt-engineering docs explicitly recommend using XML tags with Claude to delineate sections like instructions, background, constraints, and output format for complex prompts.[1]
- One commenter links directly to Anthropic’s “use XML tags” documentation page and notes this is guidance **specific to Claude**, i.e., “Anthropic explicitly say XML is better for Claude specifically.”[1]
- Other commenters point out that some of this guidance is dated (“from a time long long ago (last year)”) and that newer models can parse poorly written or loosely structured text just fine, so XML can become more of a context/token tax than a necessity.[1]

***

## Opinions on XML vs Markdown/JSON/YAML

- Some users feel XML prompting used to provide noticeably better responses but now mostly wastes tokens compared to concise Markdown, especially with larger, newer models like Opus 4.5.[1]
- One person emphasizes token efficiency, claiming XML is more token-efficient than JSON and that YAML is more efficient than both, referencing the popularity of formats like TOON, though this is contested in replies.[1]
- A counter-argument stresses that XML is inherently more verbose than Markdown/JSON; more characters and longer tokens make it strictly less token-efficient up front, so its only plausible “efficiency” gains would come from dramatically improved accuracy or reduced iterations, which are not consistently observed for general tasks.[1]
- Several commenters converge on the idea that XML is particularly useful where rigid structure and automated parsing matter (e.g., coding agents, data pipelines), but unnecessary overhead for simple, human-facing content or exploratory chat.[1]

***

## Agent- and tooling-related workflows

- A commenter says they have “been telling people to write agents in xml for ages,” reporting that XML-defined agents are “so much better at staying on rails,” highlighting its usefulness for constrained, agent-like behaviors rather than ad-hoc chat.[1]
- Another user notes that coding agents especially benefit from structured output because they often “fail at reading outputs,” and giving them XML (or similar structure) reduces ambiguity and parsing failures, even for smaller models or weaker stacks (e.g., Ollama).[1]
- One user mentions using Haiku to fill an `agent.md` file (templated for different use cases), reviewing it, and then sending Claude “off with one big task,” effectively using a smaller, cheaper model to generate structured agent specs and a larger model to execute the complex work.[1]

***

## Systems for meta‑prompting and project development

- A creator describes an entire project development system built around XML meta-prompting, context engineering, and spec-driven development: **Get Shit Done (GSD)**, available on GitHub at `glittercowboy/get-shit-done`.[1]
- GSD builds on an earlier “create-prompt” slash command (from `glittercowboy/taches-cc-resources`) that converts a user’s desired goal into an XML-formatted prompt, including verification steps and “definition of done” criteria, turning goals into structured, testable specifications.[1]
- The same approach is presented in a meta-prompting video: using XML-formatted meta-prompts as **reusable templates** that encode goals, constraints, verification steps, and success criteria, which can be composed into larger project systems (as GSD does).[1]

***

## Structured thinking tools and data systems

- One commenter built a tool (xtended.ai) that uses relational tables to mirror the user’s mental model and combines this with AI access, batch queries, SQL-like aggregations, and third-party API integrations.[1]
- With that system, they ask questions like: “Which outreach variant has the best response rate?”, “Show tasks blocked by incomplete dependencies,” or “Pageviews this week vs last?” (pulling from PostHog), and the AI helps define schemas and converts unstructured data into the chosen structure on the fly.[1]
- This pattern shifts the “hard part” from ad-hoc reasoning to designing schemas and structured artifacts once, then letting the AI continually populate and query those structures.[1]

***

## Concrete prompt/formatting practices

- Common patterns for structured prompting include:  
  - Explicit sections for **task**, **background**, **constraints**, and **output formatting**, often wrapped in XML tags or clearly marked Markdown headings.[1]
  - Using Markdown as the primary format because it is faster to write and easier to read while still giving the model the structural signals it needs.[1]
  - Asking an LLM to summarize a conversation into a compact, structured format (often Markdown by default) and then passing that to another LLM as a “handoff” artifact.[1]
- Some users stress “dog-fooding” prompts: repeatedly using, testing, and refining the same instruction templates in real work to make them “field-hardened” rather than relying on theoretical best practices.[1]
- A commenter notes that even minimal structure (meaningful spacing, bullet lists, or simple “do X, then Y” instructions) plus clear hints (“md artifact”, “rewrite in a more professional form”) often suffices, and that **clarity of intent** matters more than elaborate formats.[1]

***

## Diverging views and nuances

- Several people argue that the **perceived** magic of XML is mostly cognitive: forcing the human to think clearly, decompose tasks, and write better instructions, which would also improve results in Markdown or well-structured prose.[1]
- Others argue that XML tagging itself is beneficial for some models and stacks because it aligns with how tools and code consume output (e.g., strict XML/JSON parsing, programmatic reference to specific tags), reducing downstream brittleness.[1]
- There is disagreement about how much Anthropic specifically “trained on” XML, but one commenter mentions Anthropic’s own system prompts showing structured usage and another responds that structured training data is still likely dwarfed by unstructured text, so any gains are mostly about the model’s pattern recognition rather than special-case XML understanding.[1]

***

## Operational patterns and setups

**Multi-model and staged workflows**

- Use a smaller model (e.g., Haiku) to fill in an `agent.md` or similar spec/agent file for a particular use case, review and tweak that document, then hand it off to a larger Claude model as a single, comprehensive task description.[1]
- Summarize long or messy sessions into structured Markdown using one LLM, then feed that summary as context to another LLM to continue work, effectively using one model as a compression/handoff layer.[1]
- Combine meta-prompting templates with a project system (e.g., GSD) so each individual LLM call is driven by an XML/Markdown meta-prompt that fits into an overarching project graph, rather than isolated, one-off prompts.[1]

**Automation patterns**

- Use XML or other structured formats when outputs will be parsed or consumed by coding agents, scripts, or tools, reducing failure modes where agents mis-read or skip critical information.[1]
- In systems like GSD, generate XML meta-prompts automatically (via slash commands or helper scripts) that encode project goals, specs, verification steps, and “definition of done,” then reuse them across multiple tasks and sessions.[1]
- In data-centric tools (like xtended.ai), define schemas as a first-class artifact and let the AI continuously ingest unstructured inputs into those schemas, then query via higher-level questions with SQL-like semantics and API-backed metrics.[1]

**Guardrail artifacts and rules**

- `agent.md` (or similar `*.md` spec files) are used as **agent definition documents**, holding role, capabilities, constraints, and sometimes example behaviors; they are authored or co-authored by models like Haiku and then handed to larger models for execution.[1]
- XML meta-prompts in GSD and related resources (e.g., the “create-prompt” slash command in `taches-cc-resources`) encode:  
  - Clear task goals and scope  
  - Context and dependencies  
  - Verification steps / tests  
  - Definition of done criteria to determine when work is complete.[1]
- Relational schemas and tables in tools like xtended.ai act as guardrails by constraining how data is ingested and queried, turning fuzzy questions into queries over known fields and relations.[1]

***

## Practical recommendations

**Make structure a default**

- Always break prompts into clear sections (task, background, constraints, output format), using whichever format you can write and read fastest (Markdown is a strong default); reserve XML for when strict parsing or downstream automation benefits from tags.[1]
- Before adopting any new format (XML/JSON/YAML/TOON), test it on **your** workflows and measure whether it reduces iterations or errors; treat perceived improvements as hypotheses to validate, not facts.[1]

**Use meta-prompts and specs**

- Create a reusable meta-prompt template (XML or Markdown) that captures goal, context, constraints, verification steps, and definition of done; use it consistently across tasks.[1]
- Adopt a project system like **GSD** or build your own: store meta-prompts and specs (e.g., `agent.md` files) in a repo, version them, and drive individual LLM calls from those artifacts instead of ad-hoc chat.[1]

**Leverage multi-model flows**

- Use a cheaper/smaller model (e.g., Haiku) to draft structured specs (agent definitions, task plans, prompt templates), then review and refine them manually before handing them to a stronger model for execution.[1]
- Periodically summarize long sessions into compact Markdown or XML “state” documents and pass those as canonical context for future calls or other models.[1]

**Align structure with tooling**

- Whenever an output will be parsed by a script, agent, or pipeline, enforce a strict, machine-friendly format (XML/JSON) and embed clear tags/fields to minimize parsing failures.[1]
- For human-facing or exploratory tasks, favor concise Markdown sections and lists over verbose XML to save tokens and cognitive load while retaining enough structure for the model.[1]

**Continuously harden your prompts**

- “Dog-food” your templates: run them in real projects, collect failure cases, and refine the structure and wording based on those examples until they are field-hardened.[1]
- Keep guardrail artifacts (agent specs, meta-prompts, schemas) under version control so improved patterns are preserved and reused instead of rediscovered in each new session.[1]
