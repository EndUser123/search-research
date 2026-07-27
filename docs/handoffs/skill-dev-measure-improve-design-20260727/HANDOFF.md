---
thread_id: skill-dev-measure-improve-design-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T17:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 0481182 (P:) / 0d9a41b (~/.grok)
---

# /skill-dev design: measure-mode + improve-mode (not the 3-mode god-skill)

## Objective

Design and build `/skill-dev` as a **measure + improve** skill that closes the skill-optimization loop. The original 2026-07-22 plan proposed a 3-mode create/audit/improve skill; a /tp session (this session) + /www research (SLIM, CODESKILL, SkillRouter) narrowed it to measure + improve only. Create is covered by `/create-skill`; audit/retire by `/skill-prune`; design critique by `/tp`. The missing piece is **marginal-contribution measurement** (the SLIM-inspired dynamic lifecycle adapted to our non-RL context).

## The problem (one sentence)

We have 19 documented skill-optimization techniques in `[[skill-techniques-index]]` but no skill that reads them or applies them systematically — and no skill measures whether active skills are still providing marginal value.

## What this session established (verified)

- `[FACT]` The 2026-07-22 consolidation handoff planned `/skill-dev` (3 modes) but it was NEVER BUILT. Receipt: `Test-Path ~/.grok/skills/skill-dev/SKILL.md → False`.
- `[FACT]` 4 CREATE skills exist but only `create-skill` is active on Grok Build; the other 3 are disabled-plugin discoverable-only. Receipt: operator-provided skill list.
- `[FACT]` `skill-prune` (at `.agents` scope) covers audit + retire (stale/duplicate/drifted). It's active. Receipt: `P:/.agents/skills/skill-prune/SKILL.md`.
- `[FACT]` ZERO skills do marginal-contribution measurement. `/aar` finds friction; `/tp` critiques; `/dream` Pass 5 proposes edits. None measure whether an active skill's output is used or ignored.
- `[FACT]` SLIM (Shen et al. 2026, arxiv 2605.10923) formalizes dynamic skill lifecycle management: retain/retire/expand driven by leave-one-skill-out marginal contribution estimation. Our lifecycle is the static instance of what SLIM treats as dynamic.
- `[FACT]` The /tp fresh-subagent critique (36 tool calls, REVISE verdict) concluded: build improve-mode only; the create/audit/retire coverage already exists.

## The design (from /tp + /www synthesis)

### Shape: two modes, not three

| Mode | What it does | Existing coverage | Gap |
|------|-------------|-------------------|-----|
| **measure** | Evaluate marginal contribution of active skills using retrospective evidence | NONE | **THE gap** |
| **improve** | Propose targeted improvements from measured MEC + wiki techniques-index | /tp (partial), /aar (partial), /dream Pass 5 (new) | Partial — needs the measurement to target |
| ~~create~~ | ~~Scaffold new skills~~ | create-skill | Covered |
| ~~audit/retire~~ | ~~Detect stale/duplicate~~ | skill-prune | Covered |

### The measure-mode closed loop (SLIM adapted to non-RL)

```
Step 0.5: Query wiki (techniques-index) + handoffs for known optimization patterns
Step 1:   Identify target skill + recent sessions where it fired
Step 2:   Retrospective MEC analysis:
          - Did the skill's output get used or ignored? (transcript evidence)
          - Was the skill the right one for the task? (routing accuracy from /tp critique log)
          - Leave-one-skill-out retrospective: would the session have gone differently?
Step 3:   Score the skill: retain / retire / improve (SLIM's three operations)
Step 4:   If improve: query techniques-index for applicable techniques, propose targeted fix
Step 5:   Held-out validation (Technique 2 from skill-lifecycle-toolkit): test the fix on examples NOT used to draft it
Step 6:   Write findings back to wiki (the closed loop from /why Step 15)
```

### What /skill-dev is NOT (boundary)

- NOT autonomous self-enhancement (Rung 5 — forbidden per /notice v1.2 boundary)
- NOT a replacement for create-skill (creation stays simple)
- NOT a replacement for skill-prune (structural staleness is its domain)
- NOT a replacement for /tp (design critique is its domain)

## Recommended fix path

**Decision needed:** build `/skill-dev` as measure + improve, or extend an existing skill?

The /tp critique offered alternatives:
1. **Build /skill-dev measure + improve** (recommended) — clean trigger, focused scope, ~3KB lean-hybrid SKILL.md + references
2. **Extend /tp with a skill-lifecycle mode** — /tp already does design critique; adding measure-mode is additive
3. **Extend /aar with per-skill MEC analysis** — /aar already reads session transcripts

The /tp critique favored #1 (clean trigger, clean scope). The /www research (SLIM) validated: the measure-mode is the distinct capability; bolting it onto /tp or /aar dilutes them.

## Dependencies

- **Requires:** nothing blocking. The techniques-index exists. The /aar transcript-reading capability exists. The /tp critique log exists.
- **Blocks:** nothing critical. The skill-optimization gap is efficiency, not correctness.
- **Non-blocking to:** any active work stream.

## Cross-reference couplings

- `P:/docs/handoffs/skill-consolidation-20260722/HANDOFF.md` — the original 3-mode plan (this handoff supersedes its /skill-dev scope)
- `P:/.data/wiki/concepts/skill-management-in-agentic-systems-research-survey.md` — the SLIM/CODESKILL/SkillRouter research
- `P:/.data/wiki/concepts/skill-lifecycle-toolkit.md` — the 5 transferable techniques (TDD, held-out validation, description optimization, pressure testing, rationalization tables)
- `P:/.data/wiki/concepts/wiki-integrated-skills-query-save-pattern.md` — the closed-loop pattern /skill-dev should follow
- `C:/Users/brsth/.grok/skills/create-skill/SKILL.md` — creation coverage
- `P:/.agents/skills/skill-prune/SKILL.md` — audit/retire coverage
- `C:/Users/brsth/.grok/skills/notice/SKILL.md` § "Self-improvement boundary" — what /skill-dev may NOT do

## Last user message (verbatim)

> /tp I'd like to rationalize our skill create and management space. should it be consolidated into skill-dev? What should we do?

## Next session protocol

1. Read this handoff + the /www research survey concept + the /tp critique output
2. Decide: build /skill-dev measure+improve (recommended) vs extend /tp or /aar
3. If build: use `/create-skill` to scaffold, follow the measure-mode closed-loop design above
4. Validate: run the new skill on 3 existing skills (e.g., /notice, /why, /www) and check whether the MEC analysis produces actionable insights

## Provenance

Written from session 019f9f4f after /tp critique (or-nemotron-ultra-free, 36 tool calls, REVISE verdict) + /www research on skill management in agentic systems. The /tp critique reframed the 3-mode plan to measure+improve; the /www research (SLIM) provided the formal foundation for marginal-contribution measurement.
