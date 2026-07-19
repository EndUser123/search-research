# Stream 4: Prompt + schema enhancements handoff

| Field | Value |
|---|---|
| **Stream** | Text-level edits across /tp, /review or /red-team, wiki SCHEMA.md |
| **Priority** | LOWER — all text edits, no code, no plugin mutation (except red-team agents) |
| **Status** | Not started; all designs complete |
| **Effort** | ~1 hour (single subagent, batched edits) |
| **Delegation** | One subagent (`capability_mode: read-write`); benefits from Stream 3's research |

## Goal

Five prompt/schema enhancements that improve quality of existing skills without code changes. All are text edits to SKILL.md files or agent prompts.

## Background

From the session's research and critical review:
- `/tp` lacks a disconfirmation-search step (the user identified this gap)
- `/review` and `/red-team` lack Simplification and Test Quality lenses (HAMY's 9-agent pattern has these; we don't)
- `/red-team` findings don't use `@contradicts` typed links for cross-specialist conflicts
- QMD reindex ritual is documented in SCHEMA.md §11 but lacks a quarterly cadence note
- Stream 3's ultrathinks research may surface additional patterns to port

## Deliverables

### 1. Disconfirmation search in /tp (~10 lines)

**File:** `C:/Users/brsth/.grok/skills/tp/SKILL.md` or `protocol.md`

**Change:** Add to the circuit breaker or as a post-correction step:

> After proposing a fix or recommendation, run a **disconfirmation search**: phrase a query that would REFUTE the hypothesis ("does this actually work?", "is this bug already fixed upstream?", "what evidence would prove this wrong?"). Use `minimax-search__web_search` (primary) or `web-search-prime__web_search_prime` with `search_recency_filter=oneMonth` (for version-sensitive questions). If disconfirmation evidence exists, surface it before the user acts on the recommendation.

**Context:** This session's biggest single improvement to /tp methodology. The user identified it; the research validated it (Popperian falsificationism; Karpathy reviewers emphasize "honesty about what you didn't find").

### 2. Simplification lens (~20 lines)

**File:** Either `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-logic.md` (extend existing logic specialist) or create `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-simplification.md` (new specialist).

**Change:** Port HAMY's Simplification & Maintainability Reviewer:

> Ask "could this be simpler?" Check for:
> - Premature abstractions (helpers used once, unnecessary indirection)
> - Over-configured solutions when simple would suffice
> - Framework-level solutions for one-off problems
> - Clever code that sacrifices clarity
> - Change atomicity: is this one logical unit? Are unrelated changes mixed in?

**Source:** `https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents` — Agent 9.

### 3. Test Quality lens (~20 lines)

**File:** Same location as #2 (either extend or new specialist).

**Change:** Port HAMY's Test Quality Reviewer:

> Evaluate test coverage ROI:
> - Are critical paths tested? (auth, payments, data integrity)
> - Do tests verify behavior, not implementation details?
> - Will tests break for the wrong reasons? (brittle selectors, testing internals)
> - Is coverage proportionate to risk? (not all code needs equal coverage)
> - Flakiness risk: timing dependencies, race conditions, order-sensitive assertions

**Source:** Same HAMY blog post — Agent 6.

### 4. @contradicts in /red-team findings schema (~5 lines)

**File:** `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` — findings schema section.

**Change:** Add to the findings JSON schema:

> When a finding contradicts another specialist's finding, add `"contradicts": "<FINDING-ID>"` to the finding object. The critic should surface these as contradiction resolutions (already handled by the tiebreaker, but the typed link makes the conflict machine-readable).

**Also:** Update the critic agent prompt to look for `contradicts` fields and prioritize resolving them.

### 5. QMD quarterly reindex note (~3 lines)

**File:** `P:/.data/wiki/SCHEMA.md` §11 (Recommended cadence).

**Change:** The quarterly bullet already exists but says "re-baseline the QMD relevance score." Add:

> Also run `qmd update` (not `qmd update --collection wiki` — that syntax is wrong; `update` takes positional or no args) to refresh the full index against any corpus growth since the last reindex.

**Note:** This fix depends on Stream 2's QMD syntax fix being applied first. If Stream 2 hasn't run, the syntax in this addition will be correct but the rest of SCHEMA.md §11 may still have the old wrong syntax.

## Dependencies

- Benefits from Stream 3 deliverable #1 (ultrathinks research) — may surface additional patterns to port. If Stream 3 hasn't returned, proceed without it and add later.
- Item 5 (QMD reindex note) depends on Stream 2's QMD syntax fix.

## Verification criteria

1. `/tp` SKILL.md or protocol.md has the disconfirmation-search paragraph
2. Red-team has either a new simplification specialist or extended logic specialist with simplification lens
3. Same for test quality lens
4. Red-team findings schema includes `contradicts` field
5. SCHEMA.md §11 quarterly note mentions `qmd update` (correct syntax)
6. Plugin cache rebuilt for any red-team plugin changes (`plugin-audit-and-fix.py --bump red-team`)

## Source references

- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — /tp skill to edit
- `P:/packages/.claude-marketplace/plugins/red-team/agents/` — specialist agent prompts
- `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` — findings schema
- `P:/.data/wiki/SCHEMA.md` §7 (typed wikilinks) and §11 (cadence)
- `https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents` — HAMY's 9-agent review pattern (source for lenses #2 and #3)
- Stream 3 handoff: `P:/docs/stream-3-research-infrastructure-handoff-2026-07-19.md` — ultrathinks research that may inform additional enhancements
