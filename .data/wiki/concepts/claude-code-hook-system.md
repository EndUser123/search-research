---
title: "Claude Code Hook System"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, github]
summary: >
  A configuration pattern in Claude Code that allows external scripts to be invoked at specific lifecycle points, enabling users to observe, validate, or modify tool execution behavior before and after it occurs.
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
      id: claude-code-hook-system
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
  - target: wiki/concepts/claude-code-plugins.md
    type: related
  - target: wiki/concepts/agent-loop-patterns.md
    type: related
  - target: wiki/concepts/tool-execution-lifecycle.md
    type: related
---

# Claude Code Hook System

## Decision context

**Definition:** A configuration pattern in Claude Code that allows external scripts to be invoked at specific lifecycle points, enabling users to observe, validate, or modify tool execution behavior before and after it occurs.

Synthesized from **61 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "github-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The system defines hook events including PreToolUse, PostToolUse, Stop, and potentially others, each triggered at distinct phases of tool execution
- Hooks are configured through a hooks section in the Claude Code configuration file, where each hook event maps to an external script path
- The external scripts receive environment information, though multiple bug reports indicate issues with $CLAUDE_TOOL_INPUT and environment variables being empty or unavailable in some versions
- Hook scripts produce output that should be captured, but bug reports document cases where JSON output is not captured correctly and cases where zero output triggers a 'Stop hook error'
- Exit codes from hook scripts affect Claude Code behavior; a PreToolUse hook with exit code 2 causes Claude to stop rather than acting on error feedback, representing a specific design choice around error handling
- Hook scripts execute in a shell environment, with reported issues including 'spawn /bin/sh ENOENT' failures on session end in certain versions
- PreToolUse hooks may display the hook invocation itself rather than the actual tool that will be called, which can be confusing for users expecting to see the tool arguments
- Documentation gaps exist regarding JSON response schemas for different hook events, with reported inconsistencies between PreToolUse and PostToolUse schemas

## Verifiable values

| Name | Value |
|---|---|
| PreToolUse exit code for stop behavior | `2` |
| Hook shell path that may fail | `/bin/sh` |

## Related concepts

- claude-code-plugins — Claude Code Plugins
- agent-loop-patterns — Agent Loop Patterns
- tool-execution-lifecycle — Tool Execution Lifecycle

## Citations (from contributing transcripts)

- **Claim:** The hook system defines events like PreToolUse and PostToolUse triggered at specific phases
  - Source: claude-code-commands-skills-agents/docs/hooks-guide.md at main - GitHub (`3d027f2f-518a-43f1-ba65-9ce09ef91072`)
  - Context: Hooks guide documentation describing hook events at different phases
- **Claim:** PreToolUse hook with exit code 2 causes Claude to stop instead of acting on error feedback
  - Source: [BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub (`a69f43d5-cdb1-484b-b502-5d6d12fff965`)
  - Context: Exit code 2 from a PreToolUse hook causes Claude to stop execution
- **Claim:** Stop hook fails with 'spawn /bin/sh ENOENT' error on session end
  - Source: Stop hook fails with 'spawn /bin/sh ENOENT' on every session end (v2.1.39) · Issue #27674 · anthropics/claude-code - GitHub (`b53c064f-2631-436c-9701-646a1a178580`)
  - Context: Stop hook fails with spawn /bin/sh ENOENT on session end
- **Claim:** Hook environment variables and $CLAUDE_TOOL_INPUT are reported as empty or unknown
  - Source: [BUG] Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown · Issue #9567 · anthropics/claude-code - GitHub (`40df9c24-41d7-4a92-9821-78c9770b5412`)
  - Context: Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown
- **Claim:** PreToolUse hook displays the hook invocation rather than the actual tool invocation
  - Source: PreToolUse hook displayed instead of actual tool invocation · Issue #9661 · anthropics/claude-code - GitHub (`63125907-bd0b-4d8e-ac2d-f71fc2aea295`)
  - Context: PreToolUse hook displayed instead of actual tool invocation
- **Claim:** Documentation issue exists regarding conflicting JSON response schemas between PreToolUse and PostToolUse
  - Source: [DOCS] Conflicting JSON Response Schemas for Hook Events (`PreToolUse` vs `PostToolUse`) · Issue #19115 · anthropics/claude-code - GitHub (`cfcc0573-7849-4307-8fa1-be00ba724c87`)
  - Context: Conflicting JSON Response Schemas for Hook Events (PreToolUse vs PostToolUse)
- **Claim:** Plugin hooks JSON output is not captured correctly in certain cases
  - Source: [Bug] Plugin hooks JSON output not captured · Issue #10875 · anthropics/claude-code (`260ded71-c1f6-4583-bb6a-6996cc4eda0d`)
  - Context: Plugin hooks JSON output not captured
- **Claim:** Hooks with zero output may trigger a 'Stop hook error' message
  - Source: [BUG] 'Stop hook error' displayed despite hooks producing zero output (v2.0.28) · Issue #10463 · anthropics/claude-code - GitHub (`774bfb0b-0944-4137-b058-ce8da65c56ac`)
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
