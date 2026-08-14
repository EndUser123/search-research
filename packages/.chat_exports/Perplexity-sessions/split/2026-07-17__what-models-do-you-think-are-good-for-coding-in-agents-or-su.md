---
title: "what models do you think are good for coding in agents or subagents and why?"
date: "2026-07-17"
mode: "COPILOT"
uuid: "2d5e482a-7854-4e71-85ad-57ffce461881"
entry_count: 4
---

## Human

what models do you think are good for coding in agents or subagents and why?

## Assistant

For agent/subagent coding, I’d treat models in three broad roles: (1) primary “repo-scale” coders, (2) agile task coders, and (3) heavy long‑context/agentic orchestrators. Within that, Hy3, Qwen3‑Coder, Nemotron 3 Ultra, and your existing GLM/Minimax/local stack each fit very specific lanes rather than “one best coder.”[1][2][3][4]

I’ll keep this grounded in what you’re already wiring (CCR, Grok/or‑* agents, OpenRouter) and focus on subagent use, not generic chat coding. Confidence: medium–high, with explicit speculation flagged where evidence is thin.

***

## Core roles for coding agents

The most useful distinction is *role* rather than model: what exactly is the subagent doing.

- Repo‑scale reasoning and navigation over many files, tests, and tools.
- Focused “single artifact” coding (one file, one script, one hook).
- Long‑horizon agentic workflows: multi‑step plans, tool chains, and verification loops.[5]

In practice, the same model can serve multiple roles, but you get better predictability if you pin lanes:

- **Orchestrator / planner lane**: designs workflows, decomposes tasks, calls tools and subagents, and judges outputs.[4][5]
- **Heavy repo coder lane**: runs multi‑file edits, test updates, refactors, and CI integration.[3][6]
- **Fast “worker” coder lane**: implements localized changes, scripts, and glue code with low latency.

***

## Hy3 as a generalist coding + agentic subagent

Evidence: Hy3 is a MoE built for reasoning and agentic workflows, with 256K context, configurable “effort” (no‑think vs low/high CoT), and strong performance in coding/productivity scenarios.  You’ve also observed Hy3 is “good at coding” in real runs, which is more valuable than benchmarks for your specific harness.[2][7][1]

### Why Hy3 is strong for subagents

- **Agentic design**: Tencent explicitly targets tool‑calling, multi‑step reasoning, and operating inside pipelines; that’s exactly what you need for subagents inside Grok’s or‑* harness or CCR.[2][4]
- **Configurable thinking modes**: ability to flip between “fast, no‑think” and “high‑effort” chains gives you a natural way to differentiate subagent tiers (e.g., quick worker vs deep reviewer) without changing models.[2]
- **Long context**: 256K native context means Hy3 can hold a sizeable workspace or multi‑file patch set per subagent without constant rereads.[7][2]

### Best roles for Hy3 in your stack (CONSENSUS from evidence + your prior)

- Orchestrator for *coding‑heavy* multi‑step agents where you still want a free or cheap tier.[1][4][2]
- “Senior reviewer” subagent: evaluate GLM/Minimax/local outputs, run cross‑file consistency checks, highlight risk before commit/push.[7]
- Generalist coding subagent for mid‑size tasks when local Ornith/Minimax aren’t enough but you don’t want a flagship model.[2]

Assumption: Hy3’s real SWE‑bench style performance is competitive with other open MoEs; if you see it lag significantly in your harness, demote it to reviewer/planner and keep Qwen3‑Coder or Nemotron Ultra as heavy coders.

***

## Qwen3‑Coder as repo‑scale coding specialist

Evidence: Qwen3‑Coder is explicitly marketed and benchmarked as an “agentic code model” for long‑context, multi‑step programming tasks, with MoE architecture, strong SWE‑bench performance, and up to 256K–1M context variants.  It’s optimized for repository‑scale understanding, with a high code ratio in pretraining.[8][6][3]

### Why Qwen3‑Coder is good for coding subagents

- **Repo‑scale understanding**: up to 256K native context and extrapolation methods to ~1M give it the ability to hold an entire mid‑sized codebase in working memory, ideal for agents that must navigate, search, patch, and reason about structure.[6][3]
- **Agentic RL on SWE‑Bench**: Qwen3‑Coder is explicitly trained with long‑horizon reinforcement learning on SWE‑Bench‑like tasks, which resemble what your “fix bug from issue + run tests + patch” agents will do.[6]
- **Code‑heavy training mix**: ~70% code ratio means strong coding priors, less risk of hallucinating non‑idiomatic patterns compared to models with a more general mix.[6]

### Best roles for Qwen3‑Coder (FACT from model docs + SPECULATION about your harness)

- “Heavy coding” subagent for multi‑file edits: feature additions, refactors, plus test updates in one pass.[3][6]
- “Repository navigator” subagent: answer questions about architecture, find relevant modules, propose cutpoints for new features.[3][6]
- “Automated SWE agent” in lanes where you’d otherwise consider a proprietary flagship (e.g., Opus/Sonnet‑class), but want lower cost and open access.[3]

Given your routing preferences, Qwen3‑Coder maps well to your “Opus‑like reasoning + Sonnet‑like coding” composite for repo work, but as a single model that you pin per task type.

***

## Nemotron 3 Ultra as long‑context agentic powerhouse

Evidence: Nemotron 3 Ultra 550B is an open hybrid Mamba‑Transformer MoE with 1M context, explicitly fine‑tuned for agentic tasks (tool use, multi‑step reasoning, function calling, complex pipelines) and strong performance on SWE‑bench style coding agents.[9][4]

### Why Nemotron Ultra is valuable for agents/subagents

- **1M context**: that’s enough to hold very large repos, long transcripts, and multi‑tool traces per agent, reducing orchestration complexity for your lane layer.[9]
- **Agentic fine‑tuning**: NVIDIA’s positioning and benchmarks emphasize function calling and multi‑step workflows, similar to Hy3, but with more capacity and longer context.[4]
- **Competitive SWE‑bench performance**: reports indicate top‑tier results on coding agent tasks where the model must navigate a codebase, identify bugs, and generate working patches.[4]

### Best roles for Nemotron Ultra (FACT + cautious SPECULATION)

- “Max context” coding subagent when you genuinely need ~1M tokens (monorepo, huge logs, multi‑language services).[1][9]
- High‑authority “fixer” subagent when cheaper coders fail; triggered by CCR as a fallback lane with strict cost controls.[4]
- “Planning + execution” agent for long autonomous workflows (e.g., migrating a subsystem, implementing a multi‑service feature) under human‑in‑the‑loop guardrails.[5][4]

Given your cost sensitivity, this is not your default worker; it’s the “escalate only when necessary” lane, similar to Opus in your current mental model.

***

## How these compare to your existing GLM / Minimax / local stack

From your memory: you’re already routing GLM‑5.2 for reasoning, Minimax M3 for coding, DeepSeek for flash tasks, plus a local Ornith‑1.0‑9b as an underutilized coder.  These remain excellent for many subagents, especially if you value throughput, low latency, and local control.

### Where they shine

- **Minimax M3**: strong coder with good context and speed for single‑file or small multi‑file tasks; ideal as a “fast worker” subagent.
- **GLM‑5.2**: great for planning and high‑level reasoning, often used as an Opus proxy in your routing; good orchestrator/architect, less specialized for deep repo coding than Qwen3‑Coder.
- **Ornith‑1.0‑9b (local)**: ideal for well‑defined coding tasks with high throughput, particularly when you want to maximize local work and minimize API spend.

### Gaps that Hy3 / Qwen / Nemotron fill (CONSENSUS + SPECULATION)

- Very long context + tool‑first agentic behavior (Hy3, Nemotron).[9][2][4]
- Repo‑scale coding specialization (Qwen3‑Coder) vs general reasoning/coding mix in GLM/Minimax.[3][6]
- Open, agent‑optimized models tuned on SWE‑bench‑like tasks, which may outperform generic models when used as autonomous coders.[4][6]

So the pragmatic answer is not “replace GLM/Minimax/local with Hy3/Qwen/Nemotron” but “add these as specific lanes and only trigger them when needed.”[1]

***

## Suggested role table for coding agents/subagents

Here’s a concrete mapping you could encode in CCR or Grok’s or‑* harness.

| Role / lane                    | Priority models                                  | Why this fits                                                                 |
|--------------------------------|--------------------------------------------------|-------------------------------------------------------------------------------|
| Fast single‑file worker        | Minimax M3, local Ornith‑1.0‑9b                  | Low latency, good coding, cheap/high throughput; ideal for most trivial tasks  |
| Repo‑scale coder               | Qwen3‑Coder (30B or larger), Nemotron 3 Ultra   | Long context, SWE‑bench tuned, multi‑file patches, test updates               [3][4] |
| Generalist coding + tools      | Hy3                                             | Long context, agentic design, configurable effort; good all‑round coder       [2][7][1] |
| High‑level planner/orchestrator| GLM‑5.2, Hy3, Nemotron 3 Ultra                  | Strong reasoning, tool calling, multi‑step workflows                          [4][2] |
| Senior reviewer subagent       | Hy3, Qwen3‑Coder                                | Cross‑file consistency, design checks, risk review before apply               [7][3] |
| “Max context emergency” fixer  | Nemotron 3 Ultra                                | 1M context, high accuracy reasoning over big repos/logs                       [9][4] |

Each lane can be pinned per *task type* (e.g., “repo‑edit”, “single‑file‑script”, “review”) in CCR, with autoswitching only when no pin is active, as you already prefer.

***

## Next steps for you (actionable)

Given your architecture and preferences, I’d suggest:

1. **Empirically benchmark in your harness**  
   - Run a small set of standard coding agent tasks (e.g., SWE‑bench style issues, multi‑file refactor, test addition) across Hy3, Qwen3‑Coder, Nemotron Ultra, Minimax M3, GLM‑5.2, and Ornith‑1.0‑9b.[6][4]
   - Log success rate, patch validity, test pass rate, latency, and token cost per task; wire this into your “epistemic audit” logger.

2. **Codify lane mapping in CCR**  
   - Add task‑type → model mappings roughly as in the table above, using GLM‑5.2 for planning and Minimax/Ornith for fast work, Qwen/Nemotron for heavy repo work, and Hy3 as generalist/reviewer.[1]
   - Keep Hy3 near the top of “coding quality” lanes given your prior, even if its name doesn’t say “coder.”[7][1]

3. **Guardrails and fallbacks**  
   - Implement “on_failure: escalate lane” logic: local/Minimax first, then Hy3/Qwen, then Nemotron only when repeated failures or context overflow.[4]
   - Add a simple falsifier: if Hy3 consistently beats Qwen/Nemotron in your real agent tasks, promote it; otherwise keep it as reviewer/planner.[1]

Open question that would change the recommendations substantially: are you prioritizing *local* execution (e.g., Ollama qwen3‑coder, local Nemotron variants) over cloud, or is OpenRouter/Together acceptable for your core coding agents right now?

## Human

with openrouter, free models still cost money.  is the cost for a 1M context free model the same as a 200K free model?

There are other models, why not consider them?

## Assistant

Short answer: no, a “1M context free model” and a “200K context free model” on OpenRouter do **not** all cost the same; you have to treat “free” as a tag with rate‑limit and routing semantics, not “all usage is zero‑cost,” and then pick from a broader set of models based on actual per‑token prices and your workload.[1][2][3]

I’ll split this into (1) how OpenRouter “free” and context interact, and (2) why we should widen the candidate pool beyond Hy3/Qwen/Nemotron for coding agents.

***

## How “free” and context actually work

FACT: OpenRouter exposes multiple notions of “free”:

- **`openrouter/free` router**: a special pseudo‑model that routes you to one of several free models; it’s explicitly priced at **$0.00 per 1M input and $0.00 per 1M output tokens**, with a ~200K context window.[4][1]
- **Model IDs with `:free` suffix** (e.g., `tencent/hy3:free`, some Gemini/Meta/Mistral variants): these are specific free tiers whose per‑token price is also listed as **$0.00/1M** in the pricing calculator.[2][3][1]

So at the *pricing* layer:

- If the pricing page says “$0.00 / 1M input, $0.00 / 1M output” for that **exact** model ID (including `:free` suffix), your marginal *token* cost is zero, regardless of whether the context window is 200K or 1M.[3][1][2]
- If you call the non‑`:free` version (e.g., `tencent/hy3` without suffix, or Nemotron Ultra paid tier), you pay the per‑token price given, independent of its context length.[1][2]

CONSENSUS: context size affects *what you can do* per call (how many tokens you can pack into a single request), but does not directly change the **price per million tokens** listed; price and max context are separate columns on the compare/pricing pages.[5][6]

Where the confusion usually comes from:

- OpenRouter has historically warned that if you don’t include `:free`, even for models that have a free tier, **you get charged**, because you’re hitting the paid tier.[7]
- “Free” models have **rate limits** (requests per minute/day, global caps) and may be **subsidized** by OpenRouter or provider promo; the fact that they’re zero‑price now doesn’t mean they always will be, or that you can hammer them indefinitely.[8][9][2][3]

So: a “1M context free model” and a “200K free model” are both $0.00/1M tokens if they’re listed as free, but their **effective cost to you** differs because:

- Larger context invites you to stuff far more tokens per call (so if that free tier disappears or turns paid, you’ve built habits around bigger invoices).  
- Free models have tighter rate limits; the higher‑context ones may be rate‑limited more strictly to protect infrastructure.[9][8][3]

Assumption (SPECULATION, but common pattern): when OpenRouter or providers later convert a “free” tier into paid, longer‑context versions tend to be **priced higher per million tokens** than shorter‑context siblings, simply because the infra cost scales with KV/cache size and bandwidth. Their current free tier may mask that future differential.[5][2][3]

***

## Why we should consider “other models” for coding agents

You’re absolutely right: Hy3/Qwen/Nemotron are not the whole story. OpenRouter’s free/promo ecosystem includes a **lot** of strong coders and agentic models that could sit in your CCR lanes.[10][6][2]

FACT: current OpenRouter free/low‑cost lineup includes models like:

- **Google Gemini 2.0/2.5 Flash free tiers** – 1M context, good code+reasoning, strong tool‑calling, often zero‑cost in promo/free lanes.[3]
- **Meta Llama 3.x / 4 Scout/Maverick free tiers** – large MoE with ~256K context and strong coding performance.[10]
- **DeepSeek R1 / V4 Flash** – free or low‑cost reasoning/coding models with good performance per dollar.[11][3]
- **Mistral “Devstral” / Small 3.1‑24B** – coding‑optimized, sometimes exposed as free or very cheap.[3][10]

These are worth considering for agents/subagents because:

- They often have **code‑specific tuning** (e.g., Mistral/MiMo coding models, Llama coding‑heavy variants) and solid benchmarks, not just generic chat performance.[12][6][10]
- Some have **extremely favorable value curves**—e.g., MiMo‑V2‑Flash, DeepSeek V4 Flash, etc.—with strong real coding performance at a fraction of flagship cost.[12][11]

CONSENSUS from practitioner posts and pricing lists: best value for coding agents tends to cluster around:

- **Mid‑size “flash” coders** (MiMo‑Flash, DeepSeek Flash, Gemini Flash) for high‑throughput workers.[6][11][12]
- **Large MoE coders with long context** (Mistral Devstral, Llama‑4 Scout/Maverick, Qwen3‑Coder) for repo‑scale or long‑horizon tasks.[13][14][10]

So when we say “other models,” I’d concretely add:

- Fast worker lane: MiMo‑V2‑Flash, DeepSeek V4 Flash, Gemini Flash, plus your Minimax/local.[11][12]
- Repo coder lane: Qwen3‑Coder, Mistral Devstral, Llama‑4 Scout/Maverick.[6][13][10]
- Reasoner/orchestrator lane: Hy3, DeepSeek R1, Gemini Pro/Exp, Nemotron Ultra.[15][16][10][3]

SPECULATION with medium confidence: for your use case (heavy coding, multi‑agent orchestration, CCR), it’s more useful to pick **2–3 strong “value” coders and 1–2 strong orchestrators** than to chase every free model. OpenRouter’s compare/pricing pages make that tractable.[12][6]

***

## Practical way to choose among all these

Given your cost focus and multi‑provider routing:

1. **Use OpenRouter’s compare/pricing view as the ground truth.**  
   - Filter by “best for code” and “most affordable” and record: price per 1M, context, benchmarks.[17][6]
   - Explicitly check whether the models you care about have `:free` tiers and what their limits are.[2][3]

2. **Separate “pricing reality” from “current promo.”**  
   - Treat current free tiers as “temporary subsidies”; design CCR so that if/when a free tier flips to paid, you can swap in nearby alternatives without breaking lanes.[8][2][3]
   - Prefer models whose *paid* per‑token price is already tolerable for you, so a promo ending doesn’t blow up your budget.[11][12]

3. **Empirically rank a shortlist.**  
   - Build a small internal benchmark: 5–10 coding tasks (single‑file and repo‑scale), run them across Hy3, Qwen3‑Coder, DeepSeek Flash, MiMo‑Flash, Mistral Devstral, Llama‑Scout/Maverick, plus your Minimax/GLM/local.[10][6][12]
   - Track success, latency, and token usage per task; then choose 3–4 “production lanes” and ignore the rest.

***

## Cost vs context: how to reason about it for CCR

Putting it in one sentence: **context length multiplies how much you *can* spend per request, price per 1M tokens multiplies how much you *actually* pay, and “free” multiplies how long that remains true.**[5][1][3]

So for designing agent/subagent lanes:

- Don’t assume “1M free context = same economic profile as 200K free context”; assume “both are zero now, but 1M invites you to burn more tokens and will likely be more expensive if/when pricing changes.”[2][5][3]
- Prefer **shorter‑context, cheaper‑per‑token models for high‑throughput workers**, and reserve 1M‑context models (Nemotron, Gemini Flash Pro, etc.) for rare “big repo / long logs” workflows.[18][11][3]
- Wire CCR with per‑lane caps (tokens/task, model choice) rather than relying purely on “free” label, so your behavior doesn’t break when OpenRouter tweaks free tiers or rate limits.[8][2]

***

Concrete next question that will help narrow the “other models” list: do you want me to constrain candidates to **OpenRouter’s current “best for code” + “most affordable” cluster**, or do you still want to include frontier‑class models (GPT‑5.x, Claude Fable, Gemini Pro) in the agent design even if they’re rarely used?

## Human

openrouter has a minimun cost per token don't they?

Note I'm think of grok build cli not ccr.

## Assistant

They don’t have a “minimum cost per token” across the board; they have a **minimum fee on credit purchases**, and then each model has its own per‑million‑token price (including $0 for true free tiers).  For Grok Build CLI specifically, the underlying Grok Build model has a normal per‑token rate, even though the CLI itself is bundled into xAI’s subscription.[1][2][3][4][5][6]

I’ll separate OpenRouter’s cost floor from Grok Build’s economics.

***

## OpenRouter: fees vs per‑token pricing

FACT from OpenRouter docs:

- **Credits & fees**: when you buy credits, OpenRouter charges a **5.5% fee with an $0.80 minimum** on the purchase.[7][5]
  - Example: load $10 of credits → pay $10.55 total; load $5 → pay $5.28 (because of the minimum).[5][7]
- **Per‑token pricing**: each model has its own **$ per 1M input tokens and $ per 1M output tokens**, visible on the model pages and compare tool. There is no global “minimum price per token”; prices differ widely by model.[8][9]

So economically:

- There *is* a minimum **fee per credit purchase**, not a minimum **price per token** across the board.[7][5]
- Once you have credits, you pay **exactly the per‑token rate of the model** (plus that initial fee), or $0 if you’re using a true free model tier with $0/1M pricing.[3][1]

FACT on free models:

- OpenRouter’s own blog says: “Are OpenRouter’s free models really free? Yes, **$0 per token**. Limits are 50 requests/day on a free account, 1,000/day once you add credits.”[3]
- The `openrouter/free` router and `…:free` model variants are shown as **$0.00/1M input, $0.00/1M output**, with their own context window (often ~200K for router, more or less for specific models).[10][11][12]

So from a token‑pricing perspective:

- There’s **no floor like “minimum $0.10 per 1M tokens”**; each model can be 0, $0.02, $0.20, $1.25, etc., depending on upstream provider.[13][8]
- Your effective minimum is the combination of “cheapest model you’re willing to use” plus the **initial credit fee**.

***

## Grok Build CLI economics

You flagged this isn’t CCR; it’s Grok Build CLI. That changes the cost story:

- **Grok 4.5** (general xAI model) is listed around **$2 per 1M input tokens and $6 per 1M output tokens** in current comparisons.[2]
- **`x-ai/grok-build-0.1`** (the model powering Grok Build CLI on OpenRouter) is documented as **$1 per 1M input tokens, $2 per 1M output tokens**, with **256K context** and no hard output limit.[4]
- Grok Build CLI itself is bundled into xAI’s subscription (SuperGrok / Grok Build plans), which you pay as a flat monthly fee (e.g., $99–$300/month in current promos/tiers) and then get “nearly unlimited” usage within that plan’s internal limits.[14][6][2]

Two layers here:

1. **OpenRouter side:** if you hit Grok Build via OpenRouter, you pay the Grok Build per‑token rate ($1/1M in, $2/1M out) plus OpenRouter’s credit fee, unless you’re on some arrangement where tokens are bundled.[4][5][7]
2. **xAI subscription side:** if you use the Grok Build CLI that talks directly to xAI, you pay the **subscription price** (SuperGrok, Grok Build tier) and then the token usage is covered inside that bundle, with whatever soft caps xAI enforces.[6][2][14]

CONSENSUS from current reviews: Grok Build CLI is **not** a “free” coding solution; it’s part of xAI’s higher‑end subscription and effectively locks you into Grok family models for most of that CLI’s workflows.[15][2][6]

***

## How this matters for your Grok Build CLI use

For the Grok Build CLI context (rather than CCR):

- There is no OpenRouter‑level “minimum price per token” that applies universally; you pay Grok Build’s documented rate when using it through OpenRouter, or the xAI subscription if you’re using the official CLI.[2][14][4]
- Your *real* floor is: “minimum subscription tier you’re willing to pay for Grok Build + OpenRouter credit fee, plus the cheapest adjacent models you might call from Grok agents,” not a generic per‑token floor.[5][15][7]

If you’re designing Grok Build CLI‑centric agents (or subagents) and care about cost:

- Treat Grok Build as your **fixed baseline coder** (with known $1/$2 per‑M pricing and 256K context) and be deliberate about how much context you send each turn.[4]
- If/when Grok Build CLI lets you swap underlying models (xAI has hinted at different Grok variants and OpenRouter shows multiple xAI models), you’d want a small shortlist of cheaper coders for non‑critical tasks, but that’s more in Kilo‑style CLIs than in Grok’s current “locked into Grok” beta.[15][6]

***

One dimension that would help tailor this: are you thinking of **Grok Build CLI as a primary day‑to‑day coding surface**, or more as a “spike/experiment” tool while CCR + Claude Code remains the main control plane?

## Human

please critically review your recommendations and do internet search to support your claims.

## Assistant

You’re right to ask for a critical review; some of my earlier statements need tightening and clearer evidential backing. I’ll walk through the main claims, what the current web evidence actually supports, where I overstated or speculated, and how I’d adjust the recommendations for Grok Build CLI and model choice. Confidence: medium–high overall, with explicit notes where data is incomplete or promo‑biased.

***

## FACT: What OpenRouter actually says about “free” and pricing

**Claim I made:** “Free models are $0 per token, there’s a 5.5% fee with an $0.80 minimum on credit purchases, and there is no global minimum cost per token.”  

Evidence now:

- OpenRouter’s pricing/overview and third‑party pricing guides confirm:  
  - A **platform fee of 5.5%** on credit purchases (5% for crypto), with a **$0.80 minimum per transaction**.[1][2][3]
  - Once credits are bought, **you spend them at provider model rates**; there is no extra per‑token markup from OpenRouter beyond that fee.[4][1]
- Model pricing is defined per model: “All pricing values are in USD per token/request/unit; a value of `\"0\"` indicates the feature is free.”[5]

So:

- FACT: OpenRouter has a **minimum platform fee**, not a universal minimum token price.[2][1]
- FACT: Some models have pricing value `0` → truly free per token usage (subject to rate limits), others have whatever $/M rate their provider sets.[6][5]

Where my phrasing was slightly loose:

- I said “free models are $0 per 1M tokens”; that’s accurate when the pricing column shows 0, but not every model in the “free models collection” stays zero forever—promo free tiers can convert, and some entries in that collection include non‑zero image pricing, etc.[7][6]
- I implied OpenRouter itself “has no minimum price per token”; more precise: it **passes through underlying provider token prices**, and the only *global* minimum is the **platform fee on credit purchases**.[1][2]

**Adjusted recommendation (CONSENSUS):**  
For Grok‑based or other agent systems, treat OpenRouter pricing as:

- A per‑model **token rate** that may be zero or non‑zero.[8][5]
- A **fixed fee for credit top‑ups**, which is your real floor.[2][1]

Don’t assume “free collection” = permanently zero‑cost; check the per‑model pricing fields and design your lanes so you can swap models if a promo ends.

***

## FACT: Grok Build model pricing vs CLI subscription

**Claim I made:** “Grok Build 0.1 is ~$1/1M input, $2/1M output; Grok 4.5 is ~$2/1M in, $6/1M out; CLI is bundled in xAI’s subscription.”  

Evidence:

- Requesty and xAI docs show **grok‑build‑0.1** priced at **$1.00 per million input tokens, $2.00 per million output tokens**, with **256K context**.[9][10][11]
- Comparison articles mention **Grok 4.5** at roughly **$2 input, $6 output per million tokens**, with context and performance tuned for general reasoning.[12]
- Grok Build CLI is described as part of **SuperGrok/Grok Build subscriptions**, with flat monthly fees and “full access” to Grok Build features.[13][14][15][12]

So:

- FACT: **grok‑build‑0.1** has a standard per‑token price when accessed via OpenRouter or direct API.[10][11][9]
- FACT: The CLI side is a **subscription product**, not a pay‑per‑token usage model in isolation; your total cost is subscription fee plus any underlying API usage limits.[14][12][13]

Where I was speculative:

- I said “nearly unlimited usage” inside the subscription; actual limits are not clearly documented publicly yet and likely include soft caps or fair‑use terms. That was speculation based on marketing tone rather than explicit quotas.[13][14]

**Adjusted recommendation (CONSENSUS):**  
For Grok Build CLI:

- Treat **grok‑build‑0.1** as a **256K‑context coding model with known per‑token prices** when accessed via APIs.[11][9][10]
- Treat the CLI as a **subscription interface** whose economics are dominated by the monthly fee and whatever hidden or soft limits xAI enforces; don’t assume it is “cheap unlimited coding.”[12][14][13]

If you’re evaluating Grok Build as a spike tool, log token usage and outcome quality against cost for a week, then decide if it deserves a persistent lane.

***

## FACT: Hy3, Qwen3‑Coder, and Nemotron 3 Ultra as agentic coding models

**Claims I made:**

1. Hy3 is a MoE model with 256K context, built for agentic workflows and coding.  
2. Qwen3‑Coder is a long‑context agentic code family (256K native, 1M extended) with strong agentic coding performance.  
3. Nemotron 3 Ultra is a 550B MoE with 1M context, tuned for long‑running agents and SWE‑bench‑style coding tasks.

Evidence now:

- **Hy3:**  
  - Tencent’s model card: Hy3 is a **295B‑parameter MoE** (21B active), designed for **agentic workflows and production**, with **256K context**, stable tool‑calling, long‑horizon tasks, and anti‑hallucination behavior.[16][17]
  - Target domains include **coding**, document processing, finance analysis, game dev, and frontend design. Coding is explicitly listed as a use case.[16]

- **Qwen3‑Coder:**  
  - InfoQ and Qwen blog: Qwen3‑Coder is “a new family of **agentic code models** designed for **long‑context, multi‑step programming tasks**.”[18][19]
  - The top variant (480B MoE, 35B active) supports **256K context natively, 1M with extrapolation**, and achieves **state‑of‑the‑art results among open models on Agentic Coding, Browser‑Use, and Tool‑Use**, comparable to Claude Sonnet 4 on those benchmarks.[19]

- **Nemotron 3 Ultra:**  
  - NVIDIA’s blog: Nemotron 3 Ultra is a **550B MoE** with **55B active parameters**, “built for frontier reasoning and orchestration in agentic systems.”[20]
  - It is designed to “help long‑running agents complete tasks faster while lowering cost,” with experiments on SWE‑Bench and Terminal Bench 2.0 showing **fewer total tokens and fewer tokens per turn** than comparable models.[20]
  - Model cards on OpenRouter describe **1M context** and strong agentic tool‑use performance.[21][22]

These directly back the core framing:

- FACT: Hy3, Qwen3‑Coder, and Nemotron 3 Ultra are explicitly agentic and explicitly suitable for coding.[17][22][18][19][16][20]
- FACT: Qwen3‑Coder and Nemotron 3 Ultra in particular are **repo‑scale, long‑context** models tuned on real‑world tasks (SWE‑bench style) where the model acts as an autonomous coder.[19][20]

Where I extrapolated:

- I framed Qwen3‑Coder as “ideal heavy repo coder” and Nemotron Ultra as “emergency max context fixer”; that’s consistent with their docs, but it’s still SPECULATION as to whether they outperform alternative models *specifically in your harness* versus GLM, Minimax, or frontier closed‑source models.[20][19]
- I implied Hy3 can fully replace repo‑scale coders; in reality, its training mix covers coding but doesn’t claim SWE‑bench SOTA like Qwen3‑Coder/Nemotron; it’s more a strong generalist agent than a pure code specialist.[17][16]

**Adjusted recommendation (CONSENSUS + SPECULATION):**

- Hy3: **generalist reasoning + tools model** with good coding support; ideal orchestrator/reviewer, solid mid‑tier coder, but not necessarily your best repo‑scale coder.[16][17]
- Qwen3‑Coder: **primary repo‑scale agentic coder** for open‑weight setups, especially when you need 256K–1M context and strong SWE‑bench performance.[19]
- Nemotron 3 Ultra: **agent orchestrator and long‑context powerhouse** for rare, big tasks; use it sparingly due to size, even if it’s open‑weight.[21][20]

The *fact* is that they’re very credible candidates; the *speculative* part is their relative ranking vs your existing GLM/Minimax/local stack, which you need to test.

***

## FACT & CONSENSUS: Other models worth considering

You asked “There are other models, why not consider them?”—my earlier answer gestured at Gemini, Llama, DeepSeek, MiMo, etc. Let’s now anchor that properly:

- OpenRouter’s **“Best AI Models for Coding”** collection includes Hy3 among others, but also highlights **DeepSeek, MiMo, Llama, Gemini, GLM, Mistral** coding‑oriented models.[8][17]
- Qwen’s blog and open‑source ecosystems point to **Qwen2.5‑Coder, Qwen3‑Coder** as top open coders.[19]
- NVIDIA and independent guides highlight **Nemotron 3 Ultra** and allied models as strong agentic options.[22][20]
- Cost calculators and Reddit comparisons show high “value scores” for models like **MiMo‑V2‑Flash, DeepSeek variants, GLM‑5, Kimi**, i.e., good intelligence per dollar.[23][24]

So the “other models” I named are not arbitrary; they show up in:

- Official “best for code” collections.[17][8]
- Provider blogs as “agentic coding” models.[20][19]
- Community cost/value comparisons.[24][23]

However, I should have been clearer that:

- There is **no single global ranking**; performance depends on task type, harness, and prompts. Benchmark SOTA doesn’t always correlate with your particular coding workflow.[20][19]
- Your existing GLM‑5.2, Minimax M3, DeepSeek, Kimi, and local Ornith are themselves competitive; the question is whether Hy3/Qwen/Nemotron/DeepSeek/MiMo etc. outperform them for specific agent roles *in your environment*, not in abstract.[23][8]

**Adjusted recommendation (CONSENSUS):**

- Use OpenRouter’s **coding collection and compare tool** to build a shortlist: Hy3, Qwen3‑Coder, Nemotron 3 Ultra, DeepSeek V4 Flash/R1, MiMo‑V2‑Flash, GLM‑5, Gemini Flash, Llama‑4 Scout/Maverick, Mistral’s devstral.[23][24][8][17]
- Then do **your own harness‑level bake‑off** rather than relying purely on marketing or third‑party blogs.

***

## SPECULATION: My earlier lane mapping vs reality

I proposed a lane table (fast worker, repo coder, orchestrator, reviewer, max‑context fixer). That was architecturally reasonable, but:

- It’s **speculative** which exact model should own each lane for you, because no public data covers “performance inside your CCR/Grok agent skeleton + your style of prompts + your codebases”.  
- Public benchmarks (SWE‑Bench, Terminal Bench) are helpful but not decisive; NVIDIA’s Nemotron blog shows token efficiency vs competitors but not against GLM/Minimax/local Ornith specifically.[20]

Given your explicit preference for epistemic audit and falsifiers, the more honest stance is:

- Treat that lane mapping as a **hypothesis**.  
- Implement logging and head‑to‑head experiments to **falsify or confirm** each model’s recommended lane.

***

## Concrete next steps (strongly recommended, now evidence‑backed)

Adjusting for the critical review, here’s what I’d suggest you actually do for Grok Build / OpenRouter‑centric agent design:

1. **Ground model selection in OpenRouter’s own metadata.**  
   - Pull model data from OpenRouter’s API/compare pages: price per 1M, context, provider, “best for coding” tags.[5][8][17]
   - Encode those into your Grok agent harness as **structured metadata** (e.g., JSON for lanes), not hard‑coded intuitions.

2. **Run a small, focused benchmark in your environment.**  
   - Choose 5–10 coding tasks (single‑file fixes, multi‑file refactor, test addition, CLI/tool integration).  
   - Run them across: Grok‑Build‑0.1, Hy3, Qwen3‑Coder, Nemotron 3 Ultra, DeepSeek Flash, MiMo‑Flash, GLM‑5.2, Minimax M3, Ornith‑1.0‑9b.[11][23][16][19][20]
   - Log: success rate, test passes, tokens used, latency, and subjective readability.

3. **Use cost evidence to set guardrails.**  
   - For Grok Build CLI: treat **$1/2 per‑M** for Grok‑Build and your subscription fee as upper bounds; design agents to minimize unnecessary context stuffing and to short‑circuit failed attempts.[9][10][12][13]
   - For OpenRouter models: factor in **per‑token price and context** from model cards, not just “free collection” membership.[5][1][8]

4. **Iteratively refine lane assignments with falsifiers.**  
   - Example falsifier: “If Hy3 loses >20% of head‑to‑head coding tasks vs Qwen3‑Coder in my harness, demote it from repo‑coder lane.”[16][19]
   - Another: “If Nemotron 3 Ultra uses more tokens and time than Qwen3‑Coder for mid‑size repos, reserve it only for truly massive contexts.”[21][20]

***

If you’d like, next step I can propose a **JSON lane spec** specifically for a Grok Build CLI‑based agent harness, with each model annotated by `price`, `context`, and `role`, all grounded in current OpenRouter/xAI docs rather than my earlier informal mapping.
