---
title: "for antigravity, how do I add a rule?"
date: "2026-01-14"
mode: "COPILOT"
uuid: "8ef37c03-d5e8-4202-9b4c-f5356596a392"
entry_count: 4
---

## Human

for antigravity, how do I add a rule?

## Assistant

I need to understand what you're referring to by "antigravity" and what kind of rule you want to add. This could relate to several different contexts:

1. **A game or mod** (given your interest in Sims modding) - are you working on a Sims mod that has antigravity mechanics?
2. **A custom AI/coding framework** - could this be a rule in your custom systems (CKS, CHS, or another framework)?
3. **A physics simulation or engine** - are you building or configuring something with gravity simulation?
4. **A specific tool or library** - is "antigravity" a particular tool, plugin, or framework you're using?
5. **A Semgrep or linting rule** - could this be related to code analysis rules?

Could you provide more context about:
- What project or tool you're working with?
- What you're trying to accomplish with this rule?
- Any relevant code, configuration files, or documentation you're referencing?

This will help me give you a precise answer tailored to your specific use case.

## Human

gemini vscode clone

## Assistant

Based on the search results, I can provide you with clarity on what you might be looking for:

## Gemini VSCode Clone Options

You have several options depending on what you need:

**1. Clone a Gemini VSCode Extension Repository**

If you want to clone a community-created Gemini VSCode extension from GitHub, look for projects like the **Web Chat for Gemini** extension:[1]

```bash
git clone https://github.com/viv1/gemini-web-vscode.git
```

This is an open-source extension that lets you interact with Gemini APIs directly in VS Code using Gemini 1.5 Flash.

**2. Use the "Clone in VS Code" Browser Extension**

For cloning any GitHub repository into VS Code quickly, install the **"Clone in VS Code"** browser extension, which adds a one-click button on GitHub, GitLab, and Bitbucket repos to clone them directly into VS Code.[2]

**3. Official Gemini Code Assist Extension**

If you want the official Google extension, install **Gemini Code Assist** directly from the VS Code Marketplace:[3][4]
- Open VS Code
- Press `Ctrl+Shift+X` to open Extensions
- Search for "Gemini Code Assist"
- Click Install

**4. Gemini CLI Integration**

For a more comprehensive setup, use **Gemini CLI** with VS Code integration:[5]

```bash
npm install -g @google/gemini
```

Then run `/ide install` from the Gemini CLI terminal to integrate with VS Code.

Could you clarify which of these scenarios matches your use case? Are you looking to:
- Clone a Gemini extension repository?
- Install an official Gemini tool in VS Code?
- Set up Gemini CLI with IDE integration?
- Something else entirely?

## Human

Google release a product called Antigravity.

## Assistant

Perfect! Now I have the detailed information. Here's how to add a rule in Google Antigravity:

## How to Add a Rule in Google Antigravity

**Rules** are system-level guidelines that help shape the agent's behavior across code generation, testing, and verification tasks. They're persistent instructions the agent applies to all future tasks within their scope (either globally or at the workspace level).

### Quick Steps to Add a Workspace Rule

1. **Open Customizations**: Click the `...` menu in the top right corner of Antigravity and select `Customizations`

2. **Navigate to Rules**: Click on the `Rules` section

3. **Create a New Rule**: Click the `+Workspace` button to add a workspace-specific rule (or use the global option if you want it to apply everywhere)

4. **Define Your Rule**: Write your rule as markdown guidelines. For example:

```
* Make sure all code follows PEP 8 style guide
* Always add docstrings to all functions and methods
* Use type hints for all function parameters
```

5. **Save**: The rule is automatically saved to your workspace

### Rule Storage Locations

- **Global rules**: `~/.gemini/GEMINI.md`
- **Workspace rules**: `your-workspace/.agent/rules/`

### Example Workflow

Once you've added rules, they'll automatically guide the agent's behavior. For instance, if you create a code-generation rule like this:

```
* Generate functionality in separate files (e.g., feature_x.py)
* Call example functions from the main method
* Keep main.py as the entry point only
```

When you ask the agent to implement features, it will follow these patterns automatically without you having to repeat them in every prompt.

### Workflows vs. Rules

If you want **on-demand** instructions instead, use **Workflows** (saved prompts triggered with `/`). But for persistent guidelines across all tasks, **Rules** is what you need.

This architecture aligns well with your agentic AI systems background—rules function similarly to system-level instructions in Claude Code, establishing governance while agents maintain autonomy to execute within those constraints.

## Human

I tried saving, and it looked like it saved, but then the rule was never available, and when I went back to look it wasn't there.

## Assistant

This is a known issue with Antigravity. Based on the troubleshooting documentation and community reports, here are the most common causes and fixes for rules not persisting:

## Why Your Rules Aren't Saving

**Known Issue: Rules not persisting or disappearing after saving is a documented bug in Antigravity**, particularly with workspace rules. The UI may show a successful save, but the rule files aren't being properly written or synced.

### Immediate Troubleshooting Steps

**1. Clear Antigravity Cache & Restart**

The most effective fix is to clear local cache files and restart:

**Windows (PowerShell):**
```powershell
rd /s /q "%APPDATA%\Antigravity\Cache"
rd /s /q "%APPDATA%\Antigravity\GPUCache"
```

**macOS:**
```bash
rm -rf ~/Library/Application\ Support/Antigravity/Cache
rm -rf ~/Library/Application\ Support/Antigravity/GPUCache
```

**Linux:**
```bash
rm -rf ~/.config/Antigravity/Cache
rm -rf ~/.config/Antigravity/GPUCache
```

Then fully close and restart Antigravity.

**2. Manually Verify File Creation**

After saving a rule through the UI, manually check if the file was actually created:

- **Workspace rules** should appear in: `your-workspace/.agent/rules/`
- **Global rules** should appear in: `~/.gemini/GEMINI.md`

If the files don't exist, the save operation failed.

**3. Create Rules Directly via File System**

Instead of using the UI, create rule files manually:

For workspace rules, create `.agent/rules/code-style.md` in your workspace root:
```
* Make sure all the code is styled with PEP 8 style guide
* Make sure all the code is properly commented
```

For global rules, edit `~/.gemini/GEMINI.md` directly and add your rules there.

**4. Check for Permission Issues**

Ensure the `.agent/` directory has write permissions:

**Windows:**
```powershell
Get-Acl "your-workspace\.agent" | Format-List
```

**macOS/Linux:**
```bash
ls -ld your-workspace/.agent/
```

If you see permission restrictions, your Antigravity process can't write to that directory.

**5. Try Global Rules Instead**

If workspace rules consistently fail, temporarily use global rules instead (`~/.gemini/GEMINI.md`). Global rules have better persistence currently.

### Report the Bug

Since this appears to be a persistent bug with workspace rule persistence:

- **Email:** support@perplexity.ai (or check Antigravity's official support channel)
- **Include:** Screenshots of the save attempt, your Antigravity version, OS, and the exact rule you tried to save
- **Workaround in the meantime:** Use global rules or manually edit `.agent/rules/` files directly in your editor rather than the Antigravity UI

Given your background with custom frameworks and system architecture, this type of state persistence issue likely stems from the UI changes not properly triggering file writes or a race condition during the save operation. The cache clearing typically resolves it because it resets the connection state between the UI and the filesystem layer.
