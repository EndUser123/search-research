---
title: "in openai codex on windows 11, how can I have two different tasks working at the same time?  at the cli, I would have  t"
date: "2026-04-18"
mode: "COPILOT"
uuid: "74bb0b8b-24df-4b60-a2bd-6be35b78b536"
entry_count: 3
---

## Human

in openai codex on windows 11, how can I have two different tasks working at the same time?  at the cli, I would have  two terminals, but how do I do that in the windows app?

## Assistant

**OpenAI's Codex app on Windows 11 supports parallel tasks natively via multiple threads and Git worktrees, unlike single CLI sessions.** Download it from the Microsoft Store or via `winget install Codex -s msstore`.[1]

## Core Methods
Use **threads** in one app window: Create separate threads for each task (Local mode for direct work, Worktree for isolated Git clones avoiding conflicts). Each includes an integrated PowerShell terminal (customizable to Git Bash/WSL).[2][3]

**Worktrees** enable true parallelism: Codex clones your branch into a new worktree per thread, letting agents run independently on the same codebase without interference.[4][2]

**Cloud mode** spins up remote isolated containers for heavy parallel tasks, viewable in the dashboard.[5][2]

## Windows Setup
Install prerequisites: Git, Node.js, Python via `winget` in PowerShell (e.g., `winget install Git.Git`). Native sandbox uses PowerShell; switch to WSL2 agent in Settings if needed (restart required).

Open multiple app windows for non-syncing parallelism per project, but prefer threads/worktrees to avoid stale file states.[6]

## Steps for Two Tasks
1. Add project (Ctrl+O), create Thread 1 (Worktree mode, prompt task A).
2. Create Thread 2 (Worktree mode, prompt task B)—both run concurrently with separate terminals/diffs.
3. Review diffs inline, commit/push per thread.[2]

Assumption: Tasks are non-conflicting (use worktrees). Windows native has minor sandbox bugs per GitHub; test in worktrees first. Confidence: High (official docs). Next: `codex add-task` in terminal or app UI.[7][2]

## Human

I didn't understand that.  Can I run two codex windows apps at the same time?

## Assistant

Yes, you can run multiple instances of the OpenAI Codex Windows app simultaneously, as it's a standard WinUI app without single-instance enforcement.[1][2]

## Parallelism Options
**Multiple app windows** work for separate projects or logins (use different API keys to avoid rate limits), but file sync may lag without worktrees.[3][1]

Preferred: **Single window with threads/agents**—each on isolated Git worktrees for true concurrent tasks on the same repo, no conflicts. Agents run in background with status dashboard.[2][4]

## Quick Steps
1. Launch Codex app twice (search "Codex" in Start menu).
2. Open project in each; use `codex worktree create <task>` for isolation.
3. Monitor via dashboard (Ctrl+Shift+D).[4]

Uncertainty: Rate limits apply per account (Tier-dependent); test locally. Next: Verify your tier via `codex status`.[1]

## Human

No, I'm not talking about different worktrees.  I mean two codex instances running against the same folder in the same tree and branch.

## Assistant

**No, OpenAI Codex does not reliably support two instances running against the exact same folder/tree/branch without sync issues or interference.** Each instance snapshots files independently, leading to desynced views and conflicting changes if both edit simultaneously.[1][2]

## Limitations
Instances share session state (~/.codex/), causing context swaps or locks on Windows. No real-time file watching sync between apps—mirrors multiple unsynced terminals, but Codex warns against concurrent writes.[2][1]

## Recommended Workaround
Use **one app window** with multiple threads/agents on the shared folder: They coordinate internally via queue/diff dashboard, avoiding conflicts. Or Git worktrees (`git worktree add ../task1 branch`) for near-identical isolation with fast merges.[3][1]

Confidence: High (user reports + issues). Next step: Test `codex agent add --parallel` in single app terminal.[1]
