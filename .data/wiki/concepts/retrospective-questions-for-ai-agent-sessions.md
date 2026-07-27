---
title: "Retrospective questions for solo AI agent sessions: what /tp session was missing"
created: 2026-07-27
source: session-2026-07-27 (/www research on retrospective question coverage)
tags: [retrospective, session-review, tp-session, agile-adaptation, solo-developer, continuous-improvement]
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
summary: >
  Traditional retrospective frameworks (Start-Stop-Continue, 4Ls, Parabol 50+
  questions) ask 6 questions that /tp session was missing: what went well
  (Continue), what to stop doing (Stop), what surprised us, what we learned,
  whether prior recommendations helped, and the cost of inaction. Team-oriented
  questions (wellbeing, icebreakers, process complaints) do NOT translate to
  solo AI agent sessions. The 6 additions are lean passes, not full sections —
  the disconfirmation research shows retrospectives fail when bloated. Connects
  to [[ai-thought-partner-industry-expectations-and-now-next-later]] (the
  Now-Next-Later origin) and [[visible-output-contracts-for-behavioral-skill-steps]]
  (the enforcement pattern for session-review steps).
sources:
  - https://www.parabol.co/resources/retrospective-questions/ (Parabol, 2024)
  - https://www.atlassian.com/blog/teamwork/revitalize-retrospectives-fresh-techniques (Atlassian, 2024)
  - https://www.teamretro.com/retrospective-templates/4ls-retrospective/ (TeamRetro, 2024)
  - https://arxiv.org/html/2504.11780v1 (arxiv, Apr 2025)
relations:
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later.md
    type: extends
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: related
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/skill-authoring-patterns-dos-and-donts.md
    type: related
---

# Retrospective questions for solo AI agent sessions

## Decision context

**Why this research was needed:** the operator asked "/www what other questions should /tp session ask?" after discovering that `/tp session` had missed 6 Python quoting failures, 3 permission denials, and a vanished file — not because the transcript scan (Step 0) failed to find them, but because the NOW/NEXT/LATER framework focused exclusively on problems and opportunities. It never asked what went well, what to stop, what surprised us, or what we learned. The question was: do established retrospective frameworks ask things we don't?

**What alternatives were explored:** the current NOW/NEXT/LATER/FILTER/CROSS-DOMAIN protocol was derived from the Now-Next-Later product-management framework (Intercom popularization). It was NOT derived from agile retrospective traditions (Scrum sprint retros, 4Ls, Start-Stop-Continue). The research revealed a systematic blind spot: the current protocol covers "what to fix" but not "what to keep," "what to stop," "what surprised us," or "what did we learn."

## Key findings

### The 6 missing questions (from established frameworks)

**1. CONTINUE — "What went well that we should keep doing?"**

Source: Start-Stop-Continue (the most widely used retro format), 4Ls (Liked). The current protocol focuses 100% on problems, gaps, and opportunities. It never asks what worked well this session that should be preserved. The wiki captures findings but not "this approach worked — use it again."

For AI agent sessions: the 3-layer isolation strategy (worktree + state_dir + scan window) worked perfectly for Phase 3 acceptance. Without a CONTINUE pass, this approach isn't surfaced as reusable — the next session has to re-derive it. This connects to [[compound-skill-improvement-patterns]] — CONTINUE captures the "what worked" that compounds across sessions.

**2. STOP — "What should we stop doing?"**

Source: Start-Stop-Continue. Dead patterns, unused skills, stale rules, and obsolete workflows accumulate because nothing retires them. The `/skill-prune` skill exists for wiki/skill retirement, but `/tp session` never triggers it because it doesn't ask the stop question.

For AI agent sessions: "stop using `python -c` with nested quotes" is a STOP recommendation. Without the STOP pass, this surfaces as a NEXT friction item (something to fix) rather than a STOP item (something to cease doing entirely). The STOP pass also connects to [[skill-authoring-patterns-dos-and-donts]] — retiring stale patterns is as important as adding new ones.

**3. SURPRISES — "What surprised us?"**

Source: Parabol future-oriented questions, Atlassian significant events. Unexpected events are the highest-signal data in any retrospective — surprises are assumptions that were wrong. The current protocol doesn't explicitly mine for them.

For AI agent sessions: the verifier script vanishing from `P:/tmp/` was a surprise. The workspace fast-path misidentifying nested repos was a surprise. Both were high-signal findings that the NOW pass caught incidentally but the protocol didn't systematically surface.

**4. LEARNED — "What did we learn (knowledge, not opportunities)?"**

Source: 4Ls (Learned). The current protocol captures opportunities (what to do) and friction (what to fix) but not learnings (what we now know that we didn't before). Learnings are durable; opportunities expire.

For AI agent sessions: "the `_check_obligation_satisfied` function requires a single receipt to cover ALL blocked paths — it doesn't aggregate partial receipts" is a learning. It's not a wiki concept (too specific) but it's knowledge that would help the next session avoid re-deriving it.

**5. PRIOR FOLLOW-THROUGH — "Did our prior recommendations help?"**

Source: Parabol "did improvements from previous retro help?" The critique log tracks whether recommendations were acted on (git commits after critique = likely-acted-on). But the session protocol doesn't close the loop: did the last session's DO_NOW items actually improve things? Without this, the same recommendations recur.

For AI agent sessions: if the last session recommended "add visible-output contracts to /why Step 0.5" and it was done, the current session should note that it's done, not re-recommend it. The critique log has this data mechanically — the session protocol just needs to surface it. This is the session-scale instance of [[visible-output-contracts-for-behavioral-skill-steps]] — the receipt discipline that makes the follow-through check auditable.

**6. COST OF INACTION — "What's the cost of doing nothing?"**

Source: Parabol action-item questions. The current protocol surfaces issues with dispositions (DO_NOW, NEW_HANDOFF, MONITOR) but doesn't assess the cost of inaction. This helps prioritize: a MONITOR item with high inaction cost should be DO_NOW.

For AI agent sessions: "the workspace fast-path defect is MONITOR but the cost of inaction is that every Phase 3 acceptance on this host will hit the same nested-repo identity failure" — that cost statement elevates it toward DO_NOW.

### What NOT to add (disconfirmation)

The disconfirmation pass searched for evidence that retrospectives fail. The research was clear:

- **Team wellbeing questions** — not applicable to solo AI agent sessions. The "how do you feel" axis doesn't translate.
- **Check-in / icebreaker questions** — the operator doesn't need warming up.
- **Process/system questions** ("did any processes create problems?") — already covered by NEXT recurring friction + Step 0 transcript scan.
- **More question formats** — [GoRetro 2022](https://www.goretro.ai/post/why-developers-hate-retrospectives) and [Reddit r/agile](https://www.reddit.com/r/agile/comments/1gipoyn/) document that retrospectives fail when bloated or monotonous. The 6 additions are lean; adding more would push toward the failure mode. The operator who asked "did we capture everything?" was looking for completeness, not more ceremony — the additions must serve that goal or they become noise.

## What this means for our workspace

The revised `/tp session` protocol becomes: **Step 0 (transcript scan) → NOW → CONTINUE → STOP → NEXT → LATER → SURPRISES → LEARNED → FILTER → CROSS-DOMAIN**, with prior follow-through woven into the dispositions and cost-of-inaction as a one-sentence annotation per MONITOR item.

The additions are **lightweight passes, not full sections**. Each produces 1-3 bullets, not a paragraph. The goal is to catch what the NOW/NEXT/LATER framework structurally misses, not to create a bloated retrospective that the operator skips. The key insight from the disconfirmation research: the failure mode for retrospectives is not "missed questions" but "too many questions" — each addition must earn its place by catching something the existing passes systematically miss.

The protocol also gains mechanical support: the SURPRISES pass can be transcript-scanned (`Select-String "unexpected|surprised|didn't expect"`), the PRIOR FOLLOW-THROUGH pass can be critique-log-scanned (`tp_critique_log.py auto --limit 5`), and the CONTINUE pass can cross-reference the session's commits to identify what worked. This mirrors the Step 0 transcript scan — mechanical scanning catches what recall misses.

## Receipts

- **"Current /tp session protocol has NOW/NEXT/LATER/FILTER/CROSS-DOMAIN but no CONTINUE/STOP/SURPRISES/LEARNED":** receipt — code read of `C:/Users/brsth/.grok/skills/tp/SKILL.md` lines 200-290 (the `/tp session` section), this session.
- **"Parabol organizes 50+ questions into check-in, what went well, what didn't, future-oriented, action items, wellbeing":** receipt — web_fetch of parabol.co/resources/retrospective-questions/ this session.
- **"Start-Stop-Continue is the most widely used retrospective format":** receipt — minimax-search__web_search returned Start-Stop-Continue as top result across multiple sources (TeamRetro, Retrium, Neatro, Scatterspoke).
- **"Retrospectives fail when bloated or monotonous":** receipt — GoRetro 2022 + Reddit r/agile discussion, both surfaced in the disconfirmation pass.

## Falsifier

These additions are wrong if:
- **They add ceremony without value.** If the operator never finds CONTINUE/STOP/SURPRISES/LEARNED useful, remove them. Test after 5 sessions of use.
- **They make /tp session too long to run mid-session.** If the total runtime exceeds 90 seconds inline, the additions have failed. Each pass should be ≤5 bullets.
- **The prior follow-through check is noise.** If the critique log is stale or the git-commit heuristic is unreliable, the prior follow-through pass produces false signals. Test against 3 sessions with known follow-through.

## Sources

- [Parabol: 50+ Retrospective Questions](https://www.parabol.co/resources/retrospective-questions/) (Parabol, 2024) — the comprehensive question catalog organized by purpose (check-in, what went well, what didn't, future-oriented, action items, wellbeing)
- [Atlassian: 9 Retrospective Techniques](https://www.atlassian.com/blog/teamwork/revitalize-retrospectives-fresh-techniques) (Atlassian, 2024) — significant events, Start-Stop-Continue, 4Ls (Liked, Loathed, Learned, Longed For), Mad-Sad-Glad
- [TeamRetro: 4Ls Retrospective](https://www.teamretro.com/retrospective-templates/4ls-retrospective/) (TeamRetro, 2024) — the 4Ls format (Liked, Learned, Lacked, Longed For)
- [arxiv 2504.11780](https://arxiv.org/html/2504.11780v1) (Apr 2025) — academic study of agile retrospective question patterns
- [GoRetro: Why Developers Hate Retrospectives](https://www.goretro.ai/post/why-developers-hate-retrospectives) (2022) — disconfirmation source: retros fail when monotonous or bloated
