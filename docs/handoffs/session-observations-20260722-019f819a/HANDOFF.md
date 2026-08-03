---
thread_id: session-observations-019f819a
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console_b6a64919-a533-417e-875d-a72c
produced_at: 2026-07-22T20:50:00Z
status: CLOSED
handoff_type: observations
accurate_as_of_head: HEAD
assigned_to: unassigned
---

# Session Observations — 2026-07-22 (session 019f819a)

## Observations

1. **`/close` skill v3 (code-driven gates)** — rewrote close_accounting.py to resolve all gates mechanically, compute loop decision, and emit summary template. The "scanner thinks, LLM judges" pattern worked well — `/check` verified PASS. Code-vs-prose balance is the right frame for skill design.

2. **`/www` layering restructure** — discovered via `/tp` that `/www` was doing `/web`'s job (research logic) while claiming delegation. Restructured: `/web` now owns shape framing, scoring, conflicts, synthesis, iterative refinement. `/www` is thin orchestrator (219 lines, down from 450). The `/tp` fresh-subagent critique was the right tool for catching the architectural smell.

3. **Wiki query purpose in `/www`** — refined from "short-circuit" (blocking) to "strategy refinement" (feeds gap targeting + source/terminology hints to `/web`). The user's signal: "I invoked `/www` because I want internet info" was the cleanest framing — the wiki query informs the research, doesn't gate it.

4. **DDG is unlimited** — user corrected the tier classification. Free + no binding constraint = use it in the parallel fan-out. Reframe from quality tiers to constraint-based grouping.

5. **Search tool benchmark (AIMultiple)** — top 4 APIs (Brave, Firecrawl, Exa, Parallel) are statistically indistinguishable. When quality is tied, latency and cost decide. Our fleet pays $0 for what would cost $225-300/mo.

6. **SkillAxe finding** — skills improve execution reliability (coverage) not answer quality. Skills should focus on preventing execution failures, not making the LLM smarter. Validates the `/close` code-first pattern.

7. **Deep research vendor convergence** — all vendors (Anthropic, OpenAI, Perplexity) converge on plan → iterative search-reason-search → synthesize with citations. Token usage explains 80% of variance. GPT-Researcher (28.6k stars) is the most mature open-source option with MCP server.

## Seeds (ideas not yet developed into tasks)

- **`/web --deep` mode with parallel subagent decomposition** (Anthropic orchestrator-worker pattern) — task packet DR-02 in handoff `www-skill-add-youtube-ddg-backends-20260722`
- **Wire GPT-Researcher MCP server** for genuine deep research — task packet DR-03 in same handoff
- **Add budget-driven stopping** to `/web` (max searches, max pages, max time) — task packet DR-05
- **Exa --hyde as default for shape=research/facts** — neural search materially better for academic/semantic queries
- **Wire Brave and Exa as MCPs** — keys already in `.env`, both benchmark-tier quality
- **RCA skill design** — handoff exists at `rca-skill-design-20260722`
