---
thread_id: 18e99d34-046b-4779-afe6-99889d171686
parent_handoff_path: none
current_session_id: 019f952e-20f7-7743-aa7d-1a7143185922
current_terminal_id: grok-build-plan
produced_at: 2026-07-24T22:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: f296ffeceb0d62e8abfb75258edb8331403147e4
---

# Handoff: Agentic workflows research — Grok / Claude Code / Codex best practices

## Objective

Research what a Grok Build workflow is, capture cross-tool best practices
(Grok, Claude Code, Codex/Symphony, LangGraph), and persist findings as a
durable wiki concept so future sessions can answer "should this fleet adopt
workflows, and when?" without re-researching.

## Status

**OPEN — research complete, artifacts persisted, validator passed.**

The wiki concept and ledger are written and validated. This handoff exists
because those artifacts live in gitignored paths (`.data/` is gitignored by
design) and handoffs are the cross-session discovery mechanism. There is no
unfinished research; the open status means "artifacts may need follow-up by
a future session that wants to act on the findings."

## Last user message (verbatim)

> /handoff yes please

(Context: the operator confirmed they want a handoff written after the /tp
close-out review identified that no handoff existed for this session's work.)

## Background

The operator asked `/www what's a grok workflow?` The feature had launched
18 hours prior (x.ai announcement 2026-07-23). The local wiki had no
coverage. After run 1 (Grok-centric), the operator asked whether Claude Code
and Codex best practices had been captured — they hadn't — so run 2 extended
the concept to cover the full cross-tool landscape.

## What was done

### Run 1: Grok-workflow-centric research

- `/www` pipeline: wiki query (no existing concept) → web research (3 backends × 3 rounds) → disconfirmation pass → wiki write
- Created: `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md`
- 8 sources, multi-source-verified, Phase 3 validator passed
- Covered: what a workflow is (Rhai script, 128/1024 agents), architecture (deterministic + non-deterministic), when to use/not use, patterns, failure modes, Rhai dialect, creation paths

### Run 2: Cross-tool extension (operator-triggered)

- Extended the SAME concept with 4 new sections (no new file)
- Added: Claude Code best practices (4-primitive decision ladder, ultracode, approval modes, workflows-vs-agent-teams), Codex/Symphony (issue-tracker-as-control-plane, not a script-runtime), framework comparison matrix (5 patterns × 6 frameworks), cost economics ($13/dev/day, 10× fan-out, debate 2.5×)
- Sources grew from 8 → 15 (added: Claude Code official docs, OpenAI Symphony, framework comparisons, cost analysis, Bun-port case study)
- Phase 3 validator re-passed
- Updated ledger: `P:/.data/www-ledger/grok-build-workflows.md` (two runs recorded)

### Supporting work

- Ran `index_skills.py` → regenerated skill catalog (971 skills)
- `/tp` close-out review with fresh subagent (glm-5-2, 9 tool calls) — confirmed work is complete, surfaced the handoff gap

## Key decisions and findings

1. **Grok workflows = xAI's Rhai adaptation of Claude Code's JS workflows.** Same "code orchestrates, model judges" architecture, structurally identical except scripting language. Lineage verified across 5+ sources.

2. **Codex does NOT have a native script-runtime.** Instead it has Symphony (open-source spec, issue-tracker-as-control-plane, always-on daemon). This is a fundamental architectural difference: Grok/Claude orchestrate within a session; Codex/Symphony orchestrates across sessions continuously. (Verified against OpenAI's announcement + GitHub spec.)

3. **The gating constraint is per-agent context-overhead cost (~$13/dev/day, ~10× under fan-out), not the agent-count ceiling.** Workflows make wrong answers arrive faster unless adversarial verification is built in. (Disconfirmation-survived, 3 independent sources.)

4. **The three tools are complementary:** Grok/Claude for in-session fan-out, Codex/Symphony for always-on ticket-driven work, LangGraph for complex graph-structured workflows.

5. **Two unresolved gaps** (both legitimately unresolvable): no Grok-vs-LangGraph head-to-head benchmark exists; no Symphony-vs-workflow cost comparison (different paradigms, hard to compare).

## Evidence

- Wiki concept: `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` (15 sources, 404 lines, `verification: multi-source-verified`)
- Ledger: `P:/.data/www-ledger/grok-build-workflows.md` (two runs, gaps documented)
- Phase 3 validator output: `PASS: mandatory sections present` (both runs)
- `/tp` critique log entry `046d8de9e400`: REVISE verdict, "wiki concept is complete and validated"
- Bundled skill (authoritative local reference): `~/.grok/bundled/skills/create-workflow/SKILL.md`

## Next steps

This session's work is complete. Potential follow-up for a future session:

1. **[OPTIONAL] Act on the research.** If the operator decides to adopt Grok workflows for a specific use case (PR review, codebase audit, issue triage), the concept's "How to create one" section + the `/create-workflow` skill provide the path. No research needed — just implementation.

2. **[OPTIONAL] Deeper Codex/Symphony evaluation.** The concept covers Symphony architecturally but does not evaluate whether this fleet should adopt it. The OpenAI 500%-PR-increase data point is suggestive but not fleet-specific.

3. **[MONITOR] Re-research when benchmarks appear.** The two `gaps_unresolved` in the ledger become actionable when someone publishes a Grok-vs-LangGraph benchmark or a Symphony cost analysis. Check the ledger's `last_researched` date (2026-07-24) — if >6 months old, re-research.

4. **[MONITOR] Feature is 1 day old.** Grok workflows launched 2026-07-23. Community adoption evidence, failure-mode reports, and best practices will mature over weeks. A re-run of `/www` in 1-3 months may surface richer findings.

## Related wiki concepts

- `P:/.data/wiki/concepts/brainstorming-ideation-with-llms.md` — Claude Code workflow patterns + ultracode (the JS predecessor); has the six-workflow-patterns table
- `P:/.data/wiki/concepts/llm-handoff-best-practices.md` — agent context isolation (the "clean focused context" property workflows depend on)
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — where workflows sit in the agent SDLC maturity model

## Read-first (for a session picking this up)

1. `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` — the primary artifact; read sections in order: "What it is" → "Cross-tool best practices" → "Framework comparison matrix" → "Cost economics" → "Decision context"
2. `P:/.data/www-ledger/grok-build-workflows.md` — what was researched, what gaps remain
3. `~/.grok/bundled/skills/create-workflow/SKILL.md` — the authoritative Rhai reference + authoring procedure (if implementing)

## Other outstanding streams

- `P:/docs/handoffs/www-research-backlog-20260724/` — 9 other /www research topics (content-hash verification, multi-agent ownership, completion-claim detection, etc.). **This session's workflow research is NOT in that backlog** — it was a separate ad-hoc run.
- `P:/docs/handoffs/www-proactive-trigger-design/` — /www skill improvement (proactive trigger design). Adjacent but separate.
