---
title: "what are popular statusLine items for claude code?"
date: "2025-12-30"
mode: "COPILOT"
uuid: "5eb6b3f6-2f78-4a9d-b46a-9f90a5701672"
entry_count: 5
---

## Human

what are popular statusLine items for claude code?

## Assistant

Perfect! I have comprehensive information about Claude Code statusLine items. Let me provide a complete answer.

## Popular StatusLine Items for Claude Code

Claude Code's statusLine feature allows you to display real-time metrics and information at the bottom of your terminal during coding sessions. Here are the most popular items developers include:

### Core Context & Token Metrics

The most commonly tracked metrics relate to your API usage:

- **Context Percentage** – Shows percentage of context limit used (out of 200k total)[1]
- **Context Percentage (Usable)** – Shows percentage of usable context (out of 160k, accounting for auto-compact at 80%)[1]
- **Tokens Input** – Input tokens consumed in current session[1]
- **Tokens Output** – Output tokens generated[1]
- **Tokens Cached** – Tokens read from or written to cache[1]
- **Tokens Total** – Cumulative total tokens across entire session[1]
- **Context Length** – Current context window size in tokens[1]

### Cost & Session Tracking

Since cost awareness is critical for heavy Claude Code users:

- **Session Cost** – Total cost in USD for current session[1]
- **Session Clock** – Elapsed time since session start (e.g., "2hr 15m")[1]
- **Block Timer** – Time elapsed in current 5-hour conversation block with optional progress bar[1]

### Model & Workspace Info

Essential contextual information about your current setup:

- **Model Name** – Current Claude model being used (e.g., "Claude 3.5 Sonnet")[1]
- **Output Style** – Currently set output style in Claude Code[1]
- **Current Working Directory** – Shows working directory with configurable path segments[1]
- **Version** – Claude Code version number[1]

### Git Integration

Repository awareness for better session context:

- **Git Branch** – Current git branch name[1]
- **Git Changes** – Uncommitted insertions/deletions (e.g., "+42,-10")[1]
- **Git Worktree** – Active git worktree name when using git worktrees[1]

### Advanced Features

For power users building custom workflows:

- **Custom Text** – Static custom text for project identifiers or environment indicators[1]
- **Custom Command** – Execute shell commands with output displayed inline, receiving Claude Code's JSON data via stdin[1]
- **Separator/Flex Separator** – Visual dividers between widgets that can expand to fill space[1]

### Most Popular Combinations

Based on community implementations, the most practical statusLine setups combine:[2][3]

1. **Budget-Conscious Setup** – Model, Session Cost, Context Percentage, Git Branch
2. **Performance Monitoring** – Context Percentage, Session Clock, Tokens Total, Block Timer
3. **Comprehensive Dashboard** – Model, Git Branch, Context %, Session Cost, Session Clock, Lines Added/Removed[3]

### Available JSON Data Fields

Your custom statusLine script receives real-time JSON data via stdin, including:[1]

```
- model.display_name (e.g., "Claude 3.5 Sonnet")
- workspace.current_dir / project_dir
- context_window.total_input_tokens / total_output_tokens
- context_window.current_usage (real-time token counts)
- cost.total_cost_usd / total_duration_ms
- cost.total_lines_added / total_lines_removed
- version
- output_style.name
- hook_event_name (e.g., "Status")
- session_id / transcript_path
```

### Popular Pre-Built Tools

If scripting isn't your preference, these community tools provide pre-built statusLine solutions:[2]

- **ccstatusline** – Highly customizable with 18+ atomic components, powerline support, and interactive TUI configuration
- **chongdashu/cc-statusline** – Interactive setup with multiple layout options and modern color schemes
- **hell0github/claude-statusline** – Multi-layered progress bars with weekly tracking and cost integration
- **Owloops/claude-powerline** – Vim-style powerline rendering with theme support

### Implementation Tips

When building your statusLine, keep in mind:[1]

- Updates run at most every 300 ms
- First line of stdout becomes the status line text
- ANSI color codes are supported for styling
- Use `jq` for JSON parsing in bash scripts
- Test with: `echo '{"model":{"display_name":"Test"},...}' | ./statusline.sh`

For Windows 11 users specifically, ccstatusline supports PowerShell 7.5+ with full Powerline font compatibility through Windows Terminal or by installing a Nerd Font like JetBrains Mono.

## Human

I have a command called /retro.  It's for goign thru chat history and finding things to learn and remember.  What would be a good emoji for it?

## Assistant

🧠 would be a great emoji for your /retro command. It symbolizes learning, memory, and reflection—perfect for reviewing chat history to extract insights worth remembering.[4]

## Why 🧠 Works Best

The brain emoji directly evokes knowledge retention and cognitive processing, aligning with your goal of finding "things to learn and remember." It's clean, universally understood, and commonly used in educational/tech contexts.[1][4]

## Strong Alternatives

Consider these based on nuance:

- **📚** – Books for structured learning from past conversations[4]
- **💡** – Lightbulb for new insights discovered in history[4]
- **🔍** – Magnifying glass for searching/digging through archives
- **⏪** – Fast reverse for literally going back through chat history
- **💾** – Floppy disk for saving memorable knowledge[6]

## Usage Example

```
/retro 🧠
```

The 🧠 stands out in command lists while clearly signaling "retrospective learning." Pair it with a short description like `/retro 🧠 Review history for key learnings` in your command menu.[1]

## Human

We also have a Did You Forget reminder in the statusline.  What would be a good emoji for that?

## Assistant

🧠❓ would be an excellent emoji combo for your "Did You Forget" statusline reminder. The brain with a question mark perfectly captures memory recall prompts and gentle nudges about overlooked details.

## Why 🧠❓ Fits Perfectly

This combination signals "memory check" instantly—🧠 for retention and ❓ for the questioning reminder aspect. It's compact for statuslines while being instantly recognizable in technical interfaces like Claude Code.

## Top Alternatives

- **🧠💭** – Brain + thought bubble for reflective memory prompts[1]
- **💡❓** – Lightbulb question for "aha, remember this?" moments[2]
- **👆🧠** – Pointing finger to brain for direct "don't forget" cues[1]
- **🔔🧠** – Bell + brain for notification-style memory alerts[2]
- **🎗️❓** – Reminder ribbon with question for awareness nudges[6]

## Statusline Implementation

```
DidYouForget 🧠❓ 3 items
```

Pairs beautifully with your /retro 🧠 command—consistent brain theme across memory features while ❓ differentiates the proactive reminder from retrospective review. Keeps your statusline clean and thematic.[10]

## Human

I only want one emoji for each of Did you forget and Retro

## Assistant

For **Retro**, use: **🧠**  
For **Did You Forget**, use: **🔔**  

- **🧠 Retro** – Strong association with reflection, learning, and memory, ideal for reviewing past chats to extract insights.[1]
- **🔔 Did You Forget** – Universally understood as a reminder/notification symbol, works well in tight statusline space and clearly signals “attention, don’t forget this.”[2]

## Human

Nice!

## Assistant

Glad you like them!
