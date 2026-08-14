---
title: "where does cline in vscode keep it's chat history?  A file is missing and I hope the chat history has the contents."
date: "2025-12-20"
mode: "COPILOT"
uuid: "ed617203-1864-4db8-b619-50370079169e"
entry_count: 1
---

## Human

where does cline in vscode keep it's chat history?  A file is missing and I hope the chat history has the contents.

## Assistant

Cline stores each chat as a “task” under VS Code’s globalStorage for the extension, not in your workspace. On all platforms you’re looking for a `tasks` folder under `saoudrizwan.claude-dev` in VS Code’s user data directory.[1][2]

## Default locations

On a local (non-remote) VS Code setup, the Cline task/chat history folders are here:[2][3][1]

- **Windows**:  
  `C:\Users\<yourname>\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\tasks`
- **Linux**:  
  `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks`
- **macOS**:  
  `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/tasks`

Each subfolder under `tasks` corresponds to a conversation and typically contains `api_conversation_history.json` and `ui_messages.json`, which together hold the full chat.[4][1]

## Remote / devcontainer cases

If you were using Cline in a remote environment (SSH, Codespaces, devcontainer), the path is similar but under the remote VS Code server data dir, for example on Linux:[1]

- `~/.config/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks`

If you rebuilt a devcontainer or changed the remote environment, the VS Code extension’s history can remain on the host while the project filesystem changed, so check both local and remote `tasks` locations.[4][1]

## If a conversation is missing

- Even when a conversation disappears from the sidebar, its folder often still exists under `tasks` with large `api_conversation_history.json` / `ui_messages.json` files.[3][4]
- If you find the folder but Cline does not show it, you can:
  - Use Cline’s “Export” button if the task still opens, or  
  - Manually inspect those JSON files to recover the content.

If you tell which OS and whether you were in a devcontainer/SSH session, a more precise path or recovery approach can be suggested.
