---
title: "Blind-spot detection methods — what works, what we have, what we lack"
created: 2026-07-26
source: session-20260726 (/www research on blind-spot detection)
tags: [blind-spots, cognitive-bias, pre-mortem, devils-advocate, reference-class-forecasting, red-team, decision-making, research]
summary: >
  Five evidence-backed techniques for detecting cognitive blind spots: pre-mortem (imagine failure, work backwards), devil's advocate / red team (assigned dissenter), outside view / reference class forecasting (compare to similar past cases), bias blind spot awareness (the meta-bias of thinking you're less biased than others), and Structured Analytic Techniques like Analysis of Competing Hypotheses. The workspace already implements devil's advocate via /tp two-lens and /design critical friend; it lacks reference class forecasting and adaptive (non-fixed-checklist) blind-spot scanning. Each technique has documented limitations: pre-mortem and red team can become performative under social pressure; reference class forecasting requires a comparable reference class; outside view is hard when the situation is novel. No technique is a complete defense — the literature recommends layering multiple techniques because each catches a different bias class.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://en.wikipedia.org/wiki/Bias_blind_spot (Wikipedia, 2026)
  - https://www.mountaingoatsoftware.com/blog/use-a-pre-mortem-to-identify-project-risks-before-they-occur (Mountain Goat Software / Gary Klein lineage)
  - https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/biases-in-decision-making-a-guide-for-cfos (McKinsey, CFO biases guide)
  - https://nationalsecurityjournal.nz/wp-content/uploads/sites/13/2024/10/NSJ-2024-October-Shewring.pdf (Shewring 2024, devil's advocacy in intelligence)
  - https://corporate.jasoncollins.blog/outside-view (Jason Collins, reference class forecasting explainer)
  - https://apps.dtic.mil/sti/pdfs/AD1045908.pdf (Landry, red team adoption analysis)
relations:
  - target: wiki/concepts/extract-moves-not-conditions-tp-enhancements.md
    type: related
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: related
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: related
---

# Blind-spot detection methods

## Decision context

**Why this research was needed:** session 019f9bfe produced unusually high-quality output. The operator asked "what allowed it?" — the answer surfaced the role of operator catches and fresh-lens subagents in catching blind spots. The follow-up question: how do people *in general* look for blind spots? This is a "what does the field know that we should know?" question — the workspace has built up several blind-spot defenses (two-lens critique, critical friend, AAR Q11, /tp session FILTER) but hasn't surveyed the broader literature to check what's missing.

The gap in knowledge: is the workspace's approach (mostly devil's advocate + checklists) the best the field offers, or are there major techniques we haven't implemented?

## Five evidence-backed techniques

### 1. Pre-mortem (Gary Klein, popularized by McKinsey)

**What it is:** after a plan is drafted but before implementation, the team imagines it has failed catastrophically. Each person writes down *why* it failed. The imagined-failure frame makes it psychologically safe to surface doubts that would feel disloyal as direct criticism.

**Why it works (the mechanism):** the technique exploits an asymmetry in cognitive ease. Imagining failure and working backwards is cognitively easier than defending a plan against direct criticism — there's no social cost to "the plan failed because..." because everyone is role-playing the same hypothetical. This bypasses the conversational pressure that suppresses dissent in real-time meetings. The frame also forces *concrete* failure modes ("the integration broke at week 3 because...") rather than vague worries.

**Evidence:** Klein's original work; McKinsey's "Bias Busters: Premortems" recommends it specifically for confirmation bias and excessive optimism. The age-of-product.com source calls it out for "spot blind spots, foster psychological safety, and collaborate across functions." Dropbox's virtual-first toolkit includes a structured 5-step pre-mortem format.

**Workspace mapping:** `/design` Step 5.5 critical friend includes a falsifier question ("what would make this design wrong?"); `/risks` includes a pre-mortem specialist lens; `/aar` Phase 4 asks "what was the best earlier stop, reframe, or recovery point?" These are partial implementations — Klein's full technique is a *structured group exercise*, not a single question.

**Limitations:** the technique depends on the team being willing to imagine failure honestly. Under strong leadership pressure, pre-mortems can become performative (token objections that don't challenge the real plan). For solo operators (our case), the group-exercise structure collapses — the value comes from the *frame*, not the group dynamics. See [[extract-moves-not-conditions-tp-enhancements]] for the principle: extract the move (the imagined-failure frame), leave the condition (the group setting).

### 2. Devil's advocate / red team (military, intelligence, McKinsey)

**What it is:** a designated person or team is assigned to argue the opposite of the leading proposal. The role can be permanent (military red teams, intelligence "Revision Departments") or rotational (devil's advocate for one decision).

**Evidence:** Shewring (2024) documents Israel's AMAN Revision Department as a permanent devil's advocate unit. McKinsey's CFO guide recommends "red team–blue team activity for large investments" — explicitly expensive, reserved for high-stakes decisions. The Medium article on multi-agent AI mirrors this architecture for LLM systems.

**Limitations (Shewring 2024, Landry DTIC analysis):**
- Cultural acceptance is critical — if leadership treats the devil's advocate as obstructionist, the role becomes theater. Shewring's case study of Israel's AMAN shows the unit was effective *because* leadership protected its independence; in other agencies without that protection, similar units became captured by consensus.
- Can hamper collaboration if not properly scoped — Landry's DTIC analysis found directional (top-down) leadership styles get less value from devil's advocacy than participative styles, because the advocate's objections are filtered through the leader's prior.
- Effectiveness depends on the advocate having genuine independence from the proposing team. This is the structural property the `/tp` two-lens architecture tries to preserve — and the property that collapsed in session 019f9bfe when glm-5-2 was spawned on a glm-5-2 parent (same model = same training priors = same lens). The fix is genuine cross-family model diversity, not just "a different subagent."

**Why this matters for AI agent fleets specifically:** a fleet of LLM agents using the same model family has the same training-prior blind spots. A devil's advocate drawn from the same family shares those blind spots. Cross-family spawning (glm vs mimo vs nemotron) is the AI-agent-fleet equivalent of "genuine independence" — and it's fragile because quota and serialization failures push the pool back toward parent-inherited spawns. The workspace's `/tp` pool table (SKILL.md lines 340-365) is the structural defense, but it depends on the operator catching attribution failures in real time (as happened in session 019f9bfe).

### 3. Outside view / reference class forecasting (Kahneman & Lovallo)

**What it is:** instead of forecasting from the specifics of the current case (the "inside view"), identify a *reference class* of similar past cases and use their statistical distribution of outcomes as the forecast. Kahneman's cure for the planning fallacy.

**Evidence:** Lovallo & Kahneman (2003); Flyvbjerg et al. (2016, arxiv 1710.09419) — reference class forecasting removes optimism bias and strategic misrepresentation in cost/time predictions. McKinsey's CFO guide endorses it.

**Limitations:**
- Requires a comparable reference class — hard for genuinely novel situations. Kahneman's own caveat: the reference class must be chosen carefully, and the choice is itself a judgment call subject to bias. Pick too narrow a class and you've recreated the inside view; pick too broad and the forecast is meaningless.
- Tends to be ignored because the inside view *feels* more informative. Kahneman documents this as the "inside view temptation" — decision-makers consistently prefer the specifics of the current case over the statistical base rate, even when the base rate is more accurate.
- "Reference class" selection is itself a judgment call subject to bias. Flyvbjerg's solution is to use externally-validated reference classes (industry benchmarks, regulatory databases) rather than self-selected ones — but those don't exist for most software-engineering decisions.

**Why this is the workspace's biggest gap:** the wiki has accumulated ADR-style decisions (`qmd-patch-durability-strategy`, `coupling-inventory-as-mandatory-design-section`, etc.) but doesn't track their *resolved outcomes*. Without outcome data, there's no reference class to forecast from. A `/decide <proposal>` skill that queried past decisions AND their outcomes (6 months later: was the decision right?) would close this gap — but it requires a decision-outcome log that doesn't exist yet.

### 4. Bias blind spot awareness (Pronin, Lin, Ross 2002)

**What it is:** the meta-bias of recognizing bias in others while failing to see it in oneself. Simply knowing about it doesn't fix it — Pronin's research showed that teaching people about bias blind spot didn't reduce their own susceptibility. The structural defense is *external* review (someone else catches your bias), not self-awareness.

**Evidence:** Wikipedia's "Bias blind spot" article and the underlying Pronin et al. (2002) research. The PMC review (2021) confirms that even professionals (medicine, finance, law, engineering) systematically under-detect their own biases.

**Limitations:** this isn't really a *technique* for detecting blind spots — it's the *reason* self-applied checklists are structurally weaker than external review. It validates the Costa & Kallick "cannot refocus your own glasses" principle that drives `/tp`'s two-lens design. Pronin's research found that even after being taught about bias blind spot, participants continued to rate themselves as less biased than average — knowledge alone doesn't fix it. The only reliable defense is *structural*: route claims through an external reviewer (a fresh subagent, a cross-model pass, an operator catch) who doesn't share your training priors. This is why the workspace's `/aar` has a mandatory cross-model audit (SKILL.md line 260) and `/tp` has a model pool — both are structural responses to bias blind spot, not awareness-based responses.

### 5. Structured Analytic Techniques (SATs) — esp. Analysis of Competing Hypotheses (Heuer)

**What it is:** Richards Heuer's ACH (Analysis of Competing Hypotheses) forces the analyst to enumerate multiple hypotheses, then evaluate *each piece of evidence* against *each hypothesis* (not just the leading one). The matrix structure prevents confirmation bias from privileging the favored hypothesis.

**Evidence:** referenced in Shewring (2024) as complementary to devil's advocacy. Widely adopted in the US intelligence community post-Iraq-WMD-intelligence-failure as one of the Structured Analytic Techniques (SATs) that the CIA's Richards Heuer Jr. championed. The technique forces evidence-by-evidence evaluation rather than hypothesis-first reasoning.

**Limitations:** time-intensive; requires discipline to actually evaluate evidence against non-leading hypotheses (the temptation to skip is itself a confirmation-bias signal). For LLM agents specifically, ACH has an interesting application: forcing the model to enumerate alternative explanations for a finding before fixing on one prevents the "first plausible cause = the cause" failure mode that `/why` Step 11a tries to catch.

**Workspace mapping:** `/why` Step 11a "competing explanations" requires ≥1 alternative with evidence for/against — this is a partial ACH implementation (require alternatives, but not the full evidence × hypothesis matrix). The full matrix discipline would be valuable in `/design` (force enumeration of design alternatives before selecting one) and `/review` (force enumeration of alternative causes for a code issue before fixing on one). Currently both skills leave this to the writer's/reviewer's discretion, which the literature says is insufficient — discretion is exactly where confirmation bias reasserts itself.

## How the techniques layer (the literature's recommendation)

No single technique catches all bias classes. The literature (McKinsey CFO guide, Heuer's SATs, Kahneman) recommends layering multiple techniques because each catches a different failure mode:

- **Pre-mortem** catches optimism bias and unspoken doubts
- **Devil's advocate** catches confirmation bias and shared-prior blind spots (when genuinely independent)
- **Reference class forecasting** catches the planning fallacy and inside-view overconfidence
- **Bias blind spot awareness** explains *why* self-applied techniques are insufficient (it's the meta-justification for layering, not itself a detection technique)
- **ACH** catches confirmation bias at the evidence-evaluation step

The workspace layers pre-mortem + devil's advocate + partial ACH + bias-blind-spot-awareness. The missing layer is reference class forecasting. Adding it would complete the mainstream stack — but the prerequisite (a decision-outcome log) doesn't exist. The decision is whether the gap is worth closing now or whether the existing four-layer stack is sufficient for the workspace's current decision volume.

## What the workspace already has

| Technique | Workspace implementation | Strength of implementation |
|---|---|---|
| **Pre-mortem** | `/design` Step 5.5 critical friend includes a falsifier question; `/risks` includes pre-mortem specialist; `/aar` asks "what was the best earlier stop, reframe, or recovery point?" | Strong — multiple skills |
| **Devil's advocate** | [[extract-moves-not-conditions-tp-enhancements|`/tp` two-lens]] (fresh subagent); `/design` Step 5.5 critical friend; `/risks` specialists | Strong — but operator caught a real attribution failure (glm-5-2 on glm-5-2 parent = same-lens) in session 019f9bfe. The structural property depends on actually different models. |
| **Bias blind spot awareness** | Acknowledged in `~/.grok/AGENTS.md` § "Claims require receipts"; `/why` Step 4b evidence-tier system; [[coupling-inventory-as-mandatory-design-section]] enforces mechanical gates | Medium — the principle is documented; the structural defense (external review) is what `/tp` provides |
| **Reference class forecasting** | **None** | **Gap** — no skill explicitly asks "what was the outcome of similar past decisions?" |
| **Structured Analytic Techniques (ACH)** | `/why` Step 11a "competing explanations" partially implements ACH (enumerates alternatives, requires evidence for/against); `/tp` disconfirmation gate | Partial — present in `/why`, not consistently applied elsewhere |

## Receipts (workspace mechanism claims)

Claims about workspace skill implementations, labeled by inspection status:

- **`/aar` Q11 blind-spot sub-check is mandatory within `/aar`** — [OBSERVED] `~/.grok/skills/aar/SKILL.md` lines 313-325, "Blind-spot sub-check (mandatory within Q11)" with three named gap types (unstated decisions, operator-flagged items, failed approaches). Inspected this session.
- **`/close` auto-invokes `/aar` when the Retrospective gate is `needs_attention`** — [OBSERVED] `~/.grok/skills/close/SKILL.md` line 123: "Retrospective (needs_attention when substantive work happened without a valid, session-bound AAR completion receipt): auto-invoke /aar — do not recommend it, run it." The AAR (including its Q11 blind-spot sub-check) IS auto-fired on session close when substantive work happened. Originally mis-stated as a gap in the first draft of this concept; corrected after operator pushback. The 2026-07-22 close-summary incident (close SKILL.md line 365) is what motivated making `/aar` mandatory within `/close`.
- **`/tp` two-lens architecture depends on actually different models** — [OBSERVED] session 019f9bfe incident: glm-5-2 spawned on glm-5-2 parent was same-lens; the fresh-lens property collapsed. The /tp pool table at SKILL.md lines 340-365 documents the model-attribution requirement.
- **No workspace skill implements reference class forecasting** — [INFERENCE] based on this session's `/wiki` query (no matching concept) and review of skill catalog. Would require a focused `/preflight`-style audit to confirm definitively.
- **`/why` Step 11a partially implements ACH** — [OBSERVED] `~/.grok/skills/why/SKILL.md` Step 11a "competing explanations" requires ≥1 alternative with evidence for/against. Full ACH (matrix of evidence × hypotheses) is not implemented; this is the partial-implementation claim.

## What the workspace lacks (the actual gaps)

Three gaps surface from the literature review:

1. **No reference class forecasting.** No skill asks "for this kind of decision (refactor / dependency swap / new skill design), what was the distribution of outcomes across prior similar decisions in this workspace?" This would require either a decision-outcome log or a wiki query against past decisions with their resolved outcomes. The wiki has the *decisions* (ADR-style concepts) but not the *outcomes* (were they right?). Closing this gap would mean adding a "retrospective outcome" field to ADR concepts and a `/decide` skill that consults them.

2. **`/aar`'s Q11 blind-spot sub-check fires on session close when substantive work happened** (via `/close` auto-invoking `/aar` — close SKILL.md line 123). This is well-covered, not a gap. The actual gap is that `/close`'s auto-`/aar` invocation depends on the Retrospective gate firing `needs_attention` — sessions where the gate logic judges the work as non-substantive skip `/aar` entirely. Whether that gate-calibration is correct is a separate question from whether the structural connection exists.

3. **No skill forces enumeration of competing hypotheses outside of `/why`.** ACH-style discipline would help in `/design` (force the writer to enumerate design alternatives before selecting one) and in `/review` (force the reviewer to enumerate alternative causes for a finding before fixing on one). Currently this is left to the writer's/reviewer's discretion.

## What this means for our workspace

- **The `/tp` two-lens architecture is the workspace's strongest blind-spot defense** and is well-aligned with the literature on devil's advocate and bias blind spot. The session 019f9bfe incident (model attribution failure collapsing the fresh-lens property) is a real risk that the literature predicts: devil's advocate fails when the advocate isn't genuinely independent. Shewring (2024) documents this exact failure mode in intelligence agencies where the "devil's advocate" unit became captured by the consensus it was supposed to challenge.
- **The biggest gap is reference class forecasting.** If a future skill improvement is warranted, a `/decide <proposal>` skill that greps the wiki for similar past decisions and surfaces their outcomes would close the largest missing technique. The prerequisite is a decision-outcome log — currently the wiki has ADR-style *decisions* but not their *resolved outcomes* (were they right?). Without outcomes, there's no reference class to forecast from.
- **The `/aar` Q11 blind-spot sub-check IS auto-fired on session close** via `/close`'s Retrospective gate (close SKILL.md line 123). This was incorrectly identified as a gap in the first draft of this concept; corrected after operator pushback. The actual smaller question is whether the gate's `needs_attention` calibration is correct (does it fire on the right sessions?), not whether the structural connection exists.
- **Pre-mortem, devil's advocate, and bias-blind-spot-awareness are well-covered** by existing skills. Don't add more — the literature says layer multiple techniques, not stack many copies of one. Adding a second devil's-advocate skill would compete with `/tp` and `/risks`; better to extend what exists.
- **ACH (Analysis of Competing Hypotheses) is only partially implemented** in `/why` Step 11a. The full ACH discipline (evidence × hypothesis matrix) would help in `/design` (force alternative design enumeration) and `/review` (force alternative cause enumeration before fixing on one). This is a candidate `/design` and `/review` enhancement, not a new skill.

## Falsifier

This entry is wrong if, within 12 months:
- **Reference class forecasting is added and proves low-value** (the gap wasn't real — inside-view decisions in this workspace don't suffer optimism bias because the operator catches it). Mitigation: prototype before committing; the prototype would need a decision-outcome log that doesn't exist yet, so the prototype cost is the gating factor.
- **The literature is superceded by newer research** showing one of the five techniques is ineffective. Mitigation: revisit if a major replication failure hits any of the cited sources. The Pronin et al. (2002) bias blind spot research and Kahneman/Lovallo (2003) outside view are the most-cited; a replication failure of either would be high-signal.
- **A workspace-specific blind-spot class emerges that none of the five techniques catches** (the field is incomplete). Counter: that would itself be a finding worth capturing as a new wiki concept. The five techniques surveyed here are the established mainstream; emerging techniques (prediction markets, superforecasting training, AI-assisted bias detection) may close gaps the current five don't.
- **The workspace's existing defenses prove sufficient without adding RCF or full ACH.** This would mean the literature's recommendations don't apply to solo-operator + AI-fleet contexts. Plausible — the workspace already layers devil's advocate (multiple skills), pre-mortem (multiple skills), bias blind spot awareness (multiple rules), and partial ACH (`/why` Step 11a). Adding more might be redundant. The honest test: track whether unresolved blind spots recur across the next 6 months. If they don't, the existing layer is sufficient.

## Sources

- [Bias blind spot](https://en.wikipedia.org/wiki/Bias_blind_spot) (Wikipedia, 2026) — Pronin, Lin, Ross (2002) lineage; the meta-bias of under-detecting own biases.
- [Use a Pre-Mortem to Identify Project Risks](https://www.mountaingoatsoftware.com/blog/use-a-pre-mortem-to-identify-project-risks-before-they-occur) (Mountain Goat Software, Gary Klein lineage) — the imagined-failure technique.
- [Biases in decision-making: A guide for CFOs](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/biases-in-decision-making-a-guide-for-cfos) (McKinsey) — red team–blue team for high-stakes; pre-mortem for confirmation bias.
- [The Application of the Devil's Advocacy Technique to Intelligence Analysis](https://nationalsecurityjournal.nz/wp-content/uploads/sites/13/2024/10/NSJ-2024-October-Shewring.pdf) (Shewring, NSJ 2024) — Israel's AMAN Revision Department case study; cultural-acceptance limitations.
- [The outside view](https://corporate.jasoncollins.blog/outside-view) (Jason Collins blog, Kahneman/Lovallo lineage) — reference class forecasting explainer.
- [An analysis of the formal adoption of red teaming](https://apps.dtic.mil/sti/pdfs/AD1045908.pdf) (Landry, DTIC) — limitations of devil's advocate under different leadership styles.
- [Reference Class Forecasting (Flyvbjerg et al.)](https://arxiv.org/pdf/1710.09419) (2017) — RCF removes optimism bias and strategic misrepresentation in project forecasting.
- [The Impact of Cognitive Biases on Professionals' Decision-Making](https://pmc.ncbi.nlm.nih.gov/articles/PMC8763848/) (PMC 2021) — even professionals under-detect own biases across medicine, finance, law, engineering.
