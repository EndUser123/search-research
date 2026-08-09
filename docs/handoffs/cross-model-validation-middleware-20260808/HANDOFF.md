# HANDOFF: Cross-model validation + execution-reality middleware for ship-py

## Status
OPEN — design needed

## Objective
Implement the next architectural layer of anti-fabrication for ship-py: cross-model validation (Factory 3-role pattern) and execution-reality middleware (Singh payload-response heuristic).

## Context
- ship-py now has: polling loop, suspicion gates, transition chain, --verdict removal, path validation, canonical findings paths
- The remaining gap: the agent can still produce plausible-but-fabricated findings. The suspicion gates catch empty findings, but not non-empty fabricated ones.
- The /www research (session 019fe25d) identified two solutions with measured evidence:
  1. **Cross-model validation (Factory pattern):** `/agy` or `/codex` validates Grok's work in a fresh context. Factory achieved 89.25% issue coverage in production.
  2. **Execution-reality middleware (Singh heuristic):** ~30 lines of Python that catches 56.6% fabrication rate by checking (payload, response) coherence.

## Key design questions
1. **Where does cross-model validation fit in the pipeline?** After the review phase, before the fix phase? Or as a new phase between review and risk?
2. **Which model for validation?** `/agy` (Gemini) or `/codex` (OpenAI Codex) — both have separate quota pools from Grok.
3. **Singh heuristic implementation:** wrap every tool execution in middleware that captures the actual return value and checks whether the agent's claimed result matches reality. Where does this middleware live?
4. **Cost:** cross-model validation doubles LLM spend for the validation step. Is this justified for every ship-py run, or only for high-stakes changes?

## Acceptance criteria
- Design document produced via `/design`
- Singh heuristic implemented as ~30-line middleware
- Cross-model validation wired via `/agy` or `/codex` as a new pipeline phase or sub-step
- Tests covering the middleware's detection of fabricated vs. real findings

## References
- `P:/.data/wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md` — solution families with evidence
- `P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md` — diagnosis
- Singh KDD 2026 Workshop — payload-response misalignment heuristic (arxiv.org/abs/2607.19449)
- Factory Missions — 89.25% coverage with three-role architecture
