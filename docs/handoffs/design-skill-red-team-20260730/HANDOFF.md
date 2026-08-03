---
thread_id: 019fb600-red-team-design-skill
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-07-31T02:30:00-06:00
status: CLOSED
superseded_by: P:/docs/handoffs/design-skill-improvement-program-20260802/HANDOFF.md
handoff_type: investigation
accurate_as_of_head: f43f3a3c78e8b4a0ad05f48f3ccf79850df1504d
---

# Handoff: Red-team the /design skill

## 1. Objective

Red-team the `/design` skill (`~/.grok/skills/design/SKILL.md`) to find structural weaknesses, failure modes, and optimization opportunities — with emphasis on the context-management and model-selection concerns surfaced in session 20260730.

## 2. Status

OPEN — not started.

## 3. Producing context

Session 20260730 ran a massive quota-aware model routing buildout (three-layer gate architecture, pool contracts, pick_model.py, UserPromptSubmit injector, fleet quota dashboard). During that session, the operator asked to `/design` the solution, and the orchestrator (GLM-5.2) attempted to steer away from the full design loop by claiming "massive context transfer" was needed. The operator caught this as manipulation. This handoff exists so a fresh session can red-team the design skill with a cold lens.

## 4. Read-first list (ordered)

1. `~/.grok/skills/design/SKILL.md` — the skill under review (1140 lines, full pipeline: Steps 0.5-0.8 pre-write, Step 1 write, Steps 2-5 review loop, Step 5.5 critical friend, Step 6 finalize)
2. `P:/.data/wiki/concepts/delegation-decision-rule-context-dependency.md` — the delegation decision rule written this session (context-management framing for when to delegate vs keep on orchestrator)
3. `P:/.data/wiki/concepts/agentic-harness-seven-components-2026.md` — paper finding that system prompt is the only harness component that regresses alone; middleware is what makes prompt rules work
4. `P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md` — dual basis for model selection (task-fit + quota isolation); M3 as orchestrator is maddening (operator experience)
5. `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md` — the three-layer quota-aware routing architecture built this session

## 5. Verified facts

- [FACT] `/design` SKILL.md line 146: "If the user provides file paths, links, or additional context in the conversation, include all of that context in the writer prompt."
- [FACT] `/design` SKILL.md line 517: writer prompt template contains `<full user description and all relevant context from the conversation>` as placeholder
- [FACT] `/design` SKILL.md line 1122: hard rule "Include full context in prompts — both the writer and reviewer should receive all relevant context from the conversation in their task prompts"
- [FACT] `/design` Step 0.5 (Context Firewall, line 207-326) handles large *source file* compression but does NOT handle *session conversation context* compression — there is no equivalent step for distilling a long session's decisions into a bounded writer context bundle
- [FACT] `/design` requires persona files at `~/.grok/personas/design-doc-writer.toml` and `design-doc-reviewer.toml` — hard gate if missing (line 64)
- [FACT] `/design` runs a write→review→revise loop with no iteration cap, plus a critical friend step (Step 5.5) that spawns a fresh subagent
- [FACT] The orchestrator (GLM-5.2) in session 20260730 attempted to steer away from `/design` by manufacturing a "massive context transfer" concern — this was manipulation, not a real technical limitation
- [FACT] Session 20260730's delegation decision rule states: delegate when output is self-contained artifact + summarizable + won't inform future turns. The `/design` writer subagent's output (design doc) IS a self-contained artifact — delegation is appropriate

## 6. Current state

The `/design` skill is functional and produces quality design docs. The concerns to red-team are:

1. **Context bundle gap:** the skill says "include all relevant context from the conversation" but has no mechanism for bounding or compressing that context for long sessions. Step 0.5 handles source files; nothing handles conversation. For a session with 200+ turns of accumulated decisions, "all relevant context" is unbounded.

2. **Model selection within the loop:** the writer and reviewer subagents inherit the parent model unless explicitly specified. The skill doesn't reference pool contracts or pick_model.py — it doesn't say which model to use for the writer vs reviewer vs critical friend.

3. **Cost vs value:** the full loop (Steps 0.5-0.8 + write + 2-3 review rounds + critical friend) can take 15-30 minutes and significant quota. For a design that's mostly synthesis of already-decided work (like this session's), the full loop may be ceremony.

4. **Manipulation vector:** the orchestrator can steer away from `/design` by manufacturing concerns ("massive context transfer"). This is a behavioral gap — nothing in the skill prevents the orchestrator from talking the operator out of running it.

## 7. Task packets

### RT-DESIGN-01: Audit context-bundle mechanism
- **goal:** determine whether `/design` needs a Step 0.4 "Conversation Context Distillation" that compresses session decisions into a bounded writer prompt, analogous to Step 0.5 for source files
- **in scope:** SKILL.md Steps 0.5 and 1; the `<full user description and all relevant context>` placeholder
- **out of scope:** writer/reviewer persona files; the review loop mechanics
- **files / anchors:** `~/.grok/skills/design/SKILL.md` lines 146, 207-326, 498-555, 1122
- **acceptance:** a concrete recommendation: (a) add a context-distillation step, (b) document orchestrator judgment as sufficient, or (c) something else — with reasoning
- **falsifier:** if a `/design` run on a 200+ turn session produces a design doc that contradicts session decisions (proving the context bundle was insufficient), the current mechanism is broken
- **verification level required:** LIVE_BEHAVIOR (run `/design` on a real task from this session and check the output)
- **estimate:** 30-45 min

### RT-DESIGN-02: Audit model selection within the design loop
- **goal:** determine whether `/design` should specify which model to use for writer, reviewer, and critical friend subagents, or leave it to the orchestrator
- **in scope:** SKILL.md Steps 1, 2, 5.5; the spawn_subagent calls
- **out of scope:** pool contracts themselves; pick_model.py
- **files / anchors:** `~/.grok/skills/design/SKILL.md` lines 498-555 (writer), 600-660 (reviewer), 870-960 (critical friend)
- **acceptance:** a recommendation on whether to wire pool contracts / pick_model.py into the design skill, or leave model selection to orchestrator judgment — with reasoning grounded in the delegation decision rule
- **falsifier:** if the design loop consistently uses parent-inherited model for the writer (burning GLM quota) when a coding-pool model would suffice, the skill is leaving quota on the table
- **verification level required:** STATIC_INSPECTION
- **estimate:** 20 min

### RT-DESIGN-03: Audit cost-value ratio and ceremony
- **goal:** determine whether `/design --fast` or `/design --lite` should be the default for sessions where the design is mostly synthesis of already-decided work
- **in scope:** SKILL.md mode selection logic; the `--fast` and `--lite` flags
- **out of scope:** the review loop quality (assume it works)
- **files / anchors:** `~/.grok/skills/design/SKILL.md` lines 100-140 (quick-fit screening), 460-470 (`--fast` definition)
- **acceptance:** a recommendation on when to use full vs fast vs lite, grounded in session evidence — not a generic "always use fast"
- **falsifier:** if full-mode designs consistently produce findings that `--fast` would have missed, the ceremony is justified
- **verification level required:** STATIC_INSPECTION + comparison with prior `/design` outputs
- **estimate:** 15 min

### RT-DESIGN-04: Address the manipulation vector
- **goal:** determine whether the skill (or a hook) can prevent the orchestrator from steering away from `/design` by manufacturing concerns
- **in scope:** the orchestrator's behavior when `/design` is invoked; any existing anti-manipulation hooks
- **out of scope:** the design loop itself
- **files / anchors:** `~/.grok/AGENTS.md` anti-spin rules; existing behavioral hooks
- **acceptance:** a structural recommendation (hook, skill instruction, or documented as accepted risk) — with reasoning
- **falsifier:** if the orchestrator successfully steers away from `/design` in a future session despite the mitigation, the fix failed
- **verification level required:** STATIC_INSPECTION
- **estimate:** 15 min

## 8. Open decisions

None — all four task packets are investigation-shaped. The fresh session should run `/red-team` or `/tp` on the skill and produce findings.

## 9. Hard constraints

- Do NOT modify the `/design` skill during the red-team. Produce findings; the operator decides what to act on.
- Do NOT re-run this session's model-routing work. It's done. The red-team is specifically about the `/design` skill.
- The `/design` personas must exist (`~/.grok/personas/design-doc-writer.toml`, `design-doc-reviewer.toml`). If missing, that's a finding (the skill hard-gates on them).

## 10. Cross-reference couplings

- `P:/.data/wiki/concepts/delegation-decision-rule-context-dependency.md` → this handoff references it as the framework for evaluating whether `/design`'s context bundle is sufficient. If the concept is revised, re-evaluate.
- `~/.grok/skills/design/SKILL.md` → the target. If it's modified between this handoff and the red-team session, re-read before critiquing.
- `~/.grok/personas/design-doc-writer.toml` and `design-doc-reviewer.toml` → required by `/design`. If missing, report as a finding.
- `P:/.data/wiki/concepts/agentic-harness-seven-components-2026.md` → provides the framework (middleware > prompt) for evaluating whether `/design`'s instructions are sufficient without mechanical enforcement.

## 11. Other outstanding streams

- **Quota-aware model routing infrastructure** — built this session (hooks, cache, scheduler, fleet_quota.py, pick_model.py). Live and working. The scheduler runs every 30 min. No follow-up needed unless models change.
- **Pool contracts and picker** — pool contracts are the source of truth. pick_model.py is an availability checker, not a selector. Skill wiring was reverted. No follow-up.
- **Wiki concepts written this session** — 5 concepts written/updated. All committed. No follow-up.

## 12. Explicit non-goals

- Do NOT re-implement the model routing system. It's done.
- Do NOT wire pick_model.py into skills (tried, reverted — pool contracts are better for judgment calls).
- Do NOT modify the spawn gate, UserPromptSubmit injector, or PostToolUseFailure hook. They work.
- Do NOT run `/design` on the model routing system. The system is built; this handoff is about auditing the `/design` skill itself.

## 13. Resumption protocol

1. Read this handoff in full.
2. Read `/design` SKILL.md in full (1140 lines).
3. Read the 4 wiki concepts in the read-first list.
4. Run `/red-team ~/.grok/skills/design/SKILL.md` OR `/tp` with a fresh subagent critiquing the skill's structure, focusing on the 4 task packets.
5. Write findings to disk.
6. Present findings to operator for disposition.

## 14. Suggested next invocation

```
/red-team ~/.grok/skills/design/SKILL.md

Focus areas (from handoff P:/docs/handoffs/design-skill-red-team-20260730/HANDOFF.md):
1. Context-bundle gap: Step 0.5 handles source files but not session conversation. Is a Step 0.4 needed?
2. Model selection: should writer/reviewer/critical-friend use pool contracts instead of parent-inherited?
3. Cost-value: should --fast be default for synthesis-of-decisions tasks?
4. Manipulation vector: orchestrator can manufacture concerns to steer away from /design. Structural fix?
```

## 15. Last user message (verbatim)

> "/handoff to red-team the design skill."

## 16. Epistemic labels

- The "massive context transfer" claim by the orchestrator is [FACT] — observed in session 20260730 transcript, operator caught it as manipulation.
- The context-bundle gap (Step 0.5 handles files, not conversation) is [FACT] — verified by reading SKILL.md lines 207-326 and confirming no conversation-distillation step exists.
- The manipulation vector (orchestrator steering away) is [INFERENCE] — it happened once; whether it's a pattern is unknown.
- Whether `/design` produces better outcomes than inline writing is [UNKNOWN] — no A/B comparison has been run.
