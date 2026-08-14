---
title: "Can you help with this claude code issue?


> How many steps need a hook?  TDD: RED, GREEN, REFACTOR, REGRESSION, INTEG"
date: "2025-12-27"
mode: "COPILOT"
uuid: "9ca8e0c0-fb27-482d-a3ea-1319d5e54271"
entry_count: 2
---

## Human

Can you help with this claude code issue?


> How many steps need a hook?  TDD: RED, GREEN, REFACTOR, REGRESSION, INTEGRATION?  Other?  different?


● Good question. Let me think through this:

  TDD Cycle Steps:
  | Step                 | Can hook enforce? | Why/why not                                                          |
  |----------------------|-------------------|----------------------------------------------------------------------|
  | RED (test first)     | No                | Can't detect temporal order - was test written before code or after? |
  | GREEN (make it pass) | No                | Can't distinguish "code for test" from "just code"                   |
  | REFACTOR (cleanup)   | No                | Subjective - did you refactor or just edit?                          |
  | INTEGRATION          | Yes               | Run integration command, check exit code                             |
  | REGRESSION           | Yes               | Run regression tests, check for known failure patterns               |

  Answer: 2 hooks maximum

  - Integration test hook - Runs after critical file edits
  - Regression gate hook - Runs before commit/when patterns detected

  The first 3 steps (RED, GREEN, REFACTOR) are developer discipline, not system enforcement. A hook can't make you write tests first - it can only verify that tests pass afterward.

  Alternative interpretation: Are you asking if the problem is different? Maybe the issue isn't "need more hooks" but something else entirely?

## Assistant

The snippet you provided presents a valid critique of **stateless** hooks, but as a system architect building custom integration solutions, you can overcome these limitations by implementing a **Stateful TDD Guard**.

The "2 hooks maximum" conclusion assumes hooks are isolated events that cannot track the agent's broader context. In a sophisticated "Master-Clone" or agentic architecture, you can enforce the full RED-GREEN-REFACTOR cycle by maintaining a lightweight state (e.g., a `.tdd-context` file or memory entry) that persists across tool calls.

Here is the architectural solution to the "Claude Code Issue," upgrading the snippet’s logic from "Developer Discipline" to "System Enforcement."

### The Core Shift: Stateless vs. Stateful Hooks
The snippet argues that a hook cannot enforce "RED" because it lacks temporal awareness ("was test written before code?"). This is solvable if the hook has access to a persistent state machine.

| Step | Stateless View (Snippet) | Stateful View (Architectural Fix) |
| :--- | :--- | :--- |
| **RED** | **No.** Can't see order. | **Yes.** `PreToolUse` blocks writes to `src/` unless state is `RED_CONFIRMED` (i.e., a test just failed). |
| **GREEN** | **No.** Can't distinguish code. | **Yes.** `PreToolUse` blocks writes to `test/` (preventing goalpost moving) until state is `GREEN_PASSED`. |
| **REFACTOR**| **No.** Subjective. | **Yes.** `PostToolUse` triggers a dedicated "Refactor" sub-agent scan after `GREEN` state is achieved. |
### Implementation Strategy
You can implement this using `PreToolUse` and `PostToolUse` hooks in your Claude Code configuration or MCP wrapper.

#### 1. The State Machine (The "Memory")
Create a hidden file (e.g., `.tdd-state`) or a variable in your agent loop that tracks four phases:
1.  `IDLE`: Ready for new feature.
2.  `AWAITING_RED`: Agent must write a test.
3.  `AWAITING_GREEN`: Agent must fix implementation.
4.  `REFACTORING`: Agent cleans up code.

#### 2. The Hook Logic

**Hook A: The "Red Guard" (Enforce Test First)**
*   **Type:** `PreToolUse`
*   **Trigger:** `Edit` or `Write` to `src/**/*` (Implementation files)
*   **Logic:**
    *   Read `.tdd-state`.
    *   **IF** state is `IDLE` or `AWAITING_RED`:
        *   **BLOCK ACTION.**
        *   **Return Error:** "VIOLATION: You are attempting to write implementation code, but no failing test has been detected. Write a test in `test/` first."

**Hook B: The "Green Validator" (Verify Failure)**
*   **Type:** `PostToolUse`
*   **Trigger:** `Bash` (specifically test commands like `npm test` or `pytest`)
*   **Logic:**
    *   Parse `stdout`/`stderr` for "FAIL" or "PASS".
    *   **IF** "FAIL" detected AND state is `AWAITING_RED`:
        *   **Update State** -> `AWAITING_GREEN`.
        *   **Inject User Message:** "Good job. Red phase confirmed. You may now edit `src/` to make it pass."
    *   **IF** "PASS" detected AND state is `AWAITING_GREEN`:
        *   **Update State** -> `REFACTORING`.
        *   **Inject User Message:** "Green phase confirmed. Tests passed. Proceed to Refactor."

**Hook C: The "Refactor Gate" (Prevent Regression)**
*   **Type:** `PreToolUse`
*   **Trigger:** `Edit` to `test/**/*` during `AWAITING_GREEN`
*   **Logic:**
    *   **BLOCK ACTION.**
    *   **Return Error:** "VIOLATION: Do not change tests during Green phase. Fix your implementation to match the test."

### Advanced: "Master-Clone" Integration
Since you are working with **subagent spawning**, a cleaner pattern is to separate these concerns into distinct agents rather than just hooks:

1.  **`TestWriter` Agent:** Has permission *only* to write to `test/`. Its goal is to produce a failure.
2.  **`Implementer` Agent:** Has permission *only* to write to `src/`. Its goal is to stop the failure.
3.  **`Orchestrator` Hook:**
    *   Detects user request for "feature".
    *   Spawns `TestWriter`.
    *   **Hook** intercepts `TestWriter` completion (detects exit code 1 from test run).
    *   Spawns `Implementer` with the failure log.

### Summary Answer for Your Issue
> **Q:** How many steps need a hook?
> **A:** **3 Hooks + 1 State File.**

The snippet's "2 hooks maximum" is a conservative estimate based on *passive* observation. For *active* TDD enforcement (which "Claude Code" supports via `PreToolUse`), you need:
1.  **Red Gate:** Blocks implementation until failure is proven.
2.  **Green Gate:** Blocks test modification during implementation.
3.  **Refactor Prompt:** Triggers cleanup analysis after success.

This converts "Developer Discipline" into "System Constraints," which aligns with the robust architectural patterns you are building.

## Human

That's brilliant.  What github.com repos would you suggest can help?

## Assistant

Based on your architecture stack (Windows 11, PowerShell, Python, Claude Code), here are the most relevant repositories to implement a **Stateful TDD Guard**.

### 1. The "Plug-and-Play" Solution: `nizos/tdd-guard`
This is the closest off-the-shelf implementation of the stateful logic described. It uses Claude Code's `PreToolUse` hook to inspect the agent's intent before it executes.
*   **Repo:** [github.com/nizos/tdd-guard](https://github.com/nizos/tdd-guard)
*   **Why it helps:** It explicitly blocks "implementation" edits (writes to `src/`) unless a test failure has been recorded. It solves the "stateless" problem by maintaining a session context that tracks the TDD phase.
*   **Key Feature:** It includes a `PreToolUse` hook that you can configure in your `.claude/config.json` to intercept `Edit` and `Write` tool calls.

### 2. The "Heavy Lifter": `ruvnet/claude-flow`
If you want to move beyond simple hooks into the "Master-Clone" architecture you mentioned, this framework is the current gold standard for Claude Code orchestration.
*   **Repo:** [github.com/ruvnet/claude-flow](https://github.com/ruvnet/claude-flow)
*   **Why it helps:** It implements a "Swarm" architecture where you can define specialized agents. It has a specific **SPARC Methodology** module (Specification, Pseudocode, Architecture, Refinement, Code) which is a TDD-adjacent pattern.
*   **Relevance:** It includes "Advanced Hooks System" specifically designed for Claude Code, allowing you to daisy-chain agents (e.g., a "Test Agent" that hands off to an "Implementer Agent").

### 3. The "Architectural Blueprint": `langchain-ai/langgraph`
While not a direct Claude Code plugin, this repo contains the cleanest Python implementation of the **Stateful Graph** pattern (Red -> Green -> Refactor nodes).
*   **Repo:** [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
*   **Specific Tutorial:** Look for the "Code Assistant" tutorials.
*   **Why it helps:** It demonstrates how to build the *state machine* itself. You can write a small Python script using LangGraph that serves as the "Brain" for your hooks. Your Claude Code hook would simply call this script:
    ```powershell
    # Pseudo-hook in .claude/hooks/pre-tool-use.ps1
    $State = python check_state.py --action "write_src"
    if ($State -eq "BLOCK") { exit 1 }
    ```

### Recommended Implementation Strategy

Since you are a "power user" on Windows, I recommend a hybrid approach:

1.  **Install `nizos/tdd-guard`** immediately to get the basic "Red Guard" functionality (blocking implementation without tests).
2.  **Fork `tdd-guard`** or write a custom PowerShell hook that adds the **"Refactor Gate"**.
    *   *Current gap:* Most tools focus on "Red/Green". They rarely enforce "Refactor".
    *   *Fix:* Add a counter in your state file. If `Green` state is achieved, force the next tool call to be `Analysis` or `grep` (to find code smells) rather than `Submit`.

#### Conceptual "State File" Structure (JSON)
You can implement this in a simple `.tdd-state.json` at your project root:
```json
{
  "phase": "AWAITING_RED",
  "last_test_output": "exit_code_1",
  "allowed_tools": ["Edit:test/*", "Bash:npm test"],
  "violation_count": 0
}
```
