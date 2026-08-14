---
title: "claude code background task timeout hang zombie"
date: "2025-12-30"
mode: "COPILOT"
uuid: "9c269a9c-61e3-41c0-9adb-82fb6588e246"
entry_count: 5
---

## Human

claude code background task timeout hang zombie

## Assistant

Claude Code encounters frequent issues with background tasks timing out, hanging, or creating zombie processes, particularly from unreaped child processes like Git operations or long-running servers. These problems often stem from improper process management in extended sessions on Windows 11 or Docker setups. Common fixes involve background execution flags, context resets, and updates.[1][2][3]

## Zombie Processes
Git child processes frequently turn into zombies, blocking sessions as Claude Code waits indefinitely for completion. Subagents and background shells (run_in_background: true) exacerbate this by accumulating unreaped reminders during long sessions. Users report relief after updates or forceful kills (kill -9), though reboots help temporarily.[3][4][5][6][1]

## Timeout Causes
Default tool timeouts hit 120 seconds for blocking commands like npm run dev, causing hangs during iterative debugging. Recursive subagent spawning leads to infinite loops and 500-second session timeouts, worsened by API delays or high CPU usage. Network/load conditions on Node.js CLI can trigger 1000ms promise crashes.[5][7][8][9][10]

## Background Task Fixes
Run commands asynchronously with & (e.g., npm run dev &) or nohup to detach from the session. Use /clear frequently to reset context, preventing memory buildup, and check /status for outdated installs before updating. For Windows 11 hook races (like sapling_checkpoint.py), implement sequential locking in custom hooks.[2][11][7][12][13]

## Prevention Strategies
Chunk long operations into checkpoints with PID tracking (echo $! > pid.txt; ps -p $(cat pid.txt)) for status polls across turns. Add timeout configs (e.g., "timeout": 60000) in task YAML and avoid recursive Task(subagent_type=...) invocations. Integrate stty -tostop for free background output and test in Docker for cleaner reap.[14][15][7][2][5]

## Human

Workarounds to prevent background tasks from becoming zombies

## Assistant

Claude Code background tasks become zombies mainly from unreaped Git or shell child processes during long sessions, especially with `run_in_background: true`. Effective workarounds focus on detaching processes, manual cleanup, and session hygiene on Windows 11 or Docker.[1][2][3][4]

## Detach Commands
Use shell builtins to orphan processes from the parent shell, preventing zombie accumulation.[5][6]
- Append `&` to launch (e.g., `npm run dev &`), then `disown %1` (check job with `jobs`).
- For running tasks: Ctrl+Z to suspend, `bg` to background, `disown -h %1` to detach from SIGHUP.
- Prefix with `nohup command > /dev/null 2>&1 & disown` for full independence.[7]

## Cleanup Tools
Leverage built-in commands and monitoring to reap zombies proactively.[8]
- Run `/killbash shell_1` (or `Kill Bash`) in v1.0.86+ to terminate specific backgrounds.[8]
- Monitor with `ps aux | grep claude` or `jobs`; kill orphans via `kill -9 <PID>` if needed.[9][10]
- Add PID tracking: `long_cmd & echo $! > pid.txt`; later `kill $(cat pid.txt)`.[11]

## Session Prevention
Reset context and update to avoid buildup from subagents or hooks.
- Issue `/clear` or `/status` frequently; update Claude Code if outdated.[12]
- In Docker: Use `stty -tostop` for free background output; avoid recursive subagents.[3]
- Custom hooks: Implement `waitpid()` or double-fork in scripts for auto-reaping.[4][13]

## Human

what does reddit and youtube and twitter say about preventing and mitigating these background zombie tasks?

## Assistant

Reddit users highlight zombie background tasks in Claude Code as a persistent bug where completed shells linger as "running" reminders, consuming tokens and hanging sessions. They recommend /tasks to list them, /clear or full restarts to purge, and avoiding recursive launches. YouTube and X/Twitter offer limited direct advice, focusing more on general workflows than zombie-specific fixes.[1][2][3][4][5]

## Reddit Fixes
Communities like r/ClaudeAI and r/ClaudeCode stress proactive cleanup and detachment.[6][1]
- Use `/tasks` to identify zombie shells (e.g., 38+ lingering as "status: running"), then `/killbash <ID>` or restart Claude Code.[1]
- Script self-kills for dev servers (e.g., pkill before npm run dev &) to prevent accumulation.[2]
- Kill parent processes; zombies reparent to init/PID 1 for auto-reap, or reboot if table fills.[7]

## Monitoring Tips
Track and detach early to mitigate token drain from zombie tracking.[8][1]
- Run `/status` and `/tasks` periodically; update to v1.0.71+ for better background command handling.[4]
- In long sessions, chunk tasks and use subagents cautiously to avoid MCP process leaks causing bills.[6]
- General Linux advice applies: disown & nohup for independence, avoiding parent wait() bugs.[7]

## Other Platforms
YouTube videos demo Claude Code workflows (e.g., context engineering) but skip zombies, emphasizing bash async over blocking. X/Twitter mentions are tangential, like debugging zombies in unrelated contexts (Doom reverse engineering). No strong video/thread consensus beyond Reddit's restart-and-detach pattern.[9][3][10][5]

## Human

any github repos about this topic?

## Assistant

No dedicated GitHub repositories exist solely for Claude Code zombie process workarounds; discussions occur primarily in Anthropic's official repo issues. Related projects like claude-flow offer background task management tools that indirectly mitigate accumulation.[1][2][3]

## Official Issues Repo
Anthropic's claude-code repo hosts dozens of bug reports and feature requests on zombies from Git, subagents, and MCP processes.[4][1]
- #10078: Git zombies hang sessions; suggests process reaping fixes.[1]
- #13444: Background shell reminders pile up with `run_in_background: true`.[2]
- #11502: Subagents leak Node processes; links to cleanup patches.[4]
- #7069: FR for native task listing/killing (tasks list, tasks kill).[5]

## Community Workarounds
ruvnet/claude-flow wiki provides practical background command persistence and killing methods across sessions.[3]
- Use `/bashes` menu or "Kill bash_3" prompts for targeted termination.
- Auto-persists tasks; monitors with pattern matching (e.g., port 8080).[3]
Other mentions include MCP cleanup scripts in Reddit-linked repos (e.g., Cnova/ude-desktop-mcp-fix), but not Claude Code-specific.[6]

## Related Projects
Zed's #45211 notes zombie leaks in competing extensions, contrasting Claude's behavior. No standalone forks or plugins; users build custom slash commands in `.claude/commands/` for task registries.[7][5]

## Human

Find repos mentioning run_in_background false true patterns

## Assistant

ruvnet/claude-flow is the primary GitHub repo documenting `run_in_background: true/false` patterns for Claude Code's Bash tool, with detailed wiki examples for preventing zombie accumulation via Ctrl+B shortcuts and KillBash cleanup. Anthropic's claude-code issues frequently reference the parameter in bug reports tied to zombie hangs.[1][2][3]

## Key Repos
- **ruvnet/claude-flow**: Wiki covers programmatic use (`"run_in_background": true`), auto-detection patterns (npm dev, docker-compose), and hooks for long-running tasks like `npm run dev &` with PID tracking.[4][1]
- **anthropics/claude-code** (issues): #15493 proposes default `run_in_background` settings; #14521 notes file-write bugs with `true`; #11433 reports TUI breakage.[2][3][5]

## Usage Patterns
Repos emphasize `true` for dev servers to avoid blocking, paired with monitoring.[6][1]
| Parameter | Example | Purpose | Repo Reference |
|-----------|---------|---------|----------------|
| `true` | `"command": "npm run dev", "run_in_background": true` | Async dev servers, builds | [1][7] |
| `false` (default) | Omitted or explicit `false` | Foreground git/status checks | [8][9] |
| Monitoring | `KillBash(shell_id: "bash_1")` | Zombie cleanup | [1][10] |

No other standalone repos; patterns appear in docs/cheatsheets linking back to these.[7][11]
