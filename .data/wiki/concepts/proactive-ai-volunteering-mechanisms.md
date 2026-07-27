---
title: "Proactive AI volunteering mechanisms: research base and three-mechanism ladder"
created: 2026-07-26
source: session-2026-07-26 (/www research on proactive AI assistants)
sources:
  - external: https://erichorvitz.com/chi99horvitz.pdf (Horvitz 1999, mixed-initiative principles)
  - external: https://sven-mayer.com/wp-content/uploads/2026/03/kraus2025behave.pdf (BEHAVE-AI principles, 2025)
  - external: https://ceur-ws.org/Vol-3957/BEHAVEAI-paper01.pdf (Viswanath & Buschmeier 2025)
  - external: https://arxiv.org/abs/2509.09309 (Harari & Amir 2025, proactive help as self-threat)
  - external: https://arxiv.org/abs/2410.04596 (Chen et al. CHI 2025, "Need Help?")
  - external: https://arxiv.org/html/2502.18658v4 (Pu et al. CHI 2025, "Assistance or Disruption")
  - external: https://arxiv.org/html/2503.14724v1 (CodingGenie, Zhao et al. 2025)
  - external: https://docs.openhands.dev/sdk/guides/agent-stuck-detector (StuckLoopDetection)
tags: [proactive-ai, mixed-initiative, behave-ai, clippy-syndrome, chen-need-help, notice-skill, deferent, anti-sycophancy]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  The field is "mixed-initiative interaction" (Horvitz 1999) or "proactive AI
  assistants" (modern). BEHAVE-AI principles (Kraus et al. 2025) distill eight:
  valuable, pertinent, competent, controllable, transparent, deferent, unobtrusive,
  anticipatory — three of which are *constraints on* proactivity. The strongest
  empirical finding (Harari & Amir 2025): proactive help increased self-threat
  and reduced adoption vs reactive help, even when useful. Personal-agent hardware
  that's ungated-proactive (Friend, Humane, Rabbit) universally failed; gated-proactive
  (Limitless, Apple Siri Proactive) succeeded. Coding-agent attempts (Copilot Review,
  Cursor Tab) get disabled when they fire too often. Three-mechanism ladder for
  our workspace: (1) end-of-turn observation rule (lowest risk, ship first), (2)
  /notice skill for mid-conversation gated surfacing (medium risk, build after #1
  measured), (3) full proactive agent (high risk, NOT worth it without evidence
  #1 and #2 are insufficient).
relations:
  - target: wiki/concepts/ai-thought-partner-landscape-and-tp-improvements-2026.md
    type: related
  - target: wiki/concepts/user-modeling-for-agentic-clis.md
    type: related
  - target: wiki/concepts/operator-collaboration-style-and-leverage.md
    type: related
---

# Proactive AI volunteering mechanisms: research base and three-mechanism ladder

## Decision context

**Why this research was needed:** the operator asked how to get the agent to volunteer info/ideas mid-conversation, and whether personal agents (OpenClaw, Hermes, etc.) do this automatically. The real question: **is there a research-grounded mechanism for an agent to surface observations without being asked, and what are the failure modes?**

**What alternatives were explored:**
- Field research on proactive/mixed-initiative AI (Horvitz, BEHAVE-AI, Harari & Amir, Chen et al., Pu et al., CodingGenie)
- Ecosystem scan (Friend, Humane, Rabbit, Limitless, Apple Siri, Copilot, Cursor, Pi)
- Coding-agent marketplace scan (no /notice-like skill exists)

All three converge on: proactivity without gates universally fails; gated proactivity can succeed.

**What the research changed:** produced the three-mechanism ladder that calibrates proactivity to risk. Operator approved mechanism 1 (rule) immediately; mechanism 2 (/notice skill) after research synthesis. Mechanism 3 (full proactive agent) explicitly rejected by the research.

## Key Findings

1. **The field is named.** "Mixed-initiative interaction" (Horvitz 1999) is the canonical academic term; "proactive AI assistants" is the modern vendor framing. Both treat the question "when should an AI volunteer input?" as a first-class design problem.

2. **BEHAVE-AI principles (Kraus et al. 2025)** distill the field into eight properties a proactive agent should have: **valuable, pertinent, competent, controllable, transparent, deferent, unobtrusive, anticipatory**. Three of those eight (controllable, deferent, unobtrusive) are *constraints on* proactivity, not arguments for it.

3. **The strongest empirical finding (Harari & Amir 2025, two studies):** proactive AI help increased self-threat and **reduced adoption** vs reactive help, even when the help was useful. Reactive help was welcomed; proactive felt intrusive regardless of value. This is the strongest published evidence for the "Clippy syndrome" intuition.

4. **Chen et al. CHI 2025 "Need Help?"** — the canonical proactive coding-assistant study. Two-mode state machine (acceleration = no suggestions during typing; exploration = idle ≥5s allows suggestions) plus immediate-trigger on execution error. **Preference dropped from 80–90% to 47%** when suggestion rate increased from every 20s→5s — productivity gained, experience lost.

5. **Pu et al. CHI 2025 "Assistance or Disruption"** — across 398 interventions: 53.3% engaged, **12.1% disrupted**, 34.7% ignored. **Task-boundary triggers (R2) worked best (66–73% engagement)**; idle-based triggers (R1) worked worst. Disruptions concentrated in implementation (32.7%); nearly absent in debugging (7.3%) and refactor (1.8%).

6. **Personal-agent hardware shows the ungated-proactive failure mode.** Friend.com, Humane AI Pin, Rabbit R1 — all universally panned. Limitless and Apple Siri Proactive succeeded *because gated* (Limitless acts after meeting-end; Siri predicts by routine, on-device).

7. **Coding-agent attempts get disabled.** Copilot Code Review and Cursor Tab both have documented "users disable because too aggressive" patterns. Cursor's "Rogue Assistant" is a recognized failure mode.

8. **The field's design heuristic (Anthropic, MindStudio, Chen et al. converge):** when in doubt, lower frequency. "More proactive = better" is empirically false even within pro-proactivity research.

## Three-mechanism ladder

For our workspace specifically:

### Mechanism 1 — End-of-turn observation rule (LOW risk, ship first)

Append a single-line `Note:` at end of turn when the model noticed something the operator would likely want to know — contradiction with prior wiki, related pattern from another session, risky unstated assumption, friction signal. The note must be factual (cite a receipt), non-blocking (operator can ignore), not a re-statement, actionable or contradiction-shaped (not "interesting thought"). Silent when nothing met the bar.

**Cost:** one extra line per ~5 turns; zero latency when silent.
**Authority:** extends existing verification-suggestion pattern that already works.
**Implementation:** rule in `~/.grok/AGENTS.md`. No new skill, no hook.

### Mechanism 2 — `/notice` skill (MEDIUM risk, build after #1 measured)

Skill that surfaces high-confidence observations mid-conversation when mechanical triggers fire (T1 error state, T2 task boundary, T3 stuck-loop pattern). Manual invocation (`/notice`) always available. Global cooldown (max 1 per 10 turns). Type constraint (contradictions, drift signals, recurring friction only — not "ideas in general"). Confidence floor (≥2 source instances). Hard-skip patterns (acceleration mode, first turn, mid-implementation, comment-only).

**Cost:** ~$20/user/month at expected fire rate (CodingGenie estimate).
**Authority:** three peer-reviewed trigger-taxonomy papers (Chen, Pu, CodingGenie).
**Implementation:** skill at `~/.grok/skills/notice/SKILL.md`. Reads `/aar` Phase 4 `operator_signal_delta` where available. Could later wire to `PostToolUse` hook for T1/T2 mechanical detection — but start as skill, not hook.

### Mechanism 3 — Full proactive agent (HIGH risk, NOT worth it)

Background monitor that watches the session and interjects. This is what failed for Friend/Humane/Rabbit and what gets disabled in Cursor/Copilot. **Do not build without strong evidence that mechanisms 1 and 2 are insufficient.**

## Trigger taxonomy (synthesized from the literature)

| Trigger | Source | Engagement | /notice fit |
|---|---|---|---|
| **T1: Error state** (recent failed test/command/exit≠0) | Chen et al. immediate-trigger | High | ✅ |
| **T2: Task boundary** (file save, run completed, multi-line paste) | Pu et al. R2 | 66–73% | ✅ |
| **T3: Stuck-state mechanical** (≥2 identical or A-B-A-B tool calls) | OpenHands StuckLoopDetection | High | ✅ |
| **T4: Idle extended** (>60s no input) | Pu et al. R1 | Worst | ❌ Skip |
| **T5: Explicit request** (`/notice` invocation) | Chen et al. manual | Always | ✅ |
| Anti-pattern: mid-typing | Pu et al. (32.7% disruption in impl) | — | ❌ Never |
| Anti-pattern: comment-only context | Pu et al. R3 (50% FP) | — | ❌ Never |
| Anti-pattern: first turn of session | Parnin & DeLine resumption lag | — | ❌ Never |

## Honest trade-offs

**Like (what good proactivity produces):**
- Surface contradictions the operator wouldn't have noticed
- Close loops between adjacent sessions
- Reduce "did we already know this?" re-derivation
- Catch friction patterns early

**Dislike (what ungated proactivity costs):**
- Self-threat / intrusiveness (Harari & Amir 2025)
- Notification fatigue (Cursor/Copilot disable pattern)
- Latency (each fire is a model call)
- Authoring burden (triggers need constant calibration)
- "Rogue Assistant" / Clippy failure modes

## Falsifier

This concept is wrong if, within 6 months:

- **Mechanism 1 (rule) is sufficient and /notice is never built.** Then the three-mechanism ladder overestimated what's needed; mechanism 1 alone is the answer.
- **Mechanism 2 (/notice) is built and the operator disables it within 30 days.** Then the trigger taxonomy didn't translate from research to this workspace — the workspace-specific calibration is wrong.
- **A vendor ships provably non-intrusive proactive surfacing** (formal guarantee, not heuristic). Then we should adopt rather than build.
- **Anthropic or another lab publishes a study refuting Harari & Amir 2025.** Then the "proactive = intrusive" finding is task-scoped, not general, and the recommendation should loosen.

## Open questions

1. **What's the actual T1/T2/T3 fire rate in this workspace?** Unmeasured. Audit needed: count triggers in a sample of recent transcripts. Drives the /notice cooldown calibration.
2. **Does mechanism 1 (rule) catch the high-value observations, or does it stay silent because the model defaults to "nothing to report"?** This is the calibration risk. The rule's "non-re-statement" and "actionable-or-contradiction-shaped" constraints may be too strict.
3. **Should /notice read live or batch?** Reading /aar Phase 4 signals (end-of-session) is safe; reading the live transcript mid-turn is potentially expensive and risks acceleration-mode violations.

## Related

- [[ai-thought-partner-landscape-and-tp-improvements-2026]]@related — adjacent "AI as critical friend" research; /tp is post-hoc critique, /notice is mid-conversation observation
- [[user-modeling-for-agentic-clis]]@related — the "predict-me-as-queryable-signals" pattern /notice consumes from /aar
- [[operator-collaboration-style-and-leverage]]@related — operator profile informs what's "valuable" to surface
- `~/.grok/AGENTS.md` End-of-turn observation rule — mechanism 1 implementation
- `~/.grok/skills/notice/SKILL.md` — mechanism 2 implementation

## Receipts (mechanism + local claims)

- **"Mechanism 1 (end-of-turn observation rule) shipped to AGENTS.md":** receipt — `~/.grok/AGENTS.md` § "End-of-turn observation rule (proactive surfacing, mechanism 1)" added 2026-07-26 this session; verified present via `Select-String -Pattern "End-of-turn observation rule" ~/.grok/AGENTS.md` returning True.
- **"Mechanism 2 (/notice skill) built at ~/.grok/skills/notice/SKILL.md":** receipt — file created this session, 273 lines; structural checks confirmed: has frontmatter with `name: notice`, T1/T2/T3 trigger table, hard-skip patterns, global cooldown, falsifier section.
- **"Chen et al. preference dropped 80→47% when suggestion rate increased":** receipt — arxiv 2410.04596 §6.2, cited via subagent 019f9f93-7b97-7920-a9b4-343298e78619 output this session (direct quote of the finding from the paper's HTML).
- **"Pu et al. R2 (task boundary) 66–73% engagement; R1 (idle) worst":** receipt — arxiv 2502.18658v4 §4.1 Table 1, cited via same subagent output.
- **"Pu et al. 32.7% of disruptions in implementation":** receipt — arxiv 2502.18658v4 §6.4, cited via same subagent output.
- **"Harari & Amir 2025: proactive help increased self-threat and reduced adoption":** receipt — arxiv 2509.09309, cited via subagent 019f9f7f-3625-71d3-9535-70772aa7672e from the earlier proactive-AI research turn in this session.
- **"No existing /notice-like skill in the marketplace":** receipt — subagent 019f9f93-7b97-7920-a9b4-3445f79f3144 scanned SkillsMP, skills.sh, ClawHub, Claude Skills Hub, alirezarezvani/claude-skills (362 skills), obra/superpowers; returned "No exact match found" with 10 closest candidates listed.
- **"T4 (idle extended) excluded from /notice triggers":** [INFERENCE] from Pu et al. R1 being worst-performing — the paper measured coding assistants, not conversational agents. The inference to our workspace is reasonable but unmeasured.

## Sources

**Foundational mixed-initiative:**
- Horvitz 1999, "Principles of Mixed-Initiative User Interfaces" — https://erichorvitz.com/chi99horvitz.pdf

**Modern principles distillation:**
- Kraus et al. 2025, BEHAVE-AI principles — https://sven-mayer.com/wp-content/uploads/2026/03/kraus2025behave.pdf
- Viswanath & Buschmeier 2025, Insights for Proactive Agents — https://ceur-ws.org/Vol-3957/BEHAVEAI-paper01.pdf

**Empirical studies:**
- Harari & Amir 2025, "Proactive AI Adoption Can Be Threatening" — https://arxiv.org/abs/2509.09309
- Chen et al. CHI 2025, "Need Help? Designing Proactive AI Assistants for Programming" — https://arxiv.org/abs/2410.04596
- Pu et al. CHI 2025, "Assistance or Disruption" (Codellaborator) — https://arxiv.org/html/2502.18658v4
- CodingGenie (Zhao et al. 2025) — https://arxiv.org/html/2503.14724v1

**Industry patterns:**
- OpenHands StuckLoopDetection — https://docs.openhands.dev/sdk/guides/agent-stuck-detector
- Friend.com reviews (Wired, NYT, Fortune, Tom's Guide) — universally negative
- Limitless pendant — https://www.limitless.ai/
- Apple Siri Proactive — https://developer.apple.com/documentation/corelocation
- Copilot Code Review — https://docs.github.com/en/copilot/concepts/agents/code-review
- Cursor Tab "Rogue Assistant" — https://forum.cursor.com/t/proactive-extra-changes/43850

**Research method:**
- Research conducted 2026-07-26 via /www pipeline. 1 parallel M3 subagent (proactive AI mechanisms) + ecosystem scan. The Harari & Amir 2025 finding is the strongest disconfirmation of the naive "more proactivity is better" assumption.
