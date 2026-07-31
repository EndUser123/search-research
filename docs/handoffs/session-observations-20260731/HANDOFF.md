---
thread_id: 019fa8f8-session-obs
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-07-31T01:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: d7da624
---

# Session observations — 2026-07-30/31

## Observations

1. **Fabricated confidence is the dominant agent failure mode.** 6+ operator corrections for explanations produced without evidence. The agent optimizes for self-convenience (inline execution, familiar tools, confident framing) and rationalizes with fabricated explanations. Structural defense: apply verification receipt rule to framing claims, not just code claims.

2. **"Spawn protection, not routing" — the system name should match what it does.** Building infrastructure that blocks bad spawns and calling it "routing" over-claims. Pool contracts are guidance, not enforcement. The gate is enforcement, not selection.

3. **Pool contracts > greedy algorithms for model selection.** pick_model.py's first-available algorithm removed task-fit judgment. Pool contracts preserve it. Reverted after testing. The picker is an availability checker, not a selector.

4. **zen-deepseek-v4-flash-free fails on multi-file code review** (224K token context exhaustion from repeated file reads). Works fine for short critique prompts and single-file review with inline content. Documented in critic-model-pool.md.

5. **ddgs_search.py multi-query batch mode** eliminates the temp-script anti-pattern. The tool now handles both single and multi-query DDG searches. Stop writing temp Python scripts for search.

6. **The /close process is heavy but necessary.** The scanner, AAR validator, completion receipt, and gate resolution enforce rigor that prevents premature closure. Skipping steps produces an invalid close.

7. **Research lane design deferred.** Operator mentioned wanting to consider "how best to do a research lane" after model-quota was built. Not started.
