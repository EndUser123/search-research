---
thread_id: 57d7c178-1b0c-4fc4-8dc7-5519c12eccec
parent_handoff_path: P:\docs\handoffs\deferred-factory-work-20260726\HANDOFF.md
current_session_id: 019f9b6f-98fc-7883-9d5f-cf570a0b3812
current_terminal_id: console_4605b174-0262-4044-8d3c-3ca7
produced_at: 2026-07-26T19:55:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 39ec391
---

# Session observations — software-factory session 019f9b6f

## Observations

1. **Same-agent provenance is the dominant failure mode for adversarial review stacks.** When one agent writes the design, the research, the red-team, the /tp, and the /why, each layer inherits the prior layer's framing. The only reliable catch is mechanical verification. Cross-family critics are the unbuilt structural fix (deferred item 7).

2. **The Stop hook scope-binding contract was undocumented for months.** Agents have been running `pytest tests/` to verify code changes without knowing the receipt system needs explicit path arguments. Layer C (AGENTS.md rule) now documents this, but the contract was invisible in code comments for the entire lifetime of the receipt system.

3. **The grill-me interview pattern (Matt Pocock) is half-wrong.** The charismatic one-question-per-turn design was rejected by Pocock's own community for being too slow. The transferable parts are facts-vs-decisions separation and agent-provides-recommended-answer. This nuance matters for anyone considering adopting grill-me style patterns.

4. **`/tp` structurally overreaches on complex targets.** A single critical-friend frame on a 9-file target produced 3/6 claims that needed correction. The frame-mutation fix (≥2 frames for N>3 findings) addresses this but hasn't been tested yet.

5. **The receipt writer's auto-inference (Layer A) is the highest-leverage fix.** It turns the most common pytest invocation (`pytest tests/test_foo.py`) from empty-scope (blocked) into inferred-scope (passes) — without weakening the security model. Full pipeline test still needed.

## Source

Session 019f9b6f, 2026-07-25/26. Operator + Grok.
