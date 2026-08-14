---
title: "' feature-dev @ claude-plugins-official
 Scope: user
 Comprehensive feature development workflow with specialized agen"
date: "2026-03-04"
mode: "COPILOT"
uuid: "764e1c4f-74e8-46ec-8444-ae61bd477734"
entry_count: 1
---

## Human

" feature-dev @ claude-plugins-official
 Scope: user
 Comprehensive feature development workflow with specialized agents for codebase exploration, architecture design, and quality review

 Author: Anthropic
 Status: Enabled

 Installed components:
 • Commands: feature-dev
 • Agents: code-architect, code-explorer, code-reviewer"

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

## Assistant

The feature-dev plugin in Claude Code provides a structured 7-phase workflow for developing medium-complexity features, leveraging specialized agents like code-explorer, code-architect, and code-reviewer. It excels at tasks requiring codebase analysis, design decisions, and multi-file changes, outperforming ad-hoc prompting by enforcing checkpoints for human approval.[1][2][3]

## Best Use Cases
- Adding new API endpoints, OAuth authentication, or business logic where scope includes validation, errors, and integrations—Phase 2 explores relevant code patterns automatically.[3][1]
- Building UI components or modules like notifications/pagination, as agents match existing styles and propose balanced designs in Phase 4.[3]
- Prototyping features or extending unfamiliar codebases, using early phases for discovery and exploration without full implementation commitment.[3]
- Avoid for trivial edits (e.g., typos) or massive refactors—break large ones into bounded stages instead.[1][3]

## Maximizing Value
Start from a clean repo state (commit/stash changes) and invoke with a concise description: `/feature-dev Add rate limiting to API endpoints`.[1][3]
Engage deeply in Phase 3 (clarifying questions on edges/performance) and Phase 4 (pick from 2-3 architecture options, e.g., reuse vs. clean design)—concrete answers prevent drift.[3]
Maintain an up-to-date CLAUDE.md with conventions/tests; review Phase 6's 80%+ confidence issues before committing; run iteratively for multi-stage features.[1][3]

| Phase | Focus | Agent Used | Your Role |
|-------|--------|------------|-----------|
| 1: Discovery | Clarify requirements | None | Approve problem statement |
| 2: Exploration | Map codebase/files | code-explorer (parallel) | Review findings |
| 3: Questions | Fill gaps (edges/auth) | None | Answer specifically |
| 4: Design | Propose approaches | code-architect (parallel) | Select option |
| 5: Implement | Code changes | None | N/A (post-approval) |
| 6: Review | Bugs/style/confidence-filtered issues | code-reviewer (parallel) | Decide fixes |
| 7: Summary | Docs/next steps | None | Final check[3][1] |
