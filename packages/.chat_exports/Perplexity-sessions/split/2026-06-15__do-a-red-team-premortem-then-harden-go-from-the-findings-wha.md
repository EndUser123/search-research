---
title: "'do a red-team premortem, then harden /go from the findings', what's a better prompt than this?"
date: "2026-06-15"
mode: "COPILOT"
uuid: "d9c536cb-4ae1-4752-a086-58a6aa3e6235"
entry_count: 8
---

## Human

"do a red-team premortem, then harden /go from the findings", what's a better prompt than this?

## Assistant

A better prompt is:

**“Run a red-team premortem on this plan/system. Identify the 10 most plausible failure modes, rank them by likelihood and impact, show the earliest warning signs, and propose concrete mitigations for the top 5. Then rewrite the original /go prompt or workflow so it is resilient against those failures, with explicit guardrails, acceptance criteria, and a verification checklist.”**  

That formulation is stronger because it is specific, prioritizes by risk, and forces the output to include both diagnosis and hardening actions rather than just critique.[1][2][3]

## Why it’s better

A good premortem is not just “what could go wrong,” but “what will probably go wrong, how do we notice it early, and what do we change now?”[2][1]
Red-teaming guidance also emphasizes making the attack surface explicit, then turning findings into mitigations and retesting, so the prompt should ask for that loop directly.[4][3][5]
The phrase “harden /go” is too vague on its own, so the prompt should define the target artifact, expected behavior, and what counts as a successful fix.[6][5]

## Stronger versions

### General-purpose
**“Premortem this [plan/system/prompt] as if it already failed. List the highest-probability failure modes, the assumptions each one breaks, the observable signals, and the fixes. Then produce a hardened version of the original prompt/process that reduces those failure modes, plus a short test plan to validate the changes.”**[1][2][6]

### For prompts and agents
**“Red-team this agent/prompt in premortem mode. Focus on prompt injection, instruction conflict, tool misuse, data leakage, silent failure, and overreach. For each vulnerability, explain the exploit path, what evidence would confirm it, and the smallest change that would block it. Finish by rewriting the prompt with explicit constraints, refusal rules, and verification steps.”**[3][7][4]

### For operational workflows
**“Assume this workflow fails in production. Identify the most likely causes across people, process, and system design, rank them, and map each to a preventative control and a detection control. Then rewrite the workflow so the controls are built in, not bolted on.”**[5][2][1]

## Recommended structure

Use this output format in the prompt:

1. Failure mode.
2. Why it happens.
3. Early warning signal.
4. Severity and likelihood.
5. Mitigation.
6. Residual risk.
7. Test to verify the mitigation.

That structure makes the result actionable instead of just diagnostic, and it aligns with best practices for premortems and red-team reporting.[2][6][5][1]

## Best default prompt

If you want one reusable prompt, I’d use this:

**“Perform a red-team premortem on the following [plan/system/prompt]. Assume it has already failed. Identify and rank the 10 most plausible failure modes, including attack paths if relevant. For each, give the underlying cause, earliest detectable warning signs, severity, likelihood, and the smallest effective mitigation. Then produce a hardened revision of the original artifact with explicit guardrails, acceptance criteria, and a validation checklist.”**[4][3][5][1]

If you want, I can turn that into a **Claude Code /go wrapper prompt** specifically for your hook-based workflow.

## Human

doesn't a red-team pre-mortem already assume the target has already failed?  Isn't that inherent in the terms red-team and pre-mortem?

## Assistant

Yes — that’s basically right. A premortem explicitly assumes the target has already failed and asks “why did it fail?”[1][2][3]

What makes **red-team** different is not the failure assumption; it’s the adversarial stance. Red-teaming usually means actively trying to break the target, surface blind spots, and test defenses from an attacker’s or skeptic’s perspective, while a premortem is the failure-first framing that helps people generate plausible causes.[4][5][6]

So the two terms are not redundant, but they overlap heavily:
- **Premortem** = assume failure and work backward to causes.[3][1]
- **Red-team** = stress-test the system by actively looking for weaknesses, edge cases, and exploit paths.[5][6][4]

## What that means for the prompt

Because the failure assumption is already inherent, saying “do a red-team premortem” can be a little repetitive. The better prompt should usually add the missing pieces: scope, attack surface, ranking criteria, and what “harden” means in practice.[6][1][4]

A tighter version would be:

**“Red-team this [plan/system/prompt] using a premortem frame: assume it has already failed, identify the most plausible failure and exploit paths, rank them by likelihood and impact, show early warning signs, and propose the smallest effective fixes. Then rewrite the original artifact with explicit guardrails, acceptance criteria, and a verification checklist.”**[3][5][6]

## Practical distinction

If you only want failure analysis, “premortem” is enough. If you want adversarial stress-testing, “red-team” adds the pressure-testing angle and tends to produce sharper findings, especially for prompts, agents, and tool-using systems.[7][5][6]

If you want, I can give you:
1. a **minimal** version of the prompt,
2. a **maximal** version for Claude Code /go, or
3. a version tailored to **agentic systems and hook-based workflows**.

## Human

I'd like the minimal version of the prompt

## Assistant

Use:

**“Assume this has already failed. Red-team it: identify the most likely failure paths, rank them by impact and likelihood, and rewrite it to prevent those failures.”**

If you want it slightly more forceful but still minimal:

**“Assume failure, red-team the target, and harden it against the highest-risk failure modes.”**

## Human

is there something better than 'red-team' or 'pre-mortem'?

## Assistant

Yes — and for your use case, **“adversarial evaluation”** or **“stress test”** is usually better than either term. Those phrases are more precise, less jargon-heavy, and they describe the actual work: probe the system with edge cases, hostile inputs, and realistic failure modes, then measure what breaks.[1][2][3]

## Best alternatives

- **Adversarial evaluation**: best when you want a structured test suite and pass/fail criteria for a system, model, or agent.[2][1]
- **Stress test**: best when you want broad robustness testing without implying a security attack.[4][2]
- **Failure analysis**: best when an incident already happened and you want root causes rather than prevention.[3][4]
- **Premortem**: best when you want a prospective hindsight exercise focused on imagining failure before it happens.[5][6]
- **Red team**: best when the goal is explicitly adversarial probing, especially for security or prompt-injection scenarios.[7][8][9]

## Which term is strongest

For prompt/system hardening, I’d usually choose:

- **Adversarial evaluation** if you want rigor and repeatability.[1][2]
- **Stress test** if you want a simpler, broader term for stakeholders.[2][4]
- **Red team** if you want to signal hostile probing.[8][7]

## My recommendation

For a prompt like your `/go` workflow, the cleanest phrasing is often:

**“Adversarially evaluate this workflow, then harden it.”**

Or, if you want slightly more context:

**“Stress-test this workflow for failure modes, then rewrite it to be more robust.”**

Those avoid the extra conceptual baggage of “premortem,” while still implying systematic failure-seeking and hardening.[3][1][2]

If you want, I can give you a **single best replacement phrase** for each of these contexts: **executive-friendly, engineering-friendly, or agent/security-focused**.

## Human

wouldn't 'stress-test' implement all aspects of the target?

## Assistant

Not exactly. **Stress-test** suggests breadth and robustness checking, but it does not inherently mean “implement all aspects of the target” or model the target from every angle. Red-teaming sources explicitly describe broader adversarial simulation across people, process, and technology, while stress testing is usually a more generic term for pushing a system hard to see where it breaks.[1][2][3]

## Why the distinction matters

A stress test can be as narrow as hammering one subsystem, one prompt, or one workflow path until it fails. It can also be broad, but the word itself does not require full-scope coverage.[4][5]
By contrast, red-team engagements are commonly defined as adversarial simulations that try to mimic real-world attackers and often span multiple vectors and objectives.[6][2][1]

## Practical implication for your prompt

If you say **“stress-test this prompt”**, people may interpret that as “probe the weak spots.”  
If you say **“red-team this prompt”**, they’re more likely to interpret that as “try to break it using adversarial tactics.”  
If you say **“premortem this prompt”**, they’ll interpret it as “assume it failed and explain why.”[7][8][9]

## Better wording for your use case

For a prompt you want analyzed and hardened, the most precise minimal phrasing is usually:

**“Adversarially evaluate this, then harden it.”**

That avoids overloading “stress-test” while still implying hostile probing and remediation. If you want slightly more structure:

**“Adversarially evaluate this workflow for failure modes, then harden it.”**

That wording leaves room for both narrow and broad coverage without claiming full-scope modeling by default.[5][10][11]

## Human

Adversarially is a big word.  Is there a smaller word that does the same thing?

## Assistant

Yes: **“hostilely”** is the smallest direct substitute, but it sounds a bit unnatural in this context.[1][2][3]

For your use case, the best simpler words are:

- **hostile**.
- **aggressive**.
- **critical**.
- **skeptical**.
- **challenging**.

## Best fit

If you want the same intent without the long word, I’d use **“hostile”** only when you really mean attack-like behavior.  
For a prompt, **“skeptical”** or **“critical”** is usually better because it preserves the idea of probing weaknesses without sounding overly combative.[4][5]

## Good replacements

- **“Critically evaluate this, then harden it.”**
- **“Skeptically review this, then harden it.”**
- **“Stress-test this, then harden it.”**
- **“Challenge this, then harden it.”**

## My recommendation

For plain English with minimal jargon, I’d choose:

**“Critically review this, then harden it.”**

It’s shorter, natural, and keeps the meaning of looking for weak spots without the heavier security/attack connotation of “adversarially” or “red-team.”

## Human

criticial review = red-team, stess-test, and pre-mortem?

## Assistant

Not quite. **“Critical review” overlaps with all three, but it is broader and less specific than any of them.** It usually means evaluating strengths and weaknesses, while **red-team** implies adversarial probing, **stress-test** implies pushing hard against failure conditions, and **pre-mortem** implies assuming the thing has already failed and working backward.[1][2][3]

## How they differ

- **Critical review**: general evaluation; can be constructive, skeptical, or analytical, but it does not inherently mean adversarial or failure-first.[4][5]
- **Red-team**: actively tries to break the target, often from an attacker’s perspective.[6][1]
- **Stress-test**: applies pressure to see where it breaks; broader than a normal review, but not necessarily hostile or failure-imagining.[3][7]
- **Pre-mortem**: assumes failure already happened and asks why.[2][8][9]

## The overlap

If your goal is “look for weak spots and improve the thing,” then **critical review** is a reasonable umbrella term.  
If your goal is “try to break it,” **red-team** is better.  
If your goal is “push it hard to see failure modes,” **stress-test** is better.  
If your goal is “imagine it failed and explain the causes,” **pre-mortem** is better.[8][1][2][3]

## Best wording for your prompt

For plain English and minimal jargon, I’d use:

**“Critically review this, then harden it.”**

If you want a little more force:

**“Critically review this for failure modes, then harden it.”**

That captures most of the practical intent without pretending the three terms are identical.

## Human

and there really isn't one industry or best practice term that covers all of them?

## Assistant

Yes — in many technical contexts, **“adversarial testing”** is the closest umbrella term. It covers the overlap of red-teaming, stress-testing, and failure-mode discovery better than any of the individual labels.[1][2][3]

## Why it’s the umbrella

“Adversarial testing” explicitly means trying inputs or scenarios likely to produce problematic behavior, and the Google guidance ties it to coverage of failure modes, edge cases, and mitigation pathways.[1]
That makes it broader than **red-team** alone, because it does not require a security/attacker framing, and broader than **pre-mortem** alone, because it does not require the “assume failure has already happened” thought experiment.[4][5][1]
It also subsumes much of what people mean by **stress-test**, since both are about pushing the system until weaknesses show up.[6][1]

## Where it falls short

“Adversarial testing” is strongest in engineering and AI contexts.  
If you’re speaking to executives or nontechnical collaborators, it can sound more specialized than **critical review** or **stress test**.  
If you want the wording to be friendly and generic, you may still prefer a simpler phrase even if it is less precise.

## Best practical replacement

For your prompt, the best all-in-one phrase is probably:

**“Adversarially test this, then harden it.”**

If you want a simpler version without the longer word, use:

**“Critically test this, then harden it.”**

That is not quite as exact as “adversarial testing,” but it is probably the cleanest plain-English compromise.
