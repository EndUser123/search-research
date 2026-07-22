---
current_session_id: 019f7e24-0513-7773-875d-5a3e3051dc8f
parent_handoff_path: none
status: CLOSED
work_status: "Observations only — no actionable tasks"
created: 2026-07-20
---

# Session observations 2026-07-20 (019f7e24)

## Origin

This session started as "read this YouTube transcript" and grew into a multi-hour
arc spanning: transcript retrieval, cross-video architecture pattern synthesis,
a `/tp` critique of premature solutioning, a research deep-dive on Grok Build's
hook surface, two plugin implementations (one rejected, one shipped), and a
`/red-team` pre-check that exposed a self-preference failure.

## Observations

### 1. Premature solutioning is the dominant failure mode under horsepower bias

**Observation:** When asked "what's the best technical implementation?", I proposed
an MCP server and then a packet-runner extension *before* reading the `/agy` skill
(one directory over) or the `openai/codex-plugin-cc` canonical reference. This is
the exact failure pattern that `AGENTS.md` warns against ("Discovery Before
Implementation") and that I had multiple rules for.

**Reusable lesson:** Prose rules do not bind under context momentum when the user
asks an architecture question that I have priors about. The pull to answer from
priors is stronger than the pull to read source authority first. Only structural
guardrails (hooks, mandatory pre-checks) change the cost of the failure.

**Source:** session 019f7e24, transcript turns around the "best technical
implementation for codex" question.

### 2. `run_terminal_command` matcher is the root cause of exec-gate friction

**Observation:** The user's prior claim that "exec-gate was disabled because it
blocked reads" sounded implausible from the README (which lists read-only tools as
exempt). Reading the actual `hooks.json` matcher (`write|search_replace|run_terminal_command|spawn_subagent`)
revealed the truth: `run_terminal_command` is gated wholesale, which means every
bash-style read (`git status`, `ls`, `rg`, `Get-ChildItem`) hits the gate. The
README's exemption list is correct but irrelevant — the matcher catches the tool
name before the gate's internal exemption logic runs.

**Reusable lesson:** When investigating "why did this fail?", read the actual
matcher/dispatcher, not the README's stated exemptions. The matcher is the
ground truth; the exemption list is advisory.

**Source:** session 019f7e24, preflight for proposal-grounding-monitor.

### 3. LLM-as-judge ≠ deterministic claim verification

**Observation:** I cited a Galileo AI stat ("93% of LLM-as-judge users report
reliability issues") as evidence that LLM-judge hooks are unreliable. The user
corrected me: "we use LLMs to judge in Claude Code and do not have reliability
issues." Reading the actual Claude Code hook implementation (`P:/.claude/hooks/`)
revealed that the "judge" is a *deterministic* regex-based claim extractor plus
a deterministic evidence-matching engine — no LLM in the verification path at all.

**Reusable lesson:** The "LLM-as-judge" label conflates two architectures:
(a) LLM making holistic quality judgments (unreliable), and (b) deterministic
classifier + rule-bound decision (reliable). Industry stats about (a) do not
apply to (b). Before importing industry data to disqualify a local pattern, read
the local implementation.

**Source:** session 019f7e24, `/tp` turn on LLM-judge.

### 4. `/red-team` Pre-check 0 catches self-preference

**Observation:** When invoked to `/red-team` my own prior implementation report,
the skill's Pre-check 0 halted on a missing Completion Evidence Ledger. The
"Acceptance criteria check" table I shipped had columns `#, Criterion, Status`
but not the contract's required `claim_type, authority_required, evidence_provided,
protection_level, remaining_gap, next_action`. The pre-check caught that I had
shipped a "done" claim with a status table that looked like evidence but wasn't.

**Reusable lesson:** When writing a completion report, the CEC ledger format is
not optional decoration — it's the artifact that makes the report reviewable.
Without it, the report is an unverified claim, not evidence.

**Source:** session 019f7e24, `/red-team` invocation.

### 5. The "is this a replacement or an update?" framing question is high-value

**Observation:** When the user asks "is this a replacement or an update?" before
a restructure, they're testing whether I understand the change I'm about to make.
My honest answer ("replace the enforcement posture; update the implementation")
unlocked a cleaner execution than if I had just started editing.

**Reusable lesson:** When a task begins with a framing question from the user,
answer it explicitly before executing. The framing question is often the most
load-bearing part of the prompt.

**Source:** session 019f7e24, `/go` invocation for proposal-grounding-monitor.

### 6. Codex integration is a skill, not a plugin

**Observation:** The architecture decision (deferred to handoff at
`P:\tmp\codex-from-grok-handoff.md`) is to build a `/codex` skill modeled on
`/agy`, not an MCP server or packet runner. The decisive evidence: `/agy` is a
working pattern in this environment that proves direct shell-out is sufficient,
and `codex-plugin-cc`'s Claude-Code-specific overhead (subagents, Stop hook
review gate) doesn't transfer to Grok Build.

**Reusable lesson:** Before proposing new infrastructure for a delegation
capability, check whether a proven shell-out pattern already exists in the
installed skills. The `/agy` skill is the template; anything heavier needs
positive justification.

**Source:** session 019f7e24, handoff file at `P:\tmp\codex-from-grok-handoff.md`.

## Seeds (not yet developed)

- **Hook timeout budgeting:** Grok Build's 5s hook timeout is generous for
  Python startup but tight for transcript parsing on large sessions. A pattern
  for "spawn detached worker, read pre-computed state" (mentioned in
  `handong66/grok-plugin-codex` v0.2.0) may be reusable for heavier hooks.
- **Skill-as-guardrail-target:** The `proposal-grounding-monitor` plugin now
  exists. When writing a new skill (like `/codex`), the monitor will require
  the skill author to read `/agy` and canonical sources before the skill is
  considered grounded. This is the intended behavior, but it may surprise
  skill authors who don't know the monitor is active.

## What does NOT go here

- The `/codex` skill work itself → handoff at `P:\tmp\codex-from-grok-handoff.md`
- The proposal-grounding-monitor implementation → plugin at
  `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\`
- The four verified YouTube transcript summaries → already in session context
  and `%TEMP%` SRT files
