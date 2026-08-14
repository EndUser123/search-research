---
title: "In claude code, do people add a hook to prompt 'Did we forget something?'  If yes, how?  do they do other things also?  "
date: "2026-01-01"
mode: "COPILOT"
uuid: "d16e129c-fcc1-443f-86ca-8f8f692d2e00"
entry_count: 1
---

## Human

In claude code, do people add a hook to prompt "Did we forget something?"  If yes, how?  do they do other things also?  Are there repos with this sort of idea?

## Assistant

Now I'll create the final comprehensive response based on all the research gathered.

## Yes—And It's More Nuanced Than You'd Expect

Developers do implement "Did we forget something?" style verification in Claude Code, but not typically as a single direct hook prompt. Instead, they use a sophisticated ecosystem of patterns depending on their needs and workflow stage.[1][2]

### The Most Common Approach: Manual Checklist Verification

The most widespread method isn't actually a hook—it's a tactical pattern shared across Reddit and blog posts: **explicitly paste a verification checklist into the conversation after Claude creates a plan.** One developer documented this workflow:[3]

> After Claude generates its plan, the user copies in a detailed checklist and prompts: "Please verify plan against checklist." This forces Claude to pause and reflect instead of rushing to respond, creating a genuine evaluation moment rather than just compliance theater.

The key insight: **checklists in CLAUDE.md files get ignored**, but explicit checklist prompts in the active conversation work. The difference is forcing a reflection step rather than relying on passive documentation.[3]

### Hook-Based Verification Patterns

For developers who want automation, the ecosystem offers several approaches:

**1. Stop Hook (Block-at-Submit)**[2][4]

The most recommended pattern runs validation when Claude is about to finish, using a `Stop` hook that blocks execution until acceptance criteria are met. This follows the principle: *let Claude finish its work, then validate the final result*—avoiding the mid-plan confusion that comes from blocking at write-time.[2]

Example structure from enterprise implementations:
- `Stop` hook triggers final validation
- Checks: tests pass, documentation updated, acceptance criteria met
- Returns structured JSON with decision + reason to Claude
- Claude reads the feedback and iterates until validation passes[4]

**2. UserPromptSubmit Hook (Context Injection)**[5][4]

Injects requirements and checklists as context at prompt-submission time:

```json
"hooks": {
  "UserPromptSubmit": [{
    "hooks": [{
      "type": "command",
      "command": ".claude/hooks/user-prompt-submit.py",
      "timeout": 30
    }]
  }]
}
```

This hook reads markdown files containing:
- Definition of Done checklist
- Acceptance criteria
- Coding standards  
- Security requirements
- Architecture principles

The hook injects these as context automatically, so every session starts with the requirements visible.[4]

**3. PostToolUse Hook (Outcome Validation)**[5]

Runs after code edits to check:
- TypeScript compilation passes
- Linting rules satisfied
- Tests for changed files pass

Returns structured feedback so Claude can fix issues in the same conversation.[5]

### The "Other Things" Developers Do

Beyond checklist verification, the hook ecosystem addresses multiple pain points:

**Security & Workflow Enforcement**[5]
- Branch protection hooks: Block direct commits to main, require feature branches
- Secret scanning: Block prompts containing potential API keys or credentials
- Command policy enforcement: Only allow specific bash operations

**Quality Gates**[1][2]
- Code formatting (Prettier, Black)
- Type checking (TypeScript, mypy)
- Linting with auto-fix capability
- TDD compliance (block changes that violate test-first patterns)

**Notification & Context Management**[1]
- Desktop notifications when Claude needs permission
- Session archival for episodic memory
- Automatic context priming on startup
- Hook-based skill activation (activate right skill for current task)

**Context Preservation**[2]
- Architecture documentation enforcement (Claude must read docs before major changes)
- Repository-specific CLI reference (simplified tools instead of MCP overload)
- "Memory bank" update hooks that track progress between sessions

### Repository Examples & Tools

The **awesome-claude-code** repository lists curated hooks and workflows:[6]

- **RIPER Workflow**: Enforces Research→Innovate→Plan→Execute→Review phases with specialized agents for each
- **Claude Code Infrastructure Showcase**: Uses hooks to intelligently select which skill to activate based on context
- **TDD Guard**: Real-time monitoring that blocks file operations violating TDD principles
- **TypeScript Quality Hooks**: 5ms validation (SHA256 config caching) for live-editing feedback loop

**Hook SDKs & Tools**:
- `cchooks` (Python): Lightweight SDK for writing custom hooks
- `claude-hooks` (TypeScript): Full hook configuration system
- `/create-hook` slash command: Interactive hook generator with project-aware suggestions (auto-detects Prettier, ESLint, etc.)
- `cc-tools` (Go): High-performance hook utilities with minimal overhead

### Key Design Principle: Block-at-Submit, Not Block-at-Write

The most important learning from production implementations:[2]

❌ **Don't block** when Claude is mid-plan or mid-edit (blocks at `PreToolUse` Write/Edit)
✓ **Do block** at final submission points (`Stop` hook or `PreToolUse` Bash for git commits)

Blocking mid-workflow confuses or "frustrates" Claude. Instead, let it finish its plan, then validate the complete result. This produces better iteration loops and clearer feedback.

### Assembling Your Own Verification Hook

The most practical approach for a solo developer like you would combine:

1. **CLAUDE.md**: High-level guidelines (read once per session)
2. **Stop hook** (light): Checklist prompt at end of chat
3. **PostToolUse hook** (optional): Auto-run quality checks after edits
4. **Manual checklist paste** (for high-stakes work): Explicit verification before commit

This hybrid approach avoids static file amnesia while keeping automation friction low.

***
