---
title: "Here's a chat about claude code.  Does reddit have any info a work around?

Why is my claude code not display results pr"
date: "2025-12-19"
mode: "COPILOT"
uuid: "8fcc7f02-640a-4310-9a9b-7e302613476d"
entry_count: 2
---

## Human

Here's a chat about claude code.  Does reddit have any info a work around?

Why is my claude code not display results properly? I have rebooted.
3:09 PM
Looking at your screenshot, Claude Code's terminal output is being cut off mid-display — text is truncated horizontally and you're not seeing full lines.
🔍 Root Cause Analysis
This is a terminal rendering issue, not a Claude Code malfunction. The smart commit system executed correctly (1006+ files in 3 commits), but the display is broken.
🛡️ Diagnostic Steps
1. Verify terminal dimensions:
bash
echo $COLUMNS $LINES
Should show reasonable values (e.g., 120 30). If output is missing or shows 0 values, terminal size isn't being detected.
2. Check if output is actually complete:
bash
claude --version  # Simple command to test rendering
If this displays correctly, the issue is specific to long outputs.
3. Test with explicit width:
bash
stty cols 120  # Force terminal width
claude <your-command>
⚡ Immediate Fixes (Priority Order)
Option A: Force terminal reset [HIGH confidence]
bash
reset
# Then retry your Claude Code command
Option B: Use different terminal emulator [HIGH confidence]
If Windows Terminal: Try PowerShell 7 directly
If PowerShell: Try Windows Terminal or VS Code integrated terminal
If WSL: Try native Linux terminal
Option C: Capture full output [MEDIUM - workaround]
bash
claude <your-command> 2>&1 | tee output.log
cat output.log  # View complete output
Option D: Check Claude Code configuration [LOW - unlikely cause]
bash
# Look for display settings
cat ~/.claude/config.json  # or equivalent config location
⚠️ Additional Context Needed
What terminal are you using?
Windows Terminal / PowerShell / CMD?
VS Code integrated terminal?
WSL / Git Bash?
Does the truncation happen with all Claude Code commands or just long outputs?
🎯 Most Likely Fix
95% confidence: Terminal width detection failed. Run reset followed by stty cols 120, then retry.
PS P:\> echo $COLUMNS $LINES PS P:\> claude --version # Simple command to test rendering 2.0.73 (Claude Code) PS P:\>
3:10 PM
🔍 Context: PowerShell Missing COLUMNS/LINES Variables
PowerShell doesn't use bash-style $COLUMNS/$LINES environment variables. Your terminal dimensions exist but need different commands to check.
🛡️ Validation Steps
Check actual PowerShell terminal dimensions:
powershell
# Method 1: Get current window size
$Host.UI.RawUI.WindowSize

# Method 2: Check buffer size
$Host.UI.RawUI.BufferSize
```

**Expected output should show:**
```
Width  : 120
Height : 30
If Width shows something like 80 or less, that's your problem.
⚡ Immediate Fix
Try increasing PowerShell window width:
powershell
# Set window size (adjust values as needed)
$host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(150, 40)
Then retry your Claude Code command.
⚠️ Root Cause Hypothesis [HIGH confidence]
The truncated output suggests:
Terminal width too narrow for Claude Code's formatted output
No word wrapping is occurring (text just cuts off)
Reboot didn't help because it's a PowerShell profile or terminal configuration issue
🎯 Alternative Solutions
Option A: Use horizontal scrolling [IMMEDIATE]
Manually widen your PowerShell window
Or resize before running commands
Option B: Export to file for full view [WORKAROUND]
powershell
claude <your-command> | Out-File -Width 500 output.txt
Get-Content output.txt
Option C: Check PowerShell profile [IF RECURRING]
powershell
# Check if profile sets narrow width
Test-Path $PROFILE
notepad $PROFILE  # If exists, look for WindowSize settings
📋 Next Step
Run $Host.UI.RawUI.WindowSize and share the Width value. If it's <100, that's why Claude Code output is truncating.
PS P:\> $Host.UI.RawUI.WindowSize Width Height ----- ------ 99 85 PS P:\> $Host.UI.RawUI.BufferSize Width Height ----- ------ 99 85 PS P:\>
3:11 PM
🔍 Context: Found the Problem
Width = 99 columns — This is just barely too narrow for Claude Code's formatted output, causing text truncation.
⚡ Immediate Fix
powershell
# Increase window width to 120+ columns
$host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(120, 85)
$host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(120, 9999)
Note: BufferSize Width must be ≥ WindowSize Width. Setting Height to 9999 gives you scrollback.
Then retry your Claude Code command.
🛡️ Validation
After running the resize commands:
powershell
$Host.UI.RawUI.WindowSize  # Should show Width: 120
🏗️ Permanent Fix
Add to PowerShell profile so it persists across sessions:
powershell
# Edit profile
notepad $PROFILE

# Add these lines:
$host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(150, 9999)
$host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(150, 50)
If $PROFILE doesn't exist:
powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
⚠️ Troubleshooting
If you get "Cannot set window size" error:
Your terminal emulator may restrict sizing
Try smaller values first (e.g., Width: 110)
Set BufferSize before WindowSize
Or manually drag the PowerShell window wider instead
🎯 Why 99 Columns Failed
Claude Code's formatted output (like your smart commit report) uses:
Tree structures with indentation
File counts with padding
Status messages with alignment
These typically need 110-120 columns minimum to display without wrapping/truncation.
Next: Run the resize commands above, then retry your Claude Code operation.
PS P:\> $Host.UI.RawUI.WindowSize Width Height ----- ------ 99 85 PS P:\> $Host.UI.RawUI.BufferSize Width Height ----- ------ 99 85 PS P:\> $Host.UI.RawUI.WindowSize Width Height ----- ------ 106 92 PS P:\> $Host.UI.RawUI.BufferSize Width Height ----- ------ 106 92 PS P:\>
Is 106 OK?
Show more
3:12 PM
🔍 Analysis: 106 Columns
106 columns is borderline — it may work for some Claude Code outputs but still truncate others.
🛡️ Test It Now
The fastest way to know:
powershell
# Run a command that produces wide output
claude status
# or
git status  # If you're in a repo
If the output looks complete (no mid-word cutoffs like in your screenshot), you're good.
🎯 Recommendation [MEDIUM confidence]
Ideal minimum: 120 columns for Claude Code's formatted output
Why:
Smart commit reports use deep tree structures
File lists with counts need ~15-20 chars padding
Your screenshot showed truncation at ~99, so 106 gives you only 7 extra columns
⚡ Safe Setting
powershell
# This should work without terminal restrictions:
$host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(120, 9999)
$host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(120, 92)
If that fails (terminal won't allow 120):
106 is acceptable — just watch for occasional truncation on very wide outputs
You can always manually widen the window when needed
✅ Quick Validation
Does your current terminal window look comfortable to read? If you're manually scrolling horizontally or seeing ... cutoffs, go to 120. If everything displays cleanly, stick with 106.
Next: Test with an actual Claude Code command to confirm 106 works for your use case.
Until this latest claude code update it worked fine.
3:15 PM
🔍 Context: Claude Code 2.0.73 Regression
Critical insight: This is a newly introduced bug in Claude Code, not a terminal configuration issue.
Facts
Your terminal worked fine with previous Claude Code versions
Width: 106 was sufficient before
Claude Code 2.0.73 released recently
Truncation appeared after update only
🎯 Root Cause [HIGH confidence]
Claude Code 2.0.73 likely changed:
Output formatting logic (wider default layouts)
Terminal width detection (not respecting actual dimensions)
Text wrapping behavior (disabled or broken)
⚡ Immediate Workarounds
Option A: Downgrade Claude Code [RECOMMENDED]
powershell
# Check available versions
npm list -g claude-code

# Downgrade to previous working version (example)
npm install -g claude-code@2.0.72
# or whatever version worked for you
Option B: Force wide output capture
powershell
# Redirect to file to see full output
claude <command> | Out-File -Width 500 output.txt
cat output.txt
Option C: Increase width as temporary mitigation
powershell
$host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(150, 9999)
$host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(150, 92)
🔧 Report the Bug
This is a regression that should be reported:
powershell
# Check for bug tracker
claude --help | Select-String -Pattern "issue|bug|report"
Or file at Claude Code's GitHub issues (if public) with:
Version: 2.0.73
OS: Windows PowerShell
Terminal width: 106 (previously sufficient)
Symptom: Output truncation mid-line
⚠️ Recommended Action
Downgrade to your last working version until 2.0.73 formatting is fixed. The smart commit functionality clearly works (1006 files committed successfully) — this is purely a display regression.
What version were you running before the update?
can you confirm it's a bug by looking at an issues or bug log?
3:15 PM
🔍 Searching for Claude Code Bug Reports
Let me search for known issues with Claude Code 2.0.73 and display problems.
Claude Code 2.0.73 output truncation display bug
10 results
[[BUG] Claude CLI 2.0.73 - Response Text Cutoff/Missing Characters Issue · Issue #14593 · anthropics/claude-codegithub.com]()
[[Bug] Output truncation causing incomplete responses and fragmented text · Issue #14591 · anthropics/claude-codegithub.com]()
[[BUG] Text output is truncated/cut off at the beginning or middle of lines. Characters appear to be missing randomly from the output. · Issue #14723 · anthropics/claude-codegithub.com]()
[[Bug] Terminal output truncation: Response text missing from CLI display · Issue #14694 · anthropics/claude-codegithub.com]()
[[BUG] List items and tables not rendering correctly on Windows (v2.0.73) · Issue #14664 · anthropics/claude-codegithub.com]()
[[Bug] Response text truncation: Only first or last line visible, missing content · Issue #14586 · anthropics/claude-codegithub.com]()
[[Bug] Response text truncated and misaligned on Windows terminals · Issue #14587 · anthropics/claude-codegithub.com]()
[[Bug] Terminal rendering issue in v2.0.73 - display corruption on narrow windows · Issue #14617 · anthropics/claude-codegithub.com]()
[Version 2.0.73: Text rendering bug - lines dropped and garbled output · Issue #14594 · anthropics/claude-codegithub.com]()
[[BUG] Windows: Output renders as blank lines / excessive whitespace · Issue #14621 · anthropics/claude-codegithub.com]()
✅ Confirmed: Known Bug in Claude Code 2.0.73
[HIGH confidence] — This is a widespread, confirmed regression affecting Windows users.
Facts
Multiple GitHub issues filed in last 24 hours:
Issue #14593: "Random blank spaces, actual characters missing, table-formatted responses particularly affected" [GitHub](https://github.com/anthropics/claude-code/issues/14593)
Issue #14591: "Broken return, omits words, cut off lines, fragments only" [GitHub](https://github.com/anthropics/claude-code/issues/14591)
Issue #14694: "A lot of text is missing from claude's responses... Everything worked fine until today" [GitHub](https://github.com/anthropics/claude-code/issues/14694)
Issue #14664: "List items and tables not rendering correctly on Windows (v2.0.73)" [GitHub](https://github.com/anthropics/claude-code/issues/14664)
Issue #14587: "Response text centered and ~90% of content missing/truncated" [GitHub](https://github.com/anthropics/claude-code/issues/14587)
Affected platforms: Windows (PowerShell, CMD, Windows Terminal, Git Bash, VS Code Terminal)
Common symptoms:
Random text truncation mid-line
Missing characters/words
Left side of output cut off
Table formatting broken
All issues started after update to 2.0.73
⚡ Confirmed Fix
Users report downgrading to v2.0.50 resolves the issue completely [GitHub](https://github.com/anthropics/claude-code/issues/14664)
powershell
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code@2.0.50
🎯 Root Cause [MEDIUM confidence]
Based on error logs across issues, likely TUI (Terminal User Interface) rendering regression affecting Windows ANSI escape code handling.
⚠️ Status
All issues tagged as:
area:tui
bug
platform:windows
has repro
This is NOT your configuration — Anthropic is aware and multiple users are affected.
Recommended action: Downgrade to 2.0.50 until fix is released.
Do options other than powershell work better?
3:16 PM
🔍 Analysis: Terminal Options for Claude Code 2.0.73 Bug
Based on the bug reports, NO — all Windows terminals show the same issue.
Facts from Bug Reports
Terminals tested by affected users:
PowerShell, Visual Studio Code terminal, Git Bash — "Issue persists across multiple terminals" [GitHub](https://github.com/anthropics/claude-code/issues/14593)
Git Bash, PowerShell, VS Code Terminal — all affected [GitHub](https://github.com/anthropics/claude-code/issues/14664)
Windows PowerShell, CMD, Windows Terminal (wt), Cursor integrated Terminal — "All terminals show the same issue" [GitHub](https://github.com/anthropics/claude-code/issues/14587)
PowerShell confirmed affected [GitHub](https://github.com/anthropics/claude-code/issues/14621)
Root Cause [HIGH confidence]
This is a Claude Code rendering bug, not a terminal-specific issue. The bug is in how Claude Code 2.0.73 outputs ANSI escape codes / formatting on Windows, which breaks regardless of which terminal interprets them.
🎯 Options
Option A: Downgrade (RECOMMENDED)
powershell
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code@2.0.50
Confidence: [HIGH] — Multiple users confirm this works
Works in all terminals once downgraded
Option B: Try WSL (UNCERTAIN) If you have WSL2 installed, you could try:
bash
# From WSL terminal
npm install -g @anthropic-ai/claude-code
claude
Confidence: [LOW] — Not tested in bug reports, but WSL uses Linux rendering path which might bypass Windows TUI bug
Requires WSL setup if not already installed
Option C: Wait for fix (PASSIVE)
Anthropic is aware (10+ issues filed in 24 hours)
Likely patch release coming soon
Monitor: [https://github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)
⚠️ Bottom Line
Switching terminals won't help — this is a Claude Code bug affecting all Windows terminals equally. Your best option is downgrading to 2.0.50 until Anthropic releases a patch.
Want me to provide the exact downgrade commands for your setup?
what about changing claude output format?
3:29 PM
🔍 Analysis: Claude Code Output Format Options
Let me check if Claude Code has configuration options to change output format/rendering.
Claude Code CLI output format configuration options plain text markdown
10 results
[Common workflows - Claude Code Docsclaude.com]()
[GitHub - hesreallyhim/awesome-claude-code: A curated list of awesome commands, files, and workflows for Claude Codegithub.com]()
[What is --output-format in Claude Code | ClaudeLogclaudelog.com]()
[Claude Code: Best practices for agentic codinganthropic.com]()
[Cooking with Claude Code: The Complete Guide - Sid Bharathsiddharthbharath.com]()
[Using CLAUDE.MD files: Customizing Claude Code for your codebase | Claudeclaude.com]()
[Shipyard | Claude Code CLI Cheatsheet: config, commands, prompts, + best practicesshipyard.build]()
[Claude Code Developer Cheatsheet - Commands, Config & Workflowsawesomeclaude.ai]()
[Claude Code Cli Commands full lists 20250709 · GitHubgithub.com]()
[Complete Claude Code Commands Documentationclaude.ai]()
🔍 Analysis: Output Format Options
Yes! Claude Code has --output-format flag that could bypass the rendering bug.
⚡ Available Formats
Three output formats available:
text (default) — Plain text, human-readable
json — Structured data with metadata
stream-json — Real-time streaming JSON [Claude](https://code.claude.com/docs/en/common-workflows)[ClaudeLog](https://claudelog.com/faqs/what-is-output-format-in-claude-code/)
🎯 Workaround to Try
Option A: Use JSON output (bypasses TUI rendering)
powershell
claude --output-format json
This outputs structured JSON instead of formatted terminal text, which should avoid the Windows TUI bug entirely.
Option B: Use text format explicitly
powershell
claude --output-format text
This is the default format, but explicitly setting it might trigger different rendering code path [Claude](https://code.claude.com/docs/en/common-workflows)
Option C: Non-interactive print mode
powershell
claude -p "your query here" --output-format text
Print mode (-p) is non-interactive and may use simpler output rendering [Awesome Claude](https://awesomeclaude.ai/code-cheatsheet)
🛡️ Test This First
powershell
# Test if JSON format bypasses the bug
claude --output-format json

# In the session, ask something simple
# The output will be JSON - ugly but complete
If JSON shows complete output (even if hard to read), you've confirmed the bug is in the formatted text renderer only.
⚠️ Tradeoffs
JSON format:
✅ Complete data (no truncation)
✅ Programmatically parseable
❌ Much harder to read for humans
❌ Loses formatting/colors
Print mode:
✅ Simpler rendering
✅ May avoid TUI bug
❌ Non-interactive (one-shot queries)
🏗️ Recommendation Priority
Try --output-format json first (15 seconds to test)
If that works but is unreadable → Downgrade to 2.0.50 (permanent fix)
If you need JSON output parsed → pipe through jq or save to file
Quick test: Run claude --output-format json right now and see if output is complete (even if ugly).

## Assistant

## Claude Code 2.0.73 Display Bug: Reddit & Community Workarounds

Yes, **Reddit and GitHub confirm this is a widespread, known bug** in Claude Code 2.0.73 affecting all Windows users. Here's what the community is doing to fix it.

### Confirmed Bug Status

The issue is **extensively documented** across multiple platforms. Your experience matches dozens of reports filed in the last 24 hours on GitHub (issues #14593, #14591, #14694, #14664, #14587, #14621). This is not a configuration problem—it's a regression in Claude Code's Terminal User Interface (TUI) rendering specifically affecting Windows.[1][2]

### Community-Verified Workarounds

**Priority 1: Downgrade (Most Recommended)**

Reddit users confirm that downgrading to v2.0.50 or v1.0.88 completely resolves the truncation:[3][4]

```powershell
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code@2.0.50
```

A Reddit post with 30 upvotes documents this fix, with users reporting the issue disappeared after downgrading to 1.0.88. **Important:** Keep auto-update disabled after downgrading to prevent re-installation of the broken version.[4]

**Priority 2: Output Format Workaround**

Claude Code supports alternative output formats that bypass the rendering bug entirely:[5]

```powershell
claude --output-format json
```

This outputs structured JSON instead of the broken formatted text, giving you complete data without truncation. The tradeoff: it's less readable but 100% complete. You can pipe JSON to a file and parse it programmatically if needed.[5]

**Priority 3: Pipe to File (Temporary)**

Capture the full output by redirecting:

```powershell
claude <your-command> | Out-File -Width 500 output.txt
Get-Content output.txt
```

This preserves complete output even though the terminal display is broken.[6]

**Priority 4: Environment Variables**

Reddit discussions mention setting `BASH_MAX_OUTPUT_LENGTH` environment variable and enabling verbose mode to control truncation behavior, though this is less reliable than downgrading.[7]

### Why No Terminal Switch Works

All Windows terminals are affected equally—PowerShell, CMD, Windows Terminal, Git Bash, and VS Code integrated terminal—because the bug is in Claude Code's output rendering logic, not the terminal itself. Switching terminals won't help.[8][1]

### What the Community Recommends

The Reddit consensus is clear: **downgrade to v2.0.50** until Anthropic releases a patch (which is likely coming soon given the volume of reports). The smart commit functionality is working perfectly (1006 files successfully), so the tool itself is fine—this is purely a display bug.[1][4]

## Human

Is there a valid reason to use another terminal vs powershell on windows 11?

## Assistant

Now I have comprehensive information. Let me create a well-structured answer:

## Valid Reasons to Use Alternative Terminals on Windows 11

Yes, there are several **legitimate technical and productivity reasons** to use something other than plain PowerShell on Windows 11—though the choice depends on your specific workflow.

### Windows Terminal (Recommended for Most Users)

**Windows Terminal is the modern replacement for direct PowerShell usage**. Key advantages:[1]

**Performance & Rendering**: Windows Terminal uses GPU-accelerated DirectWrite and Direct2D text rendering, making it noticeably smoother and more responsive than PowerShell, especially with large output volumes. This is particularly relevant for your Claude Code issue—the rendering engine handles complex output better.[2][3][4]

**Tabbed Interface & Multitasking**: Multiple tabs and panes allow you to run PowerShell, CMD, and even WSL bash simultaneously in a single window. You can switch between contexts with keyboard shortcuts without managing separate window instances.[5][1]

**Modern Customization**: Extensive settings for themes, colors, fonts, and background images. Full Unicode/UTF-8 support handles special characters natively without extra configuration.[3][2]

**Unified Shell Access**: Launch PowerShell, CMD, Git Bash, or WSL distributions from the same application—crucial for developers working across Windows and Linux ecosystems.[6][1]

**Resource Tradeoff**: Windows Terminal uses more RAM (~2.5GB with multiple tabs) and GPU than plain PowerShell (~0.3GB), which matters on laptops with battery concerns but is negligible on desktop machines.[7]

### WSL (Linux Bash on Windows)

**If you work with Linux-centric tools** (Node.js, Python, Make, GNU utilities, Docker), WSL provides native Linux compatibility without translation layers:[8]

- Follow Linux tutorials verbatim without command conversion
- Match Linux server environments exactly (eliminates "works on Linux, not Windows" problems)
- Native compatibility with open-source CLI tools that prioritize Linux first[8]

**Workflow recommendation**: Use WSL for development, PowerShell for Windows administration. Configure both in Windows Terminal for seamless switching.[8]

### Git Bash

**Minimal use case**: If you only need Unix-style commands (grep, sed, awk) and heavy Git workflows, Git Bash is lightweight and self-contained. However, it's largely superseded by WSL for serious development work.[9][10]

### Summary for Your Situation

For Claude Code development work specifically:

| Terminal | Best For |
|----------|----------|
| **Windows Terminal + PowerShell** | Your current primary use—modern UI, better rendering for complex output, tabbed workflows[2][5][4] |
| **Windows Terminal + WSL** | If your Claude Code work involves Python, Node.js, or Linux-based tools[8][6] |
| **Plain PowerShell** | Avoid for extended development—limited customization, no tabs, older rendering engine[2][1] |
| **CMD** | Only for legacy Windows batch scripts[11] |

**Bottom line**: Switch to **Windows Terminal running PowerShell 7** (not Windows PowerShell). This gives you the modern interface and GPU rendering improvements while keeping the PowerShell scripting power you're already using. The tabbed interface alone significantly improves multitasking for your AI development workflows.[12][5]
