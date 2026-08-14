---
title: "why doesn't openrouter/elephant-alpha work with PI harness?"
date: "2026-04-19"
mode: "COPILOT"
uuid: "0a75efcc-7bd3-4ba7-b2e8-f1c3172d4543"
entry_count: 1
---

## Human

why doesn't openrouter/elephant-alpha work with PI harness?

## Assistant

It currently doesn’t work because PI’s OpenRouter integration doesn’t yet support the way `openrouter/elephant-alpha` is exposed (and the workaround hasn’t been generalized into PI itself). FACT, medium‑high confidence.[1][2][3]

Here’s what’s going on, distilled:

1. **Elephant is a normal OpenRouter model, but PI doesn’t speak its “dialect” yet**  
   - Elephant is just another OpenRouter model with an OpenAI‑compatible API: you call it as `model: "openrouter/elephant-alpha"` through `https://openrouter.ai/api/v1/chat/completions`.[2]
   - PI’s OpenRouter support, today, assumes a simpler mapping and doesn’t fully support OpenRouter’s more advanced routing / `models` list semantics and presets. That’s tracked in `pi-mono` as: “Support `models` in OpenRouter API.”[3]
   - The maintainer explicitly notes that you currently need a **preset workaround** instead of using `models` directly.[3]

2. **OpenRouter’s “models” vs single “model” is the core mismatch**  
   - OpenRouter allows passing a **`models` array** and/or relying on presets and routing, and their docs/frameworks lean on that.[3]
   - PI’s current OpenRouter client is closer to a “pure OpenAI” mental model: it expects a single `model` id and doesn’t implement the `models` multi‑routing and related OpenRouter‑specific fields yet.[3]
   - Elephant is surfaced in the OpenRouter UI and used by other tools that honor the full OpenRouter API, but PI is in the “partial compatibility” bucket right now.[4][5]

3. **The practical workaround (from the PI issue) and why it’s clunky**  
   The maintainer describes a workaround for using OpenRouter models that require `models`/routing:  

   - In OpenRouter:  
     1. Create a **preset** (e.g. called `foobar`) in your OpenRouter dashboard.  
     2. Configure that preset to use the `openrouter/elephant-alpha` model (and any routing/settings you want).[3]
   - In PI:  
     1. Define a model with `id: "foobar"` and point PI at OpenRouter using your key.  
     2. PI sends `model: "foobar"`, OpenRouter resolves that into the configured preset and actually runs Elephant.[3]

   This works because PI only sends `model`, and OpenRouter treats the preset name as a model alias. PI never has to send `models`, so it avoids the unsupported part. FACT, high confidence.[3]

4. **Why “it doesn’t work” for you specifically**  
   Given that context, typical failure modes when you just drop `"openrouter/elephant-alpha"` into PI:

   - PI tries to send `model: "openrouter/elephant-alpha"` directly, but:  
     - Your PI version might not yet support OpenRouter’s custom headers / routing fields it expects for newer models; or  
     - Your OpenRouter account side is configured in a way that expects `models` or a preset rather than a raw `model` string.  
   - The maintainers themselves are tracking this as missing support and pointing people to presets as the official workaround for now.[3]

   So “doesn’t work with PI harness” is not Elephant being special; it’s that **PI’s OpenRouter integration hasn’t caught up to OpenRouter’s newer usage pattern, and Elephant happens to sit behind that.** CONSENSUS, medium‑high confidence.[2][3]

5. **Actionable next steps to get it working now**

   Minimal change path:

   1. **Create Elephant preset in OpenRouter**  
      - Go to your OpenRouter dashboard → Presets.  
      - Create a new preset, e.g. `elephant-pi`.  
      - Set **model** to `openrouter/elephant-alpha` and adjust sampling/temperature as you like.[2][3]

   2. **Use that preset name as the model in PI**  
      - In your PI config (YAML/JSON/CLI, depending how you run it), define a model like:  
        ```yaml
        models:
          - id: elephant
            provider: openrouter
            model: elephant-pi   # your preset name
        ```  
      - Or whatever the PI schema is in your setup, as long as PI sends `model: "elephant-pi"` to OpenRouter.  

   3. **Verify with a trivial chat request**  
      - Use a single‑turn prompt that prints the model name or a distinctive behavior; watch OpenRouter’s dashboard logs and confirm requests are hitting `openrouter/elephant-alpha` under preset `elephant-pi`.  

6. **What will fix this “properly”**  

   Based on the open issue, a proper fix would be: FACT (issue exists), SPECULATION (about future behavior), medium confidence.[3]

   - PI adds explicit support for OpenRouter’s `models` field and/or routing metadata.  
   - PI maps its “model list” configuration to `models` on the OpenRouter side when the provider is `openrouter`.  
   - Once that ships, you’ll be able to configure `openrouter/elephant-alpha` directly in PI with no preset hack, and your original config will “just work”.  

Assumptions / uncertainty:
- I’m inferring some PI behavior from the open GitHub issue rather than PI source code in front of me; the existence of the “Support `models` in OpenRouter API” issue and its described workaround is strong evidence that this is exactly the class of problem you’re hitting.[3]
- If you’re on a bleeding‑edge PI fork that has already merged a fix, you might instead be seeing a separate bug (auth, headers, or error handling), but that would be the exception, not the norm.

If you paste your current PI model config and the exact error body PI logs when you try Elephant, I can give you a concrete, line‑edited config that should work with the preset workaround.  
