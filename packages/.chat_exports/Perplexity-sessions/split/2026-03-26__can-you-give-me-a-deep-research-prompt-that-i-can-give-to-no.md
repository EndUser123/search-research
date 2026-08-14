---
title: "Can you give me a deep research prompt that I can give to NotebookLM that will find Can you give me a deep research prom"
date: "2026-03-26"
mode: "COPILOT"
uuid: "53190c4a-3bc7-471a-b409-c420aa3b4ef9"
entry_count: 24
---

## Human

Can you give me a deep research prompt that I can give to NotebookLM that will find Can you give me a deep research prompt that I can give to NotebookLM that will find Ideas, code, prompts, repos, working examples, information that can be used to improve claude code skills.  It should include best practices, self-improvement, loops, whatever it is that people are thinking can help skills be better skills.  Prompt expansion, prompt rewriting. Don't limit yourself to what I just asked for. Be creative.

## Assistant

Here’s a compact, high‑signal research prompt you can drop into NotebookLM to surface deep, actionable material for improving Claude‑Code skills, including best practices, self‑improvement loops, and prompt engineering patterns:

***

> **Research Prompt for NotebookLM:**
> 
> You are a research assistant specializing in AI‑assisted software development and Claude‑Code skill mastery. Analyze all relevant information in the provided sources to answer the following questions thoroughly, with concrete, actionable guidance rather than vague principles.
> 
> ### 1. Core Skills and Best Practices
> - What are the key skills someone using Claude Code effectively should master (e.g., problem decomposition, test‑driven interaction, debugging workflows, refactoring, design‑before‑code)?
> - Identify documented best practices for:
>   - Using Claude Code inside VS Code (Windows / multi‑terminal environments).
>   - Structuring prompts so that Claude generates production‑grade, maintainable, and testable code.
>   - Avoiding over‑reliance on the model while still maximizing its usefulness.
> - Summarize patterns seen in engineers who “level up” their Claude‑Code skills over time (habits, workflows, feedback loops).
> 
> ### 2. Self‑Improvement and Feedback Loops
> - What self‑improvement mechanisms do experts propose for becoming better at working with Claude Code? Examples:
>   - Iterative refinement loops (prompt → Claude output → critique → rewrite prompt).
>   - Built‑in “training” or reflection workflows (e.g., self‑review checklists, code review automations, or post‑session reflections).
>   - Feedback‑rich environments (CI‑style validation, unit tests, linters, architecture reviews) that teach better prompts.
> - Extract concrete templates or routines someone can adopt: daily, per‑project, or per‑session.
> - How can someone measure progress in their Claude‑Code skills (metrics, heuristics, or checklists)?
> 
> ### 3. Prompt Engineering and Prompt Expansion
> - What are advanced prompt patterns that help Claude Code produce higher‑quality, more maintainable, and better‑aligned code (e.g., chain‑of‑thought, multi‑step decomposition, role‑stacking, constraints, style guides)?
> - How can prompts be systematically expanded or rewritten to:
>   - Increase specificity (e.g., clearer inputs, more precise constraints).
>   - Improve reasoning (e.g., step‑by‑step breakdown before code generation).
>   - Enhance structure (e.g., enforcing documentation, tests, or architecture patterns).
> - Provide concrete examples of:
>   - A “before” prompt that is weak or ambiguous.
>   - A “rewritten” prompt that is much more effective.
>   - A “prompt expansion” workflow someone can reuse to improve any prompt.
> 
> ### 4. Code Patterns, Repos, and Working Examples
> - What GitHub repos, blog posts, or public projects demonstrate excellent patterns for using Claude Code (or similar coding assistants) in production‑like workflows?
> - Identify:
>   - Specific repos or minimal projects that showcase:
>     - Multi‑file changes coordinated by an assistant.
>     - Architecture‑sensitive prompts (e.g., respecting monorepo or domain boundaries).
>     - Test‑first or “design‑then‑implement” workflows.
>   - Working examples or snippets that illustrate:
>     - How to refactor legacy code with Claude Code.
>     - How to generate and then validate code through tests or linters.
> - For each example, summarize the pattern, the context where it works well, and when it may backfire.
> 
> ### 5. Advanced Techniques and Anti‑Patterns
> - What advanced techniques do skilled users employ to “level up” their Claude‑Code skills?
>   - Hook‑based governance (e.g., pre‑commit hooks that validate or rewrite prompts).
>   - Multi‑agent or “team‑of‑agents” strategies (e.g., one agent designs, another critiques, another tests).
>   - Using Claude Code in combination with other tools (e.g., MCP servers, custom skills, semantic search, context compression).
> - What common anti‑patterns or “traps” do less‑skilled users fall into when using Claude Code (e.g., accepting code without review, brittle prompts, overfitting to local context)? For each trap, describe how to recognize it and how to escape it.
> 
> ### 6. Mental Models and Training Regimens
> - What mental models or frameworks help engineers think more effectively about how to use Claude Code (e.g., “assistant as copilot”, “assistant as junior dev”, “assistant as critic”)?
> - Does any existing literature propose structured “training regimens” or practice routines for improving AI‑assisted coding skills (e.g., daily coding challenges, deliberate practice prompts, or “red‑team / blue‑team” exercises using assistants)?
> - If such regimens exist, extract their key components and translate them into a practical training plan someone can follow for 2–4 weeks.
> 
> ### 7. Claude‑Specific Nuances
> - Are there documented differences in how Claude Code performs when:
>   - Used in long‑form projects vs. short snippets?
>   - Chained across multiple sessions vs. throwing everything into one prompt?
>   - Used with different file types or language ecosystems (e.g., Python vs. TypeScript vs. PowerShell)?
> - What are the known limitations or failure modes of Claude Code (e.g., context window mismanagement, hallucinated tests, edge‑case omissions), and how can users design their workflows to mitigate them?
> 
> ### Output Format
> - Organize the answer into clear sections that match the headings above (1–7).
> - For each section, prioritize:
>   - Concrete strategies and patterns.
>   - Short, reusable templates (e.g., prompt templates, checklists, or workflow steps).
>   - Examples drawn from real repos, public projects, or documented case studies.
> - If information is missing or conflicting, flag it explicitly and propose the most plausible next steps for the user to investigate further.

***

Would you like me to distill this into a shorter “mission‑statement” style prompt (e.g., 2–3 sentences) that you can reuse repeatedly in NotebookLM for different source sets?

## Human

Not yet, but the prompt as given is too long.  I do not know by how much it is too long.

## Assistant

NotebookLM’s custom “chat prompt” (persona / instructions) is currently capped at **10,000 characters**, up from the earlier 500‑character limit, which is roughly **1,500–2,000 words** depending on spacing.[1][2][3]

Your original prompt is comfortably under that ceiling in terms of raw length, but it’s verbose and heavily structured, so it may *feel* “too long” for NotebookLM’s UX or your own copy‑paste workflow.[3][1]

### A concise version (objective form)

Here’s a tighter, still deep version you can paste directly into NotebookLM (much shorter but preserves the intent):

> Act as a research assistant focused on improving Claude‑Code skills inside VS Code and multi‑terminal workflows. Use the provided sources to:
>
> 1. Extract concrete best practices for decomposing problems, structuring prompts, and validating Claude‑Code output (tests, linters, design‑before‑code, refactoring).
> 2. Identify self‑improvement loops (e.g., prompt → code → critique → rewrite prompt), feedback‑rich environments (CI‑style checks, review checklists), and measurable progress indicators.
> 3. Summarize advanced prompt‑engineering patterns (chain‑of‑thought, role‑stacking, constraints, style guides), and give short “before” and “after” prompt examples plus a reusable prompt‑expansion workflow.
> 4. List specific GitHub repos, blog posts, or public projects that showcase strong Claude‑Code (or similar) workflows: multi‑file changes, architecture‑sensitive prompts, test‑first or design‑then‑implement patterns.
> 5. Describe advanced techniques (hook‑based governance, multi‑agent setups, MCP‑style orchestration) and common anti‑patterns (accepting unreviewed code, brittle prompts, over‑reliance on local context) with concrete escape strategies.
> 6. Capture mental models (“assistant as copilot vs junior dev vs critic”) and any documented training regimens or practice routines (daily challenges, deliberate‑practice prompts, red‑team/blue‑team exercises).
> 7. Note Claude‑Code‑specific nuances (long‑vs‑short sessions, long‑vs‑short projects, multi‑session vs monolithic prompts, language‑specific behaviors) and how to design workflows that mitigate known failure modes.
>
> Organize findings under these 7 headings. Prioritize concrete strategies, short templates, and real‑world examples; flag missing or conflicting information explicitly.

This version is around **~1,000–1,200 characters** and should fit comfortably in NotebookLM’s 10,000‑character instruction box.[1][3]

If you tell me roughly how many characters or words you want as an upper bound (e.g., “under 500 characters” or “under 1,000”), I can shrink it further while keeping the same scope.

## Human

I couldn't tell you. I think you have better information than I do.  But it's working now.  I do have the pro account.

## Assistant

Good to hear it’s working with your Pro account—your current prompt is only about **1,751 characters** and ~200 words, so you’re nowhere near NotebookLM’s current 10,000‑character persona limit; you still have over **80% headroom**.[1][2][3]

### How to keep it safe but richer

Given that much room, you can actually **expand** your prompt a bit for more structure without risk, for example:

- Add a short “mission‑statement” line at the top (e.g., “You are a research assistant for Claude‑Code‑centric skill improvement.”).  
- Add a “preferred output format” line (e.g., “Use short bullet‑style lists, code‑block templates, and repo links.”).  
- Include a one‑liner about “flagging when sources conflict or evidence is weak.”  

If you want, I can give you a **refactored version** that:

- stays under ~3,000 characters (leaving ~70% headroom),  
- keeps all your requested topics (best practices, loops, prompt‑expansion, repos, self‑improvement),  
- and is optimized for high‑density, research‑oriented answers from NotebookLM.  

Would you like that tighter, expanded‑but‑safe variant now?

## Human

What other ideas do you think we can look at that may help improve skills? What about using CLIs in Claude Code?

## Assistant

Using Claude Code from the CLI is a massive skill‑multiplier and fits perfectly into what you’re already doing (multi‑terminal, worktrees, hook‑based governance).  Below are concrete angles you can add to your skill‑improvement research.[1][2][3]

***

### 1. CLI‑centric Claude Code workflows

Lean into the fact that `claude` is a full‑stack agentic CLI that can:

- Read and edit files, run tests, and manage git workflows directly from your terminal.[2][4][3]
- Manage sessions with commands like `claude -c` (continue last session), `claude -r <id>` (resume), and `claude -p "query"` (print‑mode query).[5][6][1]

You can research patterns like:

- Terminal‑first “agent‑in‑a‑tab” setups (dedicated tmux / Windows Terminal tab per project, always running `claude` in that dir).[6][3]
- Piping file input into Claude (`cat file.py | claude "explain this"`) and redirecting outputs to new files (`claude "generate tests" > tests.py`). [6][5]  

***

### 2. Hooks and automation (not just prompts)

Instead of relying on free‑text prompts, you can store systematic behaviors in hooks and commands:

- **Hooks**: JSON config that runs things like `prettier --write`, `tsc --noEmit`, or linters after any edit or file‑write.[7][3]
- **Slash commands**: Markdown files in `.claude/commands` that are short, reusable prompts tied to paths (e.g., `review` or `generate internal docs`).[8][7]

Research questions you can ask NotebookLM:

- “What are the highest‑leverage hook patterns for TS/Python/PowerShell in multi‑repo setups?”  
- “Show concrete hook configs that enforce style, type checks, and test runs automatically.”[3][7]

***

### 3. Plan mode and permission‑driven skills

Newer versions of Claude Code have a **plan mode** and permission tiers (normal / auto‑accept / plan) that let you:

- Explore the codebase (read‑only: `Read`, `Grep`, `Glob`, `WebSearch`) before committing to edits.[9][3]
- Write a plan in `.claude/plans/*.md`, review it, then kick off edits with explicit approval.[3][9]

You can research:

- When to force Plan Mode for feature design, refactors, or unknown codebases.[9][3]
- How to structure your own “plan template” prompts (e.g., architecture sketch → constraints → step‑by‑step plan).  

***

### 4. MCP‑style orchestration from CLI

Claude Code can talk to external MCP servers (tools, runtimes, linters, validators, etc.), which lets you:

- Build uniform “agent bundles” shared across projects (e.g., “test‑and‑lint‑bundle”, “doc‑bundle”, “security‑check bundle”).[6][3]
- Use `claude mcp add/remove` to wire services into your agentic workflow.[5][6]

Research angles:

- “Best practices for exposing internal tools as MCP servers usable from the Claude Code CLI.”  
- “How to share MCP‑based bundles across teams or repos without hard‑coding model‑specific logic.”[6][3]

***

### 5. CLI‑engageable “skill” packages

There are emerging CLI tools that standardize AI‑coding workflows across agents (incl. Claude‑like agents):

- Tools that inject 9 preconfigured skills (ask, write, execute, fix, bootstrap docs, quick‑implement, etc.) into agent configs.[10]
- CLI‑based managers for Claude Code commands and workflows (e.g., `claudecmd`‑style tools).[11]

You can ask NotebookLM to:

- Find such CLI tools, compare their skill sets, and show how you’d adapt them for your own Claude‑Code‑first workflow.[10][11]

***

### 6. Measurement and calibration with CLI

Because the CLI is scriptable, you can:

- Log session‑to‑file and diff outputs versus human‑written versions.  
- Wrap Claude‑driven refactorings in CI‑style scripts and measure “lines fixed vs. bugs introduced” or “PR‑time saved”.  

You can research:

- “How to track and measure Claude Code skill progression using CLI‑log‑based metrics.”  
- “How to design deliberate‑practice CLI‑driven coding challenges (e.g., ‘fix this bug solely in the terminal’).”[12][3]

***

If you want, I can give you a **one‑pager research prompt** you can feed NotebookLM specifically for “Claude Code CLI‑centric skills,” including hooks, plan mode, MCP, and measurement.

## Human

I think we can include agentic CLI tools in a prompt for Claude Code.  Deep research skills, MCPs, and prompts.  Let's explore that topic as well as other agentic CLIs you think might be useful.

Let's explore number two, hooks and automations, not just prompts.

If you think plan mode has a role in ideas to improve skills, by all means, let's explore it.

Let's explore how MCPs can be used to improve skills or improve outcomes.

Suggestion 5 looks good too.

Yes, please provide a research prompt I can give to Deep Research Notebook LM For all of the above.

## Assistant

Here’s a single research prompt you can paste into NotebookLM Pro that covers agentic CLIs, hooks/automation, plan mode, MCPs, and CLI‑packaged skills.

***

> **Deep Research Prompt for NotebookLM (Agentic CLIs + Claude Code Skills)**
> 
> You are a research assistant specializing in **agentic CLI coding tools**, **Claude Code**, and **MCP‑based skills**. Use all available sources to build a practical playbook for improving developer skills and outcomes in Claude Code and similar agentic CLIs.
> 
> Focus your research on the following:
> 
> 1. **Agentic CLI tools for coding**  
>    - Identify leading agentic CLI tools (e.g., Claude Code, Aider, OpenCode, Codex CLI, Gemini CLI, etc.) and summarize what they can *actually do* from the terminal: read/write files, run commands, plan, work across a full repo, integrate with git and CI, etc.[1][2][3][4]
>    - Extract patterns, not marketing: what workflows do expert users adopt (e.g., “agent in a dedicated terminal tab per repo”, “CLI‑driven refactors”, “natural‑language git operations”)?[2][4]
>    - For each major agentic CLI, note its strengths, limitations, and any ideas that could be ported back into Claude Code.
> 
> 2. **Hooks and automations (beyond free‑text prompts)**  
>    - Explain how Claude Code hooks work (PreToolUse, PostToolUse, on write, on MCP tool, etc.) and what kinds of shell commands, HTTP calls, or LLM prompts can be wired into them. Provide concrete hook JSON examples.[5][6]
>    - Find high‑leverage hook patterns for improving skills and outcomes, such as:  
>      - Auto‑running formatters, type‑checkers, and test commands after edits.  
>      - Logging or diff‑summarizing every Claude‑initiated change.  
>      - Blocking or flagging risky operations (e.g., certain MCP tools or write operations) behind extra checks.[6][5]
>    - Derive 3–5 reusable hook templates that a power user can drop into `.claude/config` to enforce better coding discipline and feedback loops.
> 
> 3. **Plan mode as a skill amplifier**  
>    - Describe in detail how Claude Code’s **plan mode** works (read‑only exploration, tools allowed, plan file generation, approval flow, context clearing, and handoff back to edit mode).[5]
>    - Identify when expert users recommend plan mode (new features, multi‑file refactors, unfamiliar codebases, tasks with multiple valid designs) and why it improves outcomes and reliability.[5]
>    - Propose concrete “plan templates” and usage habits that help humans *learn better architecture and decomposition skills* by reading and critiquing the generated plans before execution.
> 
> 4. **Using MCPs to improve skills and outcomes**  
>    - Summarize how MCP works conceptually: servers exposing **tools** (actions), **resources** (data/context), and **prompts** (parameterized templates), and how Claude/agentic CLIs connect to them.[7][8]
>    - Find examples where MCP servers are used to:  
>      - Wrap internal systems (GitHub, issue trackers, CI, monitoring, docs) into AI‑callable tools.  
>      - Encapsulate multi‑step SOPs as “skills” that sequence tools, checks, and summaries (e.g., a “weekly release helper,” or “PR triage helper”).[8]
>    - Extract design patterns for MCP servers that *teach* better habits: for example, tools that always cross‑check test status, security checks, or documentation completeness before taking actions.[7][8]
> 
> 5. **CLI‑packaged skills and agent bundles**  
>    - Investigate CLI‑level frameworks or tools that bundle multiple “skills” (ask, write, execute, fix, bootstrap docs, quick‑implement, etc.) and standardize workflows across different LLM backends.[4][9]
>    - Identify how such “skill bundles” or command sets are defined (config files, YAML/JSON, MCP prompts, slash commands), and how they can be adapted for Claude Code’s `.claude/commands` or MCP prompts.[9][10][5]
>    - Produce a small catalog of 8–12 high‑value skills/commands (e.g., “safety‑check change”, “architect‑then‑implement”, “test‑only refactor”, “doc‑driven design”) with:  
>      - A short description.  
>      - A suggested implementation mechanism (hook, command, MCP prompt, or external CLI wrapper).  
>      - How using that skill repeatedly would improve a developer’s own skills or reliability over time.
> 
> 6. **Comparing agentic CLIs for learning value**  
>    - Compare Claude Code to other agentic CLIs specifically from a *skill‑building* perspective (not just raw productivity): which tools encourage better planning, testing, and code review habits, and how?[3][1][2][4]
>    - Highlight unique ideas from other CLIs (e.g., architect modes, git‑native histories, repository graphs, multi‑model routing) that could inspire new Claude Code workflows or MCP skills.[3][4]
> 
> **Output format:**  
> - Organize your answer using the 6 numbered headings above.  
> - Under each heading, provide:  
>   - Concrete patterns, config snippets, and workflows (hooks, MCP examples, command definitions).  
>   - Short, reusable templates I can adapt (JSON/YAML fragments, CLI usage patterns, sample MCP tool definitions or prompts).  
>   - Brief notes on how each pattern improves *human* skills (planning, testing, architecture thinking, disciplined iteration), not just speed.  
> - Explicitly flag any gaps, conflicting advice, or open questions, and suggest promising directions for further experimentation.

***

If you want, the next step can be a second, smaller prompt that tells NotebookLM: “Now synthesize this into actual `.claude/config`, MCP server stubs, and command files for a specific repo (e.g., TS monorepo + Python services).”

## Human

Best prompts for deep research in agentic CLI tools

## Assistant

Here are reusable, high‑signal prompts you can give to a deep‑research system (NotebookLM, Perplexity Deep Research, etc.) specifically for **agentic CLI tools**.

***

## 1. Core landscape & comparison

> **Prompt: Agentic CLI Coding Tools – Landscape & Capabilities**  
> Analyze the provided sources to map out the ecosystem of agentic CLI coding tools (e.g., Claude Code, Aider, Codex CLI, Gemini CLI, Warp, etc.).  For each tool, identify:[1][2][3]
> 1) What it can actually do from the terminal (read/write files, run commands/tests, plan, repo‑wide edits, git and CI integration).  
> 2) Its configuration surfaces (config files, skills, commands, MCP/tools, context files like AGENTS.md).[4][2][1]
> 3) Strengths, limitations, and unique ideas that could be ported into other CLIs.  
> Organize the answer in a comparison table plus short tool‑specific notes focused on *practical workflows*, not marketing.

***

## 2. Configuration & skills (hooks, commands, context files)

> **Prompt: Configuration Mechanisms and “Skills” in Agentic CLIs**  
> From the sources, extract and compare the configuration mechanisms used by agentic coding tools (e.g., hooks, commands, skills, MCP prompts, context files like `.claude/**` or `AGENTS.md`).[5][6][1][4]
> 1) List each mechanism type (e.g., Hooks, Slash/CLI Commands, Skills, Context Files, MCP Tools/Resources/Prompts), define it, and show at least one concrete example snippet per type.[6][4]
> 2) Explain how each mechanism can encode *reusable skills* (e.g., “safe refactor”, “test‑before‑merge”, “security review”) rather than one‑off prompts.  
> 3) Synthesize 5–10 high‑value skills that could be implemented across multiple tools (Claude Code, Aider, Codex CLI, etc.), and describe *how* to implement each using their respective config surfaces.[2][3][1][4]

***

## 3. Hooks & automation for discipline (not just speed)

> **Prompt: Hooks and Automation Patterns that Improve Developer Discipline**  
> Focus on how hooks and automations in Claude Code and other agentic CLIs can enforce better engineering habits, not just speed.[4][5][6]
> 1) Describe the hook systems available (e.g., pre‑/post‑tool hooks, write hooks, test hooks) and show concrete JSON/YAML shell‑command examples.[5][6]
> 2) Identify recurring patterns like auto‑formatting, type‑checking, test‑running, security scanning, and change logging triggered by the agent’s actions.  
> 3) Propose a small library of hook templates (at least 5–7) that could be dropped into a serious TypeScript/Python monorepo to:  
>    – prevent untested changes,  
>    – surface diffs for review,  
>    – block risky operations,  
>    – and give fast feedback that “trains” the human user over time.[6][4]

***

## 4. Plan / approval modes as teaching tools

> **Prompt: Plan and Approval Modes as Architecture & Decomposition Tutors**  
> Study how agentic CLIs implement plan/approval modes (e.g., Claude Code plan mode, Codex CLI approval modes like Suggest/Auto Edit/Full Auto).[1][2][5]
> 1) Explain how these modes work: what tools they can use in “plan” vs “execute”, how plans are represented (files, messages), and how approval gates are implemented.[1][5]
> 2) Identify recommended use cases (multi‑file refactors, new features, unfamiliar repos) and why these modes reduce risk.  
> 3) Design 3–5 “plan templates” that turn plan/approval flows into *learning loops*—where the human critiques plans, adds constraints, and only then allows execution. Emphasize how this improves the user’s own architecture and decomposition skills over time.[4]

***

## 5. MCP and tool‑calling for better outcomes

> **Prompt: Using MCP / Tool‑Calling to Improve Reliability and Skills**  
> Examine how MCP‑style tool‑calling (tools, resources, prompts) and similar architectures are used with agentic CLIs.[7][8][9]
> 1) Summarize typical MCP server designs that expose internal systems (GitHub, CI, ticketing, documentation, monitoring) as tools/resources.[8][9]
> 2) Extract patterns where these tools improve answer quality and reliability (e.g., always checking tests, status dashboards, or docs before answering or editing).[9][7]
> 3) Propose a set of MCP “skill servers” whose main purpose is *teaching better practice*—for example,  
>     – a “testing coach” tool,  
>     – a “security checklist” tool,  
>     – a “docs coverage” tool,  
>   and describe the prompts & tool signatures needed for each.[8][9]

***

## 6. Methodology / meta‑prompt (how the system should research)

You can wrap any of the above with a short meta‑layer like this:

> **Prompt: Deep Research Methodology for Agentic CLI Tools**  
> For this topic, follow a literature‑review‑like approach:  
> 1) Map key systems, concepts, and configuration mechanisms.  
> 2) Extract recurring *patterns* and *anti‑patterns* across tools.[10][7][4]
> 3) For each pattern, provide at least one concrete example (config snippet, command, or workflow) and a short explanation of how it improves *human* skill (planning, testing, review, reliability) rather than just speed.  
> 4) End with a brief “gaps & open questions” section indicating where current tools/docs are weak or contradictory, and what experiments an advanced user should run next.[11][12]

If you tell me which agentic CLIs you care about most (e.g., Claude Code + Aider + Codex CLI), the next step can be: tailored prompts that force the researcher to produce **side‑by‑side config templates** for those specific tools.

## Human

Example system prompts from tallesborges agentic-system-prompts repo

## Assistant

The repository intentionally **removed** most full system‑prompt text; what you get now are **summaries and file structures**, plus per‑agent metadata you can mine and adapt.[1]

## Where the examples live

Under `agents/` you get one directory per agent, for example:  

- `agents/claude-code/` – Claude Code CLI  
- `agents/gemini-cli/` – Gemini CLI  
- `agents/cline/` – Cline VS Code extension  
- `agents/aider/` – Aider CLI  
- `agents/roo-code/` – Roo Code VS Code  
- `agents/zed/` – Zed editor agents  
- `agents/codex-rs/` – Codex CLI (Rust)[1]

Each agent directory is documented as containing:  

- **System prompts** – “Complete prompt templates with role definitions and instructions.”  
- **Tool documentation** – API specs for tools the agent exposes.  
- **Source attribution** – Original URLs and retrieval dates.  
- **Agent README** – Feature summary + links.[1]

However, the top‑level README notes it was **“updated to remove system prompt details”**, so some files have been trimmed or redacted for IP/safety.[1]

## What you can still use as “examples”

From the README and structure you can extract patterns, even without full text:  

- System prompts are split by **agent** and are intended to be “production‑grade” examples.[1]
- They consistently pair **role/instruction text** with **explicit tool definitions**, so tools are first‑class in the design.[1]
- The project’s **research value** section lists the core dimensions you can mirror in your own prompts:  
  - Prompt‑engineering patterns (how instructions are structured).  
  - Tool‑design patterns (how capabilities are exposed).  
  - Safety measures (constraints, defensive behaviors).  
  - UX patterns (how workflows and interaction modes are framed).[1]

## How to mine it effectively

For deep research or prompt‑mining you can:

- Drill into `agents/claude-code`, `agents/gemini-cli`, etc., and read whatever remains of `system-prompt.md`, `tools/*.md`, and the local README for each agent to see:  
  - How they name the agent role,  
  - How they describe responsibilities and boundaries,  
  - How tool capabilities are surfaced in the prompt text.[1]
- Use `CLAUDE.md` as a **guide to the file formats and templates** the repo expects; it explains how to add new agents and how system prompts and tools should be documented, which you can reuse for your own prompts.[1]

Because this repo is explicitly for **“research and educational purposes”**, it’s an ideal input to NotebookLM: point NotebookLM at the repo (or a local mirror) and ask it to synthesize cross‑agent patterns in **system‑prompt structure + tool specs** rather than copying any single prompt verbatim.[1]

## Human

Prompt templates for NotebookLM deep research on AI agents

## Assistant

Here are compact, reusable NotebookLM system prompts for **deep research on AI agents** (esp. agentic coding / CLI tools). Each is a template you can specialize.

***

## 1. Landscape of AI agents / agentic CLIs

> **Prompt: Map the Agentic Coding / CLI Ecosystem**  
> You are an AI research assistant. Using only the sources in this notebook, build a structured overview of **agentic AI coding tools and CLI agents** (e.g., Claude Code, Copilot‑style agents, Aider, Cline, Gemini CLI, Codex, etc.).[1][2][3][4]
> 1) Identify each distinct tool/agent and summarize its core capabilities (editing code, multi‑file reasoning, tool use, planning, CLI integration, repo‑level context).  
> 2) Describe the **configuration mechanisms** it supports (context files, skills, tools, sub‑agents, hooks, AGENTS.md, system prompts).[5][1]
> 3) Highlight unique **agentic patterns** (planning, tool‑use, multi‑agent collaboration, reflection loops) used by each tool.[6][7]
> Present:  
> – A table comparing tools by capabilities and configuration mechanisms.  
> – Short bullets per tool with concrete examples of how a developer would actually use it from terminal/editor.

***

## 2. Configuration mechanisms, skills, and sub‑agents

> **Prompt: How AI Agents Are Configured (Context Files, Skills, Sub‑Agents)**  
> Using the notebook’s sources, analyze how modern AI agents and coding tools are **configured via repository artifacts** (Markdown, JSON, YAML, etc.).[1][5]
> 1) List and define the main configuration mechanisms (e.g., Context Files, Skills, Tools, Sub‑agents, Hooks, Workflow files, AGENTS.md), citing how each mechanism is described in the literature or docs.[5][1]
> 2) For each mechanism, extract at least one **concrete example** (real or schematic) that shows how it encodes behavior or “skills” for the agent.  
> 3) Summarize which mechanisms are most common and why (e.g., context files dominating, AGENTS.md emerging as a cross‑tool standard).[1][5]
> End with a short “design guide” explaining how a practitioner should choose between context files, skills, and sub‑agents when configuring an agent for a codebase.

***

## 3. Agentic design patterns and reasoning loops

> **Prompt: Agentic AI Design Patterns for Coding Agents**  
> From the sources, extract the **design patterns** relevant to AI agents used for coding and CLI work.[7][6]
> 1) Identify patterns like ReAct, Tool Use, Planning, Reflection, Multi‑Agent Collaboration, and Chain‑of‑Thought, and briefly define each.[6][7]
> 2) For each pattern, explain:  
>    – What kind of coding/CLI task it suits (e.g., debugging, repo exploration, refactoring, research).  
>    – How it manifests in real tools or prompts (e.g., explicit “plan then act”, separate critic agent, explicit tool‑call phases).[7][1]
> 3) Provide small **prompt or config templates** that show how a developer could instantiate each pattern in an AI coding agent.  
> Conclude with which patterns are most important for reliable agentic coding and why.

***

## 4. Deep‑research / literature‑review style synthesis

> **Prompt: Literature‑Style Review of Agentic AI Coding Tools**  
> Treat this notebook as a mini‑literature base on **agentic AI coding tools and agents**.[8][6][1]
> 1) Identify the main research questions or themes (e.g., “How are agentic tools configured?”, “What are common failure modes?”, “What design patterns are emerging?”).[6][1]
> 2) For each theme, summarize key findings across sources, noting **agreements, disagreements, and open questions**.[9][10]
> 3) Extract 4–6 **recurring challenges or weaknesses** (e.g., misconfiguration, brittle context, unsafe tool use) and describe proposed mitigations or best practices.[10][1]
> 4) Finish with:  
>    – A short “state of the art” synthesis.  
>    – A list of concrete ideas for future tools or experiments that the current literature implies but doesn’t fully resolve.[8][6][1]

***

## 5. Skill‑building and pedagogy with agents

> **Prompt: Using AI Agents as Skill‑Builders, Not Just Autocomplete**  
> Using the sources, analyze how AI agents and agentic CLIs can be used to **improve human developer skills** (not just speed).[11][7][1]
> 1) Identify mechanisms that create **feedback and learning loops** (e.g., explicit planning, reflection, tool‑verified actions, approval gates, critique sub‑agents).[7][6]
> 2) Extract examples where configuration (context files, skills, AGENTS.md) encodes process discipline: testing, reviewing, security checks, documentation.[5][1]
> 3) Propose a 2–4 week “training regimen” where a developer configures and uses an agentic CLI in ways that deliberately teach:  
>    – better decomposition,  
>    – better test habits,  
>    – better use of tools and documentation.  
> Cite sources for each suggested practice and flag areas where evidence is thin or speculative.[11][1]

If you tell me which *specific* agents you’re loading as sources (e.g., Claude Code + Aider + Cline + agentic‑system‑prompts repo), the next step can be a tailored prompt that forces a **side‑by‑side config/prompt template** just for those.

## Human

For the deep research prompts that you've given me, does it cover how to prompt, how to structure a prompt, what prompt allows the LLM freedom to be great, to be successful?

## Assistant

Some of the prompts you have do touch prompting and structure, but not explicitly enough on: “how do I write prompts that let an agentic CLI / LLM be great?”  You’ll want one *dedicated* deep‑research prompt aimed at prompt‑design itself.[1][2][3]

## Gap coverage

The existing research prompts mainly emphasize:

- Ecosystem, config mechanisms, and design patterns (agents, hooks, MCP, skills).[2][4][1]
- Workflows, tools, and skill‑building loops.[3][5][2]

They **only implicitly** cover:

- Concrete prompt structures (sections, constraints, examples).  
- “Freedom vs constraints” (how tight vs open a prompt should be).  
- Meta‑prompts about *how* to ask the model to reason, explore, or self‑correct.[6][1][3]

So you’re missing an explicit “prompt‑about‑prompts” research task.

## Add this dedicated deep‑research prompt

Drop this into NotebookLM as an additional instruction:

> **Prompt: Designing Prompts for Agentic Coding & CLI Agents**  
> Using the sources in this notebook, analyze **how to write prompts and instructions** that let agentic coding tools and AI agents perform at a high level while staying reliable.[1][3][6]
> 1) Extract concrete **prompt patterns** used in production systems (system prompts, task prompts, plan prompts, critic/reviewer prompts). For each pattern, show:  
>    – Its structure (sections like role, goals, constraints, tools, outputs, examples).  
>    – At least one real or schematic example.[4][7][2]
> 2) Investigate how different levels of **constraint vs freedom** affect performance:  
>    – Highly prescriptive prompts (detailed steps, strict formats).  
>    – Looser, high‑level prompts that allow exploration and creativity.  
>    Summarize when to tighten vs loosen constraints for coding, refactoring, debugging, and research tasks.[3][6][1]
> 3) Identify prompt techniques that make agents **more successful and robust**, such as:  
>    – Asking for plans before actions.  
>    – Requiring explicit assumptions and uncertainties.  
>    – Requesting multiple options before a choice.  
>    – Built‑in self‑critique or checklist passes.[1][3]
> 4) Derive 5–10 reusable **prompt templates** for:  
>    – “Do the work” (implementation).  
>    – “Think then do” (plan then act).  
>    – “Critic” (review and improve code or plans).  
>    – “Researcher” (gather and synthesize info).  
>    – “Coach” (explain and teach concepts back).  
>    For each, emphasize which parts must be fixed (constraints) and which parts should be left open for the model to be creative.[6][3]
> 5) Summarize best‑practice guidelines for structuring prompts for **agentic CLIs** specifically (Claude Code, Aider, Cline, etc.), including how to reference tools, repo context, and editor/terminal capabilities.[8][9][2][4]
> Highlight any areas where the literature or examples conflict and clearly label speculative recommendations.

With that added, your deep‑research setup will directly cover:

- **How to prompt**  
- **How to structure prompts**  
- **How much freedom vs constraint** yields the best behavior for agentic coding and CLIs.[3][6][1]

## Human

I don't want it to be for sources in a notebook. I want it to find information.

## Assistant

Most of the templates I gave were “closed‑corpus” (NotebookLM‑style). You want **open‑web deep research prompts** you can hand to a system that goes out and finds information itself.

Here are minimal, reusable prompt templates tuned for that.

***

## 1. General deep‑research on agentic CLIs

> **Goal:** Map and deeply understand modern *agentic CLI coding tools* and how to use them well.  
>  
> **Task:**  
> Conduct an open‑web deep‑research study on **agentic CLI coding tools for software development** (e.g., Claude Code, Aider, Cline, Gemini CLI, Codex‑style CLIs, etc.).  
> 1) Identify the main tools, their capabilities (file/edit, repo‑wide reasoning, planning, tool use, git/CI integration), and their typical workflows.  
> 2) Extract concrete examples from docs, blog posts, repos, and talks showing how expert users actually run these tools from the terminal.  
> 3) Summarize strengths, weaknesses, and unique ideas for each tool, focusing on practices that improve reliability and developer skills, not just speed.  
> Present a concise written report with a comparison table plus short sections per tool.

***

## 2. Prompt design: how to prompt agentic coding tools

> **Goal:** Learn how to write prompts that let agentic coding tools “be great” while staying reliable.  
>  
> **Task:**  
> Search the open web (docs, blogs, talks, research) for **prompt patterns and best practices** used with coding‑oriented LLMs and agentic CLIs.  
> 1) Extract concrete prompt structures (role, goals, constraints, tools, examples, output format) from real systems or expert guides.  
> 2) Analyze how different levels of constraint vs freedom in prompts affect performance for coding, refactoring, debugging, and research tasks.  
> 3) Identify techniques that reliably improve outcomes: plan‑then‑act prompts, explicit assumptions, multiple options, self‑critique passes, checklists, etc.  
> 4) Produce 5–10 reusable prompt templates for: implementer, planner, critic/reviewer, researcher, and coach/teacher roles, each annotated with which parts should be fixed vs left open for the model to be creative.  
> Deliver the findings as: brief explanation of principles + the actual prompt templates.

***

## 3. Hooks, automation, and discipline (Claude Code + others)

> **Goal:** Use hooks/automation to make agentic CLIs teach better engineering discipline.  
>  
> **Task:**  
> Using open‑web sources, research how **hooks, config, and automation** are used in agentic CLIs (Claude Code, Aider, etc.) to enforce good practice.  
> 1) Document the hook/automation mechanisms available (pre/post hooks, on‑write hooks, test hooks, tool hooks, git hooks around agent actions).  
> 2) Collect real or example configurations that auto‑run formatters, type checkers, tests, security scans, or diff logging after the agent edits code.  
> 3) Synthesize 5–10 high‑leverage hook/automation patterns that:  
>    – prevent untested or unsafe changes,  
>    – surface diffs for human review,  
>    – provide fast feedback that “trains” the human user over time.  
> Output the result as a short write‑up plus concrete config snippets (JSON/YAML/shell).

***

## 4. Plan / approval modes as learning tools

> **Goal:** Turn plan/approval modes into architecture and decomposition tutors.  
>  
> **Task:**  
> Research how **plan modes** and approval workflows are implemented in Claude Code and other agentic coding tools, and how they can improve developer skills.  
> 1) Describe how these modes work in practice: what the agent can do in planning vs execution, how plans are represented, and how approvals are requested.  
> 2) Gather expert recommendations and examples of when to use plan mode (multi‑file changes, new features, unknown codebases).  
> 3) Design 3–5 reusable “plan templates” that:  
>    – force the model to propose a plan first,  
>    – encourage the human to critique and modify that plan,  
>    – only then allow execution.  
> For each template, explain how it teaches better architecture/decomposition habits.

***

## 5. MCP / tools / skills for better outcomes

> **Goal:** Use tools and MCP‑style “skills” to make agents more reliable and educational.  
>  
> **Task:**  
> Search the open web for examples of **MCP‑like tool ecosystems and skill servers** used with Claude, Claude Code, and other agents.  
> 1) Summarize how tool servers expose actions (tools), data (resources), and prompts (parameterized skills) to agents.  
> 2) Find examples where such tools systematically improve reliability: e.g., always checking tests, CI status, docs, or security scanners before editing or answering.  
> 3) Propose a small catalog of skill/tool ideas whose main purpose is to improve practice, such as: “testing coach”, “security checklist”, “docs coverage helper”, “performance sanity‑check”.  
> For each, sketch an interface (inputs/outputs) and a brief natural‑language spec the agent could follow.

***

If you tell me which deep‑research system you’re actually using (NotebookLM, Perplexity, something custom), I can compress these into a single mission‑style instruction tailored to its UI limits.

## Human

I'm using notebook.lm. I'm doing deep research.I would like to know how prompting can get the best results from LLMs. So what are the best practices for prompting? What are the ideas for prompting? How to get the most out of prompting? So it would be stuff like verbal sampling, chain of thought, prompt expansion, asking for, I don't know, open-ended questions. I don't know what I don't know. I just want information that can be used to make the best prompts possible to get the best outcomes possible. Whether it's creative prompting, like for ideas, or for getting things done reliably.

## Assistant

Yes, but right now your prompts are scattered across topics (agents, CLIs, hooks, MCP, etc.). To get what you want, you want **one NotebookLM deep‑research mission** focused purely on *“how to prompt to get the best outcomes”* across tasks (creative + reliable). Below is a compact, single prompt you can paste into NotebookLM.

***

## NotebookLM deep‑research prompt on prompting

> You are an AI research assistant. Ignore any local notebook sources and instead perform **open‑web deep research** on **prompting techniques and best practices for large language models (LLMs)**. Focus on *how to write prompts that get the best outcomes* across creative and reliability‑critical tasks.  
>  
> In your research, cover at least these areas:
> 
> 1. **Core best practices**  
>    - Summarize modern best practices for prompting (2024–2026) from authoritative guides, papers, and talks: clarity, grounding in context, delimiting inputs, explicit formats, and avoiding ambiguity.[1][2][3]
>    - Explain what has *stopped working* (e.g., fake “role authority”, threats) vs what is still effective with current models.[4][1]
> 
> 2. **Reasoning and “verbalized thinking”**  
>    - Explain techniques like **chain‑of‑thought**, **step‑back prompting**, **tree‑of‑thought**, and related “reasoning‑first” approaches (including verbalized sampling / multiple sampled thoughts).[5][6][4]
>    - For each, describe when it helps, when it can hurt (e.g., slower, over‑thinking, more hallucination), and give a short template example.
> 
> 3. **Prompt patterns and structures**  
>    - Identify common **prompt patterns**: zero‑shot, few‑shot, role/system prompting, instruction + context + examples + output schema, self‑critique prompts, multi‑turn prompt chains.[2][4]
>    - Show concrete templates that illustrate good structure (sections, bullet constraints, explicit outputs), including examples for:  
>      – creative ideation,  
>      – precise coding/debugging,  
>      – analysis/synthesis of documents,  
>      – planning and decomposing complex tasks.[1][2]
> 
> 4. **Freedom vs constraints**  
>    - Synthesize what is known about **how much freedom to give an LLM**: when high‑level open‑ended prompts work well vs when tight, highly constrained prompts perform better.[4][1]
>    - Provide guidelines on:  
>      – when to specify step‑by‑step instructions,  
>      – when to specify format schemas,  
>      – when to leave aspects open so the model can be creative.
> 
> 5. **Prompt expansion, refinement, and self‑improvement loops**  
>    - Research techniques for **prompt expansion / refinement**: iterative rewriting, asking the model to propose a better prompt, adding missing constraints, and building prompt libraries.[3][7][1]
>    - Describe practical feedback loops: prompt → model answer → critique (by human or model) → revised prompt, and how these loops improve prompts over time.[8][1]
>    - Include at least one concrete “prompt‑about‑prompts” template that asks the LLM to help design or refine the prompt itself.
> 
> 6. **Task‑specific prompting (creative vs reliable)**  
>    - Contrast prompting strategies for:  
>      – **creative tasks** (idea generation, writing, brainstorming, exploration).  
>      – **reliability‑critical tasks** (coding, data analysis, instructions, factual Q&A).[2][1]
>    - Provide specific do/don’t lists and example prompts for each class.
> 
> 7. **Summary playbook**  
>    - Distill your findings into a **concise prompting playbook**:  
>      – 10–15 bullet‑point rules of thumb.  
>      – 5–10 reusable prompt templates (for reasoning, coding, creative, analysis, and self‑critique).  
>    - Clearly label which recommendations are strongly supported vs speculative or emerging.[6][1][4]
> 
> Keep the answer organized by these headings, and include short quoted examples or schemas where allowed. If sources disagree, state the disagreement and indicate which view seems more credible and why.

This prompt tells NotebookLM exactly what you described: “go out to the web, learn *how to prompt*, and come back with principles + templates that let me get the best possible outcomes.”

## Human

What's a deep research prompt that I can give to Notebook LM so that we can find techniques that can be used in Claude Code CLI to improve display readability, formatting, and reliability?  Often the LLM does not follow the skill output format properly, sometimes not even at all.  I want the LLMs to provide the final report, in the actual report format I want to see it in.

## Assistant

Use this as a single deep‑research “mission prompt” for NotebookLM; it’s written to discover techniques you can apply in Claude Code CLI to make outputs actually obey your report formats.

***

## NotebookLM deep‑research prompt (Claude Code CLI output formats)

> You are an AI research assistant. Conduct open‑web deep research on **techniques to make LLMs, especially Claude Code CLI, consistently produce readable, well‑formatted, and schema‑respecting terminal output**.
> 
> Focus on discovering *practical, implementable techniques* that improve:
> - Display readability in terminals (Claude Code CLI and similar tools).  
> - Adherence to a desired **output schema / report template**.  
> - Reliability of “skill output formats” and structured responses.
> 
> Specifically:
> 
> 1. **Claude Code–specific mechanisms**  
>    - Document how Claude Code handles output formatting:  
>      – Output styles (what they are, how they modify the system prompt, and how to define custom styles).[1][2]
>      – CLI flags such as `--output-format` (text, json, stream-json) and when each should be used.[3]
>    - Collect examples and best‑practice guidance for configuring output styles and CLI flags to get predictable, scannable output for humans vs machines.[1][3]
> 
> 2. **Terminal formatting skills / patterns**  
>    - Find any **Claude Code skills** or third‑party tools focused on terminal output formatting (e.g., “Terminal Output Formatter” skills, report‑layout helpers).[4]
>    - Extract the patterns they use: box layouts, TOON/JSON blocks, Markdown tables, status lines, “scannable in under 5 seconds” rules, consistent section headings, etc.[4]
>    - Summarize how these patterns can be encoded into:  
>      – skill definitions,  
>      – prompt templates,  
>      – or output‑style configs.
> 
> 3. **Schema / format enforcement techniques**  
>    - Research techniques for making LLM outputs **schema‑reliable**:  
>      – Structured output / JSON‑schema enforcement,  
>      – external validators (e.g., Marshal‑style tools),  
>      – retry‑on‑invalid patterns.[5][6][7]
>    - Explain how these ideas can be adapted when using Claude Code CLI: for example, combining `--output-format json` with a schema validator, or wrapping the CLI in a script that checks and re‑prompts on invalid output.[7][3]
> 
> 4. **Prompt patterns that increase format obedience**  
>    - Collect prompt / system‑prompt patterns that significantly improve adherence to a desired format, such as:  
>      – clearly delimited schema definitions,  
>      – “only output X, nothing else” instructions,  
>      – explicit examples (few‑shot formatting),  
>      – two‑stage prompts (first plan the structure, then fill it),  
>      – self‑check steps (“verify your output matches this schema”).[8][5]
>    - For each pattern, provide at least one generic template I can adapt to my own report formats.
> 
> 5. **Designing robust report formats for CLIs**  
>    - From blogs, docs, and examples, extract best practices for designing **human‑readable report formats** for terminals: section ordering, headings, bullet styles, table usage, width limits, Unicode vs ASCII choices, etc.[9][4]
>    - Propose 2–3 reusable “report skeletons” (for status reports, analyses, and multi‑section summaries) that are realistic for Claude Code CLI to follow.
> 
> 6. **Putting it together for Claude Code CLI**  
>    - Given everything above, propose a concrete recipe for Claude Code CLI that includes:  
>      – recommended output style configuration,  
>      – example skill or command definitions for report generation,  
>      – example prompts that produce a final report *directly in the desired format*,  
>      – optional wrappers (shell scripts, validators) to catch and fix format violations.[3][7][1][4]
> 
> Output your findings as a concise guide with:  
> - A short explanation per technique.  
> - Concrete examples (prompt templates, config snippets, CLI invocations).  
> - A final checklist I can apply when creating new skills or prompts so that the LLM’s *final answer* appears exactly in the report format I want.

## Human

given the questions and deep research prompts I've asked for. How do we surface the repos that are related to them?  That would answer my questions and topics of interest.

## Assistant

To surface repos that actually answer these deep‑research prompts, treat “find the right repos” as its own mini‑pipeline and make the tools do the heavy lifting.

***

## 1. Add an explicit “repo discovery” section to each deep‑research prompt

For every NotebookLM deep‑research mission you run, append a section like:

> **Repo and asset discovery**  
> As part of this research, search the open web and GitHub for **public repositories, gists, or config collections** that:  
> - Implement or demonstrate the techniques described above (e.g., Claude Code CLI configs, hooks, MCP servers, agentic CLI skills, prompt libraries, output‑formatting helpers).  
> - Include concrete artifacts such as `.claude/config`, `.claude/commands`, MCP server code, example system prompts, or CLI wrappers.  
> For each relevant repo, provide:  
> - Name and URL  
> - Short description of what it demonstrates  
> - Which of the research topics it illustrates (e.g., “hooks & automation”, “output formatting”, “prompt libraries”, “agentic CLI skills”).  
> Prioritize repos with real‑world usage, clear READMEs, and recent activity.

That turns “repos” into a first‑class deliverable, not an incidental detail.

***

## 2. Use focused GitHub queries outside NotebookLM

Run targeted GitHub searches, then feed the *best candidates* into NotebookLM for deeper analysis:

- By topic:  
  - `claude code output styles path:.claude`  
  - `"claude code" path:.claude`  
  - `"aider" "config.yml" agent`  
  - `"AGENTS.md" lang:markdown`  
  - `"mcp" "server" language:python`  

- By concept:  
  - `"agentic" "system prompt"`  
  - `"prompt library" llm`  
  - `"structured output" "json schema"`  

Then:

1. Short‑list repos that actually contain configs/prompts (not just marketing).  
2. Add those repos as sources into a NotebookLM notebook.  
3. Ask NotebookLM:  
   - “Map and compare all the `.claude/**` files in these repos.”  
   - “Extract all prompt templates and config patterns related to X.”

***

## 3. Bake “repo mining” into your questions

When you phrase your NotebookLM questions, be explicit:

- “Find **GitHub repos, gists, and example projects** that show how to…”
- “Prefer sources with actual config/prompt files over blog posts.”
- “Only list a repo if you can point to at least one concrete file that illustrates the technique (e.g., `.claude/config`, `agents/*.md`, `skills/*.json`, `mcp_server.py`).”

This pushes the model to prioritize repos instead of generic articles.

***

## 4. Iterative refinement loop

Once you get an initial repo list from NotebookLM:

1. **Filter**: Manually skim the top 5–10 for seriousness (stars, recency, clarity).  
2. **Reload**: Create a new NotebookLM notebook with only those repos as sources.  
3. **Deep‑dive prompt**:  
   - “Given these repos, extract and generalize the patterns in:  
     – Claude Code / agentic CLI configs  
     – Prompt templates  
     – Hooks / skills / MCP usage  
     – Output‑formatting strategies.”

That two‑stage process (open‑web → curated repo notebook) tends to produce much higher‑quality, code‑level answers.

***

## 5. Concrete next step tailored to your current prompts

For the prompts you already have (agentic CLIs, prompting best practices, Claude Code output formatting):

- Add the “Repo and asset discovery” block from section 1 to each.  
- Run them once in NotebookLM Deep Research.  
- Take the repo list it returns, create a new notebook called e.g. **“Agentic CLI Repos – Patterns”**, add those repos as sources, and then ask:  
  - “Extract reusable Claude Code CLI configs, MCP servers, and prompt templates I can adapt directly, organized by topic (prompting, hooks, output formats).”

That’s the shortest path from “questions and prompts” → “actual repos that answer them.”

## Human

Actually, maybe you can do that for me. Find the Githubs, repos, gists, example projects, etc.  Instead of me asking you to provide a prompt I can give to Notebook.lm, how about you just action the prompt.

## Assistant

Yes, can action it directly and give you concrete starting points.

Below are **actual repos / resources** that are directly relevant to the Claude Code + agentic CLI + config + skills space, plus a couple of “agent‑config” anchors you can mine with NotebookLM.

***

## 1. Claude Code config, layout, and tips

These are your primary anchors for `.claude/**`, hooks, commands, and config patterns.

- **Claude Code configuration guide (paths + layout)** – *article, not repo, but extremely useful to understand the filesystem you’re mining*  
  - URL: https://inventivehq.com/knowledge-base/claude/where-configuration-files-are-stored[1]
  - Why it matters:  
    - Shows full structure of `~/.claude/` and project‑level files: `CLAUDE.md`, `.claude/settings.json`, `.claude/commands/*.md`, `.mcp.json`, and user MCP config `~/.claude.json`.[1]
    - Gives you the canonical filenames and paths you should search for inside repos (e.g., `CLAUDE.md`, `.claude/commands`, `.mcp.json`).[1]

- **Builder.io – How I use Claude Code (+ my best tips)**  
  - URL: https://www.builder.io/blog/claude-code[2]
  - Why it matters:  
    - Shows **real hook JSON** used in Claude Code (Prettier, `tsc` on edits).[2]
    - Describes using `CLAUDE.md` to encode project‑specific commands and instructions.[2]
    - Good example for: hooks + commands as “skills” and discipline enforcers.

You can feed those URLs plus any `.claude`‑containing repos into NotebookLM and ask it to extract patterns.

***

## 2. Installable Claude Code config as a “skill bundle”

There is at least one repo‑backed **skill/config installer** you can mine:

- **install-claude-config skill** (LobeHub / Skills Market entry)  
  - Listing: https://lobehub.com/skills/lelandg-.claude_code-install-claude-config[3]
  - Key details in the description:  
    - This skill **merges a repo’s Claude Code configuration into `~/.claude/`**.[3]
    - It explicitly mentions merging: “agents, skills, output styles, instructions, settings, MCP servers, and supporting files” using a diff‑and‑ask workflow.[3]
    - Mentions an `Agent` mapping table (e.g., `claude-code` uses `./.claude/skills/`), which hints at a multi‑agent config layout.[3]
  - Action for you:  
    - Click through to the underlying GitHub repo from that page; add it as a source to NotebookLM.  
    - Ask NotebookLM to **map out the structure of that repo’s `.claude/**`, skills, output‑styles, and CLAUDE.md patterns**, then generalize.

***

## 3. AGENTS.md – cross‑tool agent config pattern

- **AGENTS.md “spec”**  
  - URL: https://agents.md[4]
  - Why it matters:  
    - Defines an open format for **agent‑facing project instructions** used by many coding agents (Claude Code, Cursor, Windsurf, etc.).[4]
    - Shows the **sections** that matter to agents: project overview, build/test commands, style guidelines, testing instructions, security considerations.[4]
    - It’s effectively a **system prompt in Markdown** for tools that support it.  
  - Action:  
    - Search GitHub for `AGENTS.md` to find real projects:  
      - `AGENTS.md language:Markdown`  
    - Add a handful of serious repos to NotebookLM and ask it to:  
      - “Compare how different projects use AGENTS.md to configure agents; extract common sections and best practices.”

***

## 4. MCP server + Claude integration examples

For MCP usage and skills:

- **GitHub MCP server – install‑claude docs**  
  - URL: https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md[5]
  - Why it matters:  
    - Shows a **real `.mcp.json` style config** with a `mcpServers` entry and the `claude mcp add` / `claude mcp list` workflow.[5]
    - Gives a complete JSON snippet for adding a `github` MCP server via Docker.[5]
  - Action:  
    - Use this as a canonical pattern for MCP server config in Claude; have NotebookLM generalize how to define similar MCP “skill servers” for your use cases.

- **Emmanuel Bernard – MCP servers and Claude**  
  - URL: https://emmanuelbernard.com/blog/2025/04/07/mcp-servers-and-claude-desktop-path/[6]
  - Why it matters:  
    - Discusses sharing `~/.claude` config with containers and sandboxed environments.[6]
    - Useful for your “CLI multi‑terminal / sandbox” workflows.

***

## 5. How to turn this into a repo‑mining flow

Given what you asked (“just action the prompt”), here is a concrete flow using the links above plus your own GitHub searches:

1. **Seed NotebookLM with known anchors**  
   - Add as sources:  
     - Builder.io Claude Code tips[2]
     - InventiveHQ Claude config layout[1]
     - install‑claude‑config repo (via the LobeHub skill link)[3]
     - GitHub MCP server install‑claude docs[5]
     - AGENTS.md site and a few AGENTS.md‑using repos[4]
2. **Run a deep‑research question like:**  
   - “From these sources and the open web, locate GitHub repos and gists that contain:  
     – `.claude/` directories,  
     – `CLAUDE.md` or `AGENTS.md`,  
     – `.mcp.json` or MCP server code,  
     – Claude Code or agentic CLI configs.  
     List each repo with URL, relevant files, and what technique it demonstrates (hooks, skills, output styles, MCP, prompting).”  
3. **Refine**:  
   - Take the top 5–10 repos NotebookLM identifies; add them to a new notebook; ask it to:  
     - “Extract reusable patterns and prompt/config templates from these repos, organized by topic (prompting, hooks, output formats, MCP, skills).”

***

## TL;DR: key URLs you can act on now

- Claude config layout reference: https://inventivehq.com/knowledge-base/claude/where-configuration-files-are-stored[1]
- Claude Code hooks & commands example: https://www.builder.io/blog/claude-code[2]
- Claude config installer skill (leads to a config repo): https://lobehub.com/skills/lelandg-.claude_code-install-claude-config[3]
- AGENTS.md spec + examples: https://agents.md[4]
- GitHub MCP server config for Claude: https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md[5]

Use those as your **initial seed set**; then let NotebookLM and GitHub search extrapolate to more repos that match the same patterns.

## Human

when I use gitingest on a github repo, sometimes (often?) the file is too big to upload to notebooklm.  What can I do to get the repo into notebooklm?

## Assistant

NotebookLM’s hard limits are per **source**, not per repo, so the trick is to change *how* you ingest the repo rather than trying to shove a single giant text file in. Each source can be up to **500,000 words or ~200MB**, and you can have up to **300 sources per notebook on Pro**.[1][2][3]

Here are practical ways around the gitingest‑too‑big problem:

***

## 1. Split the repo before NotebookLM sees it

Instead of one giant gitingest dump:

- **Scope by directory or pattern**  
  - Run gitingest or an equivalent tool on **subtrees**:  
    - `src/` only, then `docs/`, then `infra/`, etc.  
  - Or export only files matching patterns: `src/**/*.ts`, `scripts/**/*.py`, `docs/**/*.md`.  
- **Chunk by size**  
  - If your tool supports it, set a max output size and generate multiple chunks (e.g., `repo-part-1.md`, `repo-part-2.md`).  
  - Aim for comfortably under 500k words and 200MB per chunk; almost any “reasonable” code directory will fit.[2][1]

Upload each chunk as a separate source; NotebookLM will still cross‑reference them inside one notebook.[4][1]

***

## 2. Use multiple source types, not just a monolithic text file

NotebookLM accepts **URLs, PDFs, text/Markdown files, and Google Docs**.[5][2]

You can:

- **Add the GitHub repo URL(s) directly** as sources. NotebookLM will crawl the pages (within limits) without you pre‑flattening everything.[2][5]
- For critical parts (design docs, AGENTS.md, CLAUDE.md, `.claude/config`, key services), **export just those files** as Markdown or PDF and upload them separately.  
- For large code trees you don’t need fully indexed, rely on the GitHub URL plus a **manually curated “map” document** summarizing structure and key files.

***

## 3. Create a curated “index” source instead of full raw code

For many of your use cases (patterns, configs, skills), you don’t need every line of code:

- Generate an **index Markdown** that includes:  
  - File tree (paths only).  
  - The content of only the important config/prompt files:  
    - `CLAUDE.md`, `AGENTS.md`, `.claude/commands/*.md`, `.claude/settings.json`, `.mcp.json`, hook configs, skill definitions.  
  - Short inline summaries of larger files rather than verbatim content.  

That single index file will be far smaller than a full gitingest dump but is much more semantically dense for the questions you care about.

***

## 4. Use multiple notebooks by layer or function

Because Pro gives you **up to 300 sources per notebook** and 500 notebooks total, you can shard by concern.[3][1]

For example:

- Notebook A: “Agent configs & prompts” – only `.claude/**`, `AGENTS.md`, MCP configs, prompt libraries.  
- Notebook B: “Core services” – only `src/` of service A/B, with minimal tests.  
- Notebook C: “Infra & pipelines” – infra code, CI configs, scripts.

When you want cross‑cutting insight, run Deep Research on the **web plus a small subset of these notebooks**, rather than trying to throw an entire monorepo variant into one source.

***

## 5. Avoid heavy formats when possible

If gitingest is giving you a **PDF** that’s near the 200MB limit (e.g., lots of diagrams or screenshots), you’ll hit size limits faster.[6][7]

Prefer:

- **Plain text or Markdown** exports of code and docs.  
- If you must use a PDF, generate a lean “text‑only” variant (no images, compressed).

***

## 6. Concrete workflow you can adopt

1. **Decide what you actually need from the repo** (configs/prompts vs all code).  
2. **Export by slice**:  
   - Slice 1: `.claude/**`, `AGENTS.md`, MCP configs → one Markdown file.  
   - Slice 2: key service directories (`service-a/src`, `service-b/src`) → per‑service files.  
3. Upload each slice as its own source into a single NotebookLM notebook.  
4. Optionally, create a **high‑level “repo map” note** summarizing components and linking file paths; NotebookLM will use that as glue.  
5. Ask your deep‑research questions against that notebook + the web.

This keeps you comfortably inside NotebookLM’s per‑source limits while still giving it enough structure to answer the kinds of pattern and skill questions you’re asking.[4][1][2]

## Human

"Add the GitHub repo URL(s) directly as sources. NotebookLM will crawl the pages (within limits) without you pre‑flattening everything"

Will we get all the information in the repo or just a summary?

## Assistant

You do **not** get a full raw mirror of the repo; you get **indexed page content with truncation/priority behavior**, not a byte‑for‑byte ingest.

## What NotebookLM does with a GitHub URL

- It treats the URL as a **web page source**, then crawls linked pages **within internal limits** (depth, size, and token budget).[1][2]
- It tends to pull:  
  - The README and other prominent Markdown docs.  
  - The main code files it can reach via links.  
  - Some directory listings / sub‑pages.[3][4]

Because there is a **per‑source size limit (~500k words / ~200MB)**, it will **stop ingesting once that budget is used**, and it may prioritize “important” pages (docs, top‑level files) over every single leaf file.[2][5][1]

## What that means in practice

- For **small and medium repos**, you often get *most* of the text content (docs + key code files).  
- For **large repos / monorepos**, you effectively get a **sampled subset**, biased toward front‑facing docs and top‑linked files, plus whatever the crawler reaches before hitting limits.[6][3]
- You do **not** get a guarantee like “every file is available character‑for‑character.”  

So the behavior is closer to:

- “Rich, searchable snapshot with some implicit summarization/selection,”  
not  
- “Exact archive suitable for e.g. full‑text code search.”

## How to get closer to “all the information”

For repos where you care about specific assets (configs, prompts, skills):

- **Explicitly upload those files** (or small bundles) as separate sources (Markdown or text).[5][1]
- Use the GitHub URL as a **supplemental context** source, not the only source.  
- Optionally add a **manually curated index/overview file** that lists paths + pasted content for key files; that file will be fully ingested because it’s small.

That combo gives you much more control than relying on the automatic GitHub crawl alone.

## Human

Is there a way to use a deep research notebook LM prompt to get closer to the full repo?

## Assistant

A prompt alone can’t force NotebookLM to mirror a full repo, but you can use Deep Research to **systematically pull in more of it** by driving GitHub‑level fetching and targeted uploads.

***

## 1. Use Deep Research to enumerate and prioritize files

Have NotebookLM first act as a **repo cartographer**, then you ingest slices yourself.

Example Deep Research prompt (you run this on the repo URL + web):

> “Given this GitHub repository URL, list the full file and directory structure (or as much as GitHub exposes), focusing on:  
> – config and metadata files (`CLAUDE.md`, `.claude/**`, `AGENTS.md`, `.mcp.json`, `*.config.*`, `*.yml`, `*.toml`),  
> – source directories (`src/`, `apps/`, `packages/`, `services/`),  
> – docs (`docs/`, `README*`, `design/**`).  
> For each directory, output a tree with relative paths and sizes if available, and highlight which files are likely most important for understanding configuration, prompts, and architecture. Also indicate which subtrees could be extracted as separate NotebookLM sources without exceeding per‑source limits.”

This uses Deep Research to:

- Crawl GitHub and reconstruct as much of the **file tree** as possible.  
- Identify **high‑value subsets** for separate upload to NotebookLM.

Then you:

- Download or script‑export those subsets (e.g., `docs/`, `.claude/`, `service-a/src/`) as separate text/Markdown files.  
- Upload them as multiple sources, staying under the per‑source limits.[1][2]

***

## 2. Use Deep Research to request *specific* files as content

You can also ask Deep Research to pull **actual file contents** for you, chunked:

> “For this GitHub repo, retrieve the full contents of all files under `path/to/dir` whose size is below NotebookLM’s per‑source limits. Split large files into logical chunks (e.g., per module or 1–2k lines) and present them in separate sections. Prioritize:  
> – config/prompt files,  
> – core service code,  
> – tests demonstrating usage.”

You then:

- Copy those chunks into local `.md` files.  
- Upload those as additional sources.

This doesn’t bypass size limits, but it lets Deep Research do the **GitHub crawling + chunking work** for you.

***

## 3. Use Deep Research to auto‑generate an “index + summaries” source

Since you can’t get every byte, aim for “max information density”:

> “From the repo and its docs, build an **index file** that:  
> – Lists all top‑level directories and notable files.  
> – For each important file, includes a 2–5 sentence summary of its purpose and any key APIs, configs, or prompts it defines.  
> – For each major directory (e.g., `services/`, `packages/`), summarizes its role and main components.  
> Make this index self‑contained and optimized for use as a single NotebookLM source.”

Upload that index as one source; it becomes a **semantic map** over the repo so NotebookLM can answer higher‑level questions even without every line of code.

***

## 4. What Deep Research cannot do

Prompting cannot:

- Override the **per‑source token/size limits**.[2][1]
- Force NotebookLM to silently store a full monorepo for arbitrary full‑text search.

So the realistic strategy is:

1. Use Deep Research to **discover structure and prioritize files**.  
2. Export those files/chunks yourself and upload them as multiple sources.  
3. Use an **index/summaries file** to glue them together.

If you want, next step can be: a concrete Deep Research prompt tailored to a specific repo (you paste the URL, and the prompt is specialized to produce a ready‑to‑upload index + chunking plan).

## Human

What's a deep research prompt I can give to notebooklm that will find more useful and practical info related to:
"Claude Code has a problem with following skills when they ask for a specific report output. How can we get the skills to follow the output format the way we want?
To get Claude Code skills to strictly follow a specific report output format, you need to combine structural prompt engineering with Claude Code's built-in configuration tools. Because LLMs can sometimes drift into conversational filler or improvise formatting, enforcing obedience requires a layered approach:
1. Create a Custom Output Style Claude Code’s default system prompt is highly optimized for software engineering and concise chatting. To change this, you can create a Custom Output Style specifically for reporting.
Create a Markdown file in ~/.claude/output-styles/ or .claude/output-styles/.
In the YAML frontmatter of this file, set keep-coding-instructions: false. This effectively "turns off" Claude's default coding personality, ensuring the agent focuses entirely on your specific reporting standards and formatting rules.
2. Use the Template and Few-Shot Pattern LLMs perform best when they are shown what success looks like rather than just being told.
Provide a Skeleton: Define a strict structure for the report using Markdown hierarchical headings (e.g., #, ##) and empty lines for negative space to improve scannability. For instance, you can design a "Status Dashboard Skeleton" that uses a Markdown table for critical metrics followed by bullet points for summaries.
Include Examples: Inside your skill's directory, create an examples/ folder with 2-3 high-quality sample outputs. This leverages "In-Context Learning" (few-shot prompting) so the agent learns the exact format to mimic.
3. Apply Two-Stage Prompting Complex reports often degrade in quality because the model tries to design the structure and retrieve the data at the same time. You can solve this by splitting the task in your skill's instructions:
Stage 1 (Structure Phase): Ask the model to generate a detailed implementation plan or structure for the report.
Stage 2 (Filling Phase): Instruct the model to fill that planned structure with the actual data.
4. Use Anchoring, Delimiters, and Negative Constraints
Anchor the Output: Give the model the exact beginning of the desired output to steer its completion. For example, tell Claude, "Start the response with the following structure: Current Status:".
Use XML Tags: Wrap different sections of your prompt (like <instructions>, <context>, and <format>) in XML tags so Claude can parse the requirements unambiguously.
Apply Strict Negative Constraints: Tell the model exactly what not to do to prevent conversational "slop." Use phrases like "Only output the following block, nothing else" or "Do not include conversational filler".
5. Implement Checklists and Validation Loops If your report format is mission-critical, you can build self-correction mechanisms into the workflow:
Skill Checklists: Include a comprehensive checklist in your SKILL.md file that Claude must explicitly confirm before it finishes generating the report.
Programmatic Validation: If you need machine-readable reports (like JSON), run Claude Code via the CLI in print mode (claude -p) and use the --json-schema flag to force the output into a validated JSON shape. You can then wrap this in a bash script that uses tools like jq to validate the output; if the schema breaks, the script automatically feeds the error back to Claude and requests a correction.
6. Consider Token-Efficient Formats If you are generating massive data reports that consume too much context window, consider teaching the model to use highly structured, compact formats like TOON (Token-Oriented Object Notation) or CSVs. You can do this by showing a small snippet of the format in the prompt, defining the fields, and explicitly instructing the model to use it.
How do I create a custom output style file?
Show me a CLAUDE.md example with report formatting rules
How can I use XML tags to anchor output?
What about skill-based hooks that validate or enforce the output or even create the output? Is that possible? Using Python to create the output or maybe the template of the output?
Yes, absolutely. Claude Code supports defining custom hooks directly inside the YAML frontmatter of your skills, which are scoped specifically to that skill's lifecycle and run only when the skill is active.
You can configure these hooks as type: "command" to execute Python scripts that validate, enforce, or even dynamically generate your report templates.
Here is how you can use skill-based hooks to achieve strict output control:
1. Validating and Enforcing Output Format You can write a Python script that validates Claude's output and blocks the agent from stopping if the formatting is wrong.
Use the Stop event: This event fires when Claude believes it has finished generating your report and is ready to stop.
Read the output: Your Python script will receive the event data as JSON via standard input (stdin), which includes last_assistant_message containing Claude's final text.
Enforce via Exit Codes: Your Python script can parse this output (e.g., checking if it's valid JSON or contains the required markdown headers). If the format is broken, your script can exit with code 2 (a blocking error) and write the specific formatting errors to stderr.
The Feedback Loop: Exiting with code 2 blocks Claude from stopping and feeds your error message directly back to the model. Claude is then forced to continue working and fix the formatting based on your Python script's feedback.
Alternatively, you could use a PostToolUse event with a matcher for the Write tool. This would run your Python validator immediately after Claude writes the report to a file.
2. Dynamically Creating Output Templates If you want to use Python to dynamically build the skeleton or template of the report before Claude starts working, you can use context injection hooks.
Use the SessionStart or UserPromptSubmit event: These events fire at the beginning of the workflow.
Inject context: Your Python script can fetch live data, assemble a blank template, and either print it to standard output (stdout) or return a JSON object with an additionalContext field.
Claude Code will seamlessly inject this generated template into the agent's context window, forcing Claude to use your exact programmatic structure as its starting point.
3. Using Prompt-Based or Agent-Based Validation If your report format is difficult to validate with pure Python (e.g., checking tone or qualitative structure), Claude Code allows you to use type: "prompt" or type: "agent" hooks.
Instead of executing a shell command, these hooks send the output to a fast LLM (like Claude Haiku) or spawn a sub-agent to evaluate the work.
You can instruct this hook: "Evaluate if this report strictly follows the required format. If it does not, return 'ok': false." If the fast model rejects the output, Claude Code forces the main agent to keep working and correct the mistakes.
To implement these in your skill, you simply add a hooks: block to your SKILL.md frontmatter pointing to your Python scripts:
---
name: generate-report
description: Generates a strictly formatted project status report.
hooks:
  - event: Stop
    type: command
    command: python validate_report_format.py
---
# Your skill instructions here...

This guarantees that your formatting rules are enforced as hard, deterministic constraints rather than just suggestions."

## Assistant

Use this as a single, self‑contained Deep Research mission for NotebookLM; it’s tuned to your exact problem (Claude Code skills not obeying report formats) and asks it to go beyond what you already know.

***

## NotebookLM Deep Research Prompt: “Claude Code skills that actually obey report formats”

> You are an AI research assistant. Ignore local notebook sources unless explicitly relevant and conduct **open‑web deep research** on how to make **Claude Code CLI skills reliably follow strict report output formats** (Markdown, tables, JSON, custom schemas, etc.).
> 
> Start from this problem statement:
> 
> “Claude Code skills often fail to follow the required output format for reports (sections, headings, tables, JSON schemas). I want Claude Code to consistently return the **final report already in the exact format I specify**, with no conversational filler or structural deviation.”
> 
> Using docs, blog posts, repos, examples, and discussions, do the following:
> 
> 1. **Claude Code–specific mechanisms for output control**  
>    - Document the official and community‑discovered mechanisms Claude Code provides for shaping output:  
>      – **Custom output styles** (e.g., files in `~/.claude/output-styles/` or `.claude/output-styles/`, `keep-coding-instructions`, report‑oriented styles).[1][2]
>      – Skill/command frontmatter options, including any `outputStyle`, `format`, or related fields.  
>      – CLI flags like `--output-format` (text vs json vs stream‑json) and known patterns for combining them with downstream validators.[2][3][1]
>    - Extract concrete examples of custom output style files, CLAUDE.md patterns, or skills that are designed to produce **structured reports**.
> 
> 2. **Prompt‑engineering patterns that increase format obedience**  
>    - Collect best‑practice patterns for making LLMs obey structure, including:  
>      – Explicit skeletons/templates (headings, tables, sections).  
>      – Few‑shot examples of correctly formatted reports.  
>      – Two‑stage prompting (plan structure first, then fill it).  
>      – Anchoring (forcing the output to start with specific text), XML/HTML‑like tag delimiters, and negative constraints (“only output this block, nothing else”).[4][5]
>    - For each pattern, provide at least one **generic template** I can drop into a Claude Code skill or output style description to improve format fidelity.
> 
> 3. **Hooks, validation loops, and programmatic enforcement**  
>    - Investigate how Claude Code’s **hooks** (global or skill‑scoped) can be used to validate or enforce output formats:  
>      – `Stop` or `PostToolUse` events that run scripts against the latest assistant output.  
>      – `type: command` hooks that call Python or shell validators and use exit codes to block completion and feed error messages back to Claude.[3][1]
>      – `type: prompt` or `type: agent` hooks that send the report to a fast model or sub‑agent for format checking and force revisions if it fails.  
>    - Find any open‑source examples (repos, gists) where hooks are used for **output validation** or schema enforcement, and summarize their patterns.
> 
> 4. **Schema and structured‑output techniques (JSON, TOON, CSV, etc.)**  
>    - Research modern techniques for making LLM outputs **schema‑reliable**: JSON schema enforcement, structured‑output APIs, Marshal‑style tools, retry‑on‑invalid loops.[5][6][3]
>    - Explain how these techniques can be adapted to Claude Code CLI, e.g.:  
>      – Running `claude` with JSON output formats.  
>      – Wrapping the CLI in a script that validates the output (with `jq` or Python) and automatically re‑invokes Claude with error feedback if the schema is broken.[2][3]
>    - Include any documented or proposed use of **compact formats** (TOON, CSV, others) when context/token budget is a concern.
> 
> 5. **Examples and templates I can reuse**  
>    - Find or construct **practical examples** for:  
>      – A custom output style file focused on reports (YAML frontmatter + instructions).[7][1]
>      – A `CLAUDE.md` or SKILL.md snippet that encodes report formatting rules (sections, headings, tables, tone).  
>      – A skill frontmatter `hooks:` block wired to a Python validator that checks Markdown or JSON and blocks completion on errors.  
>    - For each example, explain briefly **how and why** it improves adherence to the desired report format.
> 
> 6. **Synthesis: a concrete recipe for “strict report skills”**  
>    - Synthesize the findings into a **step‑by‑step recipe** for creating Claude Code skills that strictly follow a report format, combining:  
>      – Output styles,  
>      – Skill instructions and examples,  
>      – Prompt patterns (skeletons, few‑shot, anchors, constraints),  
>      – Hooks and external validators.[1][3][5][2]
>    - Present this as a short checklist plus example snippets, so it can be directly implemented in a real `.claude/` setup.
> 
> Clearly distinguish between:  
> - Techniques that are **documented and widely used** vs  
> - Techniques that are **experimental or inferred** from limited examples.[6][3][5]

You can paste this as‑is into NotebookLM Deep Research; its job is to go beyond your current write‑up, find additional mechanisms, real examples, and concrete patterns you can immediately encode into output styles, skills, and hooks.

## Human

Consider the entire chat session we've had today. What repos should I look at?

## Assistant

Given everything you’ve asked about today (Claude Code CLI, skills, hooks, MCP, AGENTS.md, output formats, agentic CLIs, prompt best practices), these are the repos and “anchor” projects that are most worth your time.

***

## Claude Code configs, skills, and CLAUDE.md

**1. Personal Claude Code config repos**

These show real `.claude/**` layouts, CLAUDE.md, skills, and sometimes hooks.

- `thkt/claude-config` – *Claude config + workflows*  
  - URL: https://github.com/thkt/claude-config[1]
  - Why it’s useful:  
    - Contains personal configurations for Claude AI/Claude Code, including **custom slash commands and systematic workflows**.[1]
    - Good for seeing how someone actually structures commands/skills and global instructions.

- `breeze4/claude-config` – *Claude Code config with CLAUDE.md focus*  
  - URL: https://github.com/breeze4/claude-config[2]
  - Why it’s useful:  
    - Has a **CLAUDE.md with global instructions** and a `.claude/` directory structure.[2]
    - Solid real‑world example of how to encode repo‑wide behavior and style guidelines for agents.

For both, you can mine:

- How they structure **CLAUDE.md** (sections, instructions, conventions).  
- The shape of `.claude/commands`, `.claude/settings`, and any hook/skill patterns.

***

## AGENTS.md and cross‑tool agent config

**2. AGENTS.md spec + examples**

- `agentsmd/agents.md` – *canonical AGENTS.md spec + examples*  
  - URL: https://github.com/agentsmd/agents.md[3]
  - Why it’s useful:  
    - Defines the **AGENTS.md format** and includes a minimal example, plus notes on usage in multi‑package repos.[4][3]
    - Shows how to structure **agent‑facing instructions** (project overview, commands, testing, etc.).

- `github/awesome-copilot` – *large, production‑grade agent/skill/hook layout*  
  - AGENTS file: https://github.com/github/awesome-copilot/blob/main/AGENTS.md[5]
  - Agents/docs: https://github.com/github/awesome-copilot/blob/main/docs/README.agents.md[6]
  - Why it’s useful:  
    - Has a rich structure: `agents/`, `instructions/`, `skills/`, `hooks/`, `workflows/`, etc., each with clear rules for frontmatter and validation.[5]
    - Skills use `SKILL.md` with **name/description and structure constraints**; hooks use `hooks.json` with event‑based config.[5]
    - Excellent pattern library for: skills, hooks, workflows, and schema for agent resources.

You can adapt these patterns directly into Claude Code skills, hooks, and even `.claude/skills/**`.

***

## MCP servers and skills

**3. Example MCP servers**

- `iddv/mcp-example` – *full FastMCP example repo*  
  - URL: https://github.com/iddv/mcp-example[7]
  - Why it’s useful:  
    - Contains multiple **MCP servers** (template, comprehensive, filesystem, minesweeper) plus clients and configs.[7]
    - Includes a `CLAUDE.md` and MCP config JSON showing how to wire servers into Claude Desktop/Code.[7]
    - Great for understanding **tool, resource, prompt** definitions and how to expose them as “skills”.

- `modelcontextprotocol/example-remote-server` – *canonical MCP remote server*  
  - URL: https://github.com/modelcontextprotocol/example-remote-server[8]
  - Why it’s useful:  
    - Full TypeScript MCP server showing tools, resources, prompts, and auth.[8]
    - Contains `examples/` and `configs/` showing client usage and config for integration.[8]
    - Strong foundation for building your own **skill‑oriented MCP servers** for Claude Code.

- `ever-works/awesome-mcp-servers` – *curated MCP servers list*  
  - URL: https://github.com/ever-works/awesome-mcp-servers[9]
  - Why it’s useful:  
    - Catalog of third‑party MCP servers (Pulumi, cloud, storage, etc.).[9]
    - Good for inspiration on **what kinds of tools** people expose and how they describe them.

***

## Claude Code internal examples

**4. Claude Code agent/skill examples in the official repo**

- `anthropics/claude-code` – *plugin dev / agent examples*  
  - Example file: `plugins/plugin-dev/skills/agent-development/examples/complete-agent-examples.md`[10]
  - Why it’s useful:  
    - Contains **production‑ready agent examples** (e.g., code review, refactor agents) with full frontmatter and instructions.[10]
    - Shows you Anthropic’s own patterns for **skills, hooks, and agent instructions**.

This is your reference for how Claude’s team intends agents/skills to be structured.

***

## How to use these with NotebookLM

1. **Create a notebook just for “Agent configs & skills”** and add as sources:  
   - `thkt/claude-config`[1]
   - `breeze4/claude-config`[2]
   - `agentsmd/agents.md`[3]
   - `github/awesome-copilot` AGENTS/skills/hooks docs[6][5]
   - `iddv/mcp-example`[7]
   - `modelcontextprotocol/example-remote-server`[8]
   - `anthropics/claude-code` agent examples file[10]

2. Then ask NotebookLM something like:  
   - “Extract and compare how these repos define **agent instructions, skills, hooks, and MCP servers**. Generalize into patterns for Claude Code CLI skills that:  
     – obey output formats,  
     – use hooks for validation,  
     – leverage MCP tools as ‘skills’,  
     – and use AGENTS.md/CLAUDE.md for project‑level instructions.”

That gives you a dense, repo‑backed pattern library aligned with everything we discussed today: Claude Code skills, output control, hooks, MCP, and agentic CLIs.

## Human

How can I get Claude Code to use git ingest for a repo in phases such that the output will go into notebooklm?

## Assistant

You won’t get a one‑shot “Claude Code → gitingest → perfect NotebookLM source” for a whole repo; you need a small pipeline and a bit of discipline. The good news is you can absolutely do this in phases so that each phase is NotebookLM‑friendly.

Below is the minimal practical workflow.

***

## 1. Decide your ingest *units*

You want **several smaller, high‑signal files**, not one giant dump.

Useful units:

- Repo‑level:  
  - `repo-map-and-index.md` (structure + key files + brief summaries)  
- Config/agent units:  
  - `.claude-and-agents.md` (CLAUDE.md, `.claude/**`, AGENTS.md, MCP configs)  
- Code units (per service or package):  
  - `service-a-core.md`, `service-b-core.md`, etc.  

Each unit should stay well under NotebookLM’s per‑source limits (which are quite high but you don’t want 200MB monsters anyway).[1][2]

***

## 2. Use Claude Code + git ingest in *scoped* passes

In a Claude Code terminal session inside the repo:

1. **Phase 1 – Structure & index**

   Ask Claude something like:

   > “Use git ingest or repository tools to build a **compact Markdown index** of this repo.  
   > Include:  
   > – A directory tree (paths only, depth 2–3).  
   > – For key directories (src, apps, packages, services, docs, infra), list the most important files with 1–3 sentence summaries based on their content.  
   > – Explicitly include contents of: `CLAUDE.md`, `.claude/**`, `AGENTS.md`, `.mcp.json`, and any other agent/config files.  
   > Save this as `notebooklm/repo-index.md`.”

   This uses Claude’s repo‑awareness instead of a blind gitingest dump, and keeps the file small and dense.

2. **Phase 2 – Agent/config slice**

   In a separate Claude Code conversation (same repo):

   > “Create a Markdown file `notebooklm/agent-configs.md` that contains:  
   > – Full content of all `.claude/**` files,  
   > – `CLAUDE.md` (or AGENTS.md),  
   > – MCP configs (`.mcp.json`, MCP client configs),  
   > with a short heading and 1–2 sentence description before each file.”

   This gives you a **single, curated agent/skills/config source** for NotebookLM.

3. **Phase 3 – Per‑service code slices**

   For each important service:

   > “For the `services/my-service` directory, create `notebooklm/my-service.md` that:  
   > – Shows the directory tree.  
   > – Inlines only the key files (entrypoints, core modules, main handlers).  
   > – For other files, include just path + brief summary, not full content.  
   > Keep the whole file under ~50k–100k words (summarize if needed).”

   Claude Code can read the files and write these Markdown digests; you’re just constraining scope.

***

## 3. Avoid raw “full repo” gitingest dumps

If you still want to use gitingest:

- Run it with **path filters** or **sub‑directories** only.  
- Then ask Claude Code:

  > “This gitingest output is too big for NotebookLM. Split it into logical parts (repo index, configs, service‑level chunks), each as separate Markdown files under `notebooklm/` and keep them well below typical NotebookLM size limits.”

Claude can refactor the gitingest text into multiple smaller `.md` files that are safe to upload.

***

## 4. Upload to NotebookLM in phases

Once Claude has produced `notebooklm/*.md`:

1. Add `repo-index.md` as a source.  
2. Add `agent-configs.md` as a source.  
3. Add each `*-core.md` / per‑service file as needed.  

You now have:

- A **map** (index)  
- A **config/agent slice**  
- A few **focused code slices**

All are tailored for your deep‑research prompts and won’t hit size limits.

***

## 5. Optional: teach Claude Code the workflow as a skill

You can encode this as a Claude Code skill:

- A SKILL.md like “prepare-notebooklm-slices” whose instructions are roughly:

  - Build `notebooklm/repo-index.md`.  
  - Build `notebooklm/agent-configs.md`.  
  - For each service, build `notebooklm/<service>.md` with constraints.

Then whenever you want a repo ready for NotebookLM, you run that skill once and upload the outputs.

If you want, next step can be: a concrete SKILL.md template for “prepare-notebooklm-slices” that you can drop into `.claude/skills/`.

## Human

I'm sure we can automate the phases in a skill.
Why wouldn't we want to pull down the entire repo if we, to phase 1 and it's too big, then we can break phase 1 into phase 1a and phase 1b. Can we do that automatically?
I'm not married to Git and Jest. We can use other CLI tools if that's going to give us a better outcome, smaller size, etc.

## Assistant

You’re right: this can be automated in a Claude Code skill, and you don’t need to be tied to gitingest. The key is: **let Claude orchestrate a “slice + split” pipeline with hard size guards**, instead of trying to dump everything at once.

Below is the high‑level design; you can then encode it as a skill.

***

## Why not “pull entire repo” in one go?

You *can* conceptually pull the whole thing, but:

- NotebookLM has **per‑source limits**; one giant dump is fragile and hard to reuse.[1][2]
- A flat dump is **low‑signal** for your use cases (you care more about configs, skills, MCP, docs, key flows than every test stub).  
- Splitting *after* producing one huge file is wasteful; better to **enforce slice boundaries at generation time**.

So the better pattern is: *traverse everything, but emit multiple bounded artifacts*.

***

## Skill design: automated, phased slicing (with auto‑splitting)

Design a skill like `prepare-notebooklm-slices` that:

1. **Scans the repo once**  
   - Use Claude Code’s tools (`ReadDirectory`, `Grep`, etc.) to build an in‑memory **file list with sizes** and basic categories (docs, configs, code, tests).  
   - This pass is cheap and doesn’t generate NotebookLM input yet.

2. **Defines target slices with hard size budgets**

   For example:

   - Slice `repo-index` – target ≤ ~100k words.  
   - Slice `agent-configs` – target ≤ ~50k words.  
   - Slice `service-X` – target ≤ ~50k words each.

   The skill instructions should make Claude treat these as **“buckets with budgets”** and include guidance like: summarize aggressively when near the limit, and prefer *structure + key files* over raw code.

3. **Emits each slice separately (Phase 1, 1a, 1b…)**

   Inside the skill:

   - For `repo-index`:
     - Start building the tree + summaries.  
     - Once a threshold is reached (e.g., “roughly N lines / tokens”), Claude **starts a new file**, e.g.:  
       - `notebooklm/repo-index-part-1.md`  
       - `notebooklm/repo-index-part-2.md`  

   You can encode this logic textually:

   > “If the repo index content approaches a size where it would be unwieldy for a single NotebookLM source (roughly ≥ X lines or Y characters), automatically create a new file and continue (e.g., `repo-index-part-2.md`). Prioritize keeping each file reasonably small and self‑contained.”

   Claude is very capable of following “when size looks big, start a new file” rules, especially when you give explicit thresholds and filenames.

4. **Category‑specific rules**

   Within the skill:

   - **Agent/config slice**  
     - Always inline full content of: `CLAUDE.md`, `AGENTS.md`, `.claude/**`, `.mcp.json`, hook and skill definitions.  
     - If over budget, split by category:  
       - `agent-configs-core.md` (CLAUDE.md, AGENTS.md, global settings)  
       - `agent-configs-skills.md` (SKILL.md, commands, hooks)  

   - **Code slices**  
     - For each service/package, include:  
       - Directory tree + short summaries.  
       - Full code only for entrypoints / core modules.  
       - Summaries for the rest.  
     - Auto‑split per service if needed: `service-X-core-part-1.md`, etc.

This all can live as **natural‑language rules** in the SKILL.md; no external CLI needed beyond the Claude tools.

***

## Replacing gitingest: Claude‑first workflow

Given your openness to dropping gitingest, a better pipeline is:

1. **Define the skill in `.claude/skills/prepare-notebooklm-slices/SKILL.md`** with:
   - Goal: produce a set of `notebooklm/*.md` files each under a rough size budget.  
   - Steps: scan repo, categorize files, generate slices with auto‑splitting, prioritize configs/prompts/skills/MCP.  
   - Format: explicit filenames and structure.

2. **Invoke the skill from the Claude Code CLI** in the repo root.  
3. **Upload the resulting `notebooklm/*.md` files** as separate sources to NotebookLM.

You don’t actually need any external CLI beyond `claude` itself; the toolset Claude Code already exposes (read dir, read file, write file) is sufficient.

If you want, next step can be a concrete `SKILL.md` skeleton that encodes this multi‑phase + auto‑split behavior in a way Claude Code is likely to follow.

## Human

"A flat dump is low‑signal for your use cases (you care more about configs, skills, MCP, docs, key flows than every test stub)."

You are correct. I don't care about test files unless they're somehow relevant or any garbage that might be in the repo.

---

I was thinking it might be a little wasteful for tokens not to use a CLI tool like Git and Jest.

## Assistant

You’re thinking about this the right way: you want **signal‑dense slices**, not a full textual mirror, and you don’t want to waste Claude tokens re‑implementing what a CLI tool already does well.

Here’s a minimal, token‑efficient strategy that respects both:

***

## 1. Use CLI tools for *listing and filtering*, not dumping

Let the CLI do what it’s good at: **enumerate and pre‑filter files**, then let Claude selectively ingest.

Examples:

- Get a high‑signal file list (no tests/garbage):

  ```bash
  git ls-files \
    | rg -v '(^|/)tests?/|(__snapshots__|__mocks__)' \
    | rg -v '\.(png|jpg|jpeg|gif|lock|bin)$' \
    > notebooklm/file-list.txt
  ```

  This gives Claude a **focused manifest** instead of full content.

- Separate categories:

  ```bash
  # Agent/config
  git ls-files \
    | rg '(CLAUDE\.md|AGENTS\.md|^\.claude/|\.mcp\.json)' \
    > notebooklm/agent-config-files.txt

  # Docs
  git ls-files docs '**/*.md' '**/*.adoc' \
    > notebooklm/doc-files.txt
  ```

Then Claude Code reads `notebooklm/*.txt` and decides what to actually open and summarize. That’s much cheaper than pouring the entire repo text into the model.

***

## 2. Let Claude generate only *curated Markdown slices* from those lists

In a Claude Code session:

> “Read `notebooklm/file-list.txt` and the specific lists for agent config and docs.  
> For each category, open only the most relevant files and build:  
> - `notebooklm/repo-index.md` – directory tree + 1–3 sentence summaries for important files only.  
> - `notebooklm/agent-configs.md` – full content of CLAUDE.md, AGENTS.md, `.claude/**`, MCP configs, with short headings.  
> - `notebooklm/docs-core.md` – key design/architecture docs (no boilerplate).  
> Do **not** inline tests or obvious boilerplate unless they illustrate important patterns.”

This way:

- The CLI did the **heavy lifting** of selection.  
- Claude only burns tokens on **reading and summarizing the interesting subset**.

***

## 3. Wrap that in a Claude Code skill (but still lean on the CLI)

Your skill doesn’t have to replace the CLI; it can **assume** those file lists exist, or even invoke the CLI:

- SKILL.md (high level):

  - Run shell commands to generate `file-list.txt`, `agent-config-files.txt`, `doc-files.txt`.  
  - Use them to drive the Markdown slice creation as above.  

You get the best of both:

- `git` / `rg` filter the repo cheaply.  
- Claude generates **NotebookLM‑ready, high‑signal artifacts**.

***

## 4. Why this is not token‑wasteful

- You’re not asking Claude to re‑discover the file tree; `git ls-files` does it.  
- You’re not asking it to summarize tests and junk; the CLI filters those out up front.  
- You’re not dumping the repo; you’re only feeding in **curated chunks** you chose (config, docs, key flows).

That’s about as token‑efficient as you can get while still having Claude understand the repo well enough to help build skills, MCPs, prompts, and NotebookLM slices.

If you want, next step can be a concrete SKILL.md that explicitly says “call these shell commands, then turn the resulting lists into `notebooklm/*.md` files.”

## Human

One last thing about token efficiency. I'm not too concerned about token efficiency for Notebook LM. It's more about token efficiency for Claude Code. So if we use tools that preserve quality while protecting Claude Code, then I would be in favor of that. But again, I'm not married to it.

## Assistant

For your goals, it’s worth *spending* Claude Code tokens on the right things and offloading everything else to cheap CLIs.

Here’s how to think about it.

***

## Where Claude Code tokens are worth it

Use Claude Code aggressively for:

- **Understanding + summarizing**  
  - Reading key files and producing:  
    - repo map and architecture narratives,  
    - patterns in skills/hooks/MCP,  
    - “this is how this repo wants agents to behave.”
- **Designing artifacts**  
  - SKILL.md, hooks, CLAUDE.md/AGENTS.md, MCP prompt specs.  
  - Output‑style definitions and report templates.
- **Selective code inspection**  
  - Core flows, tricky logic, cross‑file behavior – not every util/test.

Those are high‑leverage uses; the tokens convert to persistent assets and better skills.

***

## Where to shield Claude Code with tools

Use CLI tools (or tiny Python scripts) whenever the work is:

- **Mechanical enumeration / filtering**  
  - Listing files, excluding tests/garbage, computing sizes, globbing patterns.  
- **Bulk text transformation**  
  - Concatenating files, splitting by size, moving outputs into `notebooklm/`.  
- **Schema validation / sanity checks**  
  - JSON schema validation, Markdown header checks, “did all required sections appear?”.

This keeps Claude from burning tokens on drudge work and lets it focus on reasoning and design.

***

## Practical pattern for you

Given your priorities:

- Keep the **CLI pre‑filter + Claude slice‑builder** pattern:  
  - `git/rg` to build high‑signal file lists.  
  - Claude Code to open only what matters and turn it into NotebookLM‑ready artifacts + skills/configs.
- Don’t worry about NotebookLM tokens; treat that side as “cheap analysis on already‑curated inputs.”
- When in doubt: if a step can be **expressed as a deterministic shell/Python script that doesn’t need judgment**, do it outside Claude Code; if it needs **judgment, pattern extraction, or design**, let Claude handle it.

If you want, next step can be: a concrete repo “prep skill” that explicitly mixes shell commands (for selection) with Claude reasoning (for summarization + config generation).

## Human

Perfect. Please give me an implementation plan and prompt I can give to a simpler LLM that will do the implementation and skill creation.

## Assistant

Here’s a concise implementation plan plus a single prompt you can hand to a “simple” LLM (Claude Code itself, or another coder) to implement the repo‑prep skill.

***

## 1. Implementation plan (what the LLM should build)

Goal: Implement a **Claude Code skill** (and a tiny shell helper) that:

- Uses **CLI tools** to pre‑filter the repo (no tests/garbage).  
- Uses **Claude Code** to read only relevant files and generate **NotebookLM‑ready Markdown slices** under `notebooklm/`.  
- Produces high‑signal artifacts: repo index, agent/config slice, key services.

Phases:

1. **Create `notebooklm/` structure**

   - Ensure `notebooklm/` directory exists at repo root.  
   - Add a short `notebooklm/README.md` explaining the slices.

2. **Add helper shell script for file lists**

   Create `scripts/build-notebooklm-filelists.sh` (or similar) that:

   - Generates a global high‑signal file list (excluding tests/junk):

     ```bash
     mkdir -p notebooklm

     git ls-files \
       | rg -v '(^|/)tests?/|(__snapshots__|__mocks__)' \
       | rg -v '\.(png|jpg|jpeg|gif|lock|bin)$' \
       > notebooklm/file-list.txt
     ```

   - Generates **agent/config file list**:

     ```bash
     git ls-files \
       | rg '(CLAUDE\.md|AGENTS\.md|^\.claude/|\.mcp\.json)' \
       > notebooklm/agent-config-files.txt
     ```

   - Generates **docs file list**:

     ```bash
     git ls-files \
       | rg '^docs/|README' \
       > notebooklm/doc-files.txt
     ```

3. **Define the Claude Code skill**

   Create `.claude/skills/prepare-notebooklm-slices/SKILL.md` with:

   - **Goal**: From the file lists in `notebooklm/*.txt`, generate Markdown slices:

     - `notebooklm/repo-index-part-*.md` – high‑level structure + key file summaries.  
     - `notebooklm/agent-configs-part-*.md` – full content of agent/config files.  
     - `notebooklm/docs-core-part-*.md` – core docs and architecture notes.  
     - Optional: `notebooklm/<service>-core-part-*.md` for specific service dirs.

   - **Constraints**:

     - Each Markdown output file should stay “reasonable” in size (e.g., **≤ ~50k–100k words**; use heuristics like line count / “if this looks big, start next part”).  
     - Prefer **structure + summaries** over raw code, except for critical files (configs, prompts, main entrypoints).  
     - Do **not** inline tests or obvious boilerplate unless explicitly interesting.

   - **Steps** encoded in natural language:

     1. Run `scripts/build-notebooklm-filelists.sh`.  
     2. Read the file lists and, for each list, open selected files.  
     3. Generate the slices described above.  
     4. If a slice is getting long, automatically continue in `*-part-2.md`, `*-part-3.md`, etc.  
     5. Confirm in the final message which files were created and what each contains.

4. **(Optional) Add a small config note**

   - In `CLAUDE.md`, add a short section “NotebookLM prep” explaining the skill and how to invoke it.

5. **Usage**

   - From repo root:  
     - Run the skill via Claude Code (or just follow the SKILL.md steps):  
       - `claude` → invoke skill `prepare-notebooklm-slices`.  
   - Then upload `notebooklm/*.md` into NotebookLM as separate sources.

***

## 2. Prompt for a simpler LLM to implement everything

You can paste this directly into a coding‑oriented LLM:

> You are a senior developer assistant.  
> I want you to implement a **Claude Code + CLI workflow** that prepares any repo for ingestion into **NotebookLM** by creating high‑signal, size‑bounded Markdown slices instead of a single giant dump.  
> 
> **Goals**  
> - Use cheap CLI tools for mechanical work (listing/filtering files).  
> - Use Claude Code for judgment and summarization.  
> - Output multiple Markdown files under `notebooklm/` that I can upload to NotebookLM:  
>   - `repo-index-part-*.md` – directory tree + key file summaries.  
>   - `agent-configs-part-*.md` – Claude/agent/MCP configs.  
>   - `docs-core-part-*.md` – key docs/design/architecture.  
>   - Optionally, `service-*-core-part-*.md` – per‑service core code summaries.  
> - Each slice should avoid tests/junk and stay within a reasonable size (if it grows too large, start a new `*-part-2.md` file automatically).  
> 
> **Step 1 – Shell helper for file lists**  
> Create a POSIX‑compatible shell script at `scripts/build-notebooklm-filelists.sh` that:  
> 1) Ensures `notebooklm/` exists.  
> 2) Writes a **global high‑signal file list** to `notebooklm/file-list.txt` using `git ls-files` and `rg` (ripgrep):  
>    - Exclude tests (`tests`, `__tests__`, `__snapshots__`, `__mocks__`) and obvious binary/asset files (`*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.lock`, `*.bin`).  
> 3) Writes an **agent/config list** to `notebooklm/agent-config-files.txt` containing matches for:  
>    - `CLAUDE.md`, `AGENTS.md`, any files under `.claude/`, `.mcp.json`.  
> 4) Writes a **docs file list** to `notebooklm/doc-files.txt` containing `docs/**` and `README*` files.  
> Make the script idempotent and add `set -euo pipefail`.  
> 
> **Step 2 – Claude Code skill definition**  
> Create `.claude/skills/prepare-notebooklm-slices/SKILL.md` that:  
> - States the goal: “Prepare NotebookLM‑ready Markdown slices for this repo, using the file lists in `notebooklm/*.txt`.”  
> - Instructs Claude Code to:  
>   1) Run `scripts/build-notebooklm-filelists.sh`.  
>   2) Read the three file‑list files.  
>   3) For each list, open the relevant files and generate Markdown outputs under `notebooklm/` as follows:  
>      - `repo-index-part-1.md`, `repo-index-part-2.md`, …:  
>        – Show a directory tree and per‑file **1–3 sentence summaries** for important files listed in `file-list.txt`.  
>        – Inline full content only for truly critical files (e.g., main entrypoints), otherwise summarize.  
>      - `agent-configs-part-1.md`, etc.:  
>        – Inline full content of `CLAUDE.md`, `AGENTS.md`, `.claude/**`, `.mcp.json`, and any hook/skill definitions.  
>        – Group logically (global config, skills, hooks, MCP).  
>      - `docs-core-part-1.md`, etc.:  
>        – Inline key docs (architecture, design, ADRs) and summarize minor docs.  
>   4) Apply a **size heuristic**:  
>      - If a given output file is becoming large (e.g., very long or clearly beyond what would be pleasant to read), start a new file with `-part-2.md`, `-part-3.md`, etc., and continue.  
>   5) Avoid inlining tests or obvious boilerplate unless it clearly matters for understanding the system.  
>   6) At the end, output a brief summary listing:  
>      - Which `notebooklm/*.md` files were created.  
>      - What each one contains and how it should be used in NotebookLM.  
> 
> **Step 3 – Nice‑to‑have**  
> - Add a section to `CLAUDE.md` called “NotebookLM Prep” documenting:  
>   - The existence of the `prepare-notebooklm-slices` skill.  
>   - How to invoke it from Claude Code.  
> 
> **What to return in your answer**  
> - The full contents of `scripts/build-notebooklm-filelists.sh`.  
> - The full contents of `.claude/skills/prepare-notebooklm-slices/SKILL.md`.  
> - Any small additions you suggest for `CLAUDE.md` to document this workflow.  
> 
> Follow best practices for clarity and robustness. Use comments sparingly, only where they add real value.
