---
title: "Claude Code Skills and MCP Integration"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, github]
summary: >
  Claude Code supports an extensible skills system that allows developers to define reusable skill packages, which can integrate with Model Context Protocol (MCP) servers to enhance agentic coding workflows through structured thinking patterns and specialized task execution.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook e83b6a68-fedc-4757-b492-3360ae8377a2" (Thinking and Reasoning, synced 2026-07-28)
  - "Introducing the New Codex for (almost) everything - OpenAI Developer Community" (https://community.openai.com/t/introducing-the-new-codex-for-almost-everything/1379125, transcript synced 2026-07-28)
  - "Codex vs. Claude Code: Key Differences and When to Use Each - DataCamp" (https://www.datacamp.com/blog/codex-vs-claude-code, transcript synced 2026-07-28)
  - "An official Qdrant Model Context Protocol (MCP) server implementation - GitHub" (https://github.com/qdrant/mcp-server-qdrant, transcript synced 2026-07-28)
  - "open-compress/claw-compactor: 14-stage Fusion Pipeline for LLM token compression - GitHub" (https://github.com/open-compress/claw-compactor, transcript synced 2026-07-28)
  - "Configure permissions - Claude Code Docs" (https://code.claude.com/docs/en/permissions, transcript synced 2026-07-28)
  - "context-compression · GitHub Topics" (https://github.com/topics/context-compression?l=python&o=desc&s=updated, transcript synced 2026-07-28)
  - "Claude Code Pricing: Optimize Your Token Usage & Costs" (https://claudefa.st/blog/guide/development/usage-optimization, transcript synced 2026-07-28)
  - "GitHub - Aider-AI/aider: aider is AI pair programming in your terminal · GitHub" (https://github.com/Aider-AI/aider, transcript synced 2026-07-28)
  - "[For Beginners] What is 'ultracode,' the new feature in Claude Code? ― Tackling heavy tasks all at once with parallel agents - note" (https://note.com/tolove/n/n08cf64926fd4?hl=en-US, transcript synced 2026-07-28)
  - "Commands - Claude Code Docs" (https://code.claude.com/docs/en/commands, transcript synced 2026-07-28)
  - "Choose a permission mode - Claude Code Docs" (https://code.claude.com/docs/en/permission-modes, transcript synced 2026-07-28)
  - "Agents.md best practices · GitHub - Gist" (https://gist.github.com/0xfauzi/7c8f65572930a21efa62623557d83f6e, transcript synced 2026-07-28)
  - "40+ Claude Code Tips: From Basics to Advanced - GitHub" (https://github.com/ykdojo/claude-code-tips, transcript synced 2026-07-28)
  - "Sequential Thinking - Awesome MCP Servers" (https://mcpservers.org/servers/arben-adm/mcp-sequential-thinking, transcript synced 2026-07-28)
  - "servers/src/sequentialthinking/README.md at main · modelcontextprotocol/servers - GitHub" (https://github.com/modelcontextprotocol/servers/blob/main/src/sequentialthinking/README.md, transcript synced 2026-07-28)
  - "Claude Code vs OpenAI Codex in 2026: Which is better for daily work, agentic tasks, or teams? - Reddit" (https://www.reddit.com/r/AgentContext_dev/comments/1uk1us0/claude_code_vs_openai_codex_in_2026_which_is/, transcript synced 2026-07-28)
  - "GitHub - langchain-ai/langgraph: Build resilient agents. · GitHub" (https://github.com/langchain-ai/langgraph, transcript synced 2026-07-28)
  - "GitHub - danielsimonjr/deepthinking-mcp: Unified deep thinking MCP server combining sequential, Shannon, and mathematical reasoning with physics support · GitHub" (https://github.com/danielsimonjr/deepthinking-mcp, transcript synced 2026-07-28)
  - "Claude Code Ultracode: What It Is and When to Use It - Vibe Coding Academy" (https://www.vibecodingacademy.ai/blog/claude-code-ultracode, transcript synced 2026-07-28)
  - "[FEATURE] PostToolUse hook for agent-based large output summarization #31279 - GitHub" (https://github.com/anthropics/claude-code/issues/31279, transcript synced 2026-07-28)
  - "NotebookLM source 39fe0bf1-0490-4fe1-867e-358fa99e693a" (✳ thinking.txt, synced 2026-07-28)
  - "claude-code-tips/skills/review-claudemd/SKILL.md at main - GitHub" (https://github.com/ykdojo/claude-code-tips/blob/main/skills/review-claudemd/SKILL.md, transcript synced 2026-07-28)
  - "GitHub - OpenHands/OpenHands: 🙌 OpenHands: AI-Driven Development · GitHub" (https://github.com/All-Hands-AI/OpenHands, transcript synced 2026-07-28)
  - "danielsimonjr/MemoryJS: A TypeScript knowledge graph library for managing entities, relations, and observations with advanced search capabilities, hierarchical organization, and multiple storage backends. - GitHub" (https://github.com/danielsimonjr/memoryjs, transcript synced 2026-07-28)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-07-28)
  - "Explore the context window - Claude Code Docs" (https://code.claude.com/docs/en/context-window, transcript synced 2026-07-28)
  - "Specification - Agent Skills" (https://agentskills.io/specification, transcript synced 2026-07-28)
  - "GitHub - stanfordnlp/dspy: DSPy: The framework for programming—not prompting—language models · GitHub" (https://github.com/stanfordnlp/dspy, transcript synced 2026-07-28)
  - "GitHub - shanraisshan/claude-code-best-practice: from vibe coding to agentic engineering - practice makes claude perfect · GitHub" (https://github.com/shanraisshan/claude-code-best-practice, transcript synced 2026-07-28)
  - "Ultracode for Codex: Claude-style Dynamic Workflows with a Skill - DEV Community" (https://dev.to/pablonax/ultracode-for-codex-claude-style-dynamic-workflows-with-a-skill-3knk, transcript synced 2026-07-28)
  - "Ultrathink Mode - Claude Code 101" (https://claudecode101.com/en/tutorial/optimization/ultrathink-mode, transcript synced 2026-07-28)
  - "Ultracode in Claude Code: Effort Setting Explained" (https://claudefa.st/blog/guide/development/ultracode, transcript synced 2026-07-28)
  - "With the right skills, Codex is honestly better than Claude Code for me - Reddit" (https://www.reddit.com/r/codex/comments/1ssklf5/with_the_right_skills_codex_is_honestly_better/, transcript synced 2026-07-28)
  - "Open compress - GitHub" (https://github.com/open-compress, transcript synced 2026-07-28)
  - "distributed-systems · GitHub Topics" (https://github.com/topics/distributed-systems?l=typescript, transcript synced 2026-07-28)
  - "claude-code/plugins/plugin-dev/skills/skill-development/SKILL.md at main - GitHub" (https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md?plain=1, transcript synced 2026-07-28)
  - "GitHub - obra/superpowers: An agentic skills framework & software development methodology that works. · GitHub" (https://github.com/obra/superpowers, transcript synced 2026-07-28)
  - "GitHub - danielsimonjr/memory-mcp: Enhanced Model Context Protocol memory server with timestamps, tags, importance, search, and export capabilities · GitHub" (https://github.com/danielsimonjr/memory-mcp, transcript synced 2026-07-28)
  - "DANIEL SIMON JR danielsimonjr - GitHub" (https://github.com/danielsimonjr, transcript synced 2026-07-28)
  - "netresearch/agent-rules-skill: Agent Skill for generating AGENTS.md files following the agents.md convention | Claude Code compatible · GitHub" (https://github.com/netresearch/agents-skill, transcript synced 2026-07-28)
  - "Review Claudemd | Claude Code Skills" (https://claudemarketplaces.com/skills/ykdojo/claude-code-tips/review-claudemd, transcript synced 2026-07-28)
  - "create-plan - Skill - Smithery" (https://smithery.ai/skills/adityasanka/create-plan, transcript synced 2026-07-28)
  - "Claude Agent Skills: A First Principles Deep Dive - Han, Not Solo" (https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/, transcript synced 2026-07-28)
  - "Stop Burning Tokens: A Developer's Guide to Claude AI Token Optimization | by Mayank Jain | Level Up Coding" (https://levelup.gitconnected.com/stop-burning-tokens-a-developers-guide-to-claude-ai-token-optimization-4c70c7c52ffb, transcript synced 2026-07-28)
  - "Issues · seojoonkim/agentlinter - GitHub" (https://github.com/seojoonkim/agentlinter/issues, transcript synced 2026-07-28)
  - "Contextual compression for RAG based applications. - GitHub" (https://github.com/srgrace/contextual-compression, transcript synced 2026-07-28)
  - "GitHub - langchain-ai/deepagents: The batteries-included agent harness. · GitHub" (https://github.com/langchain-ai/deepagents, transcript synced 2026-07-28)
  - "claw-compactor · GitHub Topics" (https://github.com/topics/claw-compactor, transcript synced 2026-07-28)
  - "claude-code-tips/skills/half-clone/SKILL.md at main - GitHub" (https://github.com/ykdojo/claude-code-tips/blob/main/skills/half-clone/SKILL.md, transcript synced 2026-07-28)
  - "Orchestrate subagents at scale with dynamic workflows - Claude Code Docs" (https://code.claude.com/docs/en/workflows, transcript synced 2026-07-28)
  - "Claude Code Tips - 40+ Tips from Basics to Advanced" (https://awesomeclaude.ai/claude-code-tips, transcript synced 2026-07-28)
  - "pretooluse-hooks · GitHub Topics" (https://github.com/topics/pretooluse-hooks, transcript synced 2026-07-28)
  - "GitHub - modelcontextprotocol/servers: Model Context Protocol Servers · GitHub" (https://github.com/modelcontextprotocol/servers, transcript synced 2026-07-28)
  - "CLAUDE.md - multica-ai/andrej-karpathy-skills · GitHub" (https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md, transcript synced 2026-07-28)
  - "Claude Code by Anthropic | AI Coding Agent, Terminal, IDE" (https://claude.com/product/claude-code, transcript synced 2026-07-28)
  - "Ultracode: Claude Code Multi-Agent Orchestration Mode Explained - Developers Digest" (https://www.developersdigest.tech/blog/ultracode-effort-level-explained, transcript synced 2026-07-28)
  - "I created a /half-clone command so you can continue your conversation in Claude Code : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1q4w38p/i_created_a_halfclone_command_so_you_can_continue/, transcript synced 2026-07-28)
  - "GitHub - anthropics/skills: Public repository for Agent Skills · GitHub" (https://github.com/anthropics/skills, transcript synced 2026-07-28)
  - "Built 8 Claude Code Skills, each modeling a different human thinking pattern - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1un27ce/built_8_claude_code_skills_each_modeling_a/, transcript synced 2026-07-28)
  - "GitHub - jbabin91/super-claude · GitHub" (https://github.com/jbabin91/super-claude, transcript synced 2026-07-28)
  - "modelcontextprotocol/servers: Model Context Protocol Servers - GitHub" (https://github.com/modelcontextprotocol/servers, transcript synced 2026-07-28)
  - "How Claude remembers your project - Claude Code Docs" (https://code.claude.com/docs/en/memory, transcript synced 2026-07-28)
  - "Configure auto mode - Claude Code Docs" (https://code.claude.com/docs/en/auto-mode-config, transcript synced 2026-07-28)
  - "Claude Code Skills Structure and Usage Guide - Best practices for skill development, activation patterns, and optimization strategies" (https://gist.github.com/mellanon/50816550ecb5f3b239aa77eef7b8ed8d, transcript synced 2026-07-28)
  - "Best practices for Claude Code" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-07-28)
  - "Jonathan Haas haasonsaas - GitHub" (https://github.com/haasonsaas, transcript synced 2026-07-28)
  - "AgentLint · Actions · GitHub Marketplace" (https://github.com/marketplace/actions/agentlint, transcript synced 2026-07-28)
  - "claude-code-best-practice/best-practice/claude-skills.md at main · shanraisshan/claude-code-best-practice - GitHub" (https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md, transcript synced 2026-07-28)
  - "Week 23 · June 1–5, 2026 - Claude Code Docs" (https://code.claude.com/docs/en/whats-new/2026-w23, transcript synced 2026-07-28)
  - "Support for AGENTS.md and .agents/skills/, the community has been asking since August 2025 · Issue #31005 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/31005, transcript synced 2026-07-28)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-07-28)
  - "Model configuration - Claude Code Docs" (https://code.claude.com/docs/en/model-config, transcript synced 2026-07-28)
  - "GitHub - microsoft/graphrag: A modular graph-based Retrieval-Augmented Generation (RAG) system · GitHub" (https://github.com/microsoft/graphrag, transcript synced 2026-07-28)
  - "Agent Skills - Claude Platform Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, transcript synced 2026-07-28)
  - "evalops/deep-code-reasoning-mcp: A Model Context Protocol (MCP) server that provides advanced code analysis and reasoning capabilities powered by Google's Gemini AI - GitHub" (https://github.com/evalops/deep-code-reasoning-mcp, transcript synced 2026-07-28)
  - "Claude Code | Anthropic's agentic coding system" (https://www.anthropic.com/product/claude-code, transcript synced 2026-07-28)
  - "GitHub - evalops/deep-code-reasoning-mcp: A Model Context Protocol (MCP) server that provides advanced code analysis and reasoning capabilities powered by Google's Gemini AI · GitHub" (https://github.com/evalops/deep-code-reasoning-mcp, transcript synced 2026-07-28)
  - "Claude Code Performance: Unlock Deep Thinking for Better Results" (https://claudefa.st/blog/guide/performance/deep-thinking-techniques, transcript synced 2026-07-28)
  - "claude-skills/CLAUDE.md at main · alirezarezvani/claude-skills - GitHub" (https://github.com/alirezarezvani/claude-skills/blob/main/CLAUDE.md, transcript synced 2026-07-28)
  - "Native Claude Code hooks compatibility (PreToolUse, PostToolUse, Stop) · Issue #12472 · anomalyco/opencode - GitHub" (https://github.com/anomalyco/opencode/issues/12472, transcript synced 2026-07-28)
  - "Week 22 · May 25–29, 2026 - Claude Code Docs" (https://code.claude.com/docs/en/whats-new/2026-w22, transcript synced 2026-07-28)
  - "Manage costs effectively - Claude Code Docs" (https://code.claude.com/docs/en/costs, transcript synced 2026-07-28)
  - "GitHub - JustHereToHelp/claude-bouncer: Pattern-level command filtering for Claude Code. Blocks the dangerous stuff, asks about the risky stuff, lets the normal stuff through. · GitHub" (https://github.com/JustHereToHelp/claude-bouncer, transcript synced 2026-07-28)
  - "GitHub - froster02/mini-Brain_skills: A set of Claude Code Skills modeled after distinct human thinking patterns (brainstorm, thinking, idea, explore, create, guide, study, try). · GitHub" (https://github.com/froster02/mini-Brain_skills, transcript synced 2026-07-28)
  - "danielsimonjr/memory-mcp: Enhanced Model Context Protocol memory server with timestamps, tags, importance, search, and export capabilities - GitHub" (https://github.com/danielsimonjr/memory-mcp, transcript synced 2026-07-28)
  - "How to Use OpenAI Codex: A Developer's Guide [2026] - Scrimba" (https://scrimba.com/articles/how-to-use-openai-codex/, transcript synced 2026-07-28)
  - "Overview - Claude Code Docs" (https://code.claude.com/docs/en/overview, transcript synced 2026-07-28)
  - "Sequential Thinking MCP Server (Python Implementation) - GitHub" (https://github.com/XD3an/python-sequential-thinking-mcp, transcript synced 2026-07-28)
  - "GitHub - seojoonkim/agentlinter: ESLint for AI Agents — AGENTS.md/CLAUDE.md 채점·진단·자동수정 | Position Risk Warning · Token Efficiency · Security Check · GitHub" (https://github.com/seojoonkim/agentlinter, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-skills-and-mcp-integration
    - level: notebook
      id: e83b6a68-fedc-4757-b492-3360ae8377a2
      title: Thinking and Reasoning
      url: https://notebooklm.google.com/notebook/e83b6a68-fedc-4757-b492-3360ae8377a2
    - level: cluster
      id: 0
      name: github-https-claude
    - level: source_url
      url: https://community.openai.com/t/introducing-the-new-codex-for-almost-everything/1379125
      title: Introducing the New Codex for (almost) everything - OpenAI Developer Community
    - level: source_url
      url: https://www.datacamp.com/blog/codex-vs-claude-code
      title: Codex vs. Claude Code: Key Differences and When to Use Each - DataCamp
    - level: source_url
      url: https://github.com/qdrant/mcp-server-qdrant
      title: An official Qdrant Model Context Protocol (MCP) server implementation - GitHub
    - level: source_url
      url: https://github.com/open-compress/claw-compactor
      title: open-compress/claw-compactor: 14-stage Fusion Pipeline for LLM token compression - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/permissions
      title: Configure permissions - Claude Code Docs
    - level: source_url
      url: https://github.com/topics/context-compression?l=python&o=desc&s=updated
      title: context-compression · GitHub Topics
    - level: source_url
      url: https://claudefa.st/blog/guide/development/usage-optimization
      title: Claude Code Pricing: Optimize Your Token Usage & Costs
    - level: source_url
      url: https://github.com/Aider-AI/aider
      title: GitHub - Aider-AI/aider: aider is AI pair programming in your terminal · GitHub
    - level: source_url
      url: https://note.com/tolove/n/n08cf64926fd4?hl=en-US
      title: [For Beginners] What is 'ultracode,' the new feature in Claude Code? ― Tackling heavy tasks all at once with parallel agents - note
    - level: source_url
      url: https://code.claude.com/docs/en/commands
      title: Commands - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/permission-modes
      title: Choose a permission mode - Claude Code Docs
    - level: source_url
      url: https://gist.github.com/0xfauzi/7c8f65572930a21efa62623557d83f6e
      title: Agents.md best practices · GitHub - Gist
    - level: source_url
      url: https://github.com/ykdojo/claude-code-tips
      title: 40+ Claude Code Tips: From Basics to Advanced - GitHub
    - level: source_url
      url: https://mcpservers.org/servers/arben-adm/mcp-sequential-thinking
      title: Sequential Thinking - Awesome MCP Servers
    - level: source_url
      url: https://github.com/modelcontextprotocol/servers/blob/main/src/sequentialthinking/README.md
      title: servers/src/sequentialthinking/README.md at main · modelcontextprotocol/servers - GitHub
    - level: source_url
      url: https://www.reddit.com/r/AgentContext_dev/comments/1uk1us0/claude_code_vs_openai_codex_in_2026_which_is/
      title: Claude Code vs OpenAI Codex in 2026: Which is better for daily work, agentic tasks, or teams? - Reddit
    - level: source_url
      url: https://github.com/langchain-ai/langgraph
      title: GitHub - langchain-ai/langgraph: Build resilient agents. · GitHub
    - level: source_url
      url: https://github.com/danielsimonjr/deepthinking-mcp
      title: GitHub - danielsimonjr/deepthinking-mcp: Unified deep thinking MCP server combining sequential, Shannon, and mathematical reasoning with physics support · GitHub
    - level: source_url
      url: https://www.vibecodingacademy.ai/blog/claude-code-ultracode
      title: Claude Code Ultracode: What It Is and When to Use It - Vibe Coding Academy
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/31279
      title: [FEATURE] PostToolUse hook for agent-based large output summarization #31279 - GitHub
    - level: source_url
      url: https://github.com/ykdojo/claude-code-tips/blob/main/skills/review-claudemd/SKILL.md
      title: claude-code-tips/skills/review-claudemd/SKILL.md at main - GitHub
    - level: source_url
      url: https://github.com/All-Hands-AI/OpenHands
      title: GitHub - OpenHands/OpenHands: 🙌 OpenHands: AI-Driven Development · GitHub
    - level: source_url
      url: https://github.com/danielsimonjr/memoryjs
      title: danielsimonjr/MemoryJS: A TypeScript knowledge graph library for managing entities, relations, and observations with advanced search capabilities, hierarchical organization, and multiple storage backends. - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/skills
      title: Extend Claude with skills - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/context-window
      title: Explore the context window - Claude Code Docs
    - level: source_url
      url: https://agentskills.io/specification
      title: Specification - Agent Skills
    - level: source_url
      url: https://github.com/stanfordnlp/dspy
      title: GitHub - stanfordnlp/dspy: DSPy: The framework for programming—not prompting—language models · GitHub
    - level: source_url
      url: https://github.com/shanraisshan/claude-code-best-practice
      title: GitHub - shanraisshan/claude-code-best-practice: from vibe coding to agentic engineering - practice makes claude perfect · GitHub
    - level: source_url
      url: https://dev.to/pablonax/ultracode-for-codex-claude-style-dynamic-workflows-with-a-skill-3knk
      title: Ultracode for Codex: Claude-style Dynamic Workflows with a Skill - DEV Community
    - level: source_url
      url: https://claudecode101.com/en/tutorial/optimization/ultrathink-mode
      title: Ultrathink Mode - Claude Code 101
    - level: source_url
      url: https://claudefa.st/blog/guide/development/ultracode
      title: Ultracode in Claude Code: Effort Setting Explained
    - level: source_url
      url: https://www.reddit.com/r/codex/comments/1ssklf5/with_the_right_skills_codex_is_honestly_better/
      title: With the right skills, Codex is honestly better than Claude Code for me - Reddit
    - level: source_url
      url: https://github.com/open-compress
      title: Open compress - GitHub
    - level: source_url
      url: https://github.com/topics/distributed-systems?l=typescript
      title: distributed-systems · GitHub Topics
    - level: source_url
      url: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md?plain=1
      title: claude-code/plugins/plugin-dev/skills/skill-development/SKILL.md at main - GitHub
    - level: source_url
      url: https://github.com/obra/superpowers
      title: GitHub - obra/superpowers: An agentic skills framework & software development methodology that works. · GitHub
    - level: source_url
      url: https://github.com/danielsimonjr/memory-mcp
      title: GitHub - danielsimonjr/memory-mcp: Enhanced Model Context Protocol memory server with timestamps, tags, importance, search, and export capabilities · GitHub
    - level: source_url
      url: https://github.com/danielsimonjr
      title: DANIEL SIMON JR danielsimonjr - GitHub
    - level: source_url
      url: https://github.com/netresearch/agents-skill
      title: netresearch/agent-rules-skill: Agent Skill for generating AGENTS.md files following the agents.md convention | Claude Code compatible · GitHub
    - level: source_url
      url: https://claudemarketplaces.com/skills/ykdojo/claude-code-tips/review-claudemd
      title: Review Claudemd | Claude Code Skills
    - level: source_url
      url: https://smithery.ai/skills/adityasanka/create-plan
      title: create-plan - Skill - Smithery
    - level: source_url
      url: https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/
      title: Claude Agent Skills: A First Principles Deep Dive - Han, Not Solo
    - level: source_url
      url: https://levelup.gitconnected.com/stop-burning-tokens-a-developers-guide-to-claude-ai-token-optimization-4c70c7c52ffb
      title: Stop Burning Tokens: A Developer's Guide to Claude AI Token Optimization | by Mayank Jain | Level Up Coding
    - level: source_url
      url: https://github.com/seojoonkim/agentlinter/issues
      title: Issues · seojoonkim/agentlinter - GitHub
    - level: source_url
      url: https://github.com/srgrace/contextual-compression
      title: Contextual compression for RAG based applications. - GitHub
    - level: source_url
      url: https://github.com/langchain-ai/deepagents
      title: GitHub - langchain-ai/deepagents: The batteries-included agent harness. · GitHub
    - level: source_url
      url: https://github.com/topics/claw-compactor
      title: claw-compactor · GitHub Topics
    - level: source_url
      url: https://github.com/ykdojo/claude-code-tips/blob/main/skills/half-clone/SKILL.md
      title: claude-code-tips/skills/half-clone/SKILL.md at main - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/workflows
      title: Orchestrate subagents at scale with dynamic workflows - Claude Code Docs
    - level: source_url
      url: https://awesomeclaude.ai/claude-code-tips
      title: Claude Code Tips - 40+ Tips from Basics to Advanced
    - level: source_url
      url: https://github.com/topics/pretooluse-hooks
      title: pretooluse-hooks · GitHub Topics
    - level: source_url
      url: https://github.com/modelcontextprotocol/servers
      title: GitHub - modelcontextprotocol/servers: Model Context Protocol Servers · GitHub
    - level: source_url
      url: https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md
      title: CLAUDE.md - multica-ai/andrej-karpathy-skills · GitHub
    - level: source_url
      url: https://claude.com/product/claude-code
      title: Claude Code by Anthropic | AI Coding Agent, Terminal, IDE
    - level: source_url
      url: https://www.developersdigest.tech/blog/ultracode-effort-level-explained
      title: Ultracode: Claude Code Multi-Agent Orchestration Mode Explained - Developers Digest
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1q4w38p/i_created_a_halfclone_command_so_you_can_continue/
      title: I created a /half-clone command so you can continue your conversation in Claude Code : r/ClaudeAI - Reddit
    - level: source_url
      url: https://github.com/anthropics/skills
      title: GitHub - anthropics/skills: Public repository for Agent Skills · GitHub
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1un27ce/built_8_claude_code_skills_each_modeling_a/
      title: Built 8 Claude Code Skills, each modeling a different human thinking pattern - Reddit
    - level: source_url
      url: https://github.com/jbabin91/super-claude
      title: GitHub - jbabin91/super-claude · GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/memory
      title: How Claude remembers your project - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/auto-mode-config
      title: Configure auto mode - Claude Code Docs
    - level: source_url
      url: https://gist.github.com/mellanon/50816550ecb5f3b239aa77eef7b8ed8d
      title: Claude Code Skills Structure and Usage Guide - Best practices for skill development, activation patterns, and optimization strategies
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best practices for Claude Code
    - level: source_url
      url: https://github.com/haasonsaas
      title: Jonathan Haas haasonsaas - GitHub
    - level: source_url
      url: https://github.com/marketplace/actions/agentlint
      title: AgentLint · Actions · GitHub Marketplace
    - level: source_url
      url: https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md
      title: claude-code-best-practice/best-practice/claude-skills.md at main · shanraisshan/claude-code-best-practice - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/whats-new/2026-w23
      title: Week 23 · June 1–5, 2026 - Claude Code Docs
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/31005
      title: Support for AGENTS.md and .agents/skills/, the community has been asking since August 2025 · Issue #31005 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/model-config
      title: Model configuration - Claude Code Docs
    - level: source_url
      url: https://github.com/microsoft/graphrag
      title: GitHub - microsoft/graphrag: A modular graph-based Retrieval-Augmented Generation (RAG) system · GitHub
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
      title: Agent Skills - Claude Platform Docs
    - level: source_url
      url: https://github.com/evalops/deep-code-reasoning-mcp
      title: evalops/deep-code-reasoning-mcp: A Model Context Protocol (MCP) server that provides advanced code analysis and reasoning capabilities powered by Google's Gemini AI - GitHub
    - level: source_url
      url: https://www.anthropic.com/product/claude-code
      title: Claude Code | Anthropic's agentic coding system
    - level: source_url
      url: https://claudefa.st/blog/guide/performance/deep-thinking-techniques
      title: Claude Code Performance: Unlock Deep Thinking for Better Results
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/blob/main/CLAUDE.md
      title: claude-skills/CLAUDE.md at main · alirezarezvani/claude-skills - GitHub
    - level: source_url
      url: https://github.com/anomalyco/opencode/issues/12472
      title: Native Claude Code hooks compatibility (PreToolUse, PostToolUse, Stop) · Issue #12472 · anomalyco/opencode - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/whats-new/2026-w22
      title: Week 22 · May 25–29, 2026 - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/costs
      title: Manage costs effectively - Claude Code Docs
    - level: source_url
      url: https://github.com/JustHereToHelp/claude-bouncer
      title: GitHub - JustHereToHelp/claude-bouncer: Pattern-level command filtering for Claude Code. Blocks the dangerous stuff, asks about the risky stuff, lets the normal stuff through. · GitHub
    - level: source_url
      url: https://github.com/froster02/mini-Brain_skills
      title: GitHub - froster02/mini-Brain_skills: A set of Claude Code Skills modeled after distinct human thinking patterns (brainstorm, thinking, idea, explore, create, guide, study, try). · GitHub
    - level: source_url
      url: https://scrimba.com/articles/how-to-use-openai-codex/
      title: How to Use OpenAI Codex: A Developer's Guide [2026] - Scrimba
    - level: source_url
      url: https://code.claude.com/docs/en/overview
      title: Overview - Claude Code Docs
    - level: source_url
      url: https://github.com/XD3an/python-sequential-thinking-mcp
      title: Sequential Thinking MCP Server (Python Implementation) - GitHub
    - level: source_url
      url: https://github.com/seojoonkim/agentlinter
      title: GitHub - seojoonkim/agentlinter: ESLint for AI Agents — AGENTS.md/CLAUDE.md 채점·진단·자동수정 | Position Risk Warning · Token Efficiency · Security Check · GitHub
relations:
  - target: wiki/concepts/mcp-servers.md
    type: related
  - target: wiki/concepts/claude-code-configuration.md
    type: related
  - target: wiki/concepts/agent-skills-specification.md
    type: related
---

# Claude Code Skills and MCP Integration

## Decision context

**Definition:** Claude Code supports an extensible skills system that allows developers to define reusable skill packages, which can integrate with Model Context Protocol (MCP) servers to enhance agentic coding workflows through structured thinking patterns and specialized task execution.

Synthesized from **89 contributing transcripts** in NotebookLM notebook *Thinking and Reasoning*, clustered into the "github-https-claude" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are defined through SKILL.md files that specify metadata including name, description, and source repository information [9]
- The Agent Skills specification provides a standardized format for creating and distributing reusable skill packages across the Claude Code ecosystem [7]
- MCP servers enable structured thinking frameworks that organize thoughts through standard cognitive stages such as problem definition, research, and analysis [4]
- The Review Claudemd skill demonstrates a pattern where parallel Claude Sonnet subagents analyze conversation history to suggest improvements to CLAUDE.MD files [10]
- Skills can be installed from GitHub repositories, with public repositories like anthropics/skills serving as a central hub for shared skill packages [14]
- The skills ecosystem includes tools for code linting, analysis, and automated review workflows [11, 16]
- Model configuration allows specifying which Claude models power skills execution [17]

## Verifiable values

| Name | Value |
|---|---|
| Skill repository | `GitHub-based distribution via public repositories` |
| Skill metadata format | `SKILL.md specification format` |
| Integration protocol | `Model Context Protocol (MCP)` |

## Related concepts

- mcp-servers — MCP Servers
- claude-code-configuration — Claude Code Configuration
- agent-skills-specification — Agent Skills Specification
- parallel-agent-execution — Parallel Agent Execution

## Citations (from contributing transcripts)

- **Claim:** Skills are defined through SKILL.md files with specific metadata format
  - Source: claude-code/plugins/plugin-dev/skills/skill-development/SKILL.md at main - GitHub (`504f4cc8-b821-4567-9995-3f4014819bf0`)
  - Context: claude-code/plugins/plugin-dev/skills/skill-development/SKILL.md at main
- **Claim:** The Agent Skills specification provides standardized format for skill creation
  - Source: Specification - Agent Skills (`425a98bf-c4b5-422a-a0fd-7c38226bf502`)
  - Context: Specification - Agent Skills provides documentation for the skill creation process
- **Claim:** MCP servers enable structured thinking frameworks with cognitive stages
  - Source: Sequential Thinking - Awesome MCP Servers (`2444d3cf-e48f-4771-9ca6-36cfa8c6af75`)
  - Context: A Model Context Protocol (MCP) server that facilitates structured, progressive thinking through defined stages
- **Claim:** Review Claudemd uses parallel subagents to analyze conversation history
  - Source: Review Claudemd | Claude Code Skills (`62f1284c-a39f-4e34-bbe0-88b4c863e94a`)
  - Context: Spins up parallel Claude Sonnet subagents to analyze your conversation history and suggest improvements
- **Claim:** Anthropic maintains a public repository for sharing Agent Skills
  - Source: GitHub - anthropics/skills: Public repository for Agent Skills
  - Context: Public repository for Agent Skills
- **Claim:** AgentLint provides code linting as a GitHub Action
  - Source: AgentLint · Actions · GitHub Marketplace (`b60a356b-093c-4632-a079-31e4b91172e2`)
  - Context: AgentLint · Actions · GitHub Marketplace

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `e83b6a68-fedc-4757-b492-3360ae8377a2`
(cluster `github-https-claude`). No claims are made
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

- NotebookLM notebook [Thinking and Reasoning](https://notebooklm.google.com/notebook/e83b6a68-fedc-4757-b492-3360ae8377a2)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
