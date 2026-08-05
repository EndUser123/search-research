---
title: "Self-reflective gap discovery: indirect-hunting prompts for unknown-unknown detection"
created: 2026-08-05
source: session-2026-08-05 (/www research on self-reflection prompts + skill-dev Step 1.6)
tags: [self-reflection, gap-discovery, unknown-unknowns, pre-mortem, assumption-excavation, reference-class, blind-spot-detection, reusable-component, skill-design]
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
summary: >
  A reusable three-prompt pattern for finding issues that mechanical scanners
  cannot detect. Uses indirect-hunting techniques from blind-spot detection
  research (Klein pre-mortem, assumption excavation, reference-class forecasting)
  to surface unknown unknowns in any skill, pipeline, or workflow. The key
  insight: asking "what are you missing?" produces hedging; asking "imagine it
  failed — explain why" produces investigation. Designed to be embedded in any
  skill that wants self-improving gap discovery beyond its scanner checks.
relations:
  - target: wiki/concepts/skill-step-enforcement-architecture-grok-build.md
    type: complements — enforcement architecture + gap discovery = complete coverage
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: extends — operationalizes blind-spot techniques as reusable prompts
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: applies — scanner (code) + gap discovery (model judgment) = both layers
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related — gap discovery is the model-judgment layer that complements mechanical enforcement
---

# Self-reflective gap discovery: indirect-hunting prompts

## The component

Three open-ended prompts that find what scanners can't. Run after all
mechanical checks pass. Each prompt uses a different indirect-hunting
technique because direct introspection ("what are you missing?") produces
hedged, generic answers.

### Prompt 1: Assumption excavation

```
Complete this sentence 5 times: "This [skill/system/pipeline] works as long as ___."
The first two will be obvious. The last three are the load-bearing assumptions
nobody wrote down. If any of the last three is wrong, the scanner would not
catch it. Check each one.
```

**Why it works:** the sentence template constrains the model to
domain-specific assumptions rather than generic risk lists. "This works
as long as the referenced skill hasn't been renamed" is a real,
checkable assumption — not a platitude.

**Source:** assumption excavation from aerospace risk practice (1960s
"unk-unks"), documented in jpoindexter/blind-skills `blind-unknown-unknowns`.

### Prompt 2: Reference-class scan

```
Search the wiki for failure patterns relevant to this system's domain:
  grep pattern="<domain> failure|<domain> bypass|<domain> race|<domain> stale" path="P:/.data/wiki/concepts/"
  grep pattern="skill enforcement|activation gap|compliance|cross-skill" path="P:/.data/wiki/concepts/"

What documented failure mode does this system NOT defend against yet?
Focus on patterns matching this system's architecture.
```

**Why it works:** instead of asking the model to introspect (low signal),
it asks the model to look at external evidence (high signal). The wiki's
documented failures become free known-unknowns — the model discovers
patterns the system author never anticipated.

**Source:** reference-class forecasting (Flyvbjerg 2006; Kahneman outside view).

### Prompt 3: Pre-mortem bug report

```
Imagine it is 30 days from now. This [skill/system/pipeline] has failed in
production. The operator filed a bug report. Write the one-paragraph bug
report. What did the scanner miss?
```

**Why it works:** "What are you missing?" produces validation. "Imagine it
already failed — explain why" produces investigation. The temporal reframing
(past tense, already happened) bypasses the model's optimistic bias.

**Source:** Gary Klein pre-mortem (Klein 2007, "Performing a Project Premortem,"
Harvard Business Review). Also in blind-skills `blind-premortem`.

## How to use this component

### In skills with scanner checks

Add after all mechanical checks pass:

```markdown
## Gap discovery (runs after all checks)

The scanner catches known defect classes. It cannot catch unknown unknowns.
After all checks pass, run the three gap-discovery prompts from
[[self-reflective-gap-discovery-indirect-hunting-prompts]].

If any surfaces a new issue: add it as a finding AND consider whether it
should become a new scanner check, a refinement to an existing check, or
a documented limitation.
```

### In skills without scanner checks

Add as a self-reflection step at the end of the skill's procedure:

```markdown
## Self-reflection (before declaring done)

Before claiming completion, run the three gap-discovery prompts from
[[self-reflective-gap-discovery-indirect-hunting-prompts]]. These use
indirect-hunting techniques to find issues the skill's own steps don't
cover.
```

### In workflows (Rhai)

Add as the final phase — a read-only agent runs the three prompts against
the workflow's output:

```rhai
phase("Gap Discovery");
let gap_prompt = "Review the workflow output above. Complete 5 times: 'This workflow works as long as ___.'";
let gap_prompt += " Then search the wiki for failure patterns this workflow doesn't handle.";
let gap_prompt += " Then imagine it failed in production 30 days from now — write the bug report.";
let gap_result = agent(gap_prompt, #{ label: "gap-discovery", capability_mode: "read-only" });
```

## Why indirect framing matters

Research on LLM self-reflection (Reflexion framework, Shinn et al. 2023;
metacognitive prompting, Wang et al. NAACL 2024) shows:

- Direct introspection ("what went wrong?") is unreliable — LLMs produce
  plausible-sounding but generic explanations
- Indirect framing (pre-mortem, assumption completion, reference-class)
  constrains the model to produce specific, checkable answers
- The framing determines the quality of the output — not the model's
  inherent capability

This is the same principle as [[mechanical-enforcement-over-behavioral-reminder]]:
the structure of the prompt determines the reliability of the result.
Mechanical scanners are 100% reliable for known patterns. Indirect-hunting
prompts are the complementary layer for unknown patterns.

## Falsifier

This component is wrong if:
- The three prompts consistently produce the same answers across different
  skills (they're too generic to surface skill-specific gaps)
- The pre-mortem framing produces optimistic validation instead of
  investigation (the temporal reframing doesn't bypass optimism bias)
- The assumption hunt produces only obvious assumptions (the sentence
  template doesn't constrain to domain-specific depth)
- The reference-class scan is too noisy to be useful (the wiki has too
  many failure concepts for targeted retrieval)

## Receipts

- `~/.grok/skills/skill-dev/SKILL.md` Step 1.6 (lines 354-390) — implementation of the three prompts as a skill-dev step
- `~/.grok/skills/skill-dev/__lib/script_scan.py` — the scanner that the gap discovery complements (11 mechanical checks)
- `~/.grok/skills/tp/SKILL.md` operator-catch block — the same indirect-framing principle (surfacing model uncertainty for operator verification)
- Klein (2007) "Performing a Project Premortem" — source of the pre-mortem technique
- `github.com/jpoindexter/blind-skills` — source of the assumption excavation and unknown-unknowns frameworks

## Sources

- Klein, G. (2007). "Performing a Project Premortem." Harvard Business Review.
- jpoindexter/blind-skills: `blind-unknown-unknowns`, `blind-premortem` — agent skill implementations
- Flyvbjerg, B. (2006). "From Nobel Prize to Project Management." International Journal of Project Management.
- Shinn, N. et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS.
- Wang, Y. et al. (2024). "Metacognitive Prompting Improves Understanding in Large Language Models." NAACL.
- [[blind-spot-detection-methods]] — workspace concept on blind-spot techniques

## What this means for our workspace

1. **Embed in skill-dev Step 1.6** (already done) — runs after scanner checks
2. **Embed in ship-py and ship-rhai** — add gap discovery as final phase
3. **Reference from other skills** — any skill that produces durable output
   can link to this concept and run the three prompts as a self-reflection step
4. **The scanner grows from findings** — each gap discovered can become a
   new scanner check, making the mechanical layer smarter over time

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[self-improving-agent-systems-techniques-and-workspace-gaps]]
- [[skill-graph]]
- [[self-reflection-in-llms-fails-without-external-evidence]]

