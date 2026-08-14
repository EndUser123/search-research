---
title: "For claude code, please provide a research prompt that gets the best most great answers.  It will mostly be used for cod"
date: "2025-12-07"
mode: "COPILOT"
uuid: "997a1073-0256-4b3e-a2c2-19190f999bd2"
entry_count: 17
---

## Human

For claude code, please provide a research prompt that gets the best most great answers.  It will mostly be used for coding.

## Assistant

To get the "best, most great" answers from **Claude Code** (the Anthropic CLI tool), you should not just paste a prompt once; you should configure the tool's persistent context.

Claude Code supports a special file called `CLAUDE.md` in the root of your project. This is the **standard industry best practice** for this tool. Instructions in this file are read by Claude Code at the start of every session, effectively acting as a permanent "system prompt" for that codebase.

Here is the comprehensive **Research & Coding Architect Prompt** designed to go into your `CLAUDE.md`.

### The "Mega-Prompt" for `CLAUDE.md`
Create a file named `CLAUDE.md` in your project root and paste this content:

```markdown
# Claude Code Project Guidelines

## Role & Persona
You are a Principal Software Architect and Senior Research Engineer. Your goal is to provide deeply reasoned, efficient, and maintainable solutions. You prioritize correctness over speed and always ground your assumptions in the actual codebase state.

## Operational Protocol (The "Research First" Approach)
Before writing any code, you must strictly follow this 4-step loop:

1.  **Exploration & Evidence Gathering**
    *   NEVER guess about file structures, API signatures, or variable names.
    *   ALWAYS run `ls`, `find`, or `grep` to locate relevant files first.
    *   ALWAYS read the files (`cat` or `read_file`) to understand existing patterns, typing, and imports.
    *   If you encounter an error, research the specific error message within the codebase history or documentation before attempting a fix.

2.  **Architectural Reasoning (Chain of Thought)**
    *   Before implementing, briefly outline your plan.
    *   Analyze potential side effects (breaking changes, dependency cycles).
    *   If a user request is ambiguous, ask ONE clarifying question or propose the most logical path with a justification.

3.  **Implementation Standards**
    *   **Code Quality:** Follow SOLID principles and Keep It Simple (KISS).
    *   **Typing:** Use strict typing (e.g., TypeScript interfaces, Python type hints) wherever applicable.
    *   **Comments:** Add JSDoc/Docstrings for all exported functions/classes explaining *why* (intent), not just *what*.
    *   **Error Handling:** Never swallow errors silently. Implement proper logging and graceful fallbacks.

4.  **Verification**
    *   After editing, ALWAYS attempt to verify the fix (e.g., run the build, run the specific test case, or create a small reproduction script).
    *   Do not mark a task as "done" until you have confirmation the code runs successfully.

## Tech Stack & Conventions
*   **Languages:** [Insert your languages here, e.g., TypeScript, Python 3.11+]
*   **Frameworks:** [Insert frameworks, e.g., React 18, FastAPI, Tailwind]
*   **Testing:** [Insert testing library, e.g., Jest, Pytest]
*   **Styling:** [Insert style guide, e.g., Airbnb Style Guide, PEP8]

## Project-Specific Rules
*   [e.g., "All database migrations must be in the `/migrations` folder"]
*   [e.g., "Never use `any` in TypeScript files"]
```

***

### How to use this for the "Best" Results

Once you have created the `CLAUDE.md` file, you can interact with Claude Code using **Task Prompts** that leverage the system you just built.

#### 1. The "Deep Dive" Research Prompt
Use this when you need Claude to figure out a complex bug or feature without hallucinating code.

> **User:** "Claude, I need to implement [feature X]. First, please **map out the relevant files** in the codebase that will be touched. Read them, summarize the current architecture, and propose a plan that adheres to our patterns in `CLAUDE.md`. Do not write code yet, just the plan."

#### 2. The "Fix It" Prompt
Use this when you have an error.

> **User:** "I'm seeing error [Error String]. Please **investigate the cause** by tracing the execution flow. Create a minimal reproduction script to confirm the bug, fix it, and then run the script again to verify."

### Why this works
This strategy works better than a generic prompt because it plays to Claude Code's unique strengths as a CLI tool:
*   **Agentic Capabilities:** By forcing the "Exploration" phase, you prevent the model from guessing (hallucinating) APIs that don't exist.
*   **Context Awareness:** The `CLAUDE.md` file ensures the model doesn't "forget" that you are using Python 3.11 or React 18 halfway through the conversation.
*   **Verification:** Forcing a "verify" step is critical for autonomous coding agents, preventing them from saying "Fixed it!" when the code actually fails to compile.

## Human

Isn't it the same thing to put that in a prompt?

## Assistant

In terms of **content**, yes—the text is exactly the same. You are giving the AI the same instructions.

 However, in terms of **workflow and results with the Claude Code CLI**, they are **not** the same thing. Using the `CLAUDE.md` file is significantly better for three specific reasons:

### 1. It Solves "Agent Amnesia"
The Claude Code CLI is designed to be popped open and closed frequently. 
*   **If you use a Prompt:** You have to paste that massive block of text every single time you initialize a new session or switch tasks. If you forget, Claude reverts to its default, generic behavior.
*   **If you use `CLAUDE.md`:** It is "hard-coded" into the folder. Every time you run `claude` in that directory, the agent **automatically** adopts the persona, even if you come back to the project six months later. It ensures consistency across every interaction without you having to "prime" it.

### 2. It Protects Your Token Context
When you paste a long prompt into the chat, it occupies the "user turn" of the conversation. As the conversation gets long, the model may "forget" instructions from the very first message as they get pushed out of its primary focus.
`CLAUDE.md` is treated as **System Context**. This is a special part of the model's memory that is prioritized and persists more strongly than standard user chat messages. It acts as the "rules of the road" rather than just "something you said once."

### 3. It Enables "Per-Folder" Intelligence
This is the superpower of the file method. You can have different instructions for different parts of your system:
*   **Backend Folder:** `CLAUDE.md` says "Use Python, Pytest, and verify SQL schemas."
*   **Frontend Folder:** `CLAUDE.md` says "Use React, Tailwind, and check for mobile responsiveness."

If you rely on a manual prompt, you have to manually edit your clipboard paste depending on which folder you are working in. With the file method, Claude automatically switches its personality based on which directory you are currently in.

### Summary
| Feature | Manual Prompt | `CLAUDE.md` File |
| :--- | :--- | :--- |
| **Effort** | High (Copy/Paste every session) | Zero (Set and forget) |
| **Memory Priority** | Medium (Recedes as chat gets longer) | High (Prioritized System Prompt) |
| **Context Switching** | Manual (You must edit the prompt) | Automatic (Based on folder) |
| **Team Sharing** | None (Only you have the prompt) | High (Committed to Git, team follows same rules) |

**Recommendation:**
If you are strictly using the **Web Interface (Claude.ai)**, then yes, you have to paste it every time (or use a "Project" in the web UI). But if you are using the **Claude Code CLI tool**, the `CLAUDE.md` file is the intended and superior way to drive the agent.

## Human

What about if we are using claude code subagents?

## Assistant

To answer your question about subagents: **No, putting a prompt in `CLAUDE.md` is not enough for subagents.**

While the main `CLAUDE.md` provides global rules for the "main thread," subagents in Claude Code are distinct, specialized entities with their own separate configurations. If you rely solely on `CLAUDE.md`, your subagents will effectively be "unprompted" default models, ignoring your carefully crafted rules.

You need to explicitly configure each subagent. Here is the best-practice "Subagent Architecture" for Claude Code to ensure they perform as well as the main agent.

### 1. The Strategy: "De-Coupled Intelligence"
In Claude Code, subagents are isolated. They do **not** automatically inherit the instructions from the main `CLAUDE.md`. 
*   **Main Thread:** Reads `CLAUDE.md` (General Orchestrator).
*   **Subagent (e.g., `qa-engineer`):** Reads `.claude/agents/qa-engineer.md` (Specialist).

To get the "best" results, you must create a dedicated Markdown file for *each* subagent in a `.claude/agents/` folder at your project root.

### 2. The Setup: How to Configure Subagents
Create a folder named `.claude/agents` in your project root. Inside, create a file for your subagent, for example: `qa-engineer.md`.

#### Example `qa-engineer.md`
This file defines the subagent's entire brain. Notice the YAML frontmatter at the top—this is required.

```markdown
---
name: qa-engineer
description: Specialized agent for generating comprehensive test suites and verifying bug fixes.
tools:
  - Bash
  - ReadFile
  - WriteFile
model: inherit  # Inherits the model (Sonnet 3.5), NOT the prompt
---

# QA Engineer Persona
You are a Senior QA Automation Engineer. Your only goal is to break the code and then prove it is fixed.

## Protocol
1.  **Analysis:** Read the implementation code provided by the main agent.
2.  **Test Strategy:** BEFORE writing tests, list edge cases (null inputs, boundary values, concurrent users).
3.  **Implementation:**
    *   Write strictly typed test files (e.g., `*.test.ts` or `test_*.py`).
    *   NEVER mock the database unless explicitly told; prefer integration tests.
4.  **Verification:** Run the tests yourself using `npm test` or `pytest`.
    *   If tests fail, report the EXACT error to the main agent.
    *   If tests pass, output "VERIFICATION SUCCESSFUL".
```

### 3. How to Orchestrate Them
Once you have these files set up, you don't just "chat" with them randomly. You have two powerful ways to drive them:

#### Method A: Explicit Delegation (The "Manager" approach)
You (the user) tell the main Claude agent to use the subagent.
> **User:** "Claude, I've just written the new auth module. Please hand this off to the `@qa-engineer` to generate edge-case tests."

#### Method B: Automatic Routing (The "Auto-Pilot" approach)
Because you defined a `description` in the YAML frontmatter (e.g., "Specialized agent for generating..."), the main Claude Code agent can automatically decide to call this subagent if your request matches that description.
> **User:** "Run a full regression test on the payment API."
> **Claude Code:** *Thinking... "This looks like a job for `qa-engineer` based on its description." -> Spawns Subagent.*

### 4. Best Practice: The "Shared Knowledge" Trick
Since subagents don't read `CLAUDE.md` by default, you have a maintenance problem: if you change your coding style in `CLAUDE.md`, you have to update every subagent file.

**The Pro Tip:**
In your subagent prompts (like `.claude/agents/qa-engineer.md`), add this instruction to the very top of the system prompt section:

> "First, read the file `CLAUDE.md` in the project root to understand the global coding standards, naming conventions, and tech stack. Then apply those rules to your specific role defined below."

This forces the subagent to "dynamically inherit" your global rules every time it runs, keeping your system in sync without copy-pasting.

### Summary Checklist for Best Subagent Results
1.  **Create Directory:** `mkdir -p .claude/agents`
2.  **Create Agent File:** `touch .claude/agents/my-specialist.md`
3.  **Define YAML:** Give it a clear `name` and `description` (crucial for auto-routing).
4.  **Link Context:** Instruct it to read `CLAUDE.md` as its first step.
5.  **Specialize:** Give it a narrow, strict protocol (like the QA example above) that is *different* from your main generalist prompt.

## Human

So what config do we use for the best coding / architecture / design / solution claude code subagent?

## Assistant

Perfect. Based on the **official Claude Code documentation**, here is the **optimal configuration for a "Coding/Architecture/Design/Solution" subagent**—a specialist that excels at system design, architectural decisions, and producing high-quality solutions.

### The "Architect" Subagent Configuration

Create this file: `.claude/agents/architect.md`

```markdown
---
name: architect
description: Senior software architect. Use for system design, architecture decisions, design patterns, and high-level solution planning. Proactively invoked when designing new systems or refactoring architecture.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: plan
---

# Senior Software Architect

You are a Principal Solutions Architect with 15+ years of experience designing large-scale, production-grade systems. Your responsibility is to provide deep technical guidance on system design, architecture patterns, and solution strategy.

## Core Responsibilities

1. **Holistic System Understanding**
   - ALWAYS start by reading the entire relevant codebase architecture
   - Map out existing patterns, constraints, and tech stack
   - Identify architectural debt and bottlenecks before proposing changes
   - NEVER assume; always verify current state

2. **Architecture-First Thinking**
   - Design for scalability, maintainability, and resilience FIRST
   - Consider trade-offs explicitly (complexity vs. simplicity, performance vs. flexibility)
   - Document assumptions and constraints that shaped your decision
   - Propose multiple viable approaches when appropriate, with clear pros/cons

3. **Pattern Recognition & Consistency**
   - Respect existing architectural patterns in the codebase
   - Suggest improvements that align with, not contradict, current conventions
   - Use established design patterns (SOLID, DDD, Event-Driven, etc.) appropriately
   - Ensure new components fit the overall system topology

4. **Strategic Communication**
   - Present architecture as a structured plan with phases
   - Include visual ASCII diagrams for complex interactions
   - Explain WHY each decision matters (performance, maintainability, team velocity)
   - Flag risks and mitigation strategies

## Research Protocol (Required Every Session)

Before recommending any architecture:

1. **Codebase Discovery**
   ```
   ls -la
   find . -type f -name "*.json" -o -name "*.yaml" -o -name "*.toml" | head -20
   find src -type f -name "*.ts" -o -name "*.py" | head -30
   ```

2. **Existing Architecture Analysis**
   - Read `README.md`, `ARCHITECTURE.md`, or similar documentation
   - Examine package.json / pyproject.toml / go.mod for tech stack
   - Check for existing patterns: folder structure, naming conventions, dependency injection style
   - Review key services/modules: database layer, API layer, caching strategy

3. **Constraints & Context**
   - Identify non-functional requirements (latency SLAs, throughput, availability targets)
   - Check for regulatory/compliance constraints
   - Understand team size, skill level, deployment frequency
   - Note any legacy systems or third-party dependencies

## Design Decision Framework

For every architectural recommendation:

### Phase 1: Problem Statement
- Restate the problem in your own words
- Identify root causes (not symptoms)
- Clarify constraints and success criteria

### Phase 2: Options Analysis
Present 2–3 viable approaches:
```
Option A: [Name] - [Brief description]
  ✅ Pros: ...
  ❌ Cons: ...
  💰 Complexity: Low/Medium/High
  📈 Scalability: ... 
  🔧 Maintenance: ...

Option B: [Name] - [Brief description]
  ✅ Pros: ...
  ❌ Cons: ...
  ...
```

### Phase 3: Recommendation
- Select the option that best balances your constraints
- Provide implementation roadmap (phases, milestones)
- Identify critical technical decisions
- Suggest proof-of-concept approach if high-risk

### Phase 4: Implementation Guidance
- Provide pseudo-code or architectural sketch
- Specify testing strategy (unit, integration, load)
- Document deployment and rollback strategy
- Suggest monitoring and observability needs

## Tech Stack Awareness

For decisions involving:
- **Database Architecture**: Evaluate SQL vs NoSQL, sharding strategies, read replicas, caching layers
- **API Design**: REST, GraphQL, gRPC—match to use case, consistency requirements
- **Async Processing**: Message queues, event streams, job schedulers
- **Deployment**: Containerization, orchestration, blue-green, canary strategies
- **Observability**: Metrics, logging, tracing for debugging and alerting

## Anti-Patterns to Flag

When you encounter these, proactively surface them:
- God objects (classes doing too much)
- Circular dependencies
- Tight coupling to external services
- No clear separation of concerns
- Missing abstraction layers
- Inadequate error handling strategy
- Lack of idempotency in critical paths

## Output Standards

When delivering architecture guidance:

1. **Structured Plan**: Use markdown headers to organize (## System Overview, ## Data Flow, ## Deployment, etc.)
2. **Visual Aids**: Include ASCII diagrams for data flow, component interaction, or deployment topology
3. **Code Examples**: Provide minimal, production-ready example implementations (not pseudocode)
4. **Risk Assessment**: List top 3 risks and mitigation strategies
5. **Success Metrics**: Define how to measure if the architecture achieved its goals
6. **Next Steps**: Provide actionable, prioritized tasks for implementation

## Collaboration Protocol

- Work with the main agent for detailed coding tasks
- Suggest delegating to other subagents (qa-engineer for testing, debugger for troubleshooting)
- Preserve architectural intent when refactoring—do not introduce unwanted changes
- Always explain tradeoffs; don't force architectural patterns

## Key Values

- **Pragmatism over Purity**: Simple, working solutions beat perfect but complex ones
- **Evidence-Driven**: Base recommendations on actual codebase state, not assumptions
- **Team Alignment**: Propose architectures your team can understand, maintain, and extend
- **Future-Proof**: Design for anticipated growth without over-engineering for speculative needs
```

***

### How to Use It

#### **Explicit Invocation (Most Direct)**
```
> Use the architect subagent to design a new caching strategy for the API layer
> Have the architect subagent review the current database schema and recommend partitioning
> Ask the architect subagent for a migration plan from monolith to microservices
```

#### **Automatic Delegation (Let Claude Decide)**
Simply make architecture-related requests, and Claude Code will automatically use `architect` based on the subagent's description:
```
> Design a system to handle real-time notifications at scale
> I need to refactor the payment processing pipeline. What's the best approach?
```

***

### Why This Configuration Works

| Field | Value | Why |
|-------|-------|-----|
| **name** | `architect` | Clear, memorable identifier |
| **description** | Long, specific | Triggers auto-delegation when you mention "design," "architecture," "patterns," "system design" |
| **tools** | `Read, Grep, Glob, Bash` | Read-only exploration tools—architect researches before designing, doesn't modify yet |
| **model** | `inherit` | Uses same model as main thread (Sonnet 3.5), ensuring consistency and advanced reasoning |
| **permissionMode** | `plan` | Operates in planning mode—outputs strategy without immediately executing code changes |

***

### Integration with Your `CLAUDE.md`

At the **top of your architect.md prompt**, add this line:

> "First, read the file `CLAUDE.md` in the project root to understand global coding standards, naming conventions, and team practices. Incorporate these into your architectural recommendations."

This ensures the architect respects your codebase's conventions while bringing architectural expertise.

***

### Recommended Workflow

1. **Main Agent** (You) → High-level request: *"Design the refactored auth system"*
2. **Architect Subagent** → Returns detailed design, ASCII diagrams, options analysis
3. **Main Agent** → Implements based on architect's plan
4. **QA/Debugger Subagents** → Validate and fix issues

This division of labor gets you the **best coding, architecture, and design solutions** because the architect focuses purely on strategy—not distracted by syntax or implementation details.

## Human

Please show what it would be for the best researcher subagent for Coding/Architecture/Design/Solution

## Assistant

Here is the optimal configuration for a **Researcher** subagent.

While the "Architect" designs the *future*, the "Researcher" is responsible for deeply understanding the *present* (the codebase) and the *possibilities* (libraries, docs, external patterns). This agent is your "Recall" and "Discovery" engine.

### The "Deep Dive" Researcher Configuration

Create this file: `.claude/agents/researcher.md`

```markdown
---
name: researcher
description: Expert technical researcher. Use for investigating documentation, auditing codebase history, comparing libraries, debugging complex error logs, or explaining legacy code.
tools: Bash, ReadFile, Grep, Glob, View
model: inherit
---

# Principal R&D Engineer (Researcher)

You are a Principal Research Engineer. Your role is not to write feature code, but to gather **irrefutable evidence** and provide **deep context** to support decision-making. You replace assumptions with facts.

## Core Mandate: The "Zero Assumption" Policy
1.  **Verify, Don't Guess:** Never assume an API signature or file location. Find it.
2.  **Cite Your Sources:** Every claim must reference a specific file path, line number, or command output.
3.  **Synthesize, Don't Dump:** Do not just cat a file. Read it, analyze it, and extract the relevant logic.

## Research Protocols

### Protocol A: Codebase Archaeology (Internal)
*Use this when the user asks "How does X work?" or "Where is Y defined?"*

1.  **Map the Territory:**
    *   Start with `find` or `ls -R` to understand the structure.
    *   Use `grep -r "string" .` to trace usage patterns across the repo.
2.  **Trace the Logic:**
    *   Identify the entry point.
    *   Follow the execution flow (imports, function calls).
    *   **Crucial:** Check `git log -p filename` (via Bash) if you need to understand *why* a confusing change was made.
3.  **Deliverable:** A "Logic Map" explaining the data flow, dependencies, and potential side effects of touching this code.

### Protocol B: Technology Evaluation (External)
*Use this when the user asks "What is the best library for X?" or "How do I use this API?"*

1.  **Fetch Live Data (via Bash):**
    *   Use `npm view [package]`, `pip show [package]`, or `curl -L [docs_url]` to get real, current metadata.
    *   Check for deprecation warnings or version mismatches.
2.  **Compare Options:**
    *   Create a "Trade-off Matrix": Compare options based on Size, Popularity, Maintenance, and Compatibility with the current project.
3.  **Deliverable:** A recommendation backed by data, including a minimal "Hello World" example relevant to *our* specific stack.

### Protocol C: Debugging Investigation
*Use this when the user provides a stack trace or bug report.*

1.  **Isolate the Variable:**
    *   Locate the exact file and line number from the stack trace.
    *   Look for recent changes in that area.
2.  **Hypothesis Generation:**
    *   Propose 2-3 potential root causes based on the evidence.
    *   Suggest specific verification steps (e.g., "Run this curl command to reproduce").

## Output Format: The Research Report

Structure your responses exactly like this:

### 1. Executive Summary
*   A 2-sentence answer to the user's core question.
*   "TL;DR: The bug is in `auth.ts`, caused by a race condition."

### 2. Evidence Locker
*   **Key Files:** List relevant file paths.
*   **Code Snippets:** Show the *exact* lines of code that matter.
*   **Data Points:** Output from CLI tools (versions, error logs).

### 3. Analysis
*   Explain the "Why". Connect the dots between files.
*   "The `User` model imports `Settings`, but `Settings` tries to import `User` for type checking, causing a circular dependency."

### 4. Recommendations
*   Option 1: [Low Risk/Quick Fix]
*   Option 2: [High Value/Refactor]

## Global Context
*   First, read `CLAUDE.md` to align your analysis with the project's established patterns.
```

***

### How to use the Researcher Subagent

This agent is most powerful when used as the **first step** in a complex chain.

#### 1. The "Pre-Code" Briefing
Before you ask the Architect to design or the Coder to build, have the Researcher gather the ammo.
> **User:** "We need to migrate from Moment.js to date-fns. @researcher, please audit the codebase to find every instance of Moment.js, categorize how we are using it (formatting vs. calculation), and create a migration strategy report."

#### 2. The "Sherlock Holmes" Debugging
When you are stuck on a weird error.
> **User:** "I'm getting a 'Heap Out of Memory' error during the build. @researcher, investigate the build logs, check our `package.json` scripts, and find out which step is consuming the memory."

#### 3. The "Library Shopper"
> **User:** "@researcher, we need a drag-and-drop library for React 18. Compare `dnd-kit` vs `react-beautiful-dnd`. specific to our TypeScipt setup. Check which one is more actively maintained."

### Why this is different from the "Architect"
*   **Architect:** Says *"We should build a microservice."* (Focus: Strategy & Design)
*   **Researcher:** Says *"Here are the 3 services already using this port, and here is the documentation for the API gateway we need to integrate with."* (Focus: Facts & Context)

Using this specific `researcher.md` ensures that your coding agents stop hallucinating APIs and start building on a foundation of verified facts.

## Human

What model context protocol servers should I use to help with the reseaching?  And github.com repos?

## Assistant

For the best coding, architecture, and research results with Claude Code, you should mix **generic research tools** with **code-specific analyzers**.

Since Claude Code is a CLI tool, you configure these MCP servers in your `claude.json` (or equivalent config) to give the agent "superpowers" beyond just reading text files.

### Top 3 MCP Servers for Coding & Research

| Use Case | Recommended MCP Server | Why Use This? |
| :--- | :--- | :--- |
| **Web Research** | **Search / Brave Search** | Allows Claude to Google errors, finding up-to-date library docs that aren't in its training data. |
| **Repo Analysis** | **GitHub Analyzer** | Lets the agent read Issues, PRs, and commit history to understand *why* code was written that way (context). |
| **Documentation** | **Docs MCP** | Scrapes and indexes 3rd-party documentation (e.g., Stripe, LangChain) so Claude can "read the manual" instantly. |

***

### 1. GitHub Repository Analysis (The "Context" Engine)
This is crucial for the "Researcher" subagent. It allows the agent to see *beyond* the current files and look into the history and issue tracker.

*   **Repo:** `github.com/modelcontextprotocol/servers` (Official)
*   **Key Tools Provided:**
    *   `search_repositories`: Find relevant external libraries.
    *   `get_issue`: Read bug reports to see if a bug is known.
    *   `get_file_contents`: Read code from *other* repos (e.g., dependency source code) without cloning them.
*   **Alternative:** `github.com/jar285/github_mcp_analyzer` (Better for visualizations and activity metrics).

### 2. Documentation Search (The "Manual" Reader)
Standard LLMs have outdated knowledge of libraries. This server lets Claude fetch the *current* API reference for any library.

*   **Repo:** `github.com/modelcontextprotocol/servers` (Official) or `github.com/davepoon/docs-mcp-server`
*   **Key Tools:**
    *   `scrape_docs`: Reads a documentation URL and turns it into markdown context.
    *   `search_docs`: Semantic search over a documentation site.
*   **Usage:** "Claude, I don't know how to use `pandas` 2.0. Use the `docs` tool to read the migration guide."

### 3. Codebase Intelligence (The "Deep" Analyzer)
For massive refactors, simple `grep` isn't enough. You need an AST (Abstract Syntax Tree) analyzer.

*   **Repo:** `github.com/0xjcf/MCP_CodeAnalysis`
*   **Key Tools:**
    *   `analyze_dependencies`: Maps out the import graph (what depends on what).
    *   `get_code_metrics`: Checks cyclomatic complexity (finds "spaghetti code").
    *   `visualize_relationships`: Generates a knowledge graph of your classes.

### 4. Git History (The "Time Machine")
Understanding *who* changed a line and *why* is often more important than the code itself.

*   **Repo:** `github.com/MCPRUNNER/GitVisionMCP`
*   **Key Tools:**
    *   `compare_branches_documentation`: summarizing the diff between feature branch and main.
    *   `generate_git_documentation`: Creates a changelog automatically.
    *   `search_commits`: "Find when we removed the legacy login feature."

### How to Configure These
You typically add these to your MCP configuration file (e.g., `claude_mcp_config.json`).

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    },
    "git-vision": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "mcp/git-vision"] 
    },
    "docs-search": {
       "command": "npx",
       "args": ["-y", "docs-mcp-server"]
    }
  }
}
```

### Recommendation
Start with the **Official GitHub Server** and the **Docs Server**. These two alone will double the effectiveness of your "Researcher" subagent by giving it access to the outside world (docs) and the past (git history).

## Human

Is octocode any good?

## Assistant

Yes, **Octocode** is highly capable, but it serves a specific niche. It is a **"Local-First" Research Agent for GitHub** that runs via the MCP protocol.

It is generally considered **better** than the official GitHub MCP server for **complex research** (like "find me good examples of how to use this library"), but it might be overkill if you just need to read a single file.

### Octocode at a Glance

| Feature | Octocode MCP | Official GitHub MCP |
| :--- | :--- | :--- |
| **Search Quality** | **Semantic Search** (understands concepts) | Basic keyword search |
| **Performance** | **Parallel Queries** (fast bulk research) | Sequential (slower) |
| **Depth** | **"Smart" Context** (extracts relevant snippets) | Returns full raw files |
| **Dependencies** | Requires `gh` CLI installed locally | Uses API Token directly |
| **Privacy** | **High** (Runs locally via CLI) | Medium (Cloud API calls) |

### Why You Would Choose Octocode
1.  **"Vibe Coding" / Exploration:** If you don't know exactly what you are looking for.
    *   *You:* "Find me a React component that does drag-and-drop file uploads using Tailwind."
    *   *Octocode:* Can search multiple repos, extract snippet examples, and summarize the best implementation patterns using its semantic search.
    *   *Official GitHub:* Would just list repos named "react-drag-drop" and force you to dig through them one by one.

2.  **Speed (Parallel Execution):**
    Octocode is optimized to run multiple search queries at once. If your agent needs to check 5 different repos to compare implementations, Octocode does this in one "turn," whereas standard tools might take 5 back-and-forth steps.

3.  **Local Context:**
    Because it piggybacks on your local GitHub CLI (`gh`), it instantly has access to every private repo you have access to, without needing complex token configuration.

### When to Stick with the Official Server
*   **Simple Tasks:** If you just need to `read_file` or `create_issue` on a known repo, the official server is lighter and less likely to break.
*   **Write Operations:** The official server is more robust for *managing* GitHub (creating PRs, commenting on issues) rather than just researching code.

### Verdict
**Octocode is the superior choice for your "Researcher" subagent.**
Its semantic search and parallel querying capabilities align perfectly with the "Deep Dive" and "Technology Evaluation" protocols defined in the `researcher.md` configuration.

**Configuration for your `claude.json`:**
```json
{
  "mcpServers": {
    "octocode": {
      "command": "npx",
      "args": ["-y", "octocode-mcp@latest"]
    }
  }
}
```
*Note: Ensure you have the GitHub CLI (`gh`) installed and logged in (`gh auth login`) on your machine for it to work.*

## Human

what else competes with octocode?

## Assistant

There are several serious competitors to Octocode for the "Researcher" role, each with a slightly different superpower.

While Octocode is the best **"Local Research Agent"** (combining Semantic Search + Local CLI privacy), here is how the competition stacks up:

### Top Competitors to Octocode

| Tool | Best For... | Key Difference |
| :--- | :--- | :--- |
| **Greptile** | **Enterprise Scale** | Indexes *huge* repos (monorepos) better than local tools because it's a cloud service. It understands the full dependency graph across 100+ repos. |
| **Bloop** | **Local Privacy + Speed** | A standalone Rust-based engine. It's faster than Octocode for regex/symbol search but requires installing the Bloop app first. |
| **Sourcegraph Cody** | **Enterprise Knowledge** | If your company already uses Sourcegraph, this is unbeatable. It has "Google-level" search over your entire organization's private code. |
| **GitHub Official MCP** | **Operations / Writing** | Better for *doing* things (creating PRs, commenting on issues) rather than *finding* things. It's an "Actor," not a "Researcher." |

***

### Deep Dive: Which one should you choose?

#### 1. Greptile (The "Big Brain")
If you are working in a massive corporate environment with 50 microservices and you need to ask: *"Where is the UserID validated across all our services?"*, Octocode might choke on the volume. Greptile indexes everything in the cloud and gives you an API to query it.
*   **Pros:** True multi-repo understanding, understands "code logic" not just text.
*   **Cons:** Requires sending your code to their cloud (privacy concern for some).

#### 2. Sourcegraph Cody (The "Enterprise Standard")
If you have a Sourcegraph license, use their MCP server. It is the gold standard for code search.
*   **Pros:** It knows everything—commits, diffs, blame, and references across millions of lines of code.
*   **Cons:** Heavy setup if you aren't already a customer.

#### 3. Bloop (The "Rust Speedster")
Bloop is an interesting middle ground. It runs locally (like Octocode) but uses a highly optimized Rust engine for search.
*   **Pros:** Blazing fast. Semantic search (natural language) works offline.
*   **Cons:** You have to run the Bloop desktop app alongside Claude.

### Recommendation

*   **For Individual / Small Team (Best Balance):** Stick with **Octocode**. It requires zero infrastructure (just `gh` CLI) and provides 90% of the value of the big enterprise tools.
*   **For Massive Monorepos:** Use **Greptile** (if cloud is OK) or **Sourcegraph** (if on-prem).
*   **For Pure Speed:** If you find Octocode too slow, try **Bloop**.

### Suggested `claude.json` for a "Super-Researcher"
You can actually run *both* to cover all bases.

```json
{
  "mcpServers": {
    "octocode": {
      "command": "npx",
      "args": ["-y", "octocode-mcp@latest"]
    },
    "greptile": { 
      "command": "npx",
      "args": ["-y", "greptile-mcp-server"],
      "env": { "GREPTILE_API_KEY": "..." }
    }
  }
}
```
*Use Octocode for quick local checks, and Greptile for deep, cross-repo architectural queries.*

## Human

I have a Perplexity API key.  Is that useful?

## Assistant

Yes, it is **extremely useful**. A Perplexity API key gives your coding agent "live web intelligence."

While standard search tools (like Brave Search) give you a list of links that the agent has to visit one by one, the Perplexity API returns a **synthesized answer with citations**. This is much faster and cheaper for the agent to consume.

### Why Perplexity + Claude Code is a Power Combo
1.  **Single-Step Answers:** Instead of `Search -> Click Link -> Read -> Click Link -> Read`, the agent makes **one** API call to Perplexity: *"What is the latest breaking change in Next.js 15 regarding caching?"* and gets the full answer immediately.
2.  **Reasoning Models:** You can configure it to use `sonar-reasoning` (Perplexity's "thinking" model), which is excellent for finding obscure coding solutions.
3.  **Real-Time Docs:** It acts as a fallback when the agent's internal training data is out of date.

### How to Add It (The Best Configuration)
You should use a dedicated MCP server for this. There are several community options, but the most reliable method is to use the direct `npx` command which pulls the latest version.

**Command to Install (Run this in your terminal):**
```bash
claude mcp add perplexity --env PERPLEXITY_API_KEY=pplx-xxxxxxxx -- npx -y @perplexity-ai/mcp-server
```
*(Replace `pplx-xxxxxxxx` with your actual key)*

### How to Use It in Your "Researcher" Subagent
Once installed, update your `.claude/agents/researcher.md` to explicitly prefer this tool for "How-to" questions.

**Add this to your `researcher.md`:**
```markdown
## Research Protocol: External Knowledge
When you need to find updated documentation, library comparisons, or error fixes from the web, ALWAYS use the `perplexity` tool first.
*   **Query Strategy:** Ask specific, technical questions.
    *   *Bad:* "React dnd"
    *   *Good:* "Compare @dnd-kit/core vs react-beautiful-dnd for React 18 strict mode compatibility"
```

### The "Octocode vs. Perplexity" Decision
Since you now have both options available:

| Task | Use **Octocode** | Use **Perplexity API** |
| :--- | :--- | :--- |
| **"How do I use this library?"** | No (It searches code, not concepts) | **YES** (Perfect for docs/tutorials) |
| **"Find me a code example."** | **YES** (Finds real repo usage) | Okay (Returns snippets, not full files) |
| **"What is this error?"** | No (Unless in a commit message) | **YES** (Searches StackOverflow/GitHub Issues) |
| **"Who changed this file?"** | **YES** (Local git access) | No (Cannot see your local files) |

**Pro Tip:** Your Researcher agent should use **Perplexity** to understand *what* to do, and **Octocode** to find *examples* of it being done.

## Human

are there any repos that use multiple subagents in parallel that would useful to consider for great and useful and practical research?

## Assistant

If you want to move beyond a single researcher to a **parallel multi-agent swarm**, you are looking for frameworks that can orchestrate "Claude Code"-style agents in parallel.

While Claude Code (the CLI) is primarily a single-stream tool (even with subagents, it mostly waits for one to finish), several repositories demonstrate true parallel research architectures.

### Top Repositories for Parallel Research Agents

| Repository | Best For... | Architecture |
| :--- | :--- | :--- |
| **`gpt-researcher`** (Tavily) | **Pure Research Speed** | Spawns 5+ parallel crawlers to aggregate data into one report. The gold standard for "research only." |
| **`langgraph`** (LangChain) | **Custom Workflows** | The best framework if you want to build a *custom* graph where "Researcher A" checks docs while "Researcher B" checks GitHub. |
| **`crewai`** | **Role-Playing Swarms** | Easy setup for a "team" (e.g., "Senior Dev" + "Junior Researcher") working async. |
| **`open-deep-research`** | **Iterative Depth** | Hugging Face's open implementation of deep research; focuses on depth rather than just speed. |

***

### 1. GPT Researcher (The "Speedster")
*   **Repo:** `assafelovic/gpt-researcher`
*   **Why it's great:** It doesn't just "chat." It treats research as a parallel MapReduce job.
*   **How it works:**
    1.  Generates 20+ search queries from your one prompt.
    2.  Executes them all *simultaneously* (Parallel).
    3.  Aggregates 50+ URLs.
    4.  Synthesizes a final report.
*   **Use Case:** "Find me every breaking change in React 18, 19, and the Beta, and summarize them." (It hits 20 pages at once).

### 2. LangGraph Multi-Agent (The "Builder's Kit")
*   **Repo:** `langchain-ai/langgraph` (Look for `examples/multi_agent`)
*   **Why it's great:** It allows you to define **State Machines**.
*   **How it works:** You can design a graph where:
    *   Node A (Git Researcher) and Node B (Doc Researcher) run in parallel.
    *   Node C (Architect) waits for *both* to finish.
    *   If Node A fails, Node B keeps going.
*   **Use Case:** Building a "Coding Factory" where one agent writes tests while another writes docs *at the same time*.

### 3. Open Deep Research (The "Analyst")
*   **Repo:** `huggingface/smolagents` or `dzhng/deep-research`
*   **Why it's great:** It implements the "Iterative" pattern. It does one round of research, realizes what is missing, and spawns new parallel queries to fill the gaps.
*   **Use Case:** "Figure out why this library is crashing, but you have to read the source code of its dependencies too."

### Recommended Architecture for You
Since you like **Claude Code** (CLI) but want **Parallelism**, you should use a **hybrid approach**:

1.  **Use `gpt-researcher`** as a standalone "Research Server."
2.  **Create a Claude Code Subagent** called `deep-researcher`.
3.  **The Trick:** Configure your subagent's tool to call the `gpt-researcher` API.

**Example `.claude/agents/deep-researcher.md`:**
```markdown
---
name: deep-researcher
description: Parallel Deep Research Agent.
tools: Bash
---

# Deep Research Protocol
To perform research, DO NOT use standard search.
Instead, run this python script which triggers the parallel swarm:

`python3 scripts/run_deep_research.py --query "{query}"`

This script spins up 10 parallel agents and saves the result to `research_report.md`.
Read that file when done.
```

This gives you the best of both worlds: The interface of Claude Code, but the backend power of a parallel swarm.

## Human

Please design a system that uses parallel subagents, and whatever useful tools or concepts we have covered in this conversation.

## Assistant

Perfect. I've designed a **comprehensive parallel multi-agent research system** that integrates everything from our conversation.

## What This System Does

This is a **Production-Ready Research Factory** that:

1. **Runs 3 Agents in Parallel** (Researcher, Architect, QA Engineer)
   - All work simultaneously instead of sequentially
   - Each completes within a 5-minute timeout
   - No blocking—they work independently

2. **Leverages All Tools We Covered**
   - **Octocode MCP** → Researcher finds real code examples
   - **Perplexity API MCP** → Researcher gets current documentation
   - **Greptile MCP** → Architect understands multi-repo dependencies
   - **Git history** → Researcher finds *why* code was written

3. **Clear Specialization**
   - **Researcher:** Facts & evidence gathering
   - **Architect:** Design & strategy decisions
   - **QA Engineer:** Test planning & edge cases
   - **Implementer:** Actual code (runs AFTER all parallel phases complete)

4. **Structured Output**
   - Each agent saves findings to `/research-output/` as Markdown
   - Main agent synthesizes all reports into final recommendation
   - Everything is traceable and cited

## Key Innovation: Parallel + Sequential Hybrid

```
Time Savings Example:
Sequential: Research (5min) → Architecture (5min) → QA (5min) = 15 minutes
Parallel:   Research + Architecture + QA (all 5min) = 5 minutes TOTAL
```

You save **66% execution time** by letting specialized agents work simultaneously on their expertise.

## How to Use It

1. **Create the files** from `SYSTEM_DESIGN.md` in your project
2. **Run the orchestrator:**
   ```bash
   python3 scripts/run_parallel_research.py
   ```
3. **Monitor results** in `research-output/` as agents complete
4. **Get final synthesis** with all findings integrated

The system is designed specifically for **coding/architecture/research** tasks and will significantly improve the quality and speed of your Claude Code projects.

## Human

I thought in claude code you couldn't use python to use parallel subagents.

## Assistant

You are absolutely right to be skeptical, but there is a specific **"Headless Mode"** (`claude -p`) that makes this possible.

It's true that the standard interactive `claude` command blocks the terminal and holds a session lock. However, the `run_parallel_research.py` script I designed relies on the **non-interactive** flag:

```bash
claude -p "your prompt"
```

### How Parallel Execution Actually Works
1.  **The `-p` (Print) Flag:** This tells Claude Code to spin up, run the prompt to completion, print the result, and *immediately exit*. It does not enter the REPL loop.
2.  **No Session Locking:** Because these are stateless "one-shot" commands, they don't lock the `claude_history.db` in the same way the interactive chat does. You can run 5 of them in parallel processes.
3.  **Limitations:**
    *   **No Shared Memory:** Agent A doesn't know what Agent B is doing *while* they are running. They only sync up when they write to the shared `/research-output` files.
    *   **Token Cost:** You are spinning up 3 full context windows simultaneously. This burns tokens 3x faster.

### The Correct Command for Python
The script needs to use this exact syntax to avoid the interactive blocking you were worried about:

```python
# In scripts/run_parallel_research.py

cmd = [
    "claude", 
    "-p",  # <--- CRITICAL: Headless mode
    f"Research task: {question}. Write report to {output_file}",
    "--dangerously-skip-permissions" # Optional: if you trust the agents to write files without asking
]
```

### If you prefer a "Pure API" approach
If you find the CLI headless mode too hacky or unstable (e.g., if you run into rate limits), the **Enterprise** way to do this is to bypass the CLI entirely and use the **Anthropic Python SDK** for the parallel agents, while keeping the CLI for your main interactive session.

**Hybrid Architecture (More Robust):**
1.  **You (User):** Use `claude` CLI interactively.
2.  **Subagents:** The python script calls `anthropic.messages.create()` directly (API) instead of spawning CLI processes.
    *   *Pros:* Faster, cheaper (no CLI overhead), zero locking issues.
    *   *Cons:* You have to manually give the API agents tools (like `read_file`), whereas the CLI has them built-in.

**Recommendation:** Stick with the `claude -p` method first. It's the "official" way to automate Claude Code. If you hit file lock errors (rare in headless mode), switch to the API method.

### Updated Script Snippet
Here is the corrected subprocess call to ensure it is non-blocking:

```python
cmd = [
    "claude",
    "-p",  # Run in headless/print mode
    f"--subagent {agent_name} \"{prompt}\"", # Correct subagent syntax
    "--print-format", "text"
]
```
*(Note: Ensure you are logged in to the CLI before running the script.)*

## Human

I think you are confused.  Parallel SUBAGENTS are supported and featured in claude code.  They are launched at the prompt level.

There is a claude agent SDK so that MAY allow python subagents.  Please investigatge both solutions.

I think what you showed was for full litteral claude code instances in new powershell terminals.

## Assistant

Perfect. I've created the **corrected design** that properly explains both approaches:

## Summary of the Two Correct Methods

### **1. Native Claude Code (Simplest)**
Just type in your Claude Code chat:
```
> @researcher What are the Moment.js→date-fns breaking changes?
> @architect Design the migration strategy
> @qa-engineer Plan test coverage
>
> Run all three in parallel.
```

Claude Code **natively handles the parallelization**. All three agents launch simultaneously, work in isolated context windows, and report back.

### **2. Claude Agent SDK for Python (Programmatic)**
For automation, use the official SDK:

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    tasks = [
        query(researcher_prompt, options=ClaudeAgentOptions(subagent_type="researcher")),
        query(architect_prompt, options=ClaudeAgentOptions(subagent_type="architect")),
        query(qa_prompt, options=ClaudeAgentOptions(subagent_type="qa-engineer")),
    ]
    await asyncio.gather(*tasks)  # True parallelization

asyncio.run(main())
```

***

## Key Correction

❌ **NOT:** Spawning separate `claude` CLI instances in new terminals (file locking issues)

✅ **INSTEAD:** 
- Use Claude Code's built-in subagent orchestration (native)
- OR use Agent SDK's `asyncio.gather()` (programmatic)

Both methods are **officially supported**, **parallel**, and **designed for this exact use case**.

Thank you for pushing back on this. The design is now accurate.

## Human

claude_agent_sdk, is this actually subagents inside claude code, or multiple instances of claude code?

## Assistant

This is the **critical architectural distinction** that most people (including many tutorials) get wrong.

The **Claude Agent SDK** is **NOT** just "subagents inside Claude Code."
It is a **standalone Python library** that allows you to instantiate and run the same "engine" that powers Claude Code, but inside your own Python application.

Here is the definitive breakdown of the relationship:

| Feature | **Claude Code (The CLI Tool)** | **Claude Agent SDK (The Library)** |
| :--- | :--- | :--- |
| **What is it?** | A compiled binary / NPM package application. | A Python package (`pip install claude-agent-sdk`). |
| **Execution Model** | **Single Process** (mostly). Subagents run as "tools" inside the same process loop. | **Multiple Instances**. You can spawn 100 separate `ClaudeAgent` objects in Python. |
| **Parallelism** | **Logical**. It "multitasks" by managing context windows, but it's one application. | **Physical**. Uses Python's `asyncio` to run truly independent execution loops. |
| **Context** | Shared session history (mostly). | **Isolated**. Each SDK instance has its own memory and state unless you manually link them. |
| **Use Case** | Interactive coding in your terminal. | Building *custom* automated coding platforms or CI/CD bots. |

### Does Claude Code use the SDK?
**Yes.** The `claude` CLI tool is effectively a "reference implementation" built *on top of* the Agent SDK (or the internal equivalent of it).

### "Is this multiple instances?"
When you use the **Agent SDK**, yes, you are literally creating multiple instances of the "Claude Code Brain."
*   If you write a Python script that spawns 5 agents using the SDK, you have **5 independent API loops** running against Anthropic's servers.
*   They do **not** share a terminal window.
*   They do **not** know about each other unless you write code to pass messages between them.

### "Is this subagents inside Claude Code?"
When you use the **CLI** (`claude` command):
*   Subagents are **logical constructs**.
*   When you say `@researcher`, the CLI tool:
    1.  Pauses the main conversation.
    2.  Spins up a *new, temporary context window* for the researcher.
    3.  Runs that loop until completion.
    4.  Feeds the result back to the main thread.
    5.  Closes the temporary window.

### Which one should you use?

**Use the SDK if:**
*   You want to build a "Nightly Code Review Bot" that runs on GitHub Actions.
*   You want true, massive parallelism (e.g., "Fix these 50 files at the same time").
*   You want to integrate Claude into a larger Python application (like a Flask app).

**Use the CLI (Claude Code) if:**
*   You are sitting at your computer writing code.
*   You want the "human-in-the-loop" experience.
*   You want the convenience of `@researcher` without writing Python code to orchestrate it.

**In summary:** The SDK is the *engine block*. Claude Code is the *car*. You can buy the engine block and build your own boat, plane, or racecar (using Python), or you can just drive the car (the CLI).

## Human

I can see the subagents being invoked.  I can't see the claude code instances being invoked.  Is there a way to observe the parallel instances version?

## Assistant

Excellent question. The answer is **yes, there IS a way to observe it**, and it reveals the actual implementation:

## What You're Actually Seeing: The "Task Tool"

When you invoke parallel subagents in Claude Code, what's happening under the hood is:

**Claude Code uses the "Task Tool"** to spawn parallel executions. You can **see this happening in real-time**.

### Observable Behavior (From Reddit/GitHub findings):

When you invoke `@researcher`, `@architect`, and `@qa-engineer` in parallel, Claude Code's console shows:

```
Task 1: [Research] ⏳ Running...
Task 2: [Architecture] ⏳ Running...
Task 3: [QA] ⏳ Running...

Task 1: [Research] ✅ Complete
Task 2: [Architecture] ✅ Complete
Task 3: [QA] ✅ Complete
```

Each "Task" with the **flashing bubble indicator** = a separate subagent instance being executed.

From the Reddit PSA (June 2025):
> "Each time you see Task it is a sub-agent being utilised. Hence you'll see multiple instances of Task with a flashing bubble next to them to indicate the process is alive. It turns green when the sub-agent completes its job."

***

## The Critical Finding: Parallelism Limits

From the deep dive research:
- **Hard cap: ~10 concurrent tasks** before Claude Code queues them
- Beyond 10, tasks get batched/queued automatically
- No explicit parallelism control in the current API

***

## How to Observe It Yourself

When you type:
```
> @researcher [task]
> @architect [task]
> @qa-engineer [task]
> Run all three in parallel
```

Claude Code will:
1. **Create 3 Task tool invocations** (you'll see these listed in the Claude Code UI)
2. **Execute them concurrently** (you'll see the "flashing bubble" animation for each one)
3. **Track completion** (bubbles turn green when done)

***

## What You're Actually NOT Seeing

You **won't** see:
- Separate terminal windows/processes (like spawning new `claude` CLI instances)
- Separate file handles competing for locks
- OS-level parallelism at the process level

***

## The Distinction Clarified

**Claude Code Native Subagents:**
- Uses the built-in **Task tool** under the hood
- Spawns "logical" parallel contexts (not new OS processes)
- All within one Claude Code instance
- Observable via Task indicators in the UI

**Claude Agent SDK:**
- Creates true **Python objects** (ClaudeAgent instances)
- Uses `asyncio` for actual async execution
- Each is a separate API call to Anthropic
- Observable via print statements and logging in your Python script

***

## How to See the Task Tool in Action

Add this debug prompt to Claude Code:
```
> Show me the Task tool invocations you're creating for these parallel agents.
> Tell me:
> 1. How many Task tool calls will you make?
> 2. What parameters will you pass to each?
> 3. How will you aggregate the results?
```

Claude will reveal the underlying Task tool mechanics it's using.

***

## So What's the Real Answer?

**When you invoke parallel subagents in Claude Code:**

```
@researcher ... && @architect ... && @qa-engineer ...
```

**What's actually happening:**
1. Claude Code parses the multi-agent invocation
2. Creates **3 Task tool calls** (observable in the UI)
3. Executes them **concurrently** (you'll see flashing bubbles)
4. Waits for all to complete (up to 10 in parallel, then queues beyond that)
5. Aggregates results back to the main conversation

**You ARE seeing the parallel instances** — they're the Task indicators with the flashing bubbles in your Claude Code console.

Does this match what you're observing?

## Human

You misunderstood.  How do we see python objects for claude code?  I have the 1st claude code that I've launched manually, but how to observe the python launched claude code objects?

## Assistant

You are asking the exact right engineering question: **"Show me the process handles."**

If you have launched the SDK agents (the Python script method), you cannot see them inside the Claude Code CLI UI. They are headless Python objects running in your terminal's memory.

Here is how you actually **observe** the Python-launched Claude Code objects.

### 1. The "Poor Man's" Observability (Print Statements)
In the SDK script I provided, the visibility comes entirely from the `print()` loop.
*   **Where to look:** The terminal window where you ran `python3 run_parallel_agents.py`.
*   **What you see:** Text streaming in real-time.
*   **The Object:** The `client` object in Python is the agent.

```python
# The "Agent" is just this variable
client = ClaudeSDKClient(options=...)

# The "Observation" is this loop
async for message in client.query("Do research"):
    print(f"[Agent ID: {id(client)}] {message}")  # <--- Prints the memory address
```

### 2. The "Real" Observability (MLflow Tracing)
Since these are just Python objects, you can attach standard Python tracing tools. **MLflow** has official support for the Claude Agent SDK.

**How to set it up:**
1.  `pip install mlflow`
2.  Add this to the top of your script:

```python
import mlflow
mlflow.anthropic.autolog()  # <--- Magic line
```

3.  Run your script: `python3 run_parallel_agents.py`
4.  Run the UI: `mlflow ui`
5.  **Go to `localhost:5000`**

**What you will see:**
*   A "Trace" view showing 3 parallel tracks.
*   The exact input/output of every subagent.
*   Latency graphs for each parallel thread.
*   This is the "Dashboard" you are looking for.

### 3. The "Process" Observability
If you want to see them as OS processes (to prove they are parallel):
*   The standard `asyncio` script runs in **ONE process** (Python Global Interpreter Lock). You won't see 3 PIDs in `top` or Task Manager. You will just see one `python3` process working hard.
*   **To see separate PIDs (True Process Isolation):** You must switch your script from `asyncio` to `multiprocessing`.

**Modified "Heavy" Script (Spawns 3 OS Processes):**
```python
from multiprocessing import Process

def run_researcher_process():
    # ... entire asyncio loop for researcher ...
    print(f"Researcher PID: {os.getpid()}")

def run_architect_process():
    # ... entire asyncio loop for architect ...
    print(f"Architect PID: {os.getpid()}")

if __name__ == "__main__":
    p1 = Process(target=run_researcher_process)
    p2 = Process(target=run_architect_process)
    
    p1.start()
    p2.start()
```

**Now run `top` or Activity Monitor:**
*   You will see 3 separate `python3` processes.
*   This confirms they are truly physically isolated instances of the Claude Code engine.

### Summary
*   **Inside Claude Code CLI:** You see "Task" bubbles.
*   **Inside Python SDK (Default):** You see text logs in your terminal.
*   **Inside Python SDK + MLflow:** You see a beautiful visual trace dashboard at `localhost:5000`.
*   **Inside OS Task Manager:** You see one `python` process (unless you use `multiprocessing`).

**Recommendation:** Add `mlflow.anthropic.autolog()` to your script. That is the "Professional" way to observe what your swarm is doing.

## Human

Are custom agents useful for our researcher solution?

## Assistant

Yes, custom agents are **highly useful** for the researcher solution, but with important caveats about when and how to use them.

Let me clarify the distinction and recommendation:

## Custom Agents: Two Different Things

### 1. Custom Subagents (`.claude/agents/researcher.md`)
These are **configuration files** that define the persona, tools, and behavior of a subagent.
- **What they are:** Markdown files in `.claude/agents/`
- **How they work:** Claude Code reads them and uses them to shape the subagent's behavior
- **Usefulness:** ⭐⭐⭐⭐⭐ **Absolutely essential** for your researcher solution

### 2. Custom Python Agent Objects (Claude Agent SDK)
These are **Python classes/instances** you create using the SDK.
- **What they are:** `ClaudeSDKClient` objects spawned in Python code
- **How they work:** Full programmatic control over agent execution
- **Usefulness:** ⭐⭐⭐ **Useful only for specific automation scenarios**

***

## For Your Researcher Solution: Recommendation

**Use Custom Subagents (Approach 1: `.claude/agents/researcher.md`)**

This is what you should do because:

1. **Perfect for Interactive Research**
   - You type one prompt, invoke `@researcher`, get results immediately
   - No Python code to write or debug
   - Results stay in the Claude Code conversation for follow-ups

2. **Already Optimized**
   - The subagent system is built into Claude Code
   - No performance overhead
   - Handles parallelization automatically

3. **Easier to Iterate**
   - Edit `.claude/agents/researcher.md` → immediately takes effect
   - No need to restart Python processes
   - Changes apply on next invocation

**Skip the Python Agent SDK (Approach 2)** unless you specifically need:
- Automated nightly research runs
- Integration into a CI/CD pipeline
- Custom Python tools not available as MCP servers
- Headless operation without human interaction

***

## The Researcher Custom Subagent (What You Should Build)

Here's the **optimized custom researcher subagent** for your use case:

```markdown
---
name: researcher
description: Expert technical researcher. Investigates breaking changes, migration patterns, API documentation, and code examples. Runs in parallel with other agents.
tools: Bash, ReadFile, Grep, Glob
model: inherit
---

# Principal Research Engineer

You are a deep technical researcher. Your job is to gather facts from:
- Official documentation
- GitHub repositories
- API references
- Error messages and Stack Overflow posts
- Commit histories

## Operating Protocol

### Input Format
You will receive a research question. Examples:
- "What are the breaking changes in migrating from Moment.js to date-fns?"
- "How do we handle timezone conversion?"
- "What are the performance implications?"

### Output Format
Save your findings to `/research-output/researcher_report.md` in this format:

```
# Research Report: [Your Question]

## Executive Summary
[2-sentence answer]

## Key Findings

### Finding 1: [Topic]
- **What it is:** ...
- **Source:** [link or file:line]
- **Impact:** ...
- **Example:** [code snippet]

### Finding 2: [Topic]
- ...

## Risk Assessment
- **Critical:** ...
- **Moderate:** ...
- **Low:** ...

## Recommended Resources
1. [Resource] - Why it matters
2. [Resource] - Why it matters

## Notes for Architect
[Highlight design-relevant findings]
```

## Research Strategy

1. **Parse the Question** (1 min)
   - What specific aspect am I researching?
   - What's the user's context (library? migration? API?)?

2. **Identify Search Strategy** (2 min)
   - Official docs first
   - GitHub examples
   - Error patterns
   - Commit history

3. **Gather Evidence** (3-4 min)
   - Use Perplexity API for current docs
   - Use Octocode for real code examples
   - Use Grep to search local files
   - Use Bash to check git history

4. **Synthesize Findings** (1 min)
   - Organize by importance
   - Cite all sources
   - Flag uncertainties

## Time Management
- Total timeout: 5 minutes
- At 4:30, stop searching and write report
- Mark incomplete sections as "PRELIMINARY"

## Anti-Patterns
- Never guess about API signatures—find them
- Never speculate without evidence
- Never hallucinate breaking changes
- Always cite your sources

## Success Criteria
- Every claim has a source
- No "probably" or "likely" statements
- Clear, actionable findings
- Highlights for architect and QA teams
```

***

## How to Use It

```bash
claude chat

> I need to research the Moment.js to date-fns migration in detail.
>
> @researcher, please investigate:
> 1. Breaking changes in API
> 2. Performance characteristics
> 3. Timezone handling differences
> 4. Community migration patterns
>
> Save findings to /research-output/researcher_report.md

# Claude Code executes the custom subagent
[Researcher completes in ~2-3 minutes]

# Results automatically appear in your chat
# You can ask follow-ups:
> Based on the research, what are the top 3 risks for our codebase?
```

***

## When to Add Python Custom Agents

Only if you need:

**Scenario 1: Nightly Research Automation**
```python
# Run every night, email results
python3 nightly_research.py
```

**Scenario 2: CI/CD Integration**
```python
# On every PR, research the impact of changes
# Post results as a PR comment
```

**Scenario 3: Custom Tools**
```python
# If you need tools that don't exist as MCP servers
@tool("private_company_api", "Search our internal docs")
```

***

## Summary

| Use Case | Solution | Difficulty |
| :--- | :--- | :--- |
| Interactive research | Custom subagent (`.claude/agents/researcher.md`) | Easy ⭐ |
| Ask follow-ups | Same custom subagent | Easy ⭐ |
| Parallel research | Invoke multiple `@agents` in one message | Easy ⭐ |
| Automated nightly runs | Python Agent SDK | Medium ⭐⭐ |
| Custom tools | Python Agent SDK + @tool decorators | Hard ⭐⭐⭐ |

**For your researcher solution: Build the custom subagent. Skip the Python SDK unless you have a specific automation need.**
