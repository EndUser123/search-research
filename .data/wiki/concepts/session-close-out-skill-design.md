---
title: "Session close-out skill design: improvements + multi-terminal invariants"
created: 2026-07-22
source: session-2026-07-22-www
sources:
  - https://hermes-agent.ai/blog/ai-agent-session-handoff-checklist
  - https://www.cognizant.com/us/en/ai-lab/blog/building-debugging-multi-agent-system
  - https://www.digitalapplied.com/blog/agentic-workflow-anti-patterns-orchestration-mistakes-2026
  - https://dev.to/aureus_c_b3ba7f87cc34d74d49/building-reliable-state-handoffs-between-ai-agent-sessions-1bk3
  - https://github.com/softaworks/agent-toolkit/blob/main/skills/session-handoff/README.md
  - C:/Users/brsth/.grok/skills/close/SKILL.md
  - C:/Users/brsth/.grok/skills/aar/SKILL.md
  - C:/Users/brsth/.grok/skills/handoff/SKILL.md
tags: [session-close, close-out, handoff, orchestration, loop, idempotency, multi-terminal, stale-data, skill-design, hermes, cognizant, ai-agent]
summary: >
  Six external-sourced improvements + five multi-terminal/stale-data invariants
  for a session close-out orchestrator skill (/close). The improvements come
  from Hermes (handoff fields), Cognizant (orchestration loop safety),
  digitalapplied (unbounded-loop anti-pattern), and dev.to (restart-survival
  testing). The invariants are host-mandatory: multi-terminal isolation,
  stale-data immunity, session-scoped (not file-scoped) idempotency, decision
  locking, terminal-scoped state writes. Applied to the /close skill.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/git-worktree-multi-terminal-best-practices
    type: related
  - target: wiki/concepts/multi-agent-destructive-git
    type: related
  - target: wiki/concepts/portfolio-deep-read-transferable-techniques
    type: related
---

# Session close-out skill design: improvements + multi-terminal invariants

## What this adds

The `/close` skill (session close-out orchestrator with an iterative loop)
was built in this session. This concept captures the **external-sourced
improvements** applied during a `/www` research pass, plus the
**multi-terminal + stale-data invariants** that govern any close-out design
on this host. The skill is the instrument; this concept is the rationale and
the patterns for future close-out-shaped skills.

## Six improvements (from external sources)

### 1. Session-scoped idempotency guard (from Cognizant "GLOBAL RESTART GUARD")

**Pattern:** in an orchestration loop, skip a step only if THIS SESSION
already completed it in a prior iteration — never skip because a file exists.

**Why file-existence is wrong on this host:** `P:/docs/handoffs/` and
`P:/.data/wiki/concepts/` are shared directories. A file named
`foo-handoff/HANDOFF.md` may have been written by a *different* concurrent
session. Treating "file exists" as "this session already did Step 4" is a
stale-data false positive — you skip the handoff this session actually needs.

**Fix:** track step completion in an in-memory `$stepDone` set keyed on
this session's identity. The cognizant pattern uses "if gate_id is already
stored → step is done"; the multi-terminal adaptation is "if THIS SESSION
stored it → done; another session storing it is irrelevant."

**Source:** Cognizant, "Building & Debugging a Multi-Agentic System" (Airline
Turnaround), Failure 3 (restart loops from state misinterpretation).

### 2. "Not verified yet" + "Next safe action" fields (from Hermes checklist)

**Pattern:** the close summary must include two specific fields most agents
omit:
- **Not verified yet** — specific gaps, not "everything should work"
- **Next safe action** — one concrete action for the next session

**Why:** a fresh session opening the terminal state needs exactly these to
continue safely. Vague "done" or "should work" is the #1 handoff failure
mode (Hermes: "the biggest failure is not that the model forgets one fact;
it is that nobody can tell which facts are verified").

**Fix:** Step 7 of `/close` mandates both fields. "Not verified yet" must
name specific unverified claims (e.g., "production URL not propagated; rerun
live QA"), not generic hedges.

**Source:** Hermes Agent, "AI Agent Session Handoff Checklist."

### 3. Per-step completion criteria (from Cognizant "validation gates")

**Pattern:** each gate must define what "answered yes" means in terms of a
produced artifact, not just the operator's word.

**Why:** a gate answered "yes" without producing its completion artifact is
invalid — the loop would proceed on a false positive.

**Fix:** `/close` Step 6 defines per-step completion criteria:
- Step 2 (wiki): complete when ≥1 concept written AND retirement check passed
- Step 4 (handoff): complete when handoff(s) exist with `current_session_id == $sess`
- Step 5 (verify): complete when `/check` returned PASS or FAIL-with-hedge

**Source:** Cognizant, "Every step should define its execution conditions,
validation gates, and proceed or stop criteria."

### 4. Decision locking (from Cognizant "gate lock")

**Pattern:** once ACCOUNTING buckets are populated and confirmed, they are
locked for the `/close` run. The loop may append to "Not started" but must
not re-derive settled buckets.

**Why:** without the lock, the loop re-opens settled decisions, producing
oscillation rather than convergence (the model re-derives the same answer
each iteration).

**Source:** Cognizant, "Once gate_id is assigned, it MUST NOT change for
the remainder of this turnaround."

### 5. Per-iteration budget cap (from digitalapplied "un-bounded loops")

**Pattern:** max 2 loop iterations; after that, surface to the operator.

**Why:** "No timeouts, no budgets" is the un-bounded-loop anti-pattern. Both
flavors terminate at the credit-card limit or a human kill. A close-out loop
without a cap could spin on a gap that can't be resolved.

**Source:** digitalapplied, "Agentic Workflow Anti-Patterns" (Failure 04).

### 6. Restart-survival spot-check (from dev.to "test with real restarts")

**Pattern:** before declaring closed, read back ONE close-out artifact and
confirm it survives — opens, parses, provenance binds to this session.

**Why:** "Write your handoff. Then close the session. Then open a fresh
session and try to resume." If the artifact doesn't survive a read-back, the
close-out isn't durable.

**Fix:** `/close` Step 7 includes a restart-survival spot-check on the most
important handoff or wiki concept produced.

**Source:** dev.to, "Building Reliable State Handoffs Between AI Agent
Sessions," Lesson 4.

## Five multi-terminal / stale-data invariants (host-mandatory)

These are not from external sources — they are the host's existing
invariants (documented in `/handoff` Hard Constraints, `/aar` §0.1,
`/go` §0.5) applied to `/close`.

### 1. Multi-terminal isolation

`/close` only accounts for, reads state for, and writes state for **this
session + this terminal**. Identity resolved once at Step 0 via the
GROK→CLAUDE→WT_SESSION→TERMINAL_ID fallback chain. The ACCOUNTING
"Other sessions'" bucket exists specifically to keep concurrent sessions'
work out of this session's accounting.

### 2. Stale-data immunity

Shared directories (`P:/docs/handoffs/`, `P:/.data/wiki/concepts/`) are
mutated by concurrent sessions. Before trusting an artifact as "this
session's work," bind it to `(session_id, terminal_id)`:
- Handoffs: YAML `current_session_id` MUST match
- Wiki concepts: `source:` field MUST reference this session/date
- Commits: session tag or author filter

A file with the right name but wrong provenance belongs to another session.

### 3. Session-scoped (not file-scoped) idempotency

Covered above as improvement #1. Listed here as an invariant because it is
the structural consequence of invariants #1 + #2: in a shared filesystem,
file-existence cannot be the idempotency key.

### 4. Decision locking

Covered above as improvement #4. Listed here as an invariant because
oscillation is a multi-terminal hazard: two concurrent close-outs racing on
the same shared files amplify each other's uncertainty.

### 5. Terminal-scoped state writes

The close summary and per-run state go to
`P:/.artifacts/<termSafe>/close-state.md` — terminal-private. The durable
artifacts (handoffs, wiki concepts) ARE shared (they need cross-session
discoverability), but the session's *view of its own close-out* is
terminal-private. This mirrors `/aar`, `/go`, `/review` state-file convention.

## What the improvements changed in `/close`

| Step | Before | After |
|------|--------|-------|
| Hard constraints | (none) | §"Hard constraints" added: 5 invariants |
| Step 0 | session dir only | full identity fallback chain + `$stepDone` set |
| Step 1 | ACCOUNTING with all handoffs | session-filtered (`current_session_id == $sess`) + decision lock |
| Step 6 | re-run flagged steps | session-scoped idempotency guard + per-step completion criteria + decision lock |
| Step 7 | 9-field summary | + "Not verified yet" + "Next safe action" + restart-survival spot-check |

## Do's and don'ts

### Do
- Bind every artifact to `(session_id, terminal_id)` before trusting it
- Use in-memory `$stepDone` for idempotency, not file existence
- Lock ACCOUNTING buckets once confirmed
- Cap loop iterations (2)
- Read back one artifact before declaring closed
- Put session-private state in `.artifacts/<termSafe>/`

### Don't
- Don't count another session's handoffs in this session's ACCOUNTING
- Don't treat file existence as step completion (stale-data trap)
- Don't re-derive settled buckets in the loop (oscillation)
- Don't run the loop without a cap (un-bounded-loop anti-pattern)
- Don't write close-out state to shared paths (terminal isolation)
- Don't ship a close summary with "everything should work" as the gap field

## Mapping to the existing close-out stack

| Component | Role | Multi-terminal safe? |
|-----------|------|---------------------|
| `P:/AGENTS.md` § Session-close accounting | The requirement (advisory rule) | N/A (rule, not state) |
| `/close` skill | The mechanism (orchestrator with loop) | ✅ (this concept's invariants) |
| `/wiki`, `/aar`, `/debrief`, `/handoff`, `/check` | Delegated sub-procedures | Each enforces its own isolation |
| `P:/.artifacts/<termSafe>/close-state.md` | Terminal-private close-out state | ✅ (terminal-scoped by path) |
| `P:/docs/handoffs/`, `P:/.data/wiki/concepts/` | Shared durable artifacts | ⚠️ shared — provenance binding required |

## Falsifier

This design is wrong if:
- The session-scoped idempotency guard causes steps to re-run that shouldn't
  (the `$stepDone` set is too granular) → coarsen the keying
- The decision lock prevents legitimate re-derivation (a bucket genuinely
  needs to change post-Step-1) → allow append-only, not full re-derivation
- The "Not verified yet" / "Next safe action" fields are consistently vague
  → they're not load-bearing; drop them
- Concurrent close-outs still race despite isolation → the isolation is at
  the wrong layer (state files vs shared artifacts)

Re-evaluate if any pattern appears within 3 months across 5+ close-outs.

## Sources (scored CREDIBLE-lite)

| Source | Auth | Rec | Evid | Bias | Total | Role |
|--------|------|-----|------|------|-------|------|
| Hermes handoff checklist | 2 | 3 | 3 | 2 (vendor) | 10 | "Not verified yet" + "Next safe action" fields |
| Cognizant multi-agent debugging | 3 | 3 | 3 | 3 | 12 | Idempotency guard, validation gates, decision lock, restart-loop root cause |
| digitalapplied orchestration anti-patterns | 2 | 3 | 3 | 2 | 10 | Un-bounded-loop anti-pattern (iteration cap rationale) |
| dev.to reliable handoffs | 2 | 3 | 3 | 2 | 10 | Restart-survival testing; handoff anti-patterns (data dump, silent loader) |
| softawreck agent-toolkit (GitHub) | 2 | 2 | 2 | 2 | 8 | Session-handoff skill structure (confirming pattern) |

Phase 2 synthesis: parent-inherited model (subagent spawns rate-limited this session).

## Auto-related

- [[handoff-pre-compact-problems]]
- [[skill-enforcement-layers]]
- [[claude-code-skill-failure-patterns]]
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
