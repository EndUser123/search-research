---
title: "in claude code on windows 11, I'm using the z.ai glm-5.1 model.  I keep getting this halting error:


● Update(Stop.py)"
date: "2026-05-06"
mode: "CONCISE"
uuid: "e0f8016d-8a6e-4b3d-8251-e98dc2ab2ce6"
entry_count: 5
---

## Human

in claude code on windows 11, I'm using the z.ai glm-5.1 model.  I keep getting this halting error:


● Update(Stop.py)
  ⎿  Error editing file
  ⎿  API Error: 400 invalid params, context window exceeds limit (2013)

## Assistant

You’re hitting Z.ai’s much smaller *Anthropic/Claude-compatible* context limit from Claude Code, not GLM‑5.1’s full native window.[1][2]

## What’s actually happening

Claude Code is talking to Z.ai through the Anthropic‑compatible endpoint, which uses Anthropic’s request schema and limits.[3][1]
Even though GLM‑5.1 can handle ~200k tokens natively, Z.ai’s Anthropic bridge caps the usable context much lower, and Claude Code’s edits (including the full file, diff, and history) are pushing that over the limit, giving you: `API Error: 400 invalid params, context window exceeds limit (2013)`.[2][1]

This is why:

- The error only happens on edits like `Update(Stop.py)` where Claude Code sends a big context bundle.[4][5]
- The same GLM model works fine in simpler clients (or after `/clear`) but fails in Claude Code once there’s history + multiple files.[1]

My confidence that this is a context‑size issue mediated by the Anthropic‑compat layer is **high**, but the exact token limit for that bridge is **uncertain**, since Z.ai only documents generic 400 errors and rate limits, not per‑endpoint context sizes.[3]

## Things to try inside Claude Code

These are low‑effort changes that often unblock GLM on Claude Code.[5][1]

1. Clear the bloated conversation
   - Run `/clear` in Claude Code to drop the current session’s history.[5][1]
   - Retry the edit with a fresh prompt and just the necessary files.

2. Reduce what Claude Code sends
   - Temporarily close unneeded files from the workspace before asking for edits, so they’re not included in context.[4][5]
   - For large files, copy the relevant snippet into the chat and ask it to generate a patch, then apply manually, instead of using “Edit in place”.

3. Turn on / tweak auto‑compaction
   - If you’re using CC Switch / Antigravity‑style config, ensure auto‑compact is enabled at something like 100k, so Claude Code aggressively summarizes history.[1]
   - If you already have auto‑compact, lower the threshold (e.g., 50k) so summarization happens earlier.

4. Prefer smaller, more targeted edits
   - Ask for refactors/file changes in smaller chunks (one function or section at a time) instead of “rewrite the whole file and related files”.[6][7]
   - This keeps the system’s planning + code context from blowing out the limit on each tool call.

## Config / model choices that help

Because the integration between Claude Code and GLM‑5.1 via Z.ai is still a bit brittle, several users are seeing similar 400s and “invalid params” errors.[8][7][1]

Options:

- Try a different GLM variant  
  Some people report GLM‑4.6 is a bit more stable with tooling than 5.x in similar “external agent” setups, although it still has 400 issues in some editors.[7][8]

- Use OpenCode CLI for Z.ai instead of Claude Code  
  At least one person moved their GLM usage from Claude Code to OpenCode and stopped seeing these 400 “invalid parameter” errors, because that client shapes prompts more like OpenAI.[7][1]

- Check you’re on the Anthropic base URL Z.ai expects  
  For GLM with Claude‑style tools, users use an Anthropic‑compatible base such as `https://api.z.ai/api/anthropic` (exact path depends on current docs).[3][1]
  A mismatched URL or header can cause extra “invalid param” 400s on top of the context issue.[5][3]

Given your setup, this is not you “doing something wrong” so much as Claude Code producing very aggressive, Anthropic‑shaped prompts against a narrower Anthropic‑bridge context window on Z.ai.[1][5]

## Concrete next steps for you

In your situation (Windows 11, Claude Code, GLM‑5.1 via Z.ai), I’d do this, in order:

1. In the Claude Code session with the error:
   - Run `/clear`.[5][1]
   - Re‑run the same edit request once, see if it works.

2. If it still fails:
   - Close other open files so they’re not pulled into context.[4][5]
   - Ask Claude Code to edit just a small part of `Stop.py` instead of the entire file.

3. If it’s recurrent on that workspace:
   - Enable or lower auto‑compaction in your Claude Code config (if you’re using the Antigravity / CC Switch pattern).[1]
   - Optionally try GLM‑4.6 or another Z.ai model in the same config to see if the error pattern changes.[8][7]

4. If you need big multi‑file edits with GLM right now:
   - Consider running those via OpenCode CLI or another editor that’s known to play better with GLM‑5.x prompt shapes, as others have done.[7][1]

Would you be open to sharing your exact Claude Code model configuration block for Z.ai (base URL, model name, extra headers)? That’s the single most useful detail to debug next.  

## Human

"Enable or lower auto‑compaction in your Claude Code config (if you’re using the Antigravity / CC Switch pattern).", what is this pattern?

## Assistant

That line was confusing in context: there isn’t actually an “Antigravity / CC Switch pattern” inside *Claude Code* itself, and Claude Code doesn’t expose any user‑configurable “auto‑compaction” setting today.[1][2]

## What I meant vs what really exists

- Claude Code has its **own internal compaction** logic (via things like a hidden `/compact` operation), but you can’t tune it from a config file the way you can in some third‑party routers/IDEs.[3][1]
- Tools like OpenClaw or some Antigravity‑style IDEs implement explicit, user‑tunable **auto‑compaction** (e.g., `agents.defaults.compaction.*` in OpenClaw) and commands like `/compact` that you can wire into many assistants.[2][4]
- There is *no* officially documented “CC Switch pattern” in Claude Code’s own docs; that phrase comes from community patterns where people route traffic between Claude/OpenAI/GLM through an external orchestrator and let that orchestrator do compaction.[1][2]

So: inside pure “Claude Code on Windows 11” without an external router, you don’t have a knob to “enable or lower auto‑compaction”. My earlier phrasing implicitly assumed you were running Claude Code *through* one of those routers (like OpenClaw or a similar tool), which was a bad assumption.

## What matters for your GLM‑5.1 setup

Given that you’re directly using Z.ai’s GLM‑5.1 with Claude Code:

- Claude Code will try to manage context on its own, but it’s tuned around Anthropic’s models and their error signatures, not Z.ai’s GLM bridge.[5][3]
- Z.ai’s Anthropic‑compatible endpoint is returning `context window exceeds limit (2013)`, which Claude Code doesn’t always recognize as a “compact and retry” case, so you just see the 400 error.[6][5]
- Because you can’t adjust Claude Code’s internal compaction parameters, your levers are mostly:
  - Reduce per‑turn context (smaller edits, fewer open files, shorter history).[7][3]
  - Occasionally start a fresh session (`/clear`) when the transcript gets long.[2][3]

If you *are* actually running Claude Code traffic through something like OpenClaw / a router, then “auto‑compaction” refers to the router’s compaction settings, not Claude Code’s. In that case you’d be editing JSON like `agents.defaults.compaction.maxTokens`, `keepRecentTokens`, etc., and using `/compact` to force a summary.[8][2]

To tailor this properly: are you using Claude Code directly against Z.ai, or do you have any router/proxy (OpenClaw, custom gateway, etc.) sitting between Claude Code and Z.ai?  

## Human

are there hooks with our without claude agent sdk ideas that can change our compact behavior?

## Assistant

Yes—**with limits**. Claude Code now exposes `PreCompact` and `PostCompact` hooks, so you can run logic before or after a compaction event, and the Agent SDK exposes the same lifecycle hooks programmatically.[1][2][3]

## What hooks can do

Hooks can intercept lifecycle events such as tool calls, session start/stop, permission requests, and compaction events, including `PreCompact` and `PostCompact`.[2][1]
That means you can attach shell commands, HTTP endpoints, or SDK callbacks that run when Claude Code is about to compact context, which is useful for logging, archiving the transcript, or injecting extra instructions about what should be preserved.[4][1][2]

What hooks **can** influence:
- Preserve important state elsewhere before compaction runs.[1][2]
- Add guidance so the summary keeps architecture decisions, open TODOs, or file targets.[5][4]
- Trigger your own workflows around compaction, such as transcript snapshots or telemetry.[2][1]

## What hooks cannot do

Hooks do **not** give you a documented knob to change Claude Code’s internal compaction algorithm, token threshold, or summary strategy in the built-in CLI the way an external router might.[3][2]
So if your goal is “make Claude Code compact earlier” or “replace its summarizer,” the answer in plain Claude Code is mostly **no**, at least from the public docs I found.[3][2]

This distinction matters for your GLM/Z.ai case:
- FACT: hooks exist for `PreCompact`/`PostCompact`.[1][2]
- FACT: SDK users can create custom slash commands and manage context programmatically.[6][3]
- SPECULATION, medium confidence: you may be able to *shape* compaction outcomes by feeding better preservation hints in `PreCompact`, but not truly change when Claude Code decides to compact.[4][5][1]

## Agent SDK path

If you use the Claude Agent SDK instead of the stock CLI flow, you get more control over context management because the SDK exposes the same agent loop and supports custom slash commands, hooks, and automatic compaction controls in SDK workflows.[7][6][3]
Anthropic’s cookbook also documents `compaction_control`, where the SDK can compact automatically once token usage crosses a configurable threshold, clear history, and resume from a generated summary.[7]

That means:
- In plain Claude Code CLI, hooks are mostly adjuncts around compaction.[2]
- In an SDK-based wrapper or gateway, you can implement your own compaction policy more directly, including earlier thresholds and custom summary prompts.[3][7]

## Practical ideas for you

For your setup, the most promising pattern is not “hack Claude Code compaction,” but “wrap Claude Code behavior with preservation logic or move the session loop into SDK/gateway control.”[7][1][3]

Useful patterns:
- `PreCompact` hook writes a snapshot of current task state, touched files, open decisions, and next action into a scratch file, so loss from compaction is lower.[1][2]
- Custom slash command like `/prepare-compact` that asks the model to emit a structured working-memory note before you manually run `/compact`.[8][6]
- SDK/gateway compaction policy that triggers earlier than Claude Code would, especially for GLM models behind smaller compat-layer limits.[3][7]

For your exact Z.ai GLM‑5.1 problem, I’d challenge one premise: if the 400 happens **before** Claude Code decides to compact, then hooks alone may not save you, because the provider rejects the oversized request upstream.[9][2][1]
In that case, the stronger fix is an SDK or gateway layer that monitors token growth and compacts *before* requests reach Z.ai’s effective limit.[7][3]

Would you like a concrete design for a Windows-friendly gateway pattern—`PreCompact` hook only, SDK wrapper, or full proxy that compacts early for GLM?

## Human

I'm not really that interested in a gateway, unless we can do it in bifrost.

## Assistant

Yes—**Bifrost is the one place this idea makes sense** for your stack. Claude Code itself gives you hooks around compaction, but not real control over the compaction policy; Bifrost, as an Anthropic-compatible gateway, is where you could add earlier detection, preservation, and selective request shaping before Z.ai rejects the request.[1][2]

## What this means

Claude Code has built-in `/compact` plus hook points around compaction events, but those are mostly lifecycle triggers, not a full policy engine you can tune for GLM compatibility.[3][4][5][6]
Bifrost, by contrast, already sits in the request path and presents an Anthropic-compatible surface, so it is the natural place to implement model-aware safeguards for smaller effective context limits on providers like Z.ai’s compatibility layer.[1][2]

So your instinct is good: avoid a separate gateway if Bifrost can do it, because Bifrost is already your gateway.

## Realistic options in Bifrost

There are three levels of intervention, and only the first two are low-risk.[1][2]

- **Request budgeting:** estimate prompt size before forwarding, then reject early with a clearer local error or route to a safer model before Z.ai returns `400 context window exceeds limit`.[1]
- **Pre-forward trimming:** remove or compress obviously low-value parts of the request, such as stale chat history, while preserving system messages and recent tool context.[2][1]
- **True auto-compaction:** generate a summary/handoff note and replace old history automatically before forwarding. This is the most powerful option, but also the riskiest because it can subtly break tool flows or lose working state if done naively.[7][8]

I would challenge one premise, though: “change compact behavior” can mean two different things. If you mean “change Claude Code’s built-in compaction,” Bifrost cannot directly alter that internal algorithm.[6][3]
If you mean “make the overall system survive smaller GLM context limits,” Bifrost absolutely can help by enforcing a provider-aware preflight policy before the request reaches Z.ai.[1][2]

## Best fit for your setup

For your stack, the best minimal intervention is a **GLM-specific preflight in Bifrost** rather than a new standalone gateway.
That preflight would inspect incoming Anthropic-style `messages`, estimate tokens conservatively, and when near your configured GLM threshold, do one of these actions in order: warn, trim, summarize, or reroute.[8][2][1]

A practical policy might look like this:

- For Anthropic models, pass through normally.[2]
- For `z.ai/glm-5.1`, enforce a lower soft limit than the advertised native model window because the Anthropic-compatible bridge appears narrower in practice.[9]
- If estimated usage exceeds the soft limit:
  - First choice: return a structured local error telling Claude Code to `/clear` or reduce scope.
  - Second choice: if you add summarization later, compact older turns into a synthetic handoff block.
  - Third choice: reroute to a fallback route/model that tolerates larger Claude-shaped prompts better.

That gives you a strong safety net without trying to reimplement Claude Code itself.[1][2]

## Hooks plus Bifrost

If you want hooks *and* Bifrost, the clean pattern is:

- Use Claude Code `PreCompact` to write a lightweight working-memory snapshot, such as repo, files in play, task goal, constraints, and pending edits.[10][5][6]
- Use Bifrost preflight to keep requests under the GLM-compatible threshold.[2][1]
- Optionally have Bifrost inject that snapshot back as a high-priority system block after trimming older chat.[8][1]

That combo is stronger than hooks alone, because hooks help preserve intent, while Bifrost handles the provider-specific limit enforcement that Claude Code does not know about.[5][6][1]

My confidence is **high** that Bifrost is the right place for this in your architecture, and **medium** on how aggressive automatic summarization should be before it starts hurting coding reliability.[7][8]

## Recommended next step

I’d start with the smallest safe change: implement a Bifrost middleware for your Anthropic endpoint that does **token estimation + GLM soft-limit enforcement + explicit local error messaging**, with no automatic summarization yet.[1][2]
Once that is stable, add an opt-in `autoCompactForGLM` mode in Bifrost for only the GLM routes, not globally, so Anthropic-native flows stay untouched.[8][2]

Would you like a concrete Bifrost middleware design in TypeScript or Python for the Anthropic-compatible path?

## Human

yes please.  Woudl there be admin actions to take in the bifrost ui?

## Assistant

Yes. If you do this in Bifrost, there **would** likely be some admin actions in the Bifrost UI, but mostly for routing, limits, and rollout control—not for the actual compaction algorithm unless you build custom support for that into Bifrost itself.[1][2][3]

## UI actions you can use today

Bifrost already supports UI-managed routing rules, virtual keys, model/provider restrictions, fallbacks, and budgets/limits, so the UI can handle a meaningful part of the operational policy.[4][2][3][1]
That means you could likely manage things like “GLM route uses lower limits,” “fallback to another model,” or “only this VK may access Z.ai” from the UI without hardcoding everything.[3][1][4]

Concretely, admin actions in the UI could include:

- **Virtual Keys:** create a dedicated Claude Code VK for GLM traffic, isolate it from other routes, and attach specific provider/key restrictions.[1]
- **Routing Rules:** add a rule set that sends certain requests to GLM, others to fallback models, with priority ordering and enable/disable toggles.[2][3]
- **Budgets and limits:** set token or request limits that act as coarse guardrails before traffic gets too expensive or unstable.[4]

## What probably needs code

The part that is *not* clearly exposed as a built-in Bifrost UI feature is “inspect Anthropic-style message arrays, estimate prompt tokens conservatively for Z.ai GLM, then summarize/trim before forwarding.”[5][6][3]
That sounds like custom middleware or a Bifrost extension, because the documented UI features focus on routing/governance and not provider-specific prompt rewriting or synthetic compaction.[2][3][1]

So I’d separate this into two layers:

| Layer | Best home | Why |
|---|---|---|
| Route selection, fallback, VK isolation, coarse limits | Bifrost UI [1][4][2] | Already supported operational controls. |
| Preflight token estimation, GLM soft-limit logic, optional summarization/trim | Custom Bifrost code [5][6][3] | This is request-shaping behavior, not just governance. |

## Recommended design

For your use case, I would implement a **GLM-safe route** in Bifrost and expose only the high-level controls in the UI.[1][2]
The underlying code path would do Anthropic-request preflight for that route, while the UI would let you turn it on/off, tune thresholds, and choose fallback behavior.[3][1][2]

A practical shape:

- In the UI:
  - Create a VK such as `claude-code-glm-safe`.[1]
  - Attach routing rules for Z.ai GLM primary, fallback secondary.[2][3]
  - Set coarse token/request budgets for that VK.[4]
- In code:
  - Add a preflight middleware for Anthropic-compatible requests on that VK or route.
  - Estimate tokens from `system + messages + tools`.
  - If over soft limit, either reject with a clear local message or reroute.
  - Later, optionally add “compact old history into summary” as an opt-in mode.

That gives you admin visibility in the UI **without** trying to turn the UI into a prompt-rewriting engine.[3][1][2]

## My recommendation

Start with these admin actions in Bifrost UI:

1. Create a dedicated VK for Claude Code → GLM traffic.[1]
2. Add routing rules with explicit fallback order.[2][3]
3. Set budgets/limits conservatively for that VK.[4]
4. Add a custom middleware flag in config for `glmAnthropicSafeMode=true`, which the UI can later expose as a toggle.[6][5]

I would **not** start with full auto-compaction in the UI. That is more likely to cause hidden failure modes than to help initially.[7][8]
The first version should be: detect oversize early, fail clearly, optionally reroute; only after that works should you add summarization.[5][7]

Would you like me to sketch the actual Bifrost implementation shape next—request flow, middleware decision tree, and the exact UI/admin controls I’d add?
