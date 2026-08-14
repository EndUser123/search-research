---
title: "duf_alternatives_research_prompt.md"
date: "2026-01-25"
mode: "COPILOT"
uuid: "02057652-dbf9-4179-a21a-ace52a894953"
entry_count: 2
---

## Human

duf_alternatives_research_prompt.md

## Assistant

# DUF (Did You Forget?) – Multi‑Dimensional Expansion Report

## 1. Overview

DUF already embeds several powerful cognitive moves: premortem, inversion, second‑order thinking, adversarial imagination, boundary testing, dependency mapping, observability, assumption audits, reversibility, and value discovery. That is a stronger pre‑commit checklist than what most teams use.

The main gap is not “more of the same,” but **additional orthogonal lenses** drawn from safety‑critical engineering, reliability, and human factors. Those domains have spent decades formalizing exactly the problem you’re solving: “What are all the ways this can go wrong?”—under time pressure, with incomplete information, and fallible humans.

At a high level, the biggest missing dimensions are:

- **Structured failure mode taxonomies** (FMEA‑style): explicit enumeration of failure modes, effects, and causes for your change, not just free‑form imagination.[1][2][3]
- **Control-structure and state thinking** (STPA‑style): how your change affects control loops, feedback, and system state over time, including cascading software failures.[4][5][6][7]
- **Deviation/parameter thinking** (HAZOP‑style): systematic “guideword × parameter” scanning of inputs, environment, config, timing, and human actions.[8][9][10]
- **Top‑down hazard trees and barriers** (Fault Tree / Bowtie): visual or mental decomposition from “bad outcome” → intermediate events → basic causes and barriers.[11][12][13][14][15][16][17][18]
- **Human factors and cognitive bias checks**: explicit self‑interrogation of overconfidence, confirmation bias, fatigue, and tunnel vision.[19][20][21]
- **Data & state integrity, performance, and lifecycle considerations**: boundary/value testing is covered, but explicit attention to long‑lived data, migrations, concurrency, capacity, and upgrade paths is missing.[5][22][1]

The rest of this report:

1. Lists 5 alternative frameworks and what they add beyond DUF.  
2. Identifies missing dimensions in your current 10 checks.  
3. Proposes concrete new DUF checks.  
4. Adapts practices from aerospace, nuclear, and medical domains to a solo, CLI, pre‑commit workflow.  
5. Prioritizes what to adopt and research first.

***

## 2. Alternative Frameworks to Study (and How They Differ from DUF)

### 2.1 Summary Table

| Framework | Core Idea | Strength vs DUF | Solo‑Dev Adaptation |
| --- | --- | --- | --- |
| **TRIZ Anticipatory Failure Determination (AFD) / Predictive Failure Analysis** | Invert TRIZ problem‑solving to systematically invent ways the system could fail, then test which causes are real.[23][24][25][26] | Much more structured version of your “Pre‑mortem + Red Team + Inversion”; uses checklists and operators to make failure imagination exhaustive. | 1–2 minute micro‑AFD: “If I wanted to guarantee catastrophic failure of this change, what would I do?” then scan a short operator list. |
| **Software FMEA (Failure Mode and Effects Analysis)** | For each function/component, list potential failure modes, their effects, causes, and detection/mitigation strategies.[1][2][3] | Adds explicit taxonomy of failure modes (missing requirement, wrong timing, wrong value, no action, etc.), and considers severity and detectability, not just likelihood. | 3‑row FMEA snippet per commit: function → failure mode → effect → mitigation/observable. |
| **STPA / STPA SW‑SAF‑SEC** | Systems‑Theoretic Process Analysis treats accidents as control and feedback failures in a socio‑technical system; software‑focused variants add software failure taxonomy and cascading scenarios.[4][5][6][7] | Emphasizes control loops, unsafe control actions, and cascading software failures over time, including safety and security aspects. | “Mini‑STPA” lens: for each control your change touches, ask how it can give wrong/late/absent commands, and how feedback could mislead you. |
| **HAZOP / Software HAZOP** | Hazard and Operability Study: apply “guidewords” (NO, MORE, LESS, LATE, EARLY, OTHER THAN, etc.) to process parameters; includes variants for software and human error.[8][9][10] | Systematic deviation‑based scanning of parameters and operations; ensures you don’t miss classes of deviations (timing, configuration, human action). | Pick 2–3 key “parameters” for your change (input, config, job schedule) and run 3–5 guidewords mentally. |
| **Fault Tree Analysis & Bow‑Tie** | Fault Tree: top‑down Boolean decomposition from hazard to basic causes; Bow‑Tie: center hazard with threats on the left and consequences on the right, with barriers.[11][13][16][27][17][12][14][15] | Forces you to model combinations (AND/OR) of failures and visualize where you lack barriers; clarifies single points of failure. | Mental “bow‑tie sketch”: single bad outcome, 3–5 threats, 3–5 consequences, and which barriers your change weakens or removes. |

### 2.2 How They Differ Conceptually from DUF

- **DUF is a set of powerful questions; these frameworks are “grammars” of failure.**  
  DUF’s strength is cognitive variety; its weakness is that it relies on free recall. FMEA, STPA, HAZOP, and FTA encode decades of domain knowledge into **lists and structures** that force you to consider classes of issues you wouldn’t otherwise think of.[2][6][3][9][10][16][17][18][4][1][5][8]

- **Traditional safety methods separate: “What can fail?” vs “What are its effects?” vs “What barriers exist?”**  
  DUF’s questions partially blend these. Safety engineering insists on stepwise separation: mode → cause → effect → barrier → residual risk. That decomposition itself often surfaces blind spots.[3][13][16][27][1][2][11]

- **Human factors and bias mitigation are explicit elsewhere, implicit in DUF.**  
  Aviation/medical checklists and NASA safety guidance explicitly aim to mitigate human factors—fatigue, distraction, overconfidence—through structured prompts and sign‑off rhythms. DUF doesn’t yet have a “meta‑check” about your cognitive state.[28][29][30][31][22]

As a solo dev, you won’t apply full formal STPA or FMEA on every commit; but you can **harvest their compact, high‑leverage questions** and fold them into DUF.

***

## 3. Missing Dimensions in the Current 10‑Check DUF

Your existing checks cover:

- Failure imagination (Premortem, Inversion, Red Team)  
- Cascading impact (Second‑Order Thinking, Blast Radius)  
- Boundary conditions (Empty Test)  
- Dependencies (Blast Radius)  
- Observability (Observability)  
- Assumptions (Assumption Audit)  
- Reversibility (Rollback Sim)  
- Upside / value (Value Reveal)

Comparing these against safety‑critical and reliability frameworks reveals several gaps.

### 3.1 Failure Mode Taxonomy Gap

FMEA and Software FMEA distinguish **specific failure modes**, e.g. for a function or component:[1][2][3]

- No operation when required  
- Operation when not required  
- Wrong operation (wrong value, wrong target, wrong unit)  
- Operation at the wrong time (too early/late; too long/too short)  
- Missing requirement / behavior

Your Pre‑mortem + Inversion will sometimes hit these, but there is **no guarantee you scan each category**, especially “no operation” vs “wrong operation” vs “wrong time.” Structured software FMEA guidance explicitly pushes software engineers to think in these terms.[2][1]

**Why it matters:** Many subtle software failures are **functional absences** (a thing doesn’t happen) or **temporal misbehaviors** (it happens too soon/late), not just “wrong outputs.” Without a mini‑taxonomy, these are easy to miss.

### 3.2 Control Structure and State Evolution

STPA and its software extension STPA SW‑SAF‑SEC focus on **unsafe control actions** and how control loops fail over time: wrong/late/missing commands, bad feedback, and cascading failures in complex software.[6][7][4][5]

DUF’s “Blast Radius” and “Second‑Order Thinking” touch some of this, but:

- They don’t force you to think in terms of explicit **controllers, actuators, sensors, and feedback**.  
- They don’t ask: “How could this change cause a controller to issue the wrong action because of misleading feedback or incorrect internal state?”  
- They don’t emphasize **runtime evolution**—how a small invariant break might accumulate damage over hours or days.[5]

**Why it matters:** Your systems already have control‑loop characteristics (cron jobs, queues, retries, backoffs, watchdogs). Many catastrophic bugs arise not from single calls, but from **slow‑burn state corruption and mis‑coordinated control.**

### 3.3 Parameter Deviation & Environment

HAZOP and its software/human variants use guidewords like NO, MORE, LESS, AS WELL AS, PART OF, REVERSE, OTHER THAN, EARLY, LATE to systematically examine deviations of parameters and operations.[9][10][8]

In software HAZOP and Human HAZOP, analysts explicitly consider:

- Input parameters, configuration values, time and sequence, and human actions (wrong, omitted, late, mis‑ordered).[10][8][9]
- Environment and interfaces (OS, network, hardware, external APIs).[8][9][10]

Your “Empty Test” hits some input weirdness but:

- Doesn’t explicitly cover **config changes**, feature flags, environment variables, or external dependencies.  
- Doesn’t prompt you to consider **time‑based deviations** (too frequent, not frequent enough, late, early) or **human operation deviations** (you, as operator, making a mistake).  

**Why it matters:** Many production incidents are triggered by **config**, **scheduling**, or **deployment environment** deviations, not just code logic.

### 3.4 Top‑Down Hazard / Barrier Modeling

Fault Tree Analysis and Bow‑Tie both emphasize mapping:

- A specific **hazard** (e.g., “data loss in archive,” “job stuck in infinite loop”)  
- The **threats/causes** that can lead to it (left side of a bow‑tie; top tree and branches in FTA)  
- The **consequences** (right side of bow‑tie) and the **barriers** that should prevent/mitigate them.[12][13][14][15][16][27][17][11]

Your Premortem approximates this, but:

- You don’t explicitly separate **threats**, **consequences**, and **barriers**.  
- You don’t explicitly check whether your change **removes or weakens barriers** (e.g., simplifying logging, loosening assertions, making rollback harder).  

**Why it matters:** In high‑safety domains, degradation often occurs because changes silently **erode protective barriers**, not because they directly introduce the final failure.[13][16][27][17][11]

### 3.5 Human Factors & Cognitive Bias

Safety and engineering decision‑making literature emphasize that:

- Engineers systematically underestimate the impact of cognitive biases (overconfidence, confirmation, sunk cost, anchoring, fatigue).[20][21][19]
- Awareness + explicit prompts can reduce bias impact, especially when coupled with checklists and structured decision processes.[21][19]

Your Assumption Audit is about **content of beliefs**, not about **your own mental state:** fatigue, time pressure, tunnel vision, ego attachment to a refactor, or “I just want this commit done” mode.

**Why it matters:** As a solo dev, **you are the human factor**. All checklist structures ultimately aim to protect against your future self at 3 AM.

### 3.6 Data & State Integrity, Performance, and Lifecycle

From Software FMEA, NASA software safety guidance, and NASA coding/testing rules, recurring concerns include:[30][31][22][1]

- Persistent data integrity: migrations, repartitioning, idempotency, partial writes, backward compatibility.  
- Resource constraints and performance: worst‑case load, memory, CPU, disk, latency; loops executed 0,1,many,max‑1,max,max+1 times; extreme values of inputs.[31][22][30][1]
- Upgrade and rollback lifecycle: is there a safe path forward and back given partially updated systems and data?[32][22][30][31]

Your Empty Test + Rollback Sim + Blast Radius partially touch these, but not explicitly:

- You don’t have a **dedicated data/state lens**.  
- You don’t explicitly ask about **performance/scale** or about loops and control‑flow stress cases, which NASA emphasizes even at “minimal” safety levels.[22]

***

## 4. New Check Suggestions to Extend DUF

Below are concrete, CLI‑friendly checks to add as **new dimensions** or as refinements to existing ones. You can choose whether to add them as new numbered DUF items or as sub‑questions under existing ones.

### 4.1 Mini‑FMEA Check – “Explicit Failure Modes”

**Dimension:** Failure mode taxonomy (FMEA / Software FMEA).[3][1][2]

**Check text (mental template, 60–90 seconds):**

> For the main function or component I touched:  
> 1. What are the ways it could now **fail to act when needed** (no operation)?  
> 2. What are the ways it could **act when it shouldn’t** (spurious operation)?  
> 3. What are the ways it could **act incorrectly** (wrong value / target / unit)?  
> 4. What are the ways it could act at the **wrong time** (too early, too late, too long, too short)?

Write down at least one item per question before committing. This borrows directly from software FMEA guidance, which focuses on missing actions, incorrect actions, and timing errors.[1][2]

**Pairing:** This check logically pairs with **Pre‑mortem**, **Inversion**, and **Empty Test**.

### 4.2 Control Loop & State Evolution Check – “Mini‑STPA”

**Dimension:** Control structure, feedback, and cascading failures (STPA).[7][4][6][5]

**Check text:**

> 1. What “control loops” does this change touch? (Schedulers, queues, retries, state machines, user workflows.)  
> 2. For each, could this change cause:  
>    - The controller to send a **hazardous command** (or omit a necessary one)?  
>    - The feedback/signals to be **misleading** or delayed, so the controller acts wrongly?  
>    - The system to **stick in a bad state** or oscillate (retry storms, thrash, flapping)?

You don’t need a diagram; a quick mental pass is enough. This is a solo‑dev version of identifying unsafe control actions in STPA.[4][6][7][5]

**Pairing:** Natural companion to **Blast Radius** and **Observability**.

### 4.3 Parameter Deviation / Environment Check – “Mini‑HAZOP”

**Dimension:** Parameter and environment deviations (HAZOP, including software and human variants).[9][10][8]

**Check text:**

> For 2–3 key parameters or conditions (input payload, config, schedule, environment):  
> - What if this parameter is **NONE** (missing / null / disabled)?  
> - What if it is **MORE/LESS** than expected (too large/small, frequent/infrequent)?  
> - What if it is **EARLY/LATE** (job runs at wrong time; event order changes)?  
> - What if it is **OTHER THAN** expected (different format, API variant, OS, locale)?

This is directly inspired by HAZOP guidewords (NO, MORE, LESS, AS WELL AS, PART OF, REVERSE, OTHER THAN, EARLY, LATE).[10][8][9]

**Pairing:** Strengthens **Empty Test** and extends it to config/env/time.

### 4.4 Hazard/Barrier Check – “Mini Bow‑Tie”

**Dimension:** Explicit hazards, threats, barriers, and consequences (Bow‑Tie / FTA).[14][15][16][27][17][11][12][13]

**Check text:**

> 1. Pick **one worst‑case hazard** this change could contribute to (e.g., “irreversible data loss in archive”).  
> 2. List 3–5 **threats/causes** that could now lead to this (left side).  
> 3. List 3–5 **consequences** if it happens (right side).  
> 4. For each threat and consequence, ask:  
>    - What **barriers** (tests, checks, limits, alerts, approvals, rollbacks) exist today?  
>    - Did this change **weaken or remove** any of them?  
>    - Should I add a new barrier?

High‑hazard industries explicitly track barriers and layer of protection; your DUF currently doesn’t.[15][16][27][17][11][12][13][14]

**Pairing:** Deepens **Observability**, **Rollback**, and **Blast Radius**.

### 4.5 Human Factors & Cognitive Bias Check

**Dimension:** Cognitive biases, fatigue, and human error in engineering decisions.[19][20][21]

**Check text (ruthlessly honest, 20–30 seconds):**

> - Am I **rushing** this commit because I’m tired, frustrated, or want closure?  
> - Did I **ignore evidence** that contradicted my idea (logs, failing tests, prior incidents)?  
> - If another engineer I respect saw this change, what would they push back on first?

Engineering decision‑making studies suggest that awareness and structured prompts can reduce bias impact; students and engineers often show biased decisions when not explicitly prompted. Human factors work also warns about overconfidence and illusion of control in experts.[20][21][19]

**Pairing:** This is a meta‑check that should probably **always run**, like Premortem and Rollback.

### 4.6 Data & State Integrity Check

**Dimension:** Persistent data, backward compatibility, and state consistency (Software FMEA and NASA software safety guidance).[30][31][22][1]

**Check text:**

> 1. Does this change write, delete, or reinterpret **persistent data**? If so:  
>    - What happens to **old data** under the new code?  
>    - Can I safely **roll back** with partially migrated data?  
> 2. Could this change introduce **non‑idempotent behavior** (retries double‑process something)?  
> 3. If the process crashes mid‑way, is the state **left consistent enough** to recover?

NASA’s safety guidance and software FMEA emphasize data/state consistency, missing requirements, and single‑point failures in software behavior.[31][22][30][1]

**Pairing:** Naturally couples with **Rollback Sim** and **Blast Radius**.

### 4.7 Performance & Resource Stress Check

**Dimension:** Performance, capacity, and worst‑case execution paths (NASA testing guidance).[22][30][31]

**Check text:**

> - What is the **worst‑case input size / rate** this code might ever see in production?  
> - Have I considered loops executing 0, 1, many, max‑1, max, and max+1 times where relevant?[22]
> - Could this change cause **unbounded growth** in memory, disk, or queue length over time?

NASA recommends testing extreme values, all modes of each sensor, every branch, and loop extremes, even at minimal safety levels.[22]

**Pairing:** Extends **Empty Test** and **Second‑Order Thinking** into the performance domain.

***

## 5. Check Dependencies and Bundling

Some checks are more powerful when **always run together**; others cover overlapping ground and can be bundled.

### 5.1 Natural Bundles

1. **Hazard Triplet Bundle** – Premortem + Mini‑FMEA + Bow‑Tie  
   - Premortem: “It failed next week; what broke?” (narrative scenarios)  
   - Mini‑FMEA: “Explicitly, how can this function fail?” (mode taxonomy)  
   - Bow‑Tie: “Which barriers prevent that hazard today, and did I erode any?”  
   Together, this gives you **scenario imagination + categorical coverage + barrier analysis**.

2. **Operational Dynamics Bundle** – Second‑Order Thinking + Mini‑STPA + Performance/Resource Check  
   - Second‑Order: “Then what? And then what?”  
   - Mini‑STPA: “How do control loops and feedback go wrong over time?”  
   - Performance: “Under worst‑case load and loop extremes, does it still behave?”  
   This bundle covers **temporal, control, and load dynamics**.

3. **Interface & Environment Bundle** – Empty Test + Mini‑HAZOP + Data & State Integrity  
   - Empty Test: null/empty/zero  
   - Mini‑HAZOP: NONE/MORE/LESS/EARLY/LATE/OTHER THAN for parameters and environment  
   - Data/State: persistent data, migrations, idempotency  
   This ensures you hit **inputs, environment, and persistence** as orthogonal axes.

4. **Meta‑Cognition Bundle** – Assumption Audit + Human Factors/Bias  
   - Assumption Audit: “What did I assume without verifying?”  
   - Human Factors: “What about my current mental state and motivations?”  
   This explicitly distinguishes **assumptions about the system** from **assumptions about you**.

5. **Recovery & Observability Bundle** – Observability + Rollback Sim + Bow‑Tie  
   - Observability: “Will I know if this breaks?”  
   - Rollback: “How do I undo this change?”  
   - Bow‑Tie: “Which barriers am I relying on, and how will I know if they fail?”  
   Together, they cover **detect, respond, and recover**.

### 5.2 Always‑On vs Conditional Checks

Given your willingness to spend 5–10 minutes per commit, for non‑trivial changes (say >50–100 LOC or significant behavior change) you can reasonably treat the following as **always‑on**:

- Premortem  
- Mini‑FMEA  
- Blast Radius  
- Observability  
- Rollback Sim  
- Human Factors / Bias

Then, depending on the nature of the change:

- **Stateful / DB / migrations:** Data & State Integrity + Mini‑STPA  
- **New interfaces / configs / jobs:** Mini‑HAZOP + Performance/Resource  
- **Security‑sensitive:** Red Team + Bow‑Tie (with explicit security threats and barriers)

***

## 6. Industry Practices Adapted to Solo Dev

This section shows how practices from aerospace, nuclear, and medical domains can be scaled down into a CLI‑friendly, solo workflow.

### 6.1 Lessons from FMEA / Software FMEA

FMEA is a structured, stepwise approach to identify potential failure modes, their effects, causes, and recommended actions; Software FMEA focuses on software behavior and interfaces.[2][3][1]

Key adaptable ideas:

- **Focus on functions, not modules.** Software FMEA guidance recommends thinking in terms of functions (what the software should do) and interface behavior, not just files/classes. For DUF, that means: pick the **1–2 primary functions or flows** your change affects and run the Mini‑FMEA check against them.[1][2]

- **Missing requirements as a failure mode.** FMEA explicitly pushes you to ask “Is there a requirement missing?” not just “Does the requirement fail?” That maps to DUF’s **Value Reveal** + a new question: “What scenario is **still not handled** by this change that should be?”[2][1]

### 6.2 Lessons from STPA / STPA SW‑SAF‑SEC

STPA SW‑SAF‑SEC extends STPA with a software failure taxonomy and focuses on cascading software failures in autonomous systems.[6][7][4][5]

Key ideas for you:

- **Think in terms of unsafe control actions categories:** Too early, too late, out of sequence, not provided when needed, provided when not needed. Your Mini‑STPA check uses these categories implicitly.[5]

- **Explicitly link software behavior to system‑level hazards.** Even for non‑safety‑critical systems, you can identify a few “system‑level bad outcomes” (e.g., “large archive corruption,” “billing double‑charges users”) and trace how your software change might contribute. This is essentially Premortem + STPA framing.

### 6.3 Lessons from HAZOP / Software HAZOP / Human HAZOP

HAZOP has well‑developed guideword lists and has been adapted for software and human actions.[8][9][10]

Key ideas:

- **Use guidewords as a tiny library of “failure moves.”** A short list like NONE / MORE / LESS / LATE / EARLY / OTHER THAN can live in a text file you glance at during DUF. You already do this partially with Empty Test; formalizing it reduces dependency on memory.

- **Include human actions as parameters.** Human HAZOP treats human steps (clicks, commands, scheduling) as nodes subject to deviations (wrong person, wrong time, omitted, duplicated). As a solo dev/operator, that’s still relevant: “What if I run this migration twice? Forget a flag? Run it in the wrong environment?”[10]

### 6.4 Lessons from Fault Tree / NUREG‑0492 / Bow‑Tie

The Fault Tree Handbook (NUREG‑0492) and related NRC and DOE documents codify rigorous top‑down hazard analysis. Bow‑Tie methods present hazards, threats, consequences, and barriers in a single visual.[16][27][17][18][12][14][15]

Key adaptations:

- **Single‑hazard focus per commit.** You don’t need a large tree; just pick **one** serious hazard and ask for 3–5 basic causes and 3–5 consequences, then check barriers (Mini Bow‑Tie).

- **Implicit Boolean logic.** Even without diagrams, you can ask: “Does this hazard require **all** of these to happen (AND) or **any one** (OR)? Is my change making it more ‘OR‑like’ by removing redundancy?”

### 6.5 Lessons from NASA Software Safety & Medical Checklists

NASA’s software safety guidebook and associated checklists emphasize:[33][32][30][31][22]

- Comprehensive requirement identification and traceability.  
- Explicit classification of safety‑critical components and hazards.  
- Extreme‑value testing, full branch and path coverage where feasible, and strong coding rules (e.g., NASA’s “Power of 10”).[34][22]
- Checklists for verification, configuration management, and change impact analysis.[33][30][31]

WHO’s Surgical Safety Checklist has repeatedly shown reductions in complications and mortality by enforcing pre‑, intra‑, and post‑procedure checks.[29][28]

Adaptations for DUF:

- **Phase‑based DUF:** adopt a “Sign‑In / Time‑Out / Sign‑Out” rhythm for commits (pre‑code, pre‑commit, post‑deploy mental checks), inspired by surgical checklists.[28][29]

- **Ramp‑up on high‑criticality changes:** For large or risky refactors, temporarily **upgrade DUF to a more formal mode**: write a 1‑page FMEA snippet, do a more detailed bow‑tie, and verify extreme‑value tests before committing—similar to NASA raising rigor for safety‑critical parts.[30][31][22]

***

## 7. Prioritized Recommendations

Given your constraints (solo dev, CLI, pre‑commit, time‑tolerant), this is a pragmatic adoption sequence.

### 7.1 Phase 1 – Immediate, High‑Leverage Additions

1. **Add Mini‑FMEA to DUF.**  
   This is the single biggest improvement in **systematic failure‑mode coverage** for minimal extra time. It replaces “hope my premortem imagination hits everything” with a small, stable taxonomy.[3][1][2]

2. **Add Human Factors / Bias Check.**  
   As the sole decision‑maker, guarding against your own fatigue, overconfidence, and confirmation bias is critical. This check is cheap and addresses a class of failures that technical frameworks ignore.[21][19][20]

3. **Add Data & State Integrity Check.**  
   Your workload (large archives, transcripts, torrents) is data‑heavy; persistent state bugs are likely your highest‑cost failures. A dedicated state lens is justified.[31][30][1][22]

### 7.2 Phase 2 – Deepen Dynamic and Environmental Coverage

4. **Integrate Mini‑HAZOP with Empty Test.**  
   Replace “null/empty/zero only” with a small guideword list over inputs, config, and environmental parameters. This is an easy evolution of something you already do.[9][8][10]

5. **Integrate Mini‑STPA with Blast Radius.**  
   When asking “What depends on what I changed?”, also ask “What control loops and feedback paths did I alter, and how can they fail over time?” This makes your blast radius analysis **temporal and structural**, not just topological.[7][4][6][5]

6. **Add Performance & Resource Stress Check.**  
   Incorporate worst‑case input and loop extremes into your DUF, drawing from NASA’s emphasis on extremes and coverage.[30][31][22]

### 7.3 Phase 3 – Hazard/Barrier Modeling and Formalization

7. **Adopt the Mini Bow‑Tie check for high‑impact changes.**  
   Use it when you’re touching code that can affect availability, durability, or correctness at scale. It will help you spot barrier erosion and single points of failure.[27][17][11][12][13][14][15][16]

8. **Create a DUF “Intensive Mode” profile.**  
   For “Major” changes, define a profile that includes: Premortem, Mini‑FMEA, Mini‑STPA, Mini‑HAZOP, Bow‑Tie, Data & State, Performance, Human Factors, Observability, Rollback. Treat it like your personal NASA “elevated safety level” process.[31][30][22]

### 7.4 What to Research in Depth

If you want to go deeper into the theory behind each new lens:

1. **FMEA / Software FMEA** – structure and taxonomy of failure modes.[3][1][2]
2. **STPA and STPA SW‑SAF‑SEC** – control‑structure and cascading software failures.[4][6][7][5]
3. **TRIZ Anticipatory Failure Determination / Predictive Failure Analysis** – a more systematic extension of your premortem/inversion/red‑team cluster.[23][24][25][26]
4. **HAZOP (including software and human variants)** – guideword lists and adaptation to non‑process domains.[8][9][10]
5. **Fault Tree Handbook (NUREG‑0492) and Bow‑Tie introductions** – hazard trees, Boolean composition, and barrier thinking.[17][11][12][13][14][15][16][27]
6. **NASA Software Safety Guidebook and checklists; NASA’s Power of 10 rules and testing guidance** – for inspiration on coding rules and verification emphases.[32][34][33][30][31][22]

***

## 8. Putting It Together: DUF v2 as a Multi‑Dimensional Coverage System

Conceptually, DUF v2 would cover:

- **Scenarios & narratives:** Premortem, Second‑Order, Red Team, Value Reveal.  
- **Failure‑mode taxonomy:** Mini‑FMEA, Mini‑STPA (unsafe control actions).  
- **Parameters & environment:** Empty Test + Mini‑HAZOP.  
- **State, data, and performance:** Data & State Integrity, Performance/Resource.  
- **Structure, dependencies, hazards:** Blast Radius, Bow‑Tie.  
- **Detection & recovery:** Observability, Rollback Sim, Bow‑Tie barriers.  
- **Human cognition:** Assumption Audit, Human Factors/Bias.

That is roughly the solo‑developer analogue of how aerospace, nuclear, and medical domains layer FMEA, STPA, HAZOP, FTA/Bow‑Tie, and human‑factors checklists together for high‑reliability systems.[11][13][29][16][27][17][6][28][33][4][5][9][10][1][2][3][8][30][31][22]

You already have the discipline to run DUF regularly; the next step is to **codify these extra lenses into small, reusable prompts** in your pre‑commit script, transforming DUF from “10 good questions” into a compact personal safety‑engineering toolkit.

## Human

Are there repos that show something like duf?

## Assistant

Yes, there are a few categories of repos that are “DUF‑adjacent”:

They’re not doing your exact cognitive pre‑mortem, but they show how people embed *structured checklists* and *pre‑commit rituals* into their workflow.

Below are the closest fits.

***

## 1. Pre‑commit as a “programmable checklist”

### `pre-commit/pre-commit`

- Repo: https://github.com/pre-commit/pre-commit  
- What it is: Language‑agnostic framework for managing Git pre‑commit hooks via `.pre-commit-config.yaml`.[1][2]
- Why it’s DUF‑like: It treats pre‑commit as a **gate where a configurable set of checks must pass** before you’re allowed to commit. Most hooks are mechanical (lint, format), but nothing stops you from adding a custom hook that:
  - Prints DUF questions in the terminal
  - Blocks the commit unless you confirm you’ve mentally run through them

Useful as infrastructure for wiring DUF into your actual Git workflow.

### `dwyl/learn-pre-commit`

- Repo: https://github.com/dwyl/learn-pre-commit  
- Tagline: “Think of pre-commit as an automatic checklist for your code.”[3]
- Why it’s relevant: This repo explicitly frames pre‑commit as a **checklist concept**, with examples and guidance on setting up hooks. It’s more tutorial than framework, but good source material if you want to design a DUF hook and document it for future you.

### `git-precommit-checks` (npm package)

- Site: https://mbrehin.github.io/git-precommit-checks/  
- Repo (linked from docs): `mbrehin/git-precommit-checks` (on GitHub)  
- What it does: Config‑driven pre‑commit checker where each rule is a regex + message; non‑blocking vs blocking rules, summary output, etc.[4]
- DUF angle: Shows a **declarative rule list** for pre‑commit checks. You could adapt the model so that:
  - Some “rules” are mechanical (e.g., block `console.log`)
  - Some “rules” are cognitive prompts that always print (non‑blocking), nudging you through DUF before the commit proceeds

***

## 2. Explicit code review / self‑review checklists

These are the closest conceptual analogues to DUF: structured question lists intended to catch blind spots.

### `mgreiler/code-review-checklist`

- Repo: https://github.com/mgreiler/code-review-checklist  
- What it is: A large, structured checklist for code reviews covering implementation correctness, architecture, error handling, logging, performance, testing, readability, etc.[5]
- Why it’s DUF‑like:
  - It’s **purely question‑based**, like DUF, not a linter.
  - Sections like “Logic Errors and Bugs”, “Error Handling and Logging”, “Performance”, “Testing and Testability” map almost 1:1 to cognitive dimensions you care about.[5]
- How you could use it:
  - As raw material to expand DUF’s dimensions (e.g., add explicit “Error handling & logging” and “Performance” checks).
  - As a markdown checklist you run through pre‑commit for large changes.

### `trixi-framework/add-pr-review-checklist`

- Repo: https://github.com/trixi-framework/add-pr-review-checklist  
- What it is: GitHub Action that automatically injects a Markdown review checklist into new PRs; you keep `.github/review-checklist.md` in the repo.[6]
- DUF angle:
  - Demonstrates how to **attach a structured checklist to every code change** via automation.
  - Although it runs on PRs, you could mirror the pattern locally: a DUF markdown file + a script that prints it or requires “ack” before commit.

***

## 3. Generic pre‑commit hook collections

These aren’t cognitive frameworks, but they show idioms for building and distributing pre‑commit logic—useful if you decide to ship DUF as a hook repo.

### `pre-commit/pre-commit-hooks`

- Repo: https://github.com/pre-commit/pre-commit-hooks  
- What it is: A collection of common hooks (check AST, trailing whitespace, TOML/YAML syntax, large files, etc.).[7]
- Relevance:
  - Good reference on how to structure hook repos, IDs, config, messaging.[7]
  - You could publish `duf-pre-commit-hooks` in the same style, where one hook is “run DUF cognitive checklist”.

### `jumanjihouse/pre-commit-hooks`

- Repo: https://github.com/jumanjihouse/pre-commit-hooks  
- What it is: Another curated hook set (whitespace, shellcheck, markdownlint, etc.).[8]
- DUF angle:
  - Shows more advanced patterns (config via `.gitattributes`, integration with git core whitespace rules, etc.).[8]
  - Handy if you want DUF to coexist with other hygiene checks in one config.

***

## 4. “Checklist as a service” around code review

Not exactly DUF, but they show how checklists are integrated into PRs and workflows:

- **PR review checklist Action:** `trixi-framework/add-pr-review-checklist` (above) automatically adds checklists to PRs.[6]
- **Microsoft engineering playbook – code review checklists:** Not a repo per se, but used as markdown and integrated into review processes; good fodder for additional DUF questions.[9][10]

***

## 5. How to map these patterns to a DUF repo

If you’re thinking “what would a DUF repo look like?”, the closest combined pattern is:

1. **Core DUF spec** as markdown:
   - `docs/duf-checks.md` listing each cognitive check, with examples (similar to `code-review-checklist`).[5]

2. **CLI wrapper**:
   - A small `duf` CLI that:
     - Reads `git diff --cached`
     - Classifies change size (trivial/moderate/significant/major)
     - Prints only the relevant DUF questions, maybe in an interactive TUI.

3. **pre-commit integration**:
   - A `duf-pre-commit-hooks` repo modeled after `pre-commit-hooks` + `learn-pre-commit`, exposing a `duf-check` hook that runs your CLI and blocks commit on non‑zero exit.[2][1][3][7][8]

4. **Optional GH Action**:
   - A PR checklist action modeled after `add-pr-review-checklist`, which posts DUF‑inspired questions to PRs for bigger changes.[6]

None of the existing repos *are* DUF, but `code-review-checklist`, `learn-pre-commit`, `pre-commit` and `git-precommit-checks` together give you good templates for:

- Representing structured cognitive questions in markdown  
- Attaching them to commits / PRs automatically  
- Shipping them as a reusable tool rather than just a personal note file
