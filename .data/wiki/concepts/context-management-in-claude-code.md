---
title: "Context Management in Claude Code"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Context management in Claude Code refers to the practice of curating and controlling what information the AI model retains during coding sessions, since the system operates with finite token limits that can become insufficient for large projects.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 946158e8-0781-49b9-82ea-b8b414722d20" (Claude Code - Context Memory and Search, synced 2026-07-28)
  - "How Claude remembers your project - Claude Code Docs" (https://code.claude.com/docs/en/memory, transcript synced 2026-07-28)
  - "The Best AI Code Review Tools of 2026 - DEV Community" (https://dev.to/heraldofsolace/the-best-ai-code-review-tools-of-2026-2mb3, transcript synced 2026-07-28)
  - "Cody - better, faster, stronger | Sourcegraph Blog" (https://sourcegraph.com/blog/cody-better-faster-stronger, transcript synced 2026-07-28)
  - "Cody for VS Code v1.20: New chat UX plus automatic context retrieval | Sourcegraph Blog" (https://sourcegraph.com/blog/cody-vscode-1-20-0-release, transcript synced 2026-07-28)
  - "The Complete Guide to Claude Code V3: LSP, CLAUDE.md, MCP, Skills & Hooks — Now With IDE-Level Code Intelligence : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1qe239d/the_complete_guide_to_claude_code_v3_lsp_claudemd/, transcript synced 2026-07-28)
  - "Context Window Guide - Cline Documentation" (https://docs.cline.bot/model-config/context-windows, transcript synced 2026-07-28)
  - "What is Claude Code in 2026? - Tech Jacks Solutions" (https://techjacksolutions.com/development/tools-development/what-is-claude-code-2/, transcript synced 2026-07-28)
  - "Sourcegraph Cody vs Qodo (2026): Code Search vs Review Gates" (https://www.augmentcode.com/tools/sourcegraph-cody-vs-qodo, transcript synced 2026-07-28)
  - "On RAG Applications: From Theory to Enterprise Setups - barrahome.org" (https://barrahome.org/2026/02/19/rag-from-theory-to-enterprise.md, transcript synced 2026-07-28)
  - "Mastering Claude's Context Window: A 2025 Deep Dive - Sparkco" (https://sparkco.ai/blog/mastering-claudes-context-window-a-2025-deep-dive, transcript synced 2026-07-28)
  - "Common workflows - Claude Code Docs" (https://code.claude.com/docs/en/common-workflows, transcript synced 2026-07-28)
  - "Building Knowledge Graphs With Claude and Neo4j: A No-Code MCP Approach" (https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/, transcript synced 2026-07-28)
  - "What I Learned Building a Memory System for My Coding Agent : r/ClaudeCode - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1r1w397/what_i_learned_building_a_memory_system_for_my/, transcript synced 2026-07-28)
  - "LLM Leaderboard - Vellum AI" (https://vellum.ai/llm-leaderboard, transcript synced 2026-07-28)
  - "What Is AI Agent Memory? | IBM" (https://www.ibm.com/think/topics/ai-agent-memory, transcript synced 2026-07-28)
  - "Developer Quick Reference - Greptile" (https://www.greptile.com/docs/developer-quick-reference, transcript synced 2026-07-28)
  - "How Cody understands your codebase | Sourcegraph Blog" (https://sourcegraph.com/blog/how-cody-understands-your-codebase, transcript synced 2026-07-28)
  - "Claude 3.7 Sonnet and Claude Code - Anthropic" (https://www.anthropic.com/news/claude-3-7-sonnet, transcript synced 2026-07-28)
  - "Discover and install prebuilt plugins through marketplaces - Claude Code Docs" (https://code.claude.com/docs/en/discover-plugins, transcript synced 2026-07-28)
  - "danielrosehill/Claude-Code-Security-Auditor - GitHub" (https://github.com/danielrosehill/Claude-Code-Security-Auditor, transcript synced 2026-07-28)
  - "Features overview - Claude API Docs" (https://platform.claude.com/docs/en/build-with-claude/overview, transcript synced 2026-07-28)
  - "Sourcegraph Cody Alternatives: 7 Enterprise AI Code Assistants for Development Teams" (https://www.augmentcode.com/tools/sourcegraph-cody-alternatives-7-enterprise-ai-code-assistants-for-development-teams, transcript synced 2026-07-28)
  - "Raising the bar on SWE-bench Verified with Claude 3.5 Sonnet - Anthropic" (https://www.anthropic.com/research/swe-bench-sonnet, transcript synced 2026-07-28)
  - "Anatomy of a Claude Code Session - What Happens Under the Hood" (https://codewithmukesh.com/blog/anatomy-claude-code-session/, transcript synced 2026-07-28)
  - "NotebookLM source 4d919719-7f65-4780-823c-4c55063521bb" (Claude Code Session Chain Optimization, synced 2026-07-28)
  - "How are you guys managing context in Claude Code? 200K just ain't cutting it. - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1rrkv0h/how_are_you_guys_managing_context_in_claude_code/, transcript synced 2026-07-28)
  - "The Top Ten GitHub Agentic AI Repositories in 2025 | by ODSC - Open Data Science" (https://odsc.medium.com/the-top-ten-github-agentic-ai-repositories-in-2025-1a1440fe50c5, transcript synced 2026-07-28)
  - "Best Practices for Claude Code - Claude Code Docs" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-07-28)
  - "Using Claude Code for academic research at scale (AKA The Agents Research Lab) : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1qas3bd/using_claude_code_for_academic_research_at_scale/, transcript synced 2026-07-28)
  - "SWE-bench - Vals AI" (https://www.vals.ai/benchmarks/swebench, transcript synced 2026-07-28)
  - "Cursor vs Sourcegraph Cody: Embeddings and Monorepo at Scale | Augment Code" (https://www.augmentcode.com/tools/cursor-vs-sourcegraph-cody-embeddings-and-monorepo-scale, transcript synced 2026-07-28)
  - "Inside Claude Code's Web Tools: WebFetch vs WebSearch | Mikhail Shilkov" (https://mikhail.io/2025/10/claude-code-web-tools/, transcript synced 2026-07-28)
  - "DeepCode: Open Agentic Coding (Paper2Code & Text2Web & Text2Backend) - GitHub" (https://github.com/HKUDS/DeepCode, transcript synced 2026-07-28)
  - "Graph-based Codebase Context - Greptile" (https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context, transcript synced 2026-07-28)
  - "Scale Labs Leaderboard: SWE-Bench Pro (Public Dataset)" (https://labs.scale.com/leaderboard/swe_bench_pro_public, transcript synced 2026-07-28)
  - "CLI reference - Claude Code Docs" (https://code.claude.com/docs/en/cli-reference, transcript synced 2026-07-28)
  - "Subagents: Why you should probably be using them more : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1pz3c6v/subagents_why_you_should_probably_be_using_them/, transcript synced 2026-07-28)
  - "What Is the Context Window Limit in Claude Code? How to Manage It for Better Results" (https://www.mindstudio.ai/blog/claude-code-context-window-limit-management, transcript synced 2026-07-28)
  - "Claude Code Best Practices: Planning, Context Transfer, TDD - DataCamp" (https://www.datacamp.com/tutorial/claude-code-best-practices, transcript synced 2026-07-28)
  - "Prompting best practices - Claude API Docs" (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices, transcript synced 2026-07-28)
  - "Cline: The Collaborative AI Coder | Summary & Key Insights | Summify" (https://summify.io/discover/cline-the-collaborative-ai-coder-uIKmG3/, transcript synced 2026-07-28)
  - "Supercharging Claude Code with the Right (CLI) Tools | (think)" (https://batsov.com/articles/2026/02/17/supercharging-claude-code-with-the-right-tools/, transcript synced 2026-07-28)
  - "Claude Code Tools" (https://blog.thepete.net/claude-code-tools/, transcript synced 2026-07-28)
  - "Claude Code has amnesia. Good docs are the cure. - PhotoStructure" (https://photostructure.com/coding/claude-code-tpp/, transcript synced 2026-07-28)
  - "Modernizing Legacy Enterprise Code with Claude Code | Juteq Insights" (https://juteq.ca/insights/blog/modernizing-legacy-code-with-claude-code, transcript synced 2026-07-28)
  - "GitHub - raphaelmansuy/edgequake: High-performance GraphRAG inspired from LightRag written in Rust" (https://github.com/raphaelmansuy/edgequake, transcript synced 2026-07-28)
  - "PSA: Agent Teams ≠ Subagents - here's the actual difference : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1qwwadp/psa_agent_teams_subagents_heres_the_actual/, transcript synced 2026-07-28)
  - "Mastering Context Management in Claude Code CLI: Your Guide to Efficient AI-Assisted Coding - Lalatendu Keshari Swain" (https://lalatenduswain.medium.com/mastering-context-management-in-claude-code-cli-your-guide-to-efficient-ai-assisted-coding-83753129b28e, transcript synced 2026-07-28)
  - "hesreallyhim/awesome-claude-code: A curated list of ... - GitHub" (https://github.com/hesreallyhim/awesome-claude-code, transcript synced 2026-07-28)
  - "AI Code Review | Greptile | Merge 4X Faster, Catch 3X More Bugs" (https://www.greptile.com/code-context, transcript synced 2026-07-28)
  - "memory-graph/memory-graph: A graph DB-based MCP ... - GitHub" (https://github.com/memory-graph/memory-graph, transcript synced 2026-07-28)
  - "12 Proven Techniques to Save Tokens in Claude Code - Aslam Doctor" (https://aslamdoctor.com/12-proven-techniques-to-save-tokens-in-claude-code/, transcript synced 2026-07-28)
  - "Best AI Agent Memory Systems in 2026: 8 Frameworks Compared - Vectorize" (https://vectorize.io/articles/best-ai-agent-memory-systems, transcript synced 2026-07-28)
  - "Understanding Claude Code's Two Internet Search Methods: Built-in WebSearch vs. 6 Major MCP Search Plugins Comparison Guide" (https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html, transcript synced 2026-07-28)
  - "Web Search - LibreChat - Mintlify" (https://mintlify.com/danny-avila/librechat/features/web-search, transcript synced 2026-07-28)
  - "Leveling Up Secure Code Reviews with Claude Code - SpecterOps" (https://specterops.io/blog/2026/03/26/leveling-up-secure-code-reviews-with-claude-code/, transcript synced 2026-07-28)
  - "Repo Map - Awesome MCP Servers" (https://mcpservers.org/servers/pdavis68/RepoMapper, transcript synced 2026-07-28)
  - "Legacy Code Migration with Machine Learning: Patterns That Preserve Architecture While Modernizing" (https://www.augmentcode.com/guides/legacy-code-migration-with-machine-learning-patterns-that-preserve-architecture-while-modernizing, transcript synced 2026-07-28)
  - "Building an agentic memory system for GitHub Copilot" (https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/, transcript synced 2026-07-28)
  - "NotebookLM source d5e05b03-8ffc-4c6a-8792-2d484ca194b0" (Advanced Methodologies for Agentic Research and Autonomous Search Optimization in Claude Code, synced 2026-07-28)
  - "Repository map - Aider" (https://aider.chat/docs/repomap.html, transcript synced 2026-07-28)
  - "Claude Code overview - Claude Code Docs" (https://code.claude.com/docs/en/overview, transcript synced 2026-07-28)
  - "Feature: PageRank Repo Map — Automatic Codebase Context Selection via Symbol Graph (inspired by Aider) · Issue #535 · NousResearch/hermes-agent - GitHub" (https://github.com/NousResearch/hermes-agent/issues/535, transcript synced 2026-07-28)
  - "Claude Code + Step 3.5 Flash Best Practices Guide - GitHub" (https://github.com/stepfun-ai/Step-3.5-Flash/blob/main/cookbooks/claude-code-best-practices/README.en.md, transcript synced 2026-07-28)
  - "Understanding Claude Code's Context Window - Damian Galarza" (https://www.damiangalarza.com/posts/2025-12-08-understanding-claude-code-context-window/, transcript synced 2026-07-28)
  - "Claude CLI Automation | CodeSignal Learn" (https://codesignal.com/learn/courses/skills-plugins-cli-automation/lessons/claude-cli-automation, transcript synced 2026-07-28)
  - "Bash tool - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool, transcript synced 2026-07-28)
  - "NotebookLM source e7e9d516-57ef-460d-8d47-bf2922e6b392" (Evolutionary Architectures of Contextual Retrieval and Memory in Agentic Coding Systems, synced 2026-07-28)
  - "RAG vs GraphRAG: Shared Goal & Key Differences - Memgraph" (https://memgraph.com/blog/rag-vs-graphrag, transcript synced 2026-07-28)
  - "Exploring Anthropic's Memory Tool - Leonie Monigatti" (https://www.leoniemonigatti.com/blog/claude-memory-tool.html, transcript synced 2026-07-28)
  - "Security Components - Claude Code Templates - Mintlify" (https://www.mintlify.com/davila7/claude-code-templates/categories/security, transcript synced 2026-07-28)
  - "Claude Code and COBOL modernization: What's the reality? | Thoughtworks United States" (https://www.thoughtworks.com/en-us/insights/articles/claude-code-cobol-modernization-reality, transcript synced 2026-07-28)
  - "Memory tool - Claude API Docs - Claude Console" (https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: context-management-in-claude-code
    - level: notebook
      id: 946158e8-0781-49b9-82ea-b8b414722d20
      title: Claude Code - Context Memory and Search
      url: https://notebooklm.google.com/notebook/946158e8-0781-49b9-82ea-b8b414722d20
    - level: cluster
      id: 0
      name: https-claude-code
    - level: source_url
      url: https://code.claude.com/docs/en/memory
      title: How Claude remembers your project - Claude Code Docs
    - level: source_url
      url: https://dev.to/heraldofsolace/the-best-ai-code-review-tools-of-2026-2mb3
      title: The Best AI Code Review Tools of 2026 - DEV Community
    - level: source_url
      url: https://sourcegraph.com/blog/cody-better-faster-stronger
      title: Cody - better, faster, stronger | Sourcegraph Blog
    - level: source_url
      url: https://sourcegraph.com/blog/cody-vscode-1-20-0-release
      title: Cody for VS Code v1.20: New chat UX plus automatic context retrieval | Sourcegraph Blog
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1qe239d/the_complete_guide_to_claude_code_v3_lsp_claudemd/
      title: The Complete Guide to Claude Code V3: LSP, CLAUDE.md, MCP, Skills & Hooks — Now With IDE-Level Code Intelligence : r/ClaudeAI - Reddit
    - level: source_url
      url: https://docs.cline.bot/model-config/context-windows
      title: Context Window Guide - Cline Documentation
    - level: source_url
      url: https://techjacksolutions.com/development/tools-development/what-is-claude-code-2/
      title: What is Claude Code in 2026? - Tech Jacks Solutions
    - level: source_url
      url: https://www.augmentcode.com/tools/sourcegraph-cody-vs-qodo
      title: Sourcegraph Cody vs Qodo (2026): Code Search vs Review Gates
    - level: source_url
      url: https://barrahome.org/2026/02/19/rag-from-theory-to-enterprise.md
      title: On RAG Applications: From Theory to Enterprise Setups - barrahome.org
    - level: source_url
      url: https://sparkco.ai/blog/mastering-claudes-context-window-a-2025-deep-dive
      title: Mastering Claude's Context Window: A 2025 Deep Dive - Sparkco
    - level: source_url
      url: https://code.claude.com/docs/en/common-workflows
      title: Common workflows - Claude Code Docs
    - level: source_url
      url: https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/
      title: Building Knowledge Graphs With Claude and Neo4j: A No-Code MCP Approach
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1r1w397/what_i_learned_building_a_memory_system_for_my/
      title: What I Learned Building a Memory System for My Coding Agent : r/ClaudeCode - Reddit
    - level: source_url
      url: https://vellum.ai/llm-leaderboard
      title: LLM Leaderboard - Vellum AI
    - level: source_url
      url: https://www.ibm.com/think/topics/ai-agent-memory
      title: What Is AI Agent Memory? | IBM
    - level: source_url
      url: https://www.greptile.com/docs/developer-quick-reference
      title: Developer Quick Reference - Greptile
    - level: source_url
      url: https://sourcegraph.com/blog/how-cody-understands-your-codebase
      title: How Cody understands your codebase | Sourcegraph Blog
    - level: source_url
      url: https://www.anthropic.com/news/claude-3-7-sonnet
      title: Claude 3.7 Sonnet and Claude Code - Anthropic
    - level: source_url
      url: https://code.claude.com/docs/en/discover-plugins
      title: Discover and install prebuilt plugins through marketplaces - Claude Code Docs
    - level: source_url
      url: https://github.com/danielrosehill/Claude-Code-Security-Auditor
      title: danielrosehill/Claude-Code-Security-Auditor - GitHub
    - level: source_url
      url: https://platform.claude.com/docs/en/build-with-claude/overview
      title: Features overview - Claude API Docs
    - level: source_url
      url: https://www.augmentcode.com/tools/sourcegraph-cody-alternatives-7-enterprise-ai-code-assistants-for-development-teams
      title: Sourcegraph Cody Alternatives: 7 Enterprise AI Code Assistants for Development Teams
    - level: source_url
      url: https://www.anthropic.com/research/swe-bench-sonnet
      title: Raising the bar on SWE-bench Verified with Claude 3.5 Sonnet - Anthropic
    - level: source_url
      url: https://codewithmukesh.com/blog/anatomy-claude-code-session/
      title: Anatomy of a Claude Code Session - What Happens Under the Hood
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1rrkv0h/how_are_you_guys_managing_context_in_claude_code/
      title: How are you guys managing context in Claude Code? 200K just ain't cutting it. - Reddit
    - level: source_url
      url: https://odsc.medium.com/the-top-ten-github-agentic-ai-repositories-in-2025-1a1440fe50c5
      title: The Top Ten GitHub Agentic AI Repositories in 2025 | by ODSC - Open Data Science
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best Practices for Claude Code - Claude Code Docs
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1qas3bd/using_claude_code_for_academic_research_at_scale/
      title: Using Claude Code for academic research at scale (AKA The Agents Research Lab) : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.vals.ai/benchmarks/swebench
      title: SWE-bench - Vals AI
    - level: source_url
      url: https://www.augmentcode.com/tools/cursor-vs-sourcegraph-cody-embeddings-and-monorepo-scale
      title: Cursor vs Sourcegraph Cody: Embeddings and Monorepo at Scale | Augment Code
    - level: source_url
      url: https://mikhail.io/2025/10/claude-code-web-tools/
      title: Inside Claude Code's Web Tools: WebFetch vs WebSearch | Mikhail Shilkov
    - level: source_url
      url: https://github.com/HKUDS/DeepCode
      title: DeepCode: Open Agentic Coding (Paper2Code & Text2Web & Text2Backend) - GitHub
    - level: source_url
      url: https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context
      title: Graph-based Codebase Context - Greptile
    - level: source_url
      url: https://labs.scale.com/leaderboard/swe_bench_pro_public
      title: Scale Labs Leaderboard: SWE-Bench Pro (Public Dataset)
    - level: source_url
      url: https://code.claude.com/docs/en/cli-reference
      title: CLI reference - Claude Code Docs
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1pz3c6v/subagents_why_you_should_probably_be_using_them/
      title: Subagents: Why you should probably be using them more : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.mindstudio.ai/blog/claude-code-context-window-limit-management
      title: What Is the Context Window Limit in Claude Code? How to Manage It for Better Results
    - level: source_url
      url: https://www.datacamp.com/tutorial/claude-code-best-practices
      title: Claude Code Best Practices: Planning, Context Transfer, TDD - DataCamp
    - level: source_url
      url: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
      title: Prompting best practices - Claude API Docs
    - level: source_url
      url: https://summify.io/discover/cline-the-collaborative-ai-coder-uIKmG3/
      title: Cline: The Collaborative AI Coder | Summary & Key Insights | Summify
    - level: source_url
      url: https://batsov.com/articles/2026/02/17/supercharging-claude-code-with-the-right-tools/
      title: Supercharging Claude Code with the Right (CLI) Tools | (think)
    - level: source_url
      url: https://blog.thepete.net/claude-code-tools/
      title: Claude Code Tools
    - level: source_url
      url: https://photostructure.com/coding/claude-code-tpp/
      title: Claude Code has amnesia. Good docs are the cure. - PhotoStructure
    - level: source_url
      url: https://juteq.ca/insights/blog/modernizing-legacy-code-with-claude-code
      title: Modernizing Legacy Enterprise Code with Claude Code | Juteq Insights
    - level: source_url
      url: https://github.com/raphaelmansuy/edgequake
      title: GitHub - raphaelmansuy/edgequake: High-performance GraphRAG inspired from LightRag written in Rust
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1qwwadp/psa_agent_teams_subagents_heres_the_actual/
      title: PSA: Agent Teams ≠ Subagents - here's the actual difference : r/ClaudeAI - Reddit
    - level: source_url
      url: https://lalatenduswain.medium.com/mastering-context-management-in-claude-code-cli-your-guide-to-efficient-ai-assisted-coding-83753129b28e
      title: Mastering Context Management in Claude Code CLI: Your Guide to Efficient AI-Assisted Coding - Lalatendu Keshari Swain
    - level: source_url
      url: https://github.com/hesreallyhim/awesome-claude-code
      title: hesreallyhim/awesome-claude-code: A curated list of ... - GitHub
    - level: source_url
      url: https://www.greptile.com/code-context
      title: AI Code Review | Greptile | Merge 4X Faster, Catch 3X More Bugs
    - level: source_url
      url: https://github.com/memory-graph/memory-graph
      title: memory-graph/memory-graph: A graph DB-based MCP ... - GitHub
    - level: source_url
      url: https://aslamdoctor.com/12-proven-techniques-to-save-tokens-in-claude-code/
      title: 12 Proven Techniques to Save Tokens in Claude Code - Aslam Doctor
    - level: source_url
      url: https://vectorize.io/articles/best-ai-agent-memory-systems
      title: Best AI Agent Memory Systems in 2026: 8 Frameworks Compared - Vectorize
    - level: source_url
      url: https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html
      title: Understanding Claude Code's Two Internet Search Methods: Built-in WebSearch vs. 6 Major MCP Search Plugins Comparison Guide
    - level: source_url
      url: https://mintlify.com/danny-avila/librechat/features/web-search
      title: Web Search - LibreChat - Mintlify
    - level: source_url
      url: https://specterops.io/blog/2026/03/26/leveling-up-secure-code-reviews-with-claude-code/
      title: Leveling Up Secure Code Reviews with Claude Code - SpecterOps
    - level: source_url
      url: https://mcpservers.org/servers/pdavis68/RepoMapper
      title: Repo Map - Awesome MCP Servers
    - level: source_url
      url: https://www.augmentcode.com/guides/legacy-code-migration-with-machine-learning-patterns-that-preserve-architecture-while-modernizing
      title: Legacy Code Migration with Machine Learning: Patterns That Preserve Architecture While Modernizing
    - level: source_url
      url: https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/
      title: Building an agentic memory system for GitHub Copilot
    - level: source_url
      url: https://aider.chat/docs/repomap.html
      title: Repository map - Aider
    - level: source_url
      url: https://code.claude.com/docs/en/overview
      title: Claude Code overview - Claude Code Docs
    - level: source_url
      url: https://github.com/NousResearch/hermes-agent/issues/535
      title: Feature: PageRank Repo Map — Automatic Codebase Context Selection via Symbol Graph (inspired by Aider) · Issue #535 · NousResearch/hermes-agent - GitHub
    - level: source_url
      url: https://github.com/stepfun-ai/Step-3.5-Flash/blob/main/cookbooks/claude-code-best-practices/README.en.md
      title: Claude Code + Step 3.5 Flash Best Practices Guide - GitHub
    - level: source_url
      url: https://www.damiangalarza.com/posts/2025-12-08-understanding-claude-code-context-window/
      title: Understanding Claude Code's Context Window - Damian Galarza
    - level: source_url
      url: https://codesignal.com/learn/courses/skills-plugins-cli-automation/lessons/claude-cli-automation
      title: Claude CLI Automation | CodeSignal Learn
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool
      title: Bash tool - Claude API Docs
    - level: source_url
      url: https://memgraph.com/blog/rag-vs-graphrag
      title: RAG vs GraphRAG: Shared Goal & Key Differences - Memgraph
    - level: source_url
      url: https://www.leoniemonigatti.com/blog/claude-memory-tool.html
      title: Exploring Anthropic's Memory Tool - Leonie Monigatti
    - level: source_url
      url: https://www.mintlify.com/davila7/claude-code-templates/categories/security
      title: Security Components - Claude Code Templates - Mintlify
    - level: source_url
      url: https://www.thoughtworks.com/en-us/insights/articles/claude-code-cobol-modernization-reality
      title: Claude Code and COBOL modernization: What's the reality? | Thoughtworks United States
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
      title: Memory tool - Claude API Docs - Claude Console
relations:
  - target: wiki/concepts/ai-agent-memory.md
    type: related
  - target: wiki/concepts/subagents.md
    type: related
  - target: wiki/concepts/token-optimization.md
    type: related
---

# Context Management in Claude Code

## Decision context

**Definition:** Context management in Claude Code refers to the practice of curating and controlling what information the AI model retains during coding sessions, since the system operates with finite token limits that can become insufficient for large projects.

Synthesized from **73 contributing transcripts** in NotebookLM notebook *Claude Code - Context Memory and Search*, clustered into the "https-claude-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Claude Code sessions are temporary by design, similar to working with an intern whose knowledge resets between sessions (Source 13)
- Context windows in Claude Code have practical limits that practitioners report as insufficient for large codebases, with reports of 200K tokens not being enough (Source 8)
- Documentation serves as an externalized memory mechanism, allowing subsequent sessions to feel like continuations rather than fresh starts (Source 13)
- The /plan mode approach enables developers to establish project context before committing to execution, with /handoff available to transfer state between sessions (Source 13)
- Subagents provide a method for distributing workload across specialized AI instances rather than relying on a single continuous context (Source 11)
- Context management strategies include loading only relevant project files, avoiding unnecessary context堆积, and using focused prompts for specific tasks (Source 15)
- Token conservation techniques involve selecting appropriate model tiers for task complexity rather than defaulting to the most capable model (Source 15)

## Verifiable values

| Name | Value |
|---|---|
| Reported Context Limit | `200K tokens (reported insufficient by practitioners)` |
| Session Behavior | `temporary context that resets between sessions` |

## Related concepts

- [[ai-agent-memory]] — AI Agent Memory
- [[subagents]] — Subagents
- [[token-optimization]] — Token Optimization
- [[codebase-context-selection]] — Codebase Context Selection

## Citations (from contributing transcripts)

- **Claim:** Claude Code sessions reset between interactions, requiring documentation as externalized memory
  - Source: Claude Code has amnesia. Good docs are the cure. - PhotoStructure (`973fac71-02de-43b6-951e-eacfc6e16b63`)
  - Context: Every Claude Code session is much like a good intern: earnest, but temporary. Thoughtfully constructed documentation makes the next session feel like a continuation rather than a restart.
- **Claim:** Context window limits are reported as insufficient for large projects
  - Source: How are you guys managing context in Claude Code? 200K just ain't cutting it. - Reddit (`539804af-aea4-459c-a4eb-9fdf5f1f139b`)
  - Context: How are you guys managing context in Claude Code? 200K just ain't cutting it.
- **Claim:** Subagents offer an approach to distributing workload across multiple AI instances
  - Source: Subagents: Why you should probably be using them more : r/ClaudeAI - Reddit (`7dcffd5d-5b37-43e3-bec1-167fdd3a66b1`)
  - Context: Subagents: Why you should probably be using them more
- **Claim:** Token conservation involves selecting appropriate model tiers and avoiding unnecessary context accumulation
  - Source: 12 Proven Techniques to Save Tokens in Claude Code - Aslam Doctor (`bb418583-1ee1-4f59-a9f0-6346d288851b`)
  - Context: most developers burn through tokens unnecessarily. We load massive contexts when we don't need to. We use powerful models for simple tasks.
- **Claim:** The /plan mode and /handoff pattern enable establishing and transferring project context
  - Source: Claude Code has amnesia. Good docs are the cure. - PhotoStructure (`973fac71-02de-43b6-951e-eacfc6e16b63`)
  - Context: Start a new feature in plan mode. Wait for claude to cook. Once the plan is ready, hit escape, and run /handoff

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `946158e8-0781-49b9-82ea-b8b414722d20`
(cluster `https-claude-code`). No claims are made
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

- NotebookLM notebook [Claude Code - Context Memory and Search](https://notebooklm.google.com/notebook/946158e8-0781-49b9-82ea-b8b414722d20)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
