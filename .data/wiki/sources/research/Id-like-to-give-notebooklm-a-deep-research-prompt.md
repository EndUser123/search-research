<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I'd like to give notebooklm a deep research prompt that surfaces all the good info you did.  I'm thinking of something like: "Find everything about using the gemini-cli, and show examples for using to do deep research, video analysis, and all about the gemini llm models.  I'd like this to be a one stop shop on using the gemini models, and the cli, via claude code.  So we need to include mcps, skills, agents, anything that anyone has done that is useful.  Even how to use it with hooks.  Working code examples. "

Please make it great and include all the great stuff you found, and all the great stuff that I don't know about but wish I did.

Here’s a **polished, “drop‑into NotebookLM”**‑style deep‑research prompt that’s designed to be a **one‑stop shop** for:

- `gemini-cli`,
- Gemini models,
- MCP‑/skills‑/agents‑patterns,
- hooks,
- and working code examples,
all framed through a **Claude Code / terminal‑coding lens**.

You can paste this into NotebookLM and let it scrape and synthesize.

***

### NotebookLM research prompt: “Gemini‑CLI + Gemini models, via Claude Code”

> You are a **deep‑technical research assistant** focused on **Google Gemini** and **Gemini CLI**. Your goal is to build a **single, comprehensive “one‑stop shop” guide** for:
>
> 1. **Using `gemini-cli`**,
> 2. **Using Gemini models** (Gemini 1.5, Gemini 2.x, Gemini‑Pro, Gemini‑Flames, and the video‑analysis, embedded‑search, and agents‑stack variants),
> 3. **Integrating everything with Claude Code** (terminal, MCP servers, skills, hooks, agents),
> 4. **Working examples** of deep research, video analysis, and code‑assisted workflows that combine **Gemini CLI** and **Claude Code**.
>
> Follow this structure:
>
> ---
>
> \#\#\# 1. Summarize Gemini models and how they differ
>
> - Identify the main Gemini‑family models (e.g., Gemini 1.5 Pro, Gemini 2.0 / 2.5 variants, Gemini‑Flames, Gemini‑Flash, Gemini‑NonPro) and their key capabilities:
>   - Context length, token‑rate limits, vision, code‑generation, and multi‑modal capabilities.
>   - When to prefer one model over another (e.g., “Gemini‑Flash for fast multi‑turn iteration, Gemini‑Pro for deep context”; which ones are free vs. paid in Gemini Code Assist / Google Workspace).
> - Cover **Gemini‑for‑code** vs **Gemini‑for‑agents** vs **Gemini‑for‑video** usage patterns.
> - Explain **Gemini‑Code‑Assist**’s editor / web‑interface vs the `gemini-cli` vs using Gemini via Python SDKs.
>
> ---
>
> \#\#\# 2. Deeply research `gemini-cli`: what it is, how it works, and how it’s used
>
> - **Core behavior and mode**
>   - Describe how `gemini-cli` behaves as a **terminal‑based agent** that can:
>     - Generate, explain, and refactor code.
>     - Review diffs, suggest improvements, and run locally defined tools.
>     - Interact with Gemini models directly without leaving the shell.
>   - Identify the typical command structure:
>     - `gemini [flags] --prompt '...'`, `gemini attach FILE`, `gemini search`‑style patterns, and long‑running “headless” / script‑driven usage.
> - **Relationship to Gemini Code Assist**
>   - Explain how `gemini-cli` differs from the **Gemini Code Assist** IDE / VS Code experience:
>     - Where the power comes from (context‑aware diffs, repo‑wide awareness, built‑in diffs, web‑fetching).
>     - Strengths of the CLI vs. IDE‑based workflows.
> - **Configuration and auth**
>   - Show how `gemini-cli` is configured:
>     - Environment‑variables vs config files (`GEMINI_API_KEY`, `GEMINI_CONFIG`, profile‑level setup).
>     - Default model selection, context‑windows, and rate‑limit handling.
>   - Point out any CLI flags or config files that let you:
>     - Swap models per call,
>     - Increase/decrease context,
>     - Enable/disable web‑fetching,
>     - Log or cache requests.
>
> ---
>
> \#\#\# 3. Examples of `gemini-cli` for deep research, video analysis, and code‑enhanced workflows
>
> Gather and synthesize **real‑world working examples**, ideally with `gemini-cli` commands and their outputs, for:
>
> 1. **Deep research workflows**
>   - `gemini-cli` used to:
>     - Scan a repo, summarize it, and propose a refactor.
>     - Read a markdown or docs directory and answer complex “how does this work?” questions.
>     - Combine local context (e.g., `git diff`) with web‑fetch‑enabled queries, then summarize trade‑offs.
>   - Provide concrete command examples:
>     - `gemini --prompt "Explain the authentication flow in this repo" --files 'src/auth/**/*.ts'`
>     - `git diff $BRANCH | gemini --prompt "Review these changes and suggest improvements"`
>     - `find . -name '*.md' | xargs cat | gemini --prompt "Create a beginner guide based on these docs"`
>
> 2. **Video analysis use cases**
>   - Gemini‑video‑stack examples (e.g., Gemini‑Flames, Gemini‑video‑CLI, or Gemini‑agent‑stacks) that:
>     - Accept a video URL or locally‑stored video,
>     - Extract key frames,
>     - Generate timestamps, summaries, or structured metadata (e.g., “each shot annotated with actions, entities, emotions”).
>   - If possible, show:
>     - How to run that via `gemini-cli` (or the underlying SDK) from the shell.
>     - How to pipe that into Claude Code for further analysis or summarization.
>
> 3. **Code‑assisted workflows (with Claude Code)**
>   - Show patterns where `gemini-cli`:
>     - Acts as a **“second‑opinion” reviewer** after Claude Code edits:
>       - `git diff | gemini --prompt "Security‑review this diff"`
>       - `bat src/**/*.py | gemini --prompt "Refactor for Python 3.11 idioms"`
>     - Serves as a **code‑generator** that writes boilerplate, then Claude Code refactors, tests, and ships it.
>     - Is used **inside an MCP‑style server** that routes queries from Claude Code to `gemini` / Gemini‑API, turning Gemini into an MCP‑tool.
>
> For each example, include:
> - Exact command line or shell script.
> - A short explanation of:
>   - What the example is doing,
>   - Why it’s useful,
>   - Where Gemini vs. Claude Code is stronger in that step.
>
> ---
>
> \#\#\# 4. Integrate Gemini‑CLI into Claude Code via MCP servers, skills, and agents
>
> Research **how people embed `gemini-cli` into Claude Code workflows** using:
>
> 1. **MCP‑servers**
>   - Find any **MCP‑server‑style projects** that wrap `gemini-cli` (or Gemini‑API) as an MCP‑tool for Claude Code.
>     - Describe their architecture:
>       - Does the server shell out to `gemini-cli` binary, or call Gemini API directly?
>       - What tools are exposed (e.g., `gemini_prompt`, `gemini_review_diff`, `gemini_security_audit`) and what their schemas look like.
- How they handle auth (e.g., env vars, config files, profiles).
>   - Provide working examples:
>     - `claude mcp add gemini-cli ...`
>     - Example `claude` sessions that call `gemini‑`‑prefixed tools.
>
> 2. **Skills**
>   - List **Claude Code skills** or GitHub Gists that formalize `gemini-cli` usage as a “Gemini‑adviser”:
>     - e.g., `jezweb/gemini-cli-advisor-for-claude-code`‑style projects.
>   - What slash‑commands they expose:
>     - e.g., `/gemini-plan`, `/gemini-review`, `/gemini-build-cycle`.
>   - How they teach Claude Code to:
>     - Defer to Gemini for code‑review or explanation,
>     - Fall back to Gemini when Claude is uncertain,
>     - Keep Gemini‑suggested changes in a separate “review backlog” that Claude can then adopt.
>
> 3. **Agents**
>   - Find any **multi‑agent flows** that:
>     - Use Gemini (CLI or API) as one agent and Claude Code as another.
>     - For example:
>       - Gemini does deep‑research / summarization,
>       - Claude Code turns that into scripts, configs, or PRs.
>   - Show how those agents are wired:
>     - Shell‑based orchestrations (e.g., `while` loops, `make` / `just` files, `tmux`‑scripts),
>     - MCP‑based orchestrators that route tasks between Claude Code and Gemini.
>
> For each of these three layers (MCP servers, skills, agents), include:
> - A concrete example setup (config file, command line, or `~/.claude`‑style snippet).
> - At least one **working code example** a user can run.
>
> ---
>
> \#\#\# 5. Use `gemini-cli` with hooks, shell‑wrappers, and safety‑guards
>
> Research **how people integrate `gemini-cli` into shell‑level hooks** and governance patterns, for example:
>
> 1. **Alias‑style wrappers**
>   - `alias gemini='...gemini-cli --flags...'` patterns that:
>     - Force certain models,
>     - Log every call,
>     - Inject context files or prompts.
>   - Example:
>     - `alias gemini-in-repo='gemini --files "$(find . -name \"*.md\" -print | paste -sd",")"'`.
>
> 2. **Pre‑/post‑hook patterns**
>   - `git` / `claude`‑style hooks that:
>     - Run `gemini-cli` as a reviewer before `git push` (e.g., automatically review diffs and block on detected critical issues).
>     - Run `gemini-cli` as a summarizer on each commit, writing a changelog snippet.
>
> 3. **Safety‑guard hooks**
>   - Guardrails that:
>     - Limit context sent to Gemini (e.g., truncate very long outputs),
>     - Block or redact sensitive patterns before they reach Gemini,
>     - Log or audit all Gemini queries for compliance.
>
> For each pattern, show:
> - A short hook script or alias.
> - A brief security / governance rationale.
>
> ---
>
> \#\#\# 6. Advanced patterns and “little‑known but powerful” tricks
>
> Surface **anything that “everyone should know, but often doesn’t”** about:
>
> - `gemini-cli`:
>   - Hidden flags or advanced options (e.g., streaming, caching, plugin‑style tooling, memory‑import‑processor‑style tools, memport, etc.).
>   - Tricks for:
>     - Quickly iterating on prompts via files, not CLI‑flags.
>     - Combining `gemini-cli` with `difftastic`, `ast-grep`, `rg`, `fd`, and `fzf` for multi‑tool workflows.
> - Gemini models:
>   - GPU‑/cost‑efficiency levers,
>   - How to prompt for “more structured JSON” vs “free‑text narrative”,
>   - How to use tool‑calling / structured outputs when interfacing via Python SDK.
> - Claude Code + Gemini combos:
>   - Shared‑context files,
>   - Session‑style “logs” where Gemini output is fed back into Claude Code’s context,
>   - Orchestration layers that:
>     - Route queries by domain (e.g., security‑related ones to Gemini‑security‑fine‑tuned agents, planning to Claude Code).
>
> Wherever possible, pair each “trick” with a **working one‑liner or short script** that someone can adapt immediately.
>
> ---
>
> \#\#\# 7. Output format
>
> - **Organize by the sections above** (Gemini models, `gemini-cli` basics, research‑/video‑/code examples, MCP‑skills‑agents, hooks, and advanced tricks).
> - Within each section:
>   - Start with a **concise summary** of the key ideas.
>   - Then, list **concrete, executable examples** (commands, scripts, config snippets).
> - Use code blocks for shell commands, config files, and sample prompts.
> - Avoid hand‑waving; if something is not clearly documented, say so and describe the closest available pattern instead.
>
> The final output should be **both a reference manual and a cookbook** that an engineer can:
> - **Read** to get a holistic understanding of how to use `gemini-cli` and Gemini models, and
> - **Execute** immediately via the provided examples, even in a Claude Code / terminal‑driven workflow.

***

If you want, I can also drop a **tiny `~/.claude` / MCP‑config** example that you can feed into this same NotebookLM context so it understands how your own Claude Code setup is wired into Gemini‑CLI‑style tools.

