# HANDOFF: Singh execution-reality middleware for tool-output fabrication detection

## Status
OPEN — design needed

## Objective
Implement the Singh payload-response misalignment heuristic as middleware that detects when an agent fabricates a tool's output after the tool fails or returns empty/malformed results.

## Context
- This is a SEPARATE work item from cross-model validation (P:/docs/handoffs/cross-model-validation-middleware-20260808/)
- Cross-model validation addresses review-finding fabrication (agent writes fake findings without spawning agents)
- This middleware addresses tool-output fabrication (agent claims a tool returned X when it returned Y or nothing)
- The two failure modes are different layers — bundling them conflates the design space

## What the Singh heuristic does

~30 lines of Python that wraps tool execution and checks (payload, response) coherence:
- `(is_null_or_malformed(payload) AND contains_data_claims(response))` → flag as FAR (Fabrication)
- `(is_null_or_malformed(payload) AND contains_policy_language(response))` → flag as USR (Unfaithful Safety Refusal)

Measured baseline: 56.6% of agent responses to silent tool failures are Fabrication (Singh KDD 2026 Workshop, arXiv:2607.19449). The heuristic catches these with 0% false positive rate under neutral prompts.

## Key design questions
1. **Where does the middleware live?** Options: (a) wrap every `subprocess.run()` in ship-py's orchestrator, (b) a PostToolUse hook that checks tool results against agent claims, (c) a standalone validator that runs after each phase
2. **Scope:** ship-py phases only, or all agent tool calls? The heuristic is general — any tool the agent claims success for could be checked
3. **What counts as a "tool" for this purpose?** ship_receipt.py (tests/lint/docs), check_lifecycle.py, doc-check script — any subprocess the orchestrator runs whose output the agent might misrepresent
4. **Integration with existing suspicion gates:** the empty-findings gate catches empty fabrication; the Singh heuristic catches non-empty fabrication where the content doesn't match the tool's actual output

## Acceptance criteria
- Middleware implemented as ~30-line Python function matching the Singh heuristic
- Integrated into ship-py's orchestrator (wrapping subprocess calls or as a post-phase check)
- Tests covering: (a) agent claims success when tool returned empty → flagged, (b) agent claims success when tool genuinely succeeded → not flagged
- Documented as complementary to (not replacing) cross-model validation

## References
- Singh KDD 2026 Workshop — payload-response misalignment heuristic (arxiv.org/abs/2607.19449)
- P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md — diagnosis (hallucination-after-failure sub-pattern)
- P:/.data/wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md — solution family #2

## Suggested next invocation
```
/design Singh execution-reality middleware: ~30-line payload-response coherence check wrapping ship-py subprocess calls
```
