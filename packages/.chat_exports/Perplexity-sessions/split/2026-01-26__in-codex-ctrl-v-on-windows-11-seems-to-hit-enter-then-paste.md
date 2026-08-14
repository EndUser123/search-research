---
title: "in codex, ctrl-v, on windows 11, seems to hit enter then paste.  Why?"
date: "2026-01-26"
mode: "COPILOT"
uuid: "b0afbf9f-a4ef-416d-a0c2-f584534b6321"
entry_count: 3
---

## Human

in codex, ctrl-v, on windows 11, seems to hit enter then paste.  Why?

## Assistant

Perfect. Now I have comprehensive information. Based on the search results, I can identify the core issue and explain why this is happening.

## Why Ctrl+V Inserts Enter Before Pasting in Codex on Windows 11

The behavior you're observing—where Ctrl+V appears to hit Enter first, then pastes—occurs due to how Codex (or similar terminal-based editors) interprets the paste operation combined with Windows terminal behavior.

**The Root Cause**

When you paste content into a terminal via Ctrl+V on Windows, the terminal treats the pasted characters exactly as if you had typed them manually. If your clipboard content includes a trailing newline character (which is common when copying multi-line text or code), that newline gets transmitted to the terminal just like pressing Enter would. Since many terminal-based interfaces monitor for Enter keypresses to submit input or execute commands, the newline triggers this submission before the rest of your content is fully processed.[1][2]

**Why This Happens Specifically in Codex**

Codex's behavior stems from the interaction between terminal paste handling and the application's input processing. The GitHub issue #5172 explicitly documents this: pasting triggers a newline submission, and multiple commenters report that "stray newlines turn into literal newlines instead of submissions". This is particularly problematic in Codex because the CLI interface may be configured to interpret Enter as a submit command.[3][1]

**Windows PowerShell Context**

If you're using PowerShell in Windows Terminal on Windows 11, this behavior may be further complicated by how the terminal emulates Ctrl+V behavior. PowerShell's default Ctrl+V handling can interact unpredictably with pasted content that contains line breaks. Additionally, when Ctrl+V is bound to a terminal paste command, each line can be parsed as a separate command rather than a cohesive block.[4]

**Solutions**

1. **Use Shift+Insert instead**: This bypasses some of the keyboard shortcut handling that causes the issue[2]
2. **Use Windows+V**: On Windows 11, this opens clipboard history and lets you paste without the Enter problem[5][6]
3. **Pre-process your clipboard**: Remove trailing newlines before pasting, or use tools that strip them automatically
4. **Disable "Enter submits" on paste**: If Codex has this setting, disabling it prevents premature submission[1]
5. **Use right-click paste**: Context menu pasting sometimes avoids this issue, though behavior varies by terminal application

The fundamental issue is that terminal applications inherently process pasted content as typed input, so if that input contains a newline, it behaves like you pressed Enter. This is expected terminal behavior, not a bug—it's why command-line tools sometimes include safeguards like bracketed paste mode to differentiate typed vs. pasted input.[2]

## Human

Windows+V didn't seem to make a difference.

## Assistant

Excellent—I found the exact issue. This is a well-documented bug in Codex CLI on Windows. Let me provide you with the specific problem and working solutions.

## The Problem: Codex CLI Paste Bug on Windows

This is a confirmed bug in Codex's CLI implementation on Windows (GitHub issues #2137 and #2006). When you paste multi-line text—even if you use Windows+V—the first newline character **automatically triggers a submission** before the remaining content can be pasted. This happens regardless of the paste method because the issue is in how Codex's input handler processes newlines on Windows.[1][2]

The root cause: Codex CLI interprets every newline as an Enter keypress (immediate submission), rather than treating pasted newlines the same way as Shift+Enter (which should insert a line break without submitting).[2]

## The Real Solution: Enable Bracketed Paste Mode

One user discovered a workaround that works on similar systems: **enable bracketed paste mode** in your terminal. When enabled, the terminal wraps pasted content with special control sequences (`\e[200~` and `\e[201~`) that signal to the application "this is pasted content, not typed input"—preventing the newline from triggering submission.[3][4][2]

However, PowerShell on Windows doesn't natively support bracketed paste in the way that iTerm2 or other Unix terminals do.[2]

## Practical Workarounds for Windows

1. **Single-line reformatting workaround**: Users report success by reformatting multi-line content into a single line without line breaks before pasting. You can:[1]
   - Use an online tool to convert multi-line text to single-line
   - Pipe text through a command to remove newlines: `cat yourtext.txt | tr '\n' ' '`
   - Paste into ChatGPT.com first with the instruction "condense this into dense, single-line LLM-readable format," then copy that output and paste into Codex CLI[1]

2. **Use Shift+Insert** instead of Ctrl+V or Windows+V—though it may have the same issue since it's also a terminal paste command[5]

3. **Bypass the CLI entirely**: Paste into a file, then have Codex read the file instead of pasting directly into the interactive prompt[1]

4. **Right-click paste**: Try right-click context menu paste to see if it behaves differently (behavior varies)[2]

This is a known usability issue that the Codex maintainers have acknowledged but not yet fixed as of January 2026.[2][1]

## Human

does the clipboard thing for windows 11 have an option for no newlines?

## Assistant

Great! I found a critical feature and a workaround option. Let me get more details about the "Paste as Text" option.

## Windows 11 Clipboard History: "Paste as Text" Option

**Good news**: Windows 11's clipboard history (Windows+V) does have a built-in option that can help, though it doesn't directly remove newlines—it removes **formatting**.[1][2]

When you open the clipboard history with **Windows+V**, select an item, click the **three-dot menu (...) next to it**, and select **"Paste as Text"**. This strips all formatting (bold, italics, fonts, etc.) but **does not remove newline characters**—those are content, not formatting.[2][1]

Unfortunately, the built-in Windows clipboard doesn't have a native "remove newlines" option.[1]

## Practical Alternative: Create a Helper Utility

Since the native clipboard feature doesn't strip newlines, you'd need a workaround. You have a couple options:

1. **AutoHotkey script** (lightweight, free): Write a hotkey script that automatically removes newlines before pasting. For example:[3]
   ```
   F3::
   Clipboard := RegExReplace(Clipboard, "\v\s?", " ")
   SendInput ^v
   return
   ```
   Bind this to a hotkey, copy your text, then press F3 to paste without newlines.[3]

2. **Third-party clipboard utility**: There's a GitHub project called "Remove Newline Utility" specifically designed for this use case—a lightweight Windows utility that cleans clipboard text and removes line breaks. This might be worth exploring.[4]

3. **PowerShell one-liner**: Create a function that strips newlines from clipboard before pasting to Codex.

Given your expertise with automation and scripting, an AutoHotkey script might be the fastest solution—it would run in the background and give you a hotkey to paste-without-newlines directly into Codex.[3]

Would you want help creating a small PowerShell or AutoHotkey solution to handle this automatically?
