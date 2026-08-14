---
title: "'what still needs to be finished or fixed, or will cause problems or uncertaintity in
  the future?'

Are there best pr"
date: "2026-02-27"
mode: "COPILOT"
uuid: "631129c6-5120-4222-ae92-d0205bcf69d8"
entry_count: 2
---

## Human

"what still needs to be finished or fixed, or will cause problems or uncertaintity in
  the future?"

Are there best practice prompts or repos or claude skills that cover the above question?  I think I want to turn that into a custom skill for my use, but I'd like to consider what other people are doing also.

## Assistant

Your query targets a powerful self-audit for projects: surfacing unfinished work, fixes, or future risks/uncertainties. This aligns directly with your ongoing Claude Code optimizations like debugging/RCA frameworks, task management, hook reliability, and verification loops.[1]

## Relevant Repos
These GitHub repos offer production-ready Claude Code skills and configs for audits, gaps, and risks—ideal for forking into your custom skill.

| Repo | Key Features | Fit for Your Use |
|------|--------------|------------------|
| levnikolaevich/claude-code-skills | 102 skills incl. code quality audits (DRY/KISS/YAGNI), documentation audits, parallel workers for gaps.[2] | Matches your RCA/deep-dive audits; add to task workflows.[1][3] |
| travisvn/awesome-claude-skills | Curated list of skills/tools for workflows; includes task deps/blockers, security audits.[4][5] | Start here for skill inventory like your projects. |
| FlorianBruniaux/claude-code-ultimate-guide | Audit prompt.md flags gaps (e.g., no CLAUDE.md, missing hooks/agents).[6] | Directly audits "what's missing" like your cognitive frameworks.[7] |
| ChrisWiles/claude-code-showcase | Skill eval system suggests activations; hooks for quality gates (format/test/block).[8] | Boosts your hook auto-detection (THINK params, premortems). |

Install via `/skills install <repo-url>` or clone to `./claude/skills/`; test in worktrees.[9][10]

## Key Skills for Gaps/Risks
Existing skills handle exactly this—scan tasks/files/hooks for incompletes, deps, failure modes.

- **madappgang/claude-code-audit** (LobeHub): On-demand security/code quality audit for vulns, smells, compliance.[11]
- **nickcrew/claude-cortex/pre_mortem** (Playbooks): Surfaces failure modes/mitigations; outputs tasks for risks (90-day horizon).[12]
- **Dependency Analysis** (MCP/Task Orchestrator): Detects task bottlenecks, circular deps, unblocks.[13][14]
- **ln-501-code-quality-checker** (levnikolaevich): Git-diff audits for arch violations, severity-ranked issues.[2]
- **Two-Stage Code Review**: Checks spec compliance + quality gaps (tests, modularity).[15]

Pair with your task list tools (e.g., TaskGet/Update for blockers). Activate via skill-rules.json or UserPromptSubmit hooks.[10][16][17]

## Best Practice Prompts
Embed these in your custom skill prompt (e.g., as a `/project-audit` slash command). Structure: context review → gap list → risks → tasks.[18][19]

**Core Audit Prompt** (from ultimate-guide/hooks docs):
```
Review full repo/convo: List unfinished tasks, broken hooks/skills, missing deps/blockers. Flag future risks (e.g., token limits, hook failures, unverified RCA). Output: HIGH/MED/LOW issues with fixes + tasks. Check: CLAUDE.md gaps, task freshness, premortem modes.[web:37][web:42]
```

**Pre-Mortem Addition** (risk-focused):
```
Assume project fails in 90 days. List top failure modes (tech/UX/deps/compliance). Propose mitigations (S/M/L effort), owners, tasks. Prioritize via likelihood/impact matrix.[web:25][web:40]
```

**Stop Hook for Completion**:
```
On Stop/TaskCompleted: "All tasks complete? Gaps/risks? If not: {'ok':false, 'reason':'unfinished: X; risk: Y'}. Block if uncertain."[web:42][cite:2]
```

## Custom Skill Recommendation
Build `/audit-gaps` as hybrid: Invoke above skills via subagents, then synthesize with your RCA framework (SequentialThinking + graph RAG). Use UserPromptSubmit hook for auto-trigger on "status?" prompts; add sanity checks per your garbage-deletion pattern. This resolves your known gaps like PostToolUse reasoning, hook reliability.[20]

## Human

please create the best prompt for me that I can drop in and use.

## Assistant

Here’s a drop‑in prompt you can use as a Claude Code skill (or just paste into a slash command) to answer:

> “What still needs to be finished or fixed, or will cause problems or uncertainty in the future?”

You can name it `/audit_gaps` or similar.

***

**PROJECT GAPS & FUTURE RISKS AUDIT PROMPT**

You are an expert AI assistant working inside Claude Code on a live project.  
Your job is to answer one question with brutal clarity:

> “What still needs to be finished or fixed, or will cause problems or uncertainty in the future?”

Follow this process step by step:

1. **Scan context and structure your understanding**
   - Briefly summarize the current state of the project: goals, main components, and recent work.  
   - Note any explicit task lists, TODOs, or open questions you see (files, tasks list, comments, CLAUDE.md, standards, hooks, skills, etc.).[1][2]

2. **Identify unfinished or missing work**
   - List concrete items that are clearly unfinished, missing, or only partially implemented, including:  
     - Features or flows that are started but not complete  
     - Tests that are missing or incomplete  
     - Docs/CLAUDE.md/standards that are outdated, missing, or inconsistent  
     - Hooks/skills that are referenced but not implemented or not wired up  
     - Known bugs, TODO/FIXME comments, or tech debt that will cause friction soon.[3][4]
   - For each item, specify:  
     - What is missing or incomplete  
     - Where it lives (file, directory, task id, or component)  
     - Why it matters.

3. **Analyze dependencies, blockers, and bottlenecks**
   - Identify tasks, components, or skills that depend on other work being finished first.  
   - Call out explicit blockers (e.g., “cannot safely use this skill until exit codes are fixed”, “feature depends on X library upgrade”).[5][6]
   - Highlight any hidden bottlenecks: single points of failure, fragile hooks, or manual steps that will not scale.[7]

4. **Run a pre‑mortem (future problems & uncertainties)**
   - Imagine it is 3–6 months from now and this project has run into serious problems or failed.  
   - Answer **only** these questions, with no reassurance or balancing:  
     - What went wrong technically?  
     - What went wrong in process or workflow (tasks, hooks, skills, CLAUDE.md usage)?  
     - What important assumptions turned out to be wrong or untested?  
   - Be specific and **do not** soften or hedge; this is a pre‑mortem, not a sales pitch.[8][9][10]

5. **Prioritize and classify**
   - For every unfinished item or risk, assign:  
     - Priority: HIGH / MEDIUM / LOW  
     - Type: Feature gap, Test gap, Documentation gap, Hook/Skill gap, Task/process gap, Security/Compliance, Other.[11][3]
   - Briefly justify each HIGH priority: what could break, who it affects, and how soon.

6. **Propose concrete next actions**
   - Output a short, ordered list of the **top 5–10 next actions** that would most reduce risk or uncertainty and move the project toward a stable “done” state.  
   - For each action, include:  
     - One‑line description  
     - Suggested owner role (e.g., “AI agent”, “human dev”, “infra/ops”)  
     - Suggested verification method (test, script, manual check, code review, etc.).[12][2]

7. **Deliverable format**
   - Respond **only** in this structure:

   ```
   # Project Snapshot
   - Current goal:
   - Main components:
   - Recent or ongoing work:

   # Unfinished or Missing Work
   - [Priority] [Type] – What/where, why it matters
   - ...

   # Dependencies, Blockers, Bottlenecks
   - [Priority] – Description, dependent items, impact
   - ...

   # Pre‑Mortem: What Could Go Wrong
   - Technical failures:
   - Process/workflow failures:
   - Wrong or untested assumptions:

   # Top Next Actions (5–10)
   1. [Priority] Action – owner role – verification method
   2. ...
   ```

   - If information is missing (e.g., no CLAUDE.md, no task list, no tests), explicitly call this out as a **gap**, not as an unknown.[4][3]

***

If you want, I can now wrap this into a full Claude Code skill spec (JSON/YAML) wired to your tasks list and hooks so it auto-runs from a `/audit_gaps` slash command.
