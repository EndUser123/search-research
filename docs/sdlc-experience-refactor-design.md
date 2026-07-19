# SDLC Experience Refactor Design

**Date:** 2026-07-13
**Governing objective:** Make the SDLC skill system understandable, discoverable, low-friction, and reliable for a solo director coordinating a fleet of AI coders across long-lived, multi-topic, cross-terminal sessions.
**Scope:** Public experience and information architecture. Not a runtime-defect audit.
**Status:** Design proposal for review. Not approved for implementation.

---

## Phase 1: Verified Public System

### 1.1 Repository Roots

| Plugin | Repo root | HEAD | Clean? | Cache version | Cache matches source? |
|---|---|---|---|---|---|
| cc-skills-analysis | `P:/packages/.claude-marketplace/plugins/cc-skills-analysis` | `910106a5` | Yes | 1.0.122 | Yes (SHA256 verified) |
| cc-skills-sdlc | `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc` | (submodule, bumped to 1.0.214) | Yes | 1.0.214 | Yes (SHA256 verified) |

### 1.2 Public SDLC Command Inventory

**Active commands** (the user can type these and get a result):

| Command | Plugin | Type | Description |
|---|---|---|---|
| `/recap` | cc-skills-analysis | Script + LLM | Session chain walk + handoff synthesis |
| `/debrief` | cc-skills-analysis | Engine + Hook + LLM | Recursive root-cause investigator (4 modes) |
| `/rns` | cc-skills-analysis | Pure LLM | Strategic prioritization with `<selection>` contract |
| `/why` | cc-skills-analysis | LLM + search | Decision archaeology — trace causal chains |
| `/friction` | cc-skills-analysis | Pure LLM | Detect interaction friction + automation gaps |
| `/behave` | cc-skills-analysis | Pure LLM | Hypothesis testing for session behavior patterns |
| `/design` | cc-skills-sdlc | LLM + templates | Architecture advisor with ADR gates |
| `/risks` | cc-skills-sdlc | Pure LLM (no tools) | Fast pessimistic risk pass |
| `/check` | cc-skills-lab | Multi-phase engine | Multi-tier post-task gate |
| `/review` | cc-skills-sdlc | LLM | Code & PR review (5+ modes) |
| `/red-team` | red-team | Multi-agent engine | Adversarial trust verdict |
| `/go` | cc-skills-sdlc | Engine + Hooks | Bounded SDLC task orchestrator |
| `/improve` | improve-partner | LLM | Artifact improvement partner |
| `/genius` | cc-skills-thinking | Pure LLM | Strategic thought partner |
| `/epistemic-check` | cc-skills-analysis | Pure LLM | Validate response against epistemic contract |
| `/council` | cc-council | Multi-LLM engine | Multi-LLM deliberation |

**Deprecated stubs** (still registered, route to absorbed parents):

| Command | Stub for | Status |
|---|---|---|
| `/retro` | `/debrief chain` | Absorbed, stub remains |
| `/top-problems` | `/debrief top` | Absorbed, stub remains |

**Commands making priority/normative decisions** (the overlap cluster):

| Command | What it produces | Who reads it |
|---|---|---|
| `/recap` (RNS section) | "Recommended Next Steps" with RNS format | Human only (conversational) |
| `/rns` | `<selection>` block with ranked actions | Human only (terminal display) |
| `/debrief chain` | Internal RNS step (LLM-driven) | Human only |
| `/go` Step 0 | Task selection from queue | /go orchestrator |

None of these have a programmatic consumer — all are advisory.

### 1.3 Shared Internal Engines

| Engine | Path | Called by | Public? |
|---|---|---|---|
| `debrief_core` state machine | `skills/debrief/__lib/debrief_core.py` | debrief all modes | No |
| `gap_engine_adapter` | `skills/debrief/__lib/gap_engine_adapter.py` | debrief gaps mode | No |
| `gap_engine.__lib` | `skills/debrief/gap_engine/__lib/` | adapter (indirect) | No |
| `session_chain.walk_session_chain()` | `search-research/core/session_chain.py` | recap, debrief, why | No |
| `dream_state` | `skills/debrief/__lib/dream_state.py` | SessionEnd reflect hook | No |
| `render_rns` | `skills/recap/__lib/render_rns.py` | recap handoff formatting | No |
| Dormant hooks (4 files) | `skills/debrief/gap_engine/hooks/` | NOT REGISTERED | No |

### 1.4 Hook Dispatch Mechanisms

| Mechanism | How | Used by |
|---|---|---|
| `settings.json` → `__lib/router.py` | Global, event-routed | ACA plugins, snapshot, model-router, cc-skills-analysis (SessionEnd only) |
| SKILL.md frontmatter `hooks:` | Skill-scoped | `/go` (Stop, PreToolUse) |
| `hooks.json` per skill | Legacy, skill-scoped | debrief SessionEnd reflect only |

The `/go` skill uses SKILL.md frontmatter hooks. The `/debrief` skill does NOT — its SessionEnd hook is registered via the older `hooks.json` pattern.

---

## Phase 2: User Decision Needs

### 2.1 The Ten Questions

From the user's explicit framing and session corrections:

| # | Question | Durable user intent? | Current surface |
|---|---|---|---|
| 1 | What happened? | YES — fundamental | /recap |
| 2 | What is the current state? | YES — fundamental | /recap |
| 3 | Where should the next agent resume? | YES — fundamental | /recap (handoff template) |
| 4 | Is it ready, complete, correct, or safe? | YES — fundamental | /check, /risks, /review, /red-team |
| 5 | What went wrong and why? | YES — fundamental | /debrief, /why, /rca, /diagnose |
| 6 | What recurring friction exists? | INTERNAL CAPABILITY | /friction, /behave |
| 7 | What should be done next? | YES — fundamental | /rns, /go (step 0) |
| 8 | What design decision was made? | YES — fundamental | /design, /genius, /council |
| 9 | Did the completed work achieve the outcome? | NO current surface | /recap (outcomes section, implicit) |
| 10 | What must persist across compaction? | SYSTEM property | Handoff JSON + markdown |

### 2.2 User's Explicit Dissatisfaction (from session)

*"I don't want a loose, organic mix of skills; I want a coherent, intentional SDLC skill set"*
*"Skills should implement specific, repeatable cognitive steps, not just generic 'do work'"*
*"Reduce randomness and overlap"*
*"Mixed surfaces (e.g., thought-partner used for design, strategy, and random reflection)"*
*"Design decisions getting buried in thought-partner chats"*
*"Risk/impact checks happening informally"*
*"Prioritization happening before proper recap/debrief"*

### 2.3 User's Mental Model

The user thinks of SDLC work as cognitive steps:
1. **Orient** — what happened, where are we (/recap)
2. **Assess** — is this ready, what went wrong (debrief, check)
3. **Decide** — what should we do next, what design is authorized (rns, design)
4. **Execute** — do the work (go — execution, not SDLC)
5. **Verify** — did it work, what did we learn (check, red-team)

---

## Phase 3: Surface Evaluation

### ADHD Cognitive-Load Scoring

Scale: 1 (obvious, distinct) → 10 (guaranteed wrong first guess).

| Command | What it sounds like | Actual use | Durable? | ADHD | Overlaps | Verdict |
|---|---|---|---|---|---|---|
| `/recap` | "Tell me what happened" ✓ | Session walk + handoff | YES | 1 | None | **KEEP** |
| `/debrief` | "Debrief a session" ✓ | 4 modes: default, chain, gaps, top | YES | 3 | /why (partial) | **KEEP** but clarify modes |
| `/rns` | ??? Acronym | Prioritization with evidence audit | YES | 8 | /recap (RNS section), /go | **RENAME** → /prioritize |
| `/why` | "Why is this broken?" ✓ | Decision archaeology | YES | 2 | /debrief (partial) | **KEEP** but clarify boundary |
| `/friction` | "What's slow/annoying?" ✓ | Interaction friction + automation gaps | INTERNAL | 5 | /debrief (victim-log detector) | **INTERNALIZE** into debrief |
| `/behave` | "Analyze LLM behavior?" | Hypothesis testing for session patterns | INTERNAL | 7 | /debrief (same method) | **INTERNALIZE** into debrief |
| `/design` | "Design something" ✓ | Architecture advisor with templates | YES | 2 | /genius, /council | **KEEP** add DecisionRecord |
| `/risks` | "What risks?" ✓ | Fast pessimistic pass | YES but narrow | 4 | /check, /red-team | **MERGE** into /check as mode |
| `/check` | "Check my work" ✓ | Multi-tier post-task gate | YES | 1 | /risks, /review | **KEEP** |
| `/review` | "Review my code" ✓ | Code & PR review | YES | 2 | /check (calls review) | **KEEP** |
| `/red-team` | "Red-team this" ✓ | Adversarial trust verdict | YES | 3 | /risks (escalation boundary) | **KEEP** |
| `/epistemic-check` | ??? Academics | Validate Q&A epistemic contract | INTERNAL | 9 | /check | **RENAME** → /validate |
| `/improve` | "Improve this" ✓ | Artifact improvement | YES | 2 | /design (design improvement) | **KEEP** |
| `/genius` | "I want a genius" ✗ | Strategic thought partner | MIXED | 8 | /design, /reason, /council | **CLARIFY** — produce DecisionRecord if design outcome |
| `/go` | "Go do the work" ✓ | SDLC task orchestrator | YES | 2 | /rns (step 0) | **KEEP** |
| `/retro` | "Run a retro" ✓ | Deprecated → /debrief chain | ABSORBED | 6 | Already absorbed | **ALIAS** or remove |
| `/top-problems` | "Show top problems" ✓ | Deprecated → /debrief top | ABSORBED | 5 | Already absorbed | **ALIAS** or remove |

### Cognitive-Load Summary

| Factor | Current state | Severity |
|---|---|---|
| Commands to remember | ~16-20 plausible SDLC commands | HIGH |
| Similar names | /rns (acronym), /risks (vs /check), /why (vs /debrief) | HIGH |
| Hidden modes | /debrief (4 modes), /review (5+ modes), /check (4 tiers) | HIGH |
| Sequencing rules | recap before debrief? debrief before rns? | HIGH |
| Absorbed commands still present | /retro, /top-problems stubs | MEDIUM |
| NLP trigger overlap | "debrief this" matches both /debrief and /rns | MEDIUM |

**Overall cognitive score: 7/10** — too many overlapping commands.

---

## Phase 4: Three Design Alternatives

### Alternative A — Minimal Clarification

**Command count:** ~16
**Approach:** Rename worst offenders, keep everything else, add aliases.

| Change | Rationale |
|---|---|
| `/rns` → **`/prioritize`** | Acronym is #1 discoverability problem |
| `/epistemic-check` → **`/validate`** | Academic name is non-obvious |
| Keep all other commands | Users may depend on them |
| Add `/recap` → `/handoff` alias | Handoff is a key output |
| Add NLP routing docs | Document which trigger phrases route where |
| Add sequencing docs | "First /recap for context, then /debrief for root cause" |

**Cognitive improvement:** Fixes the two worst names. No structural change.
**Workflow example (incident):** `/recap` → `/debrief transcript.txt` → `/prioritize`
**Migration risk:** LOW — renames only.
**Implementation cost:** LOW — rename SKILL.md files.
**Capability loss risk:** NONE.
**Reversibility:** HIGH — renames are trivial to revert.

**Why this might be enough:** If the user's main frustration is `/rns` being a meaningless acronym and `/epistemic-check` being academic, this fixes both. All other commands have reasonable names.

**Why this might not be enough:** 16 commands is still a lot to remember. Overlaps between /friction and /debrief, and /risks and /check, remain.

### Alternative B — Moderate Consolidation (Recommended)

**Command count:** ~9
**Approach:** Merge narrow capabilities, expose 9 clear intents, keep internal engines hidden.

| Public command | What it answers | Internal capabilities invoked |
|---|---|---|
| `/recap` | What happened? Where are we? | session_chain, render_rns (formatting) |
| `/handoff` | Where should the next agent resume? | /recap engine + handoff template |
| `/debrief` | Why did it break? What patterns recur? | debrief_core, friction view, behave view, gap engine |
| `/prioritize` | What should I do next? | priority engine, evidence audit |
| `/why` | Why does this exist? (decision archaeology) | session_chain, CKS, ADR search |
| `/check` | Is it ready, safe, correct? | verify, typecheck, code review, gitleaks, quick-risk |
| `/design` | Record a design decision. | design templates, ADR gates, DecisionRecord schema |
| `/red-team` | Is this trustworthy? | Multi-agent adversarial pipeline |
| `/go` | Execute the planned work. | task selection, dispatch pi/claude/local |

**Internalized (no public command):**
- `/friction` → debrief view friction
- `/behave` → debrief view behave
- `/risks` → check --quick-risk
- `/epistemic-check` → check --validate
- `/retro` → alias for debrief chain
- `/top-problems` → alias for debrief top
- `/review` → internal phase of /check (and standalone alias)
- `/improve` → remains standalone (different domain)
- `/genius` → informative note to produce DecisionRecord if design outcome

**Cognitive improvement:** 9 commands instead of 16. Each maps to one question. User never has to decide between /friction and /debrief, or /risks and /check.
**Workflow example (incident):** `/recap` → `/debrief transcript.txt` → `/prioritize`
**Workflow example (readiness):** `/check --quick-risk "change the router"` → `/check --standard` → `/red-team`
**Migration risk:** MEDIUM — removing /friction, /behave as public commands may confuse existing users.
**Implementation cost:** MEDIUM — creating debrief view modes, wiring quick-risk into /check.
**Capability loss risk:** LOW — all capabilities preserved behind new entry points.
**Reversibility:** MEDIUM — can restore standalone commands if users object.

### Alternative C — Strong Consolidation

**Command count:** ~5-6
**Approach:** Replace all current commands with ordinary-language names.

| Public command | What it answers | Subsumes |
|---|---|---|
| `/situation` | What happened? Where are we? | /recap, handoff |
| `/diagnose` | Why did it break? | /debrief, /friction, /behave, /why |
| `/plan` | What should we do next? | /rns, /prioritize |
| `/verify` | Is it ready, safe, correct? | /check, /risks, /review, /epistemic-check, /red-team |
| `/decide` | Record a design decision. | /design, /genius (design output) |
| `/execute` | Do the work. | /go |

**All current commands become aliases:** `/recap → /situation`, `/debrief → /diagnose`, `/check → /verify`, etc.
**Cognitive improvement:** 5 ordinary-language commands. User never guesses. Every command is a plain English question.
**Workflow example (incident):** `/situation` → `/diagnose transcript.txt` → `/plan`
**Migration risk:** HIGH — removing 16 familiar commands is disruptive.
**Implementation cost:** HIGH — requires routing changes, re-documentation, user retraining.
**Capability loss risk:** LOW for capability, MEDIUM for discoverability (advanced modes hidden behind flags).
**Reversibility:** LOW — hard to undo once users retrain.

---

## Phase 5: Workflow Models

| Scenario | Alt A | Alt B | Alt C |
|---|---|---|---|
| **Resumption** | /recap → handoff | /handoff | /situation (loses "handoff" concept) |
| **Readiness review** | /check or /risks | /check (with --quick-risk) | /verify |
| **Incident analysis** | /debrief, /friction, /behave | /debrief (one command) | /diagnose |
| **Prioritization** | /prioritize (renamed /rns) | /prioritize | /plan |
| **Design capture** | /design | /design + DecisionRecord | /decide |
| **Cross-session resume** | /recap | /handoff | /situation |
| **User doesn't know command** | 16 choices | 9 choices | 5 choices |

**Best overall: Alternative B.** Handles all scenarios with 9 commands. The handoff boundary is explicit. Incident analysis is a single entry point. Readiness has clear tiers.

---

## Phase 6: Recommendation

### Recommended: Alternative B — Moderate Consolidation

**Reasons grounded in user dissatisfaction:**

1. *"I don't want a loose, organic mix of skills"* → B reduces 16 overlapping commands to 9 clear intents.
2. *"Reduce randomness and overlap"* → B eliminates the /friction vs /debrief and /risks vs /check overlap clusters.
3. *"Mixed surfaces"* → B makes /friction and /behave internal views, giving the user one analysis surface instead of three.
4. *"Design decisions buried in thought-partner chats"* → B gives /design a DecisionRecord output contract.
5. *"Prioritization before proper recap/debrief"* → B makes /debrief the single incident-analysis entry point.

**Why not A:** 16 commands is still too many. The overlap clusters remain.

**Why not C:** Too disruptive. Existing users depend on current names. The marginal benefit of 5 vs 9 commands does not justify the retraining cost.

### Assumptions

1. The user is willing to learn 9 commands.
2. Old commands as aliases provide a transition period.
3. The AI fleet can be directed to use the new names.
4. Internal engines stay invisible.

### Evidence Gaps

1. Actual usage frequency of /friction, /behave, /risks, /epistemic-check is unknown.
2. Whether the user depends on these commands in session transcripts or agent instructions.
3. Whether decision-record urgency justifies /design contract changes.

### Implementation Stages

| Stage | Change | Prerequisites | Rollback | Stop boundary |
|---|---|---|---|---|
| **1** | `/rns` → `/prioritize` + alias | None | Revert rename | User verifies both names work |
| **2** | `/epistemic-check` → `/validate` + alias | Stage 1 | Revert rename | User verifies both names work |
| **3** | `/friction`, `/behave` → `/debrief view` modes + aliases | Stage 2 | Restore standalone SKILL.md | User confirms alias behavior |
| **4** | `/risks` → `/check --quick-risk` mode + alias | Stage 3 | Restore standalone /risks | User confirms merged output |
| **5** | Add DecisionRecord schema to `/design` | Stage 4 | Remove schema file | User confirms output format |
| **6** | Add `/handoff` as alias for /recap output | None | Remove alias | User confirms handoff authority |

### Success Criteria

| Criterion | Baseline | Target |
|---|---|---|
| Commands to remember | ~16 | ~9 |
| NLP trigger overlap | "debrief this" matches 2 skills | 0 ambiguous |
| Duplicate analyses | /friction + /debrief on same transcript | Zero |
| DecisionRecord artifacts | None | Optional (when design is the outcome) |
| Wrong-command corrections | Not measured | Tracked in breadcrumb |

### Rollback Strategy

Each stage is independently revertible. Old commands remain as aliases. No data migration required.

---

## Verdict

`DESIGN_READY_FOR_REVIEW`

**Recommended:** Alternative B — Moderate Consolidation (9 public commands).

**Next step:** User reviews the design, selects stages to implement (or rejects and provides corrections), and authorizes Stage 1.
