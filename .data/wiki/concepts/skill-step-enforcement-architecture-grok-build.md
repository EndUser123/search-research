---
title: "Skill step enforcement architecture on Grok Build: what works, what doesn't, what's next"
created: 2026-08-05
source: session-2026-08-04/05 (declarative quality gates + UserPromptSubmit verification + /ship red-team)
tags: [skill-enforcement, grok-build, rhai-workflow, quality-gates, stop-hook, userpromptsubmit, activation-gap, ship, design-decision]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  The consolidated picture of skill step enforcement on Grok Build after
  full verification. Three mechanisms evaluated: (1) Stop hook quality gates
  — WORKS, post-execution, ~100% firing rate; (2) UserPromptSubmit hook
  injection — VERIFIED NON-FUNCTIONAL for native hooks (stdout, stderr, and
  exit 2 all tested and confirmed ignored); (3) Rhai workflow conversion —
  TARGET architecture, deterministic step enforcement via script-controlled
  flow. The interim architecture is quality gates (Layer 2). The target
  architecture is skill+workflow composition where the skill provides LLM
  judgment between phases and the Rhai workflow provides deterministic
  enforcement within each phase. This is the task-graph pattern from Trilogy
  AI (Subramaniam 2026) applied at the Grok Build skill layer.
relations:
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration.md
    type: extends — workflow engine capabilities
  - target: wiki/concepts/skill-enforcement-layers.md
    type: refines — Layer 1 (UserPromptSubmit) verified non-functional on Grok Build
  - target: wiki/concepts/declarative-quality-gates-skills-declare-evidence.md
    type: extends — quality gates as the interim Layer 2
  - target: wiki/concepts/userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build.md
    type: cites — UserPromptSubmit verification
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: addresses — the activation gap is the root problem this architecture solves
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: applies — workflow = code orchestrates, skill body = model judges
  - target: wiki/concepts/ship-phase-log-enforcement-design.md
    type: supersedes — this consolidates phase-log + quality gates + workflow into one picture
---

# Skill step enforcement architecture on Grok Build

## Decision context

**The problem:** the agent treats `/ship` (and other skills) as discussion prompts
instead of execution commands. Skills have 6-66% compliance rate per
[[llm-instruction-non-compliance-activation-gap-2026]]. The agent skips steps,
uses escape hatches, or discusses instead of executing. This is the same pattern
the Trilogy AI task-graph article documents:

> "LLMs don't execute instructions — they predict completions. The model optimizes
> for plausible completion, not thoroughness. Agents satisfice, they don't optimize."

Source: [Subramaniam 2026](https://trilogyai.substack.com/p/how-to-fix-your-ai-agents-keep-cutting)

**The question:** what enforcement mechanisms are available on Grok Build, and
which combination is optimal?

## Three mechanisms evaluated

### Mechanism 1: Stop hook quality gates — WORKS (interim architecture)

**What it is:** skills declare `quality_gates` in SKILL.md frontmatter naming
evidence artifacts. The Stop hook (`quality_gate.py` + `quality_gates_frontmatter.py`)
scans the transcript for invoked skills, then checks for evidence file existence
and session-scoped content matching.

**Status:** SHIPPED this session. The type/role bug that made skill detection
inert is fixed (41 skills detected from real transcript, was 0). Five bypass
paths in `ship_receipt.py` are closed (--session-id mandatory, --since HEAD
clamped, health-check conditional on files_changed, --llm-* documented as
display-only, check-run.json schema validation).

**Effectiveness:** ~100% firing rate (Stop hook fires on every turn end). Catches
missing evidence POST-execution — one round-trip cost (agent produces response,
Stop hook blocks, agent must re-execute).

**Limitation:** post-execution only. Cannot prevent the discuss-instead-of-execute
pattern before it happens. The agent wastes a turn producing a discussion response,
then gets blocked and has to redo the work.

### Mechanism 2: UserPromptSubmit hook injection — VERIFIED NON-FUNCTIONAL

**What it was supposed to be:** a UserPromptSubmit hook detects `/<skill-name>`
in the prompt, injects additionalContext telling the agent "execute, don't discuss."
Fires BEFORE the agent responds. Would prevent the discuss-instead-of-execute pattern.

**Status:** DEAD for native Grok hooks. Fully verified 2026-08-05 via three local
tests:

| Channel | Test | Result |
|---------|------|--------|
| stdout JSON (additionalContext) | Hook output valid JSON, hook fired (✓ 423ms) | Ignored — marker not visible |
| stderr | Hook printed marker to stderr | Not fed back to model |
| exit 2 | Hook exited 2 with marker | Recorded as ✗ failure in TUI, did NOT block, stderr not fed back |

Source: [[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]]

**Why:** UserPromptSubmit is a passive (non-blocking) event. Grok Build docs:
"For passive events, stdout is ignored; exit 0 on success." Only PreToolUse, Stop,
and SubagentStop process stdout/exit-code. All other events are passive.

**Third-party claims contradicted:** QAInsights/pleasantries claims exit 2 blocks
on grok-cli — FALSIFIED by local test. Vectorize/Hindsight claims additionalContext
works — may work via Claude Code plugin compat layer but is NOT verified for native
hooks and is definitively false for our registration path.

### Mechanism 3: Rhai workflow conversion — TARGET architecture

**What it is:** convert `/ship` from a skill (prose the LLM follows or ignores)
to a Rhai workflow that mechanically orchestrates: Phase 0 (detect) → Phase 1
(review + specialist spawn) → Phase 2 (fix-loop, conditional) → Phase 3 (verify)
→ Phase 4 (merge). The workflow controls the flow; the LLM does individual steps
within each phase.

**Why this is the structural fix:** the LLM literally cannot skip phases because
the Rhai script controls what runs next. This is the task-graph pattern from
Trilogy AI:

> "Don't give the model 12 steps in a single prompt. Give it one step. When it
> finishes, give it the next one. Make skipping structurally impossible."

**Grok Build workflow engine capabilities (from DeepWiki source analysis):**
- Conditional branching (Rhai if/else)
- Parallel agent execution (fan-out)
- State persistence (journal with sequence numbers and hashes)
- Deterministic resume (journal replay: cached results returned on resume, no re-execution)
- Budget control (agent_budget, token leases per subagent)
- TUI phase visualization (WorkflowBlock renders phase trail: Plan ✓ · Execute ● · Verify ○)

The journaling/resume capability means the workflow engine has checkpointing —
this was incorrectly attributed as exclusive to LangGraph earlier in the session.
The Rhai engine journals every host call; on resume, it replays from the journal
and returns cached results.

**Skill + workflow conditional routing:** skills provide LLM judgment BETWEEN
phases (which workflow to call next based on findings), Rhai workflows provide
deterministic enforcement WITHIN each phase. This is NOT a limitation — it's a
clean separation: the skill is the decision layer, the workflow is the execution
layer. The skill can invoke different workflows depending on conditions: "bugs
found → fix-loop workflow" vs "clean → verify workflow."

## The architecture

```
Current (interim):
  /ship skill (prose) → LLM follows or skips → Stop hook checks evidence → blocks if missing

Target:
  /ship skill (decision layer) →
    Phase 0 workflow → skill reads result → conditional branch
    → Phase 1 workflow (review) → skill reads findings → conditional branch
    → Phase 2 workflow (fix-loop, if bugs) → skill confirms
    → Phase 3 workflow (verify) → skill reads receipt
    → Phase 4 workflow (merge)
```

The skill stays as the entry point (operator types `/ship`). Internally, it
dispatches to Rhai workflows for each phase. The Stop hook quality gates remain
as the backstop — if the workflow somehow fails to produce evidence, the Stop
hook still catches it.

## What people do (from /www research)

| Pattern | Source | Platform | Liked? |
|---------|--------|----------|--------|
| Parallel fan-out + verification | xAI announcement, casetrue.com | Grok Build | ✓ speed (5-20x on independent tasks) |
| Human-in-the-loop with review gates | MikesBlogDesign | Grok Build | ✓ quality control without micromanaging |
| Phased implementation workflow | phaseddd/3DSmartDemo (101-line .rhai) | Grok Build | ✓ deterministic step enforcement |
| MCP sidecar for complex orchestration | dev.to (Roberto de la Cámara) | Claude Code | ✓ complex logic in Python, called as tool |
| Task graph with dependencies | Trilogy AI (Beads/OpenClaw) | OpenClaw | ✓ "can't skip because the tool controls the workflow" |
| Planner/Generator/Evaluator harness | Anthropic engineering blog | Any | ✓ separation of concerns |

Nobody is using LangGraph to enforce skill steps inside Grok Build or Claude Code.
The LangGraph-as-sidecar pattern runs complex logic as MCP tools but doesn't
enforce skill step ordering. The field's answer converges on the same insight:
control structure must live outside the LLM.

## Decision

**Interim (shipped):** Stop hook quality gates (Mechanism 1). Catches missing
evidence post-execution. One round-trip cost per skip.

**Target (next session):** Convert `/ship` to skill+workflow composition
(Mechanism 3). The skill dispatches to Rhai workflows per phase. The workflow
enforces deterministic step ordering. The Stop hook remains as backstop.

**Rejected for model injection:** UserPromptSubmit hook injection (Mechanism 2). Verified
non-functional on Grok Build native hooks — stdout/stderr/exit-2 all ignored by the model.

**Shipped (2026-08-05): Layer 1 operator-visible pre-check.** While
UserPromptSubmit cannot reach the MODEL, the TUI annotation (exit code +
stderr) IS visible to the OPERATOR. Hook at
`~/.grok/hooks/UserPromptSubmit_skill_precheck.py` detects `/<skill-name>`,
checks skill existence/staleness/depends_on/quality_gates plausibility, and
writes warnings to stderr. Exit 1 for critical (skill not found), exit 0 for
warnings. This is the correct Layer 1 design: the operator sees the warning
before the agent starts, and can rephrase or abort. It does NOT replace the
model-injection channel (which doesn't exist) — it adds an operator-visible
channel that does exist.

## Steelman of the rejected alternative

**LangGraph MCP sidecar:** a Python MCP server running a LangGraph graph for
`/ship`. Grok Build calls `ship_orchestrate(diff_path)` as an MCP tool. LangGraph
controls phases, conditional routing, typed state. Each node processes files via
filesystem access. Result written to files; tool returns small summary.

**Why it was reasonable:** LangGraph has typed state channels, checkpointing,
human-in-the-loop interrupts, and mature debugging (LangSmith). It's the
industry-standard graph orchestration framework.

**Why it was rejected for our case:** the Rhai workflow engine already provides
conditional branching, journaling/resume, budget control, and TUI integration —
natively, without external dependencies. The skill+workflow composition gives
the same conditional routing (skill judgment between phases) that LangGraph
provides via conditional edges. Adding LangGraph would mean maintaining a
separate Python process, MCP server, and bridge to Grok Build's tool surface
when the native workflow engine already does the job. [[grok-build-workflows-rhai-orchestration]]
documents that the journal-resume semantics are equivalent.

## Falsifier

This architecture is wrong if:
1. Rhai workflows prove unable to handle `/ship`'s conditional logic (fix-loop
   iteration, merge conflict detection) — test by prototyping the workflow
2. The skill+workflow conditional routing is insufficient (the LLM can't make
   good routing decisions between phases) — test by running the workflow end-to-end
3. Grok Build adds UserPromptSubmit stdout processing in a future release,
   making pre-execution enforcement viable — check `~/.grok/docs/user-guide/10-hooks.md`
4. The quality gates Stop hook proves sufficient on its own (the round-trip cost
   is acceptable and workflow conversion isn't worth the complexity) — measure
   skip rate across sessions after quality gates are live

## What this means for our workspace

1. **The quality gates system shipped this session IS the interim enforcement
   layer.** It works. The type/role bug is fixed. Five bypass paths are closed.
   The Stop hook fires on every turn end and checks for evidence.
2. **The `/ship`-as-discussion pattern has no pre-execution prevention.** The
   operator catches it. This is the known gap.
3. **Converting `/ship` to skill+workflow composition is the structural fix.**
   A Rhai workflow can't be discussed — it's a script that runs. The skill
   provides entry point and inter-phase judgment; the workflow provides
   deterministic phase enforcement.
4. **The handoff at `P:/docs/handoffs/skill-enforcer-port-grok-build-20260804/HANDOFF.md`
   documents 3 alternative paths for the UserPromptSubmit approach.** Path A
   (Claude Code plugin format) and Path B (.claude/settings.json dispatch) are
   untested. Path C (Stop-hook-only) is the current working state.
5. **Update [[skill-auto-invocation-reliability]]** — the gap "on Grok Build,
   the entire Claude-side enforcement is missing" is partially closed by quality
   gates (Layer 2) and will be fully closed by workflow conversion.

## Receipts

- `~/.grok/hooks/scripts/quality_gates_frontmatter.py` lines 442-470 — transcript scanning for skill invocations (scan_invoked_skills). The type/role fix at line 455 checks both `entry.get("type") != "user" and entry.get("role") != "user"`.
- `~/.grok/hooks/scripts/quality_gates_frontmatter.py` lines 370-431 — check_evidence function: glob + JSON session_id content filter. Checks existence and session matching, NOT content/schema validation (the schema validation was added to ship_receipt.py separately).
- `~/.grok/hooks/scripts/quality_gate.py` lines 1095-1133 — _quality_gate_check function calling _qg.check_quality_gates() at all 4 allow-paths.
- `~/.grok/skills/ship/__lib/ship_receipt.py` lines 1251-1310 — phase-log enforcement, specialist spawn verification, check-run.json and FINDINGS.md receipt checks.
- `~/.grok/docs/user-guide/10-hooks.md` line 89 — UserPromptSubmit: "Blocking? No". Line 304: "For passive events, stdout is ignored."
- [Grok Build source (DeepWiki)](https://deepwiki.com/xai-org/grok-build/4.6-workflow-engine) — Workflow Engine journaling: engine.rs lines 41-82 (journal with sequence number + hash), engine.rs lines 42-44 (cached result on resume).

## Sources

- [Trilogy AI: Why Your AI Agents Skip Steps](https://trilogyai.substack.com/p/how-to-fix-your-ai-agents-keep-cutting) (Subramaniam, Mar 2026) — task-graph enforcement pattern
- [Grok Build Workflow Engine (DeepWiki)](https://deepwiki.com/xai-org/grok-build/4.6-workflow-engine) — journaling, resume, budget control, state management
- [Grok Build Hooks docs](https://docs.x.ai/build/features/hooks) — passive events, stdout ignored
- [Vectorize/Hindsight Grok Build integration](https://hindsight.vectorize.io/sdks/integrations/grok-build) — additionalContext claim (unverified for native hooks)
- [QAInsights/pleasantries](https://github.com/QAInsights/pleasantries) — exit 2 claim (falsified by local test)
- [LangChain: How to turn Claude Code into a domain specific coding agent](https://www.langchain.com/blog/how-to-turn-claude-code-into-a-domain-specific-coding-agent) (Sep 2025) — Claude.md outperforms MCP for step guidance
- [Developers Digest: Claude Agent SDK vs LangGraph](https://www.developersdigest.tech/blog/claude-agent-sdk-vs-langgraph) (Jun 2026) — LangGraph runs in-process, no server required
- [Graph Harness academic paper](https://arxiv.org/html/2604.11378v1) (Hu Wei, Apr 2026) — scheduler-theoretic framework for LLM agent execution
- [MikesBlogDesign: Grok Build Workflow](https://mikesblogdesign.com/grok-build-workflow/) — human-in-the-loop pipeline with review gates
- [casetrue.com: Parallel Agent Workflows](https://www.casetrue.com/articles/grok-build-parallel-agent-workflows-guide) — best practices for parallel fan-out
- Local test hooks: `~/.grok/hooks/test-ups-injection.json`, `~/.grok/hooks/test-ups-exit2.json` — both cleaned up after testing

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[mermaid-and-code-visualization-skills-landscape]]
- [[grok-build-workflows-rhai-orchestration]]

