---
thread_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
parent_handoff_path: none
current_session_id: 019ffc5c-22cc-7453-a45c-613fb50d6cf1
parent_session: none
current_terminal_id: console_16799b2f-5107-4491-a937-1794
produced_at: 2026-08-14T02:30:00Z
last_updated_by: 019ffc5c-22cc-7453-a45c-613fb50d6cf1
last_updated_at: 2026-08-14T02:30:00Z
status: open
handoff_type: architectural
accurate_as_of_head: f2c2a51
assigned_to: grok
assigned_at: 2026-08-14T04:32:33
assigned_by: 019ffc5c-22cc-7453-a45c-613fb50d6cf1
---




# Scanner skill decomposition: /defect, /risk, /insight

## Objective

Decompose the fleet's ~15 scanning skills into 3 unified skills (/defect, /risk, /insight) named by finding type, then consolidate their functions so the operator asks "what's broken?" not "scan my code."

## Status

OPEN — design complete, implementation not started

## Producing context

- Date: 2026-08-13/14
- Session: 019ffc5c-22cc-7453-a45c-613fb50d6cf1
- Terminal: console_16799b2f-5107-4491-a937-1794

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/scanner-skill-landscape-inventory-and-capability-map.md` — the complete inventory of all scanning skills organized by domain (written this session)
2. `P:/.data/wiki/concepts/discover-first-prompt-patterns-for-unbiased-work-item-discovery.md` — the category taxonomy (blocker/error/inefficiency/risk/opportunity/unknown/other) and 5 bias-checking templates from the Perplexity research
3. `P:/.data/wiki/concepts/todo-triage-insight-skill-separation-crud-vs-analysis-vs-discovery.md` — the architectural decision for skill separation (CRUD vs analysis vs discovery)
4. `P:/.data/wiki/concepts/delegation-memory-evidence-based-model-routing.md` — evidence-based routing vision (Phase 1/2)
5. `P:/.data/wiki/concepts/orchestration-engine-decision-langgraph.md` — LangGraph chosen as orchestration engine (written this session)
6. `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — the SDLC lifecycle mapping against industry standard
7. `C:/Users/brsth/.grok/skills/todo/SKILL.md` — the current /todo scanner including Step 0.5 (parallel /insight + /aar subagents)
8. `C:/Users/brsth/.grok/skills/insight/SKILL.md` — the current /insight skill (10 categories, dual-stream routing)
9. `P:/.data/wiki/concepts/capability-node-architecture.md` — the two-layer capability node system (lean contracts + design notes)
10. `P:/.data/wiki/concepts/skill-graph-representational-limits.md` — why the skill graph can't represent scanning relationships (and how capability nodes fix it)
11. `P:/packages/.chat_exports/2026-08-10_-_Kestra_For_LLM_Skills.md` — the orchestration bake-off comparison (Python vs LangGraph vs Kestra vs Temporal)
12. `P:/packages/.chat_exports/2026-08-10_-_Explain_Agentic_Skill_Graphs.md` — the layered architecture proposal (capability graph + orchestration engine + model router)

## Verified facts

- [FACT] The current fleet has ~15 scanning skills named by scanning target (code, transcript, fleet) rather than by finding type (defect, risk, opportunity) — `scanner-skill-landscape-inventory-and-capability-map.md`
- [FACT] Every scanning skill's functions can be mapped to exactly one of three target skills: /defect, /risk, /insight — decomposition completed this session, full function map in conversation
- [FACT] 4 capability nodes already exist making scanning relationships machine-readable: scan-workspace-state, scan-code-quality, scan-session-transcript, scan-risk — committed session 019ffc5c
- [FACT] 12 skills already declare scan-* capabilities in their provides: frontmatter — committed session 019ffc5c
- [FACT] The skill graph now represents scanning relationships (Providers by capability section) — regenerated and committed
- [FACT] /todo already invokes /insight + /aar as parallel subagents (Step 0.5) and merges findings with category tags + "other" escape hatch — committed session 019ffc5c
- [FACT] /insight already absorbs /capture, /friction, and /harvest into a single skill with 5 modes (default, --skills, --fleet, --coverage, --improve)
- [FACT] Category tags (blocker/error/inefficiency/risk/opportunity/unknown/other) are implemented in /todo items and renderer — committed session 019ffc5c
- [FACT] The Perplexity research conversation defines 5 reusable bias-checking prompt templates with speculation flags, contradiction scans, and perspective-balance reviews — `discover-first-prompt-patterns-for-unbiased-work-item-discovery.md`

## Current state

### Shipped this session

1. **Exploration gate hooks** (4 commits) — UserPromptSubmit + PreToolUse hybrid system that blocks unauthorized writes during exploration mode. Permission-mode aware, knowledge-path scope, audit log, SessionEnd cleanup.
2. **Verification receipt writer fix** — pattern reorder so compound commands classify correctly (the `/tp` that started the session).
3. **`/todo` Step 0.5** — parallel `/insight` + `/aar` subagents invoked automatically by `/todo`.
4. **Category tags + "other" escape hatch** — every /todo item now has a category tag; subagent prompts include anti-tunnel-vision instruction.
5. **Scanner landscape wiki concept** — complete inventory of all scanning skills by domain.
6. **4 capability nodes** — scan-workspace-state, scan-code-quality, scan-session-transcript, scan-risk.
7. **Skill graph regenerated** — now represents scanning relationships.
8. **3 wiki concepts from .chat_exports** — discover-first patterns, delegation memory, todo-triage-insight separation.
9. **Perplexity export split** — 56MB JSON → 1363 individual markdown files with secret redaction.
10. **Scanner decomposition analysis** — every function from ~15 skills mapped to /defect, /risk, or /insight.

### Not yet done

- `/defect` skill does not exist
- `/risk` exists but doesn't absorb `/aar` Phase 4/8.5, `/why` pattern mode, `/maintain`, `/behave`
- `/insight` exists but doesn't absorb `/aar` Phase 5/6, `/dream`, `/tp explore`, `/triage`
- The decomposition is a design analysis; no skills have been renamed, merged, or refactored
- Delegation memory (evidence-based routing) is unbuilt

## Task packets

### AC-CONSOLIDATE-01: Create /defect skill

- **goal:** Unified defect-detection skill that absorbs functions from /review, /check, /grok-verify, /trace, /fmea, /doc-check, /skill-dev (defect scan), /why (current failure), /todo Step 0 (defect sources)
- **in scope:** New SKILL.md at ~/.grok/skills/defect/; mode routing for code-review, session-verify, logic-trace, pipeline-fmea, doc-check, skill-defect-scan; delegates to existing scanner infrastructure where possible
- **out of scope:** Removing existing skills (keep as aliases during transition); /risk and /insight consolidation
- **files:** ~/.grok/skills/defect/SKILL.md (new); frontmatter updates to add provides: [scan-code-quality] alias
- **acceptance:** /defect --code runs a code review equivalent to /review; /defect --session runs a check equivalent to /check; the operator can invoke /defect and get defect findings without knowing which sub-scanner to use
- **falsifier:** /defect produces findings that /review would have caught; if /defect --code misses a P0 finding that /review catches, the consolidation is incomplete
- **verification level:** LIVE_BEHAVIOR
- **estimate:** 2-4 hours (mostly SKILL.md composition + mode routing; existing scanners do the work)

### AC-CONSOLIDATE-02: Expand /risk to absorb risk-domain functions

- **goal:** /risk absorbs risk-detection functions from /aar (Phase 4 patterns, Phase 8.5 triage), /why (pattern mode with wiki feedback), /maintain (fleet health), /behave (verdict-transition integrity), /todo Step 0 (risk sources: debt, propagation, finding_coverage)
- **in scope:** Add modes to /risk: --patterns (cross-session recurring), --fleet (maintain-style health), --post-mortem (behave-style verdict analysis); update /todo Step 0.5 to invoke /risk instead of /aar for risk-domain findings
- **out of scope:** /defect and /insight consolidation; /aar remains for retrospective use
- **files:** ~/.grok/skills/risk/SKILL.md (expanded)
- **acceptance:** /risk --patterns finds recurring failure modes that /aar Phase 4 would have caught; /risk --fleet produces the maintain health report
- **falsifier:** /risk misses a recurring pattern that /aar would have identified
- **verification level:** LIVE_BEHAVIOR
- **estimate:** 2-4 hours

### AC-CONSOLIDATE-03: Expand /insight to absorb opportunity-domain functions

- **goal:** /insight absorbs opportunity-detection from /aar (Phase 5 value accounting, Phase 6 opportunity discovery), /dream (offline consolidation), /tp explore (system decomposition), /triage (category-bounded review)
- **in scope:** Add modes to /insight: --value (aar Phase 5/6), --consolidate (dream-style synthesis), --explore (tp explore decomposition), --triage (category-bounded review); update /todo Step 0.5 to invoke /insight for all opportunity-domain findings
- **out of scope:** /defect and /risk consolidation; /aar remains for retrospective; /tp remains for live critique
- **files:** ~/.grok/skills/insight/SKILL.md (expanded)
- **acceptance:** /insight --value produces value accounting equivalent to /aar Phase 5; /insight --explore decomposes systems equivalent to /tp explore
- **falsifier:** /insight misses an opportunity that /aar Phase 6 or /dream would have surfaced
- **verification level:** LIVE_BEHAVIOR
- **estimate:** 3-5 hours

### AC-CONSOLIDATE-04: Wire bias-checking templates into subagent prompts

- **goal:** The 5 bias-checking templates from the Perplexity research (evidence anchoring, contradiction scan, dual-goal, multi-perspective, self-evaluation) are wired into /insight and /risk subagent prompts
- **in scope:** Update /insight Step 0.5 subagent prompt in /todo SKILL.md to require: speculation flags, contradiction checks; update /risk specialist prompts to include dual-goal analysis
- **out of scope:** New infrastructure; this reuses existing subagent dispatch
- **acceptance:** Subagent output includes structured bias signals (speculation: true/false, contradiction_evidence: text)
- **falsifier:** Subagent output has no structured bias signals
- **verification level:** UNIT_TEST
- **estimate:** 1-2 hours

### AC-CONSOLIDATE-05: Update /todo to invoke /defect, /risk, /insight

- **goal:** /todo Step 0.5 invokes /defect, /risk, and /insight as 3 parallel subagents (instead of /insight + /aar), merging by tier
- **in scope:** Update /todo SKILL.md Step 0.5 subagent prompts and merge logic; update renderer to group by tier (defect → risk → opportunity)
- **out of scope:** Creating the 3 skills (that's AC-01 through AC-03)
- **acceptance:** /todo output groups items by tier within each NOW/NEXT/LATER section; defects first, then risks, then opportunities
- **falsifier:** /todo output does not group by tier or mixes defect/risk/opportunity without visual distinction
- **verification level:** LIVE_BEHAVIOR
- **estimate:** 1-2 hours

## Open decisions

### D1: Do existing skills become aliases or get deleted?

- **Options:** (A) Keep as aliases that route to the new skills; (B) Delete after migration; (C) Keep as-is and only the new skills invoke them internally
- **Selection criterion:** Operator familiarity vs. cognitive load. Aliases preserve muscle memory but add surface area. Deletion is clean but breaks existing handoffs/docs.
- **Current lead:** (A) aliases during transition, with a wiki concept documenting the mapping. Defer deletion until no handoffs reference the old names.
- **What would change:** If operators consistently use the new names within 30 days, delete the aliases.

### D2: Does /aar survive as a standalone skill?

- **Options:** (A) /aar stays as the always-deep retrospective (its functions split across /risk and /insight but the unified reconstruction is valuable); (B) /aar is fully absorbed, its functions distributed
- **Selection criterion:** Whether the operator values the unified retrospective report or prefers tier-separated findings
- **Current lead:** (A) /aar stays — its evidence-grounded reconstruction with cross-model audit is a different work product than tier-separated scanning
- **What would change:** If /aar findings consistently duplicate /risk + /insight, absorb it.

### D3: Does /dream merge into /insight --consolidate?

- **Options:** (A) /dream becomes /insight --consolidate; (B) /dream stays separate (it writes candidate proposals, not findings)
- **Selection criterion:** Whether dream proposals are insight-shaped (improvement opportunities) or a distinct work product (strategic proposals for operator promotion)
- **Current lead:** (B) /dream stays separate — it writes proposal files for promotion, not inline findings
- **What would change:** If dream proposals are consistently treated as insight findings.

### D4: Orchestration engine — RESOLVED: LangGraph

- **Decision:** LangGraph is the orchestration engine for skill pipeline execution. See `[[orchestration-engine-decision-langgraph]]`.
- **Rationale:** Maps directly onto /go phase architecture (state + nodes + edges + conditional routing + checkpointing + interrupts). Python-native, no external server. Deterministic enforcement breaks the ~50% prose-rule compliance ceiling.
- **Validation step:** Before broad adoption, run the bake-off — take 5-10 existing /go transitions, encode as LangGraph graph, compare against prose-driven orchestration for skipped capabilities, invalid transitions, and premature completions.

### AC-CONSOLIDATE-06: LangGraph bake-off — validate deterministic enforcement

- **goal:** Take 5-10 existing /go transitions, encode as a LangGraph graph, compare against prose-driven orchestration for skipped capabilities, invalid transitions, and premature completions
- **in scope:** Pick one real task that previously caused the agent to violate /go; implement the same mini-pipeline in LangGraph (recon → validate → implement → test → review → complete); run adversarial tests (lying agent, premature completion, missing evidence); measure outcomes
- **out of scope:** Full fleet migration to LangGraph; rewriting all skills
- **files:** New `P:/packages/langgraph-pilot/` directory with the graph definition, test cases, and results
- **acceptance:** LangGraph enforcement measurably reduces skipped capabilities and invalid transitions compared to prose-driven /go (same task, same models, same prompts)
- **falsifier:** LangGraph shows no improvement over prose rules for the same transitions (dependency adds cost without benefit)
- **verification level:** LIVE_BEHAVIOR
- **estimate:** 3-4 hours (graph definition + test cases + comparison)

## Hard constraints

- `/todo` remains the aggregation hub — it invokes the 3 scanners in parallel and merges by tier
- `/tp` remains the live critique tool (not a scanner — it's a dialogue)
- No skill is deleted without a deprecation period (aliases first, deletion later)
- The capability node architecture is the machine-readable layer — frontmatter `provides:` declarations drive routing
- Category tags (blocker/error/inefficiency/risk/opportunity/unknown/other) are the mechanism for tier filtering in the unified output

## Cross-reference couplings

- `P:/.data/wiki/concepts/scanner-skill-landscape-inventory-and-capability-map.md` → this handoff's decomposition. If the inventory changes, re-verify the function map.
- `P:/.data/wiki/capabilities/scan-*.md` → the 4 capability nodes. If new scan capabilities are added, update the graph.
- `C:/Users/brsth/.grok/skills/todo/SKILL.md` Step 0.5 → currently invokes /insight + /aar. After AC-05, invokes /defect + /risk + /insight.
- `C:/Users/brsth/.grok/skills/insight/SKILL.md` → currently absorbs /capture, /friction, /harvest. After AC-03, also absorbs /aar Phase 5/6, /dream, /tp explore, /triage.
- `P:/.data/wiki/concepts/discover-first-prompt-patterns-for-unbiased-work-item-discovery.md` → the 5 templates. After AC-04, wired into subagent prompts.

## Other outstanding streams

- **Exploration gate hooks** — shipped this session (4 commits in ~/.grok). Live testing in a non-bypass session is the remaining verification gap.
- **Delegation memory** — Phase 1 (evidence collection) scoped in `delegation-memory-evidence-based-model-routing.md`. Unbuilt. Separate from this consolidation.

## Explicit non-goals

- Do NOT delete existing skills during this consolidation — use aliases
- Do NOT change /tp — it's a dialogue tool, not a scanner
- Do NOT build a task store — handoffs are the persistence layer (confirmed by operator this session)
- Do NOT add evidence anchoring to subagent prompts — subagents already have evidence via transcript access (confirmed by operator this session)

## Resumption protocol

1. Read this handoff and the 8 read-first files
2. Start with AC-CONSOLIDATE-01: create `/defect` SKILL.md that routes to existing scanners (/review, /check, /trace, /fmea) as modes
3. Test `/defect --code` against a known diff to verify it produces equivalent findings to `/review`
4. Proceed to AC-02 (/risk expansion) and AC-03 (/insight expansion) in parallel
5. After all 3 skills exist, wire them into `/todo` Step 0.5 (AC-05)
6. Finally, wire bias-checking templates (AC-04)

## Suggested next invocation

```
/go Read P:/docs/handoffs/open-work/scanner-skill-decomposition/HANDOFF.md and implement AC-CONSOLIDATE-01: create the /defect skill that routes to existing defect-detection scanners as modes. Start with the read-first list, then compose the SKILL.md.
```

## Last user message (verbatim)

> "Ok, let's use '/defect', '/risk', and '/insight' as the 'new' names. if we take all our skills, and decompose them into functions or modules, they can be mapped to '/defect', '/risk', and '/insight'?"

## Epistemic labels

- [FACT] All claims about what skills exist and what they scan are verified by reading SKILL.md files this session
- [FACT] The decomposition map is derived from the scanner-skill-landscape-inventory wiki concept (written this session from direct observation)
- [INFERENCE] The 3-skill model will reduce cognitive load — based on the operator's stated preference for naming by finding type, not scanning target
- [INFERENCE] Existing scanners can be reused as internal delegates — based on their mode-based architecture (each already has modes or can gain them)
- [UNKNOWN] Whether the operator prefers /aar to stay standalone (D2) or be fully absorbed

## Suggested skills for next session

- `/go` — this handoff has 5 implementation task packets ready to execute
- `/design` — if the operator wants a design doc before implementation (the decomposition may warrant one given its scope)
- `/review --focus architecture` — after AC-01 through AC-03 ship, review the consolidation for correctness
- `/check` — verify each new skill produces equivalent findings to the skills it absorbs
- `/handoff` — update this handoff after each task packet completes

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-14T04:32:33 | 019ffc5c... | claimed by grok |
| 2026-08-14T02:30 | 019ffc5c | created |
