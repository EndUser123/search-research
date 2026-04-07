## Triage Classification

plan — Architecture decision analysis for comparative claim guard layering (PreToolUse vs Stop)

## Dispatched Specialists

- **adversarial-critic** — Reasoning quality, bias, architecture decision correctness
- **adversarial-logic** — Logical feasibility given schema constraints, timing analysis

## Specialist Findings Summary

### adversarial-critic

**Domain:** Architecture decision quality

**Key findings:**
- [HIGH] ARCH-001: PreToolUse Layer Timing Mismatch is Fundamental, Not Solvable — PreToolUse cannot fire during LLM drafting phase, a hard constraint of the hook system
- [HIGH] CONS-001: Stop-Only Architecture Advantages Are Decisive — complete context (full response + all tool events + transcript_path) makes Stop-only superior
- [MEDIUM] BLIND-001: Alternative PostToolUse State Accumulator Not Considered — PostToolUse hook on Read operations could accumulate state for Stop to use (optional enhancement)
- [LOW] BIAS-001: Plan Overweights PreToolUse Viability — spends too much time analyzing unsolvable approaches

### adversarial-logic

**Domain:** Schema feasibility, timing analysis

**Key findings:**
- [BLOCKER] LOGIC-001: PreToolUse schema lacks both current_context and tool_history — comparative operation (read vs. planned response) structurally impossible
- [BLOCKER] LOGIC-002: State file handoff fails because PreToolUse fires BEFORE Read completes — causal chain is backwards
- [HIGH] LOGIC-003: PreToolUse cannot support cross-read comparative claims even across turns
- [MEDIUM] LOGIC-004: Stop-only limitations (reactive, token waste) are acceptable given structural impossibility of PreToolUse

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [BLOCKER] (source: adversarial-logic) — PreToolUse comparative claim guarding is structurally impossible regardless of implementation approach. Requires `current_context` (planned response) and `tool_history` (accumulated reads), neither of which exists in PreToolUse schema. **Conclusion: PreToolUse layer should NOT be built.**

1.2. [HIGH] (source: adversarial-critic) — State file handoff approach (PreToolUse writes after Read, Stop reads) is fundamentally broken. PreToolUse fires BEFORE Read completes — the causal chain is backwards, not sequential. Location: work.md:36-37

1.3. [MEDIUM] (source: adversarial-logic) — Even cross-turn reasoning via transcript is only available in Stop, not PreToolUse. Multi-read comparative claims across turns cannot be prevented by PreToolUse. Location: work.md:29-33

### Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-critic) — Plan assumes PreToolUse could theoretically provide comparative context, but this requires state that cannot be reconstructed from available schema fields. Blind spot: PostToolUse state accumulator not considered.

2.2. [LOW] (source: adversarial-critic) — Token waste on blocked responses is presented as a significant disadvantage, but for high-stakes claims that could cause harm if unchallenged, the reactive model is acceptable.

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-logic) — Add explicit "Irreducible Constraints" section to the architecture plan that identifies hard limits early, reducing analysis time on unsolvable approaches.

3.2. [MEDIUM] (source: adversarial-critic) — Consider PostToolUse_read_state_accumulator.py as optional enhancement if per-turn reading context is needed. PostToolUse fires after Read completes, could accumulate state for Stop.

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-logic) — Stop-only fires AFTER response generation (reactive). User sees wrong response before block fires, wastes token generation. **Risk accepted as unavoidable given schema constraints.**

4.2. [LOW] (source: adversarial-critic) — Token waste from blocked responses could be mitigated with confidence threshold (only block high-severity failures).

### Concrete Recommendations

5.1. [HIGH] **Accept Stop-only as the correct final design.** Document that PreToolUse is not viable due to hard schema constraints. No implementation required.

5.2. [MEDIUM] Consider PostToolUse_read_state_accumulator.py as future enhancement (optional, not required).

5.3. [LOW] Add confidence threshold to minimize token waste on blocked responses.

### Open Questions / Unknowns

6.1. [LOW] (source: adversarial-logic) — Is there any hook phase between PreToolUse (per-tool, pre-draft) and Stop (turn-end, post-draft) that could provide both preventive timing and comparative context? (Unlikely given current Claude Code architecture.)

6.2. [LOW] (source: adversarial-logic) — Could transcript_path be made available in PreToolUse to enable cross-turn state reconstruction?