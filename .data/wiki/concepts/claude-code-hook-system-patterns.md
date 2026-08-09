---
title: "Claude Code Hook System Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, github]
summary: >
  The Claude Code environment provides a hook system that allows external scripts to intercept tool invocations and session lifecycle events, enabling customization of agent behavior through pre-execution validation, post-execution logging, and session management callbacks.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 59329bf3-4765-4d4e-8ec6-f2eceeba0f41" (Agentic Engineering Playbook, synced 2026-07-27)
  - "AGENTS.md - wenqingyu/ralphy-openspec - GitHub" (https://github.com/wenqingyu/ralphy-openspec/blob/main/AGENTS.md, transcript synced 2026-07-27)
  - "ralph/prompt.md at main · snarktank/ralph - GitHub" (https://github.com/snarktank/ralph/blob/main/prompt.md, transcript synced 2026-07-27)
  - "KSDaemon/ralphy: An autonomous AI coding agent loop with a terminal admin dashboard." (https://github.com/KSDaemon/ralphy, transcript synced 2026-07-27)
  - "GitHub - vercel-labs/ralph-loop-agent: Continuous Autonomy for the AI SDK" (https://github.com/vercel-labs/ralph-loop-agent, transcript synced 2026-07-27)
  - "Persistent state across context compaction · Issue #25999 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/25999, transcript synced 2026-07-27)
  - "Ralph Loop plugin: stop-hook.sh fails on Windows - cat command not found · Issue #16560 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/16560, transcript synced 2026-07-27)
  - "[Bug] Plugin hooks JSON output not captured · Issue #10875 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/10875, transcript synced 2026-07-27)
  - "ralph-claude-code/USAGE.md at main - GitHub" (https://github.com/ardmhacha24/ralph-claude-code/blob/main/USAGE.md, transcript synced 2026-07-27)
  - "hoodini/ai-agents-skills: AI Agent Skills Repository - A ... - GitHub" (https://github.com/hoodini/ai-agents-skills, transcript synced 2026-07-27)
  - "claude-code-commands-skills-agents/docs/hooks-guide.md at main - GitHub" (https://github.com/shakacode/claude-code-commands-skills-agents/blob/main/docs/hooks-guide.md, transcript synced 2026-07-27)
  - "[BUG] 2.1.27 session resume logic is loosing context · Issue #22107 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/22107, transcript synced 2026-07-27)
  - "[BUG] Claude fails to invoke Skills immediately despite explicit instructions #15136 - GitHub" (https://github.com/anthropics/claude-code/issues/15136, transcript synced 2026-07-27)
  - "[BUG] Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown · Issue #9567 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/9567, transcript synced 2026-07-27)
  - "claude-code-best-practice/best-practice/claude-skills.md at main - GitHub" (https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md, transcript synced 2026-07-27)
  - "[BUG] PostToolUse hook output visibility depends on exit code and stream #11224 - GitHub" (https://github.com/anthropics/claude-code/issues/11224, transcript synced 2026-07-27)
  - "superpowers/RELEASE-NOTES.md at main - GitHub" (https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md, transcript synced 2026-07-27)
  - "[BUG] Claude Code Bash tool incompatible with MSYS/Git Bash on Windows (requires cygpath) · Issue #9883 - GitHub" (https://github.com/anthropics/claude-code/issues/9883, transcript synced 2026-07-27)
  - "[BUG] Stop hooks fail with 'spawn /bin/sh ENOENT' on session end #21162 - GitHub" (https://github.com/anthropics/claude-code/issues/21162, transcript synced 2026-07-27)
  - "PreToolUse hook displayed instead of actual tool invocation · Issue #9661 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/9661, transcript synced 2026-07-27)
  - "claude-code-skills/docs/architecture/SKILL_ARCHITECTURE_GUIDE.md at master - GitHub" (https://github.com/levnikolaevich/claude-code-skills/blob/master/docs/architecture/SKILL_ARCHITECTURE_GUIDE.md, transcript synced 2026-07-27)
  - "A Claude Code specific implementation of the Ralph Wiggum loop. - GitHub" (https://github.com/harrymunro/ralph-wiggum, transcript synced 2026-07-27)
  - "[BUG] 'Stop hook error' displayed despite hooks producing zero output (v2.0.28) · Issue #10463 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/10463, transcript synced 2026-07-27)
  - "claude-code-skills/docs/architecture/AGENT_TEAMS_PLATFORM_GUIDE.md at master - GitHub" (https://github.com/levnikolaevich/claude-code-skills/blob/master/docs/architecture/AGENT_TEAMS_PLATFORM_GUIDE.md, transcript synced 2026-07-27)
  - "frankbria/ralph-claude-code: Autonomous AI development loop for Claude Code with intelligent exit detection - GitHub" (https://github.com/frankbria/ralph-claude-code, transcript synced 2026-07-27)
  - "GitHub - PageAI-Pro/ralph-loop: A long-running AI agent loop. Ralph automates software development tasks by iteratively working through a task list until completion." (https://github.com/PageAI-Pro/ralph-loop, transcript synced 2026-07-27)
  - "obra/superpowers: An agentic skills framework & software development methodology that works. - GitHub" (https://github.com/obra/superpowers, transcript synced 2026-07-27)
  - "claude-code-best-practice/CLAUDE.md at main - GitHub" (https://github.com/shanraisshan/claude-code-best-practice/blob/main/CLAUDE.md, transcript synced 2026-07-27)
  - "claude-code-skills/AGENTS.md at master · levnikolaevich/claude ..." (https://github.com/levnikolaevich/claude-code-skills/blob/master/AGENTS.md, transcript synced 2026-07-27)
  - "[BUG] Windows: Shell hooks (.sh files) no longer execute correctly, prompt file association dialog instead · Issue #24097 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/24097, transcript synced 2026-07-27)
  - "Bug: allowed-tools in skill frontmatter not enforced · Issue #18837 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/18837, transcript synced 2026-07-27)
  - "[BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub" (https://github.com/anthropics/claude-code/issues/24327, transcript synced 2026-07-27)
  - "Windows: Bash tool stdout capture broken when using Git Bash via CLAUDE_CODE_SHELL · Issue #26430 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/26430, transcript synced 2026-07-27)
  - "hook commands spawn visible conhost.exe window on every execution · Issue #35797 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/35797, transcript synced 2026-07-27)
  - "Stop hook fails with 'spawn /bin/sh ENOENT' on every session end (v2.1.39) · Issue #27674 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/27674, transcript synced 2026-07-27)
  - "GitHub - lst97/claude-code-sub-agents: Collection of specialized AI subagents for Claude Code for personal use (full-stack development)." (https://github.com/lst97/claude-code-sub-agents, transcript synced 2026-07-27)
  - "superpowers/skills/subagent-driven-development/SKILL.md at main - GitHub" (https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md, transcript synced 2026-07-27)
  - "claude-code-hooks-schemas.md - GitHub Gist" (https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34, transcript synced 2026-07-27)
  - "GitHub - snarktank/ralph: Ralph is an autonomous AI agent loop that runs repeatedly until all PRD items are complete." (https://github.com/snarktank/ralph, transcript synced 2026-07-27)
  - "[BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/24371, transcript synced 2026-07-27)
  - "[DOCS] Conflicting JSON Response Schemas for Hook Events (`PreToolUse` vs `PostToolUse`) · Issue #19115 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/19115, transcript synced 2026-07-27)
  - "Expose CLAUDE_SESSION_ID env var to hooks · Issue #27299 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/27299, transcript synced 2026-07-27)
  - "SessionStart hook fails on Windows — hooks.json points to .sh file which CMD.exe cannot execute · Issue #491 · obra/superpowers - GitHub" (https://github.com/obra/superpowers/issues/491, transcript synced 2026-07-27)
  - "[BUG] Agent/Skill instructions are read but not followed proactively ..." (https://github.com/anthropics/claude-code/issues/20989, transcript synced 2026-07-27)
  - "[BUG] Tool always fail to execute stop hook · Issue #17805 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/17805, transcript synced 2026-07-27)
  - "pi-mono/packages/coding-agent/docs/extensions.md at main - GitHub" (https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/extensions.md, transcript synced 2026-07-27)
  - "connerohnesorge/conclaude: Safely constrain and conclude your claude code sessions. - GitHub" (https://github.com/connix-io/conclaude, transcript synced 2026-07-27)
  - "awesome-ralph/README.md at master · snwfdhmp/awesome-ralph ..." (https://github.com/snwfdhmp/awesome-ralph/blob/master/README.md, transcript synced 2026-07-27)
  - "ralph-loop · GitHub Topics" (https://github.com/topics/ralph-loop?o=asc&s=updated, transcript synced 2026-07-27)
  - "claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub" (https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md, transcript synced 2026-07-27)
  - "Claude Code Skill: Prompt Architect - GitHub" (https://github.com/ckelsoe/claude-skill-prompt-architect, transcript synced 2026-07-27)
  - "disler/claude-code-hooks-mastery - GitHub" (https://github.com/disler/claude-code-hooks-mastery, transcript synced 2026-07-27)
  - "GitHub - zircote/sdlc-quality: Software Development Lifecycle standards plugin for AI coding assistants. Enforces build, quality, testing, CI/CD, security, and documentation best practices." (https://github.com/zircote/sdlc-quality, transcript synced 2026-07-27)
  - "codexstar69/bug-hunter: Adversarial AI bug hunter with ... - GitHub" (https://github.com/codexstar69/bug-hunter, transcript synced 2026-07-27)
  - "Managing and curating Copilot Memory - GitHub Docs" (https://docs.github.com/en/copilot/how-tos/use-copilot-agents/copilot-memory, transcript synced 2026-07-27)
  - "AI Assitant showing no Plan mode when connected with Github Copilot : r/ZedEditor - Reddit" (https://www.reddit.com/r/ZedEditor/comments/1qzk7wd/ai_assitant_showing_no_plan_mode_when_connected/, transcript synced 2026-07-27)
  - "GitHub - winstonkoh87/Athena-Public: The Linux OS for AI Agents — Persistent memory, autonomy, and time-awareness for any LLM. Own the state. Rent the intelligence." (https://github.com/winstonkoh87/Athena-Public, transcript synced 2026-07-27)
  - "Claude Code Frontend Dev - AI Visual Testing Plugin - GitHub" (https://github.com/hemangjoshi37a/claude-code-frontend-dev, transcript synced 2026-07-27)
  - "Feature Request: Layered memory system for persistent cross-session context · Issue #27298 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/27298, transcript synced 2026-07-27)
  - "Feature: Add Declarative Forced Evaluation Hooks (Markdown/Bash-Only) for Reliable Skill Activation · Issue #38 · malhashemi/opencode-skills - GitHub" (https://github.com/malhashemi/opencode-skills/issues/38, transcript synced 2026-07-27)
  - "Stop hook error: Failed with non-blocking status code: '${CLAUDE_PLUGIN_ROOT}' · Issue #32 · OthmanAdi/planning-with-files - GitHub" (https://github.com/OthmanAdi/planning-with-files/issues/32, transcript synced 2026-07-27)
  - "wenqingyu/ralphy-openspec: Ralph loop + OpenSpec integration for Cursor, OpenCode and ClaudeCode heavy lifting. - GitHub" (https://github.com/wenqingyu/ralphy-openspec, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-code-hook-system-patterns
    - level: notebook
      id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
      title: Agentic Engineering Playbook
      url: https://notebooklm.google.com/notebook/59329bf3-4765-4d4e-8ec6-f2eceeba0f41
    - level: cluster
      id: 1
      name: github-https-code
    - level: source_url
      url: https://github.com/wenqingyu/ralphy-openspec/blob/main/AGENTS.md
      title: AGENTS.md - wenqingyu/ralphy-openspec - GitHub
    - level: source_url
      url: https://github.com/snarktank/ralph/blob/main/prompt.md
      title: ralph/prompt.md at main · snarktank/ralph - GitHub
    - level: source_url
      url: https://github.com/KSDaemon/ralphy
      title: KSDaemon/ralphy: An autonomous AI coding agent loop with a terminal admin dashboard.
    - level: source_url
      url: https://github.com/vercel-labs/ralph-loop-agent
      title: GitHub - vercel-labs/ralph-loop-agent: Continuous Autonomy for the AI SDK
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/25999
      title: Persistent state across context compaction · Issue #25999 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/16560
      title: Ralph Loop plugin: stop-hook.sh fails on Windows - cat command not found · Issue #16560 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/10875
      title: [Bug] Plugin hooks JSON output not captured · Issue #10875 · anthropics/claude-code
    - level: source_url
      url: https://github.com/ardmhacha24/ralph-claude-code/blob/main/USAGE.md
      title: ralph-claude-code/USAGE.md at main - GitHub
    - level: source_url
      url: https://github.com/hoodini/ai-agents-skills
      title: hoodini/ai-agents-skills: AI Agent Skills Repository - A ... - GitHub
    - level: source_url
      url: https://github.com/shakacode/claude-code-commands-skills-agents/blob/main/docs/hooks-guide.md
      title: claude-code-commands-skills-agents/docs/hooks-guide.md at main - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/22107
      title: [BUG] 2.1.27 session resume logic is loosing context · Issue #22107 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/15136
      title: [BUG] Claude fails to invoke Skills immediately despite explicit instructions #15136 - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/9567
      title: [BUG] Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown · Issue #9567 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md
      title: claude-code-best-practice/best-practice/claude-skills.md at main - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/11224
      title: [BUG] PostToolUse hook output visibility depends on exit code and stream #11224 - GitHub
    - level: source_url
      url: https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md
      title: superpowers/RELEASE-NOTES.md at main - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/9883
      title: [BUG] Claude Code Bash tool incompatible with MSYS/Git Bash on Windows (requires cygpath) · Issue #9883 - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/21162
      title: [BUG] Stop hooks fail with 'spawn /bin/sh ENOENT' on session end #21162 - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/9661
      title: PreToolUse hook displayed instead of actual tool invocation · Issue #9661 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/levnikolaevich/claude-code-skills/blob/master/docs/architecture/SKILL_ARCHITECTURE_GUIDE.md
      title: claude-code-skills/docs/architecture/SKILL_ARCHITECTURE_GUIDE.md at master - GitHub
    - level: source_url
      url: https://github.com/harrymunro/ralph-wiggum
      title: A Claude Code specific implementation of the Ralph Wiggum loop. - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/10463
      title: [BUG] 'Stop hook error' displayed despite hooks producing zero output (v2.0.28) · Issue #10463 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/levnikolaevich/claude-code-skills/blob/master/docs/architecture/AGENT_TEAMS_PLATFORM_GUIDE.md
      title: claude-code-skills/docs/architecture/AGENT_TEAMS_PLATFORM_GUIDE.md at master - GitHub
    - level: source_url
      url: https://github.com/frankbria/ralph-claude-code
      title: frankbria/ralph-claude-code: Autonomous AI development loop for Claude Code with intelligent exit detection - GitHub
    - level: source_url
      url: https://github.com/PageAI-Pro/ralph-loop
      title: GitHub - PageAI-Pro/ralph-loop: A long-running AI agent loop. Ralph automates software development tasks by iteratively working through a task list until completion.
    - level: source_url
      url: https://github.com/obra/superpowers
      title: obra/superpowers: An agentic skills framework & software development methodology that works. - GitHub
    - level: source_url
      url: https://github.com/shanraisshan/claude-code-best-practice/blob/main/CLAUDE.md
      title: claude-code-best-practice/CLAUDE.md at main - GitHub
    - level: source_url
      url: https://github.com/levnikolaevich/claude-code-skills/blob/master/AGENTS.md
      title: claude-code-skills/AGENTS.md at master · levnikolaevich/claude ...
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/24097
      title: [BUG] Windows: Shell hooks (.sh files) no longer execute correctly, prompt file association dialog instead · Issue #24097 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/18837
      title: Bug: allowed-tools in skill frontmatter not enforced · Issue #18837 · anthropics/claude-code
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/24327
      title: [BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/26430
      title: Windows: Bash tool stdout capture broken when using Git Bash via CLAUDE_CODE_SHELL · Issue #26430 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/35797
      title: hook commands spawn visible conhost.exe window on every execution · Issue #35797 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/27674
      title: Stop hook fails with 'spawn /bin/sh ENOENT' on every session end (v2.1.39) · Issue #27674 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/lst97/claude-code-sub-agents
      title: GitHub - lst97/claude-code-sub-agents: Collection of specialized AI subagents for Claude Code for personal use (full-stack development).
    - level: source_url
      url: https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md
      title: superpowers/skills/subagent-driven-development/SKILL.md at main - GitHub
    - level: source_url
      url: https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34
      title: claude-code-hooks-schemas.md - GitHub Gist
    - level: source_url
      url: https://github.com/snarktank/ralph
      title: GitHub - snarktank/ralph: Ralph is an autonomous AI agent loop that runs repeatedly until all PRD items are complete.
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/24371
      title: [BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/19115
      title: [DOCS] Conflicting JSON Response Schemas for Hook Events (`PreToolUse` vs `PostToolUse`) · Issue #19115 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/27299
      title: Expose CLAUDE_SESSION_ID env var to hooks · Issue #27299 · anthropics/claude-code
    - level: source_url
      url: https://github.com/obra/superpowers/issues/491
      title: SessionStart hook fails on Windows — hooks.json points to .sh file which CMD.exe cannot execute · Issue #491 · obra/superpowers - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/20989
      title: [BUG] Agent/Skill instructions are read but not followed proactively ...
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/17805
      title: [BUG] Tool always fail to execute stop hook · Issue #17805 · anthropics/claude-code
    - level: source_url
      url: https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/extensions.md
      title: pi-mono/packages/coding-agent/docs/extensions.md at main - GitHub
    - level: source_url
      url: https://github.com/connix-io/conclaude
      title: connerohnesorge/conclaude: Safely constrain and conclude your claude code sessions. - GitHub
    - level: source_url
      url: https://github.com/snwfdhmp/awesome-ralph/blob/master/README.md
      title: awesome-ralph/README.md at master · snwfdhmp/awesome-ralph ...
    - level: source_url
      url: https://github.com/topics/ralph-loop?o=asc&s=updated
      title: ralph-loop · GitHub Topics
    - level: source_url
      url: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md
      title: claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub
    - level: source_url
      url: https://github.com/ckelsoe/claude-skill-prompt-architect
      title: Claude Code Skill: Prompt Architect - GitHub
    - level: source_url
      url: https://github.com/disler/claude-code-hooks-mastery
      title: disler/claude-code-hooks-mastery - GitHub
    - level: source_url
      url: https://github.com/zircote/sdlc-quality
      title: GitHub - zircote/sdlc-quality: Software Development Lifecycle standards plugin for AI coding assistants. Enforces build, quality, testing, CI/CD, security, and documentation best practices.
    - level: source_url
      url: https://github.com/codexstar69/bug-hunter
      title: codexstar69/bug-hunter: Adversarial AI bug hunter with ... - GitHub
    - level: source_url
      url: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/copilot-memory
      title: Managing and curating Copilot Memory - GitHub Docs
    - level: source_url
      url: https://www.reddit.com/r/ZedEditor/comments/1qzk7wd/ai_assitant_showing_no_plan_mode_when_connected/
      title: AI Assitant showing no Plan mode when connected with Github Copilot : r/ZedEditor - Reddit
    - level: source_url
      url: https://github.com/winstonkoh87/Athena-Public
      title: GitHub - winstonkoh87/Athena-Public: The Linux OS for AI Agents — Persistent memory, autonomy, and time-awareness for any LLM. Own the state. Rent the intelligence.
    - level: source_url
      url: https://github.com/hemangjoshi37a/claude-code-frontend-dev
      title: Claude Code Frontend Dev - AI Visual Testing Plugin - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/27298
      title: Feature Request: Layered memory system for persistent cross-session context · Issue #27298 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/malhashemi/opencode-skills/issues/38
      title: Feature: Add Declarative Forced Evaluation Hooks (Markdown/Bash-Only) for Reliable Skill Activation · Issue #38 · malhashemi/opencode-skills - GitHub
    - level: source_url
      url: https://github.com/OthmanAdi/planning-with-files/issues/32
      title: Stop hook error: Failed with non-blocking status code: '${CLAUDE_PLUGIN_ROOT}' · Issue #32 · OthmanAdi/planning-with-files - GitHub
    - level: source_url
      url: https://github.com/wenqingyu/ralphy-openspec
      title: wenqingyu/ralphy-openspec: Ralph loop + OpenSpec integration for Cursor, OpenCode and ClaudeCode heavy lifting. - GitHub
relations:
  - target: wiki/concepts/claude-code-plugin-development.md
    type: related
  - target: wiki/concepts/agent-loop-patterns.md
    type: related
  - target: wiki/concepts/tool-invocation-customization.md
    type: related
---

# Claude Code Hook System Patterns

## Decision context

**Definition:** The Claude Code environment provides a hook system that allows external scripts to intercept tool invocations and session lifecycle events, enabling customization of agent behavior through pre-execution validation, post-execution logging, and session management callbacks.

Synthesized from **61 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "github-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The PreToolUse hook fires before a tool is executed, potentially modifying tool parameters or preventing execution based on custom validation logic.
- The PostToolUse hook fires after tool execution, providing access to tool results for logging, transformation, or chaining operations.
- The Stop hook fires at session termination, intended for cleanup operations and final state persistence.
- Hook scripts communicate via JSON through stdout, with successful execution expecting JSON output and zero exit codes.
- Hook environment variables such as $CLAUDE_TOOL_INPUT may be empty or unavailable depending on hook type and invocation context.
- Exit code 2 from a PreToolUse hook causes the session to halt rather than proceeding with error feedback to the user.
- Hooks producing zero output (empty stdout with zero exit code) may still trigger error display in certain versions.
- Hook implementations may experience shell spawning failures when /bin/sh is unavailable, resulting in ENOENT errors.
- The PreToolUse and PostToolUse hooks have inconsistent JSON response schemas, creating challenges for developers building cross-hook functionality.
- Plugin hooks may not capture JSON tool output correctly in certain configurations, leading to incomplete data in hook handlers.
- The Stop hook may fail during session end even when hooks are configured correctly, suggesting lifecycle ordering issues.

## Verifiable values

| Name | Value |
|---|---|
| Hook exit code for stop/error | `2` |
| Successful hook exit code | `0` |
| Shell path expected by hooks | `/bin/sh` |
| Hook communication channel | `stdout (JSON)` |

## Related concepts

- claude-code-plugin-development — Claude Code Plugin Development
- agent-loop-patterns — Agent Loop Patterns
- tool-invocation-customization — Tool Invocation Customization
- session-lifecycle-management — Session Lifecycle Management

## Citations (from contributing transcripts)

- **Claim:** PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback
  - Source: [BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub (`a69f43d5-cdb1-484b-b502-5d6d12fff965`)
  - Context: PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback
- **Claim:** Hook environment variables and $CLAUDE_TOOL_INPUT are always empty or unknown
  - Source: [BUG] Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown · Issue #9567 - GitHub
  - Context: Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown
- **Claim:** PreToolUse hook displayed instead of actual tool invocation
  - Source: PreToolUse hook displayed instead of actual tool invocation · Issue #9661 - GitHub
  - Context: PreToolUse hook displayed instead of actual tool invocation
- **Claim:** Stop hook fails with 'spawn /bin/sh ENOENT' on session end
  - Source: Stop hook fails with 'spawn /bin/sh ENOENT' on every session end (v2.1.39) · Issue #27674 - GitHub
  - Context: Stop hook fails with 'spawn /bin/sh ENOENT' on every session end
- **Claim:** Conflicting JSON response schemas between PreToolUse and PostToolUse hooks
  - Source: [DOCS] Conflicting JSON Response Schemas for Hook Events (PreToolUse vs PostToolUse) · Issue #19115 - GitHub
  - Context: Conflicting JSON Response Schemas for Hook Events (PreToolUse vs PostToolUse)
- **Claim:** Plugin hooks JSON output not captured
  - Source: [Bug] Plugin hooks JSON output not captured · Issue #10875 - GitHub
  - Context: Plugin hooks JSON output not captured
- **Claim:** Stop hook error displayed despite hooks producing zero output
  - Source: [BUG] 'Stop hook error' displayed despite hooks producing zero output (v2.0.28) · Issue #10463 - GitHub
  - Context: Stop hook error displayed despite hooks producing zero output

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `59329bf3-4765-4d4e-8ec6-f2eceeba0f41`
(cluster `github-https-code`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Agentic Engineering Playbook](https://notebooklm.google.com/notebook/59329bf3-4765-4d4e-8ec6-f2eceeba0f41)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
