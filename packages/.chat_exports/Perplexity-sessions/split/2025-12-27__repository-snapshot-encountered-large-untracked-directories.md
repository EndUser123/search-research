---
title: "Repository snapshot encountered large untracked directories: .claude\session_history (752 files),
  __csf.nip\src\lib\c"
date: "2025-12-27"
mode: "COPILOT"
uuid: "30f8e56b-966d-40db-b5e2-bb779ea3371a"
entry_count: 1
---

## Human

Repository snapshot encountered large untracked directories: .claude\session_history (752 files),
  __csf.nip\src\lib\core_utils (748 files), __csf.nip\src\.ToolRegistry\chat_search_index (596
  files), 1 more. This can slow Codex; consider adding these paths to .gitignore or disabling undo
  in your config.


how do I disable undo for codex?

## Assistant

To disable the **undo** feature in Codex, you must modify your global or project-specific `config.toml` file. This feature functions by creating "ghost snapshots" using Git to allow per-turn reversals, but it can significantly degrade performance if your workspace contains large untracked directories.[1][2]

### Disabling via Configuration
You can disable the feature by setting the `undo` key to `false` within the `[features]` section of your configuration file.[1]

```toml
[features]
undo = false
```

### Configuration File Locations
Depending on your operating system and installation, the configuration file is typically located in one of the following directories:
- **Windows**: `%USERPROFILE%\.codex\config.toml`
- **Linux/macOS**: `~/.codex/config.toml`
- **Project-Specific**: A `codex.toml` or `.codex/config.toml` located in your repository's root directory.

### Alternative Performance Fixes
If you prefer to keep the undo functionality but want to stop the warnings and slowdowns, consider these alternatives:
- **Update `.gitignore`**: Adding the problematic paths (e.g., `.claude\session_history`) to your `.gitignore` is the recommended way to prevent Codex from scanning them during snapshotting.[3]
- **CLI Flags**: You can temporarily override features when launching the tool using the `--enable` or `--disable` flags (e.g., `codex --disable undo`).[1]
- **Ghost Snapshot Fixes**: Ensure you are on the latest version of the Codex CLI (v0.61.0+), as recent updates have improved the pre-scan logic to better respect ignored paths.[4][2]
