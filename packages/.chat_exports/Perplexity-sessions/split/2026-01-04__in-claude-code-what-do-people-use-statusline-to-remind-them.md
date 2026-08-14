---
title: "in claude code, what do people use statusline to remind them of?  I'm thinking things like, have lunch, or CC detected t"
date: "2026-01-04"
mode: "COPILOT"
uuid: "5ac8314b-2114-48d1-b156-53bb03166f9c"
entry_count: 5
---

## Human

in claude code, what do people use statusline to remind them of?  I'm thinking things like, have lunch, or CC detected that the prd needs updating, or that CC didn't check for linting, etc.

## Assistant

Based on current community usage and technical capabilities, **statusline** in Claude Code is a programmable interface (configured via `~/.claude/settings.json`) that executes a script ~3 times per second to update the bottom bar of your CLI.

Most users primarily use it for **resource anxiety** (cost & context window), but advanced users like yourself leverage it for **state persistence**—reminding you of background conditions that Claude itself might "forget" between turns.

Here is a breakdown of what people use the statusline to remind them of, ranging from standard to advanced workflow integrations.

### 1. The "Resource Anxiety" Reminders (Standard)
These are the most common uses, intended to prevent the session from crashing or becoming too expensive.
*   **Context Window Danger Zone:** "Am I about to lose the beginning of this conversation?"
    *   *Display:* `Context: 85% [████████..]`
    *   *Why:* Claude Code has a context limit (e.g., 200k tokens). If you hit 100%, the session might truncat or require a `/compact`. Users add a visual warning (red color) when >80% to remind them to wrap up or compact.
*   **Cost Velocity:** "Is this session getting expensive?"
    *   *Display:* `Session: $2.40 | Daily: $5.12`
    *   *Why:* Reminds you if the current task is burning tokens too quickly (e.g., stuck in a loop reading massive files).
*   **Billing Block Timer:** "When does my rate limit reset?"
    *   *Display:* `Reset in: 1h 45m`
    *   *Why:* Power users track the 5-hour message cap intervals to plan their "sprints."

### 2. The "Where Am I?" Reminders (Contextual)
Because Claude Code can traverse directories and switch git branches autonomously, users use the statusline to ground themselves.
*   **Git State Protection:** "Did Claude switch branches without me noticing?"
    *   *Display:* `Git: main ⚠️ (DIRTY)` or `Git: feat/login-page`
    *   *Why:* Prevents you from asking Claude to push code when it's sitting on the wrong branch or in a detached head state.
*   **Environment Mode:**
    *   *Display:* `ENV: PROD` vs `ENV: DEV`
    *   *Why:* A bright red reminder if you are connected to a production database or environment.

### 3. The "Workflow Compliance" Reminders (Your "Lint/PRD" Idea)
This is the advanced territory you asked about. Because the statusline script runs frequently (every ~300ms), you cannot run heavy tasks (like `npm run lint`) directly in it. Instead, users implement the **Hook-to-State Pattern**:

**How it works:**
1.  **The Hook:** A `PostToolUse` hook runs a heavy check (e.g., checks linting, compares file timestamps) and writes the result to a tiny temporary file (e.g., `/tmp/cc_state_lint`).
2.  **The Statusline:** Reads that file instantly and displays the icon.

**Examples:**
*   **"Linting Check" Reminder:**
    *   *Scenario:* You want to know if the code Claude just wrote passes linting without running it manually.
    *   *Implementation:* A `PostToolUse` hook triggers on `Edit` commands. It runs `eslint`, and if it fails, writes `FAIL` to a state file.
    *   *Statusline:* Reads file. If `FAIL`, shows: `Lint: ❌ (Check needed)`
*   **"Stale PRD" Reminder:**
    *   *Scenario:* Reminds you that code has drifted from the Product Requirement Doc.
    *   *Implementation:* A background script checks if `src/` files have a newer modification time than `docs/PRD.md` by a significant margin (e.g., > 2 hours).
    *   *Statusline:* `⚠️ PRD OUTDATED`
*   **"Human in the Loop" Reminder:**
    *   *Scenario:* Reminds you to review a specific file before approving the next step.
    *   *Statusline:* `PENDING REVIEW: api_client.ts`

### 4. Personal & Biological Reminders
Since the statusline is just a script (Bash/Python), it can display anything.
*   **Bio-Breaks:** `🍱 Lunch: 12:30` (simple clock comparison).
*   **Meeting Alerts:** Pulls next meeting from a calendar CLI tool: `Next: Standup in 15m`.
*   **Prayer Times:** Some users display prayer time countdowns.

### Summary: How to Implement Your Ideas
To implement your specific ideas in `~/.claude/statusline.sh`:

```bash
#!/bin/bash
# Read standard Claude input (optional, but good for context)
input=$(cat)

# 1. HAVE LUNCH REMINDER
current_hour=$(date +%H)
if [ "$current_hour" -ge 12 ] && [ "$current_hour" -lt 13 ]; then
  LUNCH_MSG="🍱 EAT FOOD"
fi

# 2. LINT STATUS (Requires a separate hook to write to /tmp/cc_lint_status)
if [ -f /tmp/cc_lint_status ]; then
  LINT_STATUS=$(cat /tmp/cc_lint_status)
  if [ "$LINT_STATUS" == "FAIL" ]; then
     LINT_MSG="Lint: ❌"
  fi
fi

# 3. STALE PRD (Check timestamps directly here if fast, else use hook)
# If code is newer than PRD by 1 hour
if [ $(stat -f %m src) -gt $(($(stat -f %m PRD.md) + 3600)) ]; then
  PRD_MSG="⚠️ PRD STALE"
fi

echo "$LUNCH_MSG $LINT_MSG $PRD_MSG"
```

## Human

what novel ideas are out there?  What surprised people?

## Assistant

The most novel and surprising ideas for the statusline revolve around **"Agentic Introspection"**—using the statusline not just for metrics, but to visualize what the agent "feels" or to act as a second pair of eyes on the agent's behavior.

The absolute standout that surprised the community is a "Tamagotchi" that is actually a behavioral enforcement system in disguise.

### 1. The "Behavioral Tamagotchi" (Most Surprising)
This idea (notably implemented by user `Ido-Levi`) shocked people because it looks like a toy but acts like a supervisor.
*   **The Novelty:** It places a pixel-art pet `(◕ᴥ◕)` in your statusline that has "stats" like Hunger, Energy, and Mood.
*   **The Surprise:** The "Mood" isn't random. The script uses a **second, cheaper LLM** (like Llama 3 on Groq) to silently read Claude's output in the background.
    *   **If Claude follows instructions:** The pet is happy 😊.
    *   **If Claude hallucinates or ignores the PRD:** The pet gets angry 😠.
    *   **If Claude deletes files without asking:** The pet "throws a table" ┻━┻.
*   **Why it's useful:** It gives you an instant emotional signal that "something is wrong" without you needing to read every line of the log.

### 2. The "Agentic Mirror" (Self-Summarization)
Instead of static text, some users set up a "thought mirror" that forces the model to explain *why* it is doing what it is doing, live in the status bar.
*   **How it works:** A background hook sends the current transcript to a fast model (Haiku or local LLM) with the prompt: *"Summarize exactly what the main agent is trying to do right now in 3 words."*
*   **The Display:**
    *   `🧠 Focus: Refactoring Auth`
    *   `🧠 Focus: STUCK / LOOPING` (This is the "killer" feature—catching loops early).
*   **The Reminder:** It reminds *you* what you asked it to do 20 minutes ago, preventing "scope creep" where you distract the agent with side tasks.

### 3. "Gamified" Context & Budget
Novel ideas that turn anxiety-inducing metrics (cost/context limits) into game mechanics.
*   **The "Mana Bar":** Instead of `Tokens: 140k/200k`, users render a video-game style health/mana bar.
    *   `CTX: [████████░░] (CRITICAL)`
    *   When it hits critical (red), users treat it like a "boss fight" phase where they must `/compact` to survive.
*   **The "Burn Rate" Speedometer:**
    *   `🔥 $0.50/min` (Visualizes how fast you are spending money *right now*).
    *   Surprising effect: It gamifies *efficiency*, encouraging users to write better prompts to lower the "burn rate."

### 4. The "Ghost in the Machine" (External World)
Connecting the statusline to things completely outside the terminal to remind users that the physical world exists.
*   **Bio-Feedback:**
    *   `⌚ BPM: 110 (Take a breath)` – Linked to an Apple Watch/Fitbit API. If the user is stressed (high heart rate), the statusline tells them to cool down before replying to a code review.
*   **The "Wife/Partner" API:**
    *   `🛑 HARD STOP: 5:00 PM (Date Night)` – A countdown that turns the entire bar bright red when personal obligations are approaching.

### 5. "Shadow Linter" (Asynchronous Validity)
Standard linters block the terminal. The "novel" approach is **asynchronous validity**.
*   **Idea:** A background process watches the file system. Every time Claude edits a file, the background process silently runs the test suite or type checker.
*   **Display:**
    *   `Types: ✅ | Tests: ⏳ (Running...)`
    *   `Types: ❌ (3 Errors)`
*   **Why it's novel:** It decouples the "check" from the "action." You don't have to wait for Claude to run tests; the statusline tells you *before* you even ask.

## Human

those are great!  Any more?

## Assistant

You asked for "novel" and "surprising" ideas. The community has moved far beyond simple "CPU/Memory" stats into territory that feels almost biological or like a video game.

Here are the most novel concepts people have implemented, ranging from "gamified productivity" to "agentic introspection."

### 1. The "Behavioral Tamagotchi" (The Viral Hit)
This is the one that surprised everyone. A developer (Ido-Levi) created a pixel-art pet in the statusline that isn't random—it reacts to **LLM behavior**.

*   **The Novelty:** It uses a cheap, fast model (like Llama 3 on Groq) running in the background to "audit" Claude's last output.
*   **The Surprise:** It works as a **behavioral reinforcement system**.
    *   **Happy Pet `(◕‿◕)`:** Claude followed the `PRD.md` and didn't delete any files.
    *   **Angry Pet `(ಠ_ಠ)`:** Claude hallucinated a library or tried to edit a file that doesn't exist.
    *   **Dead Pet `(✖╭╮✖)`:** You hit the context limit or the session crashed.
*   **Why people love it:** It gives you an emotional, instant read on "quality" without needing to read the logs. If the pet looks angry, you know you need to intervene before the agent destroys your codebase.

### 2. The "Context-Bricks" & "Mana Bar"
Instead of boring numbers (`145k/200k tokens`), users gamified the context window into a "Mana Bar" from an RPG.

*   **The Visual:** `CTX: [▓▓▓▓▓▓▓▓░░] (BOSS FIGHT SOON)`
*   **The Mechanic:**
    *   **Green:** Safe zone.
    *   **Yellow:** "Warning: The agent is becoming forgetful."
    *   **Red (Flashing):** "Boss Fight Mode." This indicates you have ~5 turns left before the context window fills and the agent "dies" (requires a `/compact` or reset).
*   **Surprising Upside:** Users reported it actually changed *their* behavior. Seeing the "Mana" drop made them write more concise prompts to "save mana," effectively training the user to be a better prompt engineer.

### 3. The "Fleet Monitor" (Perfect for your 5-terminal workflow)
Since you run multiple instances, this is a "God Mode" statusline.
*   **The Concept:** Instead of just showing *local* status, the statusline reads a shared JSON file (`/tmp/claude_fleet_state.json`) where every active instance writes its heartbeat.
*   **The Display:**
    *   `T1: 🔨 (Building)`
    *   `T2: 🟢 (Idle)`
    *   `T3: ❌ (ERROR - check terminal)`
*   **The Surprise:** You can see if a background agent has crashed or finished a long task without alt-tabbing through 5 windows. You essentially build a "Mission Control" center in the footer of your active terminal.

### 4. The "Shadow Linter" (Asynchronous Reality Check)
Standard linters block the terminal. This "Shadow" version runs asynchronously.
*   **How it works:** A filesystem watcher detects when Claude saves a file. It immediately runs `tsc --noEmit` or `eslint` in a *detached process*.
*   **The Display:**
    *   `TypeCheck: ⏳` (Thinking...)
    *   `TypeCheck: ✅` (Valid)
    *   `TypeCheck: 💥 5 Errors` (Invalid)
*   **The "Magic":** You see the error count *before* Claude even says "I'm done editing." You can interrupt it and say, "Stop, you broke the build," saving massive amounts of tokens and time.

### 5. The "Focus Mirror" (Anti-Drift)
Agents often get "distracted" or go down rabbit holes. This statusline forces them to admit what they are doing.
*   **The Mechanism:** A hook sends the last 3 user messages to a fast model and asks: *"Summarize the current goal in 3 words."*
*   **The Display:** `🎯 GOAL: Refactor Auth Middleware`
*   **The "Gotcha":** If the statusline suddenly changes to `🎯 GOAL: Debugging obscure CSS`, you immediately know the agent has lost the plot (scope creep) and you can steer it back.

### 6. The "Real World" Anchor
Finally, people use the statusline to remind them that the physical world exists.
*   **Bio-Feedback:** `💓 BPM: 105 (Stress High)` (Linked to Apple Watch/Fitbit). Reminds you to step away if you're getting heated at the AI.
*   **Spousal API:** `🛑 HARD STOP: 15m (Dinner)` – A countdown to personal obligations that turns the bar bright red, preventing the "just one more prompt" syndrome.

## Human

Sometimes claude code forget things, or starts to work on the wrong task or goal.  How do we detect that and put an emoji in the statusline?

## Assistant

Perfect. Now I can show you exactly how to build a "Drift Detection" system using hooks + statusline. This is **the pattern** people use to catch when Claude starts working on the wrong task.

***

## Architecture: Hook → State File → Statusline

The key insight: **Hooks run after Claude acts, but statusline runs every ~300ms.** So you can't do expensive LLM calls *in* the statusline. Instead:

1. **Hook (PostToolUse)** → Runs after Claude edits files. Calls a fast LLM (Haiku or Groq) to check: "Is Claude still on task?"
2. **State File** → Writes result to `/tmp/cc_drift_state.json`
3. **Statusline** → Reads that file instantly and displays an emoji

***

## Implementation

### Step 1: Create the Drift Detection Hook

Create a file at `~/.claude/hooks/drift_detector.py`:

```python
#!/usr/bin/env python3
"""
Drift Detection Hook
Monitors if Claude is staying on task or diverging.
Writes status to /tmp/cc_drift_state.json for statusline to read.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def load_transcript(transcript_path: str) -> dict:
    """Load the conversation transcript."""
    try:
        messages = []
        with open(transcript_path, 'r') as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    messages.append(msg)
                except:
                    pass
        return messages
    except:
        return []

def extract_goals_from_transcript(messages: list) -> str:
    """
    Extract the *original* user goal from the beginning of the conversation.
    This is what we check Claude against.
    """
    for msg in messages[:5]:  # Check first few messages
        if msg.get('role') == 'user' and msg.get('content'):
            # Return the first substantial user message
            content = msg['content']
            if len(content) > 20:  # Avoid tiny messages
                return content[:200]  # Summarize to first 200 chars
    return "No goal found"

def extract_recent_actions(messages: list) -> str:
    """Extract Claude's recent tool calls and actions."""
    recent = []
    for msg in messages[-10:]:  # Last 10 messages
        if msg.get('role') == 'assistant' and 'content' in msg:
            content = msg['content']
            if 'tool_use' in str(content):
                recent.append(str(content)[:100])
    return '\n'.join(recent[-3:]) if recent else "No recent actions"

def check_drift_with_fast_llm(goal: str, recent_actions: str) -> dict:
    """
    Call a fast, cheap LLM (Groq Llama) to check if Claude is drifting.
    This should be VERY fast (< 1 second).
    """
    import subprocess
    
    prompt = f"""You are a task drift detector. Analyze if Claude is still working on the original goal.

ORIGINAL GOAL: {goal}

RECENT ACTIONS: {recent_actions}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "on_task": true or false,
  "confidence": 0.0 to 1.0,
  "issue": "brief explanation if drifting"
}}

If you believe Claude is on task, set on_task=true.
If Claude seems to be working on something else, set on_task=false."""

    try:
        # Example: Using Groq via OpenAI-compatible API (very fast)
        # You can substitute with your preferred fast LLM
        result = subprocess.run(
            [
                'curl', '-s', 'https://api.groq.com/openai/v1/chat/completions',
                '-H', 'Content-Type: application/json',
                '-H', f'Authorization: Bearer {os.getenv("GROQ_API_KEY", "")}',
                '-d', json.dumps({
                    "model": "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.3
                })
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        response_json = json.loads(result.stdout)
        if 'choices' in response_json and response_json['choices']:
            content = response_json['choices'][0]['message']['content']
            # Extract JSON from response
            try:
                decision = json.loads(content)
                return decision
            except:
                return {"on_task": True, "confidence": 0.5, "issue": "parsing error"}
    except Exception as e:
        return {"on_task": True, "confidence": 0.5, "issue": f"LLM error: {str(e)[:30]}"}
    
    return {"on_task": True, "confidence": 0.0, "issue": "no response"}

def main():
    """Main hook logic."""
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
    except:
        # If stdin parsing fails, exit gracefully
        sys.exit(0)
    
    transcript_path = hook_input.get('transcript_path', '')
    if not transcript_path:
        sys.exit(0)
    
    # Load conversation history
    messages = load_transcript(transcript_path)
    if len(messages) < 3:
        # Not enough context yet
        sys.exit(0)
    
    # Extract goal and recent actions
    goal = extract_goals_from_transcript(messages)
    recent = extract_recent_actions(messages)
    
    # Check with fast LLM
    decision = check_drift_with_fast_llm(goal, recent)
    
    # Write to state file for statusline to read
    state = {
        "timestamp": datetime.now().isoformat(),
        "on_task": decision.get("on_task", True),
        "confidence": decision.get("confidence", 0.5),
        "issue": decision.get("issue", ""),
        "goal": goal[:50]  # Short version for display
    }
    
    try:
        with open('/tmp/cc_drift_state.json', 'w') as f:
            json.dump(state, f)
    except:
        pass  # Silently fail if we can't write
    
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### Step 2: Register the Hook in `~/.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/drift_detector.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Step 3: Create the Statusline Script

Create `~/.claude/statusline.sh`:

```bash
#!/bin/bash

# Default: No emoji
DRIFT_EMOJI=""
DRIFT_MSG=""

# Check if drift detection file exists
if [ -f /tmp/cc_drift_state.json ]; then
    # Read the state
    STATE=$(cat /tmp/cc_drift_state.json 2>/dev/null)
    
    ON_TASK=$(echo "$STATE" | jq -r '.on_task // true')
    CONFIDENCE=$(echo "$STATE" | jq -r '.confidence // 0')
    ISSUE=$(echo "$STATE" | jq -r '.issue // ""')
    
    # Only show alert if confidence is high
    if [ "$ON_TASK" == "false" ]; then
        if (( $(echo "$CONFIDENCE > 0.7" | bc -l) )); then
            DRIFT_EMOJI="⚠️"
            DRIFT_MSG="DRIFT DETECTED"
        fi
    fi
    
    # Show the issue if there is one
    if [ -n "$ISSUE" ]; then
        DRIFT_MSG="$DRIFT_EMOJI $ISSUE"
    fi
fi

echo "$DRIFT_MSG"
```

Make it executable:
```bash
chmod +x ~/.claude/statusline.sh
```

### Step 4: Register Statusline in `~/.claude/settings.json`

Add to your settings:

```json
{
  "statusline": "~/.claude/statusline.sh"
}
```

***

## How It Works

```
┌─────────────────────────────────────────────────┐
│ You: "Refactor the login form"                   │
│ Claude: Makes edits to auth.ts                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ PostToolUse Hook Fires (after Edit)              │
│ - Loads transcript                               │
│ - Extracts original goal: "Refactor login form"  │
│ - Reads recent actions: "Editing styles.css"    │
│ - Calls Groq LLM (fast, <1sec)                   │
│ - LLM says: "on_task: false, confidence: 0.85"  │
│ - Writes to /tmp/cc_drift_state.json             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ Statusline Script Runs Every 300ms               │
│ - Reads /tmp/cc_drift_state.json                 │
│ - on_task == false? YES                          │
│ - confidence > 0.7? YES                          │
│ - Output: "⚠️ Working on CSS instead of auth"    │
│ - Terminal footer updates instantly              │
└─────────────────────────────────────────────────┘
                      ↓
                 YOU SEE: ⚠️
              And interrupt Claude
```

***

## Customization Ideas

**Show different emojis based on confidence:**
```bash
if (( $(echo "$CONFIDENCE > 0.85" | bc -l) )); then
    DRIFT_EMOJI="🔴"  # High confidence drift
elif (( $(echo "$CONFIDENCE > 0.65" | bc -l) )); then
    DRIFT_EMOJI="🟡"  # Medium confidence drift
fi
```

**Use a fast local LLM instead of Groq:**
Replace the curl call with `ollama run llama2` or similar.

**Color the statusline when drifting:**
```bash
if [ "$ON_TASK" == "false" ]; then
    echo -e "\033[41m⚠️  DRIFT\033[0m"  # Red background
fi
```

**Track multiple goals (for multi-task sessions):**
Store an array of goals in a file and check against all of them.

***

This is the exact pattern people use for "autonomous drift detection" — it's non-blocking (the hook doesn't interrupt Claude), it's fast (cheap LLM calls), and it gives you instant visual feedback. The emoji appearing in your statusline is your "early warning system."

## Human

I asked CC what it kept forgetting, here's it's list:

● Summary: Top 10 Most Common Forgotten Items

  Based on analysis of 65 "did you forget" conversations across 500 recent sessions:

  | Rank | Category      | Count | Examples                                                       |
  |------|---------------|-------|----------------------------------------------------------------|
  | 1    | Verification  | 87    | Need to check API, validate assumptions, verify implementation |
  | 2    | Logging       | 46    | Missing logging, observability gaps                            |
  | 3    | Integration   | 36    | Broken integrations, missing connections                       |
  | 4    | Dependencies  | 25    | Import issues, missing dependencies                            |
  | 5    | Cleanup       | 24    | Temporary files not removed, cleanup not done                  |
  | 6    | Documentation | 18    | README not updated, docs missing                               |
  | 7    | Configuration | 11    | Hardcoded paths, no config file                                |
  | 8    | Tests         | 5     | Integration tests missing                                      |
  | 9    | Edge Cases    | 3     | Edge case handling                                             |
  | 10   | Other         | N/A   | Various smaller items                                          |

  Key Patterns:

  1. "Need to check/verify" - Most common - forgetting to validate assumptions
  2. "Missing X" - Features/integrations not implemented
  3. "Should have" - Post-completion realizations
  4. "Forgot to add/include" - Omissions discovered during review

  Note: The search also picks up some false positives from code snippets and documentation discussions. The actual top forgotten items are:

  1. Testing (unit tests, integration tests)
  2. Documentation (README, comments)
  3. Verification (checking that things work)
  4. Cleanup (removing temp files, commented code)
  5. Configuration (making things configurable instead of hardcoded)

How do people like to use hook, and/or statusline to address or notify them of these misses?

## Assistant

To solve these "top 10 forgotten items," you can use the **Hook-to-Statusline Pattern** we discussed. This transforms your statusline from a passive display into an active "Check Engine Light" for your project.

Here is the implementation guide for your top 3 misses: **Verification (Tests)**, **Documentation**, and **Cleanup**.

### 1. The "Broken Build" Light (Solves: Verification & Tests)
**The Problem:** Claude edits code but forgets to run tests, leaving you with a broken build.
**The Solution:** A "Shadow Tester" hook that runs tests *asynchronously* on modified files and updates the statusline.

**Step A: The Hook (`~/.claude/hooks/shadow_test.sh`)**
This hook triggers on `Edit/Write`, runs a fast test command (like `npm test` or `pytest`), and writes the result to a file. It does *not* block Claude.
```bash
#!/bin/bash
# Read input to get the file path
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

# Only run if it's a code file
if [[ $file_path =~ \.(ts|js|py)$ ]]; then
  # Write "RUNNING" state
  echo "RUNNING" > /tmp/cc_test_status

  # Run tests in background (detached)
  (
    # Example: Run tests related to this file (adjust for your repo)
    if npm test -- --findRelatedTests "$file_path" > /dev/null 2>&1; then
       echo "PASS" > /tmp/cc_test_status
    else
       echo "FAIL" > /tmp/cc_test_status
    fi
  ) &
fi
```

**Step B: The Statusline Integration**
Add this to your `statusline.sh`:
```bash
TEST_STATUS=$(cat /tmp/cc_test_status 2>/dev/null)
case "$TEST_STATUS" in
  "RUNNING") TEST_ICON="🧪 ⏳" ;;
  "FAIL")    TEST_ICON="🧪 ❌" ;;
  "PASS")    TEST_ICON="🧪 ✅" ;;
  *)         TEST_ICON="" ;;
esac
echo "$TEST_ICON ..."
```

### 2. The "Stale Docs" Detector (Solves: Documentation)
**The Problem:** Claude changes `src/auth.ts` but forgets to update `README.md` or `docs/api.md`.
**The Solution:** A simple timestamp comparator in the statusline.

**Step A: The Statusline Script (`~/.claude/statusline.sh`)**
No hook needed! The statusline runs every ~300ms, so it can just check timestamps directly.
```bash
# Check if source code is significantly newer than documentation
# Adjust paths ('src' and 'docs') to match your project
LATEST_SRC=$(find src -type f -exec stat -c %Y {} + | sort -rn | head -n1)
LATEST_DOC=$(find docs README.md -type f -exec stat -c %Y {} + | sort -rn | head -n1)

# If Code is > 30 mins newer than Docs
if [ $((LATEST_SRC - LATEST_DOC)) -gt 1800 ]; then
    DOC_MSG="⚠️ DOCS STALE"
fi

echo "$DOC_MSG ..."
```

### 3. The "Trash Can" Monitor (Solves: Cleanup)
**The Problem:** Claude leaves behind `temp_fix.py`, `debug.log`, or `test_script.js`.
**The Solution:** A hook that lists "untracked" files and warns you if they persist too long.

**Step A: The Statusline Script**
Check for untracked files that match specific "junk" patterns.
```bash
# Count untracked files that look temporary
JUNK_COUNT=$(git ls-files --others --exclude-standard | grep -E "temp|tmp|debug|test_" | wc -l)

if [ "$JUNK_COUNT" -gt 0 ]; then
    CLEANUP_MSG="🧹 $JUNK_COUNT Junk Files"
fi

echo "$CLEANUP_MSG ..."
```

### 4. The "Hardcoded Path" Blocker (Solves: Configuration)
**The Problem:** Claude writes `C:\Users\YourName\...` into the code.
**The Solution:** A **Blocking Hook** (PreToolUse) that refuses to let Claude save the file.

**Step A: The Hook (`~/.claude/hooks/block_paths.py`)**
```python
#!/usr/bin/env python3
import sys, json, re

# Read tool input
data = json.load(sys.stdin)
file_content = data.get('tool_input', {}).get('file_text', '')

# Regex for absolute Windows/Linux paths
if re.search(r'(?<!\/)[a-zA-Z]:\\[\\\w\s]+', file_content) or re.search(r'/home/[a-z]+/', file_content):
    print(json.dumps({
        "result": "block",
        "message": "❌ BLOCKED: Absolute path detected. Use relative paths or config variables."
    }))
    sys.exit(0)

# Pass if no issues
print(json.dumps({"result": "pass"}))
```

### Summary of "Forgot" Fixes

| Problem | Type | Fix | Statusline Visual |
| :--- | :--- | :--- | :--- |
| **Verification** | Async Hook | Run `pytest` on edit | `Tests: ❌` |
| **Docs** | Statusline | Compare `src` vs `docs` time | `⚠️ DOCS STALE` |
| **Cleanup** | Statusline | Count `git ls-files` (untracked) | `🧹 3 Junk Files` |
| **Config** | Blocking Hook | Regex for `C:\Users` | *(Blocks Action)* |
| **Logging** | Post Hook | Grep for `console.log` | `📝 No Logs Added` |

By implementing just the **Docs Stale** and **Tests** indicators, you cover ~40% of the most common errors without changing your workflow at all. You just glance down, see the warning, and tell Claude: *"Fix the docs."*
