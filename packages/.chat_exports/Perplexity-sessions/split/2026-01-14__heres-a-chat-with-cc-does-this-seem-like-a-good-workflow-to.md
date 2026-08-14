---
title: "Here's a chat with CC.  Does this seem like a good workflow to you?

❯ /git-worktrees list

● Bash(cd /p && git workt"
date: "2026-01-14"
mode: "COPILOT"
uuid: "66f61ebe-8dee-43e7-bea7-fd822125fd0b"
entry_count: 4
---

## Human

Here's a chat with CC.  Does this seem like a good workflow to you?

❯ /git-worktrees list

● Bash(cd /p && git worktree list)
  ⎿  P:                                  0d6e8208e [main]
     P:/worktrees/statusline-wt-enhance  346983a50 [statusline-wt-enhance]
  ⎿  Running PostToolUse hooks… (1/12 done)

● Current worktrees:
  ┌────────────────────────────────────┬───────────┬───────────────────────┐
  │                Path                │  Commit   │        Branch         │
  ├────────────────────────────────────┼───────────┼───────────────────────┤
  │ P:/                                │ 0d6e8208e │ main                  │
  ├────────────────────────────────────┼───────────┼───────────────────────┤
  │ P:/worktrees/statusline-wt-enhance │ 346983a50 │ statusline-wt-enhance │
  └────────────────────────────────────┴───────────┴───────────────────────┘
  You are currently in: P:/ (main worktree)

❯ cd P:/worktrees/statusline-wt-enhance

● Bash(cd P:/worktrees/statusline-wt-enhance && pwd && git branch --show-current)
  ⎿  /p/worktrees/statusline-wt-enhance
     statusline-wt-enhance
  ⎿  Running PostToolUse hooks… (1/12 done)

● Now in worktree: P:/worktrees/statusline-wt-enhance on branch statusline-wt-enhance

  Statusline should show: 🌳 statusline-wt-enhance [wt]

❯ 🔔🧠💡 │ 🤖 GLM-4.7 📂 P:\ | 🌿 main 💾 3 | 🟡 105k/200k | ⌛1:20 |  10:50 | ConsoleHost_505e2,
  that's what the statusline shows.

● The statusline shows 🌿 main because the cd command I ran only affected the subprocess - not your actual terminal.

  The issue: My Bash tool runs in a subprocess, so directory changes don't persist to your terminal where the statusline runs.

  To see [wt] in the statusline, you need to cd in your actual terminal:

  cd P:/worktrees/statusline-wt-enhance

  Then the statusline will show: 🌳 statusline-wt-enhance [wt]

  The statusline reads from your terminal's current directory, not from commands I run.

❯ but how do I know what tree I'm working in?

● Good question. Here are practical ways to check which worktree you're in:

  # Method 1: Show git root (most direct)
  git rev-parse --show-toplevel
  # Output: P:/              ← main worktree
  # Output: P:/worktrees/statusline-wt-enhance  ← named worktree

  # Method 2: List all worktrees, look for your path
  git worktree list
  # P:                                  [main]           ← you're here if toplevel is P:/
  # P:/worktrees/statusline-wt-enhance  [statusline-wt-enhance]  ← you're here if toplevel matches

  # Method 3: Quick check - am I in main or a worktree?
  git rev-parse --show-toplevel | grep -q "worktrees" && echo "Worktree" || echo "Main"

  The key indicator: If git rev-parse --show-toplevel contains worktrees/, you're in a worktree.

  Quick alias you could add:

  # Add to .bashrc/.zshrc
  alias wt='git rev-parse --show-toplevel | xargs basename'
  alias wtf='git worktree list'

  Then just type wt to see which worktree you're in.

  For the statusline to show [wt], you need to actually cd in your terminal (where Claude Code is running) to P:/worktrees/statusline-wt-enhance. The statusline reads your terminal's cwd, not subprocess commands I run.
  ⎿  Stop says:
     ⚠️ Hook violations this session: 5
     Top patterns:
       WARNING: python -c executes arbitrary code: 3x
       WARNING: find -exec with placeholder: 2x
     Run `analyze_blocks.py` for details.

❯ git rev-parse --show-toplevel

● Bash(cd /p && git rev-parse --show-toplevel)
  ⎿  P:/
  ⎿  Running PostToolUse hooks… (1/12 done)

● You're in P:/ - the main worktree.

  To be in the worktree, you'd need to cd in your actual terminal (where Claude Code runs):

  cd P:/worktrees/statusline-wt-enhance

  Then git rev-parse --show-toplevel would show P:/worktrees/statusline-wt-enhance and the statusline would show 🌳 statusline-wt-enhance [wt].
  ⎿  Stop says:
     ⚠️ Hook violations this session: 7
     Top patterns:
       WARNING: python -c executes arbitrary code: 5x
       WARNING: find -exec with placeholder: 2x
     Run `analyze_blocks.py` for details.

❯ Are you trying to say, that the only way to be sure that I'm making changes in the worktree, is to
  exist CC, cd to the worktree, start CC from that worktree, do my work, exit CC, cd to root, launch
  cc, then merge to main?

● No, that's not what I mean. You can just cd while CC is running - no need to exit/restart.

  Simpler workflow:

  # 1. Start CC from wherever (P:/ is fine)
  # 2. When you want to work in a worktree:
  cd P:/worktrees/statusline-wt-enhance

  # Statusline updates immediately to: 🌳 statusline-wt-enhance [wt]

  # 3. Do your work (commits go to the worktree's branch)

  # 4. When done, switch back:
  cd P:/

  # Statusline updates to: 🌿 main

  # 5. Merge the worktree branch into main
  git merge statusline-wt-enhance

  The key point: CC doesn't care which directory you're in - it follows your terminal's cwd. Just cd and the statusline updates instantly.

  Only restart CC if: You want to start a fresh session context. For directory changes, just cd.
  ⎿  Stop says:
     ⚠️ Hook violations this session: 8
     Top patterns:
       WARNING: python -c executes arbitrary code: 6x
       WARNING: find -exec with placeholder: 2x
     Run `analyze_blocks.py` for details.

❯ You said this:
  ● The statusline shows 🌿 main because the cd command I ran only affected the subprocess - not your
  actual terminal.

● You're right to call that out. Let me clarify the inconsistency:

  What I meant:
  ┌─────────────────────────┬───────────────────┬───────────────────────────────────────┐
  │         Action          │    Who runs it    │         Effect on statusline          │
  ├─────────────────────────┼───────────────────┼───────────────────────────────────────┤
  │ I run cd via Bash tool  │ Subprocess        │ No effect - statusline unchanged      │
  ├─────────────────────────┼───────────────────┼───────────────────────────────────────┤
  │ YOU type cd in terminal │ Your actual shell │ Immediate effect - statusline updates │
  └─────────────────────────┴───────────────────┴───────────────────────────────────────┘
  So the correct workflow:

  # In your actual terminal (not via me):
  cd P:/worktrees/statusline-wt-enhance

  Then the statusline immediately shows 🌳 statusline-wt-enhance [wt].

  My earlier confusion: I was explaining why my cd command didn't change the statusline (because bash subprocess != your terminal), but I didn't clearly state that YOUR cd would work instantly.

  Summary: You don't need to restart CC. Just cd in your terminal and the statusline follows. My cd commands don't affect your terminal's cwd.
  ⎿  Stop says:
     ⚠️ Hook violations this session: 10
     Top patterns:
       WARNING: python -c executes arbitrary code: 8x
       WARNING: find -exec with placeholder: 2x
     Run `analyze_blocks.py` for details.

❯ lol.  how can I cd in the terminal if I don't exit CC?

● You're absolutely right - I painted myself into a corner.

  The reality: If you're in CC's interactive mode, you can't cd in your terminal without exiting CC.

  Your original workflow was correct:

  1. Exit CC
  2. cd P:/worktrees/statusline-wt-enhance
  3. Start CC
  4. Do work (statusline shows [wt])
  5. Exit CC
  6. cd P:/
  7. Start CC
  8. Merge to main

  Or use CC's directory feature:
  - CC has an "Add Directory" feature (/add-dir) but that's for context, not cwd
  - There may be a /cd command in newer versions, or shell escape

  Alternative: Run CC as a subshell:
  cd P:/worktrees/statusline-wt-enhance
  claude  # Starts CC in this directory
  # Do work
  exit    # Back to shell, still in worktree

  I overcomplicated this. Your original understanding was correct - to work in a worktree with correct statusline display, start CC from that directory.

## Assistant

This is a great question, and I appreciate you catching the inconsistencies in that CC session. Let me give you my honest assessment of the workflow:

## Your Original Workflow Is Sound

Yes, the pattern you outlined is correct:

1. Exit CC
2. `cd P:/worktrees/statusline-wt-enhance`
3. Start CC
4. Do work (statusline correctly shows `🌳 statusline-wt-enhance [wt]`)
5. Exit CC, `cd P:/`, start CC, merge to main

This ensures:
- Your statusline is **truthful** about which worktree you're in
- Git operations happen in the correct worktree context
- No subprocess vs. terminal confusion

## The CC Assistant's Confusion

What happened in that chat was a classic problem: **the assistant knew the technical facts but didn't account for CC's architectural constraints**:

- ✅ Correct: "cd in subprocess doesn't affect your terminal's cwd"
- ✅ Correct: "Statusline reads from your terminal's cwd"
- ❌ Wrong conclusion: "Just cd while CC is running"
- ❌ Didn't acknowledge: "But you can't cd while CC is running"

It's a reasoning gap — the assistant had all the pieces but didn't assemble them coherently.

## Better Workflow Options

Given this limitation, here are practical alternatives:

### Option A: Multiple CC Sessions (What you're doing)
Works fine. The friction is minimal if you're already comfortable with the exit/cd/start pattern.

### Option B: Persistent Shell Tab Pattern
```powershell
# Terminal tab 1 (P:/ - main worktree)
PS> claude

# Terminal tab 2 (P:/worktrees/statusline-wt-enhance)
PS> cd P:/worktrees/statusline-wt-enhance
PS> claude  # Separate CC session here
```

You run two CC instances simultaneously on different branches. Useful if you're bouncing between worktrees frequently.

### Option C: Claude Code Hook/Alias
You could add a hook that detects you're about to cd to a worktree and handles context switching intelligently. But that's adding complexity for a workflow that's already working.

## My Take

**Your original workflow is the right call.** It's:
- Explicit (no magic, no confusion)
- Safe (you always know which branch you're on)
- Simple (three commands: exit, cd, start)

The only optimization worth considering is **Option B** if you find yourself context-switching between worktrees frequently in the same session.

The CC assistant's confusion highlights something useful for your architecture though: **if you're building multi-session orchestration**, you might want explicit session metadata that tracks `cwd` + `branch` state independently, rather than relying on statusline inference. That's probably something your custom hooks already handle, but worth noting.

Does this match your current understanding, or have you found a smoother pattern?

## Human

Are there repos that address this topic?

## Assistant

Yes, there are several actively maintained projects addressing exactly this problem:

## Direct Worktree Solutions

**sprout**  is probably the most directly relevant. It's a Python CLI tool (MIT licensed, Python 3.11+) that automates git worktree + Docker Compose workflows. Key features:[1]
- Automatic `.env` file generation from templates
- Smart port allocation to avoid conflicts
- Centralized worktree management in `.sprout/` directory
- GitHub: `SecDev-Lab/sprout`

The documentation includes architecture overviews and usage guides, and it's actively maintained (latest release v0.4.0 in June 2025).

## Claude Code + Worktree Ecosystem

There are several projects specifically for Claude Code + worktrees:

**Claude Code Desktop Docs**  now have official worktree support built-in. The desktop app can automatically create isolated worktrees at `~/.claude-worktrees` (configurable), enabling parallel Claude Code sessions per branch.[2]

**incident.io's approach**  includes a custom wrapper (`w` command) that abstracts away the friction:[3]
- `w myproject new-feature claude` - enters worktree and starts Claude Code
- Intelligent completion for worktree names
- Direct git operations without switching directories
- Handles commit/push directly from anywhere

## Educational Resources & Frameworks

**nrmitchi's Git Worktrees guide**  documents structured approaches specifically for AI agents, including:[4]
- Worktrees organized under `.trees/{TASK_ID}`
- Branch naming conventions tied to task IDs
- Instructions for allowing Claude to self-create worktrees

**Video tutorials** show working implementations:
- **IndyDevDan**  demonstrates parallelizing multiple Claude 4 Opus instances across worktrees with merge strategies[5]
- **Sami Sabiri**  shows a complete workflow video with 4 parallel Claude Code sessions[6]

## Why These Matter for Your Workflow

These repos solve the exact problem you encountered—automating away the manual exit/cd/start cycle. The evolution is clear:

1. **Manual**: Exit CC → cd → start CC → work → exit → cd → merge
2. **Sprout-level**: Automatic `.env`, port management, centralized structure
3. **Claude Desktop native**: Built-in worktree support
4. **incident.io approach**: One-command entry/exit with context preservation

The most relevant for you would be:
- **sprout** if you want a standalone tool with port/env management
- **Claude Code Desktop** if you want native first-class support
- **incident.io's wrapper** if you want minimal friction around CC entry/exit

Do any of these patterns match what you're trying to build into your system, or are you looking for something more specialized?

## Human

I got this error, presumably because the P:/.claude directory wasn't copied, or maybe ~/.claude.
PS P:\worktrees> cd .\statusline-wt-enhance\
PS P:\worktrees\statusline-wt-enhance> claude --dangerously-skip-permissions -r main_inst
No conversation found with session ID: f54b0ab3-ede5-42e0-98ed-ded67730cbbf
PS P:\worktrees\statusline-wt-enhance>

Any way around it?

## Assistant

This is a session ID mismatch. Claude Code stores conversation state in `~/.claude` (or `P:/.claude` if that's your home), and when you start a new Claude Code instance from a different worktree directory, it's trying to resume a session that doesn't exist in that context.

Here are your options:

## Quick Workarounds

**Option 1: Start fresh (simplest)**
```powershell
claude --dangerously-skip-permissions
# No -r flag, starts new session
```
This creates a new conversation in the current worktree context.

**Option 2: Copy the claude directory to the worktree**
```powershell
# From P:/ (main worktree)
Copy-Item P:\.claude P:\worktrees\statusline-wt-enhance\.claude -Recurse
```
Then `claude` will find the session cache locally. However, this can cause state conflicts if both instances write simultaneously.

**Option 3: Use a shared claude directory**
Set `CLAUDE_HOME` environment variable to point to a shared location:
```powershell
$env:CLAUDE_HOME = "P:\.claude"
claude --dangerously-skip-permissions -r main_inst
```
This tells Claude Code to look for sessions in the main worktree's `.claude` directory regardless of cwd.

**Option 4: Don't use -r flag initially**
```powershell
claude --dangerously-skip-permissions
# Starts new session, but uses local .claude if it exists
```

## Root Cause

The `-r main_inst` flag tries to resume session `f54b0ab3-ede5-42e0-98ed-ded67730cbbf`, but that session metadata lives in the original `.claude` directory. When you `cd` to a worktree without copying `.claude`, Claude Code can't find it.

## Recommendation

For your worktree workflow, I'd suggest **Option 3** (set `CLAUDE_HOME`) if you want sessions to be continuable across worktrees, or just **start fresh per worktree** (Option 1) to keep contexts isolated by branch. 

Which approach fits better with how you want to manage session state across worktrees?

## Human

PS P:\> cd .\worktrees\statusline-wt-enhance\
PS P:\worktrees\statusline-wt-enhance> $env:CLAUDE_HOME = "P:\.claude"
PS P:\worktrees\statusline-wt-enhance> claude --dangerously-skip-permissions -r main_inst
No conversation found with session ID: f54b0ab3-ede5-42e0-98ed-ded67730cbbf
PS P:\worktrees\statusline-wt-enhance>

## Assistant

The issue persists because the session ID `f54b0ab3-ede5-42e0-98ed-ded67730cbbf` doesn't exist in `P:\.claude` — either it was never saved there, or it's stored under a different identifier.

Try these steps to diagnose and fix:

**Step 1: Check what sessions exist**
```powershell
$env:CLAUDE_HOME = "P:\.claude"
ls P:\.claude\sessions -Recurse
# Lists all saved session files
```

**Step 2: List Claude's available sessions**
```powershell
claude --list-sessions
# or check if this flag exists in your version
```

**Step 3: Start without specifying a session ID**
```powershell
$env:CLAUDE_HOME = "P:\.claude"
claude --dangerously-skip-permissions
# Starts new conversation but uses P:\.claude for storage
```

**Step 4: If you need to resume main_inst specifically**
```powershell
# First, verify the session exists:
Get-Content P:\.claude\sessions\*.json | Select-String "main_inst"
# If found, try without the session ID first to test the CLAUDE_HOME env var works
```

## Most Likely Cause

The session `main_inst` was probably created in a different Claude Code instance or environment, and the session metadata either:
- Wasn't persisted to `P:\.claude`
- Was stored under a different session ID
- Uses a different naming scheme than `main_inst`

**Simplest fix: Just start fresh in this worktree**
```powershell
$env:CLAUDE_HOME = "P:\.claude"
claude --dangerously-skip-permissions
```

Then you'll have a new session in the worktree, but all subsequent Claude Code instances in worktrees will use the shared `P:\.claude` directory.

Does `claude --list-sessions` work in your version, or can you check what's actually in `P:\.claude\sessions\`?
