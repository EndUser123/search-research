---
title: "AI thought-partner / critical-friend: industry expectations and the Now-Next-Later timeframe continuum"
created: 2026-07-23
source: session-2026-07-23 (/www research on thought-partner skills and timeframe framing)
sources:
  - https://digileaders.com/using-ai-as-a-critical-friend-redefining-strategic-leadership/
  - https://www.aakashg.com/now-next-later-roadmap/
  - https://www.linkedin.com/pulse/from-echo-chamber-critical-friend-using-ai-reflect-salinas-frencia-zvwic
  - https://hbr.org/2025/09/ai-is-changing-the-structure-of-consulting-firms
  - https://lile.duke.edu/caradite/ai-student-survey/ai-as-a-thought-partner/
  - https://hbr.org/2025/10/5-critical-skills-leaders-need-in-the-age-of-ai
  - https://fortune.com/2025/12/12/ai-skills-gap-talent-executives-fear-risk-critical-strategic-thinking/
tags: [thought-partner, critical-friend, strategic-advisor, now-next-later, prioritization, roadmap, tp, timeframe-continuum]
agent: grok
host: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  The industry is converging on "AI as critical friend" (Costa & Kallick
  1993) as the dominant frame for AI advisory interactions. Six capabilities
  define what practitioners want: challenge assumptions, offer alternatives,
  stress-test logic, ask provocative questions, respect context, and create
  psychological safety. Our /tp implements all six. The timeframe continuum
  practitioners use is Now-Next-Later (popularized by Intercom): immediate
  execution (Now), validated-but-unscoped (Next, 1-3 months), and strategic
  backlog (Later, 3+ months). /tp currently answers all three timeframes but
  doesn't name the horizon — adding a horizon tag would help the operator
  calibrate the depth of the critique to the commitment level.
relations:
  - target: wiki/concepts/mental-models-for-tp-and-brainstorming
    type: extends
  - target: wiki/concepts/llm-defensiveness-under-pushback-structural-fix
    type: related
---

## What the industry thinks should be in a thought-partner / critical-friend AI

Source: Digital Leaders (Prof. Alan Brown, AI Director, Oct 2025); HBR (Sep 2025); Duke University survey; Fortune (Dec 2025).

### The six capabilities practitioners want

| Capability | What it means | In /tp? |
|---|---|---|
| **Challenge assumptions** | Don't accept the framing; probe the premises | ✅ Core domain 4 (anchoring) + disconfirmation slot |
| **Offer alternatives** | Surface options the user didn't consider | ✅ Core domain 5 (solution-space broadening) |
| **Stress-test logic** | Trace consequences to where they break | ✅ Core domain 2a (second-order thinking) |
| **Ask provocative questions** | Not advice — questions that reframe | ✅ Step C (each finding is a provocative question, not a judgment) |
| **Respect context** | Advocate for success, not adversarial | ✅ Posture: advocate, not adversary (Step 2.5) |
| **Create psychological safety** | Challenge without undermining competence | ✅ Advocate posture + matter-of-fact tone (Boundaries §2) |

**Assessment: /tp covers all six.** The Costa & Kallick (1993) definition — "a critical friend is a trusted person who asks provocative questions, provides data to be examined through another lens, and offers critiques as a friend" — is the foundational citation in our SKILL.md.

### What practitioners say they want that /tp added this session

| Want | /tp enhancement added |
|---|---|
| "What am I missing?" (from HBR, Instagram practitioners) | Information asymmetry section (Step D) |
| "Is this really right, or am I fooling myself?" | Self-rationalization check (Step D) |
| "What would change my mind?" | Disconfirmation slot + pre-mortem + steelman |
| "Is this the optimal long-term answer?" | Core domain 2 (optimal long-term vs. simplicity) |

### What the industry warns about (disconfirmation pass)

1. **Homogenization risk** — if everyone uses the same AI frameworks, strategy diversity shrinks (Digital Leaders, Oct 2025). [REFUTED for our use case: /tp generates cross-model critique via the spawn pool, which introduces diversity by design]

2. **Emotional tone-deafness** — AI doesn't know what it feels like to deliver bad news (Inc. Magazine). [QUALIFIED: /tp doesn't address this; it's a reasoning tool, not an emotional-intelligence tool. The operator provides the emotional judgment.]

3. **Over-reliance reducing critical thinking** — Fortune (Dec 2025): "AI is exposing a critical thinking gap." [QUALIFIED: our /tp explicitly forces the user to verify findings (Step 3 verification + novelty + integration checks) rather than accepting subagent output unchecked]

## The timeframe continuum: Now-Next-Later

Source: Aakash Gupta (ex-Google/Meta PM, Oct 2025); Intercom; NN/g (Nielsen Norman Group).

### The framework practitioners use

| Horizon | Timeframe | Commitment | What the question means | How /tp currently handles it |
|---|---|---|---|---|
| **Now** | Current sprint/cycle | High — actively building | "What should I do right now?" | ✅ Standard /tp — immediate critique of current work |
| **Next** | 1-3 months | Medium — validated but unscoped | "What should we prepare for?" | ⚠️ Handled but not named — /tp doesn't distinguish "is this the right next step?" from "is this the right thing to do now?" |
| **Later** | 3+ months | Low — strategic backlog | "Where is this going?" | ⚠️ Handled but not named — /tp's pre-mortem (domain 3a) covers long-term failure, but doesn't frame the answer as roadmap-level |

### How people like to ask

From the search results, practitioners use these phrasings:

| Phrasing | Horizon | Frequency in results |
|---|---|---|
| "What should we do next?" | Now → Next | Most common (HBR, LinkedIn, Instagram) |
| "Be my strategic advisor" | Next → Later | Common for strategic planning (HBR, Oracle) |
| "What am I missing?" | All horizons | Very common — crosscuts timeframes |
| "What decisions need to be made?" | Now | CAYK Marketing framework emphasis |
| "Is this the right direction?" | Later | Less common — implies roadmap-level |

### The gap /tp has

/tp treats all these as the same question type — a critique request. But they have different commitment levels and different depth requirements:

- **"What should I do right now?"** needs immediate, actionable critique — skip the pre-mortem, skip the steelman, focus on correctness and the next action
- **"What should we do next quarter?"** needs solution-space broadening + prioritization criteria — the discovery questions are most valuable here
- **"Where should this be in 6 months?"** needs pre-mortem + second-order thinking + information asymmetry — the full depth

**Recommendation:** Add an optional `horizon=now|next|later` parameter to /tp that adjusts which mandatory domains run. Default = all (current behavior). The parameter would let the operator calibrate depth to the question's commitment level.

## Decision context

**Why this research was needed:** The operator noticed that their "/tp what's next?" and "/tp what should we do?" questions span a continuum from immediate tactical to long-term strategic, and asked how others frame it and whether /tp handles it.

**What alternatives were explored:** McKinsey three-horizons model (too enterprise-focused), Eisenhower Matrix (task-level, not strategic), RICE scoring (prioritization, not critique). Now-Next-Later (Intercom popularization) is the dominant product-management frame and maps cleanly to /tp's domain.

**What the research changed:** Identified that /tp covers all six industry-expected capabilities and all three timeframes — but doesn't name the timeframe, which would help calibrate depth. The `horizon=` parameter recommendation is a future enhancement, not an immediate gap.

## Falsifier

If the Now-Next-Later framework doesn't improve /tp outcomes (operators don't use the `horizon=` parameter, or it doesn't change which domains fire), remove it and keep /tp as a unified-depth critique tool.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
