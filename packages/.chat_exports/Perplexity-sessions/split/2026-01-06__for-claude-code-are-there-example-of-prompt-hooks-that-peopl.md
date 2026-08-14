---
title: "for claude code, are there example of prompt hooks, that people try to use to stop CC from being stupid?"
date: "2026-01-06"
mode: "COPILOT"
uuid: "e1ce5cbd-f13c-4efc-92aa-d7550f1c1b78"
entry_count: 2
---

## Human

for claude code, are there example of prompt hooks, that people try to use to stop CC from being stupid?

## Assistant

---

## Prompt Hooks in Claude Code: Preventing "Stupid" Behavior

Claude Code supports two types of hooks—**prompt-based** and **command-based**—that developers use to enforce deterministic rules and prevent recurring mistakes. Here's what people actually use to stop Claude from behaving poorly:

### Prompt-Based Hooks (The Smart Approach)

Prompt-based hooks send context to Claude (Haiku) to make intelligent, context-aware decisions about whether to allow or block actions. They're currently limited to `Stop` and `SubagentStop` events, but they're powerful for preventing the agent from continuing when tasks aren't actually complete:[1]

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Evaluate if Claude should stop working. Check if: 1) All tasks complete 2) Any errors need fixing 3) Follow-up work needed. Respond with {\"decision\": \"approve\" or \"block\", \"reason\": \"explanation\"}"
      }]
    }]
  }
}
```

This prevents Claude from claiming it's done when there's actually broken code or incomplete work.

### The Block-at-Submit Strategy (Most Effective)

Enterprise-scale users at companies running billions of tokens through Claude Code discovered something important: **block at commit time, not at write time**. Blocking the agent mid-work confuses it and makes it "frustrated," but validating the final result before commit works reliably.[2]

This looks like a `PreToolUse` hook on git commits:

```bash
# Check for test success file before allowing commit
if [ ! -f /tmp/agent-pre-commit-pass ]; then
  echo "Tests must pass before commit"
  exit 2  # Blocking error - Claude gets feedback
fi
```

Exit code 2 tells Claude "your tool was blocked, here's why," and forces it into a test-and-fix loop.

### Command-Based Hooks for Behavioral Control

People use `UserPromptSubmit` hooks to inject behavioral expectations:[3]

**Stop unnecessary acknowledgments:**
```json
{
  "UserPromptSubmit": [{
    "hooks": [{
      "type": "command",
      "command": "echo 'Skip acknowledgments. Focus on the solution, not pleasantries.'"
    }]
  }]
}
```

**Block vague prompts before Claude processes them:**[4]
```python
# Hook that detects ambiguous requests and asks clarifying questions
# Uses new AskUserQuestion feature to force specificity upfront
if prompt_is_vague(prompt):
  return {"decision": "block", "reason": "Prompt is too vague. Please specify..."}
```

### Security & Code Quality Hooks

**Prevent modifications to sensitive files:**[5]
```json
{
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python3 -c \"check if .env, .git/, or package-lock.json in path; exit 2 if true\""
    }]
  }]
}
```

**Auto-validate code after edits (PostToolUse):**[3]
```json
{
  "PostToolUse": [{
    "matcher": "Edit:*.ts|Edit:*.tsx",
    "hooks": [{
      "type": "command",
      "command": "pnpm type:check --noEmit"
    }]
  }]
}
```

If type checking fails (exit code non-zero), Claude gets feedback and must fix it.

### Real Problems These Solve

From the community, people deploy hooks to stop Claude from:[6][7]

- **Making mock tests instead of real tests** — PostToolUse hook validates tests actually run
- **Hardcoding values** — PreToolUse hook checks for conditional logic requirements
- **Breaking package.json** — Protect sensitive files from Write operations
- **Repeating mistakes** — Block-at-submit catches final state, not mid-plan errors
- **Overly nested code** — PostToolUse hook rejects code with depth > N
- **Relative imports** — PreToolUse hook enforces absolute paths
- **Too many acknowledgments** — UserPromptSubmit context injection
- **Abandoning approach on minor errors** — Prompt hook forces error recovery

### Hook Configuration Best Practices

1. **Use exit code 2 for blocking** — Provides feedback to Claude
2. **Block at submit time, not write time** — Let the agent finish its plan first[2]
3. **Keep matchers specific** — `Edit:*.ts` not `Edit:*`
4. **Test commands manually** — Verify your hook works before relying on it
5. **Provide clear error messages** — When blocking with exit code 2, explain why via stderr

The fundamental insight from enterprise usage: **hooks are "must-do" deterministic rules**, while `CLAUDE.md` are "should-do" guidelines. Hooks handle the things Claude genuinely struggles with (state validation, quality gates, security boundaries), while documentation handles the context and reasoning.

## Human

Are there repos that should be considered for this kind of CC control and enhancing quality output from CC?

## Assistant

---

## High-Quality Repositories for Claude Code Control & Quality

Based on extensive research, there are **6 key repositories** you should consider depending on your needs. Here's what makes each valuable:

### **1. disler/claude-code-hooks-mastery** (1.7k stars) — Most Comprehensive
This is the gold standard for complete automation. It covers all 8 Claude Code lifecycle events (UserPromptSubmit, PreToolUse, PostToolUse, Notification, Stop, SubagentStop, PreCompact, SessionStart) with Python-based hooks that use UV for portability.[1]

**Key capabilities:**
- AI-generated task completion messages with TTS playback
- Security-focused prompt validation and dangerous command blocking
- Complete JSON logging to `logs/` for full observability
- 8+ output style formats (genui HTML, table-based, YAML-structured)
- Custom slash commands and sub-agent configurations
- Real-time status lines with session tracking

**Best for:** Enterprise automation, comprehensive visibility, building autonomous systems.[1]

***

### **2. Matt-Dionis/claude-code-configs** (520 stars) — Best for Framework-Based Projects
This is the **only repository that pre-builds complete production-ready configurations** for specific frameworks. Rather than just hooks, it provides entire `.claude/` directory structures with agents, commands, and hooks already optimized for your tech stack.[2]

**Frameworks supported:**
- Next.js 15 (11 specialized agents, App Router patterns)
- shadcn/ui (component library expertise)
- Tailwind CSS (responsive design patterns)
- Drizzle ORM (database patterns)
- Vercel AI SDK (streaming, function calling)
- MCP servers (memory persistence, token-gating)

**Installation:**
```bash
npx claude-config-composer nextjs-15 shadcn tailwindcss
```

This generates 40+ specialized agents covering your entire stack, merged intelligently without duplication.[2]

**Best for:** New projects built with modern frameworks, teams wanting framework-specific expertise out-of-the-box.[2]

***

### **3. decider/claude-hooks** (49 stars) — Focused Quality Control
Lightweight Python-based hooks targeting the specific "stupid" behaviors teams report:[1]

**Quality validators:**
- Code Quality Validator (enforces function length <30 lines, file size <200 lines, nesting depth <4)
- Package Age Checker (prevents npm/yarn installs older than 180 days)
- Task Completion Notifier (Pushover mobile notifications)

**Hierarchical configuration** lets you set different rules per directory (`.claude-hooks.json`).[1]

**Installation:**
```bash
python3 install-hooks.py
```

**Best for:** Teams wanting minimal overhead quality enforcement, code standards as guardrails.[1]

***

### **4. timoconnellaus/define-claude-code-hooks** (10 stars) — Type-Safe Modern Approach
TypeScript-first with full type safety and predefined utilities for common patterns:[3]

**Built-in utilities:**
- `blockEnvFiles` — Security protection for .env files
- `logPreToolUseEvents`, `logPostToolUseEvents` — Comprehensive logging
- TTS announcements (macOS `say`, Linux `espeak`, Windows PowerShell SAPI)
- Session tracking utilities

**Interactive setup:**
```bash
npx @timoaus/define-claude-code-hooks --init
```

**Best for:** Modern TypeScript shops, developers who want type safety and clean code patterns.[3]

***

### **5. johnlindquist/claude-hooks** (124 stars) — Performance-Focused
Leverages Bun runtime for ultra-fast TypeScript hook execution with complete type safety:[4]

**Key differentiator:** Strongly-typed payloads for PreToolUse (can return `decision: "approve" | "block"`), PostToolUse with success flags, full IntelliSense support.[4]

**Quick start:**
```bash
npx claude-hooks
```

Generates `.claude/settings.json`, `.claude/hooks/index.ts`, and utilities automatically.[4]

**Best for:** High-performance requirements, teams using Bun, developers who want native TypeScript execution.[4]

***

### **6. rosmur.github.io/claudecode-best-practices** — Strategic Reference (Not Code)
Comprehensive 5,000-word guide synthesizing 12 authoritative sources covering context management, planning workflows, quality systems, and tool strategy.[5]

**Key insights:**
- Context management is the #1 failure mode (not hooks)
- Planning before coding is non-negotiable
- Simple control loops beat complex multi-agent systems
- Heavy MCP usage (>20k tokens) cripples context
- LLM search outperforms RAG for code discovery

**Best for:** Understanding CC optimization strategy, making architectural decisions, learning from 12 expert voices.[5]

***

## Which Repo Should You Use?

| **Your Scenario** | **Recommended Repo** | **Why** |
|---|---|---|
| New Next.js/React project | Matt-Dionis/claude-code-configs | 40+ agents already built + generator |
| Need code quality gates quickly | decider/claude-hooks | Minimal setup, focused validators |
| TypeScript-first shop | timoconnellaus or johnlindquist | Type safety + modern patterns |
| Want complete automation infrastructure | disler/claude-code-hooks-mastery | Full lifecycle + TTS + observability |
| Understanding optimization strategy | rosmur.github.io/best-practices | Reference guide, synthesized wisdom |
| Existing project needing targeted control | Combination approach (see below) | Start with strategy guide, layer repos |

***

## Integration Pattern for Your Solo Developer Setup

Given your Windows 11 + Claude Code expertise:[memory:context] You'd likely benefit from:

1. **Start with strategy**: Read rosmur.github.io best practices to understand context management and planning workflows
2. **Pick one foundation**: Probably **decider/claude-hooks** for clean quality gates (Python is portable on Windows)
3. **Layer framework config**: If using frameworks, add **Matt-Dionis/claude-code-configs** to auto-generate agents
4. **Supplement with observability**: Borrow logging patterns from **disler/claude-code-hooks-mastery** (their logging examples are the best reference)
5. **Type-safety if TypeScript**: Use **timoconnellaus/define-claude-code-hooks** for type-safe hook definitions

This gives you: strategic foundation → focused quality → framework expertise → observability → type safety, without over-engineering.
