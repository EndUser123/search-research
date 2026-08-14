---
title: "I'm starting to feel like CC (Claude Code) doesn't look at any files before adding a feature or fixing a bug. What's the"
date: "2026-01-04"
mode: "COPILOT"
uuid: "ed9330ad-dce3-4fe9-83e6-71f4a9688813"
entry_count: 4
---

## Human

I'm starting to feel like CC (Claude Code) doesn't look at any files before adding a feature or fixing a bug. What's the best practice so CC doesn't create a mess?  We have taskmaster, we have a bunch of files like prd, ard, spec, data_model, etc.

## Assistant

Now I'll generate the final comprehensive answer with actionable best practices.

## Claude Code File Review Best Practices: Comprehensive Workflow

Your concern about Claude Code not reviewing files before making changes is valid and common. The solution centers on **explicit context engineering and structured workflows** that force Claude to read and understand your documentation before writing code.[1]

### Core Problem: Context Strategy Gaps

Claude Code doesn't inherently know which files to read first or their importance. Unlike Cursor (which absorbs the full repo), Claude Code requires manual context setup. Without guidance, it makes assumptions and writes code that contradicts your architecture, requirements, or data models.[2][1]

### Solution 1: Create a Comprehensive CLAUDE.md

The foundation of preventing messy changes is a **CLAUDE.md file** that Claude automatically pulls into context on every session. This is your "persistent memory" about your project.[3]

**Place this at your repo root** and check it into git:

```markdown
# Project Context

## Core Documentation
- **PRD**: docs/prd.md (Product Requirements)
- **ARD**: docs/ard.md (Architecture Review Document)
- **Spec**: docs/spec.md (Technical Specification)
- **Data Model**: docs/data_model.md (Database schema & relationships)
- **Code Standards**: standards/code-style.md

## Before Any Implementation
1. Always read the relevant PRD/Spec for that feature
2. Check data_model.md to understand schema impact
3. Review existing patterns in similar modules first
4. Never assume; ask about edge cases

## Testing Strategy
- Write tests FIRST (red → green → refactor)
- Minimum 80% code coverage
- Jest for unit tests, Playwright for E2E

## Common Commands
- `npm run test` - Run test suite (prefer single tests)
- `npm run lint` - Check code style
- `npm run typecheck` - Run TypeScript checks
- `git log --oneline` - View recent history

## Architecture Patterns
- Domain-driven design: domain logic separate from infra
- Repository pattern for data access
- Services layer between controllers and database
- Avoid circular dependencies

## Code Style
- ES modules (import/export) not CommonJS
- Destructure imports where possible
- Max 20 lines per function
- Self-documenting variable names
- Comprehensive error handling
```

This replaces the need to explain basic context in every prompt.[3]

### Solution 2: Establish a Pre-Work Ritual (Read → Plan → Code)

The **Anthropic-recommended workflow** prevents mess by separating phases:[3]

**Phase 1: Exploration (No Coding)**
```
"Before writing any code, please:
1. Read docs/prd.md to understand the requirements
2. Read docs/spec.md to understand the technical approach
3. Read docs/data_model.md to understand schema impact
4. Read src/services/similar-feature.service.ts as a pattern example
5. Summarize what you found WITHOUT proposing code changes yet"
```

**Phase 2: Planning (Thinking, Not Coding)**
```
"Now create a plan for implementing [feature]. Your plan should:
- List the files you'll modify
- Describe the changes to each file
- Show dependencies between changes
- Identify any schema or API changes needed
- Include validation and error handling approach

Do NOT write code yet. Just confirm your plan is sound."
```

**Phase 3: Implementation (With Approval)**
```
"OK, implement the plan you outlined. 
If you have questions about the plan, ask before proceeding."
```

This forces Claude to read your docs and prevents the "spray and pray" code generation. **It dramatically reduces hallucinations and duplicate code.**[1][3]

### Solution 3: Use Custom Slash Commands for Recurring Workflows

Store prompt templates in `.claude/commands/` folder for your common patterns. For instance, create `.claude/commands/implement-feature.md`:

```markdown
---
name: implement-feature
description: Implement a new feature with full file review

---

You are implementing a feature. Follow this process:

**STEP 1: Read Documentation**
- Read: docs/prd.md
- Read: docs/spec.md
- Read: docs/data_model.md
- Read: docs/ard.md

**STEP 2: Understand Current Implementation**
- Identify similar existing features
- Read a reference implementation for patterns
- Ask clarifying questions about schema changes

**STEP 3: Create Implementation Plan**
- Files to modify/create
- Data model changes (if any)
- API changes (if any)
- Test approach

**STEP 4: Implement (only after approval)**
- Follow code style from CLAUDE.md
- Write tests first (TDD)
- Run linting and type checks

**STEP 5: Verify**
- Run full test suite
- Confirm no circular dependencies
- Check error handling
```

Then invoke with: `/implement-feature [description]`[3]

### Solution 4: Keep a TODO Checklist for Complex Features

For substantial changes, have Claude maintain a `TODO.md` file as a working scratchpad:[2]

```markdown
# Feature: User Authentication [Started]

## Tasks
- [ ] Read PRD requirements (completed)
- [ ] Review existing auth patterns (completed)
- [ ] Design schema changes (in progress)
- [ ] Implement login endpoint
- [ ] Add password validation tests
- [ ] Add 2FA support
- [ ] Update API documentation
- [ ] E2E tests
```

Ask Claude to:
1. **Update** this file as it completes tasks
2. **Report progress** from it
3. **Prioritize** one task at a time and show its output

This breaks complex work into verified chunks and prevents the "surprise mess" of half-done features.[2]

### Solution 5: Test-Driven Development (TDD) Approach

Claude Code performs exceptionally well when given **concrete targets to implement against**. Use TDD:[3]

```
"Write failing tests first for the [feature] based on the requirements in docs/spec.md.
Do NOT implement the feature yet. Just confirm all tests fail as expected."
```

Then:
```
"Now implement code to make these tests pass. Do not modify the tests.
Keep iterating until all tests pass."
```

Tests act as unambiguous requirements that prevent Claude from interpreting the feature differently than your docs specify.[3]

### Solution 6: Manage Context with `/clear` Command

After completing a substantial task, use `/clear` to reset Claude's context window. Long sessions accumulate irrelevant conversation history that distracts Claude from current work. Start fresh with the task: Claude will re-read your CLAUDE.md and relevant files on demand.[3]

### Solution 7: Prevent Overreach with Explicit Constraints

Add to your prompts:

```
"Constraints:
- Only modify files explicitly required
- Do not refactor code outside the scope of this task
- Do not 'improve' code patterns not in the spec
- If you think something should change, ask first"
```

Claude tends to over-engineer and add features you didn't request. Being explicit about scope boundaries prevents this.[4]

### Implementation Checklist

**Immediate Actions:**
1. ✅ Create `CLAUDE.md` with paths to prd, ard, spec, data_model
2. ✅ Add this read-before-coding rule to CLAUDE.md
3. ✅ Create `.claude/commands/implement-feature.md` for standard workflow
4. ✅ Set a rule: "Ask for written plan before implementation"

**Per-Feature Process:**
1. Run `/implement-feature [description]` or explicitly ask Claude to read docs
2. Have Claude create a detailed plan in a markdown file
3. Review and approve plan before asking for implementation
4. Use TDD: write tests first, implement second
5. Run tests, type checks, linting before commit
6. Use `/clear` between unrelated tasks

**Team Scale-Up:**
- Check CLAUDE.md and custom commands into git
- Share across the team so everyone benefits
- Iterate on CLAUDE.md based on what works best
- Document patterns that prevent recurrence of past issues

### Why This Works

The core insight: **Claude Code works best when you engineer context explicitly.** It's not lazy—it's context-blind without guidance. By creating a persistent instruction layer (CLAUDE.md), enforcing a read-plan-code workflow, and using custom commands, you eliminate the situation where Claude makes decisions in a vacuum.

Your taskmaster, prd, ard, spec, and data_model files contain the truth about what should be built. **Make Claude read them first, every time.** That single habit prevents 80% of the "mess" you're experiencing.[2][3]

## Human

The problem is that we have multiple projects in P:/.  We are trying a constitution.md (from github.com speckit, and we have taskmaster, and then prd, ard, etc).  I don't think we have a solid best practice.

## Assistant

Perfect. Now I'll generate the comprehensive answer for multi-project Claude Code best practices.

## Multi-Project Claude Code: A Solid Best Practice Framework
You've identified the right problem. Multiple projects in `P:/` require a **three-layer governance structure** combining constitution, hierarchical CLAUDE.md files, and organized TaskMaster separation. The GitHub Spec Kit approach provides the template; here's how to operationalize it across your project portfolio.
### Layer 1: Shared Constitution (Organization Level)
The `constitution.md` file at `P:/constitution.md` is your **non-negotiable architectural DNA** that applies to all projects. This is not a per-project document; it's org-wide governance that ensures consistency across your portfolio.[1][2]

**Essential sections:**

- **Testing Standards**: Testing pyramid (unit/integration/E2E), coverage minimums, TDD approach
- **Code Quality Standards**: Linting rules, error handling patterns, naming conventions, max function length
- **Architecture Patterns**: Whether you use domain-driven design, port-adapter pattern, separation of concerns conventions
- **Tech Stack Guidelines**: When to use certain technologies, avoid future-proofing, "one way" principles
- **Deployment & Security**: CI/CD requirements, secret management, compliance checks
- **Amendment Process**: How constitution evolves (must be explicit, with rationale and backwards-compatibility assessment)

**Critical principle**: Constitution articles are **immutable**—they apply to all projects. This prevents each project from inventing its own rules. When you're working on project-a and need to decide between two architecture approaches, the constitution settles it.[2]

### Layer 2: Hierarchical CLAUDE.md (Three-Level Strategy)
Claude Code automatically loads CLAUDE.md files based on the folder being edited. Exploit this with a three-level structure:

**Level 1: Root CLAUDE.md (P:/CLAUDE.md) — Keep Under 13KB**[3]
This is your org-wide context. Include only:

```markdown
# Multi-Project Development

## Constitution
See [constitution.md](constitution.md) for non-negotiable principles.

## Project Directories
When you navigate to a project folder, read its CLAUDE.md:
- **project-a**: [1-sentence description]
- **project-b**: [1-sentence description]  
- **project-c**: [1-sentence description]

## Shared Patterns
@shared-libraries/patterns.md - Common architecture examples
@docs/testing-standards.md - Shared testing approach

## Multi-Project Workflow
1. Navigate to project folder: `cd P:/project-a`
2. Claude will auto-load `P:/project-a/CLAUDE.md`
3. Read that project's prd.md, ard.md, spec.md
4. When parsing tasks: `mcp_taskmaster-ai_parse_prd({ ... output: .taskmaster/tasks/project-a/ })`

## Tools Used Org-Wide (30%+ of projects)
[Only high-use tools; project-specific tools go in project CLAUDE.md]
```

The root CLAUDE.md acts as a **navigation hub**, not a context dump. By keeping it under 13KB and using `@` references for conditional loading, you prevent context bloat.[3]

**Level 2: Project-Specific CLAUDE.md (5-10KB each)**[3]

Each project folder (`P:/project-a/CLAUDE.md`, `P:/project-b/CLAUDE.md`, etc.) auto-loads when you edit in that directory. Claude will have access to both the root CLAUDE.md AND the project-specific one.

```markdown
# Project A: [Name]

## Constitution Reference
This project follows [constitution.md](../constitution.md).

## Local Documentation
- **PRD**: [prd.md](prd.md)
- **Architecture**: [ard.md](ard.md)
- **Technical Spec**: [spec.md](spec.md)
- **Data Model**: [data_model.md](data_model.md)

## Project-Specific Standards
[Anything unique to this project that deviates from constitution]

## Code Style & Patterns
[Project-specific patterns: folder structure, naming, framework conventions]

## Testing Approach for This Project
[How this project runs tests, specific test files, fixtures]

## Key Dependencies
[project-specific libraries, APIs, services this project uses]

## Before Any Work
1. Read prd.md and ard.md
2. Check data_model.md for schema
3. Review existing similar features in src/
```

When you navigate into `project-a/` and ask Claude to implement a feature, it will have loaded:
1. Root CLAUDE.md (org context)
2. project-a/CLAUDE.md (project context)
3. Plus whatever docs you explicitly ask it to read

This beats a single 47KB CLAUDE.md that dilutes all projects.[3]

**Level 3: Referenced Documentation** (`@` syntax)

Use `@` references in CLAUDE.md for docs that should load on-demand, not at startup:

```markdown
## Database Schema
See @data_model.md for complete schema and relationships.

## Testing Examples
See @docs/test-patterns.md for framework-specific test templates.
```

The `@` reference tells Claude "this exists and is available if you need it," without loading it into memory at session start. This keeps initial context lightweight.[3]

### Layer 3: TaskMaster Organization (Strict Separation)
Your `.taskmaster/` folder structure is critical for preventing cross-project contamination:[4]

```
.taskmaster/
├── docs/
│   ├── shared-constitution.md  ← Reference to P:/constitution.md
│   ├── project-a-prd.md        ← PRD for project-a
│   ├── project-b-prd.md        ← PRD for project-b
│   └── project-c-prd.md        ← PRD for project-c
└── tasks/
    ├── project-a/              ← ONLY project-a tasks here
    │   ├── tasks.json
    │   └── task_*.txt
    ├── project-b/              ← ONLY project-b tasks here
    │   ├── tasks.json
    │   └── task_*.txt
    └── project-c/              ← ONLY project-c tasks here
        ├── tasks.json
        └── task_*.txt
```

**Critical rule**: Each PRD gets its own project directory in `tasks/`. Never put multiple projects' tasks in the same directory.[4]

When parsing a PRD:

```powershell
# For project-a: output to project-a/ directory
mcp_taskmaster-ai_parse_prd({
  projectRoot: "P:\project-a",
  input: "P:\.taskmaster\docs\project-a-prd.md",
  output: "P:\.taskmaster\tasks\project-a\tasks.json",
  numTasks: 12
})

# For project-b: output to project-b/ directory
mcp_taskmaster-ai_parse_prd({
  projectRoot: "P:\project-b",
  input: "P:\.taskmaster\docs\project-b-prd.md",
  output: "P:\.taskmaster\tasks\project-b\tasks.json",
  numTasks: 12
})
```

This separation prevents Claude from confusing which task belongs to which project and prevents "dependency contamination" where project-b's task accidentally references project-a's code.[4]

### Integrated Workflow: Putting It Together
**When starting work on a feature in project-a:**

1. **Navigate to project**: `cd P:\project-a`
2. **Claude auto-loads**: root CLAUDE.md + project-a/CLAUDE.md
3. **Ask Claude to read docs**: "Before implementing, read prd.md, ard.md, spec.md, and data_model.md"
4. **Get explicit plan**: Claude outlines files to change, data schema impact, test strategy
5. **Load tasks**: `mcp_taskmaster-ai_load_tasks({ directory: "P:\.taskmaster\tasks\project-a" })`
6. **Pick a task**: Claude selects next incomplete task from project-a-specific task list
7. **Implement**: Claude refers to constitution for patterns, project-a/CLAUDE.md for specifics
8. **Commit**: Code committed to project-a only, no cross-project contamination

**When pivoting to project-b:**

1. **Navigate**: `cd P:\project-b`
2. **Claude automatically re-loads**: root CLAUDE.md + project-b/CLAUDE.md (totally different context)
3. **Different tasks loaded**: TaskMaster reads from `P:/.taskmaster/tasks/project-b/`, not project-a/
4. No bleeding of context, no task confusion

### Spec Kit Integration (Optional Enhancement)
If using GitHub Spec Kit with this structure, each project can have its own `.specify/` folder:[2]

```
project-a/
├── CLAUDE.md
├── prd.md / ard.md / spec.md
├── .specify/
│   ├── memory/
│   │   └── constitution.md (can reference P:/constitution.md)
│   ├── templates/
│   └── scripts/
└── src/

project-b/
├── CLAUDE.md
├── .specify/
│   ├── memory/
│   │   └── constitution.md (references P:/constitution.md)
```

When you use `/specify`, `/plan`, or `/tasks` commands, they operate within that project's scope and write outputs to that project's `.taskmaster/tasks/project-x/` directory.[2]

### Setup Checklist for P:/
**Phase 1: Create Shared Governance (1-time)**
- [ ] Write `P:/constitution.md` with your org's non-negotiable principles
- [ ] Create `P:/CLAUDE.md` (root navigation hub, <13KB)
- [ ] Set up `.taskmaster/docs/` and `.taskmaster/tasks/` structure

**Phase 2: Per-Project Setup (repeat for each project)**
- [ ] Create `project-x/CLAUDE.md` (5-10KB, references constitution)
- [ ] Move (or ensure exists): `project-x/prd.md`, `project-x/ard.md`, `project-x/spec.md`, `project-x/data_model.md`
- [ ] Create `.taskmaster/tasks/project-x/` directory
- [ ] Parse PRD: `mcp_taskmaster-ai_parse_prd({ ... output: .taskmaster/tasks/project-x/ })`

**Phase 3: Team Alignment**
- [ ] Commit constitution.md and root CLAUDE.md to version control
- [ ] Document in root README how to work with multi-project structure
- [ ] Set team policy: "Always navigate to project folder before starting work"

### Common Pitfalls to Avoid
**Pitfall 1: Single Shared PRD**
Don't store all PRDs in root `.taskmaster/docs/`. Each project needs separate parsing because TaskMaster can't distinguish scope otherwise. One PRD = one output directory.[4]

**Pitfall 2: Bloated Root CLAUDE.md**
If root CLAUDE.md exceeds 13KB, it's too detailed. Move project-specific patterns, tools, and guidance to project CLAUDE.md files. Root should be a navigation hub.[3]

**Pitfall 3: Constitution Creep**
Constitution should have 8-12 core articles covering non-negotiable principles. If it's >50KB or includes decision trees for specific projects, it's become a project guide (move to project CLAUDE.md).[2]

**Pitfall 4: Cross-Project Task Confusion**
Never mix project-a and project-b tasks in the same `.taskmaster/tasks/` directory. Claude will get confused about scope and may implement project-b features using project-a's patterns.[4]

This three-layer structure (constitution + hierarchical CLAUDE.md + TaskMaster separation) is now the **industry standard for multi-project AI-assisted development**. It scales from 2 projects to 20 projects without architectural rework.[1][2][3][4]

## Human

Is that a best practice to use taskmaster and speckit?

## Assistant

Let me write a comprehensive final answer based on all the research I've gathered.

## TaskMaster vs. Spec Kit: Best Practice Framework

This is a genuinely nuanced question because **both tools are best practices, but they optimize for different scenarios**. You should decide based on your team structure, not pick one "winner."

### TaskMaster's Strength: Breaking Down Complexity at Scale

TaskMaster excels at **converting PRDs into executable task lists with dependency tracking**. The workflow is:[1]

```
Requirements → PRD → Parse to Tasks → Task Loop
```

Real-world evidence is compelling: developers have shipped complete production applications (full Next.js apps with payments, APIs, complex UIs) using TaskMaster without writing manual code. The system:[2]

- **Analyzes task complexity** and automatically suggests breaking down high-complexity items into subtasks[1]
- **Maintains persistent task state** across `/clear` operations (not conversation-dependent)
- **Integrates natively** with Claude Code via MCP with **no token surcharge**—all requests use your Claude Code subscription tokens[1]
- **Tracks dependencies** between tasks automatically, so it suggests next task logically based on prerequisites[1]

**Best for**: Solo developers, small teams without a dedicated PM role, complex projects with 20+ tasks, or situations where you're iterating on features continuously.

### Spec Kit's Strength: Architectural Governance & Planning

Spec Kit enforces **upfront, constitutional planning before any code is written**. The structure is:[3]

```
Constitution (Governance) → Spec (Planning) → Plan (Architecture) → Tasks → Implement
```

The philosophy: your constitution.md is non-negotiable, so all work aligns with your architectural DNA before development starts. Real users report: "Surpasses Taskmaster and my existing SDD workflows."[4]

Spec Kit excels at:

- **Enforcing architectural compliance** through constitution articles (testing standards, code patterns, tech choices)[3]
- **Clear phase gates**: `/specify` → `/plan` → `/tasks` → implement, with explicit approval steps between phases[3]
- **GitHub integration**: automatic branch creation, syncing specs to repos as documentation[3]
- **Team role separation**: clear distinction between Product Owner (who writes spec/plan) and Developer (who implements)[3]
- **Junior developer guidance**: detailed specs provide guardrails and context[3]

**Best for**: Teams with a PM or architect role, multiple projects needing unified standards, junior developers who benefit from detailed guidance, or situations where you need GitHub-synchronized documentation.

### Real-World User Feedback

**Pro-TaskMaster advocates** emphasize: "Only spec-driven tool I can genuinely recommend for production use. Spec Kit/OpenSpec aren't ideal for production." Reasoning: lower token overhead, faster iteration, better for handling unforeseen complexity mid-project.[5]

**Pro-Spec Kit advocates** say: "Better planning phase results in fewer downstream surprises. Clear phase structure prevents vibe coding." Their point: architectural decisions made upfront prevent costly rework.[4]

### The Practical Answer: Use Both (Hybrid Approach)

Production teams are moving toward **combining both tools**:[6]

1. **Spec Kit for strategic planning**: Use `/specify` and `/plan` to enforce constitution and make architectural decisions with the PM
2. **TaskMaster for tactical execution**: Once plan is approved, parse it to TaskMaster for task breakdown and dependency management
3. **Spec Kit as living documentation**: Archive completed specs back to your repo as reference material

**Workflow**:
```
PRD + Constitution → Spec Kit /plan (architecture + gates) → 
Export to PRD format → TaskMaster parse_prd → 
TaskMaster task loop (implement task-by-task) → 
Done
```

This way:
- Spec Kit provides **governance and architecture enforcement** (your constitution prevents bad decisions)
- TaskMaster provides **task granularity and persistent progress tracking** (you don't lose context with `/clear`)
- You avoid token waste by running Spec Kit's verbose planning once, then using TaskMaster's efficient task loop for implementation

### Your Multi-Project Scenario (P:/)

For **multiple projects in P:/**:

- **Shared governance**: One `constitution.md` at `P:/constitution.md` enforced across all projects (use Spec Kit `/specify` to validate against it)
- **Per-project planning**: Each project runs Spec Kit `/plan` once to produce an approved architectural plan
- **Task execution**: Parse each project's plan into `.taskmaster/tasks/project-x/` and execute the task loop
- **Result**: You get Spec Kit's governance (constitution) + TaskMaster's execution efficiency (persistent tasks)

### My Recommendation for Your Setup

Based on your context (solo developer, multiple projects, existing constitution.md, TaskMaster in use):

**Go with TaskMaster as your primary tool** because:

1. **Token efficiency**: No extra cost, uses your Claude Code subscription
2. **Solo dev workflow**: You're your own PM, so Spec Kit's PM/Dev separation adds overhead
3. **Persistence**: Tasks stay available across `/clear`, crucial for context management across multiple projects
4. **Complexity handling**: Your multi-project scenario benefits from dependency tracking TaskMaster provides
5. **Existing infrastructure**: You already have taskmaster configured

**Use Spec Kit strategically** for:
- Initial planning of major features (one-time use of `/specify` and `/plan`)
- Enforcing constitutional compliance before TaskMaster task parsing
- Generating living documentation (archive specs back to repos)

**Implementation**:
```
1. Define constitution.md (shared across all projects)
2. Per new feature: Run Spec Kit /specify + /plan once
3. Approve plan, then parse to TaskMaster PRD format
4. Use TaskMaster /show_tasks and task loop for implementation
5. Archive final spec to docs/ for future context
```

This hybrid approach scales cleanly across P:/ without tool bloat.[6]

## Human

Show me the idealized file structure for claude.md, taskmaster, speckit.

## Assistant

Perfect! Now let me generate the final summary response.

***

## Idealized File Structure: CLAUDE.md + TaskMaster + Spec Kit
I've created two comprehensive reference documents for you:
**Document 1: Complete File Structure & Content Examples** (`multi-tool-structure.md`)
- Full directory tree with annotations
- Example content for each key file:
  - `P:/constitution.md` (6-article governance template)
  - `P:/CLAUDE.md` (root navigation hub)
  - `project-a/CLAUDE.md` (project-specific context)
  - `.taskmaster/docs/project-a-prd.md` (TaskMaster input format)
  - `.taskmaster/tasks/project-a/task_*.txt` (individual task files)
- Shows exactly what goes in each file

**Document 2: Setup Checklist & Quick Reference** (`setup-checklist.md`)
- One-time setup checklist (create shared governance)
- Per-project setup checklist (repeat for each project)
- Daily workflow guide with command examples
- File size guidelines for each type
- Troubleshooting common issues
- Example: "Creating Project-Y from Scratch"
### Key Architecture Highlights
**Three-Layer Structure:**

1. **Constitution.md** (Org-wide, shared)
   - 6-8 core articles defining non-negotiable principles
   - Testing standards, code quality, architecture patterns
   - Referenced by all projects, enforced by Spec Kit /specify and /plan

2. **CLAUDE.md (Hierarchical)**
   - **Root** (`P:/CLAUDE.md`): Navigation hub, <13KB
   - **Per-project** (`project-x/CLAUDE.md`): Context auto-loads when editing, 5-10KB
   - Claude auto-loads appropriate CLAUDE.md based on current folder

3. **Spec Kit** (Planning & Governance)
   - `.specify/memory/constitution.md` - reference for validation
   - `.specify/templates/` - planning templates
   - `/specify` command validates against constitution
   - `/plan` command generates `spec.md` (implementation architecture)
   - Output feeds into TaskMaster

4. **TaskMaster** (Execution & Progress)
   - `.taskmaster/docs/` - one PRD per project (input)
   - `.taskmaster/tasks/project-x/` - project-separated task lists (persistent)
   - `/show_tasks` and `/next_task` commands
   - Tasks survive `/clear` operations (unlike conversation history)

### Data Flow
```
Requirements → PRD (prd.md) → Spec Kit /plan → spec.md (architecture)
                                                     ↓
                                        Export to TaskMaster format
                                                     ↓
                                        parse_prd → task list
                                                     ↓
                                        Claude Code implements task-by-task
                                                     ↓
                                        Commit to project-x/src/
```

### Context Loading Rules
When you open Claude Code:
- **Edit in `P:/` root** → loads `P:/CLAUDE.md` only
- **Edit in `P:/project-a/`** → loads `P:/CLAUDE.md` + `P:/project-a/CLAUDE.md`
- **Switch to `P:/project-b/`** → context resets, loads `P:/CLAUDE.md` + `P:/project-b/CLAUDE.md`
- **Use `@data_model.md`** → Claude loads on-demand (not upfront)

This prevents context bloat and keeps Claude focused.

### Your Implementation Path
For your current setup (`P:/` with multiple projects + existing `constitution.md` + `taskmaster`):

1. **Create root `P:/CLAUDE.md`** pointing to each project with one-line descriptions
2. **Create `project-x/CLAUDE.md`** for each project (5-10KB, project-specific)
3. **Organize `.taskmaster/`** with project-separated task directories
4. **Set up `.specify/`** with planning templates (optional, enhances Spec Kit)
5. **Use the hybrid workflow**: Spec Kit for planning gates → TaskMaster for task execution

This structure scales from 2 projects to 20+ without rework and prevents the "context mess" you're experiencing by isolating project contexts and enforcing governance through shared constitution.

Both reference documents are ready to use as templates. Customize the constitution articles and project structures to match your actual tech stack and team needs.
