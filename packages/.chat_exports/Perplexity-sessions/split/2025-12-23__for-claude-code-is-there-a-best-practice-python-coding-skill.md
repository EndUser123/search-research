---
title: "for claude code, is there a best practice python coding skill for dec 2025?"
date: "2025-12-23"
mode: "COPILOT"
uuid: "6420e14d-d978-4e60-96c9-b82d8c55e1ce"
entry_count: 5
---

## Human

for claude code, is there a best practice python coding skill for dec 2025?

## Assistant

Now I have comprehensive information. Let me compile a professional research report on Claude Code Python best practices for December 2025.

Based on the latest December 2025 documentation and community best practices, here is the definitive guide to Python coding best practices for Claude Code:

## Python Coding Best Practices for Claude Code (December 2025)

### Core Framework: The CLAUDE.md Strategy

The foundational practice for December 2025 is creating a project-specific `CLAUDE.md` file—essentially a persistent "brain" for Claude Code that automatically loads at the start of every session. For Python projects, this should document:[1][2][3]

**Python-Specific Guidelines**
- Framework choice (FastAPI, Django, Flask) with version and core patterns
- ORM approach (SQLAlchemy with Pydantic for request/response schemas)[4]
- Database strategy (SQLite for development, PostgreSQL for production)[4]
- Code style enforcement (Black formatting, flake8 linting, type hints everywhere)[3]
- Testing framework and coverage expectations (pytest is the standard)[2][1]
- Import patterns ("no wildcard imports," preferring explicit imports)[3]

**Security-First Documentation**
- Mandate parameterized queries or ORM-only (never raw SQL concatenation to prevent injection)[2][3]
- Environment variable handling for secrets—explicitly note `.env.example` patterns[3]
- Input validation via Pydantic models; output sanitization requirements[3]
- Dependency pinning and audit workflows (`pip-audit` or similar)[3]

**Build and Run Commands**
Document exact commands: `pytest` (for testing), `black . && flake8 .` (for formatting/linting), `docker build` (for containerization), and any custom scripts.[1][2]

### Multi-Phase Workflow: Plan → Execute → Validate

The definitive December 2025 workflow separates analysis, implementation, and validation:[5][2][3]

**Phase 1: Planning with Extended Thinking**
Ask Claude to "think" or "think hard" (phrases that allocate extended thinking budget) before coding. Explicitly instruct: *"Create a detailed plan for adding user authentication. Do not write code yet."* This forces Claude to decompose requirements logically, identify affected files, and reason through potential pitfalls.[5]

**Phase 2: Implementation with Context**
Once the plan is approved, use custom prompts with specific file references. Example:
- Reference exact files: `"Update backend/models.py and frontend/auth.tsx following the plan"`
- Provide URLs to documentation: Paste FastAPI or Pydantic docs directly[5]
- Use images: Screenshot API designs or database diagrams[5]

**Phase 3: Validation with Automated Testing**
Define a `/test` command that runs `pytest --cov` automatically, catches failures, and enters a debugging loop without manual intervention.[1][2]

### Custom Skills for Python-Specific Context

As of October 2025, Claude Code supports **Skills**—auto-loaded context snippets triggered by keywords. Create `.claude/skills/` files for Python projects:[6]

**"Python Security Best Practices" Skill**
- Auto-invoke: When editing Python files or on keywords like "SQL," "password," "auth"
- Content: Explicit rules against raw SQL, password logging, and missing auth checks on protected endpoints[2][3]

**"Pydantic & FastAPI Patterns" Skill**
- Auto-invoke: When working with API endpoints or data models
- Content: Examples of correct Pydantic validation, FastAPI dependency injection, and route organization patterns

**"Database Schema Reference" Skill**
- Auto-invoke: On keywords like "query," "migration," "schema"
- Content: Your actual PostgreSQL schema and table relationships to prevent hallucinated column names[2]

### Slash Commands for Automation

Create reusable commands in `.claude/commands/` directory:[2][5]

```yaml
# /py-test: Run full test suite with coverage
/py-test → pytest --cov=backend --cov-report=term-missing

# /format-py: Black + flake8 in one command  
/format-py → black . && flake8 . && mypy .

# /db-migrate: Run Alembic migrations
/db-migrate → alembic upgrade head
```

The `/go` command is particularly powerful—structure it to always use Context7 (for live FastAPI/SQLAlchemy docs), Serena (for semantic code search), and Sequential Thinking before implementation.[1][3]

### Git Workflow for Safety

Always require Claude to work on feature branches, never `main`:[5]
```bash
git checkout -b feature/user-auth
```

For complex parallel work, use **Git worktrees**—check out multiple branches simultaneously in different directories, allowing isolated Claude instances to work independently.[2]

### MCP Integration for Python Excellence

Integrate Model Context Protocol servers for December 2025 workflows:[1][3]

- **Context7**: Fetches real-time FastAPI, SQLAlchemy, and Pydantic documentation—preventing stale API usage
- **Serena**: Semantic code search across Python modules (e.g., "Where do we validate user input?")
- **Sequential Thinking**: For complex backend logic planning (database migrations, authentication flows)

These MCPs transform Claude from a code generator into a knowledge-aware partner that always uses current best practices.

### Hooks for Deterministic Quality Gates

Set up automatic validation hooks that run on file edits:[7]

```json
{
  "hooks": [
    {
      "matcher": "Edit",
      "type": "command",
      "command": "black \"$CLAUDE_FILE_PATHS\" && flake8 \"$CLAUDE_FILE_PATHS\""
    },
    {
      "matcher": "Edit",
      "type": "command",
      "command": "if /\"$CLAUDE_FILE_PATHS\" =~ \\.py$; then mypy \"$CLAUDE_FILE_PATHS\"; fi"
    }
  ]
}
```

This ensures code is formatted and type-checked *automatically* without Claude needing reminders.

### Subagents for Specialized Roles

Define separate agent personas for complex workflows:[1][3]

**Backend Planner Agent**
- Tools: Read-only access + Serena + Context7
- Role: Analyze requirements, design API endpoints, outline database schema
- Output: Structured markdown plan with Pydantic models and migration steps

**Python Coder Agent**
- Tools: Full write access with formatting hooks
- Role: Implement according to approved plan, strictly adhering to style rules

**QA/Testing Agent**
- Tools: Bash (for pytest), read-only code access
- Role: Run tests, analyze failures, suggest debug approaches

This separation prevents a single agent from jumping between planning and coding, which typically produces lower-quality results.

### Headless Mode for CI/CD Automation

For production pipelines, use headless mode:[1][2]

```bash
claude -p "Run pytest on all backend tests. Return JSON with pass/fail status" --output-format json
```

This integrates Claude into scripts, GitHub Actions, or pre-commit hooks without interactive prompts.

### Context Management Best Practices

**Use `/clear` between unrelated tasks** to prevent context contamination. When a session exceeds 10,000 tokens of history, context becomes diluted—clearing ensures fresh focus.[5][2]

**Prefer specific file references** over vague instructions. Instead of:
- ❌ "Fix the authentication bug"

Use:
- ✅ "Debug `backend/auth.py` lines 42-67. The test in `test_auth.py::test_login_invalid_credentials` is failing because [error details]. Research the issue and fix it."[2][5]

### Team Standardization via Plugins

For December 2025, package your setup as a Claude Code **plugin** to share across teams:[3][1]
- Pre-configured MCP servers (Context7, Serena, Sequential Thinking)
- Shared slash commands (`.claude/commands/`)
- Team-wide CLAUDE.md template
- Hooks for code formatting and type checking

Installation becomes: `/plugin install team-python-stack` and Claude instantly operates with standardized practices.

### Critical Security Rules for Python

These **must** be documented in CLAUDE.md or Skills:[3][2]

| Rule | ✅ Correct | ❌ Never Do |
|------|-----------|------------|
| Database queries | SQLAlchemy ORM / parameterized SQL | f-string SQL: `f"SELECT * FROM users WHERE id={id}"` |
| Secrets | `os.getenv("API_KEY")` + `.env.example` | Hardcoded in code or git history |
| Auth | Check permissions on every protected endpoint | Assume "If endpoint exists, user can access it" |
| Input validation | Pydantic models for all request data | Trust user input directly |
| Logging | Never log passwords, tokens, PII | Debug-log everything for convenience |

### Performance Expectations with These Practices

Adopting this December 2025 framework typically yields:[5][1][2][3]

- **60-70% faster development** for standard CRUD and API features (compared to writing from scratch)
- **80%+ fewer bugs** reaching testing through automated validation hooks
- **Consistent code quality** via enforced style rules
- **Reliable iterative improvements** through the plan-execute-validate loop

### The Bottom Line

Claude Code in December 2025 excels with **explicit constraints and clear phases**. The model is powerful enough to handle complex Python architectures (FastAPI + SQLAlchemy + PostgreSQL), but only when you provide specific guidance via CLAUDE.md, Skills, custom commands, and MCP integration. The pattern is: **constrain context → separate phases → enforce validation → iterate quickly**. This transforms Claude Code from a code generator with "amnesia" into a dependable development partner capable of handling production Python workflows.[1][2][3][5]

## Human

I was thinking more in line with claude code marketplaces, plugins, and skills.

## Assistant

Based on the latest December 2025 information, here's the authoritative guide to Claude Code marketplaces, plugins, and skills:

## Claude Code Marketplaces, Plugins & Skills: December 2025 Best Practices

### The Core Ecosystem Architecture

As of December 2025, Anthropic has released three interconnected systems that form Claude Code's extensibility platform:[1][2]

**Skills** → Auto-invoked context providers triggered by semantic matching  
**Plugins** → Bundled packages containing skills, subagents, commands, and hooks  
**Marketplaces** → Git-based distribution repositories for discovering and installing plugins

Understanding when to use each is critical for modern Claude Code workflows.

### Skills: Auto-Invoked Context Providers

Skills are the foundational unit—portable `.md` files that Claude automatically loads based on semantic similarity to your current work context. They're not manually invoked; Claude's language model decides when to apply them based on description matching against conversation context.[3][4]

**Directory Hierarchy**[1]

```
~/.claude/skills/           # Personal skills (global, all projects)
.claude/skills/            # Project-specific skills
.claude/skills/shared/     # Template skills for reuse
```

**Critical Success Factor: Description Engineering**[1]

Generic skill descriptions fail silently. The winning pattern is **WHEN + WHEN NOT**:

```
✅ CORRECT:
description: Stakeholder context for Test Project when discussing product 
features, UX research, or stakeholder interviews. Auto-invoke when user 
mentions Test Project, product lead, or UX research. Do NOT load for 
general stakeholder discussions unrelated to Test Project.

❌ FAILS:
description: Provides information about stakeholders
```

The specificity difference is dramatic. One developer's refactored skill descriptions went from a 62/100 evaluation score to 82-85/100 simply by adding "WHEN NOT" clauses and possessive pronouns ("HIS/HER work" instead of generic pronouns).[1]

**Real-World Example: Personal User Manual Skill**[1]

A personal skill describing work preferences, communication style, and collaboration methods:

```
Auto-invoke when drafting HIS emails, Slack messages, or internal updates; 
planning HIS work or tasks; optimising HIS productivity workflows; 
discussing HIS collaboration approach. 

Do NOT load for external blog posts, customer-facing communications, or 
public documentation unless John explicitly requests.
```

Testing showed the resulting Slack message differed significantly—noticeably more concise and aligned to the user's actual communication style—compared to output without the skill loaded.[1]

**Skills Marketplace: SkillsMP**[5][4]

The ecosystem includes SkillsMP (skillsmp.com), a curated marketplace hosting 25,000+ agent skills compatible with Claude Code as of December 2025. These use the standardized SKILL.md format, which OpenAI adopted for ChatGPT and Codex CLI, making skills a true open standard.[4][5]

### Subagents: Workflow Orchestrators

Subagents are explicitly invoked agents that guide multi-step processes. Invoke them via `@agent-name` or the Task tool. Unlike skills, they execute specific workflows rather than providing ambient context.[1]

**Critical Learning: Conciseness Over Comprehensiveness**[1]

A developer's first-pass skill-creator-agent was 803 lines with an eval score of 62/100. After refactoring to extract repetitive patterns into separate skills:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Lines of code | 803 | 281 | -65% reduction |
| Eval score | 62/100 | 82-85/100 | +30 points |
| Functionality | Full | Full (unchanged) | Zero loss |

The refactor removed 5 duplicate TODO structures, extracted a 130-line template section into a skill file, and consolidated redundant checklists. **More lines do not equal better instructions**—Claude executes better with concise, well-structured guidance.[1]

**The Hybrid Pattern: Subagent Analysis + Main Claude Execution**[1]

A validated architectural pattern for security and maintainability:

- **Subagent Tools** (read-only): Read, Grep, Glob, TodoWrite (planning/analysis only)
- **Main Claude Tools** (modification): Write, Edit, Bash (execution only)

This preserves tool access control while enabling workflow automation—subagents plan, main Claude executes.

### Slash Commands: Workflow Shortcuts

Commands are user-initiated shortcuts saved to `.claude/commands/` and triggered via `/command`. They're stored as simple prompt files or bash scripts.[1]

**Common patterns:**

```
/create-skill      → Invokes skill-creator-agent for interactive creation
/validate-skill    → Invokes skill-validator-agent for verification
/list-skills       → Bash script listing all available skills
/py-test           → pytest --cov=backend --cov-report=term-missing
/format-py         → black . && flake8 . && mypy .
```

Commands are faster than typing `@agent-name` or explaining workflows repeatedly. They formalize frequently-used patterns.[1]

### Plugins: Bundled Distribution Packages

Plugins are the game-changer for team adoption and sharing. A single plugin bundles skills, subagents, commands, and hooks as a cohesive, versioned package.[2][6]

**What's Inside a Plugin:**[2]

According to Anthropic's specification, plugins can contain any combination of:

- Custom slash commands (`.claude/commands/`)
- Subagents (`.claude/agents/`)
- Tools via MCP servers
- Hooks (automatic validation/execution rules)
- Skills (context providers)

**Installation via Marketplace:**[7][1]

Instead of cloning multiple repos, the plugin system enables single-command installation:

```bash
# Clone the marketplace
git clone https://github.com/YoungLeadersDotTech/young-leaders-tech-marketplace.git

# Navigate to plugin
cd young-leaders-tech-marketplace/plugins/skills-toolkit

# Run install script
./install.sh
```

The script automatically:
- Detects Claude Code configuration directory
- Copies agents to `.claude/agents/`
- Copies commands to `.claude/commands/`
- Copies skill templates to `.claude/skills/shared/`
- Verifies successful installation

**No manual file management. No missing dependencies.**[1]

### Claude Code Plugin Marketplaces

Marketplaces are Git-based repositories that host versioned plugins for discovery and distribution.[6][7][2]

**Key Features (December 2025):**[6][2]

| Feature | Purpose |
|---------|---------|
| Curated plugin directory | Browseable catalog with categories, tags, documentation |
| Version control | Git-tracked updates; re-running install script gets latest |
| Team distribution | Fork for internal customization; share URL with team |
| Governance | Centralized discovery, version management, access control |
| Single-command installation | `/plugin install [plugin-name]` or via marketplace script |

**Official Marketplaces Emerging December 2025:**[2]

- **Anthropic marketplace** (`anthropics/claude-code`): Official Anthropic plugins including "feature-dev" (multi-agent development workflow)
- **Community marketplaces**: Third-party hosts like YoungLeadersDotTech, open-source contributions
- **Enterprise marketplaces**: Internal company repositories with custom workflows

**Team Rollout Workflow:**[1]

1. Share marketplace URL with team
2. Document which plugins solve which problems
3. Consider forking marketplace for internal customization
4. Use Git to keep everyone's installations in sync
5. Pull latest changes and re-run install scripts for updates

### Real-World Plugin: Skills Toolkit (October 2025)

A community example demonstrating the plugin pattern:[1]

**Contents:**
- 2 subagents (skill-creator-agent, skill-validator-agent—refactored to 281 and 306 lines respectively)
- 3 slash commands (/create-skill, /validate-skill, /list-skills)
- 4 professional skill templates (stakeholder, ground truth, product context, initiative overview)
- Automatic installation script with verification
- Full documentation

**Why it matters:** Instead of sharing scattered markdown files or complex manual setup instructions, users get a single, versioned package with one-command installation.[1]

### Skills Engine Architecture: How It Works

The system uses a meta-tool architecture where a tool named `Skill` acts as a dispatcher.[4]

**Skill Selection Mechanism:**[4]

- No algorithmic routing or intent classification at code level
- No embeddings, classifiers, or regex pattern matching
- Pure LLM reasoning: Claude's transformer decides which skills to invoke
- All available skills are formatted into text descriptions in the `Skill` tool's prompt
- Claude's language model makes the decision via forward pass reasoning

This is fundamentally different from traditional tool routing—it's pure semantic matching inside Claude's computation, not external logic.[4]

### Practical Implementation: When to Use Each

**Decision Tree:**[1]

- **"I want Claude to remember X automatically"** → Create a **Skill**
- **"I want to automate Y workflow step-by-step"** → Create a **Subagent**
- **"I use subagent Z frequently and want a shortcut"** → Create a **Command** (invoking the subagent)
- **"I want to share my entire setup with others/team"** → Package as a **Plugin** (bundle all three)

**When to Use Skills vs MCP Servers:**[3]

Use **Skills** when:
- Running workflows 3+ times per week
- Enforcing team-wide consistency (code review, documentation standards)
- Combining built-in tools (file operations, web search, code analysis)
- Sharing workflows across distributed teams via Git
- Auditing AI-assisted work for compliance

Use **MCP Servers** when:
- Integrating external systems (CRM, databases, proprietary APIs)
- Real-time data requirements (live stock prices, sensor readings)
- Heavy computational tasks (video processing, ML training)
- Building customer-facing AI features
- Orchestrating multi-agent systems

### The Claude Code Marketplace Ecosystem (December 2025 Status)

Three major hubs exist:[7][6]

| Hub | Purpose | Status |
|-----|---------|--------|
| **Claude Code Plugin Hub** (claudecodeplugin.org) | Navigation site for discovering plugins and comparing marketplaces | Active, curated |
| **SkillsMP** (skillsmp.com) | Curated marketplace of 25,000+ skills in open standard SKILL.md format | Production, 25K+ skills |
| **Claude Code Plugins CLI** (claude-plugins.dev) | Open-source CLI tool for discovering and installing plugins without manual marketplace setup | Community-maintained |

**Plugin System Status:** Beta as of late 2025, moving toward production release.[2]

### Best Practices for December 2025

1. **Start with Skills, not Subagents** – Use auto-invoked skills for ambient context (preferences, project info, team standards). This reduces conversation overhead compared to manually invoking agents.

2. **Engineer Skill Descriptions Ruthlessly** – WHEN + WHEN NOT pattern is non-negotiable. Test descriptions with real workflows. Generic descriptions cause silent failures.

3. **Keep Subagents Concise** – Target 300-400 lines maximum. Refactor repetitive patterns into separate skills. Eval scores improve 20-30 points by removing verbosity.

4. **Use the Hybrid Pattern** – Subagents analyze (read-only tools), main Claude executes (modification tools). This maintains security boundaries while automating workflows.

5. **Package Shareable Setups as Plugins** – If you're reusing a workflow across projects or sharing with teams, bundle it as a plugin in a marketplace. One-command installation beats manual setup every time.

6. **Maintain Marketplace Discipline** – Version control skills and plugins via Git. Document which plugin solves which problem. Make updates simple: `git pull && ./install.sh`.

7. **Watch the Skill Coordination** – Claude successfully loads complementary skills together. Personal + Project skills coexist without conflicts. Leverage this for layered context.

### What's Coming

The platform is moving toward enterprise-grade automation. Anthropic's roadmap hints at deeper MCP integration, cross-plugin tool sharing, and standardized skill evaluation/versioning. The open SKILL.md format adoption by OpenAI signals this is becoming industry standard rather than Anthropic-specific.[5][4]

For a technical developer like yourself optimizing LLM workflows, the December 2025 plugins + marketplaces + skills ecosystem is the foundation for building production-grade Claude Code automation at scale.[3][2][1]

## Human

Ok, for python coding in dec 2025, is there a best practice SKILL.md?

## Assistant

Now I have comprehensive information. Let me compile a professional guide on best practice SKILL.md patterns for Python coding in December 2025.

## Best Practice SKILL.md for Python Coding (December 2025)

Based on the latest standards, here's the definitive SKILL.md template and best practices for Python development in Claude Code:

### Core Structure: The Two-Part SKILL.md Pattern

Every Python-focused SKILL.md follows this architecture:[1][2]

```
---
[YAML FRONTMATTER - Configuration Layer]
---

# [Markdown Content - Instruction Layer]
```

The frontmatter loads first (just 50-100 tokens), giving Claude metadata for discovery. The markdown content loads only when triggered, containing detailed instructions.[3]

### Frontmatter: The Discovery Layer

**Required Fields**[2]

| Field | Purpose | Python Example |
|-------|---------|---|
| `name` | Skill identifier (lowercase, hyphens only, max 64 chars) | `python3-development` |
| `description` | Claude uses this for skill selection via LLM reasoning (max 1024 chars) | `"Guide for Python 3.11+ development using TDD, type hints, and modern patterns. Use when writing Python code, debugging errors, creating CLI apps, designing packages, or running tests."` |

**Optional but Recommended Fields**[1][3][2]

```yaml
---
name: python3-development
description: "Modern Python 3.11+ development with TDD, type hints, and quality gates. Use when writing Python scripts, CLI applications with Typer/Rich, designing packages, debugging errors, running tests, or reviewing code against best practices."
allowed-tools: "Read,Write,Bash,Edit,Glob,Grep"
version: 2.0.0
license: MIT
---
```

**Critical: The `allowed-tools` Field**[3][2]

Apply **principle of least privilege**. Only grant what the skill needs:

```yaml
# ✅ Python development - comprehensive but focused
allowed-tools: "Read,Write,Bash,Edit,Glob,Grep"

# ✅ For script execution with path scoping
allowed-tools: "Bash(python {baseDir}/scripts/*:*),Bash(pytest:*),Read,Write"

# ❌ Too permissive - security risk
allowed-tools: "Bash,Read,Write,Edit,Glob,Grep,WebSearch,Task,Agent"
```

### Markdown Content: The Instruction Layer

**Critical: Keep Under 500 Lines**[4][1]

If you exceed 500 lines, split into reference files and link from SKILL.md. Progressive disclosure prevents context bloat.[1]

**Recommended Structure for Python Skills**[4][1]

```markdown
# Python Development

## Purpose Statement
[1-2 sentence overview of when this skill applies]

## Core Concepts
### Python Version & Standards
[Python 3.11+ requirements, type hints expectations]

### Quality Gates
[Required tools: ruff, mypy, pytest with coverage thresholds]

## Instructions
### When Writing New Code
1. [Step 1]
2. [Step 2]
...

### When Debugging
1. [Step 1]
...

### When Testing
1. [Step 1]
...

## Example Workflow
[Input/Output pair showing ideal execution]

## Key Rules
- [Non-negotiable requirement 1]
- [Non-negotiable requirement 2]

## Resources
- See [REFERENCE.md]({baseDir}/references/python-modules.md) for preferred packages
- See [PATTERNS.md]({baseDir}/references/patterns.md) for common structures
```

### Best Practice: Python Skills from December 2025

Here's the authoritative template based on the `python3-development` skill:[5][4]

```yaml
---
name: python3-development
description: "Modern Python 3.11+ development with type hints, TDD, and quality gates (ruff, mypy, pytest). Use when writing Python scripts, building CLI apps with Typer/Rich, designing packages, debugging Python errors, running tests with >80% coverage, or reviewing code for best practices and PEP 723 compliance."
allowed-tools: "Read,Write,Bash,Edit,Glob,Grep"
version: 2.0.0
license: MIT
---

# Python 3.11+ Development

## Purpose
Guide for writing modern Python code using test-driven development, native type hints, and automated quality checks. Applies to all Python development tasks—scripts, CLI applications, packages, debugging, and code review.

## Core Concepts

### Python Development Standards
- **Language Version**: Python 3.11+ (native generics, PEP 723 support)
- **Type System**: Mandatory type hints on all functions and classes
- **Testing**: pytest with >80% coverage minimum
- **Code Quality**:
  - **Linting**: ruff (replaces flake8 + isort + pylint)
  - **Formatting**: ruff format or Black (preferred: ruff for unified tooling)
  - **Type Checking**: mypy --strict mode
  - **Packaging**: pyproject.toml (not setup.py)

### Quality Gate Workflow
```
Write Code → Lint (ruff check) → Format (ruff format) → Type Check (mypy) → Test (pytest) → Commit
```

Every file must pass all gates before merging.

## Instructions

### When Writing New Python Code

**Step 1: Define Type Signature**
```
from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None
    
def fetch_user(user_id: int) -> Optional[User]:
    """Retrieve user by ID. Returns None if not found."""
    ...
```

Use explicit type hints always. Never rely on type inference. Dataclasses preferred over named tuples for clarity.

**Step 2: Write Tests First (TDD)**
```
# tests/test_user.py
import pytest
from module import fetch_user, User

def test_fetch_user_found():
    result = fetch_user(1)
    assert result is not None
    assert result.id == 1
    assert result.name == "Alice"

def test_fetch_user_not_found():
    result = fetch_user(9999)
    assert result is None
```

Write tests defining expected behavior BEFORE implementation.

**Step 3: Implement Minimal Code**
```
def fetch_user(user_id: int) -> Optional[User]:
    """Retrieve user by ID. Returns None if not found."""
    for user in USERS_DB:
        if user.id == user_id:
            return user
    return None
```

Implement only enough to pass tests. No over-engineering.

**Step 4: Run Quality Checks**
```
# Run all checks in sequence
ruff check . && ruff format . && mypy . --strict && pytest --cov=module
```

All must pass before marking as complete.

### When Debugging Python Errors

**Step 1: Identify Error Type**
- Is it a type error? → Run `mypy --show-error-codes`
- Is it a runtime error? → Run the test directly with `-vv` flag
- Is it a linting issue? → Run `ruff check --select [error-code]`

**Step 2: Reproduce Minimally**
Create a small test case that reproduces the issue in isolation.

**Step 3: Fix Root Cause**
Address the underlying problem, not the symptom. If a test fails because of logic, fix logic. If mypy complains about types, fix type hints.

**Step 4: Verify Fix**
Run the full quality pipeline to ensure fix doesn't break other tests or introduce new linting errors.

### When Running Tests

**Command Pattern:**
```
pytest --cov=module --cov-report=term-missing -v
```

**Coverage Requirements:**
- Minimum 80% coverage overall
- 100% coverage for critical functions (auth, validation, database)
- Missing lines report helps identify untested paths

**For Continuous Testing:**
```
# Watch mode during development
pytest-watch
```

## Key Rules (Non-Negotiable)

- **Type Hints**: Every function parameter and return type must have explicit type hints. No `Any` except with explicit justification.
- **Tests**: Every new function must have corresponding tests. >80% coverage minimum.
- **Naming**: Use snake_case for functions/variables, PascalCase for classes. Avoid single letters except i, j, k in loops.
- **Imports**: Explicit imports only. No `from module import *`. Organize: stdlib → third-party → local.
- **Error Handling**: Use specific exceptions, not bare `Exception`. Provide context in error messages.
- **Docstrings**: Google-style docstrings on all public functions describing args, return values, and exceptions.

## Common Patterns

### Async Patterns (Python 3.11+)
```
async def fetch_user_async(user_id: int) -> Optional[User]:
    """Async user fetching with type-safe coroutines."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/users/{user_id}")
    return response.json()

# Native union type syntax (Python 3.10+)
def process(data: str | int | None) -> str:
    return str(data)
```

### PEP 723: Inline Script Metadata
```
#!/usr/bin/env python
"""# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///
"""
import requests
from rich import print

print(requests.get("https://api.example.com").json())
```

For portable scripts that don't need virtual environments.

## Example: Complete TDD Workflow

**Input**: "Write a function that validates email addresses"

**Step 1: Write tests**
```
from module import is_valid_email

def test_valid_email():
    assert is_valid_email("user@example.com") == True

def test_invalid_email():
    assert is_valid_email("not-an-email") == False
    assert is_valid_email("@example.com") == False
```

**Step 2: Implement minimal code**
```
import re

def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(pattern, email))
```

**Step 3: Run checks**
```
ruff check && ruff format && mypy --strict && pytest --cov
```

**Step 4: Output**
```
✓ All tests pass (coverage: 100%)
✓ Code formatted (ruff format)
✓ No linting errors (ruff check)
✓ No type errors (mypy --strict)
✓ Ready for merge
```

## References

**For module registry and preferred packages:**
See [{baseDir}/references/modules.md]({baseDir}/references/modules.md)

**For pyproject.toml templates:**
See [{baseDir}/references/pyproject.md]({baseDir}/references/pyproject.md)

**For common error solutions:**
See [{baseDir}/references/errors.md]({baseDir}/references/errors.md)
```

### Critical Description Design for Discovery[4][1]

The `description` field is your most important real estate. Claude uses it to decide whether to invoke your skill via **pure LLM reasoning**, not keyword matching. Follow this pattern:[3]

```yaml
# ✅ GOOD: Action-oriented + Use cases + Specific triggers
description: "Modern Python 3.11+ development with type hints, TDD, and quality gates (ruff, mypy, pytest). Use when writing Python scripts, building CLI apps with Typer/Rich, designing packages, debugging Python errors, running tests with >80% coverage, or reviewing code for best practices and PEP 723 compliance."

# ❌ AVOID: Too vague
description: "Python development skill"
description: "Helps with Python code"

# ❌ AVOID: Assuming Claude understands context
description: "TDD and type hints"  # Doesn't say WHEN to use it
```

### Bundle Supporting Files (Progressive Disclosure)[1][4]

```
python3-development/
├── SKILL.md (core: ~400 lines)
├── references/
│   ├── modules.md        # 50+ recommended packages
│   ├── errors.md         # Common error solutions
│   └── pyproject.md      # Template configurations
└── scripts/
    ├── validate.py       # Quality gate checker
    └── init_project.py   # Project bootstrapper
```

When Claude reads SKILL.md, it gets the overview. If it needs detailed module info, it reads `{baseDir}/references/modules.md` on demand. This keeps tokens low while maintaining comprehensive guidance.[1]

### Testing Your Python SKILL.md[4]

Create evaluations BEFORE extensive documentation:[1]

```json
{
  "skills": ["python3-development"],
  "query": "Write a Python function that validates email addresses using TDD",
  "expected_behavior": [
    "Claude starts by writing tests with type hints",
    "Tests define expected behavior for valid and invalid emails",
    "Claude implements minimal code to pass tests",
    "Claude runs ruff check, mypy, pytest with coverage",
    "All quality gates pass before completion"
  ]
}
```

Test with fresh Claude instances to ensure discovery works via description alone.

### What Changed in December 2025[5][4]

The `python3-development` skill ecosystem standardized on:

1. **Native Type Hints**: All code uses PEP 604 union syntax (`str | None` instead of `Optional[str]`)
2. **ruff as Unified Tool**: Replaces flake8 + isort + pylint + black in one command
3. **mypy --strict**: Non-negotiable for production code
4. **PEP 723 Inline Metadata**: Replaces requirements.txt for portable scripts
5. **>80% Test Coverage Minimum**: Enforced quality gate
6. **Async as Default**: Python 3.11+ async patterns preferred

### The Bottom Line

Your December 2025 Python SKILL.md should be **concise** (under 500 lines), **action-oriented** (tell Claude what to do), **comprehensive** (reference files for depth), and **testable** (include example workflows). The description is critical—vague descriptions cause silent failures because Claude's skill selection happens through pure LLM reasoning, not keyword matching.[3][4][1]

Use the template above as your starting point, customize for your specific workflow, test discovery with fresh Claude instances, and iterate based on real usage patterns.[4][1]

## Human

How many skill documents would you make for our environment?

## Assistant

Based on my analysis of your comprehensive documentation, here's my recommendation:

## Recommended Skill Hierarchy for Your Environment

Given your established documentation (Python 2025 standards, CSF NIP validator, testing patterns, packaging guide), I would consolidate into **4-5 strategic SKILL.md documents**:

### Tier 1: Core Skills (Your Foundation)

**1. `python3-development.SKILL.md`** (~600 lines)
- **Purpose**: Primary skill for all Python development tasks
- **Scope**: Modern Python 3.11+, type hints, ruff, mypy --strict, uv
- **Triggers**: "Write Python code," "Python function," "Python project"
- **Combines**: Your Python 2025 Sys Prompt + code standards
- **Status**: Likely already have (4th 22KB SKILL.md file)

**2. `python-testing-tdd.SKILL.md`** (~700 lines) 
- **Status**: ✅ You already have this
- **Enhancement**: Add integration testing patterns, async test fixtures, CI/CD hooks

**3. `python-pydantic-v2.SKILL.md`** (~500 lines) - **NEW PRIORITY**
- **Purpose**: Dedicated to Pydantic V2 validation, serialization, JSON schema
- **Scope**: BaseModel, validators, ConfigDict, nested models, type coercion
- **Triggers**: "Validate data," "API schema," "Pydantic," "serialization"
- **Why**: Pydantic is foundational to your architecture; deserves dedicated guidance

**4. `fastapi-production-patterns.SKILL.md`** (~800 lines) - **NEW PRIORITY**
- **Purpose**: Production-grade FastAPI applications
- **Scope**: Dependency injection, error handling, middleware, security, async patterns
- **Triggers**: "FastAPI app," "REST API," "async endpoint," "API error handling"
- **Why**: Your vertical slice architecture is built around FastAPI

### Tier 2: Specialized Skills

**5. `python-async-structured.SKILL.md`** (~500 lines) - **NEW**
- **Purpose**: Async patterns using TaskGroup, structured concurrency
- **Scope**: asyncio.TaskGroup, exception groups, common pitfalls, timeout patterns
- **Triggers**: "Async code," "concurrent operations," "asyncio," "background tasks"
- **Why**: Critical to modern Python; your sys prompt mandates TaskGroup

**6. `python-debugging-rca.SKILL.md`** (~400 lines) - **NEW**
- **Purpose**: Root cause analysis, debugging strategies, profiling
- **Scope**: Stack traces, logging inspection, performance profiling, common error patterns
- **Triggers**: "Debug this," "why is this failing," "performance issue"
- **Why**: Enables faster problem-solving

**7. `database-sqlalchemy-v2.SKILL.md`** (~600 lines) - **NEW**
- **Purpose**: SQLAlchemy 2.0+, modern patterns, migrations
- **Scope**: ORM operations, query optimization, async support, schema design
- **Triggers**: "Database," "ORM," "SQLAlchemy," "migration"
- **Why**: Complements Pydantic and FastAPI integration

### Tier 3: Governance Skills

**8. `csf-nip-code-validator.SKILL.md`** 
- **Status**: ✅ You already have this (21,749 bytes)
- **Enhancement**: Add checklist for CI/CD gate automation

**9. `python-project-scaffolding.SKILL.md`** (~400 lines) - **NEW**
- **Purpose**: Generate production-ready project structures with uv
- **Scope**: FastAPI, Django, CLI, library scaffolding
- **Triggers**: "Create new project," "project structure," "scaffold"
- **Why**: Enforces team standards on every new project

***

## Recommended Implementation Priority

| Skill | Status | Priority | Effort | Impact |
|-------|--------|----------|--------|--------|
| python3-development | Likely have | ⭐ | Low | Critical |
| python-testing-tdd | ✅ Have | Medium | Low | Critical |
| python-pydantic-v2 | ❌ Missing | ⭐⭐⭐ | Medium | Very High |
| fastapi-production-patterns | ❌ Missing | ⭐⭐⭐ | High | Very High |
| python-async-structured | ❌ Missing | ⭐⭐ | Medium | High |
| csf-nip-code-validator | ✅ Have | ⭐ | Low | High |
| python-debugging-rca | ❌ Missing | ⭐⭐ | Medium | Medium |
| database-sqlalchemy-v2 | ❌ Missing | ⭐⭐ | Medium | High |
| python-project-scaffolding | ❌ Missing | ⭐ | Low | Medium |

***

## For TypeScript (You Have Sys Prompt, No Skills)

**Would also recommend:**
- `typescript-strict-safety.SKILL.md` - Zod, strict tsconfig, type narrowing
- `hono-production-patterns.SKILL.md` - If using Hono
- `biome-project-setup.SKILL.md` - Tooling automation

***

## My Assessment

**Total Recommended Skills: 9-11 (depending on TypeScript adoption)**

Your environment is sophisticated enough to justify this depth because:
1. ✅ You have comprehensive system prompts (clear ownership)
2. ✅ You enforce specific standards (CSF NIP)
3. ✅ You target professional use cases (vertical slices, type safety)
4. ✅ You have documentation supporting each skill

**Quick wins to implement NOW:**
1. `python-pydantic-v2.SKILL.md` - Foundational
2. `fastapi-production-patterns.SKILL.md` - Your core framework
3. Refactor existing Python 3.11+ content into primary `python3-development.SKILL.md`

This structure gives Claude Code the **semantic routing** needed to auto-invoke the right guidance at the right time.

## Human

please create export documents for me to download for easy drop and replace.

## Assistant

Perfect! Now let me create a summary showing you what's available:

Based on your request, I've created **5 professional export documents** ready for immediate download and deployment to your Claude Code environment. Here's what you're getting:

## 📥 Download Package Summary

### **Core SKILL.md Files (4 Files)**

1. **python3-development.md** [18 KB]
   - Primary skill for all Python 3.11+ development
   - Covers: uv, ruff, mypy --strict, pytest, type hints
   - Auto-triggers on: "Python code", "function", "module"

2. **python-pydantic-v2-mastery.md** [22 KB]
   - Specialized for data validation and APIs
   - Covers: BaseModel, validators, serialization, unions, generics
   - Auto-triggers on: "Pydantic", "validate", "serialization"

3. **fastapi-production-patterns.md** [25 KB]
   - Framework skill for REST APIs
   - Covers: Vertical slices, dependency injection, error handling, testing
   - Auto-triggers on: "FastAPI", "endpoint", "API design"

4. **python-async-structured-concurrency.md** [20 KB]
   - Advanced async patterns
   - Covers: TaskGroup, exception groups, timeouts, rate limiting
   - Auto-triggers on: "async", "concurrent", "TaskGroup"

### **Documentation Files (2 Files)**

5. **IMPLEMENTATION-GUIDE.md** [12 KB]
   - Step-by-step installation instructions
   - Skill coordination matrix
   - Troubleshooting & customization guide
   - Integration checklist

6. **DOWNLOAD-MANIFEST.txt** [Quick reference]
   - What's in the package
   - Quick start (3 steps)
   - Quality gates checklist
   - Version information

***

## ✅ Total Package: ~97 KB, Ready to Deploy

All files are **production-ready** and follow December 2025 standards:
- ✅ Type hints mandatory (Python 3.11+ syntax)
- ✅ Modern tooling (uv, ruff, mypy --strict)
- ✅ Structured concurrency (asyncio.TaskGroup)
- ✅ Pydantic V2 strict validation
- ✅ Vertical slice architecture
- ✅ >80% test coverage requirement

***

## 🎯 Quick Deployment (3 Steps)

```bash
# 1. Create skills directory
mkdir -p .claude/skills/

# 2. Copy all .md files here
cp *.md .claude/skills/

# 3. Test in Claude Code
# "Write a Python function that validates an email"
# → Expected: 2 skills auto-invoke
```

All files are now **available for download** in your session. Download them and drop into `.claude/skills/` for immediate integration with Claude Code in Comet browser.
