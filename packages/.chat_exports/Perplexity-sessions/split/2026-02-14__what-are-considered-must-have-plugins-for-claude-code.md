---
title: "what are considered must have plugins for claude code?"
date: "2026-02-14"
mode: "COPILOT"
uuid: "360d87fe-a539-4c2a-9d95-a8cda20c13f6"
entry_count: 2
---

## Human

what are considered must have plugins for claude code?

## Assistant

For most people there isn’t one universal “must have” stack, but there is a very common core: a type-aware LSP, security scanner, context/doc fetcher, browser testing, and at least one “meta” plugin pack for agents and workflows.[1][2][3][4]

## Core “must have” plugins

These are the ones that show up over and over in curated lists and experienced-user threads.[2][3][5][4][1]

- **typescript-lsp** – Proper TypeScript language server inside Claude Code, with real type checking, diagnostics, and go‑to definitions; this dramatically improves TS refactors and large TS codebases.[2]
- **security-guidance** – Runs lightweight security scans while you or Claude write code, catching hardcoded secrets, auth issues, and injection risks in real projects.[1][2]
- **Context7 / context7** – On‑demand, up‑to‑date API and library docs so you’re not stuck on stale context; people use it specifically to pull fresh REST/SDK docs while coding.[1][2]
- **Playwright** – Natural-language browser automation and E2E testing; you can ask Claude to exercise flows (login, checkout, etc.) and it will drive a real browser session.[2][1]
- **code-review / PR review plugins** – Structured review plugins that add scoring, checklists, and PR‑style comments instead of generic “LGTM,” useful even for solo devs.[6][2]

Example: a common “baseline” stack for web dev is typescript-lsp + security-guidance + Context7 + Playwright + one review plugin.[4][1][2]

## High‑leverage generalist packs

These give you multi-agent or multi-skill bundles rather than single tools.[7][3][8][5][9][1]

- **Superpowers** – A popular official plugin pack that adds brainstorming, planning, code simplification and other skills; several users call it essential for Claude Code sessions.[5]
- **Production‑agent suites / marketplaces** – Packs like claude-tools, small “toolpacks,” or marketplace bundles that give you review, test, security-scan, and deploy agents via simple slash commands.[8][9][7][4]
- **Jeremy Longshore’s Claude Code Plugins** – Broad marketplace-style collection (DevOps, ML, creator workflows) that also serves as documentation and learning path for building your own.[9]

For someone like you doing multi-day, multi-terminal work, a good pack that introduces agents and hooks is typically a **force multiplier** on day one.[7][8][9]

## Nice‑to‑have, depending on your focus

These are “must have” only if you do a lot of work in that lane.[10][3][6][4][1][2]

- **Frontend/UI:**  
  - frontend-design – Better UI/UX defaults, component scaffolding, and layout proposals; often recommended by frontend-heavy users.[11][6][2]
  - Playwright (already above) becomes a must if you own E2E.[1][2]

- **Docs and project hygiene:**  
  - claude-md-management – Helps keep CLAUDE.md and other prompt/guide files organized.[12][2]

- **Context and memory:**  
  - Claude Context MCP, Memory MCP, and similar servers for huge mono-repos or knowledge-graph style long-term memory.[3]

- **IDE & editor bridges:**  
  - claude-code.nvim / claude-code.el / VS Code Claude Code chat extension, etc., to get the same plugin power from your editor while still using the Claude Code engine.[10][3]

## Quick reference table

| Need / area            | Commonly recommended plugin(s)                          | Why people consider it essential |
|------------------------|---------------------------------------------------------|----------------------------------|
| Type‑safe TS work      | typescript-lsp                                          | Real LSP diagnostics in Claude.[2] |
| Security while coding  | security-guidance                                      | Catches real vulns as you code.[1][2] |
| Live API docs          | Context7 / context7                                    | Fetches current docs on demand.[1][2] |
| Browser/E2E testing    | Playwright                                             | Natural language browser tests.[1][2] |
| Code/PR review         | code-review, pr-review-toolkit, similar agents         | Structured reviews and comments.[2][6][8] |
| General productivity   | Superpowers, production-agent suites, claude-tools     | Adds agents/skills for planning, refactors, CI/CD.[7][8][5][9] |
| Huge repos & memory    | Claude Context MCP, Memory MCP                         | Semantic search and persistent memory.[3] |
| UI/UX heavy work       | frontend-design + Playwright                           | Better defaults + real browser checks.[2][6][11] |

If you tell me your current Claude Code setup (editor + primary languages + repo scale), I can propose a minimal “starter stack” tuned to your workflow rather than a generic list.

## Human

claude code cli as editor, but vscode insiders to read files, python & typescript, monorepo 50K lines of code.

## Assistant

Claude Code CLI paired with VS Code Insiders for file viewing works seamlessly via integrated terminals and shared settings—run `claude` inside VS Code's terminal for IDE-aware diffs and diagnostics while keeping your CLI-first flow. For Python + TypeScript monorepos at 50K lines, prioritize LSPs for real-time type checking, monorepo-aware search, and security hooks to handle scale without context overload.[1][2][3][4]

## Recommended Starter Stack

Install these via `/plugin install` commands in your Claude Code CLI session (they sync to VS Code Insiders automatically).[4][1]

- **pyright-lsp** and **typescript-lsp**: Essential LSPs for Python type inference/virtualenv awareness and TS diagnostics/auto-imports/refactors; they catch errors across your 50K-line monorepo without hallucinations.[2][4]
- **security-guidance**: Pre-edit hook scans for vulns like injections/secrets before Claude commits changes—critical for monorepo scale where small mistakes propagate.[5][6]
- **Context7**: Pulls live docs for your libs (FastAPI/Django/Python 3.12+, Next.js/React/TS frameworks) so Claude uses current APIs, not stale knowledge.[6]
- **Greptile or Claude Context MCP**: Semantic codebase search for your large monorepo; ask "where's auth handled?" and get precise context without manual @-file spam.[7][2]

Run in VS Code Insiders terminal: `claude`, then `/plugins` to manage visually if needed.[3][1]

## Monorepo-Specific Additions

These handle 50K+ line complexity in Python/TS setups.[2][7][4]

- **Ralph Loop**: Autonomous agent for multi-hour tasks (migrations, test coverage); resets context per iteration to avoid monorepo overload, commits to git worktrees.[6]
- **code-review**: Multi-agent PR reviews with confidence scores for types/tests/errors; use git worktrees for parallel branches in your monorepo.[1][6]
- **Playwright MCP**: Browser E2E for TS frontend; Claude drives real sessions from CLI, visible in your browser for debugging.[1][6]

Pro tip: Use git worktrees (`git worktree add ../feature-branch -b new-branch`) for isolation in multi-terminal flows—Claude CLI detects them natively.[1]

## Integration Workflow

| Step | Command/Action | Benefit for Your Setup |
|------|----------------|-------------------------|
| 1. Open monorepo in VS Code Insiders | `code-insiders .` | File tree/diffs with LSP hovers; Insiders handles large workspaces well.[1][8] |
| 2. Run CLI in integrated terminal | `Ctrl+`` then `claude` | IDE integration: auto-shares selections/files via @-mentions.[5][8] |
| 3. Install plugins | `/plugin install pyright-lsp typescript-lsp security-guidance` | LSPs light up immediately; hooks activate on edits.[9] |
| 4. Add MCP for search | `claude mcp add greptile` (or Context MCP) | Monorepo navigation without token waste.[6][7] |
| 5. Prompt example | `@src/ explain auth flow; refactor with types` | LSP-aware, monorepo-scale responses.[5] |

This stack adds ~5-10s startup but cuts debugging/refactor cycles by 50%+ in large Python/TS repos per user reports. Test with a small worktree first; expand as needed.[2][6]
