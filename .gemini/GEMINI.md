# Gemini Project Memories - Cognitive Stack Integration

This file serves as the long-term memory for project-specific cognitive protocols and engineering standards.

## Cognitive Protocols

### 1. IoRT (Instruct-of-Reflection Gate)
Mandatory for complex architectural or debugging tasks:
- **Loop:** Basic -> Critique -> Reflective.
- **Critique Focus:** Scale (26K+ items), Assumptions, Boundary Invariants, Reversibility.
- **Decision:** Stop (same results), Select (reflective better), Refresh (both flawed).

### 2. Thinking Modes
Activated during the DESIGN phase:
- **Analytical:** Breaking down components and logic.
- **Strategic:** Long-term impact and alignment with architecture.
- **Lateral:** Alternative "outside the box" solutions.
- **Systematic:** Step-by-step verification and process flow.

### 3. Value & Safety Gates
- **Value Assessment:** Does this need deep reasoning? (Complexity > 3 steps, High Risk, or New Architecture).
- **Reversibility Checklist:**
    1. Easy git revert?
    2. No data migration required?
    3. No breaking interface changes?
    4. Can ship incrementally?
- **Enforcement:** If score < 3/4, a detailed rollback plan is required.

### 4. Reasoning Profiles
- `debug_rca`: 5-Whys + Evidence verification.
- `tradeoff_decision`: Option A vs B + Inversion (how does each fail?).
- `architecture`: Cynefin classification + Boundary impact.
- `pre_commit_risk`: Pre-mortem analysis (Immediate, Short, Medium, Long-term).

## Integration Status
- **PDS Enhanced**: SKILL.md updated with IoRT and Value Assessment.
- **Adaptive Guardrails v2.0**: Deployed Feb 2026. Behavioral Proof (evidence_store.py) replaces text-pattern matching.
- **Negative Proof Rule**: Claims of absence (e.g., "file deleted") or restoration require 2+ diverse verification strategies (e.g., ls + content check).
- **The Portability Rule**: Never use absolute paths (e.g., `P:/...`) in hook logic. Always resolve relative to `__file__` or use root-relative variables to ensure codebase portability across system roots.
- **Behavioral Parity Rule**: When refactoring logic into in-process libraries (like `pre_tool_use_logic.py`), ensure 100% parity of "secondary" outputs (prescriptive directives, error pointers). Stripping these during optimization is a behavioral regression.
- **Synchronized Configuration**: Modules sharing a config (like `directory_policy.json`) must be verified to resolve to the *exact same* canonical path in their respective execution contexts.
- **Prescriptive Escalation**: 2-strike rule for tool failures mandates a strategy shift (temp file).
- **Tracking**: Use `cognitive_stack_tracker.py` for significant workflows.
