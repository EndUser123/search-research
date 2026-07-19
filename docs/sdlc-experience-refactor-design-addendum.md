# SDLC Experience Refactor Design — Revised Addendum

**Date:** 2026-07-13
**Status:** Revision of `sdlc-experience-refactor-design.md`. Original design preserved. This addendum corrects the eight issues identified in review.

---

## 1. Corrected Command Inventory

The original design claimed "9 commands" for Alternative B while leaving `/improve`, `/genius`, `/council`, `/review`, `/friction`, `/behave`, and `/risks` publicly discoverable or aliased. This is misleading. The honest inventory must separate what the user is expected to learn from what remains reachable.

### Full Before-and-After Menu

#### Current (everything public)

| Category | Commands | Count |
|---|---|---|
| Canonical SDLC | `/recap`, `/debrief` (4 modes), `/rns`, `/why`, `/design`, `/risks`, `/check` (4 tiers), `/review` (5+ modes), `/red-team`, `/go` | **10** |
| Deprecated stubs | `/retro`, `/top-problems` | **2** |
| Thinking/exploration | `/genius`, `/s`, `/reason`, `/reflect`, `/probe`, `/skeptic`, `/truth`, `/prospect` | **8** |
| Specialized utilities | `/improve`, `/council`, `/epistemic-check`, `/trace`, `/claude-audit`, `/skill-audit`, `/friction`, `/behave` | **8** |
| Planning/documentation | `/planning`, `/writing-plans`, `/writing-skills`, `/docs`, `/wiki`, `/specify` | **6** |
| Review variants | `/review-pr`, `/review_bundle`, `/improve-codebase-architecture` | **3** |
| **Total public commands** | | **~37** |

The user cannot be expected to hold all 37 in working memory. The SDLC subset alone is **10 canonical commands + 2 stubs = 12** the user must navigate.

#### After Alternative B (honest accounting)

| Layer | Commands | Count | User must recall? |
|---|---|---|---|
| **Canonical SDLC** | `/recap`, `/debrief`, `/prioritize` (renamed `/rns`), `/why`, `/design`, `/check`, `/red-team`, `/go` | **8** | **YES — these are the SDLC vocabulary** |
| **Public compatibility aliases** | `/rns → /prioritize`, `/risks → /check --quick-risk`, `/friction → /debrief view`, `/behave → /debrief view`, `/retro → /debrief chain`, `/top-problems → /debrief top`, `/epistemic-check → /validate` | **7** | Discoverable via `/help`, not expected for daily use |
| **Independent non-SDLC tools** | `/improve`, `/genius`, `/council`, `/review`, `/go` | **5** | Separate domain; not SDLC-specific |
| **Internal capabilities (no public command)** | gap_engine, dream_state, session_chain, debrief_core, render_rns | **0** | Hidden by design |
| **Canonical SDLC for daily use** | **8** | | |

**Realistic cognitive surface:** 8 canonical commands + 5 independent tools = 13 commands the user might plausibly reach for. The 7 aliases are discoverable but not required reading.

### 1.2 What "Internalize" Means

Making a skill "internal" means:
- No `/command` entry point
- No standalone SKILL.md under the skill name
- The capability is accessed through a mode or view of a parent command
- The old name becomes a visible alias (for one release cycle, then removed)

For `update`/`add`/`remove` of SKILL.md entries, this is a documentation and metadata change — the SKILL.md stays in the repo but its `name:` frontmatter changes so it's only reachable via the parent command's documentation, not as a top-level slash command.

---

## 2. Handoff as a Transition Contract

### Three Models Compared

| Dimension | Model A: /recap output mode | Model B: Automatically produced artifact | Model C: Separate public /handoff command |
|---|---|---|---|
| **Writer** | `/recap` LLM synthesis | Snapshot plugin (`PreCompact_snapshot_capture.py` writes JSON) | `/recap` LLM synthesis (same as A) |
| **Storage** | Conversational (chat output) | `~/.claude/state/handoff/console_*_handoff.json` | Conversational + file (both) |
| **Reader** | Next session LLM (if user copies output) | Chain walker (`acquire.py`) for session IDs only | Next session LLM + chain walker |
| **Authority over objective** | Advisory — LLM best-effort summary | **NONE** — JSON handoff carries no objective field | Advisory (same as A) |
| **Authority over resume action** | Advisory — "Resume Here" section | **NONE** — JSON has no next-action field | Advisory (same as A) |
| **Session/workstream identity** | Present in markdown (if LLM preserves it) | `session_id` in JSON payload | Both |
| **Freshness** | Stale on compaction (conversational) | ≤5 minutes (`FRESH_HANDOFF_THRESHOLD_SECONDS`) | Both |
| **Invalidation** | Overwritten by next /recap output | Cleared by snapshot on next session start | Both |
| **Transcript disagrees** | Transcript wins | Transcript wins | Transcript wins |
| **Cross-terminal identity** | No explicit mechanism | No explicit mechanism (per-terminal files) | Same limitation |
| **Repository revision** | None (conversational only) | None in current schema | Could be added |
| **Failure direction** | Silent degradation (lossy resume) | Silent fallback (re-walk session chain) | Same as A + B |
| **User cognitive cost** | None — implicit in existing flow | None — fully automatic | **User must remember another command exists** |

### Recommendation

**Keep handoff as a `/recap` output mode (Model A), not a separate command.**

Evidence:
- No independent demand for a `/handoff` command has been established — the user has never asked for one in this session.
- The JSON handoff (Model B) already exists and is consumed by the chain walker. It is correctly scoped to metadata (session_id, transcript_path) and has no authority over objectives or actions.
- Adding a third handoff artifact (Model C's conversational + file) would create the same ambiguity as the current two-artifact system without solving a proven problem.
- The "/handoff" concept is best communicated as a `/recap` output mode: `/recap --handoff` or `/recap brief` both serve the transition need without adding a command.

**If independent demand emerges later** (user explicitly asks "where do I hand off to the next agent" without typing `/recap`), add a `/handoff` alias at that point. Do not speculate.

---

## 3. Readiness Contracts: Five Distinct Needs

Before consolidating readiness surfaces, model each contract independently.

### Contract Map

| Contract | Entry | Scope | Output | Authority | Runs tools? | Runtime model |
|---|---|---|---|---|---|---|
| **Completion orchestration** (`/check`) | User invokes after task | Git diff → multi-phase pipeline | CLEAN / FINDINGS / ERROR / BLOCKED | Structural (verify passes typechecks, gitleaks) | Yes — runs verify, typecheck, gitleaks | Multi-script engine |
| **Code review** (`/review`) | User invokes, or called by /check | Source files or diff | File:line findings | Advisory — reviewer opinion | Yes (Bash, Glob, Grep, Read) | LLM + tools |
| **Prospective risk** (`/risks`) | User invokes on proposal | Un-actioned proposal text | Risk table + mitigations | Advisory — no runtime enforcement | **No** (`allowed-tools: []`) | Pure LLM |
| **Epistemic validation** (`/epistemic-check`) | User invokes on any response | Q&A response text | allow / warn / block | Structural (format + causal claim checks) | No (regex + LLM) | Pure LLM |
| **Adversarial trust** (`/red-team`) | User invokes for high-risk decisions | Proposal + context | PROCEED / REVISE / BLOCK | Advisory — multi-agent, highest scrutiny | Yes (specialist agents) | Multi-agent pipeline |

### Overlap assessment

| Pair | Overlap | Can share entry point? |
|---|---|---|
| `/check` + `/review` | `/check` Phase 2 calls `/review` internally. Code review is a phase of the readiness pipeline. | **YES** — `/check` already does this. No change needed. |
| `/check` + `/risks` | Different input domains (diff vs proposal). Different runtime models (multi-script vs pure LLM). | **NO** — incompatible execution models. A `--quick-risk` flag would need to reimplement `/risks` logic within `/check`. Not worth it. |
| `/check` + `/epistemic-check` | `/epistemic-check` validates response format, not task readiness. Different objects. | **NO** — unrelated domains. Rename `/epistemic-check` to something discoverable instead. |
| `/check` + `/red-team` | `/red-team` is escalation for high-trust decisions after `/check` passes. Different depth. | **NO** — sequential (check first, red-team if needed), not merged. Document the escalation path. |
| `/risks` + `/red-team` | `/risks` documents its boundary (lines 24-30): single-pass proposal risk; `/red-team` for trust verdicts. | Well-documented. No merge needed. |

### Recommendation

**Keep `/check`, `/review`, `/risks`, `/red-team`, `/epistemic-check` as separate commands.** Do not consolidate them. The ADHD cost of 5 commands is lower than the cost of forcing incompatible execution models into a single entry point.

Actions:
- Rename `/epistemic-check` to something discoverable. Convention so far has been two-word names: **`/check-claims`** (most descriptive of what it does: check that causal and comparative claims are properly labeled). Alternative: `/audit-response`. The key requirement is the user can guess what it does without reading docs. `/epistemic-check` fails this.
- Document the escalation path: `/check` → `/risks` (optional) → `/red-team` (for trust boundaries).
- `/review` already works as a `/check` phase. This is correct — keep it.

---

## 4. `/why` versus `/debrief`: Ten Representative Requests

| # | User says | Intended route | Rationale |
|---|---|---|---|
| 1 | "Why is this hook not firing?" | `/debrief` | Defect investigation — needs origin tracing |
| 2 | "Why do we have this NLM thing?" | `/why` | Decision archaeology — traces origin, not bug |
| 3 | "Why did the tests pass but the deploy fails?" | `/debrief` | New defect across sessions |
| 4 | "Why did we choose Postgres over SQLite?" | `/why` | Historical decision reconstruction |
| 5 | "Why does this transcript keep showing bash returning empty?" | `/debrief` | Recurring symptom, needs victim-log detection |
| 6 | "Why is this function called `_resolve` — what was the reasoning?" | `/why` | Naming/architecture rationale |
| 7 | "Why did you choose this approach?" | `/why` (or `/design`) | Design decision — `/design` if recording, `/why` if tracing past |
| 8 | "Why didn't the snapshot hook fire?" | `/debrief` | Hook failure — code-level defect |
| 9 | "Why do we have both a TS and a Python version of the same tool?" | `/why` | Cross-repository decision archaeology |
| 10 | "Why did we stop using bifrost?" | `/why` | Historical retirement decision |

**Ambiguous cases:**

| # | User says | Ambiguity | Tiebreaker |
|---|---|---|---|
| 3 | "Why did the build fail?" | Could be root-cause (debrief) or historical (why) | If the build JUST failed → `/debrief`. If asking about past build patterns → `/why`. |
| 7 | "Why did you choose this?" | Design decision or decision archaeology | If the decision WAS JUST MADE → `/design` to record it. If asking about PAST decision → `/why`. |

**The boundary is:**
- **Past decision, already resolved, need to understand rationale** → `/why`
- **Current failure, need to find root cause** → `/debrief`
- **Decision being made now, need to record it** → `/design`

### Recommendation

**Keep `/why` as a independent command.** Do not rename, do not internalize into `/debrief` or `/design`. It serves a distinct need (decision archaeology) that neither `/debrief` (defect discovery) nor `/design` (new decisions) covers.

The cognitive cost of three analysis surfaces (`/debrief`, `/why`, `/design`) is acceptable because each maps to a distinct temporal frame:
- **Past failure** → `/debrief`
- **Past decision** → `/why`
- **Future/current decision** → `/design`

---

## 5. Durable DecisionRecord

### Proposed contract (for evaluation, not implementation)

| Field | Value |
|---|---|
| **Producer** | `/design` LLM synthesis (user invokes `/design`, produces DecisionRecord as output) |
| **Storage** | Conversational (chat output) — same as current `/design` output |
| **Reader** | **NONE IDENTIFIED** — no current consumer reads DecisionRecords |
| **Authorization** | User approval implicit in recording the decision |
| **Revision binding** | Would need git SHA — not currently captured by `/design` |
| **Supersession** | No rule — no mechanism to supersede a prior DecisionRecord |
| **Freshness** | Permanent (decisions don't expire, but context evolves) |
| **Failure behaviour** | None — decision is not recorded, user proceeds based on chat |
| **Acceptance evidence** | None — no consumer validates that decisions were recorded |

### Recommendation

**Do NOT build a DecisionRecord schema now.** No consumer exists. No automatic invalidation is needed. The current `/design` output (alternatives, criterion, verdict) already approximates a DecisionRecord in conversational form.

If a consumer emerges (e.g., a future "Why was this decision made?" agent that reads DecisionRecords), add the schema at that point. The output template for `/design` should be improved to reliably include alternatives, criterion, and verdict — but this is a prompt-level improvement, not a schema or data migration.

---

## 6. Complete Workflow Traces

### Scenario 1: Agent finishes implementation, another must continue

```
User intent: "Hand off this work to the next session/agent"
Routing: /recap (explicit) or session-end compaction (automatic)
Public surface: /recap (handoff mode)
Internal mechanisms: session_chain.walk_session_chain() → recap_v2.py → render_rns
Evidence read: All transcript files in current session chain
Output/artifact: Markdown handoff document (Resume Here, Completed, Risks, Decisions)
Storage: Conversational (chat output)
Downstream consumer: Next session's LLM
Authority: Advisory — "Resume Here" is the recommended starting point, not a binding contract
Freshness: Stale on next /recap invocation. Transcript remains authoritative.
Failure: No handoff produced → next LLM starts from scratch (transcript only)
Success proof: Next agent reads the "Resume Here" section and picks up without re-reading transcript
Cross-terminal: Terminal A calls /recap → terminal B reads handoff from conversation history
             NO explicit cross-terminal handoff — relies on user copying or shared conversation
```

### Scenario 2: Work appears complete, needs readiness review

```
User intent: "Is my change safe to commit?"
Routing: /check (obvious name — user types this)
Public surface: /check --standard
Internal mechanisms: verify → gitleaks → git-hygiene → typecheck → code-review → drift-check
Evidence read: git diff HEAD, git log, source files of changed lines
Output/artifact: Verdict line (CLEAN / FINDINGS / ERROR / BLOCKED) + per-phase details
Storage: Conversational (chat output)
Downstream consumer: User decides whether to commit
Authority: Structural for typecheck/gitleaks (errors block); advisory for code-review findings
Freshness: Per-invocation — git diff is the source of truth
Failure: /check passes but a different change breaks tests → /check did not run against that diff
Success proof: /check outputs CLEAN → user commits with confidence
Cross-session: /check is stateless — no cross-session issues
```

### Scenario 3: Several attempts failed, user wants to understand why

```
User intent: "This keeps breaking and I don't know why"
Routing: User types /debrief <transcript> or "why is this broken" (NLP match)
Public surface: /debrief (default mode)
Internal mechanisms: chunk_plan → extraction prompts → debrief_core.run() (discover→classify→locate→verify→write) → TaskCreate
Evidence read: Single transcript file or session export
Output/artifact: Written tasks (TaskCreate) with VERIFIED origins + causal chains
Storage: Task tracker + breadcrumb task + renamed transcript file
Downstream consumer: Next session reads breadcrumb task, picks up investigation
Authority: VERIFIED findings are root-caused; UNVERIFIED blocked at gate; recursion_exhausted flagged
Freshness: Based on single transcript — stale if later sessions contradict or fix findings
Failure: LLM skips Agent subagents for locate/recurse → findings stuck at LOCATED with recursion_exhausted=True
Success proof: /debrief exits through close gate (Phase 9) with ACCOUNTING sentinel → tasks exist in tracker
Cross-session: dream_state records topic reviewed; should_re_review prevents duplicate within 7 days
             No cross-terminal dedup — finding could be independently discovered in another terminal
```

### Scenario 4: User wants ranked next workstream

```
User intent: "What should I do next?"
Routing: /prioritize (renamed from /rns) — or /rns alias during transition
Public surface: /prioritize [text or @file or session context]
Internal mechanisms: Evidence audit (LLM) → Diagnosis → Action ranking + red team → <selection> contract
Evidence read: User-provided text, file reference, or current session context
Output/artifact: Ranked actions (1-4) with red-team notes + <selection> block
Storage: Conversational (chat output) — NO persistent artifact
Downstream consumer: Human user reads output, selects action, bridges to /go
Authority: Advisory — user must act; no automation consumes the <selection>
Freshness: Per-invocation — re-running with same input may produce different rankings
Failure: Evidence audit section cites stale or inferred facts → ranking quality degrades silently
Success proof: User reads the ranked actions, picks one, and takes the recommended next step
Precondition note: If the user has NOT run /debrief first, the ranking is based on raw symptoms,
                   not verified origins. This is a sequencing risk the user must manage.
```

### Scenario 5: Design choice must be recorded before implementation

```
User intent: "We need to decide on the database and record it before I forget"
Routing: /design (or "I have a design decision")
Public surface: /design
Internal mechanisms: Audit-first → classify intent → template routing → self-critique → contract closure
Evidence read: Project context, ADRs, existing decisions (CKS, memory)
Output/artifact: Design proposal with alternatives, criterion, verdict
Storage: Conversational (chat output). NO persistent DecisionRecord file.
Downstream consumer: User (and future /why if the decision needs to be traced)
Authority: Advisory — user can override at implementation time
Freshness: Permanent reference but context evolves — reversal trigger is the mechanism for supersession
Failure: Design is recorded in chat, compaction loses it, next session re-derives from scratch
Success proof: User has clear direction for implementation without re-debating the decision
Cross-session: Decision recorded in chat survives until compaction. After compaction, /why or /recap
             may recover the reasoning. If the decision hasn't been recorded yet, user re-derives.
```

### Scenario 6: Cross-compaction, cross-day, cross-terminal resume

```
User intent: "I was working on something yesterday in another terminal. Where was I?"
Routing: /recap
Public surface: /recap (full chain walk)
Internal mechanisms: session_chain.walk_session_chain(session_id) → handoff-file chain → mtime-gap fallback
Evidence read: All transcript files in the session chain for this terminal
Output/artifact: Session history with origin-tagged synthesis + handoff summary
Storage: Conversational (chat output) + JSON handoff (metadata only, ≤5 min)
Downstream consumer: User reads summary, picks up where they left off
Authority: Advisory — transcript is authoritative, recap is synthesis
Freshness: Based on transcript mtimes — stale if handoff chain is broken
Failure: Wrong session_id → wrong chain walked → silent miss (the anti-compaction invariant prevents this
         ONLY if the LLM correctly derives session_id from transcript_path)
Cross-terminal: /recap walks only ONE terminal's chain. If work spans terminals, user must call /recap
               from both. No cross-terminal chain merge. This is a KNOWN LIMITATION.
Revision identity: No git revision in any handoff or recap artifact. If repo has moved between sessions,
                  the recap won't know.
Conflict handling: If terminal A and terminal B both modified the same files, no conflict detection exists.
                  User resolves manually.
```

### Scenario 7: User states ordinary-language need without knowing command name

```
User intent: "I need to understand why this keeps breaking"
Routing: "why" matches /why (decision archaeology) AND /debrief (NLP trigger) AND "what gaps remain" → debrief
Ambiguity: This exact phrase matches /debrief ("why is this broken" trigger) AND /rns ("analyze this output")
           AND /why (semantic match)
Correct route: /debrief (the user is asking about a CURRENT problem, not a PAST decision)
Likely wrong route: /why (the name "why" seems to fit better than "debrief")
User correction needed: User learns that /debrief = current failures, /why = past decisions
Success proof: After 2-3 corrections, user learns the distinction
```

### Cross-session and Cross-terminal Gaps

| Gap | Current behavior | Risk |
|---|---|---|
| **Workstream identity** | No explicit workstream concept — sessions are the unit | Work spanning multiple sessions has no named container |
| **Repository revision** | Not captured in handoff or debrief artifacts | Could produce stale recommendations |
| **Stale-state rejection** | No mechanism to reject stale handoff data | User must manually verify timeliness |
| **Cross-terminal conflict** | No merge or conflict detection | Duplicate findings across terminals |

---

## 7. Revised Cognitive-Load Comparison

### Rubric

Each alternative is scored on these dimensions (heuristic estimates, not measured):

1. **Canonical commands to recall** — how many commands the user must hold in working memory
2. **Plausible wrong commands per representative intent** — for each of the 10 questions, how many commands sound vaguely right
3. **Sequencing rules** — how many ordering constraints must be remembered ("do X before Y")
4. **Hidden modes** — how many commands have sub-modes the user doesn't see at invocation time
5. **Discoverable aliases** — how many additional names the user might encounter and wonder about
6. **Repeated context** — how often the user must re-supply information (file paths, session IDs)
7. **State reconstruction** — how much work to rebuild context after compaction
8. **Likely wrong-first-choice** — count of common mis-routings

### Comparison

| Dimension | Current (12 SDLC) | Alternative A (~16) | Alternative B (8+5) | Alternative C (5+aliases) |
|---|---|---|---|---|
| Canonical commands | 12 | 16 (kept all + aliases) | 8 | 5 |
| Plausible wrong commands per intent | ~3-4 | ~2-3 | ~1-2 | ~1 |
| Sequencing rules | "debrief before rns" (unwritten) | same as current | documented line | implicit (diagnose→plan→verify) |
| Hidden modes | /debrief (4), /review (5+), /check (4) | same as current | /debrief (2 views), /check (4 tiers) | /verify (all readiness modes) |
| Discoverable aliases | 2 stubs | 2 stubs + /handoff | 7 (one transition cycle) | ~16 (all old names) |
| Repeated context | session ID on /recap, file path on /debrief | same | same | same |
| State after compaction | /recap rebuilds from chain | same | same | same |
| Likely wrong-first-choice count | /why vs /debrief, /rns vs /recap, /risks vs /check | /why vs /debrief, /risks vs /check | /why vs /debrief (remaining) | /situation vs /diagnose (less overlap) |

### Key insight

The consolidation moves don't reduce the most frequent friction point: **the user must still decide between `/why` and `/debrief`** in all three alternatives. That distinction (past decision vs current failure) is inherent to the problem domain, not a naming problem. A renamed `/why` (e.g., `/trace-decision`, `/history`) might reduce confusion but would add a new command name to learn.

---

## 8. Independent Implementation Candidates

Each candidate is independently implementable and independently skippable. No prerequisite chain.

### Candidate 1: Rename `/rns` to `/prioritize`

| Dimension | Value |
|---|---|
| **Evidence supporting** | `/rns` is an acronym with zero discoverability. User explicitly wants "coherent, intentional skill names." |
| **Public behavior affected** | `/rns` stops being the canonical name. `/prioritize` becomes primary. `/rns` works as alias during transition. |
| **Dependencies** | None |
| **Capability preservation** | Full — same SKILL.md body, same LLM behavior, new frontmatter name |
| **Migration/alias** | Add `aliases: [/rns]` to frontmatter. Old name continues working. |
| **Acceptance test** | `/prioritize` loads the skill; `/rns` also loads it (alias); output identical. |
| **Rollback** | Revert the rename; `/prioritize` becomes an alias or is removed. |
| **Why NOT to do it** | If the user already knows `/rns` and uses it fluently, changing the name creates unnecessary friction. |

### Candidate 2: Rename `/epistemic-check` to `/check-claims` or `/audit-response`

| Dimension | Value |
|---|---|
| **Evidence supporting** | `/epistemic-check` is academic terminology. User won't guess what it does. |
| **Public behavior affected** | Old name disappears (or becomes alias). New name at `/check-claims` or `/audit-response`. |
| **Dependencies** | None |
| **Capability preservation** | Full |
| **Migration/alias** | Optional alias for old name |
| **Acceptance test** | New name loads the skill; user can guess it validates claims in responses. |
| **Rollback** | Revert rename |
| **Why NOT to do it** | Low-value renaming if the user rarely uses this skill. `/check-claims` may collide with `/check` in routing. |

### Candidate 3: Deprecate `/retro` and `/top-problems` stubs

| Dimension | Value |
|---|---|
| **Evidence supporting** | Both are already absorbed by `/debrief`. Stubs add cognitive noise. |
| **Public behavior affected** | Old commands stop working. User must use `/debrief chain` and `/debrief top`. |
| **Dependencies** | None |
| **Capability preservation** | Full — `/debrief chain` and `/debrief top` already provide the functionality. |
| **Migration/alias** | One-release-cycle deprecation notice; then remove stubs |
| **Acceptance test** | `/retro` and `/top-problems` return "deprecated — use /debrief chain / /debrief top" |
| **Rollback** | Restore stub SKILL.md files |
| **Why NOT to do it** | Low value — stubs are invisible unless the user explicitly types them. Removing them creates a breaking change for any script or instruction that references them. |

### Candidate 4: Add `--quick-risk` mode to `/check`

| Dimension | Value |
|---|---|
| **Evidence supporting** | User wants coherent readiness checking. `/risks` and `/check` answer different questions but both are "is this safe?" |
| **Public behavior affected** | `/check --quick-risk` runs the risk pass. `/risks` still works independently. |
| **Dependencies** | None at code level. Requires SKILL.md documentation update. |
| **Capability preservation** | Full — `/risks` unchanged |
| **Migration/alias** | `/risks` stays. `--quick-risk` is additive. |
| **Acceptance test** | `/check --quick-risk "change the router"` produces risk table + mitigations matching standalone `/risks` output. |
| **Rollback** | Remove `--quick-risk` from /check documentation |
| **Why NOT to do it** | `/risks` is `allowed-tools: []` — a pure LLM skill. Making it a `/check` phase would require reimplementing it within `/check`'s execution model. Not worth the engineering. |

### Candidate 5: Create `/debrief view friction|behave` modes

| Dimension | Value |
|---|---|
| **Evidence supporting** | `/friction` and `/behave` capabilities overlap with `/debrief`'s transcript-mining. |
| **Public behavior affected** | `/friction` and `/behave` become aliases for `/debrief view friction|behave`. |
| **Dependencies** | None at code level. Requires SKILL.md updates for both skills. |
| **Capability preservation** | Full — same code paths, new entry convention |
| **Migration/alias** | Old commands remain as aliases |
| **Acceptance test** | `/debrief view friction <transcript>` produces identical friction findings to standalone `/friction <transcript>`. |
| **Rollback** | Restore standalone SKILL.md frontmatter names |
| **Why NOT to do it** | Low value if the user never types `/friction` or `/behave`. Renaming creates unnecessary churn for existing users who depend on the command names. |

### Candidate 6: Document `/why` vs `/debrief` boundary

| Dimension | Value |
|---|---|
| **Evidence supporting** | This is the most frequent ambiguous-routing case. The user may type `/why` when they should type `/debrief`. |
| **Public behavior affected** | None — documentation only |
| **Dependencies** | None |
| **Capability preservation** | Full |
| **Migration/alias** | N/A — documentation change only |
| **Acceptance test** | User reads boundary docs and correctly routes "why did this break?" to `/debrief`. |
| **Rollback** | Revert documentation |
| **Why NOT to do it** | Documentation is the weakest intervention. The user may not read it before invoking a command. |

### Candidate 7: `/design` output template improvement

| Dimension | Value |
|---|---|
| **Evidence supporting** | User wants design decisions captured. Current `/design` output is inconsistent (sometimes includes alternatives, sometimes not). |
| **Public behavior affected** | `/design` output more consistently includes alternatives, criterion, verdict, and reversal trigger. |
| **Dependencies** | None |
| **Capability preservation** | Full — no capability removed |
| **Migration/alias** | N/A |
| **Acceptance test** | `/design "choose a database"` produces output with at least: alternatives, criterion for selection, chosen option, reversal trigger. |
| **Rollback** | Revert SKILL.md prompt additions |
| **Why NOT to do it** | Prompt-level changes are hard to enforce. The LLM may follow or ignore the template. No runtime validation exists. |

---

## Ranked Implementation Candidates

| Rank | Candidate | Value | Cost | Risk | Evidence level |
|---|---|---|---|---|---|
| **1** | Document `/why` vs `/debrief` boundary | High — resolves most frequent routing confusion | Lowest — 15 min | Low — docs only | Source-visible ambiguity |
| **2** | Rename `/rns` → `/prioritize` | High — fixes worst discoverability problem | Low — SKILL.md rename | Low — alias preserves old name | Source-visible poor naming |
| **3** | Rename `/epistemic-check` → `/check-claims` | Medium — fixes obscure name | Low — SKILL.md rename | Low — alias preserves old name | Source-visible poor naming |
| **4** | `/design` output template improvement | Medium — more consistent DecisionRecord | Low — SKILL.md prompt | Low — no enforcement | User explicitly stated |
| **5** | Deprecate `/retro`, `/top-problems` stubs | Low — minor cognitive noise reduction | Low — remove stubs | Medium — breaking change | Already absorbed |
| **6** | `/debrief view friction|behave` modes | Low — capability already present | Medium — SKILL.md + aliases | Low — aliases preserve | Duplicate mining capability |
| **7** | Add `--quick-risk` to `/check` | Lowest — incompatible execution models | Highest — reimplementation | Medium — may break | Not justified |

### Single smallest change recommended first

**Candidate 1: Document `/why` vs `/debrief` boundary.**

Evidence: This is the most frequent routing ambiguity (approximately 3 of 10 representative requests are ambiguous between the two). It requires no code changes, no renames, no aliases, no new capabilities. It is pure documentation. If it does not reduce wrong-command routing after one session, escalate to Candidate 2.

### What would falsify this recommendation

- The user reports that the `/why` vs `/debrief` documentation did not help and they continue to route incorrectly. → Escalate to rename `/why` to `/decision-history` or similar.
- The user reports that `/rns` being a meaningless acronym is their #1 frustration. → Make Candidate 2 (rename) the first priority instead.
- The user reports they never type `/why` and the boundary documentation is irrelevant. → Skip Candidate 1 entirely.

---

## Summary

| Section | Finding |
|---|---|
| **Canonical inventory** | 10 SDLC commands + 2 stubs = 12 user must navigate. Alternative B honest count: 8 canonical + 5 independent tools + 7 aliases. |
| **Handoff** | Not a separate command. Keep as `/recap` output mode. The existing JSON handoff (snapshot plugin) handles chain reconstruction. |
| **Readiness contracts** | 5 distinct contracts. Keep separate. `/check` and `/review` already share an entry point. `/risks` and `/check` have incompatible execution models. Document escalation path instead. |
| **/why vs /debrief** | Distinct temporal frames (past decision vs current failure). Keep both. Document boundary. |
| **DecisionRecord** | No consumer exists. Defer schema. Improve `/design` output template as prompt-level change only. |
| **Cognitive scoring** | 12 → 8 canonical is a real reduction. The 5 independent tools (improve, genius, council, review, go) are not SDLC-specific. The remaining routing friction is inherent to the domain. |
| **Implementation** | 7 independent candidates ranked by value/cost/risk. Start with boundary documentation (#1). Rename `/rns` (#2) only if the user confirms the acronym frustrates them. |

---

`DESIGN_READY_FOR_APPROVAL`
