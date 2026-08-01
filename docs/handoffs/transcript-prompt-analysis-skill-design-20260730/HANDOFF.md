---
thread_id: e8439197-192d-4136-9519-7017f4310a6d
parent_handoff_path: none
current_session_id: 019fb0bd-b3a3-7600-87f7-9d56fa67cdac
current_terminal_id: grok-build-019fb0bd
produced_at: 2026-07-30T12:05:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 4de257ccaeb915f74a87637d380a4b528fde60d9
---

# Transcript Prompt Analysis → Skill Design Recommendations

## Objective

Scan 1,299 Grok Build session transcripts for human prompts that resulted in system improvements, classify them into domains, and determine which should become new skills or skill enhancements.

## Status

**READY_FOR_REVIEW** — Analysis complete, 154 improvement-producing prompts found across 10 domains. Design recommendations produced for `/prevent` and `/directive` placement. Skill graph limitations assessed. Awaiting operator decision on implementation priority.

## Producing context

- Date: 2026-07-30
- Session: `019fb0bd-b3a3-7600-87f7-9d56fa67cdac`
- Terminal: `grok-build-019fb0bd`

## Read-first list (ordered, with reasons)

1. `P:/tmp/scan_prompts.py` — the transcript scanner (re-runnable to track new sessions)
2. `P:/.data/wiki/concepts/skill-graph.md` — the auto-generated skill dependency graph (assessed for representational power)
3. `P:/.data/wiki/scripts/build_skill_graph.py` — graph builder (assessed for schema extensibility)
4. `P:/.data/wiki/capabilities/` — capability contract stubs (assessed for richer metadata potential)

## Verified facts (with source paths)

- [FACT] 1,299 `chat_history.jsonl` files exist under `C:\Users\brsth\.grok\sessions\P%3A%5C\` (scanner output)
- [FACT] 154 improvement-producing prompts found across 10 domains (scanner output: `call_d23212d4e63640b996d6afd2.log`)
- [FACT] Domain distribution: hook-enforcement (59), meta-improvement (36), model-routing (24), knowledge-capture (17), workflow-friction (10), config-rules (10), skill-creation (8), recurring-fix (8), automation (7), prompt-engineering (6)
- [FACT] 64 skills currently exist in the workspace (verified via directory scan)
- [FACT] Skill graph schema has 4 fields per skill: `delegates_to`, `consumes_provider`, `provides`, `domain` (verified from `build_skill_graph.py`)
- [FACT] 13 domains in the graph: analysis, cross-model, design, discovery, fleet-ops, implementation, infrastructure, knowledge, lifecycle, orchestration, review, self-improvement, testing
- [FACT] 69 capability contract stubs exist in `P:/.data/wiki/capabilities/` (verified via `list_dir`)
- [FACT] Capability stubs are typically 2-3 lines with `Inputs:` and `Outputs:` only (verified by reading `root-cause-analysis.md`, `after-action-review.md`)

## Current state

### What's done
- Scanner written and run against all 1,299 sessions
- 154 prompts classified into 10 domains
- 7 prioritized recommendations produced (2 new skills, 5 enhancements)
- `/prevent` and `/directive` design contracts defined
- Skill graph representational gaps identified (6 missing dimensions)
- Two implementation paths proposed (enhance graph schema vs enrich capability contracts)

### What's not done
- No skills created or modified
- No capability contracts written for prevention-design or directive-capture
- No scanner committed to a tracked location (currently in gitignored `P:/tmp/`)

## Analysis findings

### Top domains by prompt frequency

| Domain | Prompts | Pattern |
|--------|---------|---------|
| Hook enforcement | 59 | Operator repeatedly tunes quality gate, false positives, stale receipts |
| Meta-improvement | 36 | "How do we improve our system?" — recurring meta-question |
| Model routing | 24 | Which model for which task, quota conservation, fallback |
| Knowledge capture | 17 | "Remember this", "document this decision" |
| Workflow friction | 10 | "Too many steps", "lowest friction possible" |
| Config/rules | 10 | "Add a rule", "from now on" |
| Skill creation | 8 | "Turn this into a skill" |
| Recurring fixes | 8 | "This keeps happening", "still broken" |
| Automation | 7 | "Why do we always have to", "shouldn't have to" |
| Prompt engineering | 6 | "Improve the skill", "better prompt" |

### `/prevent` placement decision

**Decision:** `/prevent` is a **prevention-design phase** best owned as a mode of `/aar` (`/aar --prevent`), not a standalone skill.

**Rationale:**
- Input: verified root cause + prevention goal + evidence
- Output: selected control mechanism + authority target + acceptance test
- It composes `/why` (root cause) and `/aar` (improvement governance), then routes implementation to `/go`
- The graph flow: `/why → /aar --prevent → /skill-dev | /go → /check`

**Contract:**
```yaml
inputs: {problem, prevention_goal, evidence, known_root_cause?, scope, constraints}
outputs: {root_cause_status, prevention_strategy, mechanism, authority_target, acceptance_criteria, implementation_route}
hard_gate: no implementation recommendation if root cause is only inferred
```

### `/directive` placement decision

**Decision:** `/directive` is an **intent-capture and authority-routing** capability, best owned as detection in `/notice` plus persistence in `/wiki`, not a standalone skill.

**Rationale:**
- It classifies operator instructions ("from now on", "remember that") into: rule, decision, task, correction, observation
- Routes each to the correct authority target: AGENTS.md, SKILL.md, wiki concept, task, handoff
- Does not execute autonomously — capture_only mode must not mutate runtime code
- The graph flow: `operator message → /notice → directive classification → /wiki | AGENTS.md | SKILL.md | /tasks`

### Skill graph limitations

The current graph **cannot** represent:
1. Workflow position / temporal ordering (can't show `/why → /aar → /prevent → /go`)
2. Trigger conditions (can't show *when* a skill fires)
3. Composition vs delegation (can't distinguish calling from embedding)
4. Modes/sub-modes (can't show `/aar --prevent` vs `/aar --measure`)
5. Authority targets (can't show what a skill writes to or governs)
6. Problem-type mapping (domains too coarse — both /prevent and /directive would land in `self-improvement`)

### Recommended path

**Path B now, Path A later:** Use the graph as-is. Put richer metadata (triggers, workflow position, composition, authority targets) in capability contract stubs. Enhance the graph schema when the composition graph pilot (A2b) is operational.

## Task packets

### PKT-1: Move scanner to tracked location and document
- **Goal:** Move `P:/tmp/scan_prompts.py` to a permanent location and add documentation
- **In scope:** Script relocation, README, wiki concept for the methodology
- **Out of scope:** Automating the scanner on a schedule
- **Files:** `P:/tmp/scan_prompts.py` → `P:/.agents/scripts/scan_improvement_prompts.py`
- **Acceptance:** Script runs from new location and produces same results
- **Verification:** `python P:/.agents/scripts/scan_improvement_prompts.py` produces domain counts

### PKT-2: Add `prevention-design` capability contract
- **Goal:** Write a capability contract stub for prevention-design that documents placement
- **In scope:** `P:/.data/wiki/capabilities/prevention-design.md`
- **Acceptance:** Contract has triggers, workflow position, inputs/outputs, authority targets
- **Verification:** `grep -l "prevention" P:/.data/wiki/capabilities/` returns the file

### PKT-3: Add `directive-capture` capability contract
- **Goal:** Write a capability contract stub for directive-capture
- **In scope:** `P:/.data/wiki/capabilities/directive-capture.md`
- **Acceptance:** Contract has detection patterns, authority routing table, scope classification
- **Verification:** `grep -l "directive" P:/.data/wiki/capabilities/` returns the file

### PKT-4: Add prevention phase to /aar (after operator approval)
- **Goal:** Add `--prevent` mode to `/aar` that takes a diagnosed root cause and designs a durable control
- **In scope:** `C:/Users/brsth/.grok/skills/aar/SKILL.md`
- **Out of scope:** Hook implementation, AGENTS.md rule writing
- **Acceptance:** `/aar --prevent` produces a structured prevention packet
- **Verification:** Cold-start session can follow the prevention packet without re-deriving

### PKT-5: Add directive detection to /notice (after operator approval)
- **Goal:** Add directive-candidate detection to `/notice` trigger scoring
- **In scope:** `C:/Users/brsth/.grok/skills/notice/SKILL.md`
- **Acceptance:** `/notice` detects "from now on", "remember that" patterns and classifies them
- **Verification:** Test directive phrases produce structured candidates

## Open decisions

### Decision 1: Which recommendations to implement first?
- **Options:** (A) `/aar --prevent` mode, (B) `/notice` directive detection, (C) capability contracts only, (D) graph schema enhancement
- **Selection criterion:** highest leverage × lowest effort
- **Current lead:** (C) capability contracts first (small effort, documents the design for future implementation), then (A) `/aar --prevent` (highest leverage)
- **Evidence needed:** operator prioritization

### Decision 2: Should the scanner be scheduled?
- **Question:** Should `scan_improvement_prompts.py` run on a schedule to track improvement-producing prompt trends over time?
- **Options:** (A) Manual invocation, (B) Weekly scheduled task, (C) Part of `/aar`
- **Current lead:** (A) Manual — the scanner is fast (43s for 1299 sessions) and the value is in periodic comparison, not real-time monitoring

## Hard constraints

1. Do NOT create standalone `/prevent` or `/directive` skills without operator approval — the analysis recommends modes of existing skills
2. Do NOT modify the skill graph schema yet — wait for the composition graph pilot
3. The scanner must remain read-only (no session file mutation)

## Cross-reference couplings

- `P:/tmp/scan_prompts.py` → reads from `C:\Users\brsth\.grok\sessions\P%3A%5C\*/chat_history.jsonl`. If the JSONL format changes, the scanner breaks.
- `/aar` skill → would gain `--prevent` mode. The AAR skill already delegates to `/why`, `/check`, `/go`, `/review`.
- `/notice` skill → would gain directive detection. Notice already has motivation scoring and trigger conditions.
- Skill graph (`P:/.data/wiki/concepts/skill-graph.md`) → auto-generated. Adding capability contracts requires running `build_skill_graph.py` to pick them up.

## Other outstanding streams (not handed off)

- **A2b-3 deferral adapter correction** — separate handoff at `a2b3-deferral-adapters-corrected-20260730`
- **Semantic skill composition graph pilot** — ongoing, design doc at `P:/docs/semantic-skill-composition-graph-design-20260730.md`

## Explicit non-goals

- Do NOT implement `/prevent` or `/directive` as standalone skills
- Do NOT modify the skill graph schema (`build_skill_graph.py`)
- Do NOT modify `/aar` or `/notice` without operator approval
- Do NOT automate the scanner on a schedule yet

## Resumption protocol

1. Read the scanner output to see the full prompt list: `C:\Users\brsth\.grok\sessions\P%3A%5C\019fb0bd-b3a3-7600-87f7-9d56fa67cdac\terminal\call_d23212d4e63640b996d6afd2.log`
2. Ask the operator which recommendations to prioritize
3. Write capability contracts first (small effort, documents the design)
4. Then implement the selected skill enhancements

## Suggested next invocation

```
The transcript analysis found 154 improvement prompts in 10 domains. The top recommendations are: (1) capability contracts for prevention-design and directive-capture, (2) /aar --prevent mode, (3) /notice directive detection. Which should we implement first?
```

## Last user message (verbatim)

> "Is our skill graph sophisticated enough to show the domain(s) of existing skills optimally, and of prevent and directive?"

## Epistemic labels per claim

- Prompt counts and domain distribution: `[FACT]` (scanner output cited)
- Skill count (64): `[FACT]` (directory scan verified)
- Graph schema fields: `[FACT]` (source code read)
- `/prevent` and `/directive` placement recommendations: `[INFERENCE]` — based on skill graph analysis and existing capability ownership
- "Path B now, Path A later": `[RECOMMENDATION]` — grounded in the composition graph pilot status
