---
thread_id: 019f9f4f-design-bloat-assessment-20260726
parent_handoff_path: P:/docs/handoffs/session-019f9f4f-shipped-work-20260726/HANDOFF.md
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-26T19:40:00Z
status: CLOSED
superseded_by: P:/docs/handoffs/design-skill-improvement-program-20260802/HANDOFF.md
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: /design (1015 lines) bloat assessment

## Objective

Apply the same introspection method used on /www to `~/.grok/skills/design/SKILL.md` (1015 lines, flagged twice in session 019f9f4f as the worse instance of the same second-system-effect pattern), decide whether to pare, and if so produce the keep/pare list with cross-model review.

## Status

OPEN — ready for a fresh session. The session that identified this work (019f9f4f) is ending; this handoff preserves the context.

## Producing context

- Identifying session: `019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9`
- Twice flagged in /tp sessions: once in the original /www self-assessment concept (`research-vs-design-vs-architect-skills-and-www-self-assessment`), once in the second /tp's LATER section
- /design is load-bearing (used for every architecture decision); the assessment cannot be rushed

## Read-first list

1. `P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md` — the method, the research base (MindStudio inverted-U, Brooks second-system effect, Anthropic "smallest set of high-signal tokens," arxiv input-length-degrades-performance), and the /www keep/pare result that informs the threshold
2. `~/.grok/skills/design/SKILL.md` — the target (1015 lines)
3. `~/.grok/skills/www/SKILL.md` — the post-pare reference (450 lines); the contrast is the structural argument
4. `~/.grok/AGENTS.md` § "Optimal long-term solution (not minimal fix)" — including the anti-"smallest viable" framing added this session; the assessment must apply this rule (don't pare for paring's sake; pare only where ceremony > value)

## Verified facts

- [FACT] `~/.grok/skills/design/SKILL.md` is 1015 lines as of 2026-07-26 (receipt: `Get-Content $design.FullName).Count` measured during session 019f9f4f, output shown in /www self-assessment research)
- [FACT] /www (585 lines) was assessed as past the MindStudio inverted-U inflection and pared to 450 lines (receipt: commit `51d269c`)
- [FACT] /design at 1015 lines is ~2.2× /www's pre-pare size and ~2.25× /www's post-pare size
- [FACT] The research base for second-system effect and skill bloat is documented in `research-vs-design-vs-architect-skills-and-www-self-assessment` with 5+ source citations

## Current state

/design has not been introspected. Unknown:
- Enhancement-batch count
- Mandatory-rule count
- Section word counts (where's the bulk?)
- Which sections are structural (produce findings/decisions) vs ceremonial (rarely fire)

The /www assessment measured these and produced a keep/pare list. The /design assessment should produce the same shape of output.

## Task packets

### DBA-01: Introspect /design

- **goal:** produce the measured metrics for /design that /www self-assessment produced for /www
- **in scope:** line count, section-word-count breakdown, enhancement-batch count (from provenance section), mandatory-rule count, copyable-checklist length
- **out of scope:** the keep/pare recommendation (that's DBA-02, after data is in)
- **files / anchors:** `~/.grok/skills/design/SKILL.md`
- **acceptance:** the metrics table appears in the assessment concept (DBA-02 output)
- **falsifier:** metrics show /design is structurally tight (every section is load-bearing) → assessment documents why size is justified, no pare recommended
- **verification level required:** STATIC_INSPECTION
- **estimate:** ~15 min

### DBA-02: Produce assessment concept with keep/pare recommendation

- **goal:** wiki concept `design-skill-bloat-assessment` with measured metrics + keep/pare list + honest trade-offs + falsifier
- **in scope:** apply the /www self-assessment template to /design; recommend keep/pare per section
- **out of scope:** implementing any pare (separate handoff after assessment is reviewed)
- **files / anchors:** new concept in `P:/.data/wiki/concepts/` named `design-skill-bloat-assessment`
- **acceptance:** concept passes `validate_wiki_entry.py`; cross-model review (glm-5-2 or codex) if recommendation is to pare; concept includes decision-context section explaining why this assessment was needed
- **falsifier:** assessment recommends pare but review rejects ≥1 keep/pare call → revise before any implementation
- **verification level required:** STATIC_INSPECTION + cross-model review (per `/why` Step 15b pattern)
- **estimate:** ~30 min (write + review)

### DBA-03 (conditional): Pare implementation

- **goal:** apply the pare per DBA-02's reviewed recommendation
- **status:** BLOCKED on DBA-02
- **in scope:** single-file edit to `~/.grok/skills/design/SKILL.md`
- **acceptance:** all /design tests pass; structural sections preserved per the assessment
- **verification level required:** LIVE_BEHAVIOR (run /design on a small task post-pare)

## Open decisions

### Decision 1: Should DBA-02 also assess /tp and /aar?

- **question:** /tp was rewritten recently with the 4D matrix; /aar grew from Phase 4 + Phase 8.5 additions this session. Should the assessment cover all three, or stay narrow on /design?
- **options:**
  - (A) Narrow: /design only (worst instance at 1015 lines)
  - (B) Broad: /design + /tp + /aar (recently grew)
- **selection criterion:** sufficient evidence to decide on the fleet-wide rule (OA-03 in the session handoff)
- **currently leads:** (A) — /design is the worst instance; if it doesn't warrant pare, the others likely don't either. If it does, expand to (B).
- **what would change this:** if /design assessment shows the pattern is subtle (some large sections are structural), then broader evidence helps calibrate the threshold

## Hard constraints

1. **/design is load-bearing.** Used for every architecture decision. Pare must preserve the writer/reviewer/revise loop and the preflight gate.
2. **Anti-"smallest viable" rule applies.** Don't pare for paring's sake. The assessment must justify each cut with evidence the section is ceremonial, not structural.
3. **No hook or dispatch changes.** /design is a model-orchestrated skill, not a hook; changes don't touch runtime infrastructure.

## Cross-reference couplings

- `P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment` → provides the method; if the method is wrong, this assessment inherits the flaw
- `~/.grok/AGENTS.md` § "Optimal long-term solution" → anti-"smallest viable" framing informs the keep/pare bar
- This handoff's `accurate_as_of_head` → `ea0a48be` (P:\). /design lives in ~/.grok (separate repo); the P:\ HEAD is for the wiki concepts cited.

## Other outstanding streams (not handed off)

- **OA-03 (fleet-wide enhancement-offsetting-retirement rule)** — depends on this assessment + the /www result. Separate handoff exists (`enhancement-offsetting-retirement-rule-20260726`).

## Explicit non-goals

1. **Do not pare /design within this assessment.** DBA-02 produces the recommendation; DBA-03 (separate handoff, blocked) implements.
2. **Do not re-assess /www.** Already done this session.
3. **Do not assess /tp or /aar unless Decision 1 resolves to (B).**

## Resumption protocol

1. Read this handoff + `research-vs-design-vs-architect-skills-and-www-self-assessment` wiki concept
2. Execute DBA-01 (introspection) — `Get-Content $design.FullName).Count`, section breakdown via `(Select-String -Pattern "^## ").Line`, enhancement-batch count via provenance grep
3. Execute DBA-02 (assessment concept) using the /www self-assessment as template
4. If recommendation is to pare: invoke cross-model review (glm-5-2 preferred per /why Step 15b)
5. Resolve Decision 1 before finalizing — narrow vs broad scope
6. Commit the assessment concept to P:\

## Suggested next invocation

```
Continue work from session 019f9f4f. Read P:/docs/handoffs/design-bloat-assessment-20260726/HANDOFF.md.

Execute DBA-01 + DBA-02: introspect ~/.grok/skills/design/SKILL.md using the
method from [[research-vs-design-vs-architect-skills-and-www-self-assessment]],
produce the design-skill-bloat-assessment concept with keep/pare recommendation.

If recommending pare, run cross-model review (glm-5-2 via spawn_subagent) per
/why Step 15b pattern. Resolve Decision 1 (narrow vs broad scope) before
finalizing.
```

## Last user message (verbatim)

> "do the recommended action   make sure the deferred items have hand-off files."

## Epistemic labels

- All "Verified facts" are `[FACT]` with receipts cited inline.
- "Load-bearing" characterization of /design is `[INFERENCE]` — based on the skill being named in AGENTS.md routing for architecture work, not on direct invocation observation this session.
- Decision 1 "currently leads (A)" is `[INFERENCE]` — operator has not stated a preference; (A) is the cautious default.
- Estimates are `[INFERENCE]` based on /www assessment's actual duration (~45 min total).
