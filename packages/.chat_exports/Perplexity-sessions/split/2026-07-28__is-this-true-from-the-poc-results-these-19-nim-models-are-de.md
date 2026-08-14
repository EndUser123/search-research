---
title: "Is this true? 'From the POC results, these 19 NIM models are dead (410 Gone or 404 Not Found):

┌────┬──────────────────"
date: "2026-07-28"
mode: "COPILOT"
uuid: "a936e5fd-49dc-46a5-aeef-628310ede50e"
entry_count: 2
---

## Human

Is this true? "From the POC results, these 19 NIM models are dead (410 Gone or 404 Not Found):

┌────┬──────────────────────────────────────────────────┬───────────────┐
│ #  │ Model slug                                       │ Error         │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 1  │ nim-bytedance-seed-oss-36b-instruct              │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 2  │ nim-meta-llama-3-1-nemotron-70b-instruct         │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 3  │ nim-nvidia-llama-3-1-nemotron-ultra-253b-v1      │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 4  │ nim-mistralai-mistral-small-4-119b-2603          │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 5  │ nim-qwen-qwen2-5-coder-32b-instruct              │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 6  │ nim-qwen-qwen3-coder-480b-a35b-instruct          │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 7  │ nim-qwen-qwen3-next-80b-a3b-instruct             │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 8  │ nim-qwen-qwen3-5-122b-a10b                       │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 9  │ nim-qwen-qwen3-5-397b-a17b                       │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 10 │ nim-microsoft-phi-4-mini-instruct                │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 11 │ nim-meta-llama-4-maverick-17b-128e-instruct      │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 12 │ nim-microsoft-phi-4-multimodal-instruct          │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 13 │ nim-mistralai-mistral-medium-3-5                 │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 14 │ nim-mistralai-mistral-7b-instruct-v0-3           │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 15 │ nim-mistralai-mixtral-8x7b-instruct              │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 16 │ nim-mistralai-mixtral-8x22b-instruct-v0-1        │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 17 │ nim-mistralai-mistral-large-3-675b-instruct-2512 │ 410 Gone      │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 18 │ nim-mistralai-magistral-small-2506               │ 404 Not Found │
├────┼──────────────────────────────────────────────────┼───────────────┤
│ 19 │ nim-mistralai-ministral-3-14b-instruct-2512      │ 404 Not Found │
└────┴──────────────────────────────────────────────────┴───────────────┘

Plus 4 that timed out (provisional — may be temporary NVIDIA outages):

┌────┬──────────────────────────────────────────────┬─────────┐
│ #  │ Model slug                                   │ Status  │
├────┼──────────────────────────────────────────────┼─────────┤
│ 20 │ nim-deepseek-ai-deepseek-v4-flash            │ timeout │
├────┼──────────────────────────────────────────────┼─────────┤
│ 21 │ nim-meta-llama-3-2-3b-instruct               │ timeout │
├────┼──────────────────────────────────────────────┼─────────┤
│ 22 │ nim-nvidia-llama-3-1-nemotron-nano-8b-v1     │ timeout │
├────┼──────────────────────────────────────────────┼─────────┤
│ 23 │ nim-nvidia-llama-3-3-nemotron-super-49b-v1-5 │ timeout │
└────┴──────────────────────────────────────────────┴─────────┘

The 19 dead models are all NVIDIA NIM hosted — they were available when added to config but have since been deprecated or removed from NVIDIA's catalog. Many of these are also available through other providers (OpenRouter, OpenCode/Zen) where they may still work."

## Assistant

I can’t fully verify the entire 23-model list from the evidence I found, but the blanket claim “these 19 NIM models are dead” is **not proven** as stated. What I *can* confirm is that NVIDIA’s current public catalog still shows many active NIM models, and at least some of the slugs in your list appear to have changed naming or packaging rather than being definitively “dead.”[1][2]

## What the evidence supports

NVIDIA’s live model catalog on build.nvidia.com currently lists 127 models and includes several NVIDIA-hosted/free-endpoint models that are clearly active as of July 2026, such as `deepseek-v4-flash`, `mistral-medium-3.5-128b`, `nemotron-3-ultra-550b-a55b`, `nemotron-3.5-content-safety`, `nemotron-3-nano-omni-30b-a3b-reasoning`, and `deepseek-v4-pro`.[1]
That means the broader statement “NVIDIA NIM models are being deprecated/removed across the board” is false.[1]

## What looks questionable

One of your listed slugs, `nim-qwen-qwen2-5-coder-32b-instruct`, appears to correspond to an active NVIDIA/Qwen model page, but the current public slug format is different: the page shows `qwen2.5-coder-32b-instruct` and the example NIM path uses `nim/qwen/qwen2.5-coder-32b-instruct:latest`, which suggests a naming mismatch rather than an indisputably dead model.[2]
So at least some of the “404/410” results may reflect stale config slugs, alias drift, or endpoint-path changes, not necessarily permanent removal.[2]

## What is still plausible

It is plausible that several of your 19 entries are truly retired or unavailable on NVIDIA’s hosted API, because NVIDIA forum posts and third-party writeups explicitly describe some models returning 404 when they have been retired from hosted service, and NVIDIA has publicly deprecated specific model access in the past.[3][4]
But that still does **not** let us conclude all 19 are dead without checking each slug against the current catalog or the underlying API response.[4]

## Best current judgment

My confidence is **medium-low** that the exact “19 dead models” claim is correct as written, and **medium-high** that the underlying problem is real: some of those config entries are likely stale, renamed, or no longer hosted on NVIDIA’s free/public NIM endpoints.[4][2][1]
The stronger, more defensible statement is: “A subset of these slugs no longer resolve on NVIDIA’s hosted NIM service, but some may still exist under updated names or through other providers.”[5][4]

## Next step

The right way to validate this is to do a slug-by-slug check against NVIDIA’s current `/models` catalog and, where needed, the current API endpoint behavior for each model name.[4][1]
Would you like me to turn your 23 entries into a verified matrix with columns for current NVIDIA status, likely rename/alias, and alternative providers?

## Human

fix the slugs, don't change provider away from nvidia

## Assistant

The slugs need to be updated to NVIDIA’s current naming/ID scheme; for several of the models you listed, there is clear evidence of newer, working NVIDIA NIM identifiers, while others appear genuinely retired from hosted NIM.[1][2][3][4][5][6][7]

Below is a **focused mapping** for models where there is reasonably strong evidence of a correct, current NVIDIA-style slug, staying with NVIDIA as provider. I’m keeping this concise and only correcting what we can actually ground in current docs or catalog entries.

## Strongly supported corrections

These are cases where NVIDIA or partner docs show a clear model identifier and NIM container path.

| Old slug (from your list)                            | Correct/current NVIDIA identifier (model field / NIM image)                                     | Evidence |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------|---------|
| `nim-meta-llama-3-1-nemotron-70b-instruct`           | `nvidia/llama-3.1-nemotron-70b-instruct` (model); `nvcr.io/nim/nvidia/llama-3.1-nemotron-70b-instruct:latest` | NVIDIA build page and NGC catalog show this exact ID and NIM image name. [2][8] |
| `nim-mistralai-mistral-medium-3-5`                   | `mistralai/mistral-medium-3.5-128b` (model); `nvcr.io/nim/mistralai/mistral-medium-3.5-128b:latest` | NVIDIA’s build.nvidia.com and NGC catalog use this as the NIM model; Medium 3.5 is surfaced via this slug. [3][4][9][7] |
| (generic “mistral-medium-3.5” alias)                 | `mistralai/mistral-medium-3.5-128b`                                                               | Release notes describe “mistral-medium-3.5” with an alias but NVIDIA NIM front-end uses the full `-128b` slug. [4][6] |
| `nim-qwen-qwen2-5-coder-32b-instruct`                | `nim/qwen/qwen2.5-coder-32b-instruct:latest` (NIM image); `qwen/qwen2.5-coder-32b-instruct` (model) | NVIDIA’s Qwen page shows this exact NIM path and model identifier; the difference is dot vs hyphen and org prefix. [10] |
| `nim-bytedance-seed-oss-36b-instruct`                | `nim/bytedance/seed-oss-36b-instruct:latest` (NIM image); `bytedance/seed-oss-36b-instruct` (model) | Free-model reference and NVIDIA-hosted docs use `bytedance/seed-oss-36b-instruct` as the ID; NIM images follow `nim/<org>/<slug>:latest`. [1] |

In all of these cases, your config slugs look like “OpenRouter-style” or custom slugs rather than the canonical NVIDIA NIM identifiers; updating to the `org/slug` pattern (and using dots where NVIDIA does) should fix 404s when you call the NIM-compatible `/v1/chat/completions` endpoint against your own NIM container or NVIDIA’s integrate API.[2][3][10][1]

## Likely-deprecated or unavailable via hosted NIM

For at least one of the models in your list, NVIDIA support explicitly says they no longer host it on their NIM endpoints:

- Llama 3.1 Nemotron 70B Instruct: a later NVIDIA forum thread states “we no longer host the Llama 3.1 nemotron 70b model” and recommends using newer Nemotron variants such as “Llama 3.3 Nemotron Super 49b” or “Nemotron nano 9b v2” instead.[5]

So even with a correct slug (`nvidia/llama-3.1-nemotron-70b-instruct`), hosted NIM calls may return 404/410 because the model has been removed from NVIDIA’s production catalog, while the container image and Hugging Face checkpoint remain available for self-hosting or other providers.[11][2][5]

Several of your “dead” Mistral slugs (e.g., `nim-mistralai-mistral-small-4-119b-2603`, `nim-mistralai-mistral-large-3-675b-instruct-2512`) look like older or internal IDs that are not present in the current NVIDIA public catalog; the catalog shows only a small set of Mistral slugs such as `mistral-medium-3.5-128b`.[3][4][12]
Without an explicit mapping table from NVIDIA, these are best treated as **deprecated or renamed** rather than simply “fixable” by slug edits.

## What I cannot safely “fix” yet

For the remaining entries in your 19 + 4 list (e.g., `nim-qwen-qwen3-coder-480b-a35b-instruct`, `nim-nvidia-llama-3-1-nemotron-ultra-253b-v1`, `nim-mistralai-magistral-small-2506`, `nim-mistralai-ministral-3-14b-instruct-2512`, and the timeout-only Nemotron/Qwen variants), I don’t find authoritative NVIDIA documentation with matching public slugs or obvious new identifiers.[12]

Given NVIDIA’s catalog is actively changing and some models are clearly being removed or rebalanced, the most accurate stance is:

- FACT: They do **not** appear in the current public build.nvidia.com model catalog under those slug patterns.[12]
- CONSENSUS: They are likely deprecated/retired or only available as internal/private containers rather than general hosted endpoints.[13][14][5]
- SPECULATION (low confidence): Some may have direct replacements with similar names (e.g., newer Nemotron “super” models) but I can’t assign exact slugs without NVIDIA’s own mapping.[14]

So I will **not** guess replacements for those; doing so risks giving you wrong IDs that look plausible but still 404 on NIM.

## Practical next step for your config

For each model you want to keep on NVIDIA, I’d recommend this flow:

1. Look up the model by concept (e.g., “Nemotron 70B”, “Mistral Medium 3.5”, “Seed OSS 36B”, “Qwen coder 32B”) directly on build.nvidia.com and copy the exact `org/slug` identifier from their curl examples.[10][1][2][3][12]
2. In your router/config, set:
   - `model` to the canonical ID (e.g., `mistralai/mistral-medium-3.5-128b`).[3]
   - For self-hosted NIM, set the image to `nvcr.io/nim/<org>/<slug>:latest`.[2][3]
3. For any slug where NVIDIA’s catalog does not list a matching model, either:
   - Mark it as deprecated/unavailable in your config, or  
   - Replace it with a currently-listed NVIDIA model that matches the intended capability (e.g., swap “3.1 Nemotron 70B” for “3.3 Nemotron Super 49b”).[5][12]

If you paste your current config for one or two representative entries (e.g., one Nemotron, one Mistral, one Qwen), I can rewrite them line-by-line with corrected NVIDIA NIM slugs and endpoint settings.
