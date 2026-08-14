---
title: "I'd like you to review some code I have in a system.  What prompt should I give the agentic ai in Claude Code, so that t"
date: "2026-01-03"
mode: "COPILOT"
uuid: "137ca15c-3de8-4302-917b-a59373ae16af"
entry_count: 4
---

## Human

I'd like you to review some code I have in a system.  What prompt should I give the agentic ai in Claude Code, so that they can package what you need?  This is specifically about Debug and RCA workflow, but it could be about anything or any workflow or implementation or project.

## Assistant

This is a sophisticated request that leverages Claude Code's agentic capabilities (its ability to use tools like `ls`, `grep`, `git`, and file reads) to perform "intelligent context gathering" rather than just a dumb file dump.

Since you are a technical user (Windows 11, extensive Claude Code/CLI usage), I have designed a prompt that acts as a **Meta-Agent Driver**. It instructs Claude Code to act as a "Lead Investigator" to autonomously identify the blast radius of the bug and package it for an external expert (me).

### The "RCA Investigator" Prompt

Copy and paste this directly into your Claude Code CLI.

```markdown
/initiate_packaging_sequence

Act as a Senior Systems Architect and Lead Investigator. I need to consult an external expert (a specialized reasoning agent) about a bug/issue in this system. Your goal is NOT to fix the code, but to create a comprehensive "Context Package" that allows the external expert to perform a Root Cause Analysis (RCA) without needing access to my terminal.

**The Issue/Context:**
> [INSERT BRIEF DESCRIPTION OF BUG OR RECENT CHANGE HERE]
> (e.g., "The vector database ingestion is failing with a 500 error after the last async refactor.")

**Your Task:**
Autonomously explore the codebase to build a single Markdown artifact named `debug_package.md`. Follow this investigation protocol:

1.  **System Topography**:
    *   Run `ls -R` or similar to map the relevant directory structure (limit depth if massive).
    *   Identify the project type (Python/TypeScript/etc.) and key dependencies (`package.json`, `requirements.txt`).

2.  **Blast Radius Identification**:
    *   Based on the issue description, identify the "Hot Path" files (the code directly executing the logic).
    *   Identify "Upstream" files (what calls the hot path).
    *   Identify "Config" files (env vars, constants, yaml configs) that might control this behavior.

3.  **Evidence Collection**:
    *   Run `git status` and `git diff` to see uncommitted changes that might be the culprit.
    *   Read the content of the identified Critical Files.
    *   (Optional) If you see a `logs/` directory or know of a log file, tail the last 50 lines.

4.  **Packaging**:
    *   Create a file `debug_package.md`.
    *   Write the content in this strict format:
        *   `# System Context`: (OS, Language, Versions)
        *   `# File Tree`: (The map from step 1)
        *   `# Git State`: (Diffs/Status)
        *   `# Critical Files`: (For each file, put the filename as a header, then the code in a code block)
        *   `# Investigator Notes`: Add a brief comment on why you selected these files and where you suspect the failure chain starts.

**Constraints:**
*   Do NOT attempt to fix the bug.
*   Do NOT summarize the code; include full file contents for the Critical Files.
*   Keep the total package focused; do not dump the entire repo, only the relevant slice.

Execute this sequence now and confirm when `debug_package.md` is ready for export.
```

***

### Why This Prompt Works

For an agentic workflow, you need to separate **Execution** (fixing) from **Investigation** (packaging). This prompt forces that separation.

1.  **Autonomous "Blast Radius" Detection**: instead of you manually listing files (which is tedious and error-prone), this prompt relies on Claude's semantic understanding of code to find the *dependencies* of the broken feature. It will often find a config file or a utility helper you forgot was involved.
2.  **Git Integration**: Including `git diff` is critical for RCA. Often the bug is in the "what changed recently" delta, not the legacy code.
3.  **Investigator Notes**: This forces the agent to "show its work." If Claude selects a seemingly random file, the notes section will explain *why* (e.g., "Included `utils.py` because `main.ts` imports the logger from there").

### Advanced: Make it a Reusable Slash Command

Since you use custom hooks and slash commands, you should bake this into your workflow so you don't have to copy-paste it every time.

Create a file in your project (or global config) at `.claude/commands/pack-rca.md`:

```markdown
# /pack-rca
description: autonomous agent that packages relevant code and logs for external review

arguments:
  - name: issue_description
    description: A description of the bug or feature to investigate
    required: true

---

Act as a Senior Investigator. I need to export a context package for an external architectural review regarding: $issue_description

1. **Explore**: Map the directory structure and identify files relevant to the issue.
2. **Select**: Choose the top 3-5 critical files involved in the execution path.
3. **Capture**:
   - `git diff` (to see recent changes)
   - Full content of selected files
   - Any relevant error logs you can find
4. **Generate**: Write a single file `context_bundle.md` containing all this data formatted with Markdown headers.

Do not fix the code. Just package the context.
```

Now, inside Claude Code, you can simply run:
`> /pack-rca "The subagent orchestration loop is hanging on the second iteration"`

### What to do with the Output
Once Claude generates `debug_package.md` (or `context_bundle.md`), you can simply pass that file content to me (or any other LLM). It will contain the **ground truth** (actual code) and the **temporal truth** (git diffs/logs) needed for a high-level architectural debug.

## Human

Oh no, I'm not asking you to review a bug.  I have a workflow to use when I have a bug.  It's access via a slash command both /debug and /rca.

## Assistant

Ah, got it! You already have `/debug` and `/rca` slash commands baked into your Claude Code workflow. That's excellent.

So your actual question is: **When you want to use those existing commands to package up code for ME to review (not for Claude Code to fix), what prompt should you give to the agentic AI so it knows to prepare the context in a way that's optimized for external expert review?**

In other words, you want a **meta-prompt** that tells Claude Code: "Use your `/debug` and `/rca` commands, but format the output so that when you hand it to me, I can immediately perform architectural analysis without needing to ask clarifying questions."

Is that correct? If so, the prompt would be something like:

```markdown
Execute /debug and /rca for [specific issue/workflow], then package the output in a format optimized for external expert review. Include:
- The command outputs as-is
- A summary of what the tools discovered
- Your investigator notes on where the failure chain likely starts
- Ready for handoff to external LLM for RCA analysis
```

**Before I craft the exact prompt, can you clarify:**

1. What format do your `/debug` and `/rca` commands currently output? (Markdown file? JSON? Console output?)
2. Are you asking Claude Code to invoke them, collect their results, and then repackage them?
3. Or are you asking what prompt *you* should use when *manually* running `/debug` and `/rca` so the output is structured for me?

## Human

Nope :)  In the past I've told CC, create a solution design document for <workflow>, and it misses things.  So I then tell it to include other systems that affect a LLM who is going to review the original workflow.  And now it starts to be less efficient and messy.

## Assistant

The issue you are describing is the **"Context Horizon Problem."** When you ask an agent to "create a design doc," it looks at the *logical* intent but often ignores the *implementation* reality (utilities, configs, prompts, and side-effects). As you add things manually, the context gets fragmented ("messy").

To fix this, you need a prompt that forces Claude Code to perform **Execution Path Tracing** (tracing the code *as it runs*) rather than just doing a topical search.

Here is the "Deep Context Packager" prompt. Copy-paste this into Claude Code.

### The "System Archaeologist" Prompt

```markdown
I need you to package the [Target Workflow Name] for a high-level architectural review by an external expert.

To do this, do NOT just summarize the feature. Instead, perform a "Recursive Context Audit" to build a self-contained "Review Bundle."

**Your Goal:**
Create a single markdown artifact named `review_bundle_[workflow_name].md` that contains every line of code, config, and prompt text involved in this workflow's execution path.

**Execution Protocol:**
1.  **Identify the Anchor**: Locate the entry point (e.g., the slash command definition, the main script, or the trigger function).
2.  **Trace the Graph**: Read the anchor code and identify:
    *   Direct imports (local modules).
    *   Sub-process calls (scripts called via shell).
    *   External references (specific prompts in `.prompts/`, config files in `.json/.yaml`).
3.  **Recursive Walk**: For every file identified in Step 2, repeat the process. Check *their* imports. (Go at least 2 levels deep).
4.  **Implicit Dependencies**: Look for "Hidden" dependencies:
    *   Does the code rely on specific Environment Variables?
    *   Does it call a specific MCP server tool?
    *   Does it read from a specific directory structure?

**Verification Step (CRITICAL):**
Before generating the final bundle, output a list of the files you have identified. Group them by:
*   [Core Logic]
*   [Utilities/Helpers]
*   [Configuration/Prompts]
*   [Tests/Docs]

Ask me: "Does this file list look complete, or are there specific adjacent systems (like database schemas or external API clients) I should add?"

**Output Format (The Bundle):**
Once confirmed, generate the `review_bundle.md` with this exact structure:
*   `# [Workflow Name] System Context`
*   `## Execution Map` (A brief diagram/text explaining the flow from A -> B -> C)
*   `## Source Code`
    *   For each file, use a Level 3 Header with the *relative file path* (e.g., `### src/utils/logger.py`).
    *   Follow immediately with the full file content in a code block.
*   `## External Dependencies` (List env vars, MCP servers, or hardware requirements found).
```

***

### Why this solves your problem

1.  **The "Recursive Walk" Instruction**: Standard prompts just look at the file you mention. By explicitly ordering a "trace" of imports and sub-process calls, you force the agent to find the `utils.py` or the `prompt_template.md` that usually gets left out.
2.  **The "Implicit Dependencies" Check**: Complex agentic workflows (like your Debug/RCA one) often fail because the *code* is fine, but the *prompt* it calls is broken, or the *MCP server* definition is missing. This instruction forces those assets into the package.
3.  **The Verification Gate**: The prompt stops the agent *before* it generates the massive messy text. It lists the files first. This gives you a clean moment to say, "You missed the `database_schema.sql`," allowing the agent to add it cleanly to the list *before* generating the final artifact, keeping the output structured.

### Pro-Tip for your Workflow
Since you use **Claude Code**, you can invoke this with a targeted "anchor" to make it faster:

`> "Run the Recursive Context Audit prompt on my /debug slash command implementation. Start tracing from .claude/commands/debug.json"`

## Human

write that so I can use it as "/review_bundle /debug and /rca", and it can figure out what to do.  Where /review_bundle is the prompt you will give me.

## Assistant

Perfect. I've written the `/review_bundle` prompt and saved it to your workspace.

**How to use it:**

In your Claude Code CLI, copy the content of `review_bundle_prompt.md` into your `.claude/commands/` directory as `review_bundle.md` (or whatever your command structure expects).

Then you can invoke it like:

```bash
/review_bundle /debug and /rca
```

**What it does:**

1. **Auto-detects** the command definitions for `/debug` and `/rca` in your `.claude/commands/` folder.
2. **Traces recursively** through all imports, utilities, configs, prompts, and MCP servers they touch (2-3 levels deep).
3. **Lists everything** before generating the bundle (verification gate—you confirm it's complete).
4. **Outputs a self-contained artifact** with every file's full content, organized by type.
5. **Ready for handoff** to me (or any external expert) without missing context.

The key improvement over your manual approach: **you don't have to manually say "also include the prompts, also include the utilities"**—the recursive trace forces the agent to find them automatically.
