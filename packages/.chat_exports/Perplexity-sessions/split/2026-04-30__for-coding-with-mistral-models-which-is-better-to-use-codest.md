---
title: "for coding, with mistral models which is better to use?   codestral-latest or devstral-2512?"
date: "2026-04-30"
mode: "CONCISE"
uuid: "c44bc2f4-fb40-4753-bd99-b5d875d6aa75"
entry_count: 3
---

## Human

for coding, with mistral models which is better to use?   codestral-latest or devstral-2512?

## Assistant

For coding work, **Devstral 2512 is better if you're building agentic systems with code generation**; **Codestral-latest if you prioritize cost and need a general-purpose model**.[1][2]

## Performance & Specialization

Devstral 2 2512 outperforms Codestral on coding benchmarks and is specifically tuned for agentic code workflows. Devstral 2 reaches 72.2% on SWE-bench Verified and shows a 42.8% win rate against DeepSeek V3.2 in human evaluations. It has a 256K context window (vs. Codestral's 256K), so both handle similarly-sized codebases. Devstral 2's 123B parameters are 5x smaller than DeepSeek V3.2 while matching performance, making it practical for deployment.[3][1]

## Cost Trade-off

Codestral is cheaper on input tokens ($0.30/M vs. Devstral's $0.40/M), but Devstral is cheaper on output ($0.90/M vs. $2.00/M). However, Codestral's blended rate is $0.80/M while Devstral Small 2 is $0.40/M—a significant difference if you're cost-constrained. The key insight: **if your workflow is read-heavy (analyzing code), Codestral wins on cost; if write-heavy (generating code in loops), Devstral's output pricing matters less end-to-end**.[2][4][1]

## Tool-Calling Reliability

Devstral 2512's tool-calling reliability is the best in Mistral's lineup, which matters for multi-step agentic loops where the model chains tools autonomously. Codestral lacks this specialization.[2]

**Recommendation**: Use **Devstral 2512 for agentic code-generation workflows** (write-test-iterate loops, tool chains); use **Codestral or Mistral Large 2512 for general coding tasks** where you're more likely to read existing code than generate large volumes.[2]

## Human

is there a devstral-latest?

## Assistant

There is no public `devstral-latest` alias in the way Mistral exposes `codestral-latest`; you generally have to target a specific Devstral version such as `devstral-2512` (or “Devstral 2 2512”).[1][2]

## What Mistral actually ships

Mistral’s own announcement and downstream hosts (OpenRouter, Ollama, HF, etc.) talk about concrete Devstral versions, not a rolling “latest” tag:  

- Mistral announces **Devstral 2** as a model family (Devstral 2, Devstral Small 2) with specific checkpoints like **2512**.[3][1]
- OpenRouter lists `mistralai/devstral-2512` with that exact name, including price and context, but does not show a `devstral-latest` alias.[2]
- Hugging Face similarly uses concrete names like `Devstral-Small-2-24B-Instruct-2512`, again no `-latest`.[3]

That’s in contrast to Codestral, where wrappers and some providers expose a **`codestral-latest`** convenience alias.[4]

## Practical implication

So if your provider’s API model list doesn’t explicitly show `devstral-latest`, assume it does not exist and use the explicit version, e.g.:

- `mistralai/devstral-2512` on OpenRouter.[2]
- `Devstral-Small-2-24B-Instruct-2512` or similar on HF / local runtimes.[3]

If you tell me which provider / SDK you’re using (Mistral direct, OpenRouter, Fireworks, local, etc.), I can map the exact Devstral model string you should plug into your code.  

## Human

I using the mistral provider with bifrost, but don't see devstral 2 in the auto discovered models.

## Assistant

You’re running into a limitation of Bifrost’s auto‑discovery, not Mistral’s API: Devstral 2 is available from Mistral, and Bifrost’s model catalog shows it, but it may not be included in the automatic list your instance is pulling.[1][2]

## What Bifrost supports today

Bifrost’s own public model library for the Mistral provider lists multiple Devstral variants, including both versioned and `-latest` aliases:[2]

- `mistral/devstral-2512` (Devstral 2, 123B, 256k context, functions)  
- `mistral/devstral-latest` (same pricing/limits as 2512)  
- `mistral/devstral-medium-2507` and `mistral/devstral-medium-latest`  
- `mistral/devstral-small-2505`, `-2507`, and `devstral-small-latest`  

So: from Bifrost’s perspective, Devstral 2 *is* a supported model; it’s just not surfacing in your auto‑discovered list.

## Why auto-discovery may not show Devstral

Likely causes, given their Mistral provider docs and model catalog:  

- **Static model list or caching**: Your Bifrost deployment may be using a cached / pinned model list that predates Devstral 2, instead of pulling the latest catalog.[3][4]
- **Subset filters**: Some configs restrict to “default” / “stable” models; Devstral family might be marked differently in the catalog and thus filtered out.[4]
- **Different list endpoint**: The “List Models” endpoint described for the Mistral provider is OpenAI‑compatible, but not every wrapper updates their discovery to include new SKUs immediately.[3]

Given that the public catalog has Devstral entries now, this is almost certainly a configuration or versioning issue on the Bifrost side, not that Devstral is missing.[2][4]

## How to use Devstral 2 with Bifrost anyway

Because Bifrost is OpenAI‑compatible for Mistral, you can typically bypass auto‑discovery and just set the model id explicitly in your client code:[3][2]

Use one of:

- `model: "mistral/devstral-2512"`  
- or, if you want a rolling alias: `model: "mistral/devstral-latest"`  

as long as your Bifrost version and config accept arbitrary Mistral model names (most do).

If that fails with “model not found” or similar, next steps:

1. **Check your Bifrost version**  
   Ensure you’re on a build from 2026 or later that includes the Devstral entries present in their model catalog.[4][2]

2. **Check Bifrost’s provider config**  
   In the `mistral` provider block, look for any `allowed_models` / `default_models` or similar list. If it whitelists specific Mistral models, add:  
   - `mistral/devstral-2512`  
   - and optionally `mistral/devstral-latest`  

3. **Force a model catalog refresh**  
   Some gateways cache model metadata; check Bifrost docs or UI for a “refresh models” / “sync catalog” action or restart with cache cleared.[4]

4. **Confirm directly against Mistral**  
   If you can hit Mistral’s API outside Bifrost, call their list‑models or just send a test chat with `model: "devstral-2-25-12"` / `devstral-2512` as per their model card.[1]
   If that works, you know the problem is strictly in Bifrost.

If you paste your Bifrost `mistral` provider config (redact keys), I can suggest an exact minimal edit that should make Devstral 2 selectable.  
