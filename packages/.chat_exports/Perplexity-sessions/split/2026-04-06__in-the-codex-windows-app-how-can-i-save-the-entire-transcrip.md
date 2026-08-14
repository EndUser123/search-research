---
title: "in the codex windows app, how can I save the entire transcript?"
date: "2026-04-06"
mode: "COPILOT"
uuid: "f5fe0c2c-fe7d-4849-b555-4597003801c8"
entry_count: 1
---

## Human

in the codex windows app, how can I save the entire transcript?

## Assistant

The Codex Windows app (OpenAI's desktop coding agent tool from the Microsoft Store) stores conversation transcripts locally but lacks a direct built-in "save entire transcript" button per current docs and user reports.[1][2][3]

## Access Local Files
Transcripts are saved automatically in `~/.codex/sessions/` or equivalent Windows path (e.g., `%USERPROFILE%\.codex\sessions\`) as JSONL files with timestamps, messages, and token usage—similar to CLI behavior.[4][5]

- Navigate via File Explorer to `%USERPROFILE%\.codex\sessions\`.
- Open JSONL files in a text editor (e.g., VS Code) for full raw transcript.
- Use tools like `JsonlToMD` (C# converter) to export to Markdown.[6]

## Copy Transcript
Use Ctrl+T (or equivalent shortcut) to view/highlight transcript, then copy to clipboard—user-requested but unconfirmed in app vs CLI.[7][8]

## Export Alternatives
Request Codex generate/export via prompt (e.g., "Export this full transcript to Markdown file"), or use OpenAI data export for all history: Settings > Data Controls > Export Data (email-delivered ZIP).[9][10]

Uncertainty: No official Codex app docs detail Windows-specific UI export; CLI methods dominate results. Check app updates or GitHub issues for changes. Next step: Prompt Codex in-app for its local storage path.[11][12]
