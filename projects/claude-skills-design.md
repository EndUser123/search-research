# Claude Code Skills System – Design & Implementation Guide

**Version:** 1.0  
**Date:** 2026-01-12  
**Target:** Advanced solo dev using Claude Code 2.1.5 (unified Skill tool)  
**Purpose:** Portable design + implementation spec you can hand to any LLM to implement your skills ecosystem with minimal friction.

---

## 1. Goals & Non‑Goals

### 1.1 Primary Goals

1. Build a **coherent, scalable skills system** on top of Claude Code 2.1.5’s unified Skill tool.
2. Make it **discoverable**: 45+ skills remain usable without constantly re‑reading SKILL.md files.
3. Make it **maintainable**: clear ownership, versioning, health checks, and deprecation.
4. Optimize for **LLM collaboration**: clear frontmatter, predictable patterns, minimal token waste.
5. Enable **hybrid workflows**: LLM reasoning + deterministic scripts + subagents.

### 1.2 Non‑Goals

- Not a generic “how to use Claude Code” tutorial.
- Not tied to any one model vendor beyond file layout expectations.
- Not a complete CI/CD story; this focuses on local skills architecture.

---

## 2. High‑Level Architecture

Your Claude skills system is structured as follows:

```text
~/.claude/
├── CLAUDE.md                  # Global behavior & preferences
└── skills/                    # Global skills (optional)

P:/                            # Project workspace root
├── CLAUDE.md                  # Workspace-level config
├── .claude/
│   ├── commands/              # Simple, single-file commands
│   │   ├── foo.md
│   │   └── ...
│   ├── skills/                # Complex, multi-file skills
│   │   ├── debug-memory/
│   │   │   ├── SKILL.md
│   │   │   └── resources/
│   │   │       ├── examples.md
│   │   │       ├── templates.md
│   │   │       └── scripts/... (.py / .ps1 helpers)
│   │   ├── refactor-security/
│   │   ├── _tools/            # Meta-tools for skills system
│   │   │   ├── generate_index.py
│   │   │   ├── health_check.py
│   │   │   └── check_duplicates.ps1
│   │   └── _archive/          # Deprecated skills
│   └── ...                    # Other Claude artifacts
└── P:/.claude/SKILL_INDEX.md  # Auto-generated registry
```

Key ideas:

- **Commands** (`.claude/commands/*.md`) and **skills** (`.claude/skills/*/SKILL.md`) are both invoked via the **unified Skill tool** in Claude Code 2.1.5.
- **Commands**: single `.md`, simple functionality, <100 lines.
- **Skills**: directory with `SKILL.md` + `resources/` for examples, templates, scripts.
- A set of meta‑tools in `_tools/` manage **indexing, health, and duplicate detection**.

---

## 3. Unified Skill Model (Claude Code 2.1.3+)

### 3.1 Mental Model

Claude Code 2.1.3+ unifies slash commands and skills:

| Before 2.1.3                   | After 2.1.3+                                  |
| ------------------------------ | --------------------------------------------- |
| `SlashCommand` tool            | **Single `Skill` tool**                       |
| Commands in `.claude/commands` | Commands **and** skills via same invocation   |
| Skills in `.claude/skills`    | `/name` works for both commands and skills    |
| Different invocation stacks    | One unified invocation & autocomplete system  |

Implications:

1. **No functional break** – existing commands and skills continue to work.
2. **One mental model** – design around **complexity & organization**, not tool type.
3. **Unified invocation** – `/skillname` works for both commands and skills; both show in the slash menu (unless hidden).

### 3.2 When to Use Commands vs Skills

Decision is **organizational**, not functional:

| Use `.claude/commands/`         | Use `.claude/skills/`                            |
| --------------------------------| -------------------------------------------------|
| Single `.md` file               | Directory with `SKILL.md` + `resources/`         |
| <100 lines                      | 100–500 lines main, plus resources               |
| No helper scripts needed        | Needs scripts, examples, templates               |
| Simple, self-contained action   | Multi-step workflows, orchestration, subagents   |

Reserved built‑ins like `/clear`, `/compact`, `/cost`, `/planning`, `/config`, `/memory`, `/mcp` **must not be overridden**.

---

## 4. Skill Taxonomy & Naming

With 45+ skills you need predictable naming.

### 4.1 Naming Convention

Use a **domain‑first, concern‑second** pattern:

```text
<domain>[-<subdomain>][-<variant>][@<version>]
```

Examples:

- `debug` – generic debugging
- `debug-memory` – memory‑specific debugging
- `debug-perf` – performance debugging
- `refactor` – generic refactoring
- `refactor-security` – security‑focused refactor
- `test-write` – generating tests
- `test-migrate` – migrating tests
- `doc-api` – documenting APIs
- `research-libs` – library research

### 4.2 Recommended Domains

| Domain        | Examples                              |
|---------------|----------------------------------------|
| `debug`       | `debug`, `debug-memory`, `debug-perf`  |
| `test`        | `test-write`, `test-coverage`          |
| `refactor`    | `refactor`, `refactor-security`        |
| `doc`         | `doc-api`, `doc-architecture`          |
| `research`    | `research-patterns`, `research-libs`   |
| `architecture`| `architecture`, `architecture-async`   |
| `admin`       | `admin-audit`, `admin-cleanup`        |

You can expand this, but keep **top-level domains small and stable**.

---

## 5. SKILL.md Schema & Frontmatter

### 5.1 Standard SKILL.md Structure

Each complex skill lives in a folder:

```text
P:/.claude/skills/debug-memory/
├── SKILL.md
└── resources/
    ├── examples.md
    ├── templates.md
    └── scripts/...
```

### 5.2 Frontmatter Template

Use a rich YAML frontmatter that captures identity, taxonomy, invocation, config, performance, and maintenance:

```markdown
---
# === Identity ===
name: debug-memory
version: 1.2.0
description: Diagnose memory leaks and memory usage issues

# === Taxonomy ===
category: debug
domain: debug
subdomain: memory

# === Invocation ===
aliases:
  - /debug-mem
  - /mem-debug
triggers:
  - "memory leak"
  - "memory usage"
  - "out of memory"

# === Claude Code 2.1.3+ Config ===
context: fork                # 'main' or 'fork' for subagent isolation
agent: general-purpose       # Agent type when forked
user-invocable: true         # false hides from slash menu
disable-model-invocation: false  # true prevents auto-calls
argument-hint: "<file_or_pattern>"  # Slash menu hint

# === Performance Metadata ===
estimated_tokens: 3000-6000
typical_response_time: 60-120s
context_required: "codebase structure, memory metrics"

token_budget_hint: "If <20K tokens remain, use /debug-memory-quick"
error_recovery: "If OOM or context truncated, fall back to /debug-memory-quick"
high_token_triggers:
  - "codebase >10K lines"
  - "full-module scan"
  - "project-wide analysis"

# === Ownership & Lifecycle ===
owner: "your-name"
owner_contact: "slack:@yourname or email@domain"
status: stable               # stable | experimental | deprecated
last_reviewed: 2026-01-12
next_review_date: 2026-04-12

# === Dependencies ===
depends_on_skills:
  - /debug                    # Uses generic patterns from /debug
requires_tools:
  - python
  - psutil                    # External dependency, documented here
---

# Debug Memory

## Purpose

Short explanation of what this skill is for.

## When to Use

- Symptom 1
- Symptom 2

## Workflow

Step-by-step instructions / phases.

## Success Criteria

- [ ] Condition 1
- [ ] Condition 2

## Failure Modes

| Failure   | Symptom           | Recovery                 |
| --------- | ----------------- | ------------------------ |
| Example   | What you see      | How to fix or escalate  |

## Integration

- **Related skill**: /debug – generic debugging
- **Related scripts**: resources/scripts/*.py

## Assumptions & Gotchas

- Assumes X
- Gotchas table...

## Real Examples

Concrete invocations + results.
```

Any LLM can read this and understand how to invoke, maintain, and extend the skill.

---

## 6. Performance & Token Budget Strategy

### 6.1 Per‑Skill Performance Metadata

Each skill should answer:

- How many tokens it typically uses.
- When to abort or fall back to a quick variant.
- What inputs make it "dangerous" from a token perspective.

Use the `Performance Metadata` block as specified above.

### 6.2 Token Budget Decision Tree (Inside SKILL.md)

Embed a short decision section:

```markdown
## Pre-Execution Checklist

Before running this skill:

- Estimate remaining token budget (`/cost` in Claude Code)
- Assess input size (files, modules, project scope)

### Token Budget Decisions

| Budget Remaining | This Skill         | Alternative                 |
|------------------|--------------------|-----------------------------|
| >50K             | ✅ Full workflow   | —                           |
| 20K–50K          | ⚠️ Full or quick  | Prefer `/debug-memory-quick`|
| <20K             | ❌ Do not run      | `/debug-memory-quick` only  |
```

### 6.3 Quick Variants

Complex skills should often have a cheap variant:

```text
debug-memory/
├── SKILL.md               # Full analysis
└── quick-variant.md       # Lightweight path
```

Frontmatter example:

```markdown
---
name: debug-memory
aliases:
  - /debug-memory
  - /debug-memory-quick
variants:
  - name: quick
    file: quick-variant.md
    token_estimate: 500-1500
    description: "Fast heuristics for memory issues without full scan"
---
```

Implementation detail for quick variant is tool/environment-specific, but the pattern is portable.

---

## 7. Skills Registry & Discoverability

### 7.1 Problem Statement

At ~45+ skills, discoverability becomes a bottleneck:

- Hard to remember existing skills.
- Easy to create near-duplicates.
- LLM may not choose the optimal skill without explicit reference.

### 7.2 Auto‑Generated SKILL_INDEX.md

Create `P:/.claude/SKILL_INDEX.md` as an auto‑generated registry.

**File Contract (what any LLM can rely on):**

- File path: `P:/.claude/SKILL_INDEX.md`.
- Markdown table(s) listing each skill with:
  - `name`
  - `aliases`
  - `description`
  - `estimated_tokens`
  - `status` (stable / experimental / deprecated)
- Grouped by `category`/`domain`.

### 7.3 Generator Script (Concept)

Implementation language can vary (Python, PowerShell). Behavior:

1. Scan `P:/.claude/skills/*/SKILL.md` (excluding `_tools`, `_archive`).
2. Parse frontmatter (YAML) for fields:
   - `name`, `description`, `aliases`, `category`, `version`, `estimated_tokens`, `status`.
3. Group skills by `category`.
4. Emit markdown that looks like:

```markdown
---
# P:/.claude/SKILL_INDEX.md
# AUTO-GENERATED — Do not edit manually
# Last updated: 2026-01-12T09:30:00-07:00
# Regenerate with: python P:/.claude/skills/_tools/generate_index.py
---

# Skills Registry

## Debugging (3 skills)

| Name | Aliases | Description | Tokens | Status |
|------|---------|-------------|--------|--------|
| `/debug` | `/d` | Quick diagnosis | 2K–5K | ✅ Stable |
| `/debug-memory` | `/debug-mem` | Memory leaks | 3K–6K | ✅ Stable |

## Refactoring (2 skills)

| Name | Aliases | Description | Tokens | Status |
|------|---------|-------------|--------|--------|
| `/refactor` | `/rf` | General refactors | 4K–8K | ✅ Stable |
| `/refactor-security` | `/sec-refactor` | Security refactors | 3K–6K | 🟡 Experimental |

## By Stability Status

### ✅ Stable
- `/debug`
- `/debug-memory`
- `/refactor`

### 🟡 Experimental
- `/refactor-security`
```

An LLM in another environment can regenerate this by following the same rules.

---

## 8. Health, Duplicates & Maintenance

### 8.1 Skill Health Checks

A `health_check` tool should:

- Iterate over each `P:/.claude/skills/*/SKILL.md`.
- Compute:
  - Lines count (warn if >500 in main file).
  - Presence of frontmatter markers (`---`).
  - Presence of `description`, `version`, `category`, `owner`.
  - Warning if `TODO`/`FIXME` present.
  - Warning if suspicious hardcoded paths (`P:/`, `C:\` etc.) appear.
- Emit a JSON report (e.g., `_health_report.json`) and a console summary.

Any LLM can reimplement this using:

1. Directory walk.
2. Basic text parsing.
3. JSON serialization.

### 8.2 Duplicate & Overlap Detection

A `check_duplicates` tool should:

- Read all `aliases` across skills.
- Flag any alias used by more than one skill.
- Optionally compare descriptions for high textual similarity.

This can be done in PowerShell, Python, or any language the LLM prefers.

### 8.3 Maintenance Cadence

Recommended schedule:

- **Weekly**
  - Run `health_check` and fix obvious issues.
  - Regenerate `SKILL_INDEX.md`.

- **Monthly**
  - Break any SKILL.md >500 lines into `resources/`.
  - Add missing ownership, version, or taxonomy fields.

- **Quarterly**
  - Deprecate unused skills and move them to `_archive/`.
  - Consolidate overlapping skills.
  - Review alignment with latest Claude Code release notes.

---

## 9. Skill Invocation & Prompting Strategy

### 9.1 Invocation Modes

| Mode          | Example                                       | When to Use                     |
|---------------|-----------------------------------------------|---------------------------------|
| Direct        | `/debug connection timeout`                   | Explicit, predictable behavior  |
| Natural       | "help me debug this timeout"                 | Conversational, auto‑selection  |
| Chained       | "Run /rca, then feed results to /refactor"   | Multi‑step workflows            |

Any LLM interacting with this system should:

- Prefer **direct** invocation when you explicitly name a skill.
- Use **natural language** when exploring or unsure which skill to call.
- Document chains in SKILL.md when multi‑skill workflows are expected.

### 9.2 Context‑Rich Invocation Patterns

Encourage patterns like:

```text
/debug "connection timeout in database.py:42" --component=db
/refactor the function in src/utils/parser.py starting at line 100

Before running /architecture, consider: we're limited to Python stdlib only

/deep-research authentication patterns (we have ~50K tokens remaining)
```

An LLM should:

- Parse inline hints like `--component=db` or `we have ~50K tokens` and adapt depth accordingly.

### 9.3 Skill Chaining Templates

Include in your guide:

```markdown
## Skill Chain: Debug → RCA → Refactor → Test

1. `/debug` to identify surface‑level issue.
2. `/rca` for deep root cause analysis.
3. `/refactor` to implement chosen fix.
4. `/tdd` or `/test-<something>` to add/verify tests.
```

LLMs should implement these chains as separate calls and show intermediate results.

---

## 10. Hybrid LLM + Deterministic Scripts

### 10.1 When to Use Scripts vs LLM

Quick rule of thumb:

- **Use scripts for**:
  - Deterministic operations (same input → same output).
  - Math, counting, hashing.
  - File system operations.
  - API calls with secrets.
  - Pattern matching and regex.
- **Use LLM for**:
  - Reasoning and planning.
  - Non‑deterministic or open‑ended tasks.
  - Natural language generation.
  - Trade‑off decisions.

### 10.2 Script Layout

Place common helpers in:

```text
P:/.claude/skills/_tools/
  file_analyzer.{py,ps1}
  dep_checker.{py,ps1}
  git_health.{py,ps1}
```

Skill‑specific scripts in:

```text
P:/.claude/skills/<skill-name>/resources/scripts/
```

### 10.3 Usage Pattern in SKILL.md

```markdown
## Step 1: Deterministic Data Collection

Run this script first:

```bash
python P:/.claude/skills/_tools/dep_checker.py
```

Then feed the output back to the LLM:

```markdown
Based on this JSON output:
[PASTE OUTPUT]

1. Identify security‑critical packages.
2. Suggest an update plan.
```
```

Any LLM can follow this pattern: **scripts gather facts, LLM reason about them**.

---

## 11. Subagents & Forked Contexts

### 11.1 When to Use Subagents

Use subagents (forked contexts) for:

- Web or CHS research.
- Large file/codebase exploration.
- Token‑heavy analysis.
- Parallel tasks.
- Experimental or risky operations.

Avoid subagents for:

- Tiny, quick tasks.
- Highly stateful conversations.

### 11.2 Forked Context in Frontmatter

```yaml
context: fork
agent: general-purpose
```

Semantics for any LLM:

- Treat `context: fork` as **an isolated reasoning sandbox**.
- Only return summarized results back to main context, not full intermediate noise.

### 11.3 Subagent Invocation Template (Conceptual)

Inside SKILL.md, specify how to dispatch subagents (implementation syntax is environment‑specific):

```markdown
## Subagent Invocation Template

**Task**: [Clear, specific]

**Context**:
- Relevant files
- Current state summary
- Constraints

**Success Criteria**:
- [ ] Outcome 1
- [ ] Outcome 2

**Return Format**:
- Key findings
- Recommendations
- Blockers
```

LLMs in other environments can map this to their own subagent APIs.

---

## 12. CLAUDE.md & Routing Rules

### 12.1 Layered CLAUDE.md

```text
~/.claude/CLAUDE.md         # Global
P:/CLAUDE.md                # Workspace
P:/project/CLAUDE.md        # Project
P:/project/src/CLAUDE.md    # Optional component-specific
```

The closer to the code, the more specific the rules.

### 12.2 Route to Skills & Subagents

You can describe routing logic generically so any LLM can implement it:

```markdown
## Subagent Routing Rules

Dispatch to subagent when:
- Task reads >5 files.
- Task requires web search.
- Task can run independently in background.

Keep in main agent when:
- Task needs ongoing user interaction.
- Task is small (<30 seconds).
- Task depends heavily on prior conversation.
```

Any LLM can interpret this when deciding whether to use a secondary worker.

---

## 13. Skill Lifecycle, Ownership & Deprecation

### 13.1 Versioning Semantics

- `0.x.y` – Experimental; breaking changes allowed.
- `1.x.y` – Stable; follow semantic versioning.
- Use suffixes like `-beta`, `-exp` only for very short‑lived experiments.

### 13.2 Deprecation Workflow

1. Mark in frontmatter:

   ```yaml
   deprecated: true
   deprecated_by: /new-skill-name
   deprecated_date: 2026-01-15
   ```

2. Add a visible warning in the skill body:

   > ⚠️ This skill is deprecated. Use `/new-skill-name` instead.

3. Maintain both old and new for ~30 days.
4. Move deprecated skill folder into `P:/.claude/skills/_archive/`.

Any LLM can follow this lifecycle when refactoring or replacing skills.

### 13.3 Ownership Metadata

Frontmatter fields:

```yaml
owner: "your-name"
owner_contact: "slack:@yourname"
maintained_by: "primary owner"   # or a team name
last_reviewed: 2026-01-12
next_review_date: 2026-04-12
```

LLMs can use this to:

- Decide whether to modify a skill.
- Add TODOs mentioning the owner.
- Generate change logs referencing maintainers.

---

## 14. What NOT to Put in Skills

### 14.1 Anti‑Patterns

| Item                        | Why                              | Better Location              |
|-----------------------------|----------------------------------|------------------------------|
| Team onboarding docs        | Static, not task-driven          | README, wiki                 |
| Corporate policy text       | Non‑operational noise            | Policy repository            |
| Huge templates & examples   | Token bloat                      | `resources/templates.md`     |
| Math/crypto logic           | Must be exact                    | Script files (e.g. `math.py`)|
| API reference documentation | Better in dedicated docs         | External site, doc repo      |
| Deprecated patterns         | Confuses new usage               | `_archive/`                  |
| Multiple unrelated workflows| Hard to reason about             | Separate skills              |

### 14.2 Monthly Content Audit

Check that:

- SKILL.md ≤ 500 lines.
- Extended examples live in `resources/`.
- Deterministic logic is in `.py`/`.ps1` files.
- No secrets or credentials are in any file.

---

## 15. Quick Implementation Plan for Another LLM

This section is written as explicit instructions you can paste into another LLM.

### 15.1 Initial Setup

1. Create directory structure:
   - `P:/.claude/skills/`
   - `P:/.claude/skills/_tools/`
   - `P:/.claude/skills/_archive/`
2. For each existing complex command you want to convert:
   - Create `P:/.claude/skills/<name>/SKILL.md`.
   - Migrate content and add full frontmatter as defined in §5.2.
3. For simple commands (<100 lines):
   - Keep as `.claude/commands/<name>.md`.

### 15.2 Implement Meta‑Tools

1. Implement a script (language of your choice) that:
   - Scans `P:/.claude/skills/*/SKILL.md`.
   - Parses frontmatter to extract metadata.
   - Writes `P:/.claude/SKILL_INDEX.md` in the format defined in §7.3.
2. Implement a health check tool that:
   - Validates presence of key fields.
   - Warns for long SKILL.md or TODOs.
   - Exports `_health_report.json`.
3. Implement a duplicate checker that:
   - Flags alias conflicts.

### 15.3 Normalize Existing Skills

For each skill:

- Add/normalize frontmatter to match the template in §5.2.
- Assign `category`, `domain`, `subdomain` from the taxonomy in §4.2.
- Add `owner`, `status`, `version` if missing.
- Move large examples/templates into `resources/`.

### 15.4 Document Chains & Relationships

For your core workflows (e.g., debug → rca → refactor → test):

- Add a "Skill Chain" section as shown in §9.3.
- Ensure `depends_on_skills` in frontmatter is accurate.

### 15.5 Validate & Iterate

- Run the health and duplicate tools.
- Regenerate `SKILL_INDEX.md`.
- Do a quick manual pass on 5–10 key skills and refine.

At that point, **any** capable LLM with file system access and basic scripting can fully implement, extend, or refactor your skills ecosystem using this document as the authoritative design.
