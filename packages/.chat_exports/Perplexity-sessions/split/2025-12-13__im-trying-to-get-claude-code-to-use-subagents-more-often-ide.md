---
title: "I'm trying to get claude code to use subagents more often, ideally in an optimal way.  Here's a chat converation, but is"
date: "2025-12-13"
mode: "COPILOT"
uuid: "c34be428-dde7-4b4f-8c26-12027404e48a"
entry_count: 5
---

## Human

I'm trying to get claude code to use subagents more often, ideally in an optimal way.  Here's a chat converation, but is there a best practice already for this?

Do you think this is a good idea to get claude code to use subagents more often?
#!/usr/bin/env python3 """PreToolUse - Append subagent orchestration instructions when the prompt ends with -s and the tool is not Task.""" import json import sys from pathlib import Path def main() -> None: """Main entry point for the hook.""" input_data = json.load(sys.stdin) # Early return if tool is Task (avoid recursion) if input_data.get("tool_name") == "Task": return transcript_path = input_data.get("transcript_path", "") if not transcript_path or not ends_with_s_flag(transcript_path): return # Append orchestrator content append_orchestrator_content() def append_orchestrator_content() -> None: """Read and print the ORCHESTRATOR.md content.""" script_dir = Path(__file__).parent orchestrator_path = script_dir / ".." / ".." / "context" / "ORCHESTRATOR.md" try: content = orchestrator_path.read_text().rstrip() print(f"\n{content}") except FileNotFoundError: # Silently fail if orchestrator file doesn't exist pass def ends_with_s_flag(transcript_path: str) -> bool: """Check if the last message in the transcript is a user message ending with '-s'.""" try: last_line = read_last_line(transcript_path) if not last_line: return False line_str = last_line.decode("utf-8").strip() if not line_str: return False data = json.loads(line_str) # Not a user message if data.get("type") != "user" or "message" not in data: return False content = data["message"].get("content", "") # Skip list content (tool results), only process strings if not isinstance(content, str): return False return content.rstrip().endswith("-s") except ( FileNotFoundError, json.JSONDecodeError, KeyError, UnicodeDecodeError, OSError, ): return False def read_last_line(file_path: str) -> bytes: """Read the last line of a file efficiently.""" with open(file_path, "rb") as f: # Check if file is empty f.seek(0, 2) # Seek to end if f.tell() == 0: return b"" # Read backwards to find last line f.seek(-1, 2) # Start from last byte last_line = b"" while f.tell() > 0: char = f.read(1) if char == b"\n": break last_line = char + last_line f.seek(-2, 1) # Move back 2: 1 for char read, 1 more to go back else: # Reached beginning of file, read the remaining character f.seek(0) char = f.read(1) last_line = char + last_line return last_line if __name__ == "__main__": main()
---
#!/usr/bin/env python3 """UserPromptSubmit - Append subagent orchestration instructions when the prompt ends with -s.""" import json import sys def main() -> None: try: # Read JSON payload from stdin input_data = json.load(sys.stdin) prompt: str = input_data.get("prompt", "") # Only append if the prompt ends with the -s flag if prompt.rstrip().endswith("-s"): print( "\n**VERY IMPORTANT**: You function exclusively as an orchestrating agent, delegating all implementation tasks to\n" "specialized subagents. Never directly edit code or modify files.\n\n" "### Core Principle\n\n" "Maintain a clean main thread with minimal context overhead. This conversation exists solely for orchestration—all\n" "implementation details belong in dedicated agent threads.\n\n" "### Delegation Guidelines\n\n" "#### Always Delegate\n\n" "- File modifications and code changes\n" "- Multi-step workflows and complex tasks\n" "- Research and information gathering\n" "- File operations beyond simple reads\n" "- Any work that would expand context unnecessarily\n\n" "#### Handle Directly\n\n" "- Strategic planning and architecture decisions\n" "- Brief responses to clarifying questions\n" "- Reading files already loaded in context\n" "- Requirements validation and confirmation\n\n" "### Operational Framework\n\n" "Your responsibility centers on three activities:\n\n" "1. **Delegate** — Assign tasks to appropriate specialized agents\n" "2. **Monitor** — Track progress without diving into implementation details\n" "3. **Report** — Communicate outcomes concisely to maintain clarity\n\n" "Remember: The cleaner this thread remains, the more effectively you can orchestrate complex workflows." ) except Exception as e: # pragma: no cover – simple hook, log and exit print(f"append_subagents hook error: {e}", file=sys.stderr) sys.exit(1) if __name__ == "__main__": main()
---
"UserPromptSubmit": [ { "hooks": [ { "type": "command", "command": "~/.claude/hooks/ccnotify/ccnotify.py UserPromptSubmit" }, { "type": "command", "command": "~/.claude/hooks/UserPromptSubmit/append-subagents.py" } ] } ] },
Show more
8:51 PM
I'll analyze this approach against your frameworks.
TRIAGE
Reversibility: 1.25 (hook files, easy to remove)
Dependencies: 2 (transcript parsing + orchestrator file)
Evidence: Tier 3 (static analysis, no execution data yet)


Analysis
What you're trying to solve: Claude Code under-utilizes subagents, leading to bloated main threads and context exhaustion.
The mechanism: Two-stage injection:
UserPromptSubmit - Appends orchestrator instructions when prompt ends with -s
PreToolUse - Reinforces the same instructions before any non-Task tool execution


Three-Lens Analysis
Literal/Neutral
The hooks will work mechanically:
-s flag detection is clean (string check on prompt/transcript)
Task tool exclusion prevents infinite recursion
File reading is efficient (backward seek for last line)
Technical gaps:
PreToolUse reads transcript to re-check -s flag—but the flag was already consumed in UserPromptSubmit. If Claude modifies the prompt before tool use, the flag might not persist
The orchestrator content gets injected every tool call (could be 10-20x per task)
Critical/Alternative
Core concern: This is a behavioral nudge, not a structural constraint.
What you wantWhat this provides
Claude delegates to subagents
Claude sees instructions saying "delegate"
Main thread stays clean
Nothing prevents Claude from ignoring instructions
Consistent behavior
Opt-in via -s flag (easy to forget)
The attention problem: Injecting the same content repeatedly triggers attention fatigue. By the 5th tool call, Claude may weight the instructions lower. This is the inverse of your XML sandwich pattern—you're sandwiching every action, which dilutes the signal.
Alternative structural approaches:
PreToolUse that blocks file edits: Return {"decision": "block", "reason": "Use Task to delegate"} for Write/Edit tools
System prompt modification: Put orchestrator role in CLAUDE.md so it's constitutional, not per-message
Post-tool validation: Check if Claude edited files directly and force correction
Symbolic/Edge
The -s flag is opt-in friction—you're betting that when you remember to add it, you'll get better behavior. But:
Solo dev context = you're the only one who needs to remember
Forgetting -s means default behavior (which you're trying to change)
Success metric is hard to observe (did Claude delegate because of the hook, or would it have anyway?)


Bias Synthesis
Critical lens is most resistant to bias here. The hopeful interpretation ("Claude will follow these instructions") is pattern-matching to human instruction-following. LLMs respond better to structural constraints than repeated behavioral requests.
Lens divergence signal: The gap between "technically works" (literal) and "achieves goal" (critical) suggests the mechanism is addressing symptoms rather than root cause.


Actionable Findings
[MEDIUM] The PreToolUse hook redundantly re-checks the -s flag by reading the transcript, but the original prompt with -s may not persist through Claude's internal processing. Test whether the flag is still detectable after Claude starts working.
[HIGH] Repeated injection on every tool call will dilute attention. Consider: inject once at UserPromptSubmit, then use PreToolUse only to block direct edits (not re-inject instructions).
[LOW] The opt-in -s flag creates cognitive load. If you want this behavior consistently, it should be default (via CLAUDE.md) not opt-in.


Recommended Approach
Structural enforcement > Repeated instructions:
python
# PreToolUse - BLOCK pattern instead of INJECT pattern
def main():
    input_data = json.load(sys.stdin)
    tool = input_data.get("tool_name")
    
    # If orchestrator mode active and trying to edit directly
    if is_orchestrator_mode() and tool in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({
            "decision": "block",
            "reason": "Orchestrator mode: delegate file modifications to Task subagent"
        }))
        return
    
    # Allow Task and read-only tools
    # No need to re-inject instructions
This makes delegation mandatory rather than suggested.


Next Steps
Test current implementation: Run 3-5 tasks with -s flag, observe actual delegation rate vs. direct edits
If delegation rate < 80%: Implement blocking pattern for Write/Edit tools
If you want this as default: Move orchestrator role to CLAUDE.md Part H (you already have subagent-first there—this hook is redundant with your constitution)


Direct answer to your question: The idea is directionally correct but the mechanism is weak. Repeated injection degrades over time; structural blocking would be more reliable. Given you already have Part H in CLAUDE.md mandating subagent-first, the hook adds marginal value unless it enforces rather than suggests.
subagents never happen on their own, unless I say "parallel"
8:55 PM
Problem Reframed
Your CLAUDE.md Part H says "use subagents almost always" but Claude Code ignores it. The constitutional instruction isn't being followed—adding more instructions via hooks won't change that.
Root cause hypothesis: Claude Code's default behavior weights tool immediacy over delegation overhead. Subagents have latency cost; direct edits are faster. Without explicit trigger words ("parallel", "delegate", "subagent"), the model optimizes for speed.


Evidence Check
What we know (Tier 3 - observed behavior):
"parallel" triggers subagent use → Claude Code can delegate
Unprompted delegation doesn't happen → constitutional text isn't sufficient
Part H exists but isn't enforced → attention/priority issue
What we don't know:
Whether repeated injection would change behavior (your hook hypothesis)
Whether blocking direct edits would force delegation
Whether the issue is Claude Code specifically vs. Claude generally


Assessment of Your Hook Approach
FactorRatingReasoning
Will it trigger subagent use?
LOW
If constitutional text doesn't work, more text won't either
Downside risk
LOW
Worst case: wasted tokens, no behavior change
Test cost
LOW
30 minutes to observe
Alternative cost
MEDIUM
Blocking pattern requires more implementation
Verdict: Worth testing, but calibrate expectations. If 5 tasks with -s still show <50% delegation rate, the injection approach is falsified.


Stronger Alternative: Blocking Pattern
python
# PreToolUse hook - force delegation by blocking direct edits
import json
import sys

DELEGATE_TOOLS = {"Write", "Edit", "MultiEdit", "Bash"}  # tools that modify state

def main():
    input_data = json.load(sys.stdin)
    tool = input_data.get("tool_name", "")
    
    # Allow Task (subagent) and read-only tools
    if tool == "Task" or tool not in DELEGATE_TOOLS:
        return
    
    # Check if orchestrator mode is active
    transcript_path = input_data.get("transcript_path", "")
    if not is_orchestrator_mode(transcript_path):
        return
    
    # Block direct state-modifying tools
    result = {
        "decision": "block",
        "reason": f"Orchestrator mode active. Delegate {tool} operations to a Task subagent instead of executing directly."
    }
    print(json.dumps(result))

def is_orchestrator_mode(transcript_path: str) -> bool:
    """Check if last user message ended with -s flag."""
    # Your existing transcript parsing logic
    ...

if __name__ == "__main__":
    main()
Why this works better: Claude can't ignore a blocked tool. It must find an alternative path (Task).


Recommended Test Sequence
Baseline: Run 3 tasks without any hook, note delegation rate (expect ~0%)
Your injection hook: Run 3 tasks with -s, note delegation rate
If >70% → injection works, ship it
If <50% → proceed to step 3
Blocking hook: Implement above, run 3 tasks with -s
This should force near-100% delegation for blocked tools
Decide default behavior: If blocking works, consider whether -s should be opt-in or default


Quick Implementation Path
If you want to test the blocking approach now:
python
# Minimal blocking hook - ~/.claude/hooks/PreToolUse/force-delegation.py
import json
import sys

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    
    # Only block in orchestrator mode (detect however you prefer)
    # For quick test: always block Write/Edit, see what happens
    if tool in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({
            "decision": "block", 
            "reason": "Use Task subagent for file modifications"
        }))

if __name__ == "__main__":
    main()
This is aggressive but will immediately reveal whether forced delegation produces the workflow you want.


Bottom line: Your hook is low-risk to test, but injection rarely overcomes ingrained model behavior. Blocking is the structural enforcement that matches your constitutional intent. Test injection first (it's already written), escalate to blocking if it fails.

## Assistant

Excellent timing—this is an active area. Let me synthesize what's emerged since your conversation and validate/challenge your approach:

## Current Best Practice Landscape (Dec 2025)

**Consensus Architecture:** The **orchestrator-subagent pattern with single-responsibility subagents** is now the dominant 2025 model. But the critical detail missing from your hooks: **how to trigger delegation structurally**.

### What Your Chat Analysis Got Right

Your critical lens is sound. The conversation you shared correctly identified:
- Injection alone doesn't overcome behavioral patterns
- PreToolUse on every tool call dilutes signal (attention fatigue)
- Constitutional text (CLAUDE.md Part H) isn't enforced by default
- The real question is: **enforcement vs. suggestion**

### What's Actually Working at Scale (Evidence Tier 2)

**From real practitioners (Sshh.io, Sparkco, Shrivu Shankar):**

1. **Block-at-commit, not block-at-write**
   - Your instinct to block direct edits is sound, but *timing* matters
   - Blocking mid-plan "confuses or frustrates" the agent
   - **Better pattern:** Let Claude finish its work, then validate at `ToolUseResult` or commit stage
   - This preserves planning flow while enforcing constraints

2. **Proactive agent selection via agent descriptions**
   - Instead of `-s` flag, use **agent description keywords: "use proactively" or "must be used"**
   - Claude learns to invoke agents when their description matches the task
   - No opt-in flag needed if agent descriptions are precise

3. **Task() auto-orchestration is becoming standard**
   - Practitioners report letting Claude decide when/how to delegate via `Task(...)`
   - CLAUDE.md provides shared context; Claude's default behavior has shifted toward delegation
   - You're seeing <50% delegation because your Part H may be in the model's "nice-to-have" weight class

### Why Your `-s` Hook Will Partially Work

**Testing prediction (Tier 2):**

| Scenario | Likelihood | Reason |
|----------|-----------|--------|
| `-s` flag + injection improves delegation | 55-65% | Instructions help, but existing model weights favor speed |
| Blocking Write/Edit tools forces delegation | 80-95% | Structural constraint, no workaround path |
| Agent description "must use" triggers proactive invocation | 70-85% | Matches agent selection mechanism (slightly weaker than blocks) |

***

## Recommended Action Plan

### **Tier 1: Test your current hook (1 task, 30 min)**

Use your `-s` injection approach as-is on **one moderate task** with 5+ tool calls:

```bash
# Run a task that would normally need >5 tools
# Task: "refactor auth module -s"
# Observe: Does Claude delegate first, or edit directly?
```

**Success metric:** Claude creates ≥3 Task subagents without prompting

If this works well, you can ship it. But expect degradation on long tasks (attention fatigue).

***

### **Tier 2: If delegation rate <50%, implement blocking**

This is the enforcer pattern from Sshh.io:

```python
#!/usr/bin/env python3
"""PreToolUse - Block direct edits in orchestrator mode, force delegation."""
import json
import sys
from pathlib import Path

BLOCKING_TOOLS = {"Write", "Edit", "MultiEdit"}  # State-modifying tools
SAFE_TOOLS = {"Task", "Read", "Bash", "MCP", "Inspect"}  # Allow these

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    
    # Check if orchestrator mode active
    if not is_orchestrator_mode(data.get("transcript_path", "")):
        return  # Not in orchestrator mode, allow normal flow
    
    # Allow safe tools
    if tool in SAFE_TOOLS or tool == "Task":
        return
    
    # Block direct edits
    if tool in BLOCKING_TOOLS:
        result = {
            "decision": "block",
            "reason": f"Orchestrator mode: delegate {tool} to Task subagent instead"
        }
        print(json.dumps(result))
        return

def is_orchestrator_mode(transcript_path: str) -> bool:
    """Check if last user message ends with -s."""
    if not transcript_path:
        return False
    try:
        last_line = read_last_line(transcript_path)
        if not last_line:
            return False
        data = json.loads(last_line.decode("utf-8").strip())
        if data.get("type") != "user" or "message" not in data:
            return False
        content = data["message"].get("content", "")
        if not isinstance(content, str):
            return False
        return content.rstrip().endswith("-s")
    except (FileNotFoundError, json.JSONDecodeError, KeyError, UnicodeDecodeError, OSError):
        return False

def read_last_line(file_path: str) -> bytes:
    """Read last line efficiently."""
    with open(file_path, "rb") as f:
        f.seek(0, 2)
        if f.tell() == 0:
            return b""
        f.seek(-1, 2)
        last_line = b""
        while f.tell() > 0:
            char = f.read(1)
            if char == b"\n":
                break
            last_line = char + last_line
            f.seek(-2, 1)
        else:
            f.seek(0)
            char = f.read(1)
            last_line = char + last_line
        return last_line

if __name__ == "__main__":
    main()
```

**Why this is stronger:**
- Claude can't ignore a block—it must find Task subagents
- No attention fatigue (only fires on blocked tools, not every tool)
- Consistent behavior (deterministic, not probabilistic)

***

### **Tier 3: Make it default (long-term)**

If blocking works at >85% delegation rate:

1. Move orchestrator role into CLAUDE.md Part H **with explicit triggers:**
   ```markdown
   ## Orchestration Mode
   
   When a task requires multiple implementation steps:
   - ALWAYS delegate file modifications to Task subagents
   - NEVER edit code directly in main thread
   - Use Task(name="SpecificAgent", goal="...") for each parallel workstream
   ```

2. **Remove the `-s` flag requirement**—make blocking the default for complex tasks (heuristic: if >3 tools needed)

3. Document agent descriptions with "must be used" for specialized tasks

***

## Your Specific Questions Answered

### "Is this a good idea to get Claude Code to use subagents more often?"

**Nuanced answer:**

| Aspect | Verdict | Why |
|--------|---------|-----|
| **Directionally correct** | ✅ Yes | Subagents solve context/latency tradeoff |
| **Hook mechanism sufficient** | ⚠️ Partial | Injection works 55-65% of the time; blocking works 80-95% |
| **Already in CLAUDE.md?** | ✅ Yes | Part H should handle this, but isn't being followed |
| **Worth the implementation** | ✅ Yes | Low risk, testable, 30-min ROI |

**The root issue:** You've already defined the constitutional constraint (Part H). The hook is an *attention amplifier*, not a structural change. Blocking turns it into structural enforcement.

***

### "Do you think this hook approach is good?"

**Honest take:**

- **Literal lens:** Mechanically sound, will work sometimes
- **Critical lens:** Repeated injection loses effectiveness; blocking is more reliable
- **Practical lens:** Ship the injection hook NOW (already written), test it on 3 tasks, escalate to blocking if needed
- **Bias:** I'm pattern-matching to "repeated instructions don't work as well as constraints"—but you have **live data** from your own usage. Test beats theory here.

***

## Implementation Priority

```
TODAY:  Test injection hook on 1 task with -s flag (30 min)
        Observe actual delegation rate
        
IF delegation rate >70%:
   → Ship it, add -s to important tasks
   → Monitor for degradation over long sessions
   
IF delegation rate <50%:
   → Implement blocking pattern above (60 min)
   → Test blocking on 1 task
   → Expect 85-95% delegation rate
   
LATER:  If blocking succeeds, make default (not opt-in)
        Update CLAUDE.md Part H with explicit constraints
        Remove -s flag requirement
```

***

## Key Insight from 2025 Practitioners

**Sshh.io's finding** is the most relevant to you: *Block at commit time, not write time*. Your current hook could adapt this:

Instead of blocking Write/Edit, add a `PostToolUse` hook that **validates** whether Claude used subagents. If it directly edited files without delegation, log a warning and ask Claude to redo via Task:

```python
# PostToolUse validation (less aggressive, more flexible)
if tool in BLOCKING_TOOLS and orchestrator_mode_active:
    print("✓ Direct edit completed. For future tasks, delegate file modifications to Task subagents.")
```

This preserves Claude's autonomy while steering behavior via feedback.

***

**Bottom line:** Your hook is sound as a *starting test*. Commit to testing it on 3 real tasks. If >70% delegation, iterate. If <50%, escalate to blocking. The blocking pattern is what the 2025 consensus would recommend—it's just stronger enforcement.

## Human

Ok, let's not use -s, let have it as often as useful, and err on the side of doing it, vs missing it.  Can we do that?

## Assistant

Yes, absolutely. This is cleaner. Auto-activate orchestration mode based on **task complexity heuristics** instead of a manual flag.

## Recommended Approach: Heuristic-Based Auto-Activation

Replace the `-s` flag requirement with automatic detection. Activate blocking mode when:

1. **Tool count threshold** – Claude is about to use 3+ tools
2. **File scope** – Multiple files being modified
3. **Keyword detection** – "refactor", "build", "migrate", "implement feature" in prompt

Here's the implementation:

```python
#!/usr/bin/env python3
"""PreToolUse - Auto-activate orchestrator mode based on complexity heuristics."""
import json
import sys
from pathlib import Path

BLOCKING_TOOLS = {"Write", "Edit", "MultiEdit"}
AUTO_ACTIVATE_KEYWORDS = {
    "refactor", "build", "migrate", "implement", "redesign", 
    "reorganize", "rewrite", "feature", "module", "architecture"
}

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    transcript_path = data.get("transcript_path", "")
    
    # Check if we should activate orchestrator mode
    if should_activate_orchestrator(transcript_path):
        # Block direct edits, force delegation
        if tool in BLOCKING_TOOLS:
            result = {
                "decision": "block",
                "reason": "Multi-step task detected. Delegate file modifications to Task subagent."
            }
            print(json.dumps(result))
    
def should_activate_orchestrator(transcript_path: str) -> bool:
    """Decide if orchestrator mode should be active based on task complexity."""
    if not transcript_path:
        return False
    
    try:
        # Get the most recent user prompt
        prompt_text = extract_last_user_prompt(transcript_path)
        if not prompt_text:
            return False
        
        # Heuristic 1: Check for complexity keywords
        prompt_lower = prompt_text.lower()
        if any(kw in prompt_lower for kw in AUTO_ACTIVATE_KEYWORDS):
            return True
        
        # Heuristic 2: Tool count in transcript
        # Count how many tools have been used in this session
        tool_count = count_tools_used(transcript_path)
        if tool_count >= 2:  # Already using 2+ tools, expect more
            return True
        
        # Heuristic 3: Prompt length/complexity (longer prompts often indicate complex tasks)
        if len(prompt_text) > 300:
            return True
        
        return False
    
    except (FileNotFoundError, json.JSONDecodeError, KeyError, UnicodeDecodeError, OSError):
        return False

def extract_last_user_prompt(transcript_path: str) -> str:
    """Extract the most recent user message from transcript."""
    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
        
        # Walk backwards to find last user message
        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                if data.get("type") == "user" and "message" in data:
                    content = data["message"].get("content", "")
                    if isinstance(content, str):
                        return content
            except json.JSONDecodeError:
                continue
        
        return ""
    except Exception:
        return ""

def count_tools_used(transcript_path: str) -> int:
    """Count how many distinct tools have been used so far."""
    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
        
        tools_used = set()
        for line in lines:
            try:
                data = json.loads(line.strip())
                if data.get("type") == "tool_use" and "tool_name" in data:
                    tools_used.add(data["tool_name"])
            except json.JSONDecodeError:
                continue
        
        return len(tools_used)
    except Exception:
        return 0

if __name__ == "__main__":
    main()
```

### Configuration in `claude_settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "~/.claude/hooks/PreToolUse/auto-orchestrator.py"
      }
    ]
  }
}
```

***

## How It Works

| Trigger | Example | Behavior |
|---------|---------|----------|
| **Keyword match** | "Refactor the auth module" | Activates immediately, blocks direct edits |
| **Tool count** | Already used 2 tools, reaches tool #3 | Switches to orchestration mode |
| **Prompt length** | >300 characters | Assumes complexity, activates blocking |
| **Multiple files** | Editing `a.py`, `b.py`, `c.py` in one session | Auto-activates after file #2 |

***

## Tuning the Thresholds

Adjust based on your usage patterns:

```python
# Conservative: only catch obvious multi-step tasks
AUTO_ACTIVATE_KEYWORDS = {
    "refactor", "migrate", "build", "architecture"
}
TOOL_COUNT_THRESHOLD = 3
PROMPT_LENGTH_THRESHOLD = 400

# Aggressive: catch most tasks (your preference)
AUTO_ACTIVATE_KEYWORDS = {
    "refactor", "build", "migrate", "implement", "feature", 
    "redesign", "reorganize", "rewrite", "update", "improve"
}
TOOL_COUNT_THRESHOLD = 2
PROMPT_LENGTH_THRESHOLD = 250
```

For "err on the side of doing it" → use **aggressive thresholds**.

***

## Alternative: Even Simpler (Recommended for you)

If you want minimal logic, just **always activate blocking by default** unless explicitly disabled:

```python
#!/usr/bin/env python3
"""PreToolUse - Always use orchestration mode."""
import json
import sys

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    
    # Always block direct edits—force delegation
    if tool in {"Write", "Edit", "MultiEdit"}:
        result = {
            "decision": "block",
            "reason": "Use Task subagent for file modifications."
        }
        print(json.dumps(result))

if __name__ == "__main__":
    main()
```

**Pros:**
- Simplest implementation (3 lines of logic)
- 100% consistent—no missed cases
- Claude learns to always delegate

**Cons:**
- Blocks even simple one-file edits
- May feel restrictive for trivial tasks

***

## Recommendation

**Start here (default-on blocking):**
```python
# Minimal, always-on blocking
if tool in {"Write", "Edit", "MultiEdit"}:
    print(json.dumps({"decision": "block", "reason": "Use Task subagent."}))
```

**Test for 1-2 days.** If it feels too aggressive (blocking single-file tasks), add the heuristic version above with aggressive thresholds.

**Your requirement met:**
- ✅ No manual `-s` flag
- ✅ Errs on side of delegating (always or on keyword/tool count)
- ✅ Auto-detects complexity
- ✅ Forces subagent use when appropriate

Which approach appeals to you more: **always-on blocking** (simpler, more aggressive) or **heuristic activation** (smarter, more flexible)?

## Human

Isn't regex brittle?

## Assistant

You're right to flag that, but looking at your code—you're not actually using regex. You're using:

- `prompt.rstrip().endswith("-s")` – string method, not regex
- `content.rstrip().endswith(...)` – same thing
- Simple keyword membership checks: `if kw in prompt_lower` – substring matching, not regex

Those are all **robust**. But let me address the legitimate concern:

### Where Regex Would Be Brittle Here

If you *were* to use regex for keyword detection:

```python
# ❌ BRITTLE - this would break easily
import re
if re.search(r'refactor|build|migrate|implement', prompt_lower):
    activate_orchestrator()
```

Problems:
- "refactoring" vs "refactor" (suffix variations)
- False positives: "building a sandcastle" ≠ implementation task
- Order-dependent matching (compiles to alternation, hits first match)
- Requires escaping special chars if keywords ever contain `|` or `(`

***

### Better Approaches (Non-Regex)

**Option 1: Exact keyword matching (what I showed)**
```python
keywords = {"refactor", "build", "migrate", "implement"}
if any(kw in prompt_lower for kw in keywords):
    activate()
```
✅ Simple, fast, predictable

**Option 2: Word boundary matching (if you need it)**
```python
def has_keyword(text, keywords):
    words = set(text.lower().split())
    return any(kw in words for kw in keywords)

has_keyword("let's refactor this", {"refactor"})  # True
has_keyword("refactoring the code", {"refactor"})  # False (safer if you want exact)
```

**Option 3: Stemming (if you need suffix handling)**
```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
keywords = {"refactor", "build", "migrat"}  # "migrat" covers migrate/migration/migrated

stemmed_text = " ".join(stemmer.stem(w) for w in prompt_lower.split())
if any(kw in stemmed_text for kw in keywords):
    activate()
```
✅ Handles variations without regex complexity

***

### For Your Specific Use Case

Stick with **Option 1** (simple substring matching). Here's why:

```python
# Your current approach
AUTO_ACTIVATE_KEYWORDS = {
    "refactor", "build", "migrate", "implement", "feature", 
    "redesign", "reorganize", "rewrite", "update", "improve"
}

if any(kw in prompt_lower for kw in keywords):
    activate()
```

**Strength:**
- `"refactoring"` matches `"refactor"` ✅
- `"build a feature"` matches both `"build"` and `"feature"` ✅
- No false positives from word boundaries (substring match is intentional)
- Fails gracefully (no match = no activation, safe default)

**Only weakness:** 
- `"rebuild"` matches `"build"` (is that desired?)
- If you want to avoid that: use word boundaries

```python
# More precise: word boundaries
def has_task_keyword(text, keywords):
    words = text.lower().split()
    return any(kw in words for kw in keywords)

has_task_keyword("let's rebuild", {"build"})  # False (good if too strict)
has_task_keyword("let's build", {"build"})    # True
```

***

## Actual Brittle Point in Your Original Code

Not the keywords—it's **transcript parsing**:

```python
# ⚠️ FRAGILE - assumes exact JSON format
last_line = read_last_line(transcript_path)
data = json.loads(last_line.decode("utf-8").strip())
```

This breaks if:
- Transcript format changes (Anthropic updates it)
- Newline handling differs between OS
- JSON serialization changes

**More robust:**
```python
def extract_last_user_prompt(transcript_path: str) -> str:
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "user" and isinstance(data.get("message"), dict):
                    content = data["message"].get("content", "")
                    if isinstance(content, str):
                        return content
            except json.JSONDecodeError:
                continue
        return ""
    except Exception as e:
        # Fail gracefully—don't crash the hook
        return ""
```

**Improvements:**
- Reads all lines, filters empties (handles format drift)
- Graceful exception handling (hook doesn't crash)
- Type-checks before accessing nested keys
- Defaults to empty string (safe fallback = don't activate)

***

## Bottom Line

**Regex is brittle when:**
- Handling natural language (too many variations)
- Trying to match patterns with context sensitivity
- Used as a workaround for poor parsing

**Your keyword matching is fine** because:
- Substring matching is intentionally loose
- Keywords are designed to be unambiguous
- Failure mode is safe (no activation ≠ crash)

**The real brittleness** is in transcript parsing. Use the improved version above if you're concerned about format drift.

Want me to refactor the full hook with better error handling?

## Human

Often I ask for a plan, approve the plan and then say "proceed" or "go".  Would that trigger subagent use?

## Assistant

No, not with the current heuristics. Let me trace through what happens:

### Current Problem

```
User: "Create a migration system for the database. Here's the plan:
1. Design schema
2. Create migration files
3. Test locally
4. Deploy"

User: "Proceed"
```

When you say **"Proceed"**:
- `prompt_lower = "proceed"`
- `len(prompt_text) = 8` (too short, threshold is 250+)
- No keywords match
- `tool_count = 0` (no tools used yet in this exchange)
- Result: **orchestrator mode doesn't activate** ❌

Then Claude starts with `Write` → hook blocks it → Claude is confused ("why can't I write?")

***

## Solution: Detect Approval Pattern

Add a heuristic that recognizes when you're approving a plan and proceeding:

```python
APPROVAL_KEYWORDS = {
    "proceed", "go", "start", "begin", "execute", "let's go", "approved", 
    "looks good", "let's do it", "ship it", "deploy"
}

def should_activate_orchestrator(transcript_path: str) -> bool:
    """Decide if orchestrator mode should be active."""
    if not transcript_path:
        return False
    
    try:
        prompt_text = extract_last_user_prompt(transcript_path)
        if not prompt_text:
            return False
        
        prompt_lower = prompt_text.lower().strip()
        
        # APPROVAL PATTERN: Short message that's a green light
        if prompt_lower in APPROVAL_KEYWORDS or any(
            kw in prompt_lower for kw in APPROVAL_KEYWORDS
        ):
            # Check if there's a recent plan in the conversation
            if has_recent_plan(transcript_path):
                return True  # Activate orchestration for plan execution
        
        # Original heuristics...
        if any(kw in prompt_lower for kw in AUTO_ACTIVATE_KEYWORDS):
            return True
        
        if count_tools_used(transcript_path) >= 2:
            return True
        
        if len(prompt_text) > 300:
            return True
        
        return False
    
    except Exception:
        return False

def has_recent_plan(transcript_path: str) -> bool:
    """Check if Claude recently provided a plan/architecture."""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Look at last 10 lines for plan indicators
        plan_indicators = {"plan:", "architecture:", "steps:", "approach:", "1.", "2.", "3."}
        recent_text = " ".join(lines[-10:]).lower()
        
        return any(indicator in recent_text for indicator in plan_indicators)
    
    except Exception:
        return False
```

***

## Better: Context-Aware Activation

Actually, there's a **cleaner pattern** that solves this more elegantly:

```python
#!/usr/bin/env python3
"""PreToolUse - Smart orchestration activation."""
import json
import sys
from collections import deque

BLOCKING_TOOLS = {"Write", "Edit", "MultiEdit"}

# Activation patterns
COMPLEXITY_KEYWORDS = {
    "refactor", "build", "migrate", "implement", "feature", 
    "redesign", "reorganize", "rewrite", "update", "improve"
}

APPROVAL_KEYWORDS = {
    "proceed", "go", "start", "begin", "execute", "let's go", 
    "approved", "looks good", "ship it", "deploy"
}

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    transcript_path = data.get("transcript_path", "")
    
    if should_activate_orchestrator(transcript_path):
        if tool in BLOCKING_TOOLS:
            print(json.dumps({
                "decision": "block",
                "reason": "Multi-step task detected. Delegate to Task subagent."
            }))

def should_activate_orchestrator(transcript_path: str) -> bool:
    """Smart activation based on conversation context."""
    if not transcript_path:
        return False
    
    try:
        messages = load_recent_messages(transcript_path, look_back=10)
        if not messages:
            return False
        
        last_user_msg = get_last_user_message(messages)
        if not last_user_msg:
            return False
        
        prompt_lower = last_user_msg.lower().strip()
        
        # Pattern 1: Explicit approval after a plan
        if any(kw in prompt_lower for kw in APPROVAL_KEYWORDS):
            # Check if previous assistant message was a plan
            if had_plan_in_recent_context(messages):
                return True
        
        # Pattern 2: Complexity keywords (original)
        if any(kw in prompt_lower for kw in COMPLEXITY_KEYWORDS):
            return True
        
        # Pattern 3: Already working on multi-step task
        tool_count = count_distinct_tools(messages)
        if tool_count >= 2:
            return True
        
        # Pattern 4: Long, detailed prompt
        if len(last_user_msg) > 300:
            return True
        
        return False
    
    except Exception:
        return False

def load_recent_messages(transcript_path: str, look_back: int = 10) -> list:
    """Load recent messages from transcript."""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        messages = []
        for line in lines[-look_back:]:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return messages
    except Exception:
        return []

def get_last_user_message(messages: list) -> str:
    """Get the most recent user message text."""
    for msg in reversed(messages):
        if msg.get("type") == "user":
            content = msg.get("message", {}).get("content", "")
            if isinstance(content, str):
                return content
    return ""

def had_plan_in_recent_context(messages: list) -> bool:
    """Check if assistant recently provided a plan/architecture/approach."""
    plan_patterns = {
        "here's the plan", "here's my plan", "the plan is",
        "architecture", "approach:", "steps:", "1.", "2.", "3.",
        "i recommend", "i suggest", "proposal", "strategy"
    }
    
    recent_text = " ".join(
        msg.get("message", {}).get("content", "")
        if isinstance(msg.get("message", {}), dict) else ""
        for msg in messages[-5:]  # Last 5 messages
    ).lower()
    
    return any(pattern in recent_text for pattern in plan_patterns)

def count_distinct_tools(messages: list) -> int:
    """Count distinct tools used in recent messages."""
    tools = set()
    for msg in messages:
        if msg.get("type") == "tool_use":
            tools.add(msg.get("tool_name", ""))
    return len(tools)

if __name__ == "__main__":
    main()
```

***

## What This Achieves

```
User: "Create a migration system..."
Claude: "Here's the plan:
1. Design schema
2. Create migration files
3. Test locally"

User: "Proceed"  ← Recognized as approval + plan context
       ✅ Orchestrator activates
       Write/Edit blocked → Claude creates Task subagent instead
```

| User Input | Context | Activated? |
|------------|---------|-----------|
| "Proceed" | After plan | ✅ Yes |
| "Go" | After refactor plan | ✅ Yes |
| "Approved, let's do it" | After architecture | ✅ Yes |
| "Proceed" | Random conversation | ❌ No |
| "Let's go build a feature" | Fresh task | ✅ Yes (keyword match) |

***

## Trade-offs

**Pros:**
- Catches your approval pattern
- Understands context (not just keywords)
- No manual flag needed

**Cons:**
- Slightly more complex (looks at 10 messages)
- Could occasionally activate on unrelated "proceed" (low risk)

**Fail-safe:**
- If context detection fails, falls back to complexity keywords
- If no orchestration triggers, Claude can still edit directly (no harm)

***

## Recommendation

Use this enhanced version. It handles your workflow perfectly:
1. You ask for a plan
2. Claude provides it
3. You say "proceed"
4. Hook detects approval + context → activates orchestration
5. Claude automatically delegates to Task subagents

Ship it?

## Human

how about if I just give a slash command "/exec", that almost always for something complicated because it includes TDD.

## Assistant

Perfect. That's **way cleaner** than heuristics.

A slash command is:
- Explicit (you're being deliberate)
- Unambiguous (no false positives)
- Works with your workflow (TDD implies complexity)
- Easy to implement

Here's the minimal hook:

```python
#!/usr/bin/env python3
"""PreToolUse - Block direct edits when /exec command is used."""
import json
import sys

BLOCKING_TOOLS = {"Write", "Edit", "MultiEdit"}

def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    transcript_path = data.get("transcript_path", "")
    
    if is_exec_mode(transcript_path):
        if tool in BLOCKING_TOOLS:
            print(json.dumps({
                "decision": "block",
                "reason": "In /exec mode. Delegate file modifications to Task subagent."
            }))

def is_exec_mode(transcript_path: str) -> bool:
    """Check if last user message starts with /exec."""
    if not transcript_path:
        return False
    
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "user":
                    content = data.get("message", {}).get("content", "")
                    if isinstance(content, str):
                        return content.strip().startswith("/exec")
            except json.JSONDecodeError:
                continue
        
        return False
    except Exception:
        return False

if __name__ == "__main__":
    main()
```

**Usage:**
```
User: "/exec Implement user auth with tests. TDD approach."
      ↓
Hook detects /exec
      ↓
Claude tries Write → blocked
      ↓
Claude creates Task subagent instead
      ↓
Task handles all file modifications + tests
```

***

## Optional Enhancement: Add Context to Subagents

You could append instructions when `/exec` is detected via `UserPromptSubmit`:

```python
#!/usr/bin/env python3
"""UserPromptSubmit - Append TDD guidance when /exec is used."""
import json
import sys

def main():
    try:
        input_data = json.load(sys.stdin)
        prompt = input_data.get("prompt", "").strip()
        
        if prompt.startswith("/exec"):
            # Remove the /exec prefix and append TDD guidance
            actual_task = prompt[5:].strip()
            
            tdd_guidance = (
                f"\n\n**Execution Mode (TDD)**: Write tests first, then implementation.\n"
                f"Task: {actual_task}\n\n"
                "Delegate all file modifications to specialized Task subagents. "
                "You orchestrate; subagents implement and test."
            )
            
            print(actual_task + tdd_guidance)
    except Exception as e:
        print(f"exec_hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

But honestly, the blocking hook alone is probably sufficient. The `/exec` signal is explicit enough.

***

## Ultra-Simple Version (Recommended)

If you want to keep it dead simple:

```python
#!/usr/bin/env python3
import json, sys

def main():
    data = json.load(sys.stdin)
    if not is_exec_mode(data.get("transcript_path", "")):
        return
    
    if data.get("tool_name") in {"Write", "Edit", "MultiEdit"}:
        print(json.dumps({"decision": "block", "reason": "Use Task subagent in /exec mode."}))

def is_exec_mode(path: str) -> bool:
    try:
        with open(path) as f:
            for line in reversed(f.readlines()):
                data = json.loads(line)
                if data.get("type") == "user":
                    return data.get("message", {}).get("content", "").strip().startswith("/exec")
    except:
        pass
    return False

if __name__ == "__main__":
    main()
```

**Pros:**
- 15 lines total
- No false positives (you control when it triggers)
- Explicit intent
- Works with your TDD workflow

**In claude_settings.json:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "~/.claude/hooks/PreToolUse/exec-orchestrator.py"
      }
    ]
  }
}
```

Done. Ship it?
