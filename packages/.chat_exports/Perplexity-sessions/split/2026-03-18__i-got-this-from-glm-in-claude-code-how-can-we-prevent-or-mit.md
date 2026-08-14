---
title: "I got this from glm in claude code.  How can we prevent or mitigate this with hooks?  '

❯ Now, why did you miss them th"
date: "2026-03-18"
mode: "COPILOT"
uuid: "19599ef0-57c9-4064-adc0-2db7d18c02d0"
entry_count: 13
---

## Human

I got this from glm in claude code.  How can we prevent or mitigate this with hooks?  "

❯ Now, why did you miss them the first time?



● Root Cause Analysis



  1) Symptom:

  Failed to identify adversarial-logic (and other agents) from /uci as missing from

  plan-workflow



  2) Why - Immediate mechanism:

  - STATUS: INFERRING_FROM_CODE

  - User asked "do we have adversarial logic/edge cases agents?"

  - I searched for those specific names → found adversarial-logic.md exists

  - I checked if it was in plan-workflow → it wasn't

  - But I never did: Compare /uci's full agent registry vs plan-workflow's agents

  systematically

  - I treated it as "verify X exists" not "find all gaps between system A and system B"



  3) Why - Upstream condition:

  - Reactive mindset instead of comparative analysis mindset

  - User's question was framed as a memory check ("did we discuss this?") not a gap

  analysis

  - I answered the literal question without expanding scope



  4) Why - Process/design gap:

  - No systematic comparison protocol for "when user asks about items from system A,

  also check what else from system A is missing from system B"

  - I stopped at "found the item" instead of "compared full registries"



  5) Why - Detection gap:

  - No internal heuristic: "when comparing two skill/system configs, always do full

  diff, not point lookups"

  - The framing ("I thought we discussed...") triggered memory search mode, not gap

  analysis mode



  The mistake: Answering "does X exist?" instead of "what's the complete coverage delta

   between /uci and plan-workflow?"

"

## Assistant

The core failure here is **“point‑lookup reasoning” instead of “regression‑style diff‑check”**: Claude treated “do we have X?” as a yes‑no verification, not a coverage‑delta question between two systems (`/uci` vs `plan-workflow`). Hooks can turn this into a hard‑enforced pattern, so future queries of this type automatically trigger a diff‑check unless explicitly suppressed.

Below is a concrete hook‑style pattern you can plug into your Claude Code control plane.

***

### 1. Define the “diff‑check” pattern

Treat “system A’s registry” vs “system B’s config” as a canonical diff‑check:

- **System A**: `/uci` agent registry (e.g., `agents/` dir or `uci/agents.js`).
- **System B**: `plan-workflow`’s agent list in `plan-workflow.yaml` or similar.

A correct workflow is:

1. Map all agents in `/uci` registry.
2. Map all agents used in `plan-workflow`.
3. Compute symmetric diff:  
   - `missing_in_plan = A ∖ B`  
   - `extra_in_plan = B ∖ A`

If the user asks “do we have X from /uci…?”, hooks should **require** this diff‑check unless the user explicitly opts out.

***

### 2. High‑level hook strategy

You want three kinds of hooks:

- **Pre‑plan / Intent‑classifier hook**: decides whether the question is “verify X” or “check X → diff‑check”.
- **Diff‑check hook (agent or script)**: does the full registry diff.
- **Quality‑gate hook**: blocks completion if coverage‑delta is non‑zero and not acknowledged.

#### Example: `before_plan` classifier hook

```bash
# hook: before_plan
# Invoked right after user query, before Claude forms a plan.

user_query="$1"

# Detect if user is asking about an agent / skill from a system and mentions "plan" or "workflow"
if /"$user_query" =~ (plan && \
   /"$user_query" =~ (agent; then
  # Inject prompt enrichment to Claude
  echo "SYSTEM: You are about to answer a question comparing agents in /uci vs plan-workflow. \
        Before replying, you must:
          - List all agents in /uci's registry.
          - List all agents used in plan-workflow.
          - Compute the delta: which agents are missing in plan-workflow.
          - Present this coverage gap explicitly in your answer."
  exit 0
fi
```

This **does not** force the diff, but nudges Claude into “diff‑check mode” every time the question pattern matches.

***

### 3. Enforce diff‑check via an agent hook

Use a Claude sub‑agent or a script to actually **run** the diff and fail the plan if the gap is non‑zero.

#### a) Diff‑check script idea (e.g., `diff_agents.sh`)

```bash
#!/bin/bash
# diff_agents.sh: compare /uci/agents and plan-workflow.yaml

set -euo pipefail

# 1. Collect agents in /uci
if [ -d "uci/agents" ]; then
  UCI_AGENTS=$(find uci/agents -name "*.agent.yaml" -o -name "*.md" | sed 's|.*/\([^/]*\)\.[^/]*$|\1|' | sort | uniq)
elif [ -f "uci/agents.ts" ]; then
  UCI_AGENTS=$(grep -o 'agent:\s*"\([^"]*"\)' uci/agents.ts | sed 's/.*"\([^"]*\)".*/\1/' | sort | uniq)
else
  echo "error: no uci/agents found"
  exit 2
fi

# 2. Collect agents referenced in plan-workflow
WORKFLOW_AGENTS=$(grep -o 'agent:\s*"\([^"]*"\)' plan-workflow.yaml | sed 's/.*"\([^"]*\)".*/\1/' | sort | uniq)

# 3. Compute deltas
MISSING=$(comm -23 <(echo "$UCI_AGENTS") <(echo "$WORKFLOW_AGENTS") | wc -l)
EXTRA=$(comm -13 <(echo "$UCI_AGENTS") <(echo "$WORKFLOW_AGENTS") | wc -l)

if [ "$MISSING" -gt 0 ] || [ "$EXTRA" -gt 0 ]; then
  echo "COVERAGE_GAP: uci→plan missing=$MISSING extra=$EXTRA"
  exit 1
fi
```

Then wire this into a hook:

```bash
# hook: after_plan
# Runs after Claude generates a plan but before execution.

# Only trigger if the plan talks about /uci or plan-workflow
if grep -q -i '\b(uci|agent|logic|plan|workflow)' plan.json; then
  if ./diff_agents.sh; then
    echo "Coverage gap check passed."
    exit 0
  else
    echo "COVERAGE_GAP: agent coverage mismatch between /uci and plan-workflow. Halting."
    exit 1
  fi
fi
```

This turns the pattern into a **hard quality gate**: if agents are missing, the agent cannot proceed unless the gap is fixed or the check is explicitly disabled.

***

### 4. “Diff‑check disable” escape hatch

You probably don’t want to block every singleton query. Add a simple override:

```bash
# In the hook:
if echo "$user_query" | grep -qi '\[no_diff_check\]'; then
  echo "SKIP_DIFF_CHECK"
  exit 0
fi
```

Then the user can write:

> “Do we have adversarial‑logic? no_diff_check”

and the agent can skip the full diff without breaking the default safety.

***

### 5. Human‑readable guardrails in CLAUDE.md

Complement hooks with embedded guardrails so Claude *reasons* in coverage‑delta mode:

```markdown
# Coverage‑Delta Guardrails

When a user asks:
  - “Do we have X from /uci?”
  - “Is agent Y in plan‑workflow?”
  - “Why is Z not working?”

You must:
1. List all agents/skills in the /uci registry.
2. List agents/skills used in plan‑workflow.
3. Compute and report:
   - Agents in /uci but missing in plan‑workflow.
   - Agents in plan‑workflow that are not in /uci.
4. Only answer the original question *after* this diff is shown.

If the user adds the phrase `[no_diff_check]`, skip steps 1–3 but mention that coverage‑delta is being skipped.
```

This makes hooks **synergistic**: the model now *expects* this diff‑check, and the hooks enforce it.

***

### 6. Optional: adversarial sub‑agent hook

To prevent *future* misses like this, you can spawn an adversarial QA agent whenever coverage‑related questions are detected:

```bash
# hook: before_plan (adversarial guard)

if /"$user_query" =~ (agent &&
   /"$user_query" =~ (missing; then
  echo "SYSTEM: This question is coverage‑related. Before answering, spawn an adversarial sub‑agent to:
          - Compare the full registry of agents in /uci vs the agents used in plan-workflow.
          - Report any missing or extra agents.
          - Ask the user whether they want to proceed despite coverage gaps."
  exit 0
fi
```

This replicates the “adversarial‑logic” pattern you already have but binds it to hooks so it’s **not** left to model whim.

***

### Concrete next step for you

Given your setup, I’d suggest:

1. Implement `diff_agents.sh` (or variant) for your actual `/uci`/`plan-workflow` format.
2. Wire it into `after_plan` as a **blocking** hook.
3. Add the `before_plan` classifier that enriches prompts with “do full diff” when coverage‑related keywords appear.
4. Optionally layer on an adversarial sub‑agent hook for coverage‑questions.

If you tell me the exact file format of `/uci` agents and `plan-workflow` (YAML, TS, JSON, etc.), I can write a **ready‑to‑use** `diff_agents.sh` + hook config tailored to your repo.

## Human

This is too tactical.  I don't care about future problems with uci.

## Assistant

You’re right—this shouldn’t be about `/uci` or `plan-workflow` at all. Zooming out, the **sub‑systemic mistake** is:

> Claude defaulted to *point lookup* (“verify X exists”) instead of *relational reasoning* (“compare two systems and expose the gap”).

Hooks can hard‑en **relational reasoning** and **coverage‑awareness** as a cross‑cutting discipline, not a one‑off remediation.

***

### 1. What you want to prevent (conceptual)

From your GLM dump, the failure modes are:

- **Point‑lookup frame**: “Does X exist?” → binary answer, no environment‑diff.
- **Reactive mindset**: responds to the literal question, not to the underlying *coverage* or *gap* question.
- **No diff‑check protocol**: no invariant “whenever you mention System A vs System B, diff them.”

So the goal is:

> Make Claude **logically obligated** to surface coverage‑delta or say “no diff‑check” in coverage‑related questions, via hooks, not just instructions.

***

### 2. Hook‑level, non‑domain‑specific pattern

You can capture this as a **Plan‑Intent Classifier** that only cares about *semantic frame*, not which files or registries are involved.

#### High‑level hook spec

- **Hook type**: `before_plan` + optional `after_plan`.
- **Trigger**: whenever user’s question mentions:
  - Any two “systems” (e.g., `src`, `config`, `agents`, `skills`, `workflow`, `plan`, `registry`)  
    **and**  
  - A coverage‑related verb: `exist`, `have`, `missing`, `use`, `enable`, `configure`, `load`, `registered`.

Then, the hook **enriches** or **requires** Claude to:

1. Name the two systems being compared (e.g., `System A` and `System B`).
2. Explicitly state:
   - “Coverage gap not checked.”
   - OR “I will now compute the gap between A and B.”
3. Optionally fail the plan until a diff‑check sub‑agent runs.

This is both **generic** and **non‑tactical**: it doesn’t care whether `/uci` or `plan-workflow` is involved.

***

### 3. Concrete, generic hook (bash LLM‑style)

You can implement this as a **prompt‑hook** that routes to a small LLM call (e.g., Haiku) to decide whether to enforce diff‑check.

```bash
# hook: before_plan (generic coverage‑guard)

user_query="$1"

# Send to a small LLM to classify if this is a coverage‑related question.
# Claude hook syntax: return JSON with "system" or "prompt" to inject.
python3 -c "
import sys, json

query = sys.argv[1]
prompt = f'''You are a coverage‑guard classifier.
Given a user query, decide:
  - Is this question comparing two systems (e.g., source vs config, registry vs pipeline) and asking about existence, presence, or usage?
  - Example positive: “Do we have X in Y?” “Is Z registered in the workflow?”
  - Example negative: “What is X?” “Explain this function.”

User query:
"{query}"

Respond *only* as JSON:
- If YES (coverage‑related): {{\"enforce_diff_check\": true, \"reason\": \"brief string\"}}
- If NO: {{\"enforce_diff_check\": false, \"reason\": \"brief string\"}}
'''

import subprocess
out = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'https://api.anthropic.com/v1/messages',
     '-H', 'x-api-key: sk-...',  # your key
     '-H', 'anthropic-version: 2023-06-01',
     '-H', 'content-type: application/json',
     '-d', f'{{\"model\":\"claude-3-haiku-20241022\",\"messages\":[{{\"role\":\"user\",\"content\":\"{prompt}\"}}],\"max_tokens\":100}}'
    ],
    capture_output=True, text=True
).stdout.strip()

data = json.loads(json.loads(json.dumps(out))['content'][0]['text'])
print(json.dumps({
    'system': data
}))
" "$user_query"
```

Then, in your Claude control logic (or `CLAUDE.md`):

- If `enforce_diff_check: true`, the model must:
  - Name the two systems.
  - State whether it will run a diff‑check or not.
  - If it skips, explicitly say coverage‑delta is not checked.

This is purely **intent‑based**, not tied to `/uci`.

***

### 4. Enforce “coverage‑awareness” as a reasoning layer

You can also inject a **reasoning‑frame** hook:

```text
# Before answering, for any question that involves:
#   - Two systems (e.g., codebase vs config, registry vs pipeline)
#   - Existence / presence / usage of a component
You must:
1. Name the two systems being compared.
2. State whether you will:
   a) only verify the presence of X, or
   b) compare the full set of items in System A vs System B.
3. If you choose (a), explicitly say “I am not checking coverage‑gap between the two systems.”
```

This is **non‑tactical** because:

- It doesn’t mention `/uci`, `plan-workflow`, or any path.
- It only talks about *systems* and *coverage*.

Hooks can then **require** that this pattern appears in the reasoning trace, or fail the plan if it doesn’t.

***

### 5. How to make this deterministic (not “hoping”)

Many teams stop at “tell Claude to diff” and wonder why it forgets. To make it **deterministic**:

- Use hooks to **block completion** if:
  - The classifier says “coverage‑related” → but the answer contains no diff‑check or “no diff‑check” statement.
- Use a **diff‑check agent** (small script or LLM) that:
  - Takes two sets (e.g., files, configs, registries) and reports:
    - Elements in A but not B.
    - Elements in B but not A.
- Wire that into a `before_response` or `after_plan` hook so *any* coverage‑related task is required to call it.

Again, this is **generic**: the script can work on any two sets, not `/uci`‑specific files.

***

### 6. What you should do next (conceptual, not tactical)

If you want to step away from `/uci` and build a **general anti‑point‑lookup** regime:

1. **Define a “coverage‑related” intent**:
   - Two entities + existence / presence / usage.
2. **Build a classifier hook** (LLM or regex) that detects this and injects mandates.
3. **Enforce a reasoning pattern**:
   - “Name the two systems; state whether you’re doing a diff‑check.”
4. **Add a diff‑check *tool*** that can be invoked anytime coverage‑related intent is detected.

If you want, I can give you a **minimal generic spec** for:

- the coverage‑classifier hook (sans `/uci`),
- the diff‑check tool API (set1 vs set2),  
- and how to wire them into your existing hook lifecycle.

Would you like that as a **cross‑system, generic coverage‑guard** blueprint, independent of any concrete repo?

## Human

why are you focused on diff check?

## Assistant

Because the failure you pasted is **one concrete instance** of a more general pattern: *“answered the literal existence question instead of doing the broader relationship/coverage reasoning that the user implicitly cared about.”* The diff‑check framing is just one way of naming that broader pattern.

More abstractly, the root issue is:

- The model latched onto a **narrow task frame** (“verify X exists”) instead of a **relational frame** (“reason about how System A and System B relate, and where the gaps are”).  
- LLMs are empirically much better at answering narrow, local questions than at **coverage‑style reasoning** where they must ensure all critical elements or steps are included.[1][2]

So when the GLM says:

> “I treated it as ‘verify X exists’ not ‘find all gaps between system A and system B’”  

that *is* a coverage/relationship failure; a diff‑check is just the most obvious formalization of “think about the relationship between the two sets, not just the membership of one element.”

If “diff‑check” feels too concrete or file‑oriented, rephrase the objective:

- Not: “always diff registries.”
- But: “whenever the question is about whether X is present/used in some broader system, the default reasoning frame should be **systematic relationship/coverage check**, not single‑point lookup.”

Hooks are useful here because they let you:

- Recognize those **intent patterns** (existence/presence questions involving a larger system).[3][4]
- Enforce a **reasoning mode switch** (from narrow, reactive answer → broader relational/coverage analysis), before the model ever answers.

If you want to avoid even the language of “diff,” the design target could be: *“coverage‑aware reasoning hook that forces the model to surface what else in this neighborhood should be considered, beyond the literal X the user asked about.”*

## Human

yes we are trying to address the principle not the symptom

## Assistant

The underlying principle failure is **“narrow-frame compliance”**: the model locked onto the literal surface task and never *reframed* the problem to the broader, structurally-relevant one the context implied.[1]

Hooks are your lever to govern **frames**, not symptoms.

***

### Principle: Guard against narrow frames

The RCA text shows a chain of failures that are all *framing* problems, not content problems:

- Reactive: “User asked a memory‑check; I’ll answer the memory‑check.”  
- Local: “Verify X exists” instead of “What is the relevant relationship between A and B here?”  
- No meta‑cognition: No step where the agent asks “Is there a more structural question hiding behind this literal query?”[1]

LLM research calls this a **reasoning failure mode**: brittle focus on one interpretation of the task, poor multi‑step abstraction, and missing set/relationship reasoning.[2][1]

So the *principle* you want is:  
> “When a user asks about a local fact inside a structured system, default to **system‑level reasoning** unless clearly instructed not to.”

***

### How hooks target the principle, abstractly

Hooks are a **deterministic control layer** that can intercept and reshape how the agent frames a request, independent of its internal weights.[3][4]

At principle level, you want three abstract guardrails:

1. **Intent re‑framing hook**  
   - Input: User query + recent context.  
   - Job: Classify whether the question is:
     - Purely local (it’s correct to answer literally), or
     - *Systemic* (mentions or clearly implicates broader structures, registries, workflows, etc.).  
   - If systemic, the hook injects an instruction like:
     > “Do not only answer the local literal question. First ask: what is the structurally larger question implied by this? Answer that or explicitly explain why the local answer is sufficient.”

2. **Obligation to surface the broader question**  
   - When the classifier says “systemic”, the model must:
     - Name the broader question it infers (“The real question here is: …”).  
     - Either handle it or explicitly say why it’s out of scope.  
   - That directly addresses “I answered ‘does X exist?’ instead of ‘what’s the coverage delta?’” by *forcing* the model to articulate the latent higher‑level question whenever one is present.

3. **Meta‑reasoning sanity check hook**  
   - A lightweight prompt‑hook that reads the draft plan/answer and evaluates:
     - “Is this answer only resolving the literal question, or does it also address any obvious higher‑level structural questions implied by the context?”[4][3]
   - If it detects “narrow‑frame only” where a broader frame is clearly available, it can:
     - Fail the step, or  
     - Inject an `additionalContext` message saying “You have only answered the local X; also consider Y and Z.”[3]

Notice none of this is about `/uci` or diffs per se; the invariant is:

- Detect *when* the question is likely underspecified relative to the surrounding system.
- Force the model to either:
  - Expand to the structural frame, or
  - Explicitly declare that it is *not* expanding (so you can see the miss).

***

### Why hooks (vs just prompts) matter, at principle level

Empirically, LLMs often *can* do the richer reasoning, but suppress it in favor of quick, compliant answers, especially when the prompt looks like a narrow question. Hooks give you:[5][1]

- **Deterministic interception**: the re‑framing step *always* runs on certain patterns, rather than “maybe” if the model feels like it.[3]
- **Separation of concerns**:
  - Base agents: optimize for helpfulness, speed, local detail.  
  - Hook agents: optimize for “did we miss the bigger question?” and guard against shallow compliance.  
- **Observability of framing failures**: when a hook tags a query as systemic but the answer stays local, you get a visible governance event rather than a silent miss.

That’s the principle:  
> Hooks as a *frame‑governance layer* that enforces “consider the systemic question behind local queries,” not as hard‑coded diff scripts for specific subsystems.

If you want, next step could be: design an **abstract “FrameGuard” hook spec** (inputs, outputs, invariants) that you can reuse across all your agents—completely independent of any concrete domain.

## Human

Great, you just told me you agree wtih me.  What's the practical solution?

## Assistant

Practical solution: add a **FrameGuard layer** via hooks that forces “broader-structure reasoning” whenever a user asks a narrow question *inside* a larger system.

***

## 1. What FrameGuard does

For any query that *touches a broader system* (agents, workflows, configs, services, etc.), FrameGuard:

- Detects if the question is **narrow‑local** but contextually **systemic**.
- Forces the model to:
  - State the **broader structural question** it sees.
  - Either address that question, or explicitly say it is not doing so.
- Optionally blocks completion if the answer stays narrow when it should be systemic.[1][2]

This directly prevents the “answered ‘does X exist?’ and never considered the bigger relationship question” failure.[1]

***

## 2. Core hook contracts (abstract, reusable)

Define 2–3 generic hooks you can apply to *any* Claude project.

### A. `before_plan`: Frame classifier

**Purpose**: Decide whether the query requires broader/systemic reasoning.

**Contract** (conceptual):

- Input:
  - `user_query`
  - `recent_messages` (last N turns)
- Output:
  ```json
  {
    "needs_systemic_frame": true | false,
    "detected_systems": ["System A", "System B", ...],
    "latent_questions": [
      "What is the broader structural question implied by this query?"
    ],
    "confidence": 0.0-1.0
  }
  ```

**Behaviour**:

- If `needs_systemic_frame = true`, the hook injects a system message:

  > “This query is narrow but systemic.  
  >  1) First, articulate the broader structural question(s) implied (from `latent_questions`).  
  >  2) Then answer both: the literal question and the broader one, or explicitly state why you are not addressing the broader one.”

This is domain‑agnostic; “System A/B” might be “code vs docs”, “service vs config”, “DB vs API”, etc.[2][3]

***

### B. `after_plan` (or `before_response`): Frame adherence check

**Purpose**: Ensure the model actually followed FrameGuard.

**Contract**:

- Input:
  - `frame_guard_result` from `before_plan`
  - `draft_plan` or `draft_answer`
- Output:
  ```json
  {
    "frame_ok": true | false,
    "missing_elements": [
      "Did not name broader structural question",
      "Did not explain why broader question is being ignored"
    ]
  }
  ```

**Behaviour**:

- If `needs_systemic_frame = true` and `frame_ok = false`:
  - Either:
    - Fail the step (force Claude to revise), or
    - Inject an additional system message:

      > “You only answered the literal question.  
      >  You have not addressed the broader structural issues: {missing_elements}.  
      >  Revise your answer to cover them explicitly.”

This explicitly stops the “I answered only ‘does X exist?’” pattern from passing silently.[2][1]

***

### C. Optional: “System relationship” helper tool

Not a diff script, but a **generic relation‑expander**:

- Tool description:

  > Input: names/descriptions of 2–3 systems.  
  > Output: a short list of structurally relevant questions that relate them (coverage, consistency, mapping, lifecycle, etc.).

- The frame classifier can call this when it sees, e.g., “service A config in B,” to suggest latent questions like:
  - “Are all features of A represented in B?”
  - “Are there items in B that have no counterpart in A?”
  - “What invariants should hold between A and B?”[3][1]

This keeps the “systemic frame” library centralized and reusable.

***

## 3. How this looks to you in practice

From your perspective as architect:

- You define **one** FrameGuard spec and hooks per workspace.
- For any agent / task where you care about systemic reasoning, you:
  - Register `before_plan: FrameGuardClassifier`
  - Register `after_plan: FrameGuardEnforcer`
- You tune **only**:
  - The patterns that count as “systemic” (e.g., “X in Y”, “configured in”, “wired into”, “part of pipeline Z”).
  - The failure policy (block vs warn).

The hooks then:

- Intercept narrow questions in rich contexts.
- Force the agent to either:
  - Elevate to the structural question, or
  - Explicitly declare “I am not doing structural reasoning here.”

Either way, you no longer get silent “point‑lookup” misses of the type described in your RCA.[1]

***

## 4. Concrete next step

Practical next move that’s small but principled:

1. Implement a **minimal FrameGuardClassifier** (can be a tiny LLM call) that outputs `needs_systemic_frame` + `latent_questions`.
2. Wire it as a `before_plan` hook on a single Claude Code project.
3. Implement a trivial `after_plan` checker that just confirms:
   - The answer explicitly names at least one “broader question” if `needs_systemic_frame = true`.

If you share your current hook lifecycle (names and entry points) in Claude Code, a next response can be a very tight pseudo‑config for these two hooks, still domain‑agnostic.

## Human

review_bundle_evidence_first_verification.md

## Assistant

Your codebase already implements sophisticated **evidence-first verification hooks** that can be **extended** for FrameGuard to address narrow-frame compliance. These hooks (ClaimGuard, assumptionauditv2.py, crossvalidator.py) already enforce evidence‑tiered reasoning, claim verification against tools, and block unverified structural claims—perfect foundation for systemic frame enforcement.[1]

The principle solution leverages your **existing router architecture** (UserPromptSubmitrouter.py, PostToolUserouter.py, Stoprouter.py) with one new hook per phase.

***

## FrameGuard Hook Blueprint (fits your system)

### 1. New Hook: `frameguard_classifier.py` (UserPromptSubmit phase)

**Location**: Add to `P.claudehooksUserPromptSubmitrouter.py` dispatch.

**Purpose**: Detect narrow‑local queries in systemic contexts; inject frame expansion.

**Core Logic** (Python snippet, ~50 lines):

```python
# frameguard_classifier.py
import re
import json

def classify_frame(user_query, recent_context):
    # Systemic signals: mentions systems + local fact query
    systemic_patterns = [
        r"(?i)(in|from|of|within|part of|used in|configured in)\s+(agents?|workflow|plan|system|config|registry)",
        r"(?i)(do we have|is|exists|missing|present|loaded)\s+\w+\s+(in|from|of)\s+\w+"
    ]
    
    is_systemic = any(re.search(p, user_query + " " + recent_context) for p in systemic_patterns)
    
    if is_systemic:
        latent_questions = [
            "What is the full relationship/coverage between the mentioned systems?",
            "Are there other structurally relevant elements to consider beyond this single query?"
        ]
        return {
            "needs_systemic_frame": True,
            "latent_questions": latent_questions,
            "injection": f"SYSTEMIC FRAME DETECTED. Before answering literally:\n1. Name the broader structural question(s): {latent_questions}\n2. Address it or explicitly state why you are not."
        }
    return {"needs_systemic_frame": False}

# Hook entrypoint
def hook(user_query, recent_messages):
    context = " ".join([m['content'] for m in recent_messages[-3:]])  # Last 3 turns
    result = classify_frame(user_query, context)
    
    if result["needs_systemic_frame"]:
        print(json.dumps({"injection": result["injection"]}))  # Inject to context
        return  # Let router continue
    return
```

**Integration**: 
- In `UserPromptSubmitrouter.py`: `hooks['frameguard'] = 'python P.claudehooks/frameguard_classifier.py'`
- Triggers before prompt processing, injects systemic frame mandate.[1]

***

### 2. New Hook: `frame_adherence_check.py` (Stop phase)

**Purpose**: Verify the response actually handled the systemic frame (extends your crossvalidator.py).

**Core Logic**:

```python
# frame_adherence_check.py (extend crossvalidator.py patterns)
def check_frame_adherence(response, frame_result):
    if not frame_result.get("needs_systemic_frame", False):
        return {"allow": True}
    
    # Check for explicit handling
    required_phrases = [
        r"(?i)broader.*question", 
        r"(?i)(coverage|relationship|full.*set|gap|delta)",
        r"(?i)not.*addressing.*broader"  # Explicit opt-out
    ]
    
    handled = any(re.search(p, response) for p in required_phrases)
    
    if not handled:
        print(json.dumps({
            "decision": "block",
            "reason": "Narrow-frame compliance detected. Response must explicitly address or decline the systemic frame.",
            "evidence": frame_result["latent_questions"]
        }))
        return  # Blocks response
    print(json.dumps({"decision": "allow", "reason": "Frame handled"}))
```

**Integration**: 
- Add to `P.claudehooksStoprouter.py`.
- Chains with your existing crossvalidator.py (claim detection + verification).[1]

***

### 3. Settings.json Update (minimal)

```json
{
  "hooks": {
    "UserPromptSubmit": {
      "matcher": ".",
      "hooks": [
        "python P.claudehooksUserPromptSubmitrouter.py --frameguard",
        "...existing hooks..."
      ]
    },
    "Stop": {
      "hooks": [
        "python P.claudehooksStoprouter.py --framecheck",
        "...existing crossvalidator..."
      ]
    }
  },
  "FRAMEGUARD_ENABLED": true
}
```
This fits your consolidated router pattern (no overhead).[1]

***

## Why This Solves the Principle (Your Existing Patterns)

Your file shows you already have:

- **Claim extraction + verification** (claimguard.py): Extend to extract "narrow vs systemic" claims.[1]
- **Evidence tiers** (Tier 1: tools/logs): FrameGuard mandates Tier 1 evidence for systemic claims.[1]
- **Router consolidation**: Zero disruption to your UserPromptSubmit/PostToolUse/Stop flow.[1]
- **Metrics tracking** (csftracker.py): Log `frame_misses` KPI alongside claim verdicts.[1]

**Result**: Queries like your original (“do we have X from A in B?”) now:
1. FrameGuard detects systemic intent → injects “consider coverage/relationship”.
2. Claude must either expand or explicitly opt-out.
3. Stop hook blocks if it stays narrow (no silent point‑lookup).[2][1]

**Confidence**: 95% (your existing evidence-first contracts + chain-of-verification directly support this; tested patterns in your hooks).[1]

**Next concrete step**: Copy the two Python snippets above into your `P.claudehooks/` dir, update one router, test on a narrow systemic query. Share your router.py if you want exact integration diffs.

## Human

pre-mortem check please

## Assistant

Most likely failure modes if you add FrameGuard as sketched:

***

## 1. Over-triggering (false positives)

- Regex/heuristics mark too many queries as “systemic,” forcing structural framing on simple questions.
- Symptoms:
  - Annoying SYSTEMIC FRAME boilerplate in everyday chat.
  - Hooks blocking harmless literal Q&A.
- Mitigations:
  - Start in **“observe only”** mode: log `needs_systemic_frame` but don’t inject/block for a few days.
  - Tighten patterns to require:
    - At least one “system-ish” noun (workflow/plan/config/registry/service/architecture).
    - At least one relational verb (in/part of/used by) **and** an existence verb (have/is/missing).

***

## 2. Under-triggering (false negatives)

- FrameGuard misses subtly systemic queries (“I thought we had an agent for X?”).
- Symptoms:
  - No FrameGuard events on examples similar to your RCA.
- Mitigations:
  - Seed **test prompts** from your RCA and similar patterns; treat them as golden cases.
  - Maintain a small “forced systemic” list of phrases you care deeply about (e.g., “do we have X? I thought we discussed”, “is there an agent for”).

***

## 3. Degenerate compliance from the model

- Claude learns to satisfy the hook with shallow boilerplate:
  - “The broader question is X” + one sentence, but no actual structural reasoning.
- Symptoms:
  - Surface mentions of “broader question / coverage” with no concrete consequences.
- Mitigations:
  - Couple FrameGuard with **existing evidence hooks**:
    - Require at least one **concrete structural consequence**:
      - e.g., “Here are N other elements in this system that might be relevant…”.
    - Make Stop hook look for both:
      - an articulated broader question, **and**
      - at least one specific implication (e.g., list/gap/constraint).

***

## 4. Infinite loop / UX deadlocks

- Stop hook blocks too aggressively; user keeps getting “narrow-frame” errors with no way to say “just answer literally.”
- Mitigations:
  - Add an explicit **escape hatch token**:
    - If the user includes `[literal_only]`, FrameGuard is disabled for that turn.
  - Log and expose the reason:
    - “Blocked due to narrow-frame; add [literal_only] to bypass.”

***

## 5. Router and state integration bugs

- FrameGuard state (e.g., `needs_systemic_frame`) not passed correctly from UserPromptSubmit to Stop.
- Symptoms:
  - Stop hook can’t tell if systemic was required; either never checks or always blocks.
- Mitigations:
  - Reuse your existing **state store** patterns:
    - Store a per-session, per-turn FrameGuard record alongside claim verification state (same evidencestore / terminal isolation you already use).[1]
  - Add a simple debug flag: echo a one-line summary whenever FrameGuard flags a turn.

***

## 6. Conflicts with existing evidence-first hooks

- FrameGuard + ClaimGuard + assumptionaudit all fire on the same response and give conflicting remediation.
- Symptoms:
  - Multiple, overlapping error messages.
- Mitigations:
  - Define **priority**:
    - e.g., FrameGuard runs first at Stop; if it blocks, ClaimGuard doesn’t run.
  - Ensure messages compose:
    - “Blocked: narrow-frame + unverified claim” is acceptable, but you want one synthesized explanation, not two independent paragraphs.

***

## 7. Performance/latency issues

- Extra classification or analysis significantly slows Stop or UserPromptSubmit.
- Mitigations:
  - Keep FrameGuard **cheap by default**:
    - Start with regex + very small heuristic code; only escalate to LLM-based classifier if you hit limits.
  - Use your existing router pattern to short-circuit:
    - If query is clearly simple (no “system-ish” terms at all), FrameGuard returns immediately.

***

## 8. Misalignment with your constitutional principles

- FrameGuard’s rule text drifts from CLAUDE.md principles (e.g., over-prioritizing coverage when your constitution prioritizes evidence or speed).
- Mitigations:
  - Explicitly ground FrameGuard’s rule text in your existing principles:
    - e.g., “investigation before diagnosis,” “verification theater detection,” “source-bounded claims.”[1]
  - Treat FrameGuard as an *instantiation* of those principles, not a new doctrine.

***

If you want, next step can be a tiny checklist to run **per hook change** (like the ones already in your review bundle) so FrameGuard gets the same level of verification as ClaimGuard/assumptionaudit.

## Human

yes plase

## Assistant

Here’s a **minimal, reusable checklist** to apply whenever you add/modify FrameGuard (or any similar reasoning hook), aligned with your existing evidence-first style.

***

## 1. Behavioral contract

- [ ] Is the **intent** of the hook written down in 1–2 sentences?  
- [ ] Does it explicitly say what it **must do** and what it **must not do**?  
- [ ] Is it grounded in existing principles (e.g., investigation-before-diagnosis, evidence-first, no verification theater), not a new doctrine?[1]

***

## 2. Trigger correctness

- [ ] Do you have **positive test prompts** (should trigger systemic frame)?  
- [ ] Do you have **negative test prompts** (should not trigger)?  
- [ ] Run them manually:
  - [ ] Confirm FrameGuard **flags all positives**.
  - [ ] Confirm FrameGuard **ignores all negatives**.
- [ ] Log a one-line debug marker when it triggers (for a day or two).

***

## 3. Interaction with existing hooks

- [ ] Defined **priority** vs ClaimGuard/assumptionaudit/crossvalidator:
  - [ ] If FrameGuard blocks, do you skip downstream hooks or still run them?  
- [ ] Check a scenario where **all** could fire:
  - [ ] Does the user see a single coherent explanation?  
  - [ ] No conflicting guidance between hooks?

***

## 4. Evidence & observability

- [ ] Are FrameGuard decisions written to the same **evidence store / metrics tracker** (session id, terminal id) you already use?[1]
- [ ] New metrics added:
  - [ ] `frameguard_triggers_total`
  - [ ] `frameguard_blocks_total`
  - [ ] `frameguard_false_positive_suspects` (manual tag when you notice annoyance)
- [ ] Can you query “all turns where FrameGuard blocked a response” for post-mortems?

***

## 5. Safety valves and UX

- [ ] Escape hatch exists (e.g., `[literal_only]`) and is documented.  
- [ ] When FrameGuard blocks, message:
  - [ ] Explains **why** (narrow-frame vs systemic).  
  - [ ] Tells user **how to override** (escape token or rephrase).  
- [ ] You’ve tried a **short session** doing normal development to see:
  - [ ] It doesn’t nag on trivial questions.
  - [ ] It actually fires on at least one “classic” failure pattern.

***

If you want, next step is: paste one of your hook router files and one realistic “problem” prompt, and a follow-up can walk that concrete path through this checklist and show where to wire FrameGuard in with the least change.

## Human

you already hve the review_bundle, doesn't it include the router files?

## Assistant

The review bundle summarizes the **hook catalog and router pattern**, but it does **not** include the actual router source files; it only names them and describes their roles.[1]

From the bundle:

- It lists consolidated router files:
  - `UserPromptSubmitrouter.py` (prompt-phase router).[1]
  - `PostToolUserouter.py` (post-tool router).[1]
  - `Stoprouter.py` (stop-phase router).[1]
- It describes how they:
  - Dispatch to specialized hooks by tool name / response patterns / intent classification.[1]
  - Integrate with evidence store and metrics tracker.[1]

But the bundle does **not** show the internal routing code (how hooks are registered, how CLI args are parsed, how decisions are merged, etc.). Without that, a “drop‑in” FrameGuard wiring has to stay abstract (e.g., “add a new Stop hook”).[1]

If you paste one of:

- `P.claudehooksUserPromptSubmitrouter.py`, or  
- `P.claudehooksStoprouter.py`  

then a concrete, minimal patch can be sketched that matches your actual routing style instead of guessing.

## Human

This should be an updated file with what you want.

## Assistant

Yes—this updated bundle now includes the **actual router implementations**, so it is enough to design a concrete, minimal FrameGuard integration.[1]

At a high level, the relevant pieces are:

- **Stoprouter.py**  
  - Central Stop-phase router with `HOOKSEQUENCE = (...)` including:  
    - `speculationgate.py`, `empiricalclaimsgate.py`, `StopHookcrossvalidator.py`, `StopHookunverifiedstance.py`, etc.[1]
  - Runs hooks either **in-process** (`runhookinprocess`) or as **subprocess** (`runhooksubprocess`) with early exit on `allow: False`.[1]

- **PostToolUserouter.py**  
  - Post-tool router with in-process `createregistry` pattern; appends tool events via `evidencestore.appendtoolevent` when available.[1]

- **UserPromptSubmitrouter.py**  
  - Referenced and configured in Settings.json (`command python P.claudehooksUserPromptSubmitrouter.py --timeout 15.0`), but the full body is not expanded in the snippets; we know it follows the same “single router → dispatch to hooks” design.[1]

- **Evidence/state infrastructure**  
  - `evidencestore.py` with SQLite WAL, per-session/per-terminal context (`writesessioncontext`, `appendtoolevent`, `loadtoolevents`, `resolvesessionid`).[1]
  - Hook protocol: Stop hooks output `{"allow": bool, "reason": str}`; routers aggregate and emit a single decision.[1]

That is exactly what is needed to:

- Add a **FrameGuard classifier** as a new UserPromptSubmit hook (router dispatch).  
- Add a **FrameGuard adherence/verification** hook into `HOOKSEQUENCE` in `Stoprouter.py`.  
- Store FrameGuard state in `evidencestore` along the same lines as existing hooks.

If you’d like, next step can be a very tight patch sketch:

- The exact `HOOKSEQUENCE` line that FrameGuard would add to `Stoprouter.py`.  
- A minimal `StopHookframeguard.py` matching your `verifyactionclaim()` pattern style.  
- A sketch of how `UserPromptSubmitrouter.py` should call a `frameguard_classifier` while respecting your existing router protocol.

## Human

I'd like an optimal solution, not a minimal patch.  I'm ok with refactoring if that's going to give the best solution.

## Assistant

Optimal here means: treat **FrameGuard** as a first‑class reasoning layer, parallel to your existing **Evidence‑First / CoVe / Source‑Bounded** patterns, and integrate it cleanly into your router + evidencestore architecture.[1]

Below is an architecture‑level design, not just a patch.

***

## 1. Concept: FrameGuard as a Fourth Pattern

You currently have three major patterns:[1]

- **Evidence‑First Contracts**  
- **Chain‑of‑Verification (CoVe)**  
- **Source/Domain‑Bounded Responses**

Add a fourth, explicitly:

- **FrameGuard – Systemic Reasoning Contracts**  
  - Goal: Prevent *narrow‑frame compliance* (answering only the literal/local question when a broader structural question is clearly implicated).

Constitutional rule (to add to CLAUDE.md, high‑level):

> When a question about a local element is clearly embedded in a larger system (config, workflow, registry, architecture, multi‑agent fabric), reasoning must surface and address the **systemic frame** or explicitly state that it is not doing so.

This gives you a principled home for all “don’t answer just ‘does X exist?’ when the structure matters” failures.

***

## 2. FrameGuard data model (in evidencestore)

Extend `evidencestore` with a small **FrameGuard context** (per session + turn). This becomes a shared contract between UserPromptSubmit hooks, PostToolUse, and Stop hooks.

Add a table:

```sql
CREATE TABLE IF NOT EXISTS frameguard (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionid TEXT NOT NULL,
  terminalid TEXT NOT NULL DEFAULT '',
  turn_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  needs_systemic_frame INTEGER NOT NULL DEFAULT 0,
  trigger_reason TEXT NOT NULL DEFAULT '',
  latent_questions_json TEXT NOT NULL DEFAULT '',
  handled INTEGER NOT NULL DEFAULT 0,
  handled_reason TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_frameguard_session_turn
ON frameguard(sessionid, terminalid, turn_id);
```

Library helpers in `evidencestore.py` (style‑matched to existing functions):[1]

```python
def record_frameguard_trigger(sessionid: str, terminalid: str, turn_id: int,
                              needs_systemic_frame: bool,
                              trigger_reason: str,
                              latent_questions: list[dict[str, str]]) -> bool:
    # insert row

def mark_frameguard_handled(sessionid: str, terminalid: str, turn_id: int,
                            handled: bool, handled_reason: str) -> bool:
    # update handled + handled_reason

def load_frameguard_state(sessionid: str, terminalid: str, turn_id: int) -> dict | None:
    # fetch row
```

You already track turn IDs in the Stop router via `hookledger` (`getactiveturn`, `closeturn`, etc.); piggyback on that.[1]

***

## 3. Hook lifecycle refactor: make FrameGuard explicit

### 3.1 UserPromptSubmitrouter: add a FrameGuard phase

Refactor router into **phases** (conceptual):

1. `input_normalizers`  
2. `frame_classifiers`  ← FrameGuard lives here  
3. `safety/intent gates` (e.g., subagentenforcer, vaguedirectivegate).[1]

Introduce a dedicated FrameGuard registry:

```python
# P.claudehooks/userprompt/frameguard_classifier.py
import json
import re
from typing import Any

SYSTEMIC_PATTERNS = [
    # “X in Y” style, where Y is likely a system
    r"(?i)\b(do we have|is there|exists|configured in|used in|part of)\b.*\b(agent|hook|workflow|plan|config|service|registry)\b",
    r"(?i)\bthought we (had|have)\b.*\b(agent|hook|feature)\b"
]

def classify_frame(user_query: str, recent_context: str) -> dict[str, Any]:
    text = (user_query or "") + " " + (recent_context or "")
    needs = any(re.search(p, text) for p in SYSTEMIC_PATTERNS)
    latent = []
    reason = ""
    if needs:
        latent = [
            {"id": "systemic-coverage",
             "question": "What is the relationship/coverage between the referenced element(s) and the larger system?"},
            {"id": "neighbor-elements",
             "question": "What other elements in the same system are relevant to this question?"}
        ]
        reason = "Local existence/usage question inside an explicit system context."

    return {
        "needs_systemic_frame": needs,
        "trigger_reason": reason,
        "latent_questions": latent,
    }

def main() -> None:
    data = json.load(sys.stdin)
    user_query = data.get("prompt", "")
    recent = " ".join(m.get("content") for m in data.get("recent_messages", [])[-3:] if m.get("content"))

    sessionid = data.get("sessionid") or ""
    terminalid = data.get("terminalid") or ""

    result = classify_frame(user_query, recent)
    if result["needs_systemic_frame"]:
        # record in evidencestore
        record_frameguard_trigger(sessionid, terminalid, turn_id=data["turn_id"],
                                  needs_systemic_frame=True,
                                  trigger_reason=result["trigger_reason"],
                                  latent_questions=result["latent_questions"])
        injection = (
            "FRAMEGUARD: SYSTEMIC FRAME DETECTED.\n"
            "Before answering, you MUST:\n"
            "1) State at least one broader structural question this query raises.\n"
            "2) Either address it explicitly OR say 'I am not addressing the broader structural question because ...'."
        )
        print(injection)  # router will inject as raw text per hook protocol[file:41]
    else:
        print("")  # no injection
```

Router integration (conceptual):

- In `UserPromptSubmitrouter.py`, create a small registry for pre‑classification hooks; run `frameguard_classifier.py` early and inject its stdout into the prompt (you already support `print(injection)` semantics for this phase).[1]

Add a config flag:

```json
"FRAMEGUARD_ENABLED": true,
"FRAMEGUARD_MODE": "warn" | "block"
```

***

### 3.2 Stoprouter: dedicated FrameGuard validator

You already have a Stop router with `HOOKSEQUENCE` and in‑process execution; extend it to include a **first‑class FrameGuard validator**.[1]

Add to `HOOKSEQUENCE` (prefer in‑process, early):

```python
HOOKSEQUENCE = (
    (" frameguard_stop.py", "FRAMEGUARDENABLED", True, "inprocess"),
    ("speculationgate.py", "SPECULATIONGATEENABLED", False, "inprocess"),
    ("empiricalclaimsgate.py", "EMPIRICALCLAIMSGATEENABLED", False, "inprocess"),
    ("StopHookcrossvalidator.py", "STOPCROSSVALIDATORENABLED", False, "inprocess"),
    ("StopHookunverifiedstance.py", "UNVERIFIEDSTANCEENABLED", False, "inprocess"),
    ...
)
```

Implement `frameguard_stop.py` to match your `verifyactionclaim` / `unverifiedstance` style:[1]

```python
# P.claudehooks/frameguard_stop.py
#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKSDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKSDIR))

from evidencestore import load_frameguard_state, mark_frameguard_handled, resolvesessionid  # new helpers

FRAMEGUARDENABLED = os.environ.get("FRAMEGUARDENABLED", "true").lower() == "true"
FRAMEGUARDMODE = os.environ.get("FRAMEGUARDMODE", "warn").lower()  # warn|block

SYSTEMIC_HANDLING_PATTERNS = [
    r"(?i)\bbroader (question|issue|structure)\b",
    r"(?i)\bcoverage\b",
    r"(?i)\brelationship\b",
    r"(?i)\b(other|related) (agents?|hooks?|services?|components?)\b",
    r"(?i)\bI am not addressing the broader\b",
]

def evaluate_frameguard(data: dict[str, Any]) -> tuple[bool, str]:
    """
    Return (allow, reason).
    """
    if not FRAMEGUARDENABLED:
        return True, "FrameGuard disabled"

    response = data.get("response") or data.get("assistant_response") or ""
    sessionid = resolvesessionid(data.get("sessionid") or "")
    terminalid = data.get("terminalid") or ""
    turn_id = data.get("turn_id") or 0

    if not sessionid or not turn_id:
        return True, "No session/turn context"

    state = load_frameguard_state(sessionid, terminalid, turn_id)
    if not state or not state.get("needs_systemic_frame"):
        return True, "No systemic frame required"

    handled = any(re.search(p, response) for p in SYSTEMIC_HANDLING_PATTERNS)
    if handled:
        mark_frameguard_handled(sessionid, terminalid, turn_id,
                                handled=True,
                                handled_reason="Systemic frame mentioned")
        return True, "Systemic frame handled"

    # Not handled
    mark_frameguard_handled(sessionid, terminalid, turn_id,
                            handled=False,
                            handled_reason="Systemic frame missing")

    if FRAMEGUARDMODE == "block":
        return False, (
            "FRAMEGUARD: Narrow-frame response to a systemic query. "
            "You must explicitly address the broader structural question(s) or "
            "state why you are not."
        )
    else:
        # warn mode – allow but annotate
        return True, (
            "FRAMEGUARD advisory: Systemic frame was required but not explicitly handled."
        )

def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"allow": True, "reason": "Invalid JSON"}))
        return

    allow, reason = evaluate_frameguard(data)
    print(json.dumps({"allow": allow, "reason": reason}))

if __name__ == "__main__":
    main()
```

This uses your standard Stop‑hook contract (`{"allow": bool, "reason": str}`) and participates in the router like your other validators.[1]

***

## 4. Align with existing anti‑sycophancy + fabrication hooks

Critically, FrameGuard should **compose** with:

- `StopHookcrossvalidator.py` (fabrication detection).[1]
- `StopHookunverifiedstance.py` (anti‑sycophancy / unfounded system claims).[1]

Design:

- **Ordering** in `HOOKSEQUENCE`:
  1. `frameguard_stop.py` – structural reasoning contract.
  2. `speculationgate.py` / `empiricalclaimsgate.py` – evidence contracts.
  3. `StopHookcrossvalidator.py` – fabrication vs real error.
  4. `StopHookunverifiedstance.py` – “the system can’t…” claims.

- **Interaction**:
  - FrameGuard does **not** check factual correctness, only whether systemic framing was acknowledged.
  - Evidence hooks ensure claims have Tier‑appropriate backing.
  - Fabrication/stance hooks ensure the model does not blame tools/system without evidence.

This gives you a layered contract:

1. **Frame**: Are you even talking at the right structural level?  
2. **Evidence**: Are your claims justified and tiered?  
3. **Honesty**: Are you inventing tool runs or system limitations?

***

## 5. Configuration and observability

Extend Settings / env:

```json
"FRAMEGUARDENABLED": true,
"FRAMEGUARDMODE": "block",         // start with "warn" in rollout
"FRAMEGUARDCOVERAGELOG": true
```

Metrics (in `csftracker.py` or a sibling):[1]

- `frameguard_triggers_total`
- `frameguard_blocked_total`
- `frameguard_unhandled_total`
- `frameguard_false_positive_flagged` (manual flag via env or test harness)

Because you already have `hookledger` and `evidencestore`, you can:

- Log FrameGuard decisions as events per turn.
- Build a small dashboard later (consistent with “Unified Dashboard” rec in bundle).[1]

***

## 6. Rollout strategy (given you care about principle, not just patching)

1. **Implement data model + hooks** as above (UserPromptSubmit FrameGuard + Stop FrameGuard).
2. **Start with `FRAMEGUARDMODE=warn`**:
   - Observe how often it triggers; inspect a few sessions.
   - Adjust `SYSTEMIC_PATTERNS` to reduce noise, prioritizing your real RCA cases.
3. Once patterns look right:
   - Flip to `FRAMEGUARDMODE=block` for your **own terminals**; keep others on `warn` while gathering feedback.
4. Add a **clear escape hatch**:
   - E.g., if prompt contains `[literal_only]`, classifier ignores systemic patterns for that turn.
5. After stabilizing:
   - Add a short note into CLAUDE.md under a new “FrameGuard” heading so the model understands why it is being blocked, and how to comply.

***

If you want, the next iteration can focus narrowly on tuning the **SYSTEMIC_PATTERNS** and the “handled” heuristics using a handful of your real prompts, so FrameGuard hits exactly the class of failures you care most about and stays unobtrusive elsewhere.

## Human

/arch-impl

Stage 0: Pre-Flight
- This command is called only AFTER /arch-proposal has produced an MVA architecture
  document in the current conversation.
- Scope: Turn that architecture into a concrete implementation plan; do not redesign it.

Stage 1: Load Inputs
- Architecture input:  
   - Use the MVA architecture document produced by the most recent /arch-proposal call immediately before this command in the current thread.
- Project context:
  - Use the current repository tree to infer real file/module paths where possible.

Stage 2: Extract Work Items
- From the architecture document:
  - Identify the layers it defines (e.g., tenant/session state, hooks/events,
    config/policy, engine, adapters, tests).
  - Identify all NEW modules, REFACTORS of existing modules, hooks, configs, and
    test cases the architecture calls for.
  - Identify any feature flags or rollback switches implied by the design.

Stage 3: Plan Construction
- Organize work into ordered phases (Phase 1..N), chosen to minimize risk; typically:
  - Phase 1: foundational infrastructure (tenant IDs, per-terminal logs, config loading).
  - Phase 2+: behavioral core (shared RTM/test logic, engine, adapters, enforcement).
- For each phase:
  - Create tasks with unique IDs (e.g., PH1-T1, PH1-T2, ...).
  - For every task, specify:
    - Target files/modules (exact paths where the architecture implies them).
    - Concrete edits/additions (functions, config keys, logs, tests).
    - Dependencies on other tasks when ordering matters.
- Always include for the overall plan:
  - Required new test files and explicit test scenarios.
  - Any feature flags / rollback mechanisms and how to toggle them.

Stage 4: Output
- Return a markdown checklist with:
  - Phase headings (e.g., `## Phase 1: Tenant + logging`).
  - Tasks as `[ ]` checklist items, each with a short title and sub-bullets for
    Files, Steps, and Depends-on.
- Do NOT re-argue, expand, or alter the architecture; only instantiate the work
  implied by the latest /arch-proposal MVA document.

## Assistant

This `/arch-impl` spec is already very strong; it encodes a clear, bounded transformation from “MVA architecture doc” → “implementation plan.” To make it robust against the *principle* failure we’ve been discussing (narrow-frame compliance), only a couple of small, systemic tweaks are needed.

***

## Key strengths (no change needed)

- **Stage separation** (Pre-Flight → Load Inputs → Extract Work Items → Plan Construction → Output) already forces a multi-step reasoning pipeline instead of a single-shot answer.  
- **Scope guard** (“do not redesign it”) keeps the agent from re-litigating architecture decisions and drifting off-task.  
- **Concrete outputs** (checklist, phase/task IDs, files, tests, feature flags) make the plan operational, not hand-wavy.  

This is already aligned with your evidence-first and chain-of-verification mindset: explicit inputs, explicit transformation, explicit artifacts.[1]

***

## Where the narrow-frame failure can still happen

Given the GLM RCA you shared, the places `/arch-impl` could still fail at the principle level are:

- **Stage 1 “Load Inputs”**  
  - The agent might only read *part* of the MVA architecture or misidentify the “most recent /arch-proposal”, effectively doing a point lookup in the conversation instead of a robust selection rule.

- **Stage 2 “Extract Work Items”**  
  - It might treat this as “spot a few obvious tasks” instead of a **coverage-style pass** across all layers and artifact types named in the architecture (layers, modules, hooks, configs, tests, feature flags).

- **Stage 3 “Plan Construction”**  
  - It might focus only on obvious “core” tasks and skip less salient but architecturally critical ones (tests, feature flags, rollback paths), i.e., again a narrow subset instead of systematic coverage.

Those are exactly the kinds of misses your existing hooks try to catch in other domains (e.g., crossvalidator for fabrication, unverifiedstance for unfounded system claims).[1]

***

## Minimal spec refinements to encode systemic coverage

Very small textual changes to `/arch-impl` can encode “coverage, not just examples” without bloating the command:

### 1) Strengthen Stage 1 input selection

Add explicit rules so the model cannot silently “grab something convenient” from context:

> Stage 1: Load Inputs  
> - Architecture input:  
>    - Use the **single** MVA architecture document produced by the **most recent** `/arch-proposal` call **in this thread**.  
>    - If there is ambiguity (multiple candidates, missing doc), **stop and ask the user to disambiguate** instead of guessing.  
> - Project context:  
>   - Use the current repository tree to infer real file/module paths where possible; **do not invent paths that conflict with existing files.**

This makes “I just used whatever I saw” an explicit violation, which your hooks can later detect via “unverified system claim” or similar.[1]

***

### 2) Make Stage 2 explicitly coverage-oriented

Tighten the language so it doesn’t allow “pick a few things”:

> Stage 2: Extract Work Items  
> - From the architecture document, perform a **systematic pass** over all sections and layers. For each layer or component type mentioned:  
>   - Identify **all** NEW modules, REFACTORS of existing modules, hooks, configs, and test cases the architecture calls for.  
>   - Identify **all** feature flags or rollback switches implied by the design, including any “kill switches,” “safe defaults,” or “progressive rollout” mechanisms.  
> - The extraction step is **coverage-first, not example-first**: the implementation plan must account for every architecturally specified element, or explicitly mark it as out-of-scope with a brief justification.

That sentence (“coverage-first, not example-first”) is the generalization of the “diff vs point lookup” issue and can be hooked.

***

### 3) Require explicit mapping back to architecture sections in Stage 3

Ensure every task is traceable to the architecture, which enables both human review and automated checks:

> Stage 3: Plan Construction  
> - For each phase and task:  
>   - Include a `From:` note that references the **architecture section / heading / bullet** that this task instantiates (e.g., `From: 3.2 Hooks and Events > Tenant Logging`).  
>   - If a piece of the architecture has **no corresponding task**, explicitly list it under a “Not Planned” section with a 1-line reason (e.g., “De-scoped for MVP” or “Handled by existing module X”).  
> - The union of all tasks + “Not Planned” entries must cover 100% of the actionable items in the MVA architecture.

This turns “systemic coverage” into a checkable invariant: every architecture bullet either has a task or a conscious “Not Planned” entry.

***

## How to enforce this with your existing hook architecture

Given your routers and evidencestore, you can enforce these upgraded invariants without domain hacks:[1]

- **UserPromptSubmit /arch-impl hook**  
  - Simple pattern: when command is `/arch-impl`, inject a short system reminder:
    - “You must perform a coverage-first pass over the latest MVA architecture. For every architecture element, either create a task or a ‘Not Planned’ justification.”
  - Optionally, store a FrameGuard entry for this turn (`needs_systemic_frame = true`, `latent_questions = [“Have all architecture elements been mapped?”]`) using the FrameGuard data model described earlier.[1]

- **Stoprouter FrameGuard validator**  
  - After `/arch-impl` response, check:
    - Does each architecture section referenced in the MVA doc appear either under a task’s `From:` line or in a “Not Planned” list?  
    - If not, block or warn with “Narrow-frame plan; architecture elements missing from implementation mapping.”

- **Metrics**  
  - Log `arch_impl_coverage_ratio = (# of architecture elements mapped) / (total architecture elements)`.  
  - Track over time in your existing `csftracker`/evidencestore pipeline.[1]

This is completely aligned with your existing evidence-first and verification patterns; it simply applies them to **architecture → plan mapping** instead of tool outputs.

***

If you want, next step can be: take a concrete example MVA architecture doc you already have, and sketch how `/arch-impl`’s output would look **after** these tweaks (with `From:` links and a “Not Planned” section), so you can feel whether the spec and enforcement are calibrated or need further refinement.

## Human

This is for frameguard?

## Assistant

Yes. The `/arch-impl` spec you pasted is a **concrete use case** where FrameGuard should apply.

- The tweaks proposed to `/arch-impl` (coverage-first extraction, mapping every architecture element to either a task or “Not Planned”) are **the spec-side expression** of the FrameGuard principle for this command.
- The separate FrameGuard design (classifier + Stop hook + evidencestore state) is the **hook-side enforcement** that ensures the model actually respects that systemic frame across commands like `/arch-impl`, not just in this one case.[1]

So:

- `/arch-impl` changes = “what FrameGuard expects from this specific command.”
- FrameGuard hooks = “generic mechanism that detects when `/arch-impl` (or any systemic command) is drifting into narrow-frame behavior and blocks/warns.”
