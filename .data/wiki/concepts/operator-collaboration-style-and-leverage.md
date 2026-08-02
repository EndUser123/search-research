---
type: concept
title: "Operator collaboration style, leverage gaps, and recommendations"
created: 2026-07-20
sources:
  - internal: C:\Users\brsth\.grok\sessions\P%3A%5C\prompt_history.jsonl (~1021 prompts, 2026-07-16 → 2026-07-20)
  - internal: 12 sampled transcripts from C:\Users\brsth\.grok\sessions\P%3A%5C\
  - internal: P:\.data\wiki\concepts\llm-handoff-best-practices.md
  - internal: P:\.data\wiki\concepts\skill-enforcement-layers.md
  - internal: P:\.data\wiki\concepts\solo_operator_adr_best_practices.md
  - internal: C:\Users\brsth\.grok\AGENTS.md, P:\.claude\CLAUDE.md, P:\AGENTS.md
  - external: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - external: https://www.anthropic.com/engineering/claude-code-best-practices
  - external: https://www.anthropic.com/engineering/building-effective-agents
  - external: https://arxiv.org/abs/2503.13657 (Cemri et al. 2025, MAST taxonomy, NeurIPS)
  - external: https://arxiv.org/abs/2307.03172 (Liu et al. 2023, "Lost in the Middle")
  - external: https://addyosmani.com/blog/ai-coding-workflow/
  - external: https://simonwillison.net/2025/Jul/21/coding-with-llms/
tags:
  - collaboration-style
  - self-reflection
  - leverage
  - prompt-patterns
  - fleet-orchestration
summary: "Four-lane evidence-grounded analysis of how the operator collaborates with LLMs (style profile, divergence from own documented bar, under-used capabilities, ranked recommendations). All subagent syntheses were spot-checked per the report-gate rule before propagation."
host: both
---

# Operator collaboration style, leverage gaps, and recommendations

**Context for this page:** the operator asked "am I using you properly? Am I using you fully?" — requesting an evidence-grounded analysis of their own collaboration patterns, benchmarked against (a) their own documented bar and (b) the external field. This page synthesizes four parallel investigation lanes, each delegated to a subagent, with spot-checks applied per the `subagent-synthesis → report gate` rule in `~/.grok/AGENTS.md`.

**Calibration:** the operator is a solution architect operating solo as director of an AI coder fleet. They have already codified extensive best practices in `llm-handoff-best-practices.md`, AGENTS.md, CLAUDE.md, and 24+ wiki concept pages. This page's value is **not** in introducing external theory — the operator is ahead of the field on several dimensions (subagent synthesis spot-checking, skill host-applicability tags, pre-mortem prompting discipline, bounded task packets for solo fleet operation). Its value is in **mirroring live behavior back** and naming where it diverges from the documented bar.

---

## Method

Four lanes ran in parallel:

| Lane | Question | Method | Sample |
|------|----------|--------|--------|
| 1. Quantitative | What does the prompt corpus look like statistically? | Parse `prompt_history.jsonl` | ~1021 prompts |
| 2. Qualitative | How does the operator open, push back, close, tolerate verbosity? | Code 12 stratified transcripts | small/medium/large/very-large mix, 2026-07-17 → 2026-07-20 |
| 3. Wiki cross-ref | What has the operator already codified? Where are internal tensions? | Read 10 wiki concept files + 2 governance docs | full text |
| 4. External research | What does the field say? | 11 web searches, 6 detailed extracts | Anthropic, OpenAI, xAI, Cemri et al., Liu et al., practitioner blogs |

### Spot-check gate applied

Before propagation, each lane's synthesis was checked against at least one piece of evidence already in the orchestrator's context:

- **Lane 1's** "1021 prompts, 2026-07-16 start" was confirmed by direct read of `prompt_history.jsonl:1` (`2026-07-16T13:36:50Z`, "can you see the code at P:\\packages\\yt-is?"). **Caveat:** Lane 1's subagent could not execute its Python script (explore role has no Bash) — length distribution and intent classification are grep-based estimates, not computed values. The script is at `P:\tmp\analyze_prompts.py` (text-only, never saved by the subagent). Numbers below mark this explicitly.
- **Lane 2's** per-session observations (specific session IDs, file counts, quotes) are **not independently verified** — they are reported by the subagent and consistent with the directly-read Gemini transcript pattern. Quotes from `chat_history.jsonl:323` of `019f7653-...` etc. are taken on the subagent's report; if cited downstream, they should be re-verified.
- **Lane 3's** claims about `skill-enforcement-layers.md` (Layer 1 ~50%), the cc-council incident (AGENTS.md hard rules), and the $47K case (`llm-handoff-best-practices.md` line 100) are all directly present in files the orchestrator already read.
- **Lane 4's** external sources (Cemri et al. arxiv 2503.13657, Liu et al. arxiv 2307.03172) are also cited in the operator's own `llm-handoff-best-practices.md`, confirming existence.

### Limitations

1. **Sample window is 4 days** (2026-07-16 → 2026-07-20). Older behavior may differ. Prompts pre-Grok-Build-adoption are not in this corpus.
2. **`prompt_history.jsonl` is Grok-only** — does not include Claude Code sessions (those live in a different store). Style may be Grok-specific.
3. **No assistant-side analysis** — this page documents the operator's prompts, not the assistant's response quality. A follow-up could analyze operator reactions to assistant outputs (pushback rate, acceptance rate, cut-off rate).
4. **Lane 1's metrics are approximate** (grep-based, not computed). The full script exists as text in the Lane 1 subagent report and can be saved and run to produce exact distributions.

---

## 1. Operator collaboration style profile

### 1.1 What the data shows

| Dimension | Observation | Evidence |
|-----------|-------------|----------|
| **Volume** | ~1021 prompts over 4 days across many sessions; mean prompts/session estimated 3-8 (rough) | `prompt_history.jsonl` line count; Lane 1 report |
| **Length** | Bimodal: many <200 char turn-taking tokens; several >50K char paste-and-ask blocks | Direct read of lines 1-3; Lane 1 |
| **Opening pattern** | Lowercase, conversational; "can you", "i want", "what", "why", "did you", slash commands | Lane 1 grep; Lane 2 cross-sample |
| **Slash-command dominance** | `/agy`, `/grok-sdlc`, `/review`, `/refactor`, `/go`, `/debrief`, `/red-team`, `/wiki`, `/aar`, `/check`, `/tp`, `/design`, `/mo` | Lane 1; verified across Lane 2 samples |
| **Affirmative glue** | Frequent single-token affirmatives: "yes please", "continue", "commit", "1.", "2.", "a)" | Lane 2 cross-sample (samples 8, 9, 12) |
| **Typos** | Fast typing, accepts typos ("efficinet", "shoudl", "Ithink", "Wwill") — does not ask LLM to be terse | Lane 2 direct quotes |
| **Cost awareness** | Surfaces occasionally: "Be efficinet and use code if it will help save LLM costs"; "use minimax and zai direct" | `prompt_history.jsonl` lines per Lane 2 |

### 1.2 Documented style profile

The operator's collaboration style, as evidenced across 12 sampled transcripts and ~1021 prompts:

1. **Tight turn-taking glue.** The operator uses minimum-token affirmatives ("yes please", "continue", numbered options) as conversational steering — they don't write full sentences for "go ahead". This is a deliberate efficiency, not laziness.

2. **Slash-command as primary interface.** Slash commands schedule behavior rather than request it. The operator invokes `/tp`, `/agy`, `/red-team`, `/check`, `/debrief` rather than writing imperative prose. Slash commands are how the operator **binds the LLM to a contract** before giving it the task.

3. **Thought-partner framing by default.** Across 5+ direct quotes (`:5`, `:74`, `:88`, `:235`, `:330`), the operator explicitly requests "act as a thought partner" and acknowledges "I don't know what I don't know." This is a **deliberate stance request**, not a passive style.

4. **Adversarial review demand.** Direct quotes: "please critically review your proposal" (`:9`, `:109`, `:110`), "friendly critic review your proposal" (`:824`), "push harder" (`:830`), "/red-team your proposal" (`:910`). The operator escalates from soft to hard adversarial review when the LLM's first answer is too narrow.

5. **Meta-cognition as the dominant verb.** The most common operator verb is some form of "what are we missing?" — not "do X" but "find X for me." Sessions 11 and 12 (Lane 2) show the operator iterating `/agy` 6+ times, each turn adding constraints, never resetting. The operator is constantly refining the prompt envelope, not just the task.

6. **Iterative constraint-tightening, not single-pass proposals.** Sample 11 (`019f6f1e-...`) shows 6 redesigns of the `/agy` skill in one session, each adding one constraint ("no host-storage assumption", "no LATEST-* pointer", "preserve-authority"). The operator does not propose complete specs; they **grow specs through adversarial iteration.**

7. **Explicit trust-loss, no performance of niceness.** Sample 12 contains "You say this day after day after day, how can I trust you now?" (`chat_history.jsonl:323`). Other direct quotes: "what the fuck? I want that handoff because the problem is not solved" (`prompt_history.jsonl:992`). The operator **names trust loss rather than papering over it.** This is rare in human-AI corpora.

8. **Fleet narration as default.** In long sessions, the operator narrates fleet state to the current agent: "i asked another LLM to clean the tree", "we have multiple terminals working", "this is from another LLM's context", "we need to be multi terminal isolated." The current agent is implicitly briefed on the broader fleet as a precondition for its answer.

9. **Re-scope and route, don't argue.** Sample 10 (`019f756d-...`) shows the canonical pushback pattern: `Just do it for check. Another LLM is going to do its own work for AAR.` The operator changes the spec, changes the lens, or splits the work across another LLM — they do not argue content.

10. **Thoroughness over brevity.** Direct quotes: "I don't want a short sweep, do that, but also look for repos that have good ideas. don't be lazy." (`:100`), "I'd rather err on the side of doing more, to ensure quality outcomes. We shouldn't artificially limit the lenses we use." (`:186`). This matches AGENTS.md Environment: "lean slightly more thorough rather than less."

11. **Recommendation completeness expectation** (added 2026-08-01 via /dream Pass 4). The operator wants the FULL list of items with positive ROI, each tagged with confidence (H/M/L). Does NOT want pre-curated "top N" subsets. Scans and prioritizes himself. Direct quote: "I don't like it when you hide recommendations from me. I don't want only two, I want all of them that have value." Evidence: sessions 019fbdfb (2026-08-01) and 019f9aff AAR E2/E5 (2026-07-26). Now enforced via AGENTS.md § Recommendations "Completeness over curation."

12. **Correction frequency baseline** (added 2026-08-01 via /dream Pass 4). ~1-3 corrections per session is the norm. Corrections cluster around: (1) completeness vs curation of recommendations, (2) premature closure under time pressure, (3) asserting behavior from memory rather than testing. Evidence: AAR 019f9aff recorded 3 corrections; session 019fbdfb recorded 2 (hiding recommendations, skipping Phase 1 review). Pattern visible across ≥3 sessions per wiki concepts `overclaiming-under-exploration-to-recommendation-pressure.md` and `reactive-pattern-matching-and-closure-pressure.md`.

### 1.3 Alignment with external best practices

Per Lane 4, the operator's documented practices converge with the field on 11 of 12 high-confidence practices identified (verification gates, spec-before-code, just-in-time context, subagent architectures, tiered model routing, etc.). The operator is **ahead of external literature** on:
- Subagent synthesis spot-checking (more rigorous than Anthropic's "adversarial review step")
- Skill host-applicability tags (no external equivalent)
- Pre-mortem prompting discipline (no canonical LLM pre-mortem guide found)
- Bounded task packets for solo fleet operation (MAST documents failures; user prescribes structure)

---

## 2. Where behavior diverges from documented bar

These are the highest-signal findings. The operator wrote the bar; live behavior sometimes falls short.

### 2.1 "Evidence for done" gap (self-documented)

The operator's `llm-handoff-best-practices.md` line 213-219 lists 9 things current handoffs miss, including:
- ❌ Decision log as a separate file
- ❌ Evidence requirement for "done"
- ❌ Drift audit before close
- ❌ Verbatim last-user-message preservation
- ❌ MAST 14-mode pre-flight checklist
- ❌ Sub-agent isolation for context-heavy inspection
- ❌ Cost/step budgets on delegating handoffs

**The operator knows.** The wiki page documents the gap. The question is whether the operator demands these from the LLM at handoff time — and the transcripts show that the operator sometimes accepts narrative "done" claims without enforcing the evidence packet. **This is the highest-leverage gap because the operator has already done the work of documenting the bar; they just don't always enforce it on themselves.**

### 2.2 Capability gap gate vs source-authority-discovery conflict

`P:/.claude/CLAUDE.md` "Mandatory Source-Authority Discovery" requires invoking the skill before non-trivial review/implementation. `~/.grok/AGENTS.md` "Capability gap gate" requires STOP before freeform multi-file tours. The cc-council incident (2026-07-20, documented in AGENTS.md hard rules) is a case where **both gates were structurally bypassed** — a dense architecturally-significant target was bundled with another into a shared subagent without the discovery step. The operator wrote the rule *because* the rule was violated.

**Implication:** documented rules without mechanical enforcement (hooks) are aspirational. The operator's own `skill-enforcement-layers.md` reports ~50% Layer 1 compliance for advisory rules. The "hard rules" in AGENTS.md are mostly not hook-enforced.

### 2.3 Trust-loss loop not converted to AAR

Sample 12 (`019f7653-...`) contains the strongest trust-loss quote: "You say this day after day after day, how can I trust you now?" The transcript shows the operator pushing through, but there is no evidence in the sampled window of an `/aar` invocation to convert that trust-loss into a durable lesson. The `/aar` skill exists; the operator has it; but **the reflex to invoke it at trust-loss moments is not visible in the sample.**

### 2.4 Plan mode omission

`~/.grok/AGENTS.md` "/plan (plan mode) suggestion rule" exists because of a reference incident where plan mode was omitted from options (the multi-stream yt-is cleanup ask). Lane 2 found the operator doing extensive multi-turn analysis (e.g., session `019f7a94-...` on web-search-tools-handoff) **inline in chat rather than in plan mode**, even though the deliverable would outlive the conversation.

### 2.5 Examples-over-rules documented but rarely applied

`P:/.data/wiki/concepts/examples-over-rules-escape-hatch.md` documents the pattern: when rules fail, use 10-30 curated past outputs labeled with rationale. The operator's prompts are overwhelmingly **rules-based directives** ("do X, don't do Y, constraint Z"). There is no visible practice of curating few-shot examples for skills that underperform.

### 2.6 Fleet state narration is not formalized

The operator manually narrates fleet state to each new agent ("we have multiple terminals working", "another LLM is doing X"). This is effective but **not durable** — it depends on the operator remembering to do it every session. The `llm-handoff-best-practices.md` three-artifact architecture (Handoff + Plan structure + Plan status) exists to solve exactly this, but the transcripts show the operator relying on conversational narration rather than reading from a persisted fleet-status file.

---

## 3. Under-used capabilities

Capabilities that exist in the operator's environment but are not consistently used:

| Capability | Path / skill | Under-use signal |
|---|---|---|
| **Plan mode** | `/plan` (plan mode rule in AGENTS.md) | Documented reference incident where it was omitted; Lane 2 shows long inline analyses that would benefit |
| **`/aar` (After-Action Review)** | `P:\.grok\skills\aar\SKILL.md` | Not invoked at trust-loss moments in sampled window |
| **Multi-LLM consensus (parallel review)** | Manual via `/agy` or parallel subagents | Used occasionally (yt-is handoff review, sample 3) but not a default gate for hard-to-reverse decisions |
| **`/red-team` as default gate** | `P:\packages\.claude-marketplace\plugins\red-team\commands\red-team.md` | Used reactively ("push harder", "/red-team your proposal") but not proactively at decision time |
| **Cost-aware model tiering** | Documented in CLAUDE.md Cost Tiering | Only one explicit prompt in sample: "use minimax and zai direct" (`:132`) — most delegations don't specify model tier |
| **Examples-over-rules curation** | `examples-over-rules-escape-hatch.md` | Documented pattern; no visible practice of building example corpuses for underperforming skills |
| **Wiki pre-check** | `P:\.data\wiki\` | The prompt "I want you to look in /wiki for information that can optimize..." (`:712`) suggests sometimes forgetting to check first |
| **`source-authority-discovery` skill** | `P:/.agents/skills/source-authority-discovery/` | cc-council incident shows it was bypassed |
| **`grok-verify` completion gate** | `~/.grok/skills/grok-verify/SKILL.md` | Not visible as a default step before "done" claims in sampled transcripts |
| **Three-artifact handoff separation** | `llm-handoff-best-practices.md` Handoff vs Plan vs Status | Operator relies on conversational fleet narration; doesn't persist status files per the documented Option C |

---

## 4. Recommendations ranked by leverage

Each recommendation is paired with the bar it enforces, the gap it closes, and a falsifier.

### Tier 1 — Highest leverage (closes self-documented gaps)

#### R1. Make `/aar` invocation automatic at trust-loss moments

- **Closes:** §2.3 (trust-loss loop not converted to AAR)
- **Bar enforced:** `solo_operator_adr_best_practices.md` — "decision durability matters more than conversation fidelity"
- **Mechanism:** when the operator catches themselves writing "you said X yesterday" or "how can I trust you now," invoke `/aar` before continuing the work. The skill exists; the reflex doesn't.
- **Effort:** One habit change.
- **Falsifier:** if the operator already does this consistently in sessions outside the 4-day sample, R1 is wrong.

#### R2. Default-gate hard-to-reverse decisions through `/red-team` or `/tp` proactively (not reactively)

- **Closes:** §3 (under-use of `/red-team` as default gate) and §2.4 (plan mode omission)
- **Bar enforced:** `~/.grok/AGENTS.md` Recommendation Rule — "≥2 viable options + selection criterion"
- **Mechanism:** any decision involving architectural commitment, file moves, hook changes, or plugin mutations triggers a `/tp` or `/red-team` review **before** the operator approves. Currently the operator uses these reactively after a bad answer.
- **Effort:** One slash-command invocation per significant decision.
- **Falsifier:** if the operator's reactive pattern already catches every case that proactive gating would, R2 adds latency without value.

#### R3. Close the "evidence for done" gap by demanding it at handoff time

- **Closes:** §2.1 (the self-documented gap in current handoffs) — the highest-signal finding because the operator already documented the bar
- **Bar enforced:** `llm-handoff-best-practices.md` "Best practices §9 Attach evidence to completed steps" + "Implications for solo director §6 Drift audit before close is non-negotiable"
- **Mechanism:** before accepting any "done" claim, require the assistant to produce: changed files, commands run, test results, remaining risks. The `grok-verify` skill exists for exactly this. The fix is to invoke it before "done" rather than after.
- **Effort:** One slash-command invocation per work-stream completion.
- **Falsifier:** if the operator already demands evidence packets and the wiki's "what we miss" section is stale, R3 is wrong.

### Tier 2 — Medium leverage (improves consistency)

#### R4. Pre-load wiki before asking "what should we do"

- **Closes:** §3 (wiki pre-check under-use)
- **Bar enforced:** `P:/.claude/CLAUDE.md` "Look Up First" rule
- **Mechanism:** before asking the LLM "what should we do about X," run `/wiki query X` or grep the wiki manually. Many operator prompts ask questions the wiki already answers.
- **Effort:** 30 seconds per question.
- **Falsifier:** if the wiki doesn't actually answer the questions being asked, R4 is wrong.

#### R5. Make model-tier routing explicit in delegation packets

- **Closes:** §3 (cost-aware model tiering under-use)
- **Bar enforced:** `P:/.claude/CLAUDE.md` Cost Tiering principle
- **Mechanism:** every delegation packet specifies `model: haiku|sonnet|opus|minimax|zai` explicitly. The operator has the rule; live behavior shows ~1 explicit tier request in ~1021 prompts.
- **Effort:** One field per delegation.
- **Falsifier:** if the default model selection is already optimal for the operator's task mix, R5 adds overhead.

#### R6. Persist fleet status in the three-artifact form rather than narrating it

- **Closes:** §2.6 (fleet state narration not formalized)
- **Bar enforced:** `llm-handoff-best-practices.md` "Handoff vs plan vs status — the architecture"
- **Mechanism:** maintain `.artifacts/<termSafe>/plan-<planId>/status.jsonl` per the documented Option C. Read from it at session start rather than re-narrating.
- **Effort:** One-time setup per work stream; then near-zero.
- **Falsifier:** if the operator's manual narration is faster than reading a status file, R6 is wrong.

### Tier 3 — Lower leverage (quality elevation)

#### R7. Apply examples-over-rules to skills that underperform

- **Closes:** §2.5 (examples-over-rules documented but rarely applied)
- **Bar enforced:** `examples-over-rules-escape-hatch.md`
- **Mechanism:** when a skill keeps producing wrong output despite rule edits, curate 10-30 past outputs labeled with rationale, embed as few-shot examples.
- **Effort:** High per skill; rare trigger.
- **Falsifier:** if rule edits are catching every problem, R7 is unnecessary.

#### R8. Apply the subagent-synthesis spot-check rule to chat-level syntheses too

- **Closes:** generalizes the `subagent-synthesis → report gate` rule from subagent outputs to long LLM answers
- **Bar enforced:** the rule already exists for subagents
- **Mechanism:** before propagating a long LLM answer into a decision, spot-check it against one piece of evidence already in context.
- **Effort:** One verification per significant decision.
- **Falsifier:** if the operator already does this implicitly, R8 is unnecessary.

---

## 5. Internal tensions in the documented bar (for awareness)

These are not recommendations; they are tensions the operator should resolve when next editing the governance docs. From Lane 3:

- **T1.** "Trust over believability" vs "Self-review before shipping advice" — both demand scrutiny, but the cc-council incident showed self-review can structurally bypass trust-over-believability when the synthesis sounds right.
- **T2.** "Hook enforces, document provides context" vs "~50% Layer 1 compliance" — many "hard rules" in AGENTS.md are advisory; the constitution's claim assumes they can be enforced.
- **T3.** "Minimal fix and root cause" vs "Three-artifact handoff design" — the handoff architecture is decidedly non-minimal; the wiki's own reconciliation (line 268: "design at full architecture; collapse when work is small") is not codified as a binding rule.
- **T4.** "Mandatory Source-Authority Discovery" vs "Capability gap gate" — both fire on vague requests; order of application is unspecified.
- **T5.** "Examples over rules" vs "Skill-enforcement inline-content BEST fix" — the skill-enforcement wiki treats rules as the strong encoding; examples-over-rules treats them as the fallback.
- **T6.** "Cost runaway caps" vs "Context-rich handoffs require more tokens" — the documented handoff rigor burns the budget the cost caps protect.
- **T7.** "Drift audit before close is non-negotiable" vs "Auto-commit fail-closed concurrent" — unspecified coordination between audit ownership and commit ownership.

---

## 6. What the operator does well (do not change)

These are strengths visible in the data that align with both the documented bar and external best practices. Preserving these is as important as fixing gaps.

1. **Direct pushback on LLM suggestions** — catches anti-patterns in real time ("Why do we want to hard code 3 anywhere?"). Matches Anthropic's "add an adversarial review step" and exceeds it.
2. **Framing pushback** ("We have a bigger problem... strategic issue being missed") — refuses local optimization. Matches the operator's own `Minimal fix and root cause` rule.
3. **Meta-cognitive awareness of prompting as a skill** — "how do I prompt you next time so your answers are not limited?" External sources (xAI, Anthropic) endorse iterative prompting; the operator is already doing it.
4. **Iterative constraint-tightening** — 6 redesigns of `/agy`, each adding one constraint. External sources call this "iterative refinement"; the operator does it at architectural scale.
5. **Cost-awareness without length-obsession** — "Be efficient and use code if it will help save LLM costs" is more sophisticated than "be concise." Matches Anthropic's context-engineering guidance (just-in-time retrieval, not context dumps).
6. **Slash-command-driven interface** — binds the LLM to a contract before giving the task. Matches the operator's `skill-protocol.md` "Slash commands invoke the Skill tool immediately."
7. **Independence from Claude where possible** — "I want the grok skill so that we don't need to use claude skills" is a deliberate portability stance.
8. **Fleet narration** — even when not formalized, the operator maintains fleet awareness across sessions. External sources do not document an equivalent solo-fleet-director pattern.
9. **Naming trust loss rather than papering over it** — rare and valuable. Most human-AI corpora show performance of niceness; this operator does not.

---

## 7. Companion wiki links

- [[llm-handoff-best-practices]] — the master external-research doc
- [[skill-enforcement-layers]] — explains the ~50% Layer 1 compliance ceiling
- [[solo_operator_adr_best_practices]] — solo-specific decision documentation
- [[examples-over-rules-escape-hatch]] — when to switch from rules to examples
- [[multi-agent-correlated-errors]] — frame diversity, falsifier-gating, LLM-as-judge margins
- [[auto-commit-authority-isolation]] — the multi-terminal authority-isolation pattern
- `~/.grok/AGENTS.md` Hard rules — the subagent-synthesis spot-check gate
- `P:/.claude/CLAUDE.md` — constitution v9.0

## 8. Open questions for follow-up

1. **Does the 4-day sample generalize?** A follow-up could analyze prompts from a wider window once available. Pre-Grok-Build-adoption prompts are in a different store.
2. **Is the operator's reactive `/red-team` use actually catching every case proactive gating would?** Quantitative analysis of decisions made without red-team review vs decisions that later regressed.
3. **What's the assistant-side acceptance/rejection rate?** This page documents the operator's prompts; the assistant's response quality and the operator's reaction rate are a separate study.
4. **Does the examples-over-rules pattern actually produce better skill output in this codebase?** No A/B data exists; the wiki documents the pattern but not a measured outcome.
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
