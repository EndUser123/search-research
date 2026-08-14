---
title: "I'm getting an error with a Kimi K3 in Claude Code and Grok build. How am I supposed to set it up for an agentic CLI?"
date: "2026-07-26"
mode: "COPILOT"
uuid: "c449cc19-1609-42df-b02a-a4259c76cf59"
entry_count: 4
---

## Human

I'm getting an error with a Kimi K3 in Claude Code and Grok build. How am I supposed to set it up for an agentic CLI?

## Assistant

Yes — but the clean setup depends on **which endpoint** you are actually targeting. For agentic CLI use, Kimi’s own coding endpoint is the most authoritative documented path for Claude Code, while generic “Moonshot Anthropic-compatible” setups appear in third-party guides and may work differently or break on tooling assumptions.[1][2]

## Likely issue

If you are seeing errors in Claude Code or Grok Build, the most common root cause is mixing two different integration modes: Kimi Code’s dedicated Claude Code integration uses `ANTHROPIC_BASE_URL=https://api.kimi.com/coding/` with `ANTHROPIC_API_KEY`, while many unofficial guides use `https://api.moonshot.ai/anthropic` with `ANTHROPIC_AUTH_TOKEN`. Those are not documented by Kimi as the same setup path, so combining variables from both usually leads to auth, model-selection, or tool-routing failures.[1][2]

A second common issue is model/context mismatch: Kimi documents `k3-256k` and `k3[1m]` specifically for Claude Code, and says the `k3[1m]` form is only for Claude Code environment variables. If you pass the wrong model string or omit the matching context window env vars, agentic sessions can fail or compact badly.

## Claude Code setup

For Claude Code, the authoritative Kimi setup is:

1. Create a Kimi Code API key in the Kimi Code Console and make sure your membership tier includes the model/context you want. Kimi says Allegretto and above can use K3 with up to 1,048,576 context, while lower tiers may be limited to 262,144 or different model variants.
2. Skip Claude’s default login flow by patching `~/.claude.json` as Kimi’s docs describe, because their guide explicitly says not to start Claude first and provides a script that enables third-party model support and onboarding completion.
3. Set all Claude-facing model vars to the same Kimi model, including the subagent model, so the harness does not silently delegate parts of the workflow to a different default model.

For **PowerShell 7 on Windows**, use this for the 1M setup:

```powershell
$env:ANTHROPIC_BASE_URL="https://api.kimi.com/coding/"
$env:ANTHROPIC_API_KEY="YOUR_KIMI_CODE_KEY"

$env:ANTHROPIC_MODEL="k3[1m]"
$env:ANTHROPIC_DEFAULT_FABLE_MODEL=$env:ANTHROPIC_MODEL
$env:ANTHROPIC_DEFAULT_OPUS_MODEL=$env:ANTHROPIC_MODEL
$env:ANTHROPIC_DEFAULT_SONNET_MODEL=$env:ANTHROPIC_MODEL
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL=$env:ANTHROPIC_MODEL
$env:CLAUDE_CODE_SUBAGENT_MODEL=$env:ANTHROPIC_MODEL

$env:CLAUDE_CODE_EFFORT_LEVEL="high"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW="1048576"
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS="1048576"

claude
```

That block matches Kimi’s own Claude Code docs, including the requirement to use `k3[1m]` only in Claude Code env vars.

For the cheaper/default daily-driver setup, Kimi recommends `k3-256k` and notes it gives the same results within 256k context while consuming about half the quota of `k3` 1M. That is often the better default for an agentic CLI unless you truly need long-repo context or large transcript history.

## Grok Build setup

I could not verify, from an authoritative xAI CLI doc page, that Grok Build supports the same Kimi endpoint override mechanism as Claude Code. I found third-party material describing Grok Build as an agentic CLI, but I do **not** have a fetched primary-source configuration reference showing Kimi-as-backend support there, so I would treat “Kimi K3 in Grok Build” as unverified until you confirm xAI’s current CLI supports custom OpenAI/Anthropic-compatible endpoints.[3]

So the safe assumption is:

- **FACT:** Claude Code can be pointed at Kimi Code via Kimi’s documented env-var method.
- **UNCERTAIN:** Grok Build may or may not let you swap its backend to Kimi in the same way; I do not have primary-source confirmation here.[3]
- **Best practical pattern:** use Claude Code as the orchestrator harness for Kimi-backed agentic coding, and use Grok Build separately when you want Grok-native behavior rather than forcing one CLI to impersonate the other. This also aligns with your stated preference to keep Claude Code as an orchestrator and avoid fragile piecemeal setups.

## Agentic CLI pattern

For an agentic CLI, the important part is not just “make one prompt work,” but making the whole loop consistent: main model, fallback model labels, and subagents should all resolve to Kimi. Kimi’s docs explicitly show setting the default Fable, Opus, Sonnet, Haiku, and subagent variables to the same Kimi model, which is exactly what you want to prevent mixed-model behavior inside the harness.

Use this operating pattern:

- Default to `k3-256k` for most coding tasks to reduce quota burn.
- Switch to `k3[1m]` only for big-repo analysis, multi-file refactors, or long-context agent loops.
- Keep thinking enabled; Kimi says disabling thinking routes K3/K2.7 Code to K2.6, which means you may think you are on K3 while actually running something else.
- Verify with `/status`; Kimi says success is confirmed when Base URL shows `https://api.kimi.com/coding/`, even if the displayed model label still looks like a Claude model.

## Debug checklist

If it is failing right now, check these in order:

- Remove any old `ANTHROPIC_AUTH_TOKEN` if you are using the Kimi Code endpoint path, because Kimi’s official Claude Code doc uses `ANTHROPIC_API_KEY` instead.
- Make sure `ANTHROPIC_BASE_URL` is exactly `https://api.kimi.com/coding/` with trailing slash if you are following Kimi’s official path.
- Make sure every default model env var points to the same Kimi model.
- Match context numbers exactly to the model, `262144` for `k3-256k` or `1048576` for `k3[1m]`.
- Run `/status` after launch and verify the Base URL, not the friendly model label.
- If you previously configured Claude with another provider, clear stale model IDs/settings first; Kimi’s login-skip script explicitly removes old model env entries from Claude settings.

My confidence is **high** on the Claude Code setup because it comes from Kimi’s own docs, and **low to medium** on Grok Build using Kimi as a backend because I do not yet have a primary-source xAI config proving that path.[3]

Paste the exact error text plus your current env block with keys redacted, and I’ll turn it into a minimal known-good PowerShell setup for your Windows agentic CLI.

## Human

How about setting up K3 with OpenCode or Pi coding agent?

## Assistant

Yes. OpenCode is the **cleaner** K3 integration right now because Kimi documents it directly, while Pi appears to support Kimi through its provider model and ecosystem, but the exact setup path depends on whether you use Pi’s built-in `kimi-coding` provider or an extension.[1][2]

## OpenCode

Kimi’s own OpenCode docs say to install OpenCode, run `opencode auth login`, select **Kimi For Coding**, paste a Kimi Code API key from the Kimi Code Console, then start `opencode` and choose a model with `/models`. The documented K3 options are `k3` for the flagship model and `k3-256k` for the cheaper 256K-context variant.

Minimal flow:

```bash
npm install -g opencode-ai
opencode auth login
opencode
/models
/variants
```

Inside login, choose **Kimi For Coding**; inside `/models`, choose `k3` or `k3-256k`; inside `/variants`, set reasoning effort. Kimi documents OpenCode’s effort mapping as `Default -> high`, `low -> low`, `high -> high`, and `max -> max`, with `high` recommended.

For agentic CLI work, I’d default OpenCode to `k3-256k` unless you truly need long-horizon repo context, because Kimi states `k3` 1M consumes about twice as much quota as `k3-256k` while delivering the same results within 256K context. Kimi also warns that calling models or context windows beyond your membership tier will fail.

## Pi agent

For Pi, I found evidence that Pi supports a `kimi-coding` provider using the Anthropic Messages API with base URL `https://api.kimi.com/coding`, a 1,048,576 context window for `k3`, and config fields for `apiKey`, `baseUrl`, and model metadata. That strongly suggests Pi can run K3 cleanly, but this came from Pi model/provider docs rather than Kimi’s own third-party setup page.[2][1]

The simplest Pi pattern appears to be:

```bash
npm install -g @earendil-works/pi-coding-agent
export KIMI_API_KEY="YOUR_KEY"
pi
```

Then select the `kimi-coding` provider and `k3` model, or configure it in Pi’s model/provider config. Pi’s provider docs list `KIMI_API_KEY` as the env var for **Kimi For Coding** and note that Pi can also add providers through `models.json` or extensions.[3][4][2]

## Pi options

There are two realistic Pi setup paths:

- **Built-in provider path:** use Pi’s native `kimi-coding` provider with `KIMI_API_KEY`; this looks like the most direct and least fragile approach.[1][2]
- **Extension path:** install a Kimi-specific Pi extension such as `pi-provider-kimi-code`, which adds login reuse, file uploads, cache behavior, and optional extra tooling; this is more powerful, but also adds another moving part.[5]

A built-in-style config based on the Pi model page would look roughly like this:

```json
{
  "providers": {
    "kimi-coding": {
      "apiKey": "YOUR_API_KEY",
      "api": "anthropic-messages",
      "baseUrl": "https://api.kimi.com/coding",
      "models": [
        {
          "id": "k3",
          "name": "Kimi K3",
          "reasoning": true,
          "contextWindow": 1048576,
          "maxTokens": 131072
        }
      ]
    }
  }
}
```

That shape is consistent with the published Pi model page for K3, including provider name, API type, base URL, context window, and max tokens.[1]

## Recommendation

For your workflow, I would treat **OpenCode as the fastest low-friction K3 harness** and **Pi as the more extensible provider-agnostic harness**. That matches your preference for an orchestrator/delegation setup and for durable, platformized solutions instead of brittle one-off hacks.

Use this default decision rule:

| Use case | Better fit | Why |
|---|---|---|
| Quick K3 coding sessions | OpenCode  | Kimi documents the exact login and model-selection flow.  |
| Provider-agnostic routing, custom providers, extension-heavy workflows | Pi [2][3] | Pi is designed as a multi-provider harness with custom provider support. [2][3] |
| Lowest setup risk | OpenCode  | Fewer config surfaces, direct Kimi docs.  |
| Maximum flexibility | Pi [5][2] | Built-in provider plus extension path. [5][2] |

## Caveats

Two things are still uncertain. First, Kimi’s own “third-party coding agents” help page explicitly names Claude Code, Roo Code, and OpenCode, and says Kimi Code benefits are supported only in **Kimi Code CLI, Claude Code, and Roo Code**; that wording may mean OpenCode is documented but not included in the benefits statement on that page, or it may simply be an inconsistency between Kimi docs pages. I would trust the dedicated OpenCode doc for actual setup, but note the inconsistency.

Second, for Pi I found strong ecosystem evidence but not an official Kimi-authored step-by-step page for K3-on-Pi specifically. So my confidence is **high** for OpenCode and **medium** for Pi until you confirm which Pi version/provider screen you have.[2][1]

If you want, I can give you either:
- a **PowerShell setup checklist** for OpenCode on Windows, or
- a **minimal Pi `models.json` / provider config** for K3 with sane defaults for agentic coding.

## Human

Does K3 have a native CLI?

## Assistant

Yes — K3 has a **native CLI**, and Kimi’s own launch materials point to **Kimi Code** as the terminal agent for using K3. Kimi says K3 is available in Kimi Code, and their blog explicitly says to “run Kimi Code in your terminal and select Kimi K3 using the `/model` command.”[1][2]

## What that means

The native CLI is not “K3 by itself”; it is the **Kimi Code** agent that runs K3 under the hood. That CLI is designed to read and edit files, run shell commands, and manage agentic coding loops, which is the same class of workflow as Claude Code or Codex CLI.[3][4]

Kimi’s docs also show Kimi Code as the official terminal coding agent, invoked with the `kimi` command, and describe it as open source and MIT-licensed. That makes it the closest thing to a native CLI for K3.[4]

## Practical answer

If you want the native path, use Kimi Code rather than trying to wire K3 directly into a generic harness first. The model is selected inside the CLI with `/model`, and Kimi’s docs say you can choose `kimi-k3` there.[2][3]

For Windows or cross-platform setup, the important distinction is:

- **K3** = the model.[2]
- **Kimi Code** = the native CLI harness.[4]
- **`/model kimi-k3`** = the model selection step inside that harness.[3]

## Caveat

I did not find evidence that “K3” ships as a standalone binary separate from Kimi Code. The official docs instead frame K3 as something you use **through** Kimi Code, or through other agents like Claude Code, OpenCode, or Codex via compatible routing.[5][2]

If you want, I can give you the exact **native Kimi Code install steps for Windows PowerShell** next.

## Human

How long can I use K3 for free?

## Assistant

Not indefinitely. The **free Kimi product tier exists**, but the exact amount of K3 you can use for free is quota-based and can change, and Kimi does not publish one stable “X days” guarantee for free K3 usage.[1][2][3]

## What’s actually free

Kimi’s current pricing/quickstart materials indicate K3 is available in the product with a free tier, but that tier is limited by plan entitlements and usage caps rather than a time-unlimited free license. The official quickstart also says K3 uses flat pay-as-you-go API pricing, which means the API side is not a free-permanent offer.[3][1]

## Practical interpretation

For normal chat/product use, you can use the free tier until you hit its message, agent, or rate limits. For agentic coding, the free allowance can disappear much faster because long-context and tool-using workflows consume tokens aggressively. Third-party reports describe the free tier as having limited agent credits and possible peak-time pauses, but those are not as authoritative as Kimi’s own docs.[4][2][5]

## Important distinction

There are two different “free” questions:

- **Consumer/product free tier:** free access with limits.[2][4]
- **API/free developer usage:** not something Kimi documents as a permanent free entitlement; the API is described as paid usage.[1][3]

So the honest answer is: **you can use K3 for free only within a limited, changing quota; there is no guaranteed unlimited free period.**[2][3]

If you want, I can help you estimate how long your own workflow will last on the free tier based on your expected prompt size and agent loop frequency.
