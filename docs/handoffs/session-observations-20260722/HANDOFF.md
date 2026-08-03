---
thread_id: session-observations-20260722
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T16:10:00Z
status: CLOSED
handoff_type: investigation
assigned_to: unassigned
accurate_as_of_head: 642c7ab
---

# Session observations: 2026-07-22 (session 019f821c)

## Observations and seeds

1. **dgemma's failure is transport-specific, not model-specific.** Google ships function calling for Gemma 4; the diffusion variant's thinking-mode output breaks the agent framework's parser. The same model works via direct API. — *Source: session 019f821c, dgemma HOW-TO + tool-call matrix research*

2. **The model pool should include dgemma ensemble for read-only /tp, not just agent-compatible models.** The `--enhanced` mode (3-perspective fan-out) is faster (5s), free, and multi-perspective — better for file-target critiques than slow agent subagents. — *Source: operator reframe, session 019f821c*

3. **Headless grok (`grok -p`) is slower than spawn_subagent for one-shot tasks** (~11-15s vs 5-8s). The subprocess overhead dominates for short prompts. Headless only wins for multi-turn agentic tasks. — *Source: session 019f821c, latency comparison*

4. **The `.agents/` open standard is the right home for shared agent-callable tools**, not wiki/scripts/ or cc-skills-utils/. The AGENTS.md standard (Linux Foundation, 60k+ repos) converges on `.agents/` as the directory convention. — *Source: session 019f821c, agents.md research*

5. **Test-code drift is the multi-agent version of edit-then-verify.** Advisory rules fire on what you do, not what you skip. A coverage gate (`pytest --cov-fail-under`) is the mechanical fix — same "derive constraint from real requirement" pattern as the dynamic cap. — *Source: session 019f821c, 4-version test drift on /close scanner*

6. **API guessing from function names is a valid heuristic but must be verified before shipping.** The test runner is the structural backstop — wrong guesses produce test failures in 0.19s. Reading signatures first saves the write-fix-rerun cycle. — *Source: session 019f821c, 8/24 wrong scanner tests*

7. **PI and opencode are installed but dgemma isn't configured for them yet.** These are future cross-host paths — they work as external CLIs but their model configs need setup. — *Source: session 019f821c, `Get-Command pi/opencode`*

8. **The concurrent `/close` rewrite (v1 prose → v6 scanner-based) was legitimate fleet evolution, not interference.** The v6 "scanner thinks, LLM judges" architecture is the right design — it's the same code-first pattern the session converged on everywhere. — *Source: session 019f821c, /close evolution through 6 versions*

9. **nemotron serialization-fails on real tool tasks despite passing trivial probes.** The probe (READY reply) passes; real tool-use tasks fail with `invalid type: null, expected u32`. Probes need to test BOTH trivial and tool-use paths. — *Source: session 019f821c, 4 nemotron verifier failures*

10. **The session-close accounting rule (ACCOUNTING block before "done") needs to apply at session end, not just when the user asks.** The /close skill with the scanner is the mechanical enforcement; the AGENTS.md rule is the advisory trigger. — *Source: session 019f821c, operator caught "nothing left open" twice*
