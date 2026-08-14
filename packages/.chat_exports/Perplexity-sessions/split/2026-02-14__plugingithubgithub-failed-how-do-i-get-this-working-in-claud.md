---
title: "plugin:github:github · ✘ failed, how do I get this working in Claude Code?  I think it's an authentication issue."
date: "2026-02-14"
mode: "COPILOT"
uuid: "d8449d52-88d8-48a1-986a-b5121efe3bb6"
entry_count: 2
---

## Human

plugin:github:github · ✘ failed, how do I get this working in Claude Code?  I think it's an authentication issue.

## Assistant

The "plugin:github:github ✘ failed" error in Claude Code typically stems from GitHub authentication issues during plugin installation or MCP (Model Context Protocol) connection, common on Windows setups like yours with multi-terminal Git workflows.[1][2]

## Quick Diagnosis
Run `/doctor` in Claude Code to check for auth, version, or Git config problems—it's built-in and scans your environment. Also verify Claude Code version with `claude --version` (needs 1.0.33+ for plugins).[3][4]

## Fix GitHub Auth for Plugins
GitHub plugins (like github@claude-plugins-official) often fail cloning due to SSH/HTTPS mismatches on Windows.[5][6]
- Ensure Git is installed via Git for Windows (includes Git Bash, required for Claude Code).[7]
- Test GitHub access: `git ls-remote https://github.com/anthropics/claude-code` (use HTTPS if SSH fails).[6]
- Add marketplace explicitly: `/plugin marketplace add https://github.com/anthropics/claude-code` (forces HTTPS).[3][6]
- Reinstall: `/plugin uninstall github`, then reinstall from marketplace.[3]

## Handle MCP/GitHub Connection
If it's the GitHub MCP failing (e.g., "Authentication Failed"), reset and re-auth.[1][2]
- Run `/logout`, close terminal, delete `~/.config/claude-code/auth.json` (or `%USERPROFILE%\.config\claude-code\auth.json` on Windows), restart `claude`.[4]
- Add MCP: `npx @modelcontextprotocol/server-github` (updates ~/.claude.json).[2]
- In Claude Code: `/mcp`, select GitHub, follow OAuth (copy URL if browser doesn't open).[8]

## Windows-Specific Tips
Your PowerShell 7.5.4/multi-terminal setup can leave Git locks or credential issues.[9]
- Use Git Bash for Claude Code sessions to avoid path/lock conflicts.[7]
- Clear Git creds: `git credential-manager uninstall`, reinstall via `winget install GitCredentialManager.microsoft`.
- If persistent, check ~/.claude.json for invalid entries and reset with `claude reset`.[8]

Test post-fix: `/plugin list` should show github enabled without errors. Report via `/bug` if stuck.[4]

## Human

How to set up gh CLI for Claude Code GitHub auth

## Assistant

Setting up the GitHub CLI (gh) enables Claude Code to execute GitHub operations like PRs and issues securely, resolving many plugin auth failures by providing pre-authenticated access.[1][2]

## Install gh CLI on Windows 11
Open PowerShell 7.5.4 as admin and run: `winget install --id GitHub.cli` (adds `gh` to PATH automatically). Verify with `gh --version`—expect v2.50+ for Claude Code compatibility.[3][4][1]

## Authenticate gh with GitHub
Run `gh auth login` (outside Claude Code).[5][6]
- Select GitHub.com, HTTPS protocol.
- Choose browser auth (opens Edge/Chrome for OAuth).
- Authorize GitHub CLI (scopes: repo, read:org, gist).
Verify: `gh auth status` (shows your username) and `gh api user` (confirms API access).[1][3]

## Integrate with Claude Code
Restart Claude Code terminal (ensures PATH pickup). Prompt naturally: "Use gh to list issues" or "Create PR with gh"—Claude executes via Bash(gh:*). For MCP/plugin auth boost, ensure `~/.config/gh/config.yml` (%AppData%\GitHub CLI\config.yml on Win) persists creds.[2][3][1]

## Test and Troubleshoot
In Claude Code: `/doctor` or prompt "Run gh auth status"—success means GitHub plugin/MCP works. If "not authenticated," delete `%AppData%\GitHub CLI\config.yml` and re-login; avoid multi-account conflicts with `gh auth switch`.[7][3]
