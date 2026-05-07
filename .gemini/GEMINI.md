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

## Self-Correction Protocols (Session Reflections May 2026)

### 1. Regex & Path Safety (The "Forward-Slash" Invariant)
- **Path Separation:** Never use backslashes (`\`) in hardcoded Python path strings. Always use forward slashes (`/`). Windows Python handles these perfectly and they are immune to escape-sequence errors.
- **Literal Verification:** If a string literal contains a path, it MUST NOT end in a backslash (e.g., `r"P:\"`), as this escapes the closing quote and creates a `SyntaxError`.
- **Bulk Fix Guard:** Never use regex-based bulk find-and-replace for logic-critical strings (like paths) across more than 3 files without a mandatory "Parity Verify" step on EVERY modified file.

### 2. Delegation & Audit Protocols
- **Atomic Delegation:** When using subagents for "Cleanup" or "Bulk Refactor" tasks, provide an explicit "Verification List" of every file they are authorized to touch.
- **Handover Audit:** Upon subagent completion, the orchestrator MUST perform a surgical read of at least 10% of the modified files to check for pattern regressions (e.g., double raw prefixes `rr""`).
- **Loop Interruption:** If a specific tool call (e.g., a python one-liner replace) fails twice or produces zero changes, DO NOT retry. Immediately switch to `write_file` for a surgical, definitive fix.

### 3. Verification Rigor
- **The Compile Mandate:** Every Python file modification—whether manual or automated—MUST be followed by a `python -m py_compile <path>` call in the SAME turn. Silence is not proof of health.
- **Identity Integrity:** When implementing shared state (like the identity handshake), verify the "Fallback" path (missing cache) as rigorously as the "Happy" path (valid cache).

