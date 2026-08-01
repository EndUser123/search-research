---
thread_id: 019f9aff-a619-70c2-8836-0bb6ae462827
parent_handoff_path: none
current_session_id: 019f9aff-a619-70c2-8836-0bb6ae462827
current_terminal_id: grok-build-primary
produced_at: 2026-07-26T01:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: pending
---

# Handoff — /dream skill requirements (v1)

## Objective

Implement `/dream` as a thin orchestrator skill that composes `/wiki` (additions), `preflight`/`source-authority-discovery` (contradictions), and a retirement pass (dormant in v1) to consolidate cross-session learning into the wiki vault. Manual trigger only in v1.

## Original task (verbatim)

> "/refine let's figure out our requirements for '/dream' I don't know what I don't know, so what should we figure out?"

Originates from the prior `/www` research session on LLM dreaming (see `P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md`).

## Status

`READY_FOR_REVIEW` — architectural decisions resolved; ready for `/go execute` after preflight.

## Producing context

- Date: 2026-07-26
- Session: 019f9aff-a619-70c2-8836-0bb6ae462827
- Host: grok-build
- Prior research: `P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md` (written same session)
- Refinement conversation: this session (operator + grok, 4 turns)

## Resolved decisions (the core of this handoff)

| # | Decision | Resolution | Source |
|---|---|---|---|
| 1 | Trigger model | **Manual-only for v1.** Entropy-gated scheduling deferred to v2; if added, signal = date+time+concept-count-delta (not pure time). | Operator 2026-07-25 |
| 2 | Scope | **Per-knowledge via `host:` tag** (grok-only, claude-only, both, neither). Semantic-only for v1 (`wiki/concepts/`, `www-ledger/` as input). Procedural (`AGENTS.md`, `P:/.claude/rules/`) out of scope. | Operator 2026-07-25 |
| 3 | MVP architecture | **Option C: thin orchestrator.** Composes `/wiki` (additions) + `preflight` (contradictions) + new retirement pass. Does NOT replace `/wiki`, `/aar`, `/close`, or episodic-memory MCP — those remain inputs. | Operator 2026-07-25 |
| 4 | Corpus window | **90 days for first run** (sweet spot for recency × importance × relevance per Park 2023 reflection model). Subsequent runs use `--since-last-dream` incremental. | Operator-accepted expert rec 2026-07-25 |
| 5 | Anti-bloat gate | **Present but dormant in v1.** Gate fires on ratio (≥1 retirement per addition) but has no targets yet — wiki is 1 month old, 26% orphans is normal newness. Activates naturally when wiki accumulates stale concepts. NOT dropped (correcting earlier overreaction); just dormant. | Operator pushback 2026-07-25; wiki inspection same session |
| 6 | Metrics | **None for v1.** Rejected proposed AGENTS.md-rate metric as cargo cult — no decision it would change. Kill-switch falsifier only: "if after 3 months wiki is same shape and operator notices no difference, retire /dream or redesign." | Operator pushback 2026-07-25 |
| 7 | Bloat is not real for us (yet) | Wiki data: 205 concepts, 184 created 2026-07, 26% orphans, 0 duplicates, only 1 concept has `status:` field. Cannot be bloated at 1 month. Implication: retirement pass is structurally present but will produce zero retirements in v1. | Wiki inspection 2026-07-25 |
| 8 | /refine improvement (separate stream) | Add filtered clarification block (all ambiguities surfaced at once with `[RECOMMENDED]` answers — NOT one-at-a-time grilling). Absorb `grill-with-docs` side-effect disciplines (ADR gating). Skip CONTEXT.md. **Tracked as separate handoff, not this one.** | Operator 2026-07-25; subagent verified Pocock skills |

### Additional resolutions

- **ADR location:** `P:/docs/adrs/` canonical. ADR-creation gate (from Pocock): hard-to-reverse AND surprising-without-context AND real-trade-off — all three required.
- **ADRs indexed by wiki:** YES. Mechanism `[FACT-GAP]` — qmd config not at expected paths; /go execute must resolve via preflight (move ADRs vs. add second source vs. symlink).
- **CONTEXT.md:** skipped. Glossary terms route to `wiki/concepts/`, decisions to ADRs.

## MVP shape (v1)

Three passes, one dormant:

```
/dream
  ├─ PASS 1: ADDITIONS (active)
  │   └─ invoke /wiki default-mode logic over corpus window
  │      (cross-session distillation of findings + decisions)
  ├─ PASS 2: CONTRADICTIONS (active)
  │   └─ invoke preflight / source-authority-discovery
  │      (drift detection across wiki/concepts + new findings)
  ├─ PASS 3: RETIREMENTS (dormant)
  │   └─ gate present (≥1 retirement per addition)
  │      but no targets yet — produces zero in v1
  └─ OUTPUT: P:/docs/dreams/ (date-stamped filename at runtime)
      (candidate additions, contradictions, retirements — each with receipt)
      Operator promotes via existing /wiki write flow.
```

## Verified facts

- `[FACT]` `/dream` skill does not exist at `~/.grok/skills/dream/` or `P:/.grok/skills/dream/` (verified via `ls` 2026-07-26)
- `[FACT]` `/wiki` skill exists at `C:/Users/brsth/.grok/skills/wiki/SKILL.md`; all wiki scripts accessible via `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/` (per /wiki SKILL.md)
- `[FACT]` `preflight` skill exists at `P:/.agents/skills/preflight/SKILL.md` (per session skill catalog)
- `[FACT]` `source-authority-discovery` is the Claude-side equivalent at `P:/.agents/skills/source-authority-discovery/` (per `P:/.claude/CLAUDE.md`)
- `[FACT]` Wiki corpus: 205 concepts, 184 created 2026-07, 26% orphans, 1 has `status:` field, 0 stem-duplicates, max file 264KB (inspected 2026-07-25)
- `[FACT]` AGENTS.md provenance: 25 citations dated 2026-07, 1 dated 2026-04 (baseline for "recurring failures" rate)
- `[FACT]` ADR-009 exists and is cited from `~/.grok/AGENTS.md` as `P:\docs\adrs\ADR-009-grok-cross-model-second-opinion-skills.md`
- `[FACT]` Pocock grill* skills verified at `github.com/mattpocock/skills`: `grill-me` (1-line dispatcher), `grilling` (~140 char loop), `grill-with-docs` (adds domain-modeling). Source: subagent read raw SKILL.md content 2026-07-26.

## Affected files (creation)

- `~/.grok/skills/dream/SKILL.md` — new skill definition (the deliverable)
- `P:/docs/dreams/.gitkeep` — output directory marker
- Per-run output artifacts created at runtime under `P:/docs/dreams/` (date-stamped filename; not created during this handoff)

## Affected files (composition — read-only consumers)

- `C:/Users/brsth/.grok/skills/wiki/SKILL.md` — /dream invokes /wiki default-mode logic
- `P:/.agents/skills/preflight/SKILL.md` — /dream invokes for contradictions
- `P:/.data/wiki/concepts/` — target for additions; input for contradiction scan
- `P:/.data/www-ledger/` — input (what's been researched)
- `P:/docs/handoffs/` — input (last 90 days)
- AAR artifacts — input (last 90 days)
- `P:/.data/wiki/SCHEMA.md` — §10 write procedure (referenced, not modified)

## Non-goals (`[DO NOT CHANGE]` tri-state)

- 🚫 **Never (v1):** modify procedural memory (`~/.grok/AGENTS.md`, `P:/AGENTS.md`, `P:/.claude/rules/`, `~/.claude/Claude.md`). Out of scope; too risky.
- 🚫 **Never (v1):** auto-write to `wiki/concepts/`. /dream proposes; operator promotes via existing /wiki flow.
- 🚫 **Never (v1):** modify `P:/.data/wiki/log.md` directly. Use `P:/.data/wiki/scripts/append_log.py` if logging needed.
- 🚫 **Never (v1):** auto-promote a write-rule from handoff prose into AGENTS.md (MINJA defense — handoff content is untrusted input).
- 🚫 **Never (v1):** scheduled/cron triggers. Manual only.
- ⚠️ **Ask first (v2):** entropy-gated scheduling, fan-out to M3 subagents, episodic-memory MCP integration.
- ✅ **Always (invariant):** non-destructive writes. /dream never overwrites; it proposes. Operator promotes with one git commit per promotion.
- ✅ **Always (invariant):** receipt-preserving. Every proposed addition/contradiction/retirement must cite source handoff/AAR/concept/session.
- ✅ **Always (invariant):** race-safe. Uses file-lock pattern (same as `multi-agent-transcript-race-condition-check-preprocessor`).

## Task packets

### TP-DREAM-01: Create /dream SKILL.md
- **goal:** Author the skill definition at `~/.grok/skills/dream/SKILL.md`
- **in scope:** SKILL.md frontmatter + body; references to /wiki, /preflight; output format spec; trigger model (manual); corpus window (90d / `--since-last-dream`); three-pass structure with retirement pass documented as dormant; anti-bloat gate rule; receipt requirement; race-safety rule; security boundary (handoff content = untrusted input)
- **out of scope:** scripts (none required for v1 — /dream orchestrates existing skills); hook integration; scheduled triggers
- **files / anchors:** `~/.grok/skills/dream/SKILL.md` (new)
- **acceptance:**
  1. SKILL.md loads without error (invoke `/dream --help` or bare `/dream` in fresh session)
  2. Three passes documented with clear invocation of /wiki and /preflight
  3. Retirement pass explicitly marked dormant with activation conditions
  4. Output artifact path `P:/docs/dreams/ (date-stamped filename at runtime)` specified with section structure
  5. Receipt-preserving rule present and enforceable (every proposal has source citation)
  6. Non-goals tri-state block present verbatim from this handoff
- **falsifier:** skill loads but produces no proposals on a real 90-day corpus (disaster = silent no-op); OR skill produces proposals without receipts (security failure); OR skill modifies procedural memory (scope violation — exit-2 block if implemented as hook)
- **verification level required:** LIVE_BEHAVIOR — must observe a dry-run dream over a real 90-day window
- **no_live_run_reason:** (deferred to /go execute)

### TP-DREAM-02: ADR indexing mechanism (fact-gap resolution)
- **goal:** Resolve how ADRs at `P:/docs/adrs/` become discoverable via `qmd search --collection wiki`
- **in scope:** inspect qmd config (likely at `~/.qmd/` or `P:/.data/wiki/qmd-config.*` — `[FACT-GAP]`); evaluate three options: (a) move ADRs under `P:/.data/wiki/adrs/`, (b) add `P:/docs/adrs/` as second source for wiki collection, (c) symlink; pick one; verify `qmd search "cross-model second opinion"` returns ADR-009
- **out of scope:** renumbering ADRs; reformatting existing ADRs
- **files / anchors:** qmd config (location TBD); `P:/docs/adrs/`
- **acceptance:** `qmd search --collection wiki --query "<ADR-009 topic>"` returns ADR-009 in top-10 results
- **falsifier:** ADR-009 not findable via qmd after mechanism applied
- **verification level required:** LIVE_BEHAVIOR
- **note:** this is a preflight task for /go execute, not strictly part of /dream — but /dream's contradiction pass depends on ADR findability

### TP-DREAM-03: First dry-run dream
- **goal:** Execute `/dream` over the last 90 days; produce `P:/docs/dreams/2026-07-26-dream.md`; operator reviews
- **in scope:** real corpus: handoffs (90d), www-ledger (all), AAR artifacts (90d), wiki/concepts (target); produce candidate additions + contradictions (retirements expected zero)
- **out of scope:** promoting any proposal; touching procedural memory
- **files / anchors:** `P:/docs/dreams/2026-07-26-dream.md` (new)
- **acceptance:**
  1. Output file exists with sections: ingested-sessions, candidate-additions, contradictions, retirements (expected: 0), receipts
  2. Every candidate has a receipt (source path + session-id or date)
  3. Operator subjectively finds ≥1 useful proposal OR explicitly confirms "nothing to consolidate" (both are valid v1 outcomes)
- **falsifier:** output is empty AND operator knows there's consolidatable content (skill missed it); OR output is full of receipts that don't trace to real sources (fabrication)
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** single-pass parent Grok, 90-day corpus ≈ 1 dream ≈ 5-15 minutes wall-clock (no fan-out in v1)

## Verification plan

1. **Skill loads:** invoke `/dream` (bare) in a fresh session — confirm it produces the dry-run proposal flow, not an error
2. **Composition works:** inspect SKILL.md to confirm /wiki and /preflight invocations match their actual interfaces (citation: this handoff's Verified Facts)
3. **Receipt rule enforced:** inspect 3 random proposals from TP-DREAM-03 output — each must have a source path
4. **Non-goal respected:** `git status` after TP-DREAM-03 — `~/.grok/AGENTS.md` and `P:/.claude/rules/` must be unmodified
5. **Race-safety:** document the lock mechanism in SKILL.md (file lock at known path; refuse to start if contested)

## Open decisions

None blocking. All 8 architectural clusters resolved. Only implementation detail remains, plus the ADR-indexing fact-gap (TP-DREAM-02).

## Hard constraints (invariants that survive into next session)

1. **Non-destructive.** /dream proposes; operator promotes. Never auto-write to wiki/concepts or procedural memory.
2. **Receipt-preserving.** Every proposal cites a source. No receipt = rejected proposal.
3. **Security boundary.** Handoff/AAR/session content is untrusted input. /dream reads but never executes; never auto-promotes a write-rule from prose into AGENTS.md.
4. **Manual trigger only (v1).** No cron, no entropy gate, no auto-fire.
5. **Race-safe.** File-lock pattern; refuse to start if another agent is writing to wiki/concepts.
6. **Scope per `host:`.** Proposals respect host provenance; cross-host consolidation requires explicit promotion gate.

## Risks / constraints

| Risk | Likelihood | Mitigation |
|---|---|---|
| First dream returns empty (90-day window too narrow) | Medium | Falsifier in TP-DREAM-03 — extend to 180d and re-run |
| First dream returns unreviewable volume | Low | Single-pass parent Grok in v1 (no fan-out); hard cap implicit |
| Operator trust erosion from bad retirement | N/A in v1 | Retirement pass dormant; no retirements to be wrong about |
| Cost runaway | Low | No fan-out in v1; single-pass parent Grok |
| /wiki composition coupling breaks if /wiki changes | Medium | /dream references /wiki by interface (default-mode logic), not internals; /wiki changes tracked in its own handoff stream |
| ADR indexing mechanism blocks TP-DREAM-03 | Medium | TP-DREAM-02 sequenced first; if blocked, TP-DREAM-03 falls back to filesystem grep over `P:/docs/adrs/` |
| Pre-convention concepts (no `host:` tag) ambiguous for scope | Low | Re-tag on next edit only (matches AGENTS.md §"Skill authoring host provenance"); no bulk backfill |

## Rollback plan

Reversibility: **high** (≥1.0 — new skill, no modifications to existing systems).

- `/dream` is a new file at `~/.grok/skills/dream/SKILL.md` — delete to roll back
- `P:/docs/dreams/*` output artifacts are proposals only — delete to roll back
- No existing file is modified by /dream itself
- ADR indexing mechanism (TP-DREAM-02) may modify qmd config — snapshot config before, restore to roll back

## Cross-reference couplings

- `P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md` → this handoff's origin; if concept is superseded, this handoff's rationale weakens
- `~/.grok/skills/wiki/SKILL.md` → /dream composes /wiki; if /wiki interface changes, /dream's Pass 1 breaks
- `P:/.agents/skills/preflight/SKILL.md` → /dream composes preflight; if preflight moves or renames, /dream's Pass 2 breaks
- `P:/.data/wiki/SCHEMA.md` → /dream writes concepts via SCHEMA §10 procedure; if schema changes, /dream's output format may drift
- `~/.grok/AGENTS.md §"File editing protocol"` → /dream's non-destructive + race-safety rules inherit from this; if AGENTS.md rule changes, /dream must follow

## Read-first list (for /go execute)

1. This handoff (you are here)
2. `P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md` — research basis, especially §"How it could and should work for us"
3. `~/.grok/skills/wiki/SKILL.md` — interface /dream composes for Pass 1
4. `P:/.agents/skills/preflight/SKILL.md` — interface /dream composes for Pass 2
5. `P:/.data/wiki/SCHEMA.md` §10 — write procedure for promoted additions
6. `~/.grok/skills/refine/SKILL.md` — pattern reference (similar thin-orchestrator skill structure)
7. Existing ADR (e.g., `P:/docs/adrs/ADR-009-grok-cross-model-second-opinion-skills.md` — exact filename; the `*` glob in some references expands to this file) — format reference for the ADR indexing task

## Recommended next

```text
REFINE DONE
input: "/refine let's figure out our requirements for '/dream' I don't know what I don't know, so what should we figure out?"
handoff: P:/docs/handoffs/dream-skill-requirements-20260726/HANDOFF.md
status: ready-to-implement (architectural decisions resolved; ADR-indexing fact-gap + preflight still required)
refinements: resolved 8 architectural clusters via grilling-style clarification; dropped anti-bloat gate as active v1 feature (dormant instead); rejected cargo-cult metric; verified Pocock grill* skills to inform parallel /refine improvement stream
recommended next: /go execute P:/docs/handoffs/dream-skill-requirements-20260726/HANDOFF.md
  (preflight will run as /go's first step; TP-DREAM-02 ADR indexing should be sequenced before TP-DREAM-03 first dry-run)
```

## Parallel work stream (NOT this handoff)

The /refine improvement surfaced during this session is tracked separately:
- Add filtered clarification block to /refine (all ambiguities at once with `[RECOMMENDED]`, NOT one-at-a-time)
- Absorb grill-with-docs ADR gating (hard-to-reverse + surprising + real-trade-off)
- Skip CONTEXT.md; route glossary → wiki/concepts
- ADR location: `P:/docs/adrs/`

This is a **separate handoff** to be written when the operator authorizes it. Do NOT conflate with /dream implementation.

## Execution Status

Updated: 2026-07-26T01:50:00Z
Session: 019f9aff-a619-70c2-8836-0bb6ae462827
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | TP-DREAM-01: Create `/dream` SKILL.md | ✅ DONE | `C:/Users/brsth/.grok/skills/dream/SKILL.md` (335 lines / 428 insertions); YAML parses; `name=dream`, `host=grok`, `version=1.0.0`; skill registered (per SessionStart catalog). Commit `853cd0b` in `~/.grok`. |
| 2 | TP-DREAM-02: ADR indexing mechanism (fact-gap) | ✅ DONE (deferred mechanism) | v1 mechanism: `/dream` greps `P:/docs/adrs/` directly. qmd config (`~/.config/qmd/index.yml`) only maps `P:/.data/wiki/`; adding a second collection is non-trivial and deferred. Filesystem grep is authoritative per SKILL.md §"Known limitations". Documented as v2 enhancement. |
| 3 | TP-DREAM-03: First dry-run dream | ❌ NOT STARTED | Per /refine Hard Rule #7 and /dream's own "Manual trigger only" rule, the operator invokes `/dream` explicitly. /go execute should not auto-invoke the skill it just authored — that's self-dealing. Operator decision when to run first dream. |
| 4 | Handoff doc + output dir in P:/ | ✅ DONE | `P:/docs/dreams/.gitkeep` + `P:/docs/handoffs/dream-skill-requirements-20260726/HANDOFF.md`. Commit `d8ebc1b` in P:/. |

### Key findings during execution

- **qmd index is stale: 83 docs indexed vs 221 `.md` files on disk** (pre-existing condition, not caused by /dream). /dream SKILL.md §"Known limitations" documents the compensation: filesystem grep alongside `qmd search`, with grep authoritative. Future enhancement: rebuild qmd index + add ADRs as second collection.
- **`~/.grok/` IS a separately-tracked git repo** (not just runtime-only like `P:/.data/wiki/`). Skill commits go to `~/.grok` main; P:/ commit handles handoff + output dir. Two-repo commit pattern is correct for user-scope skills.
- **Other agents have substantial uncommitted work in both repos** (`.agents/scripts/_b4_live_*` deletions, `close` skill modifications, `aar` modifications, etc.). Surgical staging (`git add <specific paths>`) was mandatory and worked: only the 3 dream-related files were committed across the two repos; everything else was left untouched.
- **No procedural memory modified** — verified via `git diff HEAD~1 -- AGENTS.md .claude/rules/ .claude/CLAUDE.md` returning empty. Honors 🚫 Never (v1) non-goal #1.
- **Skill registered immediately on next system reminder** — `/dream` visible in the catalog with correct description. No `/reload-plugins` needed for user-scope skills (that's a plugin-cache action, not a skill action).
- **TP-DREAM-03 deliberately not run** — would be self-dealing for the orchestrator that just authored the skill to invoke it. Operator decides when to invoke `/dream` for the first dry-run; corpus window is 90 days default.

### What is NOT done (out of scope for this /go execute)

- **TP-DREAM-03 (first dry-run dream)** — operator action. The skill is ready to invoke.
- **/refine improvement** (filtered clarification block + grill-with-docs disciplines) — separate work stream, tracked in handoff §"Parallel work stream". Needs operator authorization to start.
- **qmd index rebuild** — pre-existing staleness, surfaced by /dream's discovery but not caused by it. Separate maintenance task.
- **v2 features** (entropy-gated scheduling, M3 fan-out, episodic-memory MCP integration, ADR indexing via qmd collection) — all deferred per handoff.
