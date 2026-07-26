---
thread_id: 019f9f4f-uncaptured-knowledge-20260726
parent_handoff_path: P:/docs/handoffs/session-019f9f4f-shipped-work-20260726/HANDOFF.md
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-26T20:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Uncaptured knowledge from session 019f9f4f

## Objective

Capture three knowledge items from session 019f9f4f that passed the /aar Q11 "uncaptured knowledge audit" threshold (would cost significant effort to rediscover) but were not promoted to wiki concepts or documented in other handoffs. Each item gets a task packet: the next session decides promote-to-wiki vs document-in-handoff vs reject.

## Status

OPEN — three items, each independent. None blocking; all would-cost-effort-to-rediscover.

## Producing context

- Session: `019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9` (2026-07-26)
- Audit method: /aar Q11 "uncaptured knowledge audit" — adversarial scan for tacit knowledge not in any durable artifact
- Three items surfaced; all meet the "significant effort to rediscover" threshold

## Read-first list

1. `P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md` — where item 1's decision rationale should be added (Provenance section)
2. `P:/docs/handoffs/script-backing-20260726/HANDOFF.md` — where item 2's failed-approach lesson informs the signal_baseline.py spec
3. This session's /www smoke test output (in transcript, not yet persisted) — item 3's research base for the concurrent-commit-collision concept

## Verified facts

- [FACT] The "defer /notice vs build now" decision rationale is NOT in `proactive-ai-volunteering-mechanisms.md` (receipt: `Select-String -Pattern "defer.*measure.*first|operator.*overrode" .data/wiki/concepts/proactive-ai-volunteering-mechanisms.md` returned False this session)
- [FACT] The raw-grep false-positive failure (5929 matches on "no") is NOT documented anywhere in the wiki (receipt: `Select-String -Pattern "5929|raw grep.*false positive" .data/wiki/concepts/*.md` returned no matches)
- [FACT] The concurrent-session commit collision pattern (3 observed instances) is NOT documented as its own concept; the closest match is `hook-evidence-collection-cost-vs-timeout-tradeoff.md:70` which mentions concurrent commits shifted HEAD but doesn't characterize the staged-set-interleave pattern (receipt: `Select-String -Pattern "concurrent.*commit.*collision|staged.*concurrent"` returned only that one tangential match)
- [FACT] The /www smoke test subagent (id `019fa00a-5927-7d52-9b28-5dd95213b533`) returned 10 sourced findings on the concurrent-commit-collision question, confirming it is a multi-agent-specific issue (not standard git) with a known structural fix (git worktree per agent)

## Task packets

### UK-01: Promote "defer vs build now" decision rationale to proactive-ai-volunteering-mechanisms.md

- **goal:** add a 2-3 sentence decision-rationale block to the Provenance section of `proactive-ai-volunteering-mechanisms.md` documenting why the operator overrode the "defer building /notice" recommendation
- **the uncaptured knowledge:** in turn 6, I recommended "defer building /notice; measure mechanism 1 [the end-of-turn rule] first" based on the research base alone (Harari & Amir 2025, Chen et al. preference collapse). In turn 7, the operator said "build the /notice skill" — overriding the defer recommendation. The operator's rationale (inferred from session context, not explicitly stated): session velocity made "don't forget to do it" a real cost; the research base was sufficient to act on; deferring would risk the work not happening at all. This is a generalizable operator-preference signal: **the operator prefers acting on sufficient research over deferring for perfect measurement**, especially when the cost of deferral includes forgetting.
- **why it matters:** future sessions recommending "defer and measure first" on similar decisions will repeat the same override cycle. The rationale should be captured so future sessions calibrate their defer recommendations to the operator's actual preference.
- **in scope:** add to Provenance section; do NOT restructure the concept
- **acceptance:** the rationale block is in the concept; the concept still passes `validate_wiki_entry.py`
- **falsifier:** the rationale is wrong (operator actually had a different reason) — operator can correct on review

### UK-02: Document raw-grep false-positive failure in signal_baseline.py spec

- **goal:** add a "known failure mode" note to the `script-backing-20260726` handoff (or to the signal_baseline.py spec within it) documenting that raw grep of pushback patterns against the full transcript produces massive false positives
- **the uncaptured knowledge:** when computing /aar Phase 4 signals this session, the first attempt at pushback_count used `([regex]::Matches($content, "no,?")).Count` against the full transcript — returned 5929 matches because "no" appears in every code block, every wiki concept, every system reminder. The second attempt filtered to user messages only — but still got 121 false positives for "Implement" because skill descriptions in system-reminders contain that word. The lesson: **signal-extraction patterns MUST filter to user-authored content only, AND must exclude system-reminder content that appears in the user-message envelope.** The script-backing handoff's signal_baseline.py spec doesn't currently mention this.
- **why it matters:** the next session implementing signal_baseline.py will hit the same false-positive wall without this note. The fix is mechanical (filter to `type == "user"` AND exclude content matching system-reminder patterns) but non-obvious.
- **in scope:** add a "Known calibration issues" section to the script-backing handoff OR a docstring note in the signal_baseline.py acceptance criteria
- **acceptance:** the note documents (a) the false-positive source (system-reminder content in user-message envelope), (b) the fix (filter to user-authored text, exclude system-reminder blocks), (c) the patterns most affected ("no", "Implement", "wrong" — common words with high base rates in code/docs)
- **falsifier:** the fix doesn't work (filtering still produces false positives) — would require deeper message-source detection

### UK-03: Write concurrent-session commit collision wiki concept

- **goal:** write `P:/.data/wiki/concepts/concurrent-session-commit-collision.md` from the /www smoke test research + the 3 observed instances this session
- **the uncaptured knowledge:** the pattern where `git add <file>` then `git commit` on a shared working tree captures concurrent-session changes is a known multi-agent-specific issue (not standard git). Root cause: shared `.git/index` file — concurrent git operations interleave entries. Observed 3 times this session: commits `33e17bd`, `5aa1506` (caught pre-commit), `5359d48`. The structural fix is `git worktree` per agent (each worktree has its own index); the mitigation is `git diff --cached --stat` immediately before commit to verify the staged set.
- **research base:** /www smoke test subagent returned 10 sourced findings (Bryan Finster's `test_multiplayer_collision.py`, skatejs #1487, GitHub Desktop #16260, pre-commit #2773, git worktree recommendation from Augmentcode and MindStudio)
- **why it matters:** the pattern will recur every session on this workspace. Without a wiki concept, each future session re-derives the diagnosis. The concept should reference the existing `auto-commit-authority-isolation` and `multi-agent-destructive-git` concepts as related.
- **in scope:** write the concept per SCHEMA.md; include the 3 observed instances as receipts; include the structural fix (worktree) and mitigation (staged-set verification); cross-link to existing concepts
- **acceptance:** concept passes `validate_wiki_entry.py`; cross-model review per /why Step 15b (the pattern is structural/systemic)
- **falsifier:** the pattern is actually standard git behavior that single-developer workflows also hit (disconfirmed by the research — single-developer never has concurrent `.git/index` mutation); OR the mitigation (`git diff --cached --stat` pre-commit) catches every instance (testable: would have caught all 3 this session)

## Open decisions

### Decision 1: UK-03 scope — full concept or handoff-only?

- **question:** is the concurrent-commit-collision pattern worth a full wiki concept, or just a note in an existing handoff?
- **options:**
  - (A) Full wiki concept — the pattern is structural, recurs every session, has 10 sourced findings, and the structural fix (worktree) is actionable
  - (B) Note in the session-shipped-work handoff only — lower ceremony, but future sessions won't find it via /wiki query
- **selection criterion:** would a future session facing the same pattern benefit from finding this via `qmd search`?
- **currently leads:** (A) — the pattern is exactly the shape /wiki is designed for (structural, cross-session, actionable)
- **what would change this:** if the existing `auto-commit-authority-isolation` concept already covers this angle (it doesn't — checked this session)

## Hard constraints

1. **UK-01 and UK-02 are documentation-only.** No code changes; just adding notes to existing artifacts.
2. **UK-03 follows /why Step 15 pattern.** If writing the concept, run cross-model review (glm-5-2 preferred); if review rejects, the finding stays in this handoff only.
3. **Anti-"smallest viable" applies.** UK-03's concept should be properly structured (Decision context, Key findings, Honest trade-offs, Falsifier) per the anti-thin-entry rule — not a bullet-point dump.

## Cross-reference couplings

- `P:/docs/handoffs/script-backing-20260726/HANDOFF.md` → UK-02 adds a calibration note to this handoff
- `P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md` → UK-01 adds a rationale block to this concept's Provenance section
- `P:/.data/wiki/concepts/auto-commit-authority-isolation.md` → UK-03's concept cross-links to this as related
- `P:/.data/wiki/concepts/multi-agent-destructive-git.md` → UK-03's concept cross-links to this as related

## Other outstanding streams (not handed off)

- None beyond the four handoffs already written this session (session-shipped-work, script-backing, design-bloat-assessment, enhancement-offsetting-retirement-rule).

## Explicit non-goals

1. **Do not re-do the /www smoke test.** It ran successfully; the research output is in this handoff.
2. **Do not implement the signal-extraction fix.** That's SB-01's scope (script-backing handoff).
3. **Do not implement the worktree-per-agent fix.** That's a fleet-architecture decision separate from capturing the knowledge.

## Resumption protocol

1. Read this handoff.
2. For UK-01: open `proactive-ai-volunteering-mechanisms.md`, add 2-3 sentences to Provenance documenting the defer-vs-build decision and the operator's override rationale. Validate. Commit.
3. For UK-02: open `script-backing-20260726/HANDOFF.md`, add a "Known calibration issues" section documenting the raw-grep false-positive failure. Commit.
4. For UK-03: write `concurrent-session-commit-collision.md` per the research base in this handoff's Verified facts + the smoke test subagent output. Validate. Cross-model review. Commit.
5. Each item is independent — pick up any subset.

## Suggested next invocation

```
Continue work from session 019f9f4f. Read P:/docs/handoffs/uncaptured-knowledge-20260726/HANDOFF.md.

Three independent items, each capturing knowledge that passed the /aar Q11 threshold:
- UK-01: add defer-vs-build decision rationale to proactive-ai-volunteering-mechanisms.md Provenance
- UK-02: add raw-grep false-positive calibration note to script-backing handoff
- UK-03: write concurrent-session-commit-collision wiki concept from /www smoke test research

Pick up any subset. UK-01 and UK-02 are 5-minute documentation edits. UK-03 is a
30-minute concept write with cross-model review.
```

## Last user message (verbatim)

> "run one /www smoke test
> /handoff make sure all uncaptured items that we would want captured are captured."

## Epistemic labels

- All "Verified facts" are `[FACT]` with `Select-String` receipts cited inline.
- The "operator's rationale (inferred from session context)" in UK-01 is `[INFERENCE]` — the operator did not explicitly state the rationale; I inferred it from session velocity and the override pattern. The operator can correct on review.
- The /www smoke test subagent findings are `[FACT]` (the subagent returned them; receipts are the cited URLs in the subagent output).
- Decision 1 "currently leads (A)" is `[INFERENCE]` based on the pattern matching /wiki's design intent.
