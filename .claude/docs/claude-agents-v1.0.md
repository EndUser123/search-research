# Claude Code Agents Guide

**v1.0 | April 2026 | 2.1.63+ | Reference**

---

## CHANGELOG

| Aspect | Notes |
|--------|-------|
| v1.0 (Apr 2026) | Initial release — mirrors structure of claude-hooks-v3.1.md for parity |
| `Task` → `Agent` rename | v2.1.63: `Task` tool renamed to `Agent`; `Task(...)` retained as alias |
| Agent teams | v2.1.32+: multi-session coordination via shared task list and mailbox |
| Plugin agents | v2.1+: `plugin:agent` naming convention for reusable subagent definitions |
| Plan mode | First-class control loop, not optional feature |
| Rollback patterns | Git worktree isolation, atomic multi-file changes |
| Context management | Incremental strategies, token budgeting |
| Tool restriction tree | Decision process for allowlist vs sandboxing |
| Claude Managed Agents | April 2026 public beta trade-offs |
| Fan-out pattern | Tune on few files, deploy to all — avoids per-file iteration |
| Session contamination | `/clear after 2 failures`, `/compact` as reset |
| New best practices | Rules 13–16: fan-out, contamination, disable-model-invocation, deny→ask→allow |
| New anti-patterns | Spec/implementation separation, missing rollback planning |
| New patterns | Pattern 6: Fan-Out, Pattern 7: Spec/Impl Session Separation |

---

## TABLE OF CONTENTS

1. [Core Agent Concepts](#core-agent-concepts)
2. [Subagent vs Agent Teams](#subagent-vs-agent-teams)
3. [Invocation Patterns](#invocation-patterns)
4. [Agent Taxonomy & Naming](#agent-taxonomy--naming)
5. [Tool Restrictions & Permission Modes](#tool-restrictions--permission-modes)
6. [Tool Restriction Decision Tree](#tool-restriction-decision-tree)
7. [Plugin Structure](#plugin-structure)
8. [Agent Teams Architecture](#agent-teams-architecture)
9. [Plan Mode — The Foundational Control Loop](#plan-mode--the-foundational-control-loop)
10. [Rollback & Checkpointing](#rollback--checkpointing)
11. [Context Window & Token Management](#context-window--token-management)
12. [Built-in Agents](#built-in-agents)
13. [Best Practices](#best-practices)
14. [Anti-Patterns](#anti-patterns)
15. [Pattern Catalog](#pattern-catalog)
16. [Metrics & Observability](#metrics--observability)
17. [Claude Managed Agents (April 2026)](#claude-managed-agents-april-2026)
18. [Registry](#registry)
19. [Comparison: Hooks vs Agents vs Skills vs Commands](#comparison-hooks-vs-agents-vs-skills-vs-commands)

---

## CORE AGENT CONCEPTS

Agents are **context-isolated, specialized assistants** that Claude Code can delegate to. They have their own context window, system prompt, tool restrictions, optional model overrides, and can be spawned foreground (blocking, interactive) or background (non-blocking).

### Key properties

| Property | Description |
|----------|-------------|
| **Context isolation** | Subagent context does not pollute parent; noisy investigation output stays in subagent |
| **Specialization** | Each agent has a focused role (`code-reviewer`, `debugger`, `explorer`) |
| **Tool restrictions** | `tools` allowlist or `disallowedTools` to enforce least-privilege |
| **Model selection** | Pick cheapest model that handles the task (Haiku for read-only, Sonnet/Opus for reasoning) |
| **Tool name** | `Agent(...)` as of v2.1.63; `Task(...)` is a backward-compatible alias |

---

## SUBAGENT VS AGENT TEAMS

Use **subagents** when work is self-contained and only the result is needed. Use **agent teams** when teammates need to discuss findings, challenge each other, or coordinate across multiple related workstreams.

| Dimension | Subagent | Agent Team |
|-----------|----------|------------|
| **Context** | Shared with parent (isolated for noise only) | Each teammate has full independent context |
| **Communication** | Report to parent only | Teammates can message each other directly |
| **Token cost** | Lower (one context window) | Higher (multiple context windows) |
| **Orchestration** | Parent thread | Lead + teammates + shared task list |
| **Best for** | High-volume investigation, verification, parallel read-only research | Multi-stream implementation, hypothesis competition, cross-layer coordination |
| **Can spawn subagents** | No (flat delegation only) | Teammates cannot spawn nested teams |

**Rule of thumb**: If tasks need dense shared context or iterative back-and-forth, keep it in the main conversation. Subagents are for noisy work you don't want polluting the parent context.

---

## INVOCATION PATTERNS

### 1. `Agent` tool (v2.1.63+)

```python
Agent(
    description="code-reviewer",       # Role description — used for routing
    prompt="Review this function for edge cases: foo/bar.py",
    subagent_type="adversarial-review", # Optional: explicit agent name
    model="sonnet",                      # Optional: override model
    tools=["Read", "Grep", "Glob"],     # Optional: tool allowlist
    disallowedTools=["Edit", "Write"], # Optional: deny specific tools
    background=False,                   # Optional: foreground vs background
)
```

`Task(...)` is fully supported as an alias.

### 2. Natural language (implicit delegation)

```
"Use a subagent to explore the auth module and report findings"
```

Claude selects the best-matching agent from available definitions based on the `description` field.

### 3. @-mention (guaranteed routing)

```
"@code-reviewer review this PR for race conditions"
```

Ensures a specific agent handles this task regardless of what Claude might otherwise choose.

### 4. Team spawn (natural language)

```
"Create an agent team: api-owner for backend, test-owner for integration tests, reviewer to challenge assumptions"
```

Lead session orchestrates; teammates self-claim from shared task list.

---

## AGENT TAXONOMY & NAMING

### Naming convention

| Scope | Syntax | Example |
|-------|--------|---------|
| **User agents** (`.claude/agents/*.md`) | Bare name, no namespace | `adversarial-performance`, `hook-analyzer` |
| **Plugin agents** (plugin's `agents/` dir) | `plugin-name:agent-name` | `feature-dev:code-reviewer`, `plugin-dev:agent-creator` |
| **Built-in agents** | Bare name | `Explore`, `Plan`, `general-purpose` |

### `subagent_type` design rules

- **Keep it role-based, not task-specific.** `security-reviewer` is durable; `fix-auth-bug-now` is not.
- The `description` field is the most important design field — Claude uses it for routing decisions.
- Include "use proactively" if you want Claude to reach for this agent more often.
- Single-purpose agents are more reusable and predictable than multi-purpose ones.

### Effective descriptions

```
# Good — clear role, action-oriented
"You are a code reviewer specializing in concurrency bugs. Use proactively for any code involving locks, queues, or async operations."

# Bad — vague and task-specific
"You are a helper that looks at code when asked"
```

---

## TOOL RESTRICTIONS & PERMISSION MODES

### Default stance: restrict by default, widen intentionally

| Agent role | Recommended tools |
|------------|-------------------|
| **Reviewer / researcher / explorer** | `Read`, `Grep`, `Glob`, `Bash` (read-only) |
| **Debugger / fixer** | Add `Edit` only if patching is needed |
| **Security auditor** | `Read`, `Grep` only — no mutations |
| **Test runner** | `Bash` (pytest, jest), `Read` |

### Permission inheritance

- **Foreground agents**: inherit pre-approved permissions; can surface permission prompts interactively
- **Background agents**: inherit pre-approved permissions only; clarifying-question calls fail instead of pausing
- **Team teammates**: inherit lead's permission mode at spawn time

### Anti-pattern: unbounded tool access

Give agents only the tools they need for their role. A `code-explorer` reading 500 files does not need `Write`.

---

## PLUGIN STRUCTURE

A plugin is a shareable extension bundle that can define agents, skills, hooks, and MCP servers.

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required: name, description, version, capabilities
├── skills/                 # Agent Skills (invoked by slash command or autonomously)
│   └── my-skill/
│       └── SKILL.md
├── agents/                # Subagent definitions
│   └── specialist.md
├── hooks/                 # Hook handlers
│   └── hooks.json
└── .mcp.json             # MCP server definitions
```

### `plugin.json` manifest

```json
{
  "name": "my-plugin",
  "description": "Does X",
  "version": "1.0.0",
  "agents": ["specialist"],
  "skills": ["my-skill"],
  "hooks": ["hooks.json"],
  "mcpServers": [".mcp.json"]
}
```

### Loading plugins (Agent SDK)

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [
      { type: "local", path: "./my-plugin" },
      { type: "local", path: "/absolute/path/to/another-plugin" }
    ]
  }
})) { /* ... */ }
```

---

## AGENT TEAMS ARCHITECTURE

Agent teams use four components:

| Component | Role |
|-----------|------|
| **Team lead** | Main Claude Code session; creates team, spawns teammates, coordinates, synthesizes |
| **Teammates** | Independent Claude Code instances; each has own context + tools + skills |
| **Task list** | Shared work items with dependencies; teammates self-claim via file locking |
| **Mailbox** | Direct agent-to-agent messaging layer |

### Enable agent teams

Requires Claude Code **v2.1.32+** and:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
# or in settings.json:
{ "features": { "agentTeams": true } }
```

### Spawn workflow

1. State the overall task and why parallelism helps
2. Name teammate roles (`api-owner`, `test-owner`, `reviewer`)
3. Optionally specify team size and model
4. Add guardrails: "require plan approval before changes"
5. Define task boundaries — **no overlapping file ownership**

### Coordination patterns

| Pattern | When to use |
|---------|-------------|
| **Perspective split** | Multiple teammates inspect the same artifact through different lenses (security, performance, test coverage) |
| **Hypothesis competition** | Each teammate investigates a different root-cause theory; actively try to disprove others |
| **Cross-layer split** | Separate teammates own frontend, backend, testing for the same feature |
| **Plan-first implementation** | Teammates stay read-only until lead approves approach (good for risky refactors) |

### Anti-pattern: overlapping file ownership

Two teammates editing the same file can overwrite each other. Decompose by file set, module boundary, or review dimension — not by vague functional area.

### Practical sizing

- Start with **3–5 teammates**
- Aim for **~5–6 tasks per teammate** as initial load
- Lead should stay in orchestration mode and periodically synthesize

### Team persistence

Team configuration stored at `~/.claude/teams/{team-name}/config.json`.

---

## PLAN MODE — THE FOUNDATIONAL CONTROL LOOP

Plan mode (review-before-execute) should be the **default mental model**, not an optional feature. It prevents discovering 500 lines of unwanted code after the fact.

### When to use

| Context | Use plan mode? |
|---------|----------------|
| Multi-file changes | YES — always |
| Risky refactors | YES — always |
| Schema migrations | YES — always |
| Single-line fixes | NO — overhead not justified |
| Read-only investigation | NO — plan mode is irrelevant |

### Pattern: plan-first agent team

```
Lead: "Stay read-only until I approve your plan.
      Only then make changes.
      I will only approve plans that include tests and rollback considerations."
```

### Pattern: plan mode per subagent

```
Agent(
    description="api-architect",
    prompt="Analyze the auth module. Produce a plan for adding rate limiting.
            Include: affected files, rollback considerations, test approach.
            Do NOT make changes until I approve the plan.",
    subagent_type="architect",
    tools=["Read", "Grep", "Glob"],  # read-only until plan approved
)
```

### Plan approval criteria (what to require)

A good plan must include:
1. What files change and what the diff is
2. How to verify correctness (tests, linters, assertions)
3. Rollback procedure (how to undo if it breaks)
4. What could go wrong and how to detect it

---

## ROLLBACK & CHECKPOINTING

Agent edits can break the working tree. Without explicit checkpointing, failures are silent and irreversible.

### Checkpoint pattern: git worktree per agent

```bash
# Before spawning agent with mutation rights
git worktree add .claude/worktrees/{agent-name}-{timestamp} feature-branch

# Agent edits in isolated worktree
# On success: merge back
# On failure: discard worktree
git worktree remove .claude/worktrees/{agent-name}-{timestamp}
```

### Atomic multi-file change pattern

When an agent must change multiple files:

```
Lead: "Make these changes atomically: update schema, update tests, update docs.
      If any step fails, roll back all three.
      Report only whether the full change succeeded."
```

### Rollback detection hooks

Use `PostToolUse` hooks to detect when agent edits have introduced regressions:
- Run linter after Edit/Write operations
- Run test suite on affected files
- Auto-revert if hook detects failure pattern

---

## CONTEXT WINDOW & TOKEN MANAGEMENT

Dumping entire files into every request is wasteful and slow. Structure context incrementally.

### Strategies

| Strategy | When to use | Token savings |
|---------|-------------|---------------|
| **Incremental diff** | Agent needs to understand changes, not full file | 80–95% |
| **Summary + excerpt** | Long file; agent needs specific section | 60–90% |
| **External retrieval** | Agent can Read files directly | 100% (no context usage) |
| **External memory** | Multi-turn session; agent retrieves prior state | 40–70% |

### Anti-pattern: full-file context injection

```
# Bad — burns tokens, dilutes signal
Agent(
    prompt="Review this entire auth module:\n" + open("auth.py").read()
)

# Good — let agent read what it needs
Agent(
    prompt="Review auth/ for race conditions in token refresh.
            Read files as needed. Report specific findings.",
    tools=["Read", "Grep", "Glob"],
)
```

### Token budgeting for multi-agent sessions

Each teammate has its own context window. Budget for:
- 3 teammates × ~50K tokens context = 150K tokens/session
- Lead synthesis overhead: ~20K tokens
- Total: ~170K tokens per coordinated session

---

## TOOL RESTRICTION DECISION TREE

Decide which tools to grant each agent using this process:

```
1. What is the minimum set of tools needed for this role?
   (start empty, add only what's necessary)

2. Does this role ever need to mutate state?
   ├── NO → Read-only (Read, Grep, Glob, Bash for read-only commands)
   └── YES → Add Edit/Write only for specific file patterns

3. Is Bash needed?
   ├── YES → Restrict to specific commands (pytest, git, etc.)
   └── NO → Remove Bash entirely

4. Should this role run as foreground or background?
   ├── Background → All permissions must be pre-approved
   └── Foreground → Can surface permission prompts interactively
```

### Permission modes

| Mode | Behavior | Use when |
|------|----------|----------|
| **auto** | Claude approves automatically | Trusted roles, read-only |
| **allowlist** | Only listed tools permitted | Untrusted or semi-trusted roles |
| **sandboxing** | All tools blocked except explicitly allowed | High-risk or experimental agents |

---

## BUILT-IN AGENTS

| Agent | Model | When to use |
|-------|-------|-------------|
| `Explore` | Haiku | Read-only codebase exploration, fast search |
| `Plan` | Sonnet | Planning and architecture work |
| `general-purpose` | Sonnet | Default fallback for unclassified tasks |

Built-in agents are invoked by natural language or `@Explore` / `@Plan` and require no `subagent_type` specification.

---

## BEST PRACTICES

1. **Plan by default**: Use plan mode (review-before-execute) before any non-trivial implementation. This is the foundational control loop — not an optional feature.
2. **Default stance**: main conversation for implementation; subagents for noisy investigation and verification
3. **Keep `subagent_type` stable and role-based** — not task-specific
4. **Write a sharp `description`** including "use proactively" if you want Claude to reach for it
5. **Minimize tools** — read-only by default; add mutations only when needed
6. **Choose model intentionally** — cheap models for exploration, stronger ones for reasoning-heavy review
7. **Use background only when task inputs are fully specified** and permission needs are known up front
8. **Do orchestration in the parent thread** — subagents cannot spawn subagents; nested agent trees are not supported
9. **Pair delegation with verification** — tests, linters, screenshots, or clearly stated success criteria
10. **Use skills for reusable same-context workflows**; use subagents for isolated context
11. **Preload skills inside subagents** — they do not inherit parent skills automatically
12. **Treat CLAUDE.md as a contract** — define agent scope, testing expectations, and architectural constraints upfront (Anthropic research: 72.6% of Claude.md files specify architecture concerns)
13. **Fan-out by default for multi-file changes** — tune on 2–3 representative files, verify quality, then deploy to all. Avoid per-file prompting; batch similar changes.
14. **Watch for session contamination** — if a subagent produces degraded output or the lead's context is polluted, invoke `/clear` early. The `/clear after 2 failures` rule prevents compounding errors. Treat `/compact` summarization as a contamination reset.
15. **Use `disable-model-invocation` for dangerous skills** — skills that auto-fire inappropriately can be disabled per-session with this flag, preventing unwanted skill interference in agent workflows.
16. **Permission evaluation follows deny → ask → allow** — always start from least privilege; tools are denied by default, promoted to ask or allow based on explicit need

---

## ANTI-PATTERNS

| Anti-pattern | Why it's bad | Better approach |
|-------------|--------------|-----------------|
| Subagent for tight iterative collaboration | Needs shared context; subagents can't pass intermediate state | Keep in main conversation |
| Subagent for tiny edits | Startup overhead > context savings | Do it directly in main thread |
| Unrestricted tool access on agents | Expands bad action space | Restrict by default |
| Task-specific `subagent_type` names | Not reusable; creates explosion of agent types | Role-based naming |
| Overlapping file ownership in teams | Teammates overwrite each other's changes | Decompose by file set or module boundary |
| Background agent for ambiguous tasks | Clarifying questions fail silently | Use foreground |
| Main thread implementing while teammates are still running | Lead should orchestrate, not compete | Wait for teammates or synthesize |
| No spec/implementation session separation | Spec bleed into implementation context causes goal drift and false anchoring | Keep spec drafting and implementation in separate sessions; use a fresh context for each |
| Missing rollback planning before agent tasks | Without a documented rollback path, failed agent tasks leave broken state | Require rollback consideration (git worktree, staged changes, or branch backup) before launching agent teams |

---

## PATTERN CATALOG

### Pattern 1: Parallel Investigation

```
Lead: "auth-module investigator, api-module investigator, db-schema investigator —
      each explore your module independently, report back in 5 sentences"
```

Use when three or more modules need independent research.

### Pattern 2: Hypothesis Competition

```
Lead: "Spawn 3 teammates. Each investigates a different root-cause theory
      for the bug: (A) race condition, (B) bad default, (C) schema drift.
      Actively try to disprove your assigned theory.
      Report what would prove or disprove it."
```

Use for bugs with ambiguous root cause.

### Pattern 3: Plan-First Implementation

```
Lead: "Stay read-only until I approve your plan.
      Only then make changes.
      I will only approve plans that include tests and rollback considerations."
```

Use for risky refactors or schema-touching changes.

### Pattern 4: Fresh-Context Review

```
Lead: "@code-reviewer review foo/bar.py for edge cases.
      Use a different approach than the last review —
      focus specifically on concurrency and error handling."
```

Subagents provide fresh context without parent conversation baggage.

### Pattern 5: Read-Heavy Exploration

```
Lead: "Use Explore to map the entire auth flow.
      Report only: which files are involved, which are hot paths,
      and where the session token is created."
```

Explorers use Haiku for fast read-only search.

### Pattern 6: Fan-Out for Multi-File Changes

```
Lead: "Tune on auth_form.py and settings.py first — confirm the change pattern
      looks right, then apply the same pattern to all remaining files."
```

Use when the same logical change spans many files. Tune approach on a subset, then scale. Avoid iterating per-file.

### Pattern 7: Spec/Implementation Session Separation

```
Session A (spec): Define what success looks like, constraints, file ownership.
Session B (implementation): Fresh context — only the spec and implementation task.
```

Use when spec drift or goal creep contaminates implementation. Keep spec and implementation in separate sessions to avoid anchoring on intermediate artifacts.

---

## REGISTRY

Discover valid `subagent_type` strings via runtime discovery (see REGISTRY section below).

User agents (bare name, no namespace):
```bash
ls P:/.claude/agents/*.md
```

Plugin agents (`plugin:agent`):
```bash
find "C:/Users/brsth/.claude/plugins/cache" -name "*.md" -path "*/agents/*" \
  | sed 's|.*/cache/[^/]*/\([^/]*\)/[^/]*/agents/\([^.]*\)\.md|\1:\2|' \
  | sort -u
```

---

## COMPARISON: HOOKS VS AGENTS VS SKILLS VS COMMANDS

| Component | Type | Execution | Visibility | Use Case |
|-----------|------|-----------|------------|----------|
| **Hooks** | Deterministic | Automatic at lifecycle phases | Some outputs visible | Enforce rules, validate state, audit |
| **Agents** | LLM-augmented | Spawned for isolated tasks | Summary returned only | Context isolation, specialization, parallel investigation |
| **Skills** | LLM-augmented | User-invoked or auto | Full context passed | Reusable expertise in same context |
| **Commands** | Shortcut | User-invoked | Optional context | Quick actions, automation |
| **CLAUDE.md** | Rules + Context | LLM-read | Visible to Claude | Best practices, guidelines, architecture |

### Decision tree

```
Need context isolation + parallel investigation?
├── YES → Subagent (single session) OR Agent Team (multi-session)
└── NO ↓
    Need reusable workflow in same context?
    ├── YES → Skill
    └── NO ↓
        Deterministic enforcement at lifecycle?
        ├── YES → Hook
        └── NO → Command or CLAUDE.md rule
```

### Hooks ↔ Agents interaction

Hooks can respond to agent events via `TeammateIdle`, `TaskCreated`, `TaskCompleted` events. This enables:
- Quality gates that fire after agent tasks complete
- Cross-agent logging and audit trails
- Permission enforcement for agent-spawned tools

The `hook-analyzer` agent can review hook behavior and recommend integration points. See `hook-analyzer.md` in `P:/.claude/agents/`.

---

## QUICK REFERENCE

### Invocation cheat sheet

```python
# Explicit subagent with tool restrictions
Agent(
    description="security-reviewer",
    prompt="Find injection vulnerabilities in this module",
    tools=["Read", "Grep", "Glob"],  # read-only
    subagent_type="adversarial-security"
)

# Background with model override
Agent(
    description="test-runner",
    prompt="Run pytest on auth/ — report failures only",
    model="sonnet",
    background=True
)

# @-mention (guaranteed routing)
"@code-reviewer review PR #47 for race conditions"
```

### Minimal 3-agent starting set

| Agent | Tools | Model | When |
|-------|-------|-------|------|
| `code-explorer` | `Read, Grep, Glob, Bash` | Haiku | Read-only codebase search |
| `code-reviewer` | `Read, Grep, Glob` | Sonnet | Fresh-context edge-case review |
| `debugger` | `Read, Grep, Glob, Edit, Bash` | Sonnet | Foreground, for root-cause fixes |

---

## METRICS & OBSERVABILITY

Track agent effectiveness to know when to intervene and when to trust.

### What to measure

| Metric | How | When to care |
|--------|-----|--------------|
| **Task completion rate** | Track which agent types complete vs. abandon | <80% = investigate |
| **Token cost per task** | Compare subagent vs. main-thread cost | Subagent should cost less |
| **False positive rate** | How often does this agent flag non-issues? | High = over-sensitive |
| **Time to result** | Background agent wall-clock vs. tokens | >5 min = stuck |
| **Re-edit rate** | How often does lead re-edit what agent produced? | >30% = poor delegation |

### Hook-based observability

Use existing hooks to track agent behavior:

```
PostToolUse: Track which tools agents use most
TeammateIdle: Log idle duration to detect stuck agents
TaskCompleted: Record task outcome and token usage
```

### Health check pattern

```
"Run /hook-obs --health to check agent-related hook performance.
 Look for: high block rate on agent-spawned tools, latency spikes in agent teams."
```

---

## CLAUDE MANAGED AGENTS (APRIL 2026)

Claude Managed Agents entered public beta April 2026. Key trade-off decisions:

| Dimension | Self-hosted (Claude Code) | Managed Agents |
|-----------|--------------------------|-----------------|
| **Infrastructure** | You manage | Anthropic manages |
| **Cost** | Token-only | Token + managed agent fee |
| **Team coordination** | Manual (shared task list, mailbox) | Built-in orchestration |
| **Context persistence** | Session-scoped | Extended across sessions |
| **Best for** | Solo dev, on-prem, custom hooks | Production, enterprise scale |

**When to use Managed Agents over self-hosted:**
- Multi-session tasks that need persistent context
- Enterprise compliance requiring managed infrastructure
- When orchestration overhead exceeds team value

---

## SOURCES

- [Claude Code Subagents Documentation](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Agent Teams Documentation](https://code.claude.com/docs/en/agent-teams)
- [Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Anthropic Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)
- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [VoltAgent Awesome Claude Code Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [Claude Code Subagents: Complete Guide](https://www.dplooy.com/blog/claude-code-tasks-complete-guide-to-ai-agent-workflow)
- [Agent Registry Discovery](#registry)
- [Hook Analyzer Agent](P:/.claude/agents/hook-analyzer.md)
