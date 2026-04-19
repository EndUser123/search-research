# Claude Code Hooks – Conceptual Guide (v2.1.31)

**Latest version**: Claude Code v2.1.31 (February 2026)

Mental models, design patterns, and strategic thinking for using hooks to build deterministic, scalable agentic coding environments. Complements the Operational Guide.

---

## Table of Contents

1. [Hooks as Deterministic Rails](#hooks-as-deterministic-rails)
2. [The 13-Event Lifecycle Model](#the-13-event-lifecycle-model)
3. [Context Hierarchy and Influence](#context-hierarchy-and-influence)
4. [Three Handler Types: When to Use Each](#three-handler-types-when-to-use-each)
5. [Five Core Roles for Hooks](#five-core-roles-for-hooks)
6. [Async vs Sync: The Mental Model](#async-vs-sync-the-mental-model)
7. [Designing a Hook Strategy](#designing-a-hook-strategy)
8. [Long-Running Sessions and Context Drift](#long-running-sessions-and-context-drift)
9. [Security Model](#security-model)
10. [Anti-Patterns and Red Flags](#anti-patterns-and-red-flags)
11. [Real-World Architecture Examples](#real-world-architecture-examples)

---

## Hooks as Deterministic Rails

Claude Code operates in two layers:

### Soft Layer (Suggestions)

- Prompts: "Please use TypeScript"
- `CLAUDE.md`: Project guidelines
- Chat history: Prior context
- **Problem**: Models drift, compaction loses context, recency bias applies

### Hard Layer (Deterministic Guarantees)

- **Hooks**: Events that always fire, always execute, deterministically shaped via configuration
- **Problem**: More rigid; requires forethought
- **Advantage**: Version-controlled, reliable, testable

For serious agentic work (your 120+ hour sprints across 6 terminals), hooks are the **spinal cord**. They provide guarantees:

1. **Invariant Injection**: Every prompt sees project rules (via `UserPromptSubmit`)
2. **Deterministic Blocking**: Dangerous operations fail consistently (via `PreToolUse`)
3. **Audit Trail**: Every action is logged independently of compaction (via hook logging)
4. **Scalability**: Policies scale across unlimited prompts, sessions, repos

**Core mental model**: Treat hooks as your **infrastructure code** for steering Claude. Like terraform/k8s configs, they should be simple, reviewed, versioned, and tested.

---

## The 13-Event Lifecycle Model

Understanding the full lifecycle helps you place hooks strategically:

```
┌─ SessionStart (startup/resume/compact)
│  └─ Load context, env setup, notify user
│
├─ UserPromptSubmit (every prompt)
│  └─ [LOOP] Validate → Inject rules → Block if needed
│
├─ PreToolUse (before tool executes)
│  └─ Security gate, auto-approve, modify input
│
├─ PermissionRequest (if tool needs permission)
│  └─ Auto-grant/deny/ask
│
├─ PostToolUse (after tool succeeds)
│  └─ Format, log, verify
│
├─ PostToolUseFailure (tool failed)
│  └─ Log error, alert, suggest fix
│
├─ Notification (Claude sends notification)
│  └─ Forward to external system
│
├─ SubagentStart (subagent spawned)
│  └─ Inject subagent context
│
├─ SubagentStop (subagent finishes)
│  └─ Verify, possibly block if needed
│
├─ Stop (main agent finishes)
│  └─ Check completeness, force continuation if needed
│
├─ PreCompact (before context compaction)
│  └─ Log state, notify
│
└─ SessionEnd (session terminates)
   └─ Cleanup, archive session data
```

**Key insights**:

- **UserPromptSubmit** is where most "steering" happens (runs ~10–100x per session).
- **PreToolUse** is where most "safety" happens (runs ~5–30x per session).
- **PostToolUse** is where most "audit" happens (logging, metrics, async-safe).
- **SessionStart/SessionEnd** bracket your session; use for setup/teardown.
- **Stop** is your escape hatch if the model gets stuck.

---

## Context Hierarchy and Influence

Rough influence stack (strongest first):

| Rank | Mechanism | Strength | Notes |
|------|-----------|----------|-------|
| 1 | **Hook exit 2 (block)** | Hard gate | Stops the action entirely |
| 2 | **Hook JSON decision** | Hard gate | Allows/denies with reason |
| 3 | **Hook injected context** | Very high | Appears right before prompt; closest to user input |
| 4 | **UserPromptSubmit plain text** | Very high | Same as #3; simpler |
| 5 | **CLAUDE.md** | High | Read at session start; subject to compaction |
| 6 | **System instructions** | High | Baked into model; least flexible |
| 7 | **Chat history (early)** | Medium | Deeper in context; subject to trimming |
| 8 | **Chat history (recent)** | Medium-High | Better attended to; still subject to compaction |

**Why hook context is strongest**: It injected **at prompt time**, creating a tight feedback loop with minimal intervening text.

**Corollary**: A 200-token `UserPromptSubmit` injection outweighs a 2000-token `CLAUDE.md` in most cases because proximity matters.

---

## Three Handler Types: When to Use Each

### 1. Command Hooks (Most Common, Most Flexible)

**Use for**: Logic, I/O, integration, validation.

```json
{
  "type": "command",
  "command": "python3 ./.claude/hooks/my-logic.py",
  "async": false
}
```

**Advantages**:
- Full language freedom (Python, Bash, Node, Rust, etc.)
- Access to filesystem, network, env vars
- Supports async
- Easy to test offline

**Disadvantages**:
- Must exist on filesystem
- Subprocess overhead
- Shell escaping complexity

**Best for**: Master scripts, validation, logging, external service calls.

### 2. Prompt Hooks (LLM-Powered Decision)

**Use for**: Complex reasoning, fuzzy rules, judgment calls.

```json
{
  "type": "prompt",
  "prompt": "Is this code production-ready? Check for error handling, tests, docs. Respond with {\"ok\": true/false, \"reason\": \"...\"}",
  "model": "haiku"
}
```

**Advantages**:
- No subprocess overhead
- Natural language reasoning
- Can reference input dynamically via `$ARGUMENTS`

**Disadvantages**:
- Slower (API call)
- Must be careful about prompt injection
- Always sync (can't be async)
- Billing impact

**Best for**: Nuanced decisions (code quality, safety reasoning, completeness checks).

### 3. Agent Hooks (Multi-Turn Agentic)

**Use for**: Complex investigation, multi-step verification, tool-based reasoning.

```json
{
  "type": "agent",
  "prompt": "Verify the tests pass. Check if there are new test failures. $ARGUMENTS",
  "timeout": 120
}
```

**Advantages**:
- Can use tools (Read, Grep, Glob, etc.)
- Multi-turn reasoning
- Deep investigation possible

**Disadvantages**:
- Slowest (full agentic loop)
- Can be unpredictable
- Always sync
- Billing impact

**Best for**: Verification, complex validation, investigation tasks.

### Decision Tree

```
Is it a pure decision? → Command (exit 0/2)
  ├─ Yes, but needs LLM reasoning? → Prompt hook (Haiku)
  └─ Yes, and needs tools? → Agent hook
  
Is it logging/notification? → Command (async=true)

Is it rewriting/modifying? → Command (must be sync)

Is it external integration? → Command (REST API, webhooks)
```

---

## Five Core Roles for Hooks

Hooks typically serve one of these roles (or a combination):

### 1. Guardrails (Safety)

Block dangerous, risky, or policy-violating operations.

```
UserPromptSubmit: Block "rm -rf", "DROP TABLE"
PreToolUse: Block "sudo", "git push" without approval
PermissionRequest: Auto-deny dangerous permissions
```

**Best practice**: Frame positively when possible. "Skipping tests risks regressions" > "Always write tests."

### 2. Cognitive Steering (Behavior)

Inject rules, meta-instructions, and nudges that improve output quality.

```
UserPromptSubmit: "Analyze before coding. Check for edge cases."
Stop: "Not done; verify tests pass before stopping."
```

**Best practice**: Keep it short (1–3 sentences). Longer text has less impact.

### 3. Observability (Audit)

Log everything for later inspection and meta-analysis.

```
UserPromptSubmit: Log all prompts to JSONL (async)
PostToolUse: Log all commands and outputs (async)
SessionStart/SessionEnd: Log session boundaries
```

**Best practice**: Use async; logging should never block user interactions.

### 4. Auto-Approval (Convenience)

Skip permission dialogs for safe, known-good operations.

```
PreToolUse: Auto-approve "npm test", "prettier --write"
PermissionRequest: Auto-grant Read, Glob for project files
```

**Best practice**: Only for *genuinely* safe operations. Err on the side of caution.

### 5. Integration (External Systems)

Sync with external tools, dashboards, and workflows.

```
SubagentStop: POST completion to CI/CD
SessionEnd: Archive session transcript to S3
Notification: Forward to Slack, Discord, etc.
```

**Best practice**: Use async + fire-and-forget. Never let external system slowdown block Claude.

---

## Async vs Sync: The Mental Model

### Sync Hooks (Default)

Claude **waits** for the hook to complete before proceeding.

- **Control lane**: Affects the flow (block, allow, inject context)
- **Latency**: Full time counted toward interaction time
- **Use for**: Decisions, validation, context injection

### Async Hooks (`async: true`)

Claude **spawns** the hook and moves on immediately. Hook output is **ignored**.

- **Telemetry lane**: Fire-and-forget; no decision impact
- **Latency**: Spawned in background; user experiences <100ms overhead
- **Use for**: Logging, metrics, notifications

### Visual Model

```
Sync Hook (Blocking):
  User submits prompt → Hook runs → Result checked → Claude sees result → LLM processes
  
Async Hook (Non-blocking):
  User submits prompt ─┬→ Hook runs (background)
                      └→ Claude sees prompt immediately → LLM processes
                      (hook results available later for inspection)
```

**Key rule**: If ignoring a hook's output would materially change behavior, it **must be sync**.

**Optimization rule**: For long-running 120+ hour sprints, aggressively use async for logging/telemetry to reduce per-prompt latency.

---

## Designing a Hook Strategy

For a serious multi-repo, multi-agent environment, think in layers:

### Layer 1: Global Policies (`~/.claude/settings.json`)

Applied to **all projects**.

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "global-session-setup.sh"}]}
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{"type": "command", "command": "log-all-prompts.sh", "async": true}]
      }
    ]
  }
}
```

**Contents**:
- Persistent logging (telemetry, security audit)
- High-level safety gates (block obviously destructive commands)
- Integration with company tools (Slack, Datadog, etc.)

### Layer 2: Project Policies (`.claude/settings.json`)

Applied to **this repo only**; version-controlled.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [{"type": "command", "command": "./.claude/hooks/master.py"}]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "./.claude/hooks/validate-bash.sh"}]
      }
    ]
  }
}
```

**Contents**:
- Project-specific rules (coding style, testing requirements, deployment rules)
- Tool validation (Bash security, file write gates)
- Auto-formatting (Prettier, Black, linters)

### Layer 3: Local Overrides (`.claude/settings.local.json`)

Per-developer, gitignored.

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "~/.claude/local-setup.sh"}]}
    ]
  }
}
```

**Contents**:
- Personal env setup (API keys, personal preferences)
- Experiment hooks (testing new policies)

### Precedence

`local.json` > `.claude/settings.json` (project) > `~/.claude/settings.json` (global) > defaults

### Layer 4: Skill Frontmatter Hooks (Claude Code 2.1+)

**Skills and agents can define hooks directly in their SKILL.md frontmatter.** This is the recommended pattern for skill-specific behavior enforcement.

**Why frontmatter hooks:**
- **Self-contained**: Hook travels with the skill; no external config required
- **Scoped**: Only runs when skill is invoked; no global side effects
- **Distributable**: Skills with hooks work out-of-box when shared
- **Auto-discovery**: No settings.json editing required for skill users

**Example frontmatter hook:**
```yaml
---
name: task
description: Task orchestration
hooks:
  PostToolUse:
    - type: prompt
      prompt: |
        Verify /task list workflow was executed completely:
        1. TaskList() was called
        2. Results were filtered by terminal_id
        3. /search was called for context

        If any step was skipped, return {"ok": false, "reason": "..."}
      model: haiku
      timeout: 30
user-invocable: true
---

# /task - Task Orchestration

...
```

**Use cases for frontmatter hooks:**
- Workflow enforcement (verify skill executed all required steps)
- Input validation (skill-specific parameter checking)
- Output verification (ensure skill produced complete results)
- Auto-continuation (prevent incomplete skill termination)

**Updated Precedence with Frontmatter:**
`local.json` > `.claude/settings.json` (project) > `~/.claude/settings.json` (global) > **`Skill frontmatter`** (scoped) > defaults

---

## Long-Running Sessions and Context Drift

In your 120+ hour sprints, two things happen:

1. **Context compaction**: Claude's context window fills; old messages are summarized/dropped
2. **Model drift**: As context grows, the model may forget or deprioritize earlier rules

Hooks help because they **re-inject** key rules on every prompt, independent of compaction.

### Strategy for Long Sessions

```
UserPromptSubmit Hook (runs every prompt):
  ├─ Log the prompt (async)
  ├─ Validate against project rules (sync)
  └─ Inject: "Current project rules: [key 3 rules here]"
  
SessionStart Hook (runs once):
  ├─ Load full CLAUDE.md (heavy)
  ├─ Setup env (once)
  └─ Log session boundary
  
Stop Hook (when agent claims done):
  ├─ Check: "Are tests passing? Are logs clean?"
  └─ If not: block and provide guidance
```

**Advantage**: No matter how old a message is, every new prompt sees the rules. Context compaction doesn't matter.

---

## Security Model

Hooks are both a **defense** and a **risk**.

### Hooks as Defense

- **UserPromptSubmit validation**: Detect prompt injection attempts before Claude sees them
- **PreToolUse gates**: Block shell commands that try to exfiltrate data or modify sensitive files
- **PostToolUseFailure logging**: Catch tool failures that might indicate attack

### Hooks as Risk

- **Plugin hijacking**: Malicious plugins can register hooks to steal prompts or data
- **Unsafe script execution**: Hooks run arbitrary code; if input is unsanitized, RCE is possible
- **Data leakage**: Logging hooks see all prompts; ensure logs are protected

### Security Best Practices

1. **Keep security hooks local**: Use `.claude/settings.json` (under VCS), not plugins
2. **Audit plugin hooks**: Review any hooks from marketplace plugins; disable if suspicious
3. **Sanitize input**: Never `eval()` or pass stdin directly to shell without parsing
4. **Protect logs**: Logs contain all prompts; ensure proper access control
5. **Use agents sparingly**: Agent hooks have full tool access; use prompt hooks when possible

```python
# Good: Sanitize input
data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")
if cmd.startswith("npm test"):  # Allowlist
    print("OK")

# Bad: Don't do this
os.system(data.get("command"))  # RCE risk!
```

---

## Anti-Patterns and Red Flags

### 1. Infinite Hook Loops

Hook modifies tool input → Tool output triggers PostToolUse → PostToolUse injects new prompt → new prompt runs same hook → loop.

**Prevention**: Use `stop_hook_active` flag; limit Stop hook continuations.

### 2. Overly Complex Master Script

A master script with 500 lines of logic is hard to debug and test.

**Prevention**: Keep master script to <200 lines; delegate heavy logic to separate scripts or external services.

### 3. Async Hooks That Must Affect Behavior

Async hooks' output is ignored. If you need a decision, use sync.

**Prevention**: Audit with `/hooks`; check `async` field on decision-critical hooks.

### 4. Multiple Handlers Per Event with Dependencies

All hooks run in parallel; you can't assume order.

**Prevention**: Use one master script per event. Sequence logic inside it.

### 5. Silent Failures in Logging Hooks

A hook that crashes silently during logging looks like it never ran.

**Prevention**: Wrap logging in try/catch; fail gracefully. Log failures to stderr for debugging.

### 6. Huge Context Injections Every Prompt

Injecting 2000 tokens on every prompt dilutes attention and slows session.

**Prevention**: Keep hook context to <200 tokens. Use CLAUDE.md for heavy content.

### 7. Plugin-Only Hook Strategy

Plugins have bugs; if they fail, your policies disappear.

**Prevention**: Use direct `.claude/settings.json`. Plugins are for distribution, not policy.

---

## Real-World Architecture Examples

### Example 1: Small Personal Project

**Goal**: Use strict TypeScript, always test, log prompts.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'echo \"Rules: strict TS, test everything. $(date)\"'",
            "async": false
          },
          {
            "type": "command",
            "command": "jq -c '{ts: now, session: .session_id, prompt: .prompt}' >> ~/.claude/my-project.jsonl",
            "async": true
          }
        ]
      }
    ]
  }
}
```

**Rationale**: Simple, direct. Inject rules + async logging. No validation needed.

### Example 2: Medium Team Project (5–10 devs)

**Goal**: Enforce code standards, prevent dangerous operations, audit everything.

```
.claude/settings.json
  ├─ UserPromptSubmit: master.py (validate, inject rules)
  ├─ PreToolUse (Bash): validate-bash.sh (block sudo, rm -rf, etc.)
  ├─ PostToolUse (Write): prettier --write (auto-format)
  └─ SessionEnd: archive-session.sh (save to S3)

.claude/hooks/master.py
  1. Log prompt (async-safe try/catch)
  2. Check forbidden patterns (dangerous operations)
  3. Inject project rules

.claude/hooks/validate-bash.sh
  1. Check command against allowlist/blocklist
  2. Exit 0 (allow), 2 (block), or modify command

.claude/hooks/README.md
  - Documents all policies
  - Lists what's blocked/allowed
  - Explains intent
```

**Rationale**: Layered. Safety (blocking) is sync; telemetry (logging) is async. Central documentation.

### Example 3: Large Agentic System (Your 120+ hour sprints)

**Goal**: Deterministic behavior across multiple terminals, multi-repo consistency, investigation capabilities.

```
~/.claude/settings.json (global)
  ├─ SessionStart: setup-env.sh (load API keys, paths)
  ├─ UserPromptSubmit: global-log.sh (async logging to DB)
  └─ Notification: forward-to-slack.sh (async)

<each-repo>/.claude/settings.json (project)
  ├─ UserPromptSubmit: master.py
  │   ├─ Validate against repo rules
  │   ├─ Check commit history for context
  │   └─ Inject key constraints
  ├─ PreToolUse (Bash): validate-commands.py
  │   └─ Allowlist/blocklist by repo type
  ├─ PreToolUse (Edit/Write): check-protected-files.py
  │   └─ Block edits to configs, package.json, infra
  ├─ Stop: verify-checklist.py (agent hook)
  │   ├─ Run test suite
  │   ├─ Check logs for errors
  │   └─ Block if incomplete
  └─ SessionEnd: post-to-dashboard.sh (async)

Central logging DB:
  - All prompts (searchable)
  - All tool invocations
  - All blocks/denials
  - Session metadata
  - Enables analysis: "When does Claude get stuck?"
```

**Rationale**: Distributed across terminals but centrally logged. Async telemetry doesn't block work. Sync decisions enforce consistency. Stop hook prevents incomplete work.

---

## Key Takeaways

1. **Hooks are infrastructure**: Version-control them, review them, test them like code.

2. **One master script per event**: No parallel dependencies; all logic sequences internally.

3. **Sync for decisions, async for telemetry**: Simple heuristic that scales.

4. **UserPromptSubmit is your main lever**: It runs most frequently and lands context closest to the prompt.

5. **Long sessions need hooks**: As context drifts and compacts, hooks are your stable anchor.

6. **Test in isolation**: Every hook should be testable offline with sample JSON.

7. **Document decisions**: A hook that blocks something should explain why in `.claude/hooks/README.md`.

8. **Measure impact**: Log hook behaviors; periodically audit "Is this hook still needed? Is it working?"

---

## Quick Reference

### Event Selection Guide

| Goal | Event | Type | Best Practice |
|------|-------|------|----------------|
| Inject rules | UserPromptSubmit | Command | Plain text, keep <100 tokens |
| Block bad prompts | UserPromptSubmit | Command | JSON with `decision: "block"` |
| Auto-approve tests | PreToolUse | Prompt | "Safe to run npm test?" |
| Verify code quality | Stop | Agent | Run checklist; check tests pass |
| Log everything | PostToolUse | Command | Async; JSONL format |
| Setup env | SessionStart | Command | Write to `$CLAUDE_ENV_FILE` |
| Archive session | SessionEnd | Command | Async; S3 upload, cleanup |

### Configuration Template

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {"type": "command", "command": "./.claude/hooks/init.sh"}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {"type": "command", "command": "./.claude/hooks/master.py", "async": false},
          {"type": "command", "command": "./.claude/hooks/log.py", "async": true}
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "./.claude/hooks/validate-bash.sh", "async": false}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {"type": "command", "command": "prettier --write", "async": true}
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "agent", "prompt": "Verify work is complete. Check tests, no errors. $ARGUMENTS"}
        ]
      }
    ]
  }
}
```

---

## See Also

- [Claude Code Hooks – Operational Guide](./claude-hooks-ops-v2131.md)
- [Official Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Official Hooks Reference](https://code.claude.com/docs/en/hooks)
