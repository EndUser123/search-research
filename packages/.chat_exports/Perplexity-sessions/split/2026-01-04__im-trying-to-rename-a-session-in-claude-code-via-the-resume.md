---
title: "I'm trying to rename a session in claude code via the /resume tool, but I get this error:
This error originated either b"
date: "2026-01-04"
mode: "COPILOT"
uuid: "71ac56f8-27e6-4275-9605-c18e4c20cec5"
entry_count: 1
---

## Human

I'm trying to rename a session in claude code via the /resume tool, but I get this error:
This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). The promise rejected with the reason:
Error: ENOENT: no such file or directory, open 'n/a'
    at openSync (unknown)
    at <anonymous> (B:/~BUN/root/claude.exe:12:1277)
    at tX (B:/~BUN/root/claude.exe:11:8463)
    at appendFileSync (B:/~BUN/root/claude.exe:12:1200)
    at pvD (B:/~BUN/root/claude.exe:1046:3119)
    at gB$ (B:/~BUN/root/claude.exe:1047:78)
    at gB$ (B:/~BUN/root/claude.exe:1047:214)
    at <anonymous> (B:/~BUN/root/claude.exe:3792:475)
    at <anonymous> (B:/~BUN/root/claude.exe:3792:527)
    at WH (B:/~BUN/root/claude.exe:4627:7)

## Assistant

This error occurs when Claude Code's session rename feature fails to resolve the session file path correctly, attempting to open a literal 'n/a' path instead of a valid file, which triggers an unhandled promise rejection during the async appendFileSync operation.[1][2][3]

## Cause
The bug primarily affects Windows users (like your Windows 11 setup with B:/~BUN/claude.exe), where path resolution in the rename logic mishandles session IDs or current session state, leading to ENOENT on 'n/a'.[2][1]

## Workarounds
- Avoid renaming the current active session; exit it first, then use /resume [sessionId] on a prior session and rename from there.[2]
- Use community patches like npx tweakcc --apply to enable/fix the /rename or /title commands, which handle paths more robustly across versions.[4]
- Manually rename session files in ~/.claude/sessions/ (or equivalent Windows path like %USERPROFILE%\.claude\sessions\) via PowerShell, then /resume the updated ID.[5]

## Long-term Fix
Update Claude Code to the latest version, as this is a tracked bug in Anthropic's repo (e.g., issues #15834, #15149) likely addressed in recent releases; restart after updating. Check your version with /version and report details (session ID used, full command) on GitHub for faster resolution.[6][7][1][2]
