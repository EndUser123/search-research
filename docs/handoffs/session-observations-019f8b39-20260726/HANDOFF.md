---
thread_id: session-observations-019f8b39-20260726
parent_handoff_path: P:\docs\handoffs\tp-session-shipped-work-20260726\HANDOFF.md
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
current_terminal_id: console
produced_at: 2026-07-26T20:15:00Z
status: CLOSED
handoff_type: investigation
accurate_as_of_head: varies (see commits)
---

# Session observations: 019f8b39 (2026-07-23 to 2026-07-26)

## What happened

Multi-compaction session spanning 3 calendar days. Started with web-search-prime verification, evolved through /tp improvement brainstorming → design → red-team → implementation → skill consolidation.

## Key observations

### 1. Default-selection bias is the real failure mode, not "forgetting"

When the system reminder showed MCP search tools, I defaulted to the visible ones and skipped DDG. The user correctly identified this as structural, not a memory lapse. The fix was making the fan-out recipe NON-NEGOTIABLE in the skill, not adding a reminder.

**Pattern:** the agent's tool selection is biased toward what's visible in the system reminder. Structural fixes (mandatory recipes, hard language) work better than behavioral fixes ("remember to use DDG").

### 2. Session-state questions collapse the two-lens architecture

Two cancelled /tp spawns (188.7s + 47.6s wasted) proved that spawning a subagent for a session-state question is structurally wrong — the subagent can't reconstruct conversation state from files. The carve-out (inline for session-state, spawn for external) is now in the skill.

**Pattern:** the /tp two-lens design has a boundary condition: questions whose answer lives in conversation history, not in workspace files. The boundary is detectable at screening time.

### 3. Red-team BLOCK caught a real design error

The 4-lens system duplicated existing conditional domains. Three specialists independently found the same issue. The BLOCK was correct — the fix (3 lines, not 90) was radically simpler.

**Pattern:** when a design adds complexity, check whether the capability already exists in a different form. The red-team is the structural backstop for this.

### 4. /tp critique was wrong about execute-plan consolidation

I anchored on "different mechanisms = different skills" without checking whether /go already had those mechanisms. The user corrected by asking "why can't Go absorb them?" — which forced me to read /go's plan-execute profile and discover it already had DAG parsing, worktree isolation, and per-task verification.

**Pattern:** consolidation critiques must verify the donor's capabilities before claiming the recipient can't absorb them. "Different mechanism" is an inference, not a fact, until you check.

### 5. Skill name collisions are a maintenance trap

Creating `writing-plans` at user scope collided with the superpowers plugin's `writing-plans`. Renamed to `plan-writer` — but the system reminder still showed the old name for the rest of the session (stale snapshot).

**Pattern:** new skills at user scope should avoid names that exist in plugin scope. The system reminder is a session-start snapshot, not live state.

### 6. Plan-writer should have been built first

The consolidation of writing-plans + /plan into plan-writer was requested mid-session, after the /tp improvement work was already underway. Building the tool (plan-writer) before using it (to write the /tp improvement plan) would have been more efficient. The /tp critique correctly identified that the spec WAS the plan for a 21-line edit — plan-writer was unnecessary for that specific case.

## What worked well

- The /www mandatory fan-out recipe: when actually exercised (web-search-prime history check), all 3 backends returned results and the multi-source agreement was visible
- The red-team specialist convergence: 3/4 specialists independently found the lens-duplicates-domains issue — strong signal
- The session-state carve-out: once added, immediately saved compute on the next /tp invocation
- The adaptive execution mode design for /go: auto-detecting plan format (simple/checkpoint/PR-DAG) is cleaner than 3 separate skills
- The /tp recap variant: first invocation produced the exact output the user wanted (work streams + open decisions + pending items)

## What didn't work

- The first /tp spawn (nemotron-3-ultra): serialization error on real prompt (98k tokens). Root cause later found by a concurrent session (streaming serde null-typed-as-u32, fix: `stream_tool_calls = false`)
- The /tp lens system (rev 1 of the spec): over-engineered, duplicated existing domains, made steelman/pre-mortem conditional when they should be mandatory
- My consolidation critique of execute-plan: wrong because I didn't check /go's existing capabilities
- PowerShell heredoc through Bash tool: doesn't work, repeatedly caused parser errors

## Open follow-ups for next session

1. Validate VS layer on first live /tp critique (the 3-layer improvement has never been exercised)
2. Pool composition investigation: deterministic vs random selection still open
3. /web fan-out recipe: needs a fresh /web invocation to validate on a real query
4. The /tp pool composition handoff (`tp-pool-composition-review-20260723`) is OPEN with updated pool state
