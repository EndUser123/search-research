---
title: "In claude code on windows 11 I'm getting this error:
'
● Ran 10 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: Ho"
date: "2026-05-06"
mode: "COPILOT"
uuid: "01f1b502-acb8-4379-b50c-b280d99b3915"
entry_count: 4
---

## Human

In claude code on windows 11 I'm getting this error:
"
● Ran 10 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: Hook evaluator API error: There's an issue with the selected model (Haiku). It may not exist or you
  may not have access to it. Run /model to pick a different model.
"

    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/Stop_reasoning_quality_gate.py",
            "timeout": 30
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/StopHook_sequential_thinking.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/Stop.py --timeout 10.0",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/log_hook.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/StopHook_tdd_continuation.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/cjk_drift_detector.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "prompt",
            "model": "Haiku",
            "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n\nReturn JSON only: {\"ok\":bool,\"reason\":string,\"hookSpecificOutput\":{\"additionalContext\":string?}}\n\nSTEP 1 — Extract assistant answer.\nPriority: last_assistant_message > response > transcript[].content (role=assistant).\nIf none found: {\"ok\":true,\"reason\":\"No assistant response text in payload\"}\n\nSTEP 2 — Extract user request.\nPriority: user_prompt > transcript[].content (role=user). Default to empty string.\n\nSTEP 3 — Detect scope.\nIn scope ONLY if ALL are true:\n  A. Answer text word count > 50.\n  B. Answer text makes at least one substantive claim.\n  C. User request matches /why|what caused|diagnose|explain.*regression|root cause|compare.*hypothesis|trade-off|mechanism|alternative explanation|why.*happen/ (case-insensitive)\n     OR answer text matches /root cause|because|caused by|hypothesis|diagnosis|mechanism|alternative|likely cause|regression|due to/ (case-insensitive).\nIf any condition fails: {\"ok\":true,\"reason\":\"Not a diagnostic, causal, or explanatory answer\"}\n\nSTEP 4 — Judge adequacy:\n  A. Addresses the main subject of the user request (not a side tangent).\n  B. If situation is ambiguous: answer includes at least one alternative explanation OR hedge language (uncertain, might, could be, not confirmed, provisional).\n  C. If answer claims a causal mechanism, root cause, or regression: answer provides a specific test, observation, code path, config, or falsification condition OR hedge/provisional language.\n  D. If metrics, deltas, or performance changes are discussed: answer references a baseline value, prior measurement, or explicitly states no baseline is available.\n  E. Answer includes at least one specific source: function name, file path, config key, system behavior, or explicit uncertainty statement.\n\nIf ALL A-E pass: {\"ok\":true,\"reason\":\"Checks passed\"}\n\nSTEP 5 — Block with one directive if any check fails:\n{\"ok\":false,\"reason\":\"<directive>\",\"hookSpecificOutput\":{\"additionalContext\":\"<≤2 sentence reminder>\"}}\n\nDirectives:\n  B: \"Add one alternative explanation and name one observation that would distinguish it from your current explanation.\"\n  C: \"Trace the causal mechanism by pointing to the specific code path, config, or system behavior involved, or mark your conclusion as provisional.\"\n  D: \"Compare the reported metric against a prior measurement or explicit baseline, or acknowledge that no baseline data is available.\"\n  E: \"Add at least one specific source for your key claim: a function name, file path, config key, or system behavior, or explicitly state your uncertainty.\"\n  A: \"Confirm your answer addresses the main subject of the user's request.\"\n\nOUTPUT: Valid JSON only.",
            "timeout": 30
          }
        ]
      }
    ],

## Assistant

This error means one of your stop hooks is trying to call a Claude **model named just `Haiku`**, but your environment only exposes models like `claude-haiku-4-5` (or you currently have no Haiku deployment at all).[1][2]

The core pieces to line up:

- Your *interactive* model for coding is probably fine (Sonnet or similar).
- The **stop hook** with `"type": "prompt", "model": "Haiku"` is evaluated via the “hook evaluator” API, which expects a **valid model ID you have access to**.
- Because `"Haiku"` is not a valid model name for your account, that hook evaluation fails and surfaces as:  
  “Hook evaluator API error: There's an issue with the selected model (Haiku). It may not exist or you may not have access to it. Run /model to pick a different model.”[2][3][1]

Below is how I’d fix and harden this.

***

## 1. Confirm which Haiku models you actually have

1. In Claude Code, run the model picker:
   - Use `/model` in the chat box and see what Haiku variants appear (e.g. `claude-haiku-4-5`).[4][2]
2. If you are using Azure Foundry or another proxy:
   - Check what deployment names exist for Haiku in that environment.[2]
   - E.g. `claude-haiku-4-5` or a custom deployment name like `haiku-fast`.

If nothing Haiku-like appears, then any hook that specifies `"model": "Haiku"` (or similar) will necessarily fail until you add a deployment or change the hook to a different model.[2]

***

## 2. Fix the stop hook model name in `.claude.json`

You showed the Stop hooks block, and the last entry is:

```json
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "prompt",
      "model": "Haiku",
      "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n\nReturn JSON only: {\"ok\":bool,\"reason\":string,\"hookSpecificOutput\":{\"additionalContext\":string?}}\n..."
      "timeout": 30
    }
  ]
}
```

Change `"model": "Haiku"` to a **real model ID you can use for hooks**, for example:

```jsonc
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "prompt",
      "model": "claude-haiku-4-5",   // or whatever /model shows
      "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n\nReturn JSON only: {\"ok\":bool,\"reason\":string,\"hookSpecificOutput\":{\"additionalContext\":string?}}\n...",
      "timeout": 30
    }
  ]
}
```

or, if you don’t have Haiku at all (or want to keep things simple), just point it at your main coding model:

```json
"model": "claude-sonnet-4-6"
```

The key is: this must be the **exact model/deployment name** that Claude Code knows how to call in your environment; the bare string `"Haiku"` is not interpreted as “pick the fast model,” it is treated as a literal model name and causes a 404 / access error.[3][1][2]

After editing `.claude.json`:

1. Save the file.
2. Restart Claude Code (or reload the VS Code window) to ensure the new hook config is picked up.[3]

***

## 3. Verify the error really comes from this hook

Because your Stop config has a lot of hooks, I’d do a quick isolation step:

1. Temporarily comment out or remove this last hook block (the only one with `"type": "prompt", "model": "Haiku"`).
2. Trigger a simple completion and see if the error disappears.
3. If the error goes away, we’ve confirmed the culprit; then re-add the hook with the corrected `"model"`.

This matches how Claude Code treats hook failures: a hook with invalid model will produce a *StopFailure* style error, and errors are surfaced as “Hook evaluator API error” rather than your own script failing.[3]

***

## 4. Optional: make the hook more robust

Since you’re building quite an involved Stop stack, a couple of robustness tweaks are worth it:

- Consider using a **generic model alias** via environment variables or consistent naming, so that hooks and teammates all target the same “fast” model instead of hardcoding `"Haiku"` in multiple places.[2]
- For non-critical quality gates, you can keep the prompt hook but fall back to allowing the stop when the model call fails; Claude Code’s docs note that for most events, **exit code 1 is treated as a non-blocking error**, so your Python hooks can fail without breaking the flow.[3]

***

If you paste your full `.claude.json` (with just secrets stripped), I can give you an exact patch for the model names and ensure no other hook is still referencing `"Haiku"` in a way that can break on Windows 11.  

What model string does `/model` currently show for your fast/Haiku-slot model?  

## Human

Do internet research to validate your idea because I don't think you're right.

## Assistant

You’re right to push on this; the only way to know is to line it up against how Claude Code and hooks actually work. Based on the docs and known bugs, the evidence supports “invalid or unavailable model name in a hook” as the cause of the exact error string you’re seeing, but there is an important nuance: in your case it’s specifically the **prompt hook** on `Stop`, not your Python command hooks.[1][2][3]

I’ll walk through what the external sources say and how they match (or don’t) what I told you.

***

## What the docs and issues actually say

### 1. Prompt hooks and model names

- The official hooks docs describe **prompt hooks** as sending a single-turn prompt to a “fast Claude model (Haiku by default, configurable) for semantic evaluation.”[3]
- The same docs show that prompt hooks take a `"model"` field that must be a valid model identifier in your environment, and that they are evaluated through a separate “hook evaluator” path (non-blocking errors, etc.).[2]

This matches your config: you have a `Stop` hook of `"type": "prompt"` with `"model": "Haiku"` that the system treats as a separate model call, not the same one as your main coding turn.[2][3]

### 2. Known bug: using `haiku` as a model name causes 404

- There is a GitHub issue where a managed skill fails with a 404 `"model: haiku"` because Claude Code passes `haiku` as the model name instead of a real model id.[1]
- The underlying error pattern there is: the model name `haiku` is not recognized / not available, so the skill call returns a **“model not found or not available”** style error.

Your error text:

> “Hook evaluator API error: There's an issue with the selected model (Haiku). It may not exist or you may not have access to it. Run /model to pick a different model.”

is the same *class* of failure: the hook evaluator tried to call a model named `Haiku`, but the upstream API doesn’t recognize that as a valid model you can use.[1][2]

### 3. What happens when hook model is wrong

From the hooks reference:

- For the `StopFailure` event, “Output and exit code are ignored.” Non‑2xx responses and connection failures from prompt hooks “produce non‑blocking errors that allow execution to continue,” but the error text is surfaced back to Claude as a “Stop hook error: Hook evaluator API error …”.[2]
- That is exactly the shape of your message:  
  - “Ran 10 stop hooks (ctrl+o to expand)”  
  - “Stop hook error: Hook evaluator API error: There's an issue with the selected model (Haiku) …”  

So the failure is not in your Python scripts; it’s in the **prompt hook’s model call**.[2]

***

## Why I think the error is specifically `"model": "Haiku"`

Let’s test alternative explanations against the evidence.

### Hypothesis A: Network / Windows 11 / localhost issue

- Articles on Windows‑11‑specific Claude Code errors emphasize hangs, localhost failures, or generic “can’t reach local services,” not model‑specific messages.[4]
- They do not mention a message that explicitly names a model and suggests running `/model` to pick a different one. That guidance is tailored to model selection errors.[5][4]

This doesn’t fit your exact string.

### Hypothesis B: Foundry or Anthropic access problem

- Azure Foundry docs show errors like “The model `<model-name>` is not available on your foundry deployment” when you reference a model that hasn’t been deployed.[5]
- The remediation is: deploy the missing model or change the config to point at a deployed one.[5]
- The message pattern is again “model not available / no access,” which matches “…may not exist or you may not have access to it.”  

If you’re on Foundry, this supports the idea that `"Haiku"` in the hook doesn’t correspond to a deployed model (ex: you only have `claude-sonnet-4-6` and no Haiku deployment).[5]

### Hypothesis C: Misconfigured `.claude.json` / implicit Haiku model

- There is a separate bug where Claude Code “continues using Haiku 4.5” or has weird default model behavior when config is missing, but that manifests as the main coding model reverting, not as a hook evaluator API error naming the model.[6][7]
- Your error explicitly labels itself as a **Stop hook error** and not “default model reverted to Haiku”, which makes this less likely as the root cause.[7][6][2]

### Hypothesis D (my original claim): Prompt hook hardcodes `"Haiku"` which isn’t a valid model id

- We have:
  - Your config showing `"type": "prompt", "model": "Haiku"` in a Stop hook.  
  - A known issue where passing `haiku` as the model for a skill causes a 404, because that is not the correct model identifier.[1]
  - Docs and blog examples that describe prompt hooks sending prompts to a *fast* model (Haiku by default), but the examples avoid hardcoding `Haiku` and instead rely on whatever is configured as the fast model or simply omit the model field.[3][2]
- If your environment only knows about `claude-haiku-4-5` (or no Haiku at all), then a literal `"model": "Haiku"` will produce precisely a “model not found or not available” error from the hook evaluator.[8][1][5]

This is the one hypothesis that explains:

- The name “(Haiku)” in the error.
- The suggestion to “Run /model to pick a different model.”
- The fact that the error only appears in the stop-hook summary, not as a general failure of the main turn.

***

## What I would change, based on this research

Given the above, my **best‑supported recommendation** is:

1. **Change the prompt hook model** to a concrete model id that is known‑good in your environment. For example:

   - If `/model` shows `claude-haiku-4-5`, use that:

     ```jsonc
     {
       "matcher": ".*",
       "hooks": [
         {
           "type": "prompt",
           "model": "claude-haiku-4-5",
           "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n...",
           "timeout": 30
         }
       ]
     }
     ```

   - If you don’t have Haiku at all, point it at your main Sonnet model:

     ```jsonc
     "model": "claude-sonnet-4-6"
     ```

   The key is: it must match exactly a deployed model name or configured alias.[8][1][5]

2. Alternatively, **omit the `"model"` field** in that prompt hook so that Claude Code uses whatever its default fast model is, instead of the literal string `"Haiku"`.[3][2]

3. Restart or reload VS Code so the updated `.claude.json` is picked up.[2]

If after doing that the “Hook evaluator API error … (Haiku)” message disappears while all your Python command hooks keep working, that strongly confirms the diagnosis.

***

## Where I might still be wrong

FACT: There are confirmed bugs where Claude Code internally passes `haiku` as a model for skills and gets a 404.[1]
FACT: The hooks docs show prompt hooks use a model, and model-related failures become “Stop hook error: Hook evaluator API error …”.[2]
FACT: Your config includes a prompt hook with `model: "Haiku"` on the Stop event.  

CONSENSUS: Incorrect model identifiers (wrong name, not deployed, or no access) cause the exact class of message you’re seeing, including on Azure Foundry.[5][1][2]

SPECULATION (moderate confidence, say ~0.75): The specific string `"Haiku"` in your config is what the hook evaluator is trying—and failing—to use as a model id. If Claude Code had some hidden mapping from `"Haiku"` → `claude-haiku-4-5` in your environment, you wouldn’t see a “may not exist / you may not have access to it” error.

The main remaining possibility that would falsify this is: Claude Code ignores your `"model": "Haiku"` and is instead using an internal config that’s broken in some other way, and just happens to mention “Haiku” in the error. That would require a deeper bug in Claude Code itself than what the public issues describe so far, but I can’t rule it out completely without your full `.claude.json` and environment details.[6][7][1]

***

If you’re up for it, could you do one experiment: comment out only the prompt hook with `"model": "Haiku"`, leave the Python hooks as‑is, trigger one completion, and tell me whether the “Hook evaluator API error (Haiku)” banner still appears?  

## Human

Well, what is the correct model name as of today?

## Assistant

Short answer: for Anthropic’s public API as of May 2026, the **current Haiku model name you should use is `claude-haiku-4-5` (or `claude-haiku-4-5-20251001` if you need the fully versioned ID).**[1]

More detail:

## Official current Claude model IDs

From Anthropic’s own “Models overview” page (the primary source you want to trust here), the latest Claude 4‑series models and their API IDs are:[1]

| Tier    | Model name (human) | Claude API ID (full)           | Claude API alias         |
|---------|--------------------|---------------------------------|--------------------------|
| Opus    | Claude Opus 4.7    | `claude-opus-4-7`              | `claude-opus-4-7`        |
| Sonnet  | Claude Sonnet 4.6  | `claude-sonnet-4-6`            | `claude-sonnet-4-6`      |
| Haiku   | Claude Haiku 4.5   | `claude-haiku-4-5-20251001`    | `claude-haiku-4-5`       |

So if your hook is calling Anthropic directly (or a proxy that preserves Anthropic’s IDs), the **correct Haiku identifier is `claude-haiku-4-5`**, not `"Haiku"` or `"haiku"`.[1]

Some platforms use different IDs (e.g. Bedrock, Vertex, Foundry), but they still don’t accept a bare `"Haiku"` string:

- Claude API: `claude-haiku-4-5` (alias) or `claude-haiku-4-5-20251001` (full).[1]
- AWS Bedrock: `anthropic.claude-haiku-4-5-20251001-v1:0`.[1]
- Vertex AI: `claude-haiku-4-5@20251001`.[1]

None of these are simply `"Haiku"`.

## What this means for your hook

Given the above, to be “correct as of today” your stop prompt hook should look like:

```jsonc
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "prompt",
      "model": "claude-haiku-4-5",
      "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n...",
      "timeout": 30
    }
  ]
}
```

or, if your environment is wired to a different backend (Bedrock, Foundry, Vertex), the `model` value needs to match **that** deployment’s identifier, not `"Haiku"`.[2][1]

Assumption I’m making (and where I’d still verify locally): that your Claude Code install is using Anthropic’s canonical IDs (or aliases) rather than some private aliasing layer. If your `/model` command shows a different string (e.g. `my-haiku-fast`), then **that** is what you must put into `"model"`; but it still won’t be the literal `"Haiku"`, which is not a valid ID in any of the official docs.[2][1]

To target this precisely: what exact Haiku‑ish string do you see in `/model` in Claude Code right now (copy‑paste the line that corresponds to the fast / Haiku tier)?  

## Human

This is what we have for models: "  Select model
  Switch between Claude models. Applies to this session and future Claude Code sessions. For other/previous model names, specify
  with --model.

    1. Default (recommended)  Use the default model (currently GLM-5.1[1m]) · $5/$25 per Mtok
    2. GLM-5.1                Custom Opus model
  ❯ 3. M27 ✔                  Custom Sonnet model
    4. M27                    Custom Haiku model"

## Assistant

Given that `/model` shows custom entries like `GLM-5.1`, `M27` (Sonnet), and `M27` (Haiku), the **correct model name for your prompt hook is exactly the same string you see in that list for the Haiku slot: `M27`.**[1][2][3]

So in *your* setup, the hook should be:

```jsonc
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "prompt",
      "model": "M27",  // your “Custom Haiku model”
      "prompt": "You are a diagnostic-analysis critic for Claude Code's Stop hook.\n$ARGUMENTS\n...",
      "timeout": 30
    }
  ]
}
```

not `"Haiku"`.

***

## Why this is the right ID in your environment

- You’ve wired Claude Code to a **custom provider / proxy** that exposes:
  - `Default (recommended)` → `GLM-5.1`  
  - `GLM-5.1` → “Custom Opus model”  
  - `M27` (checked) → “Custom Sonnet model”  
  - `M27` (second entry) → “Custom Haiku model”[2][1]
- In this configuration, Claude Code is not using Anthropic’s canonical IDs like `claude-haiku-4-5`; instead, it’s using whatever IDs your provider defines (`GLM-5.1`, `M27`, etc.).[1][2]
- The hooks docs say the `model` field for prompt hooks must be **a valid model name for your current provider**, i.e., one of the IDs that provider accepts.[3][4]

So for your Haiku-tier model, the valid model id is the one labelled “Custom Haiku model,” which in your `/model` menu is `M27`. Using `"Haiku"` there will cause the hook evaluator to call a model your provider does not recognize, hence the error: “It may not exist or you may not have access to it. Run /model to pick a different model.”[4][1]

***

## Concrete next step

1. Edit your `.claude.json` stop-hook block:
   - Replace `"model": "Haiku"` with `"model": "M27"` (the Haiku entry from `/model`), or with `"model": "GLM-5.1"` if you actually want the Opus-equivalent model there.
2. Reload Claude Code or restart the window.
3. Trigger a completion and see if the “Hook evaluator API error (Haiku)” disappears; if it does, that confirms the diagnosis.

If you want, paste the full output of `/model` including any provider names (e.g., “Z.AI”, “OpenAI compatible”) and I can tell you whether it might be cleaner to point the hook at `GLM-5.1` instead of `M27`.  
