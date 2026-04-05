# Claude Code Statusline Documentation

## Overview

Using [kostyay/claude-status](https://github.com/kostyay/claude-status) - a fast Go-based statusline for Claude Code CLI.

**Binary Location:** C:\Users\brsth\.claude\claude-status.exe

**Repository:** P:/worktrees/w1t2/claude-status/ (third-party, built from source)

**Config:** C:\Users\brsth\AppData\Local\claude-status\config.json

---

## Features

- **Fast** - Single binary, ~10MB, sub-millisecond startup
- **Smart Caching** - Git info cached based on file modification times
- **GitHub CI Status** - Shows build status for current branch
- **Git Diff Stats** - Line additions/deletions and file change counts
- **Context Percentage** - Actual context usage tracking
- **Multi-Profile** - Use --prefix to identify different sessions
- **Customizable** - Full Go template support with ANSI colors

---

## Configuration

Config file: %LOCALAPPDATA%\claude-status\config.json

See claude-status README for full template reference and configuration options.

---

## Previous Statusline

The previous PowerShell statusline (statusline.ps1) is documented in git history but no longer in use.
