<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I accidently foudn this to be very helpful.  Why is it so good?

"
Please review our proposed  Optimal skill critically.  Find teh logical gaps and opporltunities.  One of the goals of the skill to to make sure we don't miss the obvious things we should be doing."

What principle is it addressing?  Can a better prompt be used to address the principle?

It feels so good because it explicitly asks for *critical* reflection and “obvious misses,” which pushes the model into a self-audit / red-team mode instead of a polite agree-and-elaborate mode.[^1_1][^1_2]

## What principle it’s tapping

At least three intertwined principles are being hit:

- **Adversarial / critical review mode**
The wording “review … critically” and “find the logical gaps and opportunities” is a classic “self‑critique / verify‑and‑revise” pattern that shifts the model from generative to evaluator mode. This tends to:[^1_2][^1_1]
    - Increase error detection.
    - Surface missing considerations and edge cases.
- **Search for unknown unknowns / obvious misses**
Asking “make sure we don't miss the obvious things we should be doing” explicitly targets the model’s pattern library of “common best practices people forget,” which is a strong prior in its training data. That is very different from just “improve this,” which usually gets you cosmetic tweaks.[^1_3][^1_1]
- **Clear intent and role framing**
The prompt is short, imperative, and purpose‑driven (critical review for gaps, not praise or rewriting), which aligns with widely recommended “simple, direct, command‑oriented” prompting.[^1_4][^1_5]

If you name the underlying principle in one phrase:
> **Deliberative critical‑review prompting to surface obvious omissions and failure modes.**[^1_1][^1_2]

## Why this specific wording works

Your original text:

> “Please review our proposed Optimal skill critically. Find teh logical gaps and opporltunities. One of the goals of the skill to to make sure we don't miss the obvious things we should be doing.”

Works well because it:

- Sets a **stance**: “critically” tells the model not to be cooperative/complimentary but skeptical.[^1_1]
- Specifies a **target object**: “our proposed Optimal skill” (even though vague, in context it’s a concrete artifact).
- Names **what to look for**: “logical gaps and opportunities” narrows attention to missing steps, contradictions, and low‑hanging improvements, instead of style.[^1_2][^1_1]
- States a **goal / success criterion**: “don’t miss the obvious things we should be doing” makes it optimize for coverage of common‑sense actions and best practices.[^1_5][^1_3]

Even the slightly messy spelling helps a bit: it signals “human, informal request,” which some systems interpret as non‑templated, making them less likely to fall into canned behaviors (speculative, but consistent with how instruction‑tuned models behave).[^1_6][^1_5]

## A cleaner, stronger version of the same principle

If the goal is to lean into that principle more systematically, a tighter prompt could be:

> **“Act as a critical reviewer of our ‘Optimal’ skill. Your job is to:
> 1) Identify logical gaps, unstated assumptions, and missing steps.
> 2) List obvious actions or best practices we are not doing but clearly should be.
> 3) For each gap or missed obvious action, propose a concrete, practical change.
> Focus on what’s missing or wrong, not on summarizing or praising the current design.”**

This upgrades the original along a few axes, consistent with critical‑review patterns:[^1_5][^1_2][^1_1]

- Clear **role** (“critical reviewer”) rather than generic assistant.
- Explicit **checklist of failure modes** (gaps, assumptions, missing steps, obvious actions).
- Requirement for **actionable fixes**, not just criticism.
- Guardrail against “fluff” (no summarizing/praising).

If you want an ultra‑compact variant that preserves the same principle:

> **“Critically review this ‘Optimal’ skill.
> - Find logical gaps, hidden assumptions, and missing steps.
> - List the obvious best‑practice actions we’re not doing but clearly should be.
> - Propose specific fixes for each issue.”**

FACT vs CONSENSUS vs SPECULATION:

- FACT: Existence and naming of critical‑review / self‑critique prompting patterns, and that they are used to detect flaws and improve reliability.[^1_2][^1_1]
- CONSENSUS: Direct, role‑based, criterion‑driven prompts tend to produce more reliable, targeted outputs than vague ones.[^1_4][^1_5]
- SPECULATION (moderate confidence): The “don’t miss the obvious things we should be doing” clause especially activates the model’s internal library of common best practices and “unknown unknowns” failure modes, which is why it feels surprisingly useful.[^1_3][^1_6]
<span style="display:none">[^1_10][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://logikon.ai/docs/delib_prompting

[^1_2]: https://datalearningscience.com/p/4-reflection-agentic-design-pattern

[^1_3]: https://www.reddit.com/r/PromptDesign/comments/1q3u4fv/do_you_prompt_to_discover_unknown_unknowns_things/

[^1_4]: https://libguides.usask.ca/What_is_a_prompt/prompt_with_purpose

[^1_5]: https://www.sundeepteki.org/advice/the-definitive-guide-to-prompt-engineering-from-principles-to-production

[^1_6]: https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide/

[^1_7]: https://www.digitalocean.com/resources/articles/prompt-engineering-best-practices

[^1_8]: https://andymatuschak.org/prompts/

[^1_9]: https://www.reddit.com/r/PromptEngineering/comments/1mp0tv1/the_first_principles_of_prompt_engineering/

[^1_10]: https://addyo.substack.com/p/the-prompt-engineering-playbook-for


---

# How to improve this critical review prompt further?  It should also be usable for non skill reviews.

A more general, stronger critical‑review prompt should (1) define a reusable role, (2) separate “understand” from “critique,” and (3) enforce structured, actionable output and explicit gap‑hunting.[^2_1][^2_2][^2_3]

## Design goals for the improved prompt

For both skills and non‑skills (docs, plans, designs, code, policies, etc.), the prompt should:

- Work on any **artifact type** (no “skill”-specific language).[^2_4]
- Force a **two‑stage process**: brief understanding → deep critique.[^2_2][^2_3]
- Target specific **failure modes**: logical gaps, hidden assumptions, missing “obvious” actions, risks, contradictions.[^2_1][^2_2]
- Require **concrete fixes**, not just commentary.[^2_5][^2_6]
- Encourage **humility / uncertainty exposure** when information is missing.[^2_3]


## Reusable critical‑review prompt (general artifact)

Here is a compact, reusable prompt you can drop almost anywhere:

> **“Act as a critical reviewer of the following work (it might be a plan, design, document, policy, prompt, or skill).
> 1) First, restate in 2–3 sentences what this work is trying to achieve.
> 2) Then, identify:
> ‑ Logical gaps or inconsistencies.
> ‑ Hidden or shaky assumptions.
> ‑ Important edge cases or risks that are not addressed.
> ‑ ‘Obvious’ best‑practice actions or checks that a competent team would normally include but are missing here.
> 3) For each issue you find, propose a specific, practical improvement (change, addition, or question we should answer).
> 4) If you are uncertain or missing information, say so explicitly and explain what extra information would be needed.
> Focus on what is missing, weak, or risky rather than rephrasing or praising the current work.”**

This stays aligned with self‑critique / self‑verification patterns that improve reasoning and reduce unexamined assumptions.[^2_7][^2_2][^2_3]

## Variant with more structure (for longer artifacts)

If you want more structure for big specs or research‑style content:

> **“You are an expert critical reviewer. Analyze the following work.
>
> Output sections with these headings:
> 1. ‘Brief Intent Summary’ – 2–4 sentences on what this work is trying to accomplish.
> 2. ‘Logical Gaps \& Inconsistencies’ – numbered list of gaps, contradictions, or missing intermediate steps.
> 3. ‘Hidden Assumptions \& Fragile Dependencies’ – numbered list of assumptions that could fail.
> 4. ‘Missing Obvious Actions / Best Practices’ – numbered list of things a competent team would normally do but this work does not cover.
> 5. ‘Risks and Edge Cases’ – key failure modes or scenarios that are not handled.
> 6. ‘Concrete Recommendations’ – specific changes, additions, or questions to strengthen the work.
>
> Be candid and rigorous. Err on the side of **over‑identifying** potential issues rather than being polite. If some critiques are speculative, label them as such.”**

Sectioned, checklist‑style critique aligns well with “fact‑check list” and structured self‑criticism techniques shown to improve coverage and output quality.[^2_6][^2_2][^2_1]

## How this differs from your original

Relative to your initial phrasing, these versions:

- Drop “skill” so they apply to any artifact.
- Make the **unknown‑unknowns** goal explicit via “missing obvious actions / best practices” and “edge cases / risks.”[^2_3][^2_1]
- Build in an **uncertainty channel**, encouraging the model to admit where input is insufficient instead of hallucinating.[^2_3]
- Enforce a **structured answer format**, which generally yields more thorough critical coverage.[^2_4][^2_1]
<span style="display:none">[^2_10][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://gpt-lab.eu/effective-prompts-for-reasoning-llms/

[^2_2]: https://learnprompting.org/docs/advanced/self_criticism/introduction

[^2_3]: https://promptengineering.org/llms-learn-humility-how-self-critique-improves-logic-and-reasoning-in-llms-like-chatgpt/

[^2_4]: https://www.promptingguide.ai/techniques

[^2_5]: https://www.reddit.com/r/PromptEngineering/comments/1hv1ni9/prompt_engineering_of_llm_prompt_engineering/

[^2_6]: https://promptwritersai.com/how-to-use-reflection-and-self-critique-in-prompts-for-better-outputs/

[^2_7]: https://evjang.com/2023/03/26/self-reflection.html

[^2_8]: https://www.linkedin.com/pulse/using-llm-critique-research-meta-prompting-andrew-dempsey-5vfwc

[^2_9]: https://www.aiengineeringlab.com/blog-posts/prompt-engineering-a-catalyst-for-critical-thinking

[^2_10]: https://www.refontelearning.com/blog/the-ultimate-guide-to-prompt-engineering-jobs-landing-your-dream-role


---

# How to add chain-of-thought reasoning to the critique prompt

Best practices for iterative self-refinement in prompts
Common pitfalls in critical review prompts and fixes

To add chain‑of‑thought and self‑refinement to your critical‑review pattern, treat it as a small “review → critique → refine” protocol, and be explicit about when the model should think step‑by‑step and when it should improve its own work.[^3_1][^3_2][^3_3][^3_4]

***

## 1. Adding chain‑of‑thought to the critique prompt

Core idea: explicitly separate **reasoning steps** from **final critiques**, and tell the model to reason step‑by‑step before deciding what’s wrong.[^3_2][^3_5][^3_6][^3_1]

You can make this CoT‑enabled variant of your critical reviewer prompt:

> **“You are a critical reviewer of the following work (plan, design, document, policy, prompt, or skill).
>
> First, think through your analysis step‑by‑step, identifying potential issues before you write any conclusions. Do not skip steps in your reasoning.
>
> Then, produce your final answer with the following sections (without showing your intermediate scratch work unless explicitly requested):
> 1. Brief Intent Summary – 2–4 sentences on what this work is trying to accomplish.
> 2. Logical Gaps \& Inconsistencies – numbered list.
> 3. Hidden Assumptions \& Fragile Dependencies – numbered list.
> 4. Missing Obvious Actions / Best Practices – numbered list.
> 5. Risks and Edge Cases – numbered list.
> 6. Concrete Recommendations – specific changes, additions, or questions.
>
> Be rigorous and candid. Err on the side of over‑identifying potential issues. If some critiques are speculative, label them as such.”**

This leverages the “let’s think step‑by‑step” style chain‑of‑thought instruction while keeping the visible output structured and compact.[^3_7][^3_5][^3_6][^3_1]

If you *do* want to see the reasoning:

> “First, show your reasoning step‑by‑step under a heading ‘Reasoning’, then give the structured critique.”

***

## 2. Best practices for iterative self‑refinement in prompts

Self‑refine works best when you make the model alternate between **generation** and **feedback** with slightly different roles.[^3_3][^3_4]

A lightweight three‑call protocol:

1. **Initial critique**

> “Act as a critical reviewer and analyze this work. Use the structured format above.”
2. **Feedback on the critique**

> “Here is a critique of the work. Your job now is to evaluate *this critique* itself.
> ‑ Identify where the critique is shallow, missing issues, or overconfident.
> ‑ Add any important problems or risks the critique missed.
> ‑ Point out any weak or speculative points in the critique.
> Output: a short list of ‘Improvements to the critique’.”
3. **Refined critique**

> “Now produce a **refined critique** of the original work that:
> ‑ Incorporates the ‘Improvements to the critique’.
> ‑ Fixes shallow or speculative points.
> ‑ Keeps the same structured sections.
> Only output the improved critique.”

Best‑practice patterns from Self‑Refine‑style workflows:[^3_4][^3_3]

- Make feedback **separate** from the original answer, not mixed in.
- Have the refinement step **explicitly reference** the feedback.
- Limit iterations (e.g., 1–2 rounds) to avoid cost and drift.
- Keep roles distinct: “reviewer of the work” vs “reviewer of the review.”

You can compress this into a single prompt for tools that support multiple turns internally:

> “Generate an initial critique, then internally critique your own critique and update it once before responding. Only show the final, improved critique to the user.”

***

## 3. Common pitfalls in critical‑review prompts (and fixes)

### Pitfalls

- **Vague instructions**
“Please review and suggest improvements” yields shallow, high‑level comments.[^3_8][^3_9]
**Fix:** Specify targets: gaps, assumptions, missing best practices, risks, edge cases, and concrete recommendations.
- **No reasoning requirement**
Without CoT, models often jump to generic critiques or focus on surface‑level issues.[^3_5][^3_6][^3_1][^3_2]
**Fix:** Add “think step‑by‑step before you answer” and enforce structured output sections.
- **No uncertainty / calibration channel**
Models can sound extremely confident even when key info is missing.[^3_10][^3_8]
**Fix:** Add instructions like “If information is missing or ambiguous, explicitly say what you’re assuming and what extra information would change your conclusions.”
- **Overly positive framing**
“Provide constructive feedback and highlight strengths” pushes toward praise and light suggestions.[^3_9][^3_11]
**Fix:** Explicitly prioritize problems: “Focus on what is missing, weak, or risky; strengths are optional and brief.”
- **Unscoped domain**
Without a domain hint, models may miss domain‑specific best practices.
**Fix:** Optionally add a domain role: “Act as a security engineer / product manager / architect reviewing this work.”
- **No requirement for actionability**
You get labels (“unclear”, “risky”) but no fixes.
**Fix:** Require “for each issue, propose at least one specific change, addition, or question.”

***

## 4. Putting it all together (full pattern)

A full, CoT‑aware, self‑refining critical review pattern, reusable across artifacts:

**Step 1 – Initial CoT critique prompt**

> “You are an expert critical reviewer of the following work (plan, design, document, policy, prompt, or skill).
>
> Internally, think through your analysis step‑by‑step before writing your answer, identifying potential issues and alternatives. Do not skip steps in your reasoning.
>
> Then provide your answer with these sections only:
> 1. Brief Intent Summary
> 2. Logical Gaps \& Inconsistencies
> 3. Hidden Assumptions \& Fragile Dependencies
> 4. Missing Obvious Actions / Best Practices
> 5. Risks and Edge Cases
> 6. Concrete Recommendations
> 7. Open Questions / Unknowns (where you lack information or are uncertain)
>
> Focus on what is missing, weak, or risky; keep praise minimal. Clearly label speculative critiques as ‘Speculative’.”

**Step 2 – Self‑refinement prompt**

> “Now review your own critique above.
> ‑ Identify any important problems, risks, or missing best practices you did *not* mention.
> ‑ Identify any points that are vague, generic, or weakly justified.
> ‑ Suggest concrete improvements to your critique.
> Output a section ‘Improvements to the critique’.”

**Step 3 – Refined critique**

> “Produce a refined version of your critique that:
> ‑ Incorporates the ‘Improvements to the critique’.
> ‑ Strengthens or removes weak points.
> ‑ Keeps the same section structure.
> Only output the refined critique.”

This combines: chain‑of‑thought for better reasoning, structured critical‑review sections, and an explicit self‑refinement loop while avoiding the usual pitfalls.[^3_1][^3_2][^3_5][^3_3][^3_4][^3_8]
<span style="display:none">[^3_12]</span>

<div align="center">⁂</div>

[^3_1]: https://www.promptingguide.ai/techniques/cot

[^3_2]: https://learnprompting.org/docs/intermediate/chain_of_thought

[^3_3]: https://learnprompting.org/docs/advanced/self_criticism/self_refine

[^3_4]: https://mirascope.com/docs/v1/guides/prompt-engineering/chaining-based/self-refine

[^3_5]: https://www.ibm.com/think/topics/chain-of-thoughts

[^3_6]: https://learn.microsoft.com/en-us/dotnet/ai/conceptual/chain-of-thought-prompting

[^3_7]: https://www.prompthub.us/blog/chain-of-thought-prompting-guide

[^3_8]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12306261/

[^3_9]: https://www.promptingguide.ai/techniques

[^3_10]: https://arxiv.org/html/2512.22145v1

[^3_11]: https://www.aiengineeringlab.com/blog-posts/prompt-engineering-a-catalyst-for-critical-thinking

[^3_12]: https://www.reddit.com/r/LocalLLaMA/comments/1hf7jd2/everyone_share_their_favorite_chain_of_thought/


---

# Examples of CoT in critique prompts

Self-Refine prompt templates for reviews
How to avoid overconfidence in LLM critiques
Compare CoT vs Self-Refine for prompt improvement
Tools for iterative prompt refinement

The pieces you’re asking about all fit into one pattern: force the model to reason explicitly, critique explicitly, and then update explicitly, while also forcing it to *admit uncertainty* and avoid generic praise.[^4_1][^4_2][^4_3][^4_4][^4_5]

***

## CoT examples for critique prompts

You can embed chain‑of‑thought directly into a review prompt like this:

> “You are a critical reviewer of the following work.
>
> **Reasoning phase (internal):**
> 1) List the main goals of the work.
> 2) For each goal, think step‑by‑step about whether the current design actually supports it, and where it might fail.
> 3) Scan for logical gaps, hidden assumptions, missing ‘obvious’ actions, and unhandled risks.
> Do this reasoning step‑by‑step before writing your answer.
>
> **Output phase (for the user):**
> 1. Brief Intent Summary
> 2. Logical Gaps \& Inconsistencies
> 3. Hidden Assumptions
> 4. Missing Obvious Actions / Best Practices
> 5. Risks and Edge Cases
> 6. Concrete Recommendations
>
> Be specific and critical; minimize praise.”

If you *want* to see the chain‑of‑thought:

> “First, under a heading ‘Reasoning (step‑by‑step)’, show your reasoning in detail. Then, under ‘Final Critique’, give a concise, structured summary as above.”

Using explicit step lists like this is a standard pattern for CoT prompts, which improves reasoning especially on multi‑step tasks.[^4_6][^4_7][^4_3][^4_1]

***

## Self‑Refine templates for reviews

Self‑Refine is a loop: **Generate → Critique → Refine**. For reviews, that becomes “review the work → review the review → improved review.”[^4_8][^4_9][^4_4][^4_5]

**1) Initial review**

> “Act as an expert critical reviewer of the following work.
> Produce sections: Intent, Strengths (brief), Weaknesses, Missing Obvious Actions / Best Practices, Risks \& Edge Cases, Concrete Recommendations.”

**2) Critique of the review**

> “Now act as a *review‑of‑the‑review* critic.
> Given the work and the review above:
> - Identify important weaknesses, gaps, or risks in the work that the review *failed to mention*.
> - Identify parts of the review that are too generic, weakly justified, or likely incorrect.
> - Output a JSON object:
> ```json > { >   "missed_issues": ["..."], >   "weak_points": ["..."], >   "improvement_plan": ["..."] > } > ```”

JSON/structured feedback is consistent with Self‑Refine style designs.[^4_9][^4_4][^4_5][^4_8]

**3) Refined review**

> “Using only the original work and the JSON feedback above (`missed_issues`, `weak_points`, `improvement_plan`), produce a refined version of the review.
> - Keep the same sections.
> - Add the missed issues.
> - Strengthen or remove weak points.
> - Do not introduce new claims that are not supported by the work.”

You can wrap this into an automated loop the way many Self‑Refine implementations do: stop when the critic’s `improvement_plan` becomes empty or the score plateaus.[^4_4][^4_5][^4_8][^4_9]

***

## Avoiding overconfidence in LLM critiques

Overconfidence in “LLM‑as‑a‑judge” is well‑documented: models systematically overstate their own correctness and confidence. To counter that, make *calibration* an explicit requirement:[^4_2][^4_10]

- Force **confidence scores with justification**:

> “For each major critique, provide:
> - A 0–100 confidence score in that critique being valid.
> - A one‑sentence justification of the score.
> Label low‑confidence critiques explicitly.”
- Force **assumptions + what would change the verdict**:

> “For each critique, list:
> - ‘Assumptions this critique relies on’.
> - ‘What new information would make this critique invalid or weaker’.”
- Allow an explicit **“uncertain / insufficient information”** outcome:

> “If you lack enough information to make a strong judgment on some aspect, say so and mark it as ‘uncertain’, instead of inferring details.”
- Avoid “absolute” language by instruction:

> “Use calibrated language: ‘likely’, ‘plausible’, ‘uncertain’, instead of absolute claims like ‘definitely’, unless the evidence is overwhelming.”

Empirical work on LLM‑as‑judge shows that requiring explicit confidence estimates and conditions helps mitigate overconfidence and makes systems safer for downstream decisions.[^4_2]

***

## CoT vs Self‑Refine for prompt improvement

A compact comparison in this context:


| Aspect | Chain‑of‑Thought (CoT) | Self‑Refine |
| :-- | :-- | :-- |
| Core idea | Force step‑by‑step reasoning before answering.[^4_1][^4_3][^4_6] | Alternate between answer and self‑feedback across iterations.[^4_4][^4_5][^4_9] |
| Granularity | Single response, internally more structured. | Multi‑turn or multi‑call process, explicit loops. |
| Strengths | Better one‑shot reasoning; improves coverage of issues in a single critique. | Systematic improvement; can correct earlier mistakes and shallow critiques.[^4_4][^4_5][^4_8] |
| Weaknesses | Still can be confidently wrong in a single pass; no second thoughts. | Higher cost; risk of drift or over‑editing; needs stopping criteria.[^4_4][^4_5][^4_8] |
| Best use for prompt improvement | Design a *good first critical review* prompt. | Wrap that good reviewer in an automated refine loop to polish prompts/specs over iterations. |

In practice:

- Use **CoT** inside each reviewer prompt to make each pass smart.
- Use **Self‑Refine** outside to run 1–3 passes until the critic stops adding real value.

***

## Tools and patterns for iterative prompt refinement

Conceptual “tools” (patterns) you can script or implement:

- **Three‑prompt Self‑Refine loop** (as in the SAP / Self‑Refine writeups).[^4_5][^4_8][^4_9][^4_4]
    - `GEN_PROMPT`: produce draft (prompt, spec, policy).
    - `CRITIC_PROMPT`: structured critique with issues, score, plan.[^4_8]
    - `REFINE_PROMPT`: rewrite using only the plan and original task.
- **Prompt‑chaining for analysis → critique → rewrite**:
Many CoT resources describe breaking tasks into chained prompts: summarize → analyze → improve. For prompt refinement:[^4_7]
    - P1: “Summarize what this prompt is trying to achieve and how it works.”
    - P2: “Critically evaluate this prompt with CoT and structured sections.”
    - P3: “Rewrite the prompt to fix the identified issues, preserving the original intent.”
- **LLM‑as‑a‑judge + scorer**:
Use a judge prompt that scores clarity, specificity, safety, and robustness 1–10, plus free‑text issues; then use those scores as signals for whether to run another refinement iteration.[^4_11][^4_2]
- **Few‑shot CoT templates**:
Provide 1–2 examples of “bad prompt → critique → improved prompt” so the model learns the pattern and applies it to new prompts, as described in chain‑of‑thought and automatic‑CoT guides.[^4_6][^4_7]

If you’re building this into your own tooling, the minimal high‑leverage combo is:

1) A **CoT‑enabled critical reviewer** prompt (with confidence + assumptions).
2) A **Self‑Refine wrapper** that runs: draft prompt → reviewer → reviewer‑of‑review → refined prompt, stopping when changes become trivial.
<span style="display:none">[^4_12][^4_13][^4_14]</span>

<div align="center">⁂</div>

[^4_1]: https://www.promptingguide.ai/techniques/cot

[^4_2]: https://arxiv.org/html/2508.06225v1

[^4_3]: https://learnprompting.org/docs/intermediate/chain_of_thought

[^4_4]: https://learnprompting.org/docs/advanced/self_criticism/self_refine

[^4_5]: https://mirascope.com/docs/v1/guides/prompt-engineering/chaining-based/self-refine

[^4_6]: https://www.codecademy.com/article/chain-of-thought-cot-prompting

[^4_7]: https://www.helicone.ai/blog/chain-of-thought-prompting

[^4_8]: https://community.sap.com/t5/crm-and-cx-blog-posts-by-sap/self-refining-prompts-for-a-better-customer-experience/ba-p/14245356

[^4_9]: https://neurips.cc/virtual/2023/poster/71632

[^4_10]: https://www.nature.com/articles/s42256-024-00976-7

[^4_11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12306261/

[^4_12]: https://www.reddit.com/r/LocalLLaMA/comments/1hf7jd2/everyone_share_their_favorite_chain_of_thought/

[^4_13]: https://code.likeagirl.io/absolute-best-of-prompting-chain-of-thoughts-42fa2d583508

[^4_14]: https://community.openai.com/t/a-better-chain-of-thought-prompt/128180


---

# How do we include self-learning or auto-improvement?  Or is that excessive for this application?

Including some auto‑improvement is useful, but full “self‑learning” is overkill and risky for this use‑case. A **bounded self‑refine loop around a stable review prompt** is usually the sweet spot.[^5_1][^5_2][^5_3]

## What “self‑learning” means here

There are two very different notions:

- **In‑session self‑refinement (recommended)**
The model iteratively critiques and improves its *current* critique or prompt, without changing its underlying weights.[^5_2][^5_4][^5_1]
- **Persistent self‑training / autonomous evolution (not recommended here)**
The system writes its own training data, retrains or fine‑tunes itself, and drifts over time; this is where alignment and safety decay show up.[^5_3][^5_5]

For a critical‑review helper, you almost certainly just want the first.

## Lightweight auto‑improvement pattern

You can add auto‑improvement as a small, explicit loop, without any real “learning”:

1. **Fixed reviewer prompt** (with CoT):
    - Keep a single, versioned critical‑review prompt.
    - It already says: think step‑by‑step, find gaps, assumptions, “obvious” misses, risks, and propose fixes.
2. **One self‑refine pass** on each critique:
    - After the first critique, call a critic prompt:

> “Review the critique above.
> - List important issues it missed.
> - Flag any weak, generic, or poorly justified points.
> - Output an ‘improvement plan’.”
    - Then a refiner prompt:

> “Produce an improved critique that incorporates the improvement plan, keeping the same structure.”

This is essentially Self‑Refine applied to reviews: generate → feedback → refine, with the same LLM acting as all three components.[^5_4][^5_1][^5_2]

## When this is enough vs excessive

**Reasonable for your application**

- You want:
    - Higher‑quality critiques of prompts/skills/specs.
    - Better coverage of “obvious” misses.
    - Still‑transparent logic and easy debugging.
- A 1–2 step self‑refine loop gives ~10–20% improvements in quality on average tasks without retraining.[^5_1][^5_2]

**Excessive / risky**

- Continuous autonomous “self‑evolution” where:
    - The system changes its own review prompt or scoring rules without human oversight.
    - You store its own outputs as training data and re‑fine‑tune regularly.
- Work on self‑improving agents shows safety and alignment tend to *decay* in closed loops without external constraints.[^5_3]

For an “optimal skill / spec reviewer,” that kind of self‑training is not only unnecessary but introduces:

- Silent drift in critique style.
- Over‑fitting to your current corpus of specs/prompts.
- Harder debugging (you no longer know what behavior is baked in).


## Practical recommendation

- **Yes**:
    - Use a **stable, hand‑designed critical‑review prompt** with CoT.
    - Optionally wrap it in **one self‑refine iteration** per review for auto‑improvement.
    - Version and edit the reviewer prompt manually as you learn.
- **No** (for now):
    - Do not let the system modify its own reviewer prompt or training data autonomously.
    - Do not implement continuous self‑training loops without strong external evaluation and safety checks.[^5_5][^5_3]

So: include *bounded* auto‑improvement (Self‑Refine‑style) as part of the critique workflow; treat anything beyond that as research‑grade and excessive for this application.
<span style="display:none">[^5_10][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://arxiv.org/abs/2303.17651

[^5_2]: https://neurips.cc/virtual/2023/poster/71632

[^5_3]: https://www.youtube.com/watch?v=1pV3HrzY9fA

[^5_4]: https://www.cs.toronto.edu/~cmaddis/courses/csc2541_w25/presentations/artru_glukhov_selfrefine.pdf

[^5_5]: https://www.linkedin.com/posts/matthewbusel_the-self-improving-loop-is-live-center-activity-7431639339870228480-z5MU

[^5_6]: https://dl.acm.org/doi/10.5555/3666122.3668141

[^5_7]: https://www.reddit.com/r/singularity/comments/12a4s6d/selfrefine_iterative_refinement_with_selffeedback/

[^5_8]: https://blog.langchain.com/promptim/

[^5_9]: https://www.reddit.com/r/machinelearningnews/comments/12f2iby/this_ai_paper_introduces_selfrefine_a_framework/

[^5_10]: https://arize.com/blog/prompt-optimization-few-shot-prompting/


---

# So are there two versions of the final prompt concept?

Yes: conceptually there are two “final prompt” variants, built on the same core reviewer pattern.

## 1) Single-pass CoT critical reviewer

Use when you want a strong critique in one shot:

> “You are an expert critical reviewer of the following work (plan, design, document, policy, prompt, or skill).
>
> First, think through your analysis step‑by‑step before writing your answer. Do not skip intermediate reasoning steps.
>
> Then provide your answer with these sections only:
> 1. Brief Intent Summary – what this work is trying to achieve.
> 2. Logical Gaps \& Inconsistencies – numbered list.
> 3. Hidden Assumptions \& Fragile Dependencies – numbered list.
> 4. Missing Obvious Actions / Best Practices – numbered list.
> 5. Risks and Edge Cases – numbered list.
> 6. Concrete Recommendations – specific changes, additions, or questions.
> 7. Open Questions / Unknowns – where information is missing or you are uncertain.
>
> Focus on what is missing, weak, or risky; keep praise minimal. Clearly label speculative critiques as ‘Speculative’.”

This is the **default**: CoT inside, one visible pass.

## 2) CoT + one-step Self-Refine wrapper

Same reviewer, but with an auto-improvement pass. In practice this is implemented as two prompts around the first:

**Step A – Initial critique**
Use the CoT reviewer prompt above.

**Step B – Critique-of-the-critique**

> “Now act as a critic of the critique above.
> - List important problems, risks, or missing best practices in the original work that the critique failed to mention.
> - Flag any points in the critique that are too generic, weakly justified, or likely incorrect.
> - Output a short ‘Improvements to the critique’ list.”

**Step C – Refined critique**

> “Produce a refined version of your critique of the original work that:
> - Incorporates the ‘Improvements to the critique’.
> - Adds missed issues and strengthens or removes weak points.
> - Keeps the same section structure as before.
> Only output the refined critique.”

So: one *core* prompt (the CoT critical reviewer), and optionally a **wrapped version** that runs a single self‑refine loop around it.

---

# please create a TLDR for the CoT + one-step Self-Refine wrapper so I don't forget what it is in a week.

**TL;DR – CoT + one-step Self‑Refine wrapper**

- **What it is:**
A two-layer pattern:

1) A **CoT critical reviewer** prompt that forces step‑by‑step reasoning and structured critique in one pass.[^7_1][^7_2]
2) A **single Self‑Refine pass** where the model critiques its own review and then issues an improved version.[^7_3][^7_4][^7_5][^7_6]
- **How it runs (mentally):**

1) **Initial CoT review:** “Think step‑by‑step, then output: intent, gaps, assumptions, missing obvious actions, risks, recommendations, unknowns.”
2) **Critique-of-the-critique:** “What did this review miss or get weak/hand‑wavy?”
3) **Refined review:** “Rewrite the review once, incorporating that improvement list, same structure.”
- **Why it’s useful:**
    - CoT = better **first-pass reasoning** and coverage.[^7_7][^7_2][^7_1]
    - One Self‑Refine loop = **~one extra level of depth/quality** without heavy complexity or true self‑training.[^7_4][^7_5][^7_8][^7_3]
- **What to remember in a week:**
> “Use a strong CoT reviewer prompt as the base, then run *one* ‘review‑of‑the‑review’ step and regenerate the critique once using that feedback. No ongoing self‑learning, just a single Self‑Refine loop around a fixed reviewer.”
<span style="display:none">[^7_10][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://www.ibm.com/think/topics/chain-of-thoughts

[^7_2]: https://www.techtarget.com/searchenterpriseai/definition/chain-of-thought-prompting

[^7_3]: https://arxiv.org/abs/2303.17651

[^7_4]: https://neurips.cc/virtual/2023/poster/71632

[^7_5]: https://learnprompting.org/docs/advanced/self_criticism/self_refine

[^7_6]: https://github.com/madaan/self-refine

[^7_7]: https://www.superannotate.com/blog/chain-of-thought-cot-prompting

[^7_8]: https://www.marknagelberg.com/roam-research-notes-on-self-refine-iterative-refinement-with-self-feedback-by-madaan-et-al/

[^7_9]: https://dl.acm.org/doi/10.5555/3666122.3668141

[^7_10]: https://www.cs.toronto.edu/~cmaddis/courses/csc2541_w25/presentations/artru_glukhov_selfrefine.pdf


---

# Here's what I recorded as notes:

"**TL;DR – CoT + one-step Self‑Refine wrapper**

- **What it is:**
A two-layer pattern:

1) A **CoT critical reviewer** prompt that forces step‑by‑step reasoning and structured critique in one pass.
2) A **single Self‑Refine pass** where the model critiques its own review and then issues an improved version.
- **How it runs (mentally):**

1) **Initial CoT review:** “Think step‑by‑step, then output: intent, gaps, assumptions, missing obvious actions, risks, recommendations, unknowns.”
2) **Critique-of-the-critique:** “What did this review miss or get weak/hand‑wavy?”
3) **Refined review:** “Rewrite the review once, incorporating that improvement list, same structure.”
- **Why it’s useful:**
    - CoT = better **first-pass reasoning** and coverage.
    - One Self‑Refine loop = **~one extra level of depth/quality** without heavy complexity or true self‑training.
- **What to remember in a week:**
> “Use a strong CoT reviewer prompt as the base, then run *one* ‘review‑of‑the‑review’ step and regenerate the critique once using that feedback. No ongoing self‑learning, just a single Self‑Refine loop around a fixed reviewer.”

PROMPT 1:
“Act as an expert critical reviewer of the work (plan, design, document, policy, prompt, or skill) we have done.
First, think through your analysis step‑by‑step before writing your answer. Do not skip intermediate reasoning steps.
Then provide your answer with these sections only:
Brief Intent Summary – what this work is trying to achieve.
Logical Gaps \& Inconsistencies – numbered list.
Hidden Assumptions \& Fragile Dependencies – numbered list.
Missing Obvious Actions / Best Practices – numbered list.
Risks and Edge Cases – numbered list.
Concrete Recommendations – specific changes, additions, or questions.
Open Questions / Unknowns – where information is missing or you are uncertain.
Focus on what is missing, weak, or risky; keep praise minimal. Clearly label speculative critiques as ‘Speculative’.”

PROMPT 2:
“Now act as a critic of the critique above.
List important problems, risks, or missing best practices in the original work that the critique failed to mention.
Flag any points in the critique that are too generic, weakly justified, or likely incorrect.
Output a short ‘Improvements to the critique’ list.”

PROMPT 3:
“Produce a refined version of your critique of the original work that:
Incorporates the ‘Improvements to the critique’.
Adds missed issues and strengthens or removes weak points.
Keeps the same section structure as before.
Only output the refined critique.”"

But now I'm confused by what this looks like in practice: "  > “Use a strong CoT reviewer prompt as the base, then run *one* ‘review‑of‑the‑review’ step and regenerate the critique once using that feedback. No ongoing self‑learning, just a single Self‑Refine loop around a fixed reviewer.”"

In practice you’re just doing **three sequential calls** with the three prompts you wrote. Nothing more “magical” than that.

Think of it as:

1. **P1 – Make a critique.**
2. **P2 – Critique that critique.**
3. **P3 – Rewrite the original critique once, using the feedback from P2.**

That’s all “one Self‑Refine loop” means.

***

## Step-by-step with your three prompts

Assume you have some artifact `WORK` (prompt, spec, doc, etc.).

### 1) Call PROMPT 1 with `WORK`

Input to the model:

- System/instruction: `PROMPT 1` text.
- User content: the `WORK` you want reviewed.

Model output:

- `CRITIQUE_1` (sections: Intent, Gaps, Assumptions, Missing obvious things, Risks, Recommendations, Unknowns).

This is the **initial CoT‑enabled critical review**.

***

### 2) Call PROMPT 2 with `WORK + CRITIQUE_1`

Input:

- System/instruction: `PROMPT 2`.
- User content:
    - The original `WORK`.
    - The `CRITIQUE_1` text.

Model output:

- `IMPROVEMENTS_LIST` (bullet list of “Improvements to the critique”).

This is the **“review‑of‑the‑review”** step.

***

### 3) Call PROMPT 3 with `WORK + CRITIQUE_1 + IMPROVEMENTS_LIST`

Input:

- System/instruction: `PROMPT 3`.
- User content:
    - The original `WORK`.
    - `CRITIQUE_1`.
    - `IMPROVEMENTS_LIST`.

Model output:

- `CRITIQUE_2` – a **refined critique** that:
    - Uses the same section structure as PROMPT 1.
    - Adds missing issues and strengthens / deletes weak points.
    - Is the **only** critique you care about at the end.

That three-call sequence **is**:

> “Use a strong CoT reviewer prompt as the base, then run one ‘review‑of‑the‑review’ step and regenerate the critique once using that feedback.”

No stateful learning, no weights changing, no ongoing loop—just **P1 → P2 → P3, stop**.
<span style="display:none">[^8_1][^8_10][^8_2][^8_3][^8_4][^8_5][^8_6][^8_7][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://arxiv.org/abs/2303.17651

[^8_2]: https://learnprompting.org/docs/advanced/self_criticism/self_refine

[^8_3]: https://www.cs.toronto.edu/~cmaddis/courses/csc2541_w25/presentations/artru_glukhov_selfrefine.pdf

[^8_4]: https://github.com/madaan/self-refine

[^8_5]: https://www.youtube.com/watch?v=WtRnuMYQD5A

[^8_6]: https://tetrate.io/learn/ai/chain-of-thought-prompting

[^8_7]: https://neurips.cc/virtual/2023/poster/71632

[^8_8]: https://www.k2view.com/blog/chain-of-thought-prompting/

[^8_9]: https://prompton.wordpress.com/2025/06/20/🔍-self-correction-iterative-refinement-turning-ai-into-its-own-toughest-critic-🚀/

[^8_10]: https://www.helicone.ai/blog/chain-of-thought-prompting


---

# So I should just delete this part?  "- **What to remember in a week:**

> “Use a strong CoT reviewer prompt as the base, then run *one* ‘review‑of‑the‑review’ step and regenerate the critique once using that feedback. No ongoing self‑learning, just a single Self‑Refine loop around a fixed reviewer.”"

Keep it, but rewrite it so it explicitly points to your three prompts.

For example:

> **What to remember in a week:**
> “Run three steps:
> 1) PROMPT 1 = strong CoT reviewer on the work.
> 2) PROMPT 2 = review‑of‑the‑review (find misses/weak spots).
> 3) PROMPT 3 = regenerate the critique once, using PROMPT 2’s improvements.
> No ongoing self‑learning; just this one Self‑Refine pass.”

