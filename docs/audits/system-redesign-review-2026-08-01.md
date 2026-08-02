# Architecture Review: Proposed System Redesign

**Date:** 2026-08-01
**Reviewer:** Grok (session 019fc0a7)
**Evidence base:** Four discovery subagents (skill catalog inventory, investigation-state artifacts, wiki/KB infrastructure, model routing/authority) plus direct repository inspection of `/why`, `/harvest`, `/close`, `/agy`/`/codex`/`/mmx` SKILL.md files, skill-catalog.md, wiki directory structure, config.toml, and AGENTS.md.

---

## A. Executive verdict

The plan identifies real problems — command overlap, diffuse investigation state, and repeated repository rereading — but substantially **underestimates how much of the proposed infrastructure already exists** in this workspace. The wiki vault at `P:/.data/wiki/` already contains 810 curated concept pages, 7,565 indexed transcripts, a skill catalog of 657 entries, and a documented promotion path from raw source to durable knowledge. The `/why` skill already implements evidence-tiered investigation with competing hypotheses, discriminating tests, and feedback-to-wiki loops. The `/harvest` skill already provides event-sourced cross-session obligation tracking. The `/agy`/`/codex`/`/mmx` skills already implement fail-open advisory external-model integration with a documented evidence hierarchy. The plan's sequencing is sound in principle (audit before build, pilot before scale), but several workstreams risk creating **parallel mechanisms** that duplicate existing capability rather than extending it. The strongest contribution is the command-surface simplification direction and the cognitive-contract framing for `/research` vs `/design` vs `/plan`. The weakest is the KB infrastructure proposal, which describes building what the wiki already provides. The plan is coherent with revisions: collapse workstreams B and C into "extend existing artifacts" rather than "build new infrastructure," and gate everything behind the Phase 1 audit the plan itself prescribes.

**Overall verdict: `PLAN_COHERENT_WITH_REVISIONS`**

---

## B. Strongest parts of the plan

1. **Separation of user intent from internal mechanisms** (Principle 1). This is architecturally correct and the workspace already violates it in places — reasoning techniques like Tree of Thoughts appear as named concepts that agents reference by name rather than as internal selection criteria. The principle of hiding implementation-detail commands is sound.

2. **Distinct cognitive contracts for workflow commands** (Principle 2). The `/research` vs `/design` vs `/plan` vs `/go` distinction maps to genuinely different cognitive modes (reduce uncertainty → reduce ambiguity → reduce execution risk → reduce implementation risk). This is more useful than the current surface where `/plan` and `/go` and `/design` sometimes overlap.

3. **Evidence hierarchy** (Authority principles). The six-tier hierarchy (runtime > static analysis > repository > external sources > cross-model review > self-evaluation) is already documented in this workspace's `~/.grok/AGENTS.md` and is correct. The plan's restatement reinforces an existing strength.

4. **Fail-open advisory constraint on external models.** Already implemented in `/agy`, `/codex`, `/mmx` per their SKILL.md files and ADR-009. The plan's insistence on this constraint is well-placed.

5. **Phased sequencing with evidence gates.** The "audit before simplify, pilot before scale, expose `/kb` only after proven" sequence is the right instinct. It prevents premature infrastructure commitment.

6. **Explicit rejection of a general Graph-of-Thoughts runtime.** The plan says "begin with a narrower artifact, not a general graph runtime." This is the correct bias — graph runtimes are infrastructure that absorbs effort without proportional outcome gain.

---

## C. Load-bearing assumptions

| Assumption | Why it matters | Verified or unverified | Evidence required | Consequence if false |
|---|---|---|---|---|
| Commands like `/ask`, `/all`, `/tldr`, `/t`, `/sqa` are active and consumed | Justifies command-surface simplification workstream | **Partially unverified.** `/all` confirmed as alias for `/research` in claude-cache-local. `/find`, `/web` confirmed. `/ask`, `/tldr`, `/t`, `/sqa` not found in skill catalog. | Run `index_skills.py --audit` and grep command registrations in the actual host config. Check `~/.claude/settings.json` and `~/.grok/config.toml` for command dispatch entries. | If these commands don't exist or aren't consumed, the simplification workstream is solving a phantom problem. |
| Investigation reasoning is "buried in conversation text" with no structured artifact | Justifies typed investigation state (Workstream B) | **Partially verified — gap is narrower than plan implies.** `/why` already produces structured evidence-tiered output with hypotheses, falsifiers, and feedback-to-wiki, but output is ephemeral (conversation-only, no persistent file). `/harvest` persists cross-session obligations. Handoffs capture work-stream state at completion. | Compare `/why` output structure against the proposed `InvestigationState` fields. Check whether handoff files already capture hypothesis/evidence state. | If existing artifacts cover 80%+ of the proposed fields, Workstream B should be `EXTEND_EXISTING`, not `NEW_MECHANISM_JUSTIFIED`. (Confirmed: 12 of 14 fields already exist in `/why` protocol — gap is persistence only.) |
| Agents "repeatedly reread complete repositories, session transcripts, research collections" | Justifies durable KB infrastructure (Workstream C) | **Unverified.** The wiki has 810 concepts and 7,565 transcripts. Whether agents reread them wholesale depends on whether retrieval is targeted or not. | Audit actual agent behavior: do sessions read entire files or use grep/targeted reads? Check token consumption patterns. | If agents already use targeted retrieval (grep, wiki query), the KB infrastructure solves a problem that doesn't exist at the scale claimed. |
| The system operates across Claude Code and Codex CLI environments with different hook capabilities | Justifies the "must not assume hooks everywhere" constraint | **Verified.** `P:/AGENTS.md` documents Grok Build vs Claude Code differences. `~/.codex/skills/` contains 10 skills. Hook types differ (command/http in Grok, command/prompt/agent in Claude). | Already confirmed by repository inspection. | N/A — assumption holds. |
| A unified `/research` command would improve routing accuracy over the current diffuse retrieval surface | Justifies introducing `/research` as a new command | **Unverified.** Current routing already works via skill descriptions and AGENTS.md routing tables. The `/www` skill already does wiki→web→wiki research. | Measure current command-selection errors. Compare against a proposed `/research` contract in a pilot. | If the current routing surface already works for the operator's actual usage patterns, adding `/research` increases rather than decreases cognitive load. |
| A structural code graph (kbask, Graphify, etc.) would provide value beyond `grep` + `read_file` | Justifies KB code-structure layer | **Unverified.** `build_skill_graph.py` exists in the wiki scripts but is for skill graphs, not code graphs. `code_analysis.py` exists for per-package AST analysis in `/refactor`. No persistent cross-package code graph exists. | Test whether a persistent code graph answers "who calls X" faster than grep + read_file. | If grep + read_file already answers structural questions in <30s, the code graph is infrastructure overhead. |

---

## D. Boundary review

| Capability A | Capability B | Intended distinction | Actual ambiguity | Recommended boundary |
|---|---|---|---|---|
| `/research` (proposed) | `/www` (existing) | `/research` = decision-grade evidence gathering; `/www` = wiki→web→wiki compound | **High overlap.** `/www` already does local wiki query → web research → wiki write-back. `/research` as described would subsume `/www`. | Either: (a) rename `/www` to `/research` and expand its local-evidence inspection, or (b) keep `/www` as the external-research specialist and make `/research` a meta-router that dispatches to `/www`, `/wiki query`, and repo inspection. Option (a) is simpler. |
| `/research` (proposed) | `/find` / `/web` / `/search` (existing) | `/research` = synthesis-grade; others = retrieval primitives | **Moderate overlap.** `/web` and `/search-fleet` already do multi-backend search with RRF aggregation. `/find` does local retrieval. The question is whether `/research` adds a synthesis layer or just renames. | `/research` should be the synthesis consumer of `/find` + `/web` + `/wiki`, not a replacement for them. It should never re-implement retrieval. |
| `/design` (existing) | `/plan` / `/plan-writer` (existing) | `/design` = choose direction; `/plan` = ordered implementation path | **Low overlap.** Already well-separated. `/design` produces a design doc; `/plan-writer` produces an implementation plan. The plan's framing reinforces this. | Keep as-is. Ensure `/go` consumes plan-writer output, not design output directly. |
| `/verify` / `/check` / `/review` (existing) | `/red-team` (existing) | Verification = did the work match the claim; review = evaluate quality; red-team = adversarial challenge | **Moderate overlap.** `/check` does PASS/FAIL session verification. `/grok-verify` does evidence-first completion gating. `/review` does code/package review with FINDINGS.md. `/red-team` does adversarial review. `/trace` does manual trace-through. Five mechanisms with partially overlapping function. | Consolidate to three: `/check` (session completion), `/review` (code/package quality), `/red-team` (adversarial). Absorb `/grok-verify` and `/trace` as `/review` modes or `/check` internals. |
| Working investigation state (proposed `InvestigationState`) | Durable knowledge (wiki concepts) | Investigation = live, changing; wiki = reviewed, stable | **Low overlap in principle, high risk in practice.** The boundary is clear: investigation state is mutable and session-scoped; wiki concepts are immutable and durable. The risk is that investigation state becomes a de facto second wiki if it persists too long. | Investigation state must have a TTL or explicit promotion/discard gate. The `/why` Step 15 feedback-to-wiki loop already models this: inline investigation → mechanical gate → cross-model review → wiki write or drop. Extend this pattern rather than inventing a new artifact type. |
| External-model advisory output | Authoritative conclusions | External = hypothesis; repo/runtime = fact | **Low overlap.** Already well-separated by the evidence hierarchy. `/agy`/`/codex`/`/mmx` are fail-open advisory. | Keep as-is. The evidence hierarchy in AGENTS.md already enforces this. |
| `/handoff` (existing) | `InvestigationState` (proposed) | Handoff = continuation state for next session; investigation = live reasoning state | **High overlap.** Handoffs already capture work-stream context, open questions, and state. The plan's InvestigationState adds structured hypothesis/evidence tracking, but handoffs could be extended to carry this. | Extend handoff schema to optionally carry hypothesis/evidence blocks, rather than creating a new artifact type. |

---

## E. Workstream verdicts

### 1. Command-surface simplification

**Problem:** 657 skills across 21 scopes with documented overlap, aliases, deprecated entries, and inconsistent naming. The operator must remember which of `/web`, `/search-fleet`, `/www`, `/wiki`, `/firecrawl-search` to use for a given retrieval task.

**Evidence the problem exists:** `PROVEN` — skill-catalog.md documents 657 entries; 9+ explicitly deprecated entries found; 5+ aliases confirmed; functional overlap groups identified across search, review, planning, session management, and external models. Config.toml shows 29 plugins disabled, only 9 enabled — much pruning has already happened via config disablement, not skill deletion.

**Proposed solution:** Retire overlapping commands, consolidate TLDR variants, rename unclear commands, absorb verification rules into workflows, avoid exposing implementation details as commands.

**Existing mechanism that may already solve it:** The skill catalog itself (`skill-catalog.md`) plus the routing tables in `~/.grok/AGENTS.md` (review skill routing table, web-search tool selection table) already provide a routing layer. The `skill-prune` skill at `P:/.agents/skills/skill-prune/` already proposes merges, archives, and promotions.

**Expected user outcome:** Fewer command-selection errors, faster first-pass routing, reduced cognitive load.

**Dependencies:** Phase 1 audit must establish which commands are actually consumed vs. present-but-unused. The 537 Claude-only skills cannot be simplified from a Grok Build session without coordinating with the Claude Code deployment.

**Failure modes:** Renaming files without updating consumed registrations (the plan acknowledges this). Removing an alias that external scripts or handoffs reference by name. Creating new commands that overlap with existing skills. Building a taxonomy based on elegance rather than measured usage.

**Verdict: `SIMPLIFY_EXISTING`**

The problem is real, but the solution should be pruning and consolidation of the existing 120 Grok-active skills (of which only ~9 plugin sets are actually enabled per config.toml), not introducing new commands like `/research` that add to the surface. Use `skill-prune` + the existing routing tables. Retire deprecated entries. Do not add `/research` as a new command until the audit shows that the current retrieval surface (web, search-fleet, www, wiki) actually fails to route correctly.

---

### 2. Typed investigation state

**Problem:** Reasoning during investigations is buried in conversation text, making it hard to preserve across compaction, verify independently, or reuse in future sessions.

**Evidence the problem exists:** `PARTIALLY PROVEN` — compaction is a real issue (AGENTS.md documents "vanishing writes" and "stale-read" rules). `/why` already produces structured investigation output with evidence tiers, competing hypotheses, falsifiers, and feedback-to-wiki, but output is **ephemeral** (conversation-only). `/harvest` persists cross-session obligations. Handoffs preserve work-stream context at completion (terminal artifact). No existing artifact is created when an investigation *opens* and updated incrementally as evidence accumulates.

**Proposed solution:** A structured `InvestigationState` artifact recording hypotheses, evidence, assumptions, confidence, discriminating tests, test outcomes, unresolved questions, and provenance.

**Existing mechanism that may already solve it:** `/why` covers 12 of 14 proposed InvestigationState fields in its inline protocol:

| Proposed `InvestigationState` field | Already in `/why`? | Gap type |
|---|---|---|
| Question/decision under investigation | Step 2 | Persistence only |
| Competing hypotheses | Step 9a (3 ranked) | Persistence only |
| Supporting evidence | Step 11a (evidence for) | Persistence only |
| Contradicting evidence | Step 11a (evidence against) | Persistence only |
| Assumptions | Step 3 (surfaces implicitly) | Minor protocol gap |
| Source authority | Step 4b (evidence tiers) | Persistence only |
| Confidence/uncertainty | Step 4b (4-tier, weakest-link) | Persistence only |
| Candidate discriminating tests | Step 9a + Step 12 (Toulmin) | Persistence only |
| Test outcomes | Not tracked | Protocol gap |
| Unresolved questions | Step 11c (admit ignorance) | Persistence only |
| Current recommendation | Step 16 output | Persistence only |
| Provenance | Receipts per claim | Persistence only |
| Identity and ownership | Session-scoped | Persistence only |
| Completion status | Not tracked | Protocol gap |

`/harvest` provides persistent event-sourced storage with lifecycle and verification contracts.

**Expected user outcome:** Faster resolution of competing hypotheses, fewer unsupported completion claims, preserved reasoning through long investigations.

**Dependencies:** Must not become a second task-state, routing, or completion authority (the plan says this explicitly).

**Failure modes:** Creating a persistent artifact that nobody reads. Recording self-reported evidence without deterministic validation. The artifact becoming a de facto second wiki. The artifact becoming a second completion authority that competes with `/close` and `/check`.

**Verdict: `EXTEND_EXISTING`**

Extend `/why`'s output to optionally persist to a file (e.g., `P:/docs/investigations/<topic>-<date>.md`) when the investigation spans multiple sessions or compaction boundaries. Extend `/harvest` to accept investigation findings as obligation items. Do not create a new `InvestigationState` artifact type. The `/why` → handoff → `/harvest` chain already covers the lifecycle. The plan's field list is essentially `/why`'s step outputs persisted to disk. The extension needed: (1) `/why` writes structured output to durable file, (2) `/why` Step 0.5 searches prior investigation files, (3) add test-outcome and completion-status fields.

---

### 3. Durable KB infrastructure

**Problem:** Agents repeatedly reread complete repositories, transcripts, and source archives because there is no targeted retrieval mechanism for durable project knowledge.

**Evidence the problem exists:** `UNVERIFIED` — the wiki vault with 810 concepts, 7,565 transcripts, 648 skill stubs, and 70+ capability descriptions already exists. Whether agents reread these wholesale or use targeted retrieval (grep, wiki query) is not established. The `/wiki` skill supports query mode. The skill-catalog.md provides an index. FTS5 search exists via `wiki_search.py`.

**Proposed solution:** A `/kb` capability with four layers: code structure graph, curated conceptual knowledge, session/decision history (GraphRAG), and raw source evidence (NotebookLM).

**Existing mechanism that may already solve it:**

- **Curated conceptual knowledge:** `PROVEN` — `P:/.data/wiki/concepts/` has 810 reviewed pages with 681-line `SCHEMA.md` enforcing structure. The `/wiki` skill queries and writes this. FTS5 search via `wiki_search.py`. Auto-link injection via `wiki_after_write.py`. Contradiction scanner via `wiki_contradiction_scan.py`.
- **Session/decision history:** `PROVEN` — `P:/.data/wiki/sources/transcripts/` has 7,565 files. `/recap-grok` and `/aar` walk session transcripts. `/dream` does cross-session consolidation over 90 days of handoffs + AARs.
- **Code structure:** `GAP CONFIRMED` — No persistent cross-package code graph exists. `code_analysis.py` is per-package AST analysis for `/refactor` (single-shot). `build_skill_graph.py` builds skill relationship graphs, not code graphs.
- **Raw source evidence:** `PROVEN` — `/wiki-yt` and `/notebooklm` skills provide NotebookLM → wiki promotion with 4-hop provenance. The `_incoming/` directory has durable/signal candidate reports.
- **Promotion path:** `PROVEN` — chained pipeline: raw source → ingest skill → `validate_wiki_entry.py` → `wiki_after_write.py` → `wiki_contradiction_scan.py` → log.md → `/dream` cross-session re-eval → AGENTS.md promotion after ≥5 sessions + ≥30 days stable.
- **Session-history search:** `PARTIAL` — `session_search.sqlite` exists at `~/.grok/sessions/` but is **orphaned** (no Python script references it). Active search is regex-based (`analyze_session_patterns.py`) or transcript-walking (`/recap-grok`).

**Expected user outcome:** Reduced token consumption, improved retrieval precision, attributable answers with current evidence.

**Dependencies:** Phase 1 audit must measure actual token waste from rereading. Phase 4 pilot must prove a specific backend adds value beyond grep + wiki query.

**Failure modes:** High indexing cost with little retrieval benefit. Stale graph results treated as repository truth. Multiple stores becoming competing sources of truth. Automatic promotion of speculative output into durable knowledge. Building infrastructure before a pilot proves value.

**Verdict: `BLOCKED_PENDING_EVIDENCE`**

The KB infrastructure largely exists. The wiki IS the durable KB. The skill catalog IS the structural index. The transcript archive IS the session history. The promotion pipeline IS the raw-to-durable path. The question is not "should we build a KB" but "is the existing KB's retrieval insufficient?" That question requires measuring actual agent retrieval behavior (Phase 1 audit). Two narrow gaps are real: (1) no persistent cross-package code-structure graph, (2) orphaned session-search SQLite. Both are Phase 4 pilots, not Phase 1 infrastructure. If the audit shows agents reread entire files because grep is insufficient, the fix is better retrieval tooling (e.g., `context7` MCP, semantic search), not a new KB layer.

---

### 4. Unified routing across retrieval and KB layers

**Problem:** The retrieval surface is fragmented across `/web`, `/search-fleet`, `/www`, `/wiki`, `/firecrawl-search`, `/find`, and potentially `/research` and `/kb`, with no unified routing layer.

**Evidence the problem exists:** `PROVEN` — the skill catalog and discovery agent's overlap analysis confirm 5+ retrieval skills with overlapping function. AGENTS.md documents a web-search tool selection hierarchy (DDG → firecrawl → mmx → web_search) that is already a routing layer, but it lives in prose rules, not in a dispatch mechanism.

**Proposed solution:** A unified router that selects the appropriate retrieval backend based on query intent.

**Existing mechanism that may already solve it:** `/search-fleet` already implements capability-routed multi-backend search with RRF aggregation, reading a tool registry at `~/.grok/search-fleet.toml`. This IS a unified retrieval router. The AGENTS.md web-search selection table IS a routing policy.

**Expected user outcome:** Improved first-pass routing accuracy, reduced command-selection errors.

**Dependencies:** Must not become a second authority. Must remain fail-open.

**Failure modes:** The unified router becoming a second routing authority that competes with AGENTS.md rules. The router making incorrect intent classifications that route to the wrong backend. Adding a routing layer when direct skill invocation would be simpler.

**Verdict: `CLARIFY_EXISTING`**

`/search-fleet` already exists as a unified retrieval router. The issue is that it coexists with `/web`, `/www`, and `/wiki` as separate skills, creating confusion about when to use which. The fix is documentation and routing rules (clarify in AGENTS.md when to use `/search-fleet` vs `/web` vs `/www`), not a new routing mechanism. If `/search-fleet` is insufficient, extend its backend registry rather than building a parallel router.

---

### 5. External-model advisory integration

**Problem:** External LLMs (Gemini, Codex, MiniMax) should be available as bounded advisory specialists without becoming mandatory dependencies.

**Evidence the problem exists:** `NOT A PROBLEM` — the existing implementation already handles this correctly. `/agy`, `/codex`, `/mmx` are fail-open advisory skills with documented conductor patterns (5 assignment-adequacy dimensions × 4 classifications, 4 dispositions, 7 strict-precedence outcome labels). ADR-009 records the cross-model second-opinion architecture decision. The evidence hierarchy ranks external-model review at tier 5 (below repo evidence). The nemotron routing policy documents provider preferences. Config.toml confirms `default = "glm-5-2"` with two-lane model pool (reasoning: glm-5-2; code: tier-1 from coding-model-pool.md with fallback chain).

**Proposed solution:** External LLMs as bounded advisory specialists for hypothesis generation, test design, falsification, and adversarial review. Fail-open. No blocking on provider failure.

**Existing mechanism that already solves it:** Everything described in the proposal is already implemented and documented. ADR-009 status: implemented (PR 0-4 shipped). Fail-open contract is explicit and load-bearing. Three different shapes correctly documented (`/agy` = file+sandbox+review; `/codex` = file+sandbox with mandatory read-only override; `/mmx` = chat-only HTTP with unique web-search capability).

**Expected user outcome:** N/A — already achieved.

**Dependencies:** None new.

**Failure modes:** Over-engineering an already-solved problem. Adding abstraction layers between the conductor skills and the CLI invocations.

**Verdict: `NO_CHANGE`**

The external-model advisory integration is already correctly implemented. The plan's description matches the existing implementation almost exactly. No action needed.

---

## F. End-to-end contract gaps

| Mechanism | Producer | Storage | Consumer | Authority | Freshness check | Failure behavior | Missing contract |
|---|---|---|---|---|---|---|---|
| Wiki concepts | `/wiki` write, `/why` Step 15, `/www` Phase 3 | `P:/.data/wiki/concepts/*.md` | `/wiki query`, `/why` Step 0.5, `/www` Phase 1, agent inline grep | `SCHEMA.md` + frontmatter `status:` field | `updated:` frontmatter field; `verification:` field | Stale concept used as fact if not re-verified | **No staleness rejection contract** — a concept from 2026-07 can be cited as fact in 2026-08 without checking whether the code it describes has changed. |
| Skill catalog | `index_skills.py` | `P:/.data/wiki/concepts/skill-catalog.md` | Agent skill lookup, `/check`, routing decisions | Auto-generated (derived, not source) | `verification: generated_<date>` frontmatter | Stale catalog lists skills that were deleted; omits skills that were added | **No invalidation signal** — the catalog is regenerated manually. No hook fires when a skill is added/removed to trigger regeneration. |
| Handoffs | `/handoff` skill | `P:/docs/handoffs/*/HANDOFF.md` | Next session, `/close` scanner, `/harvest scan-handoffs` | The handoff file itself (file existence = authority) | `git log` on handoff path | Stale handoff references files/branches that no longer exist | **No expiration contract** — handoffs accumulate indefinitely. `/close` checks for coverage but doesn't expire old handoffs. |
| Harvest obligations | `/harvest add/capture` | `P:/.data/harvest/events/*.json` | `/harvest show/review`, `/close`, session start | Event-sourced (immutable events + claim files) | Event timestamp + lifecycle state | Open obligations never collected → accumulate as noise | **Partial** — lifecycle has RETIRE_CANDIDATE state, but no automatic decay-to-retirement. Decay affects ordering only, not state. |
| `/why` investigation output | `/why` Step 16 | Inline (conversation only — no persistent file unless handoff written) | Current session only (lost at compaction) | The RCA output itself | N/A (ephemeral) | Investigation lost at compaction; future `/why` Step 0.5 can't find it | **No persistence contract** — `/why` output is ephemeral unless Step 15 promotes to wiki or Step 14 routes to handoff. Multi-session investigations have no continuity artifact. |
| `/review` findings | `/review` skill | `<run_dir>/FINDINGS.md` + `findings.json` | Operator, `/ship`, `/check` | The findings file on disk | `git log` on run_dir | Findings reference code that has since changed | **No freshness-vs-code contract** — findings from a review of commit A may be cited as valid after commit B changes the reviewed code. |
| Session transcripts | Grok Build session manager | `~/.grok/sessions/<id>/` + wiki `sources/transcripts/` | `/recap-grok`, `/aar`, `/dream`, `/capture` | Session ID binding | Session timestamp | Transcript may be incomplete (session crash, truncation) | **No completeness contract** — transcripts are assumed complete but may be truncated. |
| Session search SQLite | UNKNOWN (orphaned) | `~/.grok/sessions/session_search.sqlite` | UNKNOWN (no script references it) | UNKNOWN | UNKNOWN | UNKNOWN | **No contract at all** — the file exists but no producer or consumer is identifiable. Either rehydrate or delete. |
| External-model output | `/agy`, `/codex`, `/mmx` conductor | Run record (inline or log file) | Current session only | Advisory (tier 5 evidence) | N/A (advisory, not durable) | Provider timeout/serde error → fail-open (correct) | **No gap** — fail-open contract is well-documented and implemented. |

---

## G. Revised architecture

### What to keep (no change)
- **`/go`** as the implementation orchestrator (already authoritative; selects models at subagent dispatch layer, not as user-facing command)
- **`/review`** as the code/package evaluator (already produces FINDINGS.md)
- **`/red-team`** as the adversarial challenger (already well-bounded)
- **`/check`** as the session verifier (already produces PASS/FAIL)
- **`/close`** as the session completion gate (already runs close_accounting.py; two-layer enforcement: file receipt + Stop hook)
- **`/agy`/`/codex`/`/mmx`** as fail-open advisory models (already correctly implemented per ADR-009)
- **`/wiki`** as the durable knowledge query/write interface (already works; 810 concepts, FTS5 search, SCHEMA.md)
- **`/why`** as the root-cause investigator (already implements evidence tiers + feedback loop)
- **`/harvest`** as the cross-session obligation tracker (already event-sourced with lifecycle, 81 tests)
- **`/handoff`** as the continuation document writer (already works; 150+ handoffs)
- **`/search-fleet`** as the unified retrieval router (already implements RRF aggregation)
- **`/design`** as the design-doc producer (already well-separated from `/plan`)

### What to simplify
- **Retire deprecated entries**: delete `why-old`, remove `plan/SKILL.md.disabled` permanently, clean up DEPRECATED cc-skills entries in controllable scopes.
- **Consolidate aliases**: ensure `grok-go`, `grok-sdlc`, `ship`, `model-discover` all redirect cleanly and document the redirect in AGENTS.md routing table (mostly already done).
- **Clarify retrieval routing**: document in AGENTS.md when to use `/search-fleet` (unified search), `/web` (web-only research), `/www` (wiki→web→wiki compound), `/wiki query` (local knowledge lookup). This is a documentation task, not a code change.

### What to extend (not build new)
- **Extend `/why` output persistence**: when an investigation spans compaction boundaries or multiple sessions, allow `/why` to write its structured output to `P:/docs/investigations/<topic>-<date>.md` that Step 0.5 of a future `/why` invocation can find. This addresses the "ephemeral investigation" gap in section F without creating a new artifact type.
- **Extend `/handoff` schema**: add an optional `## Hypotheses` and `## Evidence` section to the handoff template so multi-session investigations can carry structured reasoning state.

### What NOT to build
- **Do not build `/research` as a new command** until the Phase 1 audit shows that the current retrieval routing (`/www`, `/web`, `/search-fleet`, `/wiki`) actually fails. If it fails, rename `/www` to `/research` rather than adding a parallel command.
- **Do not build `/kb` as a new capability** until the Phase 1 audit shows that the existing wiki + skill catalog + transcript archive + grep is insufficient for agent retrieval. If insufficient, the fix is likely better retrieval tooling (semantic search, `context7` MCP), not a new KB layer.
- **Do not build `InvestigationState` as a new artifact type**. Extend `/why` output and `/handoff` schema instead.
- **Do not build a unified retrieval router**. `/search-fleet` already exists.

---

## H. Revised sequence

### Phase 0: Audit (the plan's Phase 1, unchanged)

- **Goal:** Establish what actually exists and is consumed.
- **Blocking prerequisite:** None.
- **Bounded change:** Run `index_skills.py --audit`, grep command registrations in host config, measure actual agent retrieval behavior (token consumption per session, file read patterns), check which skills are invoked vs present-but-unused.
- **Acceptance evidence:** A report listing: (a) active commands with dispatch registrations, (b) consumed vs unused skills, (c) measured retrieval patterns (grep vs full-file reads), (d) actual command-selection error incidents from transcripts.
- **Failure/abandonment criterion:** If the audit shows the current surface works well and agents already use targeted retrieval, stop. The plan solves a problem that doesn't exist at the claimed severity.
- **Out of scope:** Any command changes, any new artifacts, any infrastructure.

### Phase 1: Prune (narrower than the plan's Phase 2)

- **Goal:** Remove confirmed dead weight from the command surface.
- **Blocking prerequisite:** Phase 0 audit identifies specific deprecated/unused/alias entries.
- **Bounded change:** Delete or disable the confirmed dead entries (e.g., `why-old`, disabled plan files, DEPRECATED cc-skills entries in controllable scopes). Update routing tables.
- **Acceptance evidence:** `index_skills.py --audit` shows fewer entries; grep for deleted skill names returns zero hits in active routing configs.
- **Failure/abandonment criterion:** If deletion breaks a consumed reference, restore and document the dependency.
- **Out of scope:** Adding new commands, renaming active commands, building new infrastructure.

### Phase 2: Clarify routing (documentation, not code)

- **Goal:** Reduce command-selection confusion by documenting when to use which retrieval/verification skill.
- **Blocking prerequisite:** Phase 0 audit shows which skills are actually consumed.
- **Bounded change:** Update AGENTS.md routing tables to cover all active retrieval and verification skills with clear "use X when Y" rules.
- **Acceptance evidence:** Operator reports fewer command-selection errors over the next 5 sessions.
- **Failure/abandonment criterion:** If documentation doesn't reduce errors, the problem is command count, not documentation — proceed to Phase 3.
- **Out of scope:** Renaming commands, merging skills.

### Phase 3: Extend `/why` persistence (the plan's Phase 3, narrowed)

- **Goal:** Preserve investigation reasoning across compaction/session boundaries.
- **Blocking prerequisite:** Phase 0 audit confirms that investigations are actually lost at compaction (check whether `/why` Step 15 wiki write or Step 14 handoff routing already covers this).
- **Bounded change:** Add an optional `--persist` flag to `/why` that writes structured output to `P:/docs/investigations/`. Add investigation-file search to `/why` Step 0.5.
- **Acceptance evidence:** A future `/why` invocation finds and uses a prior investigation file. Operator confirms it saved re-derivation effort.
- **Failure/abandonment criterion:** If the investigation files are never read by future sessions, the persistence adds clutter without value. Remove the flag.
- **Out of scope:** New artifact types, graph runtimes, KB infrastructure.

### Phase 4: Pilot retrieval improvement (the plan's Phase 4, redefined)

- **Goal:** If Phase 0 audit shows agents reread entire files, test whether better retrieval tooling reduces token waste.
- **Blocking prerequisite:** Phase 0 audit shows measurable token waste from untargeted retrieval.
- **Bounded change:** Pilot one retrieval improvement on one bounded corpus. Candidates: (a) `context7` MCP for library docs, (b) semantic search over wiki concepts, (c) persistent cross-package code graph extending `code_analysis.py`, (d) rehydrate or replace orphaned `session_search.sqlite`.
- **Acceptance evidence:** Measured reduction in tokens consumed for the same retrieval task vs grep + read_file baseline.
- **Failure/abandonment criterion:** If the pilot shows no improvement over grep + read_file, abandon the backend. Do not expose `/kb`.
- **Out of scope:** Exposing `/kb` as a user command, building cross-layer routing, building promotion pipelines.

### Phase 5+: Deferred

- **Goal:** Only proceed if Phase 4 shows value.
- **Blocking prerequisite:** Phase 4 pilot success.
- Everything else in the plan (expose `/kb`, add promotion/ingestion, cross-layer routing) remains deferred until evidence justifies it.

---

## I. Minimum justified next step

**Run the Phase 0 audit.**

This is the single most valuable next step because every subsequent decision depends on its findings. The audit answers: which of the 657 skills are actually consumed? Which commands cause selection errors? Do agents reread entire files, or do they already use targeted retrieval? Are investigations actually lost at compaction, or do `/why` Step 15 and `/handoff` already preserve them?

Without this evidence, any implementation decision (rename commands, build KB, create investigation artifacts) is guessing. The plan itself prescribes this as Phase 1 — the correct call.

The audit should produce:
1. A consumed-skills report (which of the 120 Grok-active skills appear in session transcripts as invoked commands)
2. A retrieval-behavior report (how many tokens per session are spent on file reads vs grep vs wiki queries)
3. A command-selection-error report (scan transcripts for operator corrections about skill routing)
4. An investigation-persistence report (how many `/why` runs wrote to wiki or handoff vs were lost)

---

## J. Final implementation contract

```
TASK: Audit the current system state to produce evidence for redesign decisions.

SCOPE: Read-only investigation. Do NOT modify any files, commands, skills, or configurations.

DELIVERABLE: A single report at P:/docs/audits/system-redesign-audit-<date>.md with four sections:

1. CONSUMED SKILLS INVENTORY
   - Scan the last 30 sessions at ~/.grok/sessions/ for skill invocations
     (grep for patterns like "/<skill-name>", "skill:", "SKILL.md" references)
   - For each of the 120 Grok-active skills in skill-catalog.md:
     mark CONSUMED (found in >=1 session), DORMANT (on disk, 0 invocations), or ALIAS (redirects only)
   - List the top 20 most-invoked skills by frequency

2. RETRIEVAL BEHAVIOR MEASUREMENT
   - Sample 10 sessions from the last 30
   - For each: count read_file calls, grep calls, wiki query calls, web search calls
   - Estimate token cost of full-file reads vs targeted grep (file size x read count)
   - Report: what fraction of retrieval is targeted vs wholesale?

3. COMMAND-SELECTION ERROR SCAN
   - Scan transcripts for operator corrections about routing:
     "use /X not /Y", "why did you use", "should have used", "wrong skill"
   - List each incident with the skill pair involved

4. INVESTIGATION PERSISTENCE AUDIT
   - Count /why invocations in the last 30 sessions
   - For each: did Step 15 (wiki write) fire? Did Step 14 (handoff) fire?
   - Report: what fraction of investigations were preserved vs lost?

CONSTRAINTS:
- Do NOT modify any files
- Do NOT propose changes -- only report findings
- Use UNKNOWN when data is insufficient
- Cite specific session IDs and file paths as evidence

ACCEPTANCE CRITERIA:
- All four sections present with data
- At least 30 sessions scanned for section 1
- At least 10 sessions sampled for section 2
- Every claim cites a session ID or file path
```

---

## Summary verdict table

| Workstream | Verdict |
|---|---|
| 1. Command-surface simplification | `SIMPLIFY_EXISTING` |
| 2. Typed investigation state | `EXTEND_EXISTING` |
| 3. Durable KB infrastructure | `BLOCKED_PENDING_EVIDENCE` |
| 4. Unified routing across retrieval and KB layers | `CLARIFY_EXISTING` |
| 5. External-model advisory integration | `NO_CHANGE` |
| **Overall** | **`PLAN_COHERENT_WITH_REVISIONS`** |

---

## Evidence base and provenance

This review was produced with evidence from four parallel discovery subagents plus direct repository inspection:

1. **Skill catalog agent** (29 tool calls): counted 657 skills across 21 scopes, identified 9+ deprecated entries, 5+ aliases, and functional overlap groups across search, review, planning, session management, and external models. Source: `P:/.data/wiki/concepts/skill-catalog.md` (regenerated 2026-08-01).

2. **Investigation artifacts agent** (24 tool calls): inspected handoff system (150+ files, 16 mandatory fields), `/why` (670-line SKILL.md with evidence tiers, hypothesis diversification, Toulmin falsifier, feedback-to-wiki), `/aar` (typed episode ledger, layered root-cause, value accounting), `/harvest` (event-sourced obligation tracking, 81 tests), `/tp` (critique log), `plan-writer` (TDD task format). Confirmed: 12 of 14 proposed InvestigationState fields already exist in `/why` protocol; gap is persistence only.

3. **KB infrastructure agent** (26 tool calls): confirmed wiki vault (810 concepts, 681-line SCHEMA.md, FTS5 search, auto-link, contradiction scanner, log protocol), promotion pipeline (NotebookLM → wiki-yt → validate → auto-link → contradiction-scan → log → /dream → AGENTS.md), `/harvest` storage (event-sourced, claim-based concurrency), `/dream` (cross-session consolidation, 90-day horizon). Confirmed gaps: no persistent code-structure graph; orphaned `session_search.sqlite`.

4. **Model routing agent** (17 tool calls): confirmed `/go` delegates model selection to subagent dispatch (not user-facing), two-lane model pool (reasoning: glm-5-2; code: or-ling/nim/zen/minimax fallback chain), ADR-009 fully implemented with fail-open contract, `/close` as single completion gate with two-layer enforcement (file receipt + Stop hook), hook system mid-migration (PreToolUse.py CRITICAL_HOOKS=empty, cc-aca plugins disabled in config.toml), config.toml shows 29 plugins disabled / 9 enabled.

**Limitations:** The three later agents initially returned "not found" due to a task-ID format mismatch. Their results were retrieved using corrected IDs. All findings are `PROVEN` (verified by tool output with file citations) unless explicitly labeled `[INFERENCE]` or `[UNKNOWN]` in the text.
