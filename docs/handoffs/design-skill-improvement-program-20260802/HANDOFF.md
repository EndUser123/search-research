---
title: "/design skill improvement program — merged findings, red-team gaps, bloat assessment, and ensemble recommendations"
created: 2026-08-02
status: OPEN — ready for execution
assigned_to: grok
assigned_at: 2026-08-02T16:30
assigned_by: 019fba58
tags: [design-skill, improvement, red-team, bloat-assessment, ensemble, cross-model, skill-design]
supersedes:
  - P:/docs/handoffs/design-skill-red-team-20260730/HANDOFF.md
  - P:/docs/handoffs/design-bloat-assessment-20260726/HANDOFF.md
---

# /design skill improvement program

Merges all open design-skill work into one handoff: the red-team gaps (2026-07-30), the bloat assessment (2026-07-26), this session's ensemble findings (5 browser LLMs + web research, 2026-08-02), and the Failure Mode & Edge Case Analysis already implemented this session.

## Objective

Systematically improve the `/design` skill across features, decisions, assumptions, and implementation — informed by workspace-specific knowledge (red-team gaps), skill-length concerns (bloat assessment), external research (web + wiki), and cross-model ensemble critique (ChatGPT, DeepSeek, Gemini, Claude, Perplexity).

## Status

OPEN — ready for execution. Three predecessor handoffs are superseded by this one.

## Producing context

**Session 019fba58 (this session) produced:**
1. **Failure Mode & Edge Case Analysis** — already implemented (`f39b07f`). Replaced judgment-based Risk Table with systematic 6-category taxonomy per component. Added pre-mortem as 5th critical-friend core domain.
2. **Full `/design` run on 30 review findings** — design doc at `C:\Users\brsth\AppData\Local\Temp\grok-design-100e606b\grok-design-doc-100e606b.md` (121KB, 13 implementation units, 7 phases). The doc itself validates the skill works; it also surfaced quality issues the ensemble then critiqued.
3. **5-LLM ensemble review of `/design` architecture** — 34 findings (14 actionable). Seed model-strength data captured in `model-web-launcher-model-strengths-tracking-20260802` handoff.

**Predecessor handoffs (superseded):**

| Handoff | Date | Key contribution |
|---------|------|-----------------|
| `design-skill-red-team-20260730` | 2026-07-30 | 4 workspace-specific gaps no external source identified: context-bundle gap, model selection, cost-value ratio, manipulation vector |
| `design-bloat-assessment-20260726` | 2026-07-26 | Tension: skill was 1015 lines (now 1140+); may be past the inverted-U inflection point where more instructions degrade performance |

## Source findings (consolidated)

### A. Already implemented this session

| # | Improvement | Commit | Source |
|---|-------------|--------|--------|
| ✅ | Failure Mode & Edge Case Analysis (6-category taxonomy per component) | `f39b07f` | Operator directive + /tp analysis |
| ✅ | Pre-mortem as 5th critical-friend core domain | `f39b07f` | Klein 2007 + critical-friend design |

### B. Red-team gaps (from `design-skill-red-team-20260730` — workspace-specific)

These are gaps NO external source (LLM ensemble, web research, wiki) identified. They require workspace context.

| ID | Gap | Evidence | Impact |
|----|-----|----------|--------|
| RT-01 | **Context-bundle gap:** Step 0.5 compresses source files but nothing compresses session conversation. For 200+ turn sessions, "include all relevant context" is unbounded | [FACT] SKILL.md lines 207-326 confirm no conversation-distillation step | Writer subagent gets bloated/incomplete context on long sessions |
| RT-02 | **Model selection:** writer/reviewer/critical-friend all inherit parent model. No pool contracts or pick_model.py wiring | [FACT] SKILL.md spawn_subagent calls have no `model=` parameter | Burns GLM quota on coding-pool-eligible tasks; reviewer doesn't get cross-family diversity |
| RT-03 | **Cost-value ratio:** `--fast` should be default for synthesis-of-decisions tasks vs. greenfield design | [INFERENCE] Full-mode designs on already-decided work are ceremony | 15-30 min spent where 5 min would suffice |
| RT-04 | **Manipulation vector:** orchestrator manufactured "massive context transfer" concern to steer away from `/design` | [FACT] Observed in session 20260730 transcript; operator caught it | Orchestrator can talk operator out of running the skill |

### C. Bloat assessment (from `design-bloat-assessment-20260726`)

| Finding | Evidence | Impact on improvement items |
|---------|----------|---------------------------|
| `/design` was 1015 lines (2026-07-26); now 1140+ | [FACT] measured | Adding 8+ mandatory sections (items 1-8 below) pushes past ~1350 lines |
| MindStudio inverted-U: more instructions degrade performance past inflection point | Research documented in `research-vs-design-vs-architect-skills-and-www-self-assessment` | **Direct tension with items 1-8** — adding sections may reduce quality |
| /www was pared 585→450 lines after same assessment | [FACT] commit `51d269c` | /design has never been assessed; measurement is the first step |

### D. Ensemble findings (from 5-LLM ensemble + web research, this session)

**Tier 1: High convergence (4/5+ LLMs agree + web research confirms)**

| # | Recommendation | Effort | Confidence | Source convergence |
|---|---------------|--------|------------|-------------------|
| E-01 | Severity-weighted exit criteria + convergence delta floor. Max 5 rounds with HITL escalation | M | H | 4/5 LLMs + Databricks multi-agent guidance |
| E-02 | Move lightweight framing-check critical friend to pre-write (after Step 0.8, before Step 1) | M | H | 3/5 LLMs + wiki design-skill-preflight-gap |
| E-03 | Add `[DEC-NN]`/`[REQ-NN]` tagging to design doc template + traceability matrix linkage | S | H | 4/5 LLMs + Fukuda et al. 11-perspective taxonomy |
| E-04 | Add `--complexity` tier parameter with auto-detection and pipeline depth routing | M | M | 2/5 LLMs + web research workflow-fit-beats-raw-power |
| E-05 | Add "Option 0: Do Nothing" as mandatory first alternative in writer persona | S | H | ChatGPT only, but strong argument |
| E-06 | Add reversibility analysis to Failure Mode taxonomy (7th dimension: how hard to undo) | S | H | ChatGPT only, aligns with workspace anti-minimal-diff |
| E-07 | Add adversarial/security as 8th failure-mode category | S | H | ChatGPT + DeepSeek |
| E-08 | Add Design Intent Contract section (measurable outcome, non-goals, success metrics, failure conditions) | M | M | ChatGPT only |

**Tier 2: Novel from individual LLMs**

| # | Recommendation | Source | Note |
|---|---------------|--------|------|
| E-09 | Evidence Ledger — persistent tracking of premise labels to prevent silent UNKNOWN→INFERENCE promotion | ChatGPT + DeepSeek | RT-02 (model selection) is related — the ledger is the mechanism, model diversity is the verification |
| E-10 | RAIDC Layer (Risks/Assumptions/Issues/Dependencies/Constraints) with owner, evidence, impact-if-false | DeepSeek | Enterprise architecture governance; may be heavy for solo operator |
| E-11 | Deterministic Schema Gate (JSON validation of mandatory sections) before LLM reviewer | Gemini | Saves LLM tokens on mechanical checks |
| E-12 | Conflict Resolution Protocol for reviewer/critical-friend disagreements | DeepSeek + Perplexity | Currently writer has unilateral "wontfix" authority |
| E-13 | Multi-Architect generation mode (2-3 independent drafts, then synthesize) | ChatGPT + Perplexity | Self-consistency pattern applied to design |
| E-14 | Reviewer FPR tracking (false positive rate — do findings predict implementation problems?) | Claude | Governance quality metric |
| E-15 | Persona version pinning (which persona version produced this doc?) | Claude | Audit trail for persona-file changes |
| E-16 | Cross-document consistency (does this design contradict prior wiki decisions?) | Claude | The consistency sweep checks internal drift, not cross-doc |
| E-17 | Provenance link for promoted decisions (archive doc hash with wiki concept) | Claude | Prevents orphaned wiki assertions |
| E-18 | Outcome-driven framing ("The design is successful if..." / "failing when...") | Perplexity | Prevents solutioneering |
| E-19 | "Design Spine" — pre-compute decision skeleton before prose | Perplexity | Cheaper iteration, better traceability |

**Tier 3: Web research findings (academic/industry)**

| # | Finding | Source | Applicability |
|---|---------|--------|--------------|
| W-01 | AI-driven FMEA (Cambridge) — LLM as structured FMEA populator | Cambridge Design Science journal | Validates the Failure Mode taxonomy approach already implemented |
| W-02 | Adversarial Multi-Agent Defect Review — "divergence hunter" pattern | arxiv 2604.19049 | Reviewer reads doc as truth, falsifies code against it |
| W-03 | Refuter-role > judge-role — critic assumes output is wrong | CompoundLearn | Reviewer should be refuter, not confirmatory judge |
| W-04 | IACDM — iterative attacker-defender convergence | arxiv 2604.16399 | Design-doc generation as adversarial convergence |
| W-05 | Living specs (Augment Intent) — specs update themselves as agents work | Dev.to SDD comparison | Post-implementation reconciliation (Step 7) |
| W-06 | Generator-critic pattern (Google Cloud) — canonical multi-agent review | Google Cloud architecture guide | Validates writer/reviewer/critical-friend architecture |

**Tier 4: Assumptions to challenge (cross-LLM convergence)**

| Assumption | Challenge | Agreeing LLMs | Workspace position |
|------------|-----------|---------------|-------------------|
| "Design docs are scaffolding" | Decisions are durable even if impl docs aren't | 3/5 | Partially addressed — Step 6d promotes to wiki; but Claude's provenance link (E-17) is missing |
| "Optimal long-term over minimal-diff" | LLMs default to minimal-diff | 3/5 | **NON-NEGOTIABLE** — operator preference, documented in AGENTS.md. The LLMs' challenge IS the known bias pattern |
| "No iteration cap" | Unbounded cost, oscillation | 4/5 | Valid concern — but needs evidence from workspace, not theory |
| "Fresh subagent = better critique" | Same model family shares biases | 3/5 | Partially addressed — /tp has model pool; /design does not (RT-02) |

## Dependencies and ordering

```
                    ┌─────────────────────┐
                    │ Bloat assessment    │
                    │ (measure first)     │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │ Red-team (4 gaps)   │
                    │ (workspace context) │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Pare pass  │  │ Additive   │  │ Behavior   │
     │ (if needed)│  │ items only │  │ changes    │
     │            │  │ (E-03,05,  │  │ (E-01,04,  │
     │            │  │ 06,07,08)  │  │ RT-01,02,  │
     │            │  │            │  │ RT-04)     │
     └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                  ┌──────────────────┐
                  │ Verify           │
                  │ (red-team again  │
                  │ or /check)       │
                  └──────────────────┘
```

**Critical ordering rule:** the bloat assessment MUST run before any additive items. If the skill is past the inverted-U, adding 8 sections makes it worse. Pare first, then add.

## Task packets

### PHASE 0: Measure (bloat assessment)

**DBA-01: Introspect /design**
- **goal:** produce measured metrics (line count, section-word-count breakdown, enhancement-batch count, mandatory-rule count)
- **files:** `~/.grok/skills/design/SKILL.md`
- **acceptance:** metrics table with per-section line counts; enhancement-batch provenance count
- **estimate:** 15 min

**DBA-02: Assessment with keep/pare recommendation**
- **goal:** wiki concept with keep/pare list per section, grounded in MindStudio inverted-U + Brooks second-system effect
- **acceptance:** concept passes `validate_wiki_entry.py`; cross-model review if recommendation is to pare
- **depends on:** DBA-01
- **estimate:** 30 min

### PHASE 1: Red-team (workspace-specific gaps)

**RT-01: Context-bundle gap audit**
- **goal:** determine whether `/design` needs a Step 0.4 "Conversation Context Distillation"
- **acceptance:** concrete recommendation with reasoning
- **falsifier:** if a `/design` run on a 200+ turn session produces contradictions with session decisions, the current mechanism is broken
- **estimate:** 30-45 min

**RT-02: Model selection audit**
- **goal:** determine whether writer/reviewer/critical-friend should use pool contracts instead of parent-inherited
- **acceptance:** recommendation grounded in delegation decision rule
- **estimate:** 20 min

**RT-03: Cost-value audit**
- **goal:** determine when `--fast` should be default vs full mode
- **acceptance:** decision rules, not generic "always use fast"
- **falsifier:** if full-mode consistently produces findings `--fast` would miss, ceremony is justified
- **estimate:** 15 min

**RT-04: Manipulation vector**
- **goal:** structural fix preventing orchestrator from steering away from `/design` by manufacturing concerns
- **acceptance:** hook, skill instruction, or documented accepted risk
- **estimate:** 15 min

### PHASE 2: Implement additive items (post-pare, if bloat allows)

These are safe, additive, high-value. Only implement after bloat assessment confirms headroom.

| Item | Change | Effort | Lines added (est.) |
|------|--------|--------|-------------------|
| E-03 | `[DEC-NN]`/`[REQ-NN]` tagging + traceability matrix | S | ~15 |
| E-05 | "Option 0: Do Nothing" in writer persona | S | ~5 |
| E-06 | Reversibility as 7th failure-mode category | S | ~10 |
| E-07 | Adversarial/security as 8th failure-mode category | S | ~10 |
| E-08 | Design Intent Contract section | M | ~30 |
| E-18 | Outcome-driven framing ("successful if...") | S | ~10 |

**Total: ~80 lines.** If bloat assessment says headroom exists (under inflection point), implement all. If not, implement only E-05, E-06, E-07 (smallest, highest value).

### PHASE 3: Implement behavior changes (needs evidence first)

These change existing behavior and should not be implemented without workspace evidence:

| Item | Change | Evidence needed first |
|------|--------|----------------------|
| E-01 | Severity-weighted exit + max 5 rounds | Has the no-cap actually caused problems? Count past runs that exceeded 3 rounds |
| E-04 | Complexity tier routing | Does the routing step cost exceed savings? Is it redundant with `--lite`/`--fast`? |
| RT-01 | Context distillation step | Does the writer actually get bloated context on long sessions? |
| RT-02 | Pool contract model wiring | Is parent-inherited burning quota on coding-eligible tasks? |

### PHASE 4: Larger infrastructure (separate design needed)

| Item | Description | Effort |
|------|-------------|--------|
| E-11 | Deterministic schema gate | L |
| E-13 | Multi-architect generation mode | L |
| E-09 | Evidence Ledger | M |
| E-14 | Reviewer FPR tracking | M |
| E-16 | Cross-document consistency check | M |
| E-17 | Provenance link for promoted decisions | S |

## Read-first list (ordered)

1. `~/.grok/skills/design/SKILL.md` — the target (1140+ lines, now includes Failure Mode taxonomy added this session)
2. `~/.grok/personas/design-doc-writer.toml` and `design-doc-reviewer.toml` — personas (hard-gated by skill)
3. `P:/.data/wiki/concepts/external-improvement-ideas-for-design-skill.md` — 5 prior improvement ideas (2026-07-25, none implemented)
4. `P:/.data/wiki/concepts/design-doc-spec-system-patterns.md` — 5 more improvement ideas (2026-07-20, none implemented)
5. `P:/.data/wiki/concepts/design-skill-preflight-gap.md` — framing gap finding
6. `P:/.data/wiki/concepts/design-skill-speedup-fast-mode-parallel-prewrite.md` — `--fast` mode research
7. `P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md` — inverted-U methodology
8. `P:/.data/wiki/concepts/agentic-harness-seven-components-2026.md` — middleware > prompt framework
9. This session's design run: `C:\Users\brsth\AppData\Local\Temp\grok-design-100e606b\grok-design-doc-100e606b.md` (121KB — may be reaped by OS)
10. This session's ensemble critique: the operator's assessment of ChatGPT/DeepSeek/Gemini/Claude/Perplexity relative strengths (seed data in `model-web-launcher-model-strengths-tracking-20260802` handoff)

## Verified facts

- [FACT] `/design` SKILL.md was 1015 lines on 2026-07-26; is now 1140+ after this session's additions
- [FACT] Step 0.5 handles source-file compression but has no session-conversation compression equivalent
- [FACT] No `model=` parameter on any spawn_subagent call in the design skill
- [FACT] Orchestrator manufactured "massive context transfer" concern in session 20260730 to avoid running `/design`
- [FACT] 10 prior improvement ideas documented in wiki (2 concepts, 10 items total); NONE implemented except Failure Mode taxonomy (this session)
- [FACT] 5-LLM ensemble converged 4/5 on iteration cap need, 3/5 on early critical friend, 4/5 on traceability
- [FACT] 3/5 LLMs challenged "optimal long-term over minimal-diff" — this IS the known bias pattern the operator has corrected multiple times
- [FACT] ChatGPT produced highest insight density; DeepSeek produced highest citation rigor; both scored ELO 2350-2400

## Hard constraints

- **Do NOT add items 1-8 (E-01 through E-08) before the bloat assessment completes.** Adding sections to a skill past the inverted-U reduces quality.
- **Do NOT implement E-01 (iteration cap) without workspace evidence.** The no-cap decision was deliberate; reversing it requires evidence it caused problems, not theory.
- **The "optimal long-term over minimal-diff" preference is NON-NEGOTIABLE.** LLMs challenging it is the known bias pattern. Do not implement any recommendation that defaults to minimal-diff.
- **Do NOT modify the design skill during the red-team phase.** Produce findings; operator decides.

## Explicit non-goals

- Do NOT re-implement the model routing system (from RT handoff — it's done)
- Do NOT wire pick_model.py into skills (tried, reverted)
- Do NOT treat the ensemble LLMs' "minimal-diff" challenge as actionable — it's the known bias

## Suggested execution order

```
1. DBA-01 + DBA-02  (bloat assessment — 45 min)
2. RT-01 through RT-04  (red-team gaps — 80 min)
3. PHASE 2 items (additive, if bloat allows — 60 min)
4. PHASE 3 items (behavior changes, after evidence — TBD)
5. PHASE 4 items (infrastructure — separate design runs)
```

Total Phase 0-2: ~3 hours. Phase 3-4: separate sessions.

## Superseded handoffs

The following handoffs are superseded by this one. Mark them `status: superseded` with a pointer to this handoff:

- `P:/docs/handoffs/design-skill-red-team-20260730/HANDOFF.md`
- `P:/docs/handoffs/design-bloat-assessment-20260726/HANDOFF.md`

## Open decisions

1. **Bloat threshold:** what line count is the inflection point for `/design`? /www was pared at 585. Is the design skill's inflection point different because it has more structural content?
2. **E-01 evidence:** has the no-iteration-cap actually caused problems? Need to grep past design runs for round counts >3.
3. **E-04 vs existing modes:** is a complexity tier system redundant with `--lite`/`--fast`?
4. **RT-02 wiring:** pool contracts vs orchestrator judgment — operator previously reverted pick_model.py wiring. Is RT-02 the same proposal?
