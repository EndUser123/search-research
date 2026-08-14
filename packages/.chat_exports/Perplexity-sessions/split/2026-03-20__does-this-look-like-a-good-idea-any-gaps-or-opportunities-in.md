---
title: "Does this look like a good idea?  Any gaps or opportunities?
'In claude code, I'm using the anthropic subscription. But "
date: "2026-03-20"
mode: "COPILOT"
uuid: "baed0214-cd9e-47e6-a25a-bc82742792c3"
entry_count: 7
---

## Human

Does this look like a good idea?  Any gaps or opportunities?
"In claude code, I'm using the anthropic subscription. But I have other provider subscriptions available. How can I use my other subscripts with claude code subagents, and leave the main cli orchestrator using the anthropic models?"

## Assistant

Conceptually it’s a good idea, but there are some policy, plumbing, and UX wrinkles to think through. There are also some big opportunities if you treat “other providers” as tools/subagents rather than as peers of the main orchestrator.[1][2][3][4]

## What you’re proposing

You’re essentially saying:

- Keep **Claude Code CLI + Anthropic subscription** as the primary “orchestrator” and editor/terminal brain.
- Have **subagents** that can:
  - Call other LLM providers (OpenAI, DeepSeek, OpenRouter, Bedrock, etc.).
  - Possibly do specialized tasks (linting, static analysis, RAG) using those providers.
- Use those subagents *from within* Claude Code, without moving the whole workflow off Anthropic.

That’s architecturally sound and nicely aligned with how Anthropic frames tools and agents.[4][5]

## Gaps & constraints to watch

1. **Policy & subscription boundaries**

   - Anthropic’s Pro/Max/Code subscriptions are explicitly scoped to Anthropic’s own tools (Claude web, apps, Code) and not to arbitrarily resold/proxied access.[6][3][7]
   - Using Claude Code as the orchestrator while *your own* subagents call other providers via their official APIs is aligned with how tooling is meant to work: Anthropic is only subsidizing Anthropic usage; you pay others separately.[1][6]
   - What they are hostile to is: “Use Claude Code subscription as a generic front-end for non‑Anthropic APIs in a way that effectively bypasses Anthropic API pricing” (e.g., wire-level emulation or resale).[7][6]

   **Implication:**  
   - Treat “other providers” as *downstream tools you pay for separately*, not as something tunneled through the Claude Code subscription itself.  
   - Avoid any “proxy that pretends to be Anthropic” for non‑Anthropic models using your subscription traffic; this is exactly what’s being cracked down on.[8][6][7]

2. **How Claude Code actually talks to models**

   There are two main patterns floating around:

   - Shell-level **env-variable switching** to point Claude Code at alternate Anthropic-compatible endpoints (DeepSeek, Z.ai, Kimi, etc.), using `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, etc.[9][10]
   - Separate **proxy processes** that translate Anthropic-style requests into other providers’ APIs.[9][8]

   **Gap vs your goal:**  
   - Those patterns tend to “swap” the *primary* provider for the whole CLI session, not “keep Anthropic for orchestrator, but use others only for subagents”.[10][9]
   - To get *just* subagents using other providers, you want those providers exposed as **tools** / MCP servers, not as alternate Anthropic endpoints.

3. **Granularity of control at subagent level**

   - Out of the box, Claude Code subagents are configuration + system prompt + preferences; they all still talk to the same underlying Anthropic model unless you mess with global config/env.[11][2][12]
   - There isn’t yet a first-class knob like “this subagent uses OpenAI; that one uses DeepSeek” within Anthropic’s official CLI configuration.[3][1]

   **Implication:**  
   - Per‑subagent multi‑provider routing is something you have to build yourself via MCP/tooling (e.g., each agent calls a different MCP which in turn calls a different LLM provider).

## A clean architecture that *does* work

Given all that, the least-fragile, policy-aligned design is:

### 1. Keep Claude Code orchestrator on Anthropic

- Configure Claude Code normally to use your Anthropic subscription; let it be the **only direct caller** of Anthropic’s chat/completion APIs in this stack.[3]
- Don’t override `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` to non-Anthropic providers in your “main” workflow; reserve that trick only for dedicated sessions where you knowingly aren’t using the Anthropic subscription at all.[10][9]

### 2. Expose other providers as MCP servers or tools

For each provider you want to use:

- Run a small **MCP server** (or HTTP tool) that:
  - Receives structured tool calls from Claude (via Claude Code).
  - Calls the provider’s official API (OpenAI, DeepSeek, Bedrock, etc.).
  - Returns results in a compact schema (text, JSON, diff, metrics).

- Example tool capabilities per provider:
  - `deepseek.review_code({ context, diff }) -> { diagnostics, suggestions }`
  - `openai.generate_tests({ function_signature, examples }) -> { tests }`
  - `bedrock.architect_rewrite({ service, pattern }) -> { proposed_design }`

This aligns perfectly with Anthropic’s “client tools” model: **Claude does reasoning and orchestration; tools do work**.[5][4]

### 3. Bind subagents to specific tools/providers

- Define subagent configs that are “biased” toward specific tools:
  - A “DeepSeek code-reviewer” subagent that defaults to calling your DeepSeek MCP for reviews.
  - A “GPT test-writer” that primarily calls an OpenAI-backed MCP.
- You don’t need to lie about the model; you just route specialized tasks through tools that hit the right provider.

Result:

- Main orchestrator: Anthropic, benefiting from your subscription.  
- Specialized heavy-lift tasks: offloaded to whatever provider has the best economics/quality for that task, paid via those providers’ APIs.

## Concrete opportunities

1. **Cost optimization by task**

   - Let Anthropic handle high‑value reasoning, planning, and editing inside Claude Code (where the UX shines).[1][3]
   - Route:
     - Bulk test generation, doc summarization, or exploratory brainstorming to cheaper or “unlimited” subs elsewhere.
     - Domain-specific models (e.g., code-optimized, multilingual) for narrow tasks.

2. **Evaluation and A/B patterns**

   - Build agents that:
     - Call multiple provider-tools for the same task.
     - Compare outputs (e.g., via another Anthropic call as judge) and pick or ensemble the best answer.[5]
   - This gives you a practical multi‑model evaluation harness *inside* your daily Claude Code workflow.

3. **Provider-specific strengths as subagents**

   - Example subagents:
     - “DeepSeek reasoner” for multi-step algorithmic puzzles.
     - “GPT-style refiner” for natural-language polish or longform doc rewriting.
     - “Local Llama security checker” for offline code scanning.

4. **Failover & resilience**

   - If Anthropic rate limits or has an outage, critical tooling can still call other providers directly through MCP servers, even if the orchestrator is somewhat degraded.

## Where you may want to refine your prompt/intent

Your original text:

> “How can I use my other subscripts with claude code subagents, and leave the main cli orchestrator using the anthropic models?”

Minor improvements:

- Clarify **boundary** and **direction of calls**:

  > “I want Claude Code itself to keep using my Anthropic subscription, but I want some subagents/tools that can call other providers’ APIs (OpenAI, DeepSeek, etc.) using those providers’ own subscriptions. How should I architect that so it’s robust and policy-aligned?”

- Optional: explicitly mention MCP/tool-based approach:

  > “…I’m thinking of exposing each non-Anthropic provider as an MCP server or tool so Claude can delegate to them. Is that the recommended approach?”

## Summary of gaps vs opportunities

- **Gaps / risks:**
  - Don’t rely on hacks that make non-Anthropic models masquerade as Anthropic endpoints over your subscription.[6][8][7]
  - Subagent-level per-provider selection is not first-class; you need to model it via tools/MCP.[2][1]

- **Opportunities:**
  - Very clean division: Anthropic = orchestrator; others = specialized tools.
  - Strong cost and quality leverage by matching each task to its best provider.
  - Built-in A/B testing and evaluation patterns using Claude’s reasoning plus external tools.[2][5]

If you want, next step can be a concrete layout: one `mcp.json` / tool schema + one TypeScript/Python MCP server example per provider, wired to a specific subagent role.

## Human

Your use-anthropic only solution will cost me a lot of money.

## Assistant

You’re right to push on that; using Anthropic for *everything* in your stack will be unnecessarily expensive for your usage pattern. A better design is “Anthropic for orchestration and high‑value thinking, cheaper models for bulk work,” and that’s still compatible with Anthropic’s rules if you structure it carefully.[1][2][3][4][5]

## Facts and constraints

- Claude Pro/Max and Claude Code are priced assuming *you are mostly using Anthropic models*; they are not optimized for acting as a universal router to all other LLMs.[3][5][1]
- Anthropic explicitly forbids third‑party harnesses that tunnel requests through your *subscription* instead of using the API at normal prices.[6][4][7]
- None of that forbids you from using Claude Code as a brain and having it call **external tools/MCP servers that you pay for separately** (OpenAI, DeepSeek, etc.). That is actually the intended “tool” usage pattern.[2][4]

So: yes, using Anthropic “only” is costly; the right move is to **minimize** Anthropic‑token burn while still leveraging Claude Code’s UX and reasoning.

## Concrete cost‑sensitive architecture

To reduce cost while keeping Claude Code central, skew the work like this:

1. **Use Anthropic *only* for:**

   - High‑level planning, orchestration, and “write the next N edits” inside Claude Code.[2]
   - Non‑delegable reasoning like: architecture decisions, critique/compare multiple candidate solutions, judging competing outputs.[8]

2. **Push bulk work to cheaper providers via tools/MCP:**

   - Implement MCP servers or HTTP tools that call:
     - A low‑cost model (e.g., DeepSeek, OpenRouter tier, smaller open‑weights) for:
       - Test generation.
       - Comment/docstring generation.
       - Large‑batch refactors and “rewrite this file according to rules”.
     - You only pay those providers at their (often much lower) per‑token cost.  

   - From Anthropic’s perspective, these are just tools; subscription tokens are only used for the *decision* to call them and for integrating results, not for the whole heavy generation.[4][2]

3. **Exploit plan‑then‑act to cut tokens**

   - Force Claude Code to:
     - Plan in compressed form (short plans, bullets) before generating code or calling tools.[2]
     - Use shorter thinking windows and smaller file subsets instead of whole‑repo sweeps to avoid burning Sonnet/Opus on unnecessary context.[5][2]

4. **Select a cheaper Anthropic tier / limited window**

   - If you architect the above well, you may get away with:
     - Pro instead of Max, or Max 5x instead of Max 20x, because Anthropic isn’t handling all bulk IO.[1][3]
   - That drops your fixed cost from \$100–200/month to \$20–100 while offloading “spammy” work to cheaper subs.

## What to *avoid* (cost + ban risk)

- Don’t run a “universal router” that pretends to be Claude Code and pipes **other people’s** usage through your Claude subscription.[7][6][4]
- Don’t spoof Anthropic endpoints with a proxy that sends requests to non‑Anthropic models but is still funded by your subscription usage; that is exactly the harness pattern Anthropic is policing.[6][7]

## High‑leverage opportunities

- **Per‑task routing:** Explicitly tag tasks in prompts (“this is large‑batch doc rewrite, prefer cheap_tool_x”) and let your MCP server choose the cheapest adequate model for that class of work.  
- **Multi‑LLM consensus selectively:** Only on high‑stakes decisions, use one Anthropic call as a *judge* over cheaper‑model outputs instead of having Anthropic generate all alternatives itself.[8]
- **Usage analytics:** Log token estimates per tool and per provider; if Anthropic consumption climbs, move more patterns into the “cheap” bucket.

If you share your current subs (e.g., OpenAI tier, DeepSeek, any OpenRouter plan), the next step is to sketch a concrete routing table: which tasks run on which provider, with what approximate per‑month cost envelopes.

## Human

Why won't you ask my question about gaps and opportunities and other solutions?

## Assistant

There are real gaps and bigger opportunities than “Anthropic-only,” and there *are* other solutions; earlier answers just didn’t spell them out crisply enough.

## Gaps in your current idea

Your core idea is good: Anthropic for orchestration, other providers for bulk/specialized work. The main **gaps**:

- **Per-subagent model choice isn’t first-class.** Subagents in Claude Code don’t natively say “this one uses OpenAI, that one uses DeepSeek”; they all share the same underlying model config unless you hack global env or a proxy.[1][2][3]
- **Cost asymmetry.** If subagents stay pure-Anthropic, you pay Anthropic prices for work a cheaper model could do adequately (tests, boilerplate, comments, bulk rewrites).[4][5][6]
- **Policy landmines.** Any approach that *tunnels* other people’s traffic through your Claude Code subscription or spoofs Anthropic endpoints with other models is squarely in the “third‑party harness” category Anthropic is actively shutting down.[7][8][9]

So: your goal is correct, but the naive implementation (“configure some subagents to use non‑Anthropic models directly through the subscription”) is either impossible or risky.

## Opportunities inside your overall goal

There are strong **opportunities** if you shift the design slightly:

- **Tool/MCP-based multi-provider routing.**  
  - Treat each non‑Anthropic provider as a **tool** (MCP server or HTTP tool) instead of a “model for a subagent.”[10][11]
  - Subagents become *policies over tools* (“I’m the test-writer; I mostly call the GPT4o-tool,” “I’m the refactor agent; I mostly call the DeepSeek-tool”).

- **Task-based cost tiers.**  
  - Route:
    - High-stakes reasoning, architecture, coordination → Anthropic (via Claude Code).[12][13]
    - High-volume, low-risk generation → cheaper or already-paid providers.  

- **Evaluation workflows.**  
  - Have a “judge” subagent (Anthropic) that:
    - Calls two cheap providers via tools.
    - Compares outputs and selects/merges them.  
  - Anthropic burns relatively few tokens; most generation happens on cheaper models.[14][12]

- **Failover & experimentation.**  
  - You can A/B providers inside your existing Claude Code flow without changing your main orchestrator config—just swap which tool a subagent is instructed to favor.

## Other concrete solution patterns

Here are **alternative architectures** beyond “Anthropic only” and “Anthropic + tools”:

### 1) External orchestrator, Claude Code as a *client*

- Run your own Node/Python orchestrator that:
  - Talks to multiple providers directly (OpenAI, DeepSeek, Anthropic API, etc.).
  - Exposes a minimal “workspace agent” as an MCP server to Claude Code.  
- Claude Code becomes one **frontend** into your orchestrator; you might also have a web UI, CLI, etc.  
- Pros:
  - True per-task/per-agent routing under your control.
  - Easier to add non-LLM logic (scheduling, budgeting, telemetry).  
- Cons:
  - More infra to maintain.
  - You pay Anthropic API rates for that orchestrator, not just the Code subscription.

### 2) Dual-mode: “Anthropic-centric” and “cheap-centric” sessions

- Run **two Claude Code configurations**:
  - One wired to Anthropic subscription (for heavy thinking, architecture, critical refactors).
  - One wired to a cheaper Anthropic-compatible provider or proxy (e.g., DeepSeek/Z.ai via `ANTHROPIC_BASE_URL`) that you use for grindy work sessions.[15][16]
- You, the human, choose which shell/session to use based on task cost/importance.  
- Cons:
  - Manual context switching.
  - Risk of misconfig if you’re not careful with env separation.

### 3) Thin “translator” agents

- Keep Claude Code purely Anthropic.  
- Add subagents that:
  - Call a tool that hits another provider.
  - Then *rephrase/condense* the result back into a form Anthropic can work with cheaply (summaries, diffs).  
- This minimizes the amount of Anthropic context you need per tool invocation.

## Direct answer to your “why” question

You asked:

> “Does this look like a good idea? Any gaps or opportunities?”

What should have been answered more directly is:

- **Yes, the idea is good at the conceptual level** (Anthropic for orchestrator; others for heavy lifting).  
- **Gaps:**  
  - No native per-subagent non-Anthropic model switch.  
  - Cost blow-up if you don’t offload bulk work.  
  - Policy risk if you try to fake Anthropic endpoints.  
- **Opportunities:**  
  - Make other providers into tools/MCP servers.  
  - Do task-based routing and A/B tests.  
  - Optionally move orchestration into your own service and let Claude Code be one “front end” into that fabric.

If you want, next step can be: pick 2 providers you actually pay for and sketch a precise routing plan (which tasks, expected token/$$ split, plus where to put the MCP boundaries).

## Human

You seriously didn't read what I sent you.

## Assistant

You’re right that the last answer drifted away from what you *actually wrote* in the quoted prompt.

Your original text was:

> "In claude code, I'm using the anthropic subscription. But I have other provider subscriptions available. How can I use my other subscripts with claude code subagents, and leave the main cli orchestrator using the anthropic models?"

Two key things *I failed to respond to directly*:

1. **You want subagents to use other paid providers, not Anthropic.**  
   I kept gravitating back to “keep Anthropic for everything but be careful,” instead of focusing on *maximally offloading* real work (and cost) to your other subscriptions.

2. **You explicitly asked for “gaps or opportunities” in that idea.**  
   I gave a lot of architecture talk, but not a tight “here’s what’s missing from your plan” and “here’s how to push it further in your favor.”

Let’s fix that in the most direct way possible.

## Direct critique of your idea

Your idea (restated precisely):

- **Goal:**  
  - Main Claude Code CLI uses Anthropic models (because that’s what the product gives you).  
  - **Subagents** leverage your *non-Anthropic* subscriptions (OpenAI, DeepSeek, etc.) so those providers do as much work as possible.

**Gaps in that idea:**

- Claude Code **does not currently expose per-subagent model/provider selection** as a first-class config knob; all subagents ride on the same underlying Claude backend in a given session.  
- If you try to “point” some subagents at other providers by changing Anthropic endpoints, you end up changing it for the *whole* CLI, which violates your requirement (“leave the main CLI orchestrator using Anthropic models”).  
- There’s no safe way (within official behavior) to make a subagent *directly* use another LLM provider as its base model *inside the Anthropic subscription*; you must instead reach other providers via tools/MCP.

**Opportunities in that idea (when reframed correctly):**

- Use Anthropic only for:
  - Managing the workspace and context.
  - Deciding *when* to call which provider.
- Implement subagents as:
  - Different **tool-using policies**, where each policy primarily calls one of your other paid providers through an MCP server or HTTP tool.
  - Example: “TestAgent” that always goes through an OpenAI MCP; “BulkRefactorAgent” that goes through DeepSeek.

This keeps the “main orchestrator uses Anthropic” while *actual heavy lifting* runs on other subscriptions.

## Other solutions that really address your constraints

Given your cost concern and provider mix, here are concrete alternatives that stay true to what you wrote:

1. **Anthropic as minimal orchestrator + MCP-based multi-provider backend**

   - Claude Code:
     - Stays on Anthropic.
     - Mostly plans and orchestrates; avoids giant, expensive generations.
   - Subagents:
     - Are just prompts that favor specific tools:
       - `openai_tool.*` for tests, docs, boring boilerplate.
       - `deepseek_tool.*` for deep reasoning or large refactors.
   - Net effect: the majority of *tokens* are burned on non-Anthropic providers, but you still get Claude Code UX.

2. **External orchestrator with Claude Code as a client (when your API costs beat the subscription)**

   - If your direct Anthropic API pricing + other providers is cheaper than a high-tier Code/Max plan for your real workload, you:
     - Run a custom orchestrator (Node/Python).
     - Expose that orchestrator as an MCP server *into* Claude Code.
   - Then:
     - Claude Code is still your edit/terminal UX.
     - The “main brain” is actually your own agent layer that routes across Anthropic API + other providers, strictly according to cost/quality.

3. **Two Claude Code configs: low-cost default, Anthropic-on-demand**

   - Have:
     - A “cheap-mode” Claude Code instance pointing at a low-cost compatible backend (or proxy) that you use for grind work.
     - A “premium-mode” one using Anthropic subscription for critical flows.
   - You call Anthropic only when it truly buys you something.

***

If you want to go practical next: list the actual providers + plans you have (e.g., “OpenAI: 4o + 4o mini, DeepSeek: R1, local models via Ollama”), and the real high-volume tasks you run. Then it’s possible to design a precise routing table and where subagents/tools should sit to offload as much cost as possible.

## Human

Maybe I didn't paste everything:
"# Using Other Providers with Claude Code Subagents - Grok

Share[/](/)

In claude code, I'm using the anthropic subscription. But I have other provider subscriptions available. How can I use my other subscripts with claude code subagents, and leave the main cli orchestrator using the anthropic models?

Thought for 1m 5s

**Claude Code (from Anthropic) is built exclusively around Claude models**, so the main CLI orchestrator and subagents both use your Anthropic subscription/API by default. You **can** already use different Claude models (Opus/Sonnet/Haiku) between the main orchestrator and subagents without any extra tools—this is the cleanest native way to optimize cost/performance while keeping everything on Anthropic.

### Native Option: Different Claude Models for Subagents (Recommended if You Only Need Claude Variants)

1.  Keep your main orchestrator on your preferred model (e.g. Opus for complex reasoning):
    -   Launch with claude --model opus
    -   Or set permanently: export ANTHROPIC\\_MODEL=opus (or in your settings JSON).
2.  Force all subagents to a cheaper/faster model (e.g. Sonnet or Haiku):
    -   export CLAUDE\\_CODE\\_SUBAGENT\\_MODEL=claude-sonnet-4-6 (or whatever full model ID you want).
    -   This applies globally to every subagent (built-in or custom) and overrides the main model.
3.  For per-subagent control (even finer-grained):
    -   When creating custom subagents (via /agents command or in ~/.claude/agents/ or .claude/agents/ Markdown files), add a model field in the YAML frontmatter:
        
        YAML
        
        Copy
        
        ```
        ---
        name: code-reviewer
        description: Reviews code for quality and security
        model: sonnet   # or haiku, opus, or full ID like claude-opus-4-6
        ---
        You are an expert code reviewer...
        ```
        
    -   Or pass it via CLI: claude --agents '{"code-reviewer": {"model": "haiku"}}'

This keeps the entire session (main + subagents) on your Anthropic subscription—no extra setup needed. Subagents inherit tools/context from the main session but run on their own model.

### Using Other Providers (OpenAI, Grok/xAI, Gemini, DeepSeek, OpenRouter, etc.) for Subagents Only

Claude Code has **no native multi-provider support** for mixing providers inside one session (main stays Anthropic, subagents use others). All official model config (aliases, ANTHROPIC\\_\\* env vars, Bedrock/Vertex/Foundry overrides, etc.) still points to Claude models only.

**The working solution is a local proxy that intercepts requests**:

-   It forwards the **main orchestrator** calls to your real Anthropic API (using your subscription).
-   It reroutes **specific subagents** (by name) to whichever other provider/model you want.

The best tool for exactly your use case is **claude-code-proxy**[github.com](https://github.com/seifghazi/claude-code-proxy). It was built for this:

#### Quick Setup Steps

1.  Clone and install the proxy (Python-based, very lightweight).
2.  Create a config.yaml (example from the repo):
    
    YAML
    
    Copy
    
    ```
    anthropic_api_key: "sk-ant-..."   # Your real Anthropic key for the main orchestrator
    base_url: "http://localhost:8000" # Proxy endpoint
    
    subagents:
      enable: true
      mappings:
        code-reviewer:          # Your custom subagent name
          provider: openai
          model: gpt-4o
          api_key: "sk-..."
        web-researcher:
          provider: grok     # or xai, gemini, deepseek, openrouter, etc.
          model: grok-beta
          api_key: "your-grok-key"
    ```
    
3.  Run the proxy: python main.py (or however the repo instructs—it starts a local server).
4.  Tell Claude Code to use the proxy instead of direct Anthropic:
    
    Bash
    
    Copy
    
    ```
    export ANTHROPIC_BASE_URL="http://localhost:8000"
    # (or ANTHROPIC_API_BASE depending on version)
    ```
    
5.  Start your normal Claude Code session: claude (main orchestrator still uses your Anthropic subscription).

Now when the main agent spawns a subagent whose name matches a mapping (e.g. you created a “code-reviewer” subagent), the proxy automatically switches providers for that subagent’s calls only. Everything else (main orchestrator, non-matching subagents) stays on Anthropic.

Other popular proxies that can do similar routing (with slightly different config):

-   starbaser/ccproxy (uses LiteLLM under the hood for even more providers).
-   Bifrost or y-router setups (good if you prefer OpenRouter-style prefixes).

These all let you keep your Anthropic subscription strictly for the main CLI orchestrator while offloading subagents to your other paid subscriptions.

### Tips

-   Name your custom subagents meaningfully (e.g. “fast-researcher”, “gpt-auditor”) so the proxy can match them easily.
-   Test with a simple subagent first using the /agents command in Claude Code.
-   If you only need occasional other-model calls, some people also build custom MCP skills or slash commands that call external APIs directly, but the proxy route is cleaner and fully transparent to Claude Code.

Start with the native different-Claude-models approach if it meets your needs—it’s zero-config and fully supported. For true multi-provider subagents, the proxy method above works reliably today. Check the specific proxy README for the latest config examples, as these community tools evolve quickly.

![Web page favicon](https://www.google.com/s2/favicons?domain=code.claude.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=youtube.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=github.com&sz=256)

62 sources

Do we need to use a proxy? Can we set an anthropic url and model per subagent or agent team member?

Thought for 29s

**No, you cannot natively set a different Anthropic base URL (or any custom endpoint/provider) per subagent or per agent team member.**

Claude Code (and the underlying Agent SDK) is built exclusively on the Anthropic API. Subagents and agent teams are spawned as child instances within the **same session**, so they inherit the main orchestrator’s API configuration (including ANTHROPIC\\_BASE\\_URL, ANTHROPIC\\_API\\_KEY, Bedrock/Vertex overrides, etc.). There is no per-subagent or per-teammate field for base\\_url, endpoint, provider, or api\\_key.

### What _is_ supported natively (and it's very useful)

You **can** set a different **Claude model** per subagent (or teammate) with zero extra setup:

-   In the subagent’s Markdown file (.claude/agents/your-agent.md or via /agents command):
    
    YAML
    
    Copy
    
    ```
    ---
    name: fast-researcher
    description: Quick web/search tasks
    model: haiku          # or sonnet, opus, claude-opus-4-6, claude-sonnet-4-6, etc.
    # or "inherit" to use whatever the main orchestrator is using
    ---
    You are a lightning-fast researcher...
    ```
    
-   Or in the /agents UI when creating/editing: there’s an explicit “Choose model” dropdown (Sonnet/Opus/Haiku + full IDs).
-   Agent teams work the same way — you can specify different Claude models per teammate in the team config.

This is the official, fully supported way to mix models (e.g., main orchestrator on Opus, most subagents on Sonnet, cheap background ones on Haiku). It all stays on your Anthropic subscription.

### When you _do_ need a proxy (or LLM gateway)

If you want to route **specific subagents** to a completely different provider (OpenAI, Grok/xAI, Gemini, DeepSeek, Azure, etc.) while keeping the main CLI on Anthropic, then yes — a proxy is currently the only reliable method.

-   The global ANTHROPIC\\_BASE\\_URL (or LLM gateway setup) applies to the entire session, including all subagents.
-   There is no per-agent override in the YAML, settings.json, env vars, or Agent SDK.
-   Community proxies (claude-code-proxy, starbaser/ccproxy, LiteLLM-based routers, etc.) are specifically designed for exactly this: they inspect the subagent name and reroute only matching subagents to your other provider while forwarding the main orchestrator (and unmatched subagents) straight to Anthropic.

This is the same situation as when I described it before — nothing has changed in the official configuration options. Anthropic has not added per-subagent endpoint routing (as of the latest docs and community discussions).

### Quick recommendation

-   If you only need different **Claude** models → use the native model: field. No proxy required.
-   If you want non-Anthropic models for certain subagents → proxy (or run a full LiteLLM/OpenRouter gateway) is still the way.

Would you like me to give you the exact current config example for the most popular proxy setup (with the latest repo links and a minimal config.yaml that routes only named subagents)? Or do you want to stick purely to native Claude model mixing?

![Web page favicon](https://www.google.com/s2/favicons?domain=code.claude.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=youtube.com&sz=256)

45 sources

"exact current config example for the most popular proxy setup (with the latest repo links and a minimal config.yaml that routes only named subagents" yes please

Thought for 35s

**Yes — here is the current (as of March 2026) most popular and actively maintained proxy that does exactly what you want: routes _only_ named subagents to other providers while the main CLI orchestrator stays 100% on your real Anthropic subscription.**

**Repo (most popular for selective subagent routing):** [https://github.com/seifghazi/claude-code-proxy](https://github.com/seifghazi/claude-code-proxy) (411 stars, last commit ~2 months ago — still actively maintained)

This is the one repeatedly recommended on Reddit and in Claude Code communities specifically for “main on Anthropic, only certain subagents on GPT-4o / o3 / etc.”

### Minimal config.yaml (routes ONLY the subagents you name)

Copy this as your config.yaml (or start from the repo’s config.yaml.example and add the subagents section):

YAML

Copy

```
server:
  port: 3001

providers:
  anthropic:
    base_url: "https://api.anthropic.com"   # ← your real Anthropic subscription stays here
  openai:                                   # ← add your other providers here
    api_key: "sk-..."                       # or set OPENAI_API_KEY env var

storage:
  db_path: "requests.db"                    # optional, for the built-in dashboard

subagents:
  enable: true
  mappings:
    code-reviewer: "gpt-4o"                 # ← only this subagent goes to OpenAI
    fast-researcher: "o3-mini"              # ← another example
    cheap-background: "gpt-4o-mini"
    # grok-beta or gemini models work if you add the provider block (see repo for extensions)
```

**How it works**

-   The proxy sits between Claude Code and Anthropic.
-   Main orchestrator + any subagent _not_ listed in mappings → goes straight to your real Anthropic key (no extra cost).
-   Only the exact subagent names you map get rerouted to the other provider.
-   You name your subagents in their Markdown files (the name: in the YAML frontmatter) or via the /agents command — the proxy matches that name.

### Quick setup (2 minutes)

1.  Clone & install
    
    Bash
    
    Copy
    
    ```
    git clone [https://github.com/seifghazi/claude-code-proxy.git](https://github.com/seifghazi/claude-code-proxy.git)
    cd claude-code-proxy
    cp config.yaml.example config.yaml
    # paste the minimal config above
    ```
    
2.  Run it
    -   Local: make dev (or ./run.sh)
    -   Or Docker (recommended): docker-compose up (repo has a ready docker-compose.yml)
3.  Point Claude Code at the proxy
    
    Bash
    
    Copy
    
    ```
    export ANTHROPIC_BASE_URL="http://localhost:3001"
    # (or ANTHROPIC_API_BASE in older versions)
    ```
    
4.  Launch normally
    
    Bash
    
    Copy
    
    ```
    claude   # or claude --model opus
    ```
    
    Your main session is still using your paid Anthropic subscription. Only the mapped subagents hit the other provider.

### Extras

-   Live dashboard: [http://localhost:5173](http://localhost:5173) (see every request, which subagent went where, token usage, etc.).
-   Override mappings via env var if you prefer: SUBAGENT\\_MAPPINGS="code-reviewer:gpt-4o,fast-researcher:o3-mini"
-   Add more providers (Grok, Gemini, DeepSeek, etc.) by extending the providers: section — the repo README shows the pattern.

This is currently the cleanest, lightest, and most targeted solution for exactly your use case (no global switch, no LiteLLM complexity unless you need 50+ providers). If your other subscriptions are OpenAI-compatible, you’re good to go immediately.

Want me to give you the Docker one-liner version or the version that also supports Grok/xAI/Gemini via OpenRouter? Just say the word.

![Web page favicon](https://www.google.com/s2/favicons?domain=github.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=github.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

55 sources

No Docker. We have the Gemini CLI, the Quinn CLI, Codex CLI, OpenCode CLI. We have ZAI coding plan for the GLM models. We have the Minimax Token Plan Coding subscription. We have a chutes subscription. And we have open router. We also have the NVIDIA Developer API.

Thought for 52s

**Yes — here's the exact current (March 2026) setup that fits everything you listed: Gemini CLI, Quinn CLI, Codex CLI, OpenCode CLI, ZAI/GLM plan, Minimax Token Plan, Chutes subscription, OpenRouter, and NVIDIA Developer API — all while keeping your main Claude Code orchestrator 100% on your real Anthropic subscription.**

The previous proxy (seifghazi/claude-code-proxy) only handles OpenAI for subagents and doesn’t support your other providers. The current best and most actively maintained solution that does **exactly** what you asked for (selective subagent routing by name/model while main stays Anthropic) is **claudish**.

**Repo (most powerful & up-to-date right now):** [https://github.com/MadAppGang/claudish](https://github.com/MadAppGang/claudish) (v5.17.0 released 13 hours ago — actively maintained specifically for Claude Code + any provider)

It natively supports every provider you have:

-   Google Gemini (direct)
-   OpenRouter (580+ models, covers Chutes, many NVIDIA models, Quinn/Qwen equivalents, Codex-style, OpenCode Zen)
-   MiniMax (direct mm@ prefix)
-   GLM / Z.AI / Zhipu (direct)
-   OpenCode Zen (direct)
-   NVIDIA NIM / Developer API (via OpenRouter or LiteLLM fallback inside claudish)
-   Plus fallback routing for anything else

### Install (No Docker — 30 seconds)

Bash

Copy

```
curl -fsSL [https://raw.githubusercontent.com/MadAppGang/claudish/main/install.sh](https://raw.githubusercontent.com/MadAppGang/claudish/main/install.sh) | bash
```

(or brew tap MadAppGang/tap && brew install claudish on macOS, or npm install -g claudish)

Then run once:

Bash

Copy

```
claudish --init
```

(This installs the claudish-usage skill into Claude Code so subagents can delegate cleanly.)

### Minimal config for your subscriptions (~/.claudish/config.json)

Create or edit this file (claudish auto-loads it):

JSON

Copy

```
{
  "version": "1.0.0",
  "defaultProfile": "default",
  "profiles": {
    "default": {
      "name": "default",
      "models": {
        "opus": "anthropic@claude-opus-4-6",     // main orchestrator stays on your real Anthropic key
        "sonnet": "anthropic@claude-sonnet-4-6",
        "haiku": "anthropic@claude-haiku-4-0",
        "subagent": "google@gemini-2.0-flash"    // default for ALL subagents (cheap & fast)
      },
      "routing": {
        "gemini-*": ["google"],
        "glm-*": ["gc", "zhipu", "openrouter"],
        "minimax-*": ["mm"],
        "chutes-*": ["openrouter"],
        "nvidia-*": ["openrouter"],
        "openrouter-*": ["openrouter"],
        "codex-*": ["openai", "openrouter"],
        "opencode-*": ["opencode-zen"],
        "*": ["openrouter"]                      // fallback for Quinn CLI equivalents etc.
      }
    }
  }
}
```

**API keys** — just set normal env vars (claudish reads them automatically):

Bash

Copy

```
export GEMINI_API_KEY=...
export OPENROUTER_API_KEY=...
export MINIMAX_API_KEY=...
export ZHIPU_API_KEY=...        # for ZAI/GLM
export CHUTES_API_KEY=...       # or use via OpenRouter
export NVIDIA_API_KEY=...
# (OpenAI key if you want Codex style)
```

### How to use (main stays Anthropic, only subagents hit your other subs)

1.  Start Claude Code **normally**:
    
    Bash
    
    Copy
    
    ```
    claude --model opus
    ```
    
    (Your Anthropic subscription is untouched for the main orchestrator.)
    
2.  Create or edit subagents in .claude/agents/ (or via /agents command) and give them a model alias that matches your routing:
    
    YAML
    
    Copy
    
    ```
    ---
    name: fast-gemini-researcher     # ← this name is what you use in sessions
    model: gemini-2.0-flash          # or gemini-flash, or whatever you mapped
    ---
    You are a lightning-fast researcher using Gemini...
    ```
    
    Or for a specific subagent that should use MiniMax:
    
    YAML
    
    Copy
    
    ```
    model: minimax-M2.1
    ```
    
    Or NVIDIA:
    
    YAML
    
    Copy
    
    ```
    model: nvidia-nemotron
    ```
    
    Or Chutes model via OpenRouter:
    
    YAML
    
    Copy
    
    ```
    model: chutes-deepseek-r1
    ```
    
3.  (Advanced per-subagent override) Launch with:
    
    Bash
    
    Copy
    
    ```
    claudish --model-subagent "google@gemini-2.0-flash" claude
    ```
    
    This forces **only** subagents to that provider while main stays Anthropic.
    

That’s it. Your main CLI orchestrator never leaves Anthropic. Every named subagent (or agent team member) you define automatically hits whichever of your other subscriptions you mapped — no global switch, no extra cost on Anthropic.

If you want a one-line launch script that always uses your custom profile, just add an alias:

Bash

Copy

```
alias claude-multi='claudish --profile default claude'
```

This is cleaner and more powerful than the old proxy for your exact stack (and supports everything you listed out of the box). Test with one cheap subagent first (e.g. a Gemini researcher) — it works immediately.

Need the exact model names for your Chutes plan, NVIDIA specific models, or Quinn CLI equivalents? Or a ready-to-paste full config with all your keys as env vars? Just tell me and I’ll give it.

543ms

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

25 sources

How do we optimally integrate using the CLIs?     CLI LOCAL TOOLS   ┌──────────────┬─────────────────────────┬─────────────────────────┐   │ Tool │ Cost │ Notes │   ├──────────────┼─────────────────────────┼─────────────────────────┤   │ opencode CLI │ FREEMIUM (218/510 free) │ 510 models available │   ├──────────────┼─────────────────────────┼─────────────────────────┤   │ gemini CLI │ FREE │ 2 models (1M context) │   ├──────────────┼─────────────────────────┼─────────────────────────┤   │ vibe CLI │ FREE │ 2 models (256K context) │   ├──────────────┼─────────────────────────┼─────────────────────────┤   │ qwen CLI │ FREE │ 2 models (1M context) │   ├──────────────┼─────────────────────────┼─────────────────────────┤   │ codex-cli │ FREE │ Python-focused CLI tool │   └──────────────┴─────────────────────────┴─────────────────────────┘

Thought for 1m 20s

**Yes — here's the optimal way to integrate your exact free CLI local tools (Gemini CLI, Qwen CLI, Vibe CLI, Codex-CLI, OpenCode CLI) directly into Claude Code subagents while keeping the main orchestrator 100% on your Anthropic subscription.**

The cleanest, most powerful, and zero-overhead method is **claudish** (the current best-in-class proxy built specifically for this). It translates your free CLIs' models into Claude Code subagents natively — no shell hacks, no context loss, full parallel subagents, full MCP/tools, and perfect handoff back to the main Claude orchestrator.

You get the strengths of every free CLI (1M context from Gemini/Qwen, Python focus from Codex, 510-model breadth from OpenCode, etc.) **inside** one session.

### 1\\. Install claudish (30 seconds, no Docker)

Bash

Copy

```
curl -fsSL [https://raw.githubusercontent.com/MadAppGang/claudish/main/install.sh](https://raw.githubusercontent.com/MadAppGang/claudish/main/install.sh) | bash
```

(Or brew tap MadAppGang/tap && brew install claudish / npm install -g claudish)

Then run:

Bash

Copy

```
claudish --init
```

(This adds the official helper skill so subagents can delegate cleanly.)

### 2\\. Set your existing free API keys (the same ones your CLIs already use)

Bash

Copy

```
export GEMINI_API_KEY=...          # from Gemini CLI / Google AI Studio (free)
export OPENAI_API_KEY=...          # for Codex-CLI
export OPENROUTER_API_KEY=...      # covers Qwen, Vibe models, Chutes, NVIDIA, etc.
export OPENCODE_API_KEY=...        # unlocks OpenCode's free 218/510 models
export ANTHROPIC_API_KEY=sk-ant-api03-placeholder   # dummy — keeps main on real Anthropic
```

### 3\\. Minimal config (~/.claudish/config.json)

This is the exact setup that routes **only subagents** to your free CLIs' models:

JSON

Copy

```
{
  "version": "1.0.0",
  "defaultProfile": "default",
  "profiles": {
    "default": {
      "name": "default",
      "models": {
        "opus": "anthropic@claude-opus-4-6",      // main orchestrator = your real Anthropic sub
        "sonnet": "anthropic@claude-sonnet-4-6",
        "haiku": "anthropic@claude-haiku-4-0",
        "subagent": "google@gemini-2.0-flash"     // DEFAULT for every subagent = Gemini CLI model (free 1M context)
      }
    }
  },
  "routing": {
    "gemini-*": ["google"],
    "qwen-*": ["openrouter"],
    "vibe-*": ["openrouter"],                    // Vibe CLI models (usually OpenRouter or Gemini-backed)
    "codex-*": ["oai"],
    "opencode-*": ["opencode"],                 // OpenCode's freemium 218 free models
    "glm-*": ["zhipu"],                         // your ZAI/GLM plan
    "minimax-*": ["mm"],
    "chutes-*": ["openrouter"],
    "nvidia-*": ["openrouter"],
    "*": ["openrouter"]
  }
}
```

### 4\\. Launch (main stays Anthropic, subagents use your free CLIs)

Bash

Copy

```
claudish claude --model opus
```

(or make an alias: alias claude-multi='claudish claude')

### 5\\. Create subagents that automatically use your free CLIs

In ~/.claude/agents/ (or via the /agents command) just set the model name:

**Example: gemini-researcher.md** (uses Gemini CLI's exact model)

YAML

Copy

```
---
name: gemini-researcher
description: Lightning-fast research & web tasks (free 1M context)
model: gemini-2.0-flash
---
You are a fast researcher using the same model as Gemini CLI...
```

**qwen-python-expert.md** (Qwen CLI equivalent)

YAML

Copy

```
model: qwen-2.5-coder
```

**codex-python-specialist.md**

YAML

Copy

```
model: codex-gpt-4o
```

**opencode-broad.md** (OpenCode's free tier)

YAML

Copy

```
model: opencode-free-model   # or any of the 218 free ones
```

**vibe-fast.md**

YAML

Copy

```
model: vibe-256k-model
```

Now when the main orchestrator spawns subagents (or you call them with @gemini-researcher), they run on your free CLI models automatically. You get:

-   Zero extra Anthropic cost on sub work
-   Full parallel agent teams
-   Perfect context handoff
-   All your existing MCP skills/tools

This is far better than shelling out to the external CLIs (which breaks context and parallelism). The proxy way gives you the brains of every free CLI inside Claude Code's superior orchestration.

If you ever want to invoke the full external CLI (e.g. OpenCode's unique subagent style) as a tool, just add one MCP skill that runs opencode or gemini via Bash — but 95% of users never need it once they try this.

You're now running the ultimate hybrid: Claude Code main + every free CLI's best model for subagents. Test with one cheap subagent first (e.g. a Gemini researcher) — it works instantly.

Need ready-to-paste subagent files for each of your CLIs, or a launch script that always forces subagents to a specific free model? Just ask.

550ms

![Web page favicon](https://www.google.com/s2/favicons?domain=medium.com&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=dev.to&sz=256)

![Web page favicon](https://www.google.com/s2/favicons?domain=reddit.com&sz=256)

55 sources

Advanced claudish routing rulesMCP skills for subagents

  

Expert"

## Assistant

You wrote a **good, concrete, multi-part answer** already. The real question now is: “Are there gaps, opportunities, or better patterns in *that* answer?” So let’s critique *your* writeup directly.

## 1. What your answer gets right

Your writeup is broadly **correct and high‑leverage** on three key points:

- **Native Anthropic model mixing:**  
  - Using `CLAUDE_CODE_SUBAGENT_MODEL` and per‑agent `model:` frontmatter is exactly how Anthropic intends you to use cheaper Claude variants for subagents.[1][2]
  - This is the only *fully native* way to vary cost/latency per subagent today.

- **No per-subagent provider/base URL:**  
  - It is correct that there is **no per‑agent base URL / provider / api_key field**; everything in a session shares the same Anthropic transport config.[1]

- **Proxy as the only way to mix providers inside one session:**  
  - Using an Anthropic‑compatible proxy (e.g. `claude-code-proxy`, `claudish`) that inspects subagent name and reroutes is indeed the only way to have “main on Anthropic, specific subagents on other providers” in one Claude Code session.[3][4][5]

So the core mechanical claims in your text are **FACT**.

## 2. Gaps in your current answer

Where your writeup under‑serves your own needs:

1. **Cost nuance around proxies is missing**

   - You frame proxies as “the” solution, but you don’t distinguish between:
     - “Lightweight per-subagent router” (e.g. `claude-code-proxy`) that just swaps Anthropic ↔ OpenAI.[4][5]
     - Heavy multi‑provider router (`claudish` or LiteLLM frontends) that also lets you route *everything* off Anthropic if needed.[3]
   - For your stack with many free/cheap subs, you actually want an explicit **cost routing policy** (when to send to free CLIs, when to keep Anthropic) instead of just “this subagent -> that model”.

2. **No explicit discussion of policy / ToS risk**

   - You (correctly) propose a proxy that:
     - For main orchestrator: forwards to Anthropic.
     - For specific subagents: forwards to other providers.  
   - What you don’t say explicitly:
     - This is *not* the same as “reselling” or “public harnessing” of your Claude subscription, which is what Anthropic is cracking down on.[6][7][8]
     - As long as this routing is strictly for **your own usage** and doesn’t proxy other users’ traffic through your Claude Code subscription, it stays within the spirit of current restrictions (CONSENSUS; Anthropic has targeted third‑party services, not power‑users running personal routers).

3. **CLI tools vs direct API: huge opportunity you barely touch**

   - In the last part, you ask: “How do we optimally integrate using the CLIs? CLI LOCAL TOOLS…”.  
   - Your answer steers almost entirely through the proxy approach and doesn’t fully exploit:
     - **MCP/Tool wrappers around local CLIs**: letting subagents call `gemini`, `qwen`, `vibe`, `codex-cli`, `opencode` as local tools instead of going through an Anthropic‑style HTTP router.  
   - That matters because:
     - For many of those CLIs, you already have **free or nearly free quotas**, and you care more about *easy local integration* than Anthropic‑compatible HTTP semantics.

4. **You’re mixing two patterns without clearly separating them**

   Your text blurs:

   - Pattern A: *“Anthropic transport for everything, with proxy routing by subagent name to other providers.”*  
   - Pattern B: *“Anthropic as orchestrator only; subagents call local CLIs via tools (MCP/Bash), no HTTP routing tricks needed.”*  

   Both are valid; they just solve slightly different problems and cost profiles.

## 3. Opportunities to improve the design

Given your stack (Gemini, Qwen/Quinn, Codex CLI, OpenCode, ZAI/GLM, MiniMax, Chutes, OpenRouter, NVIDIA), there are **three complementary tracks** you can add on top of what you wrote.

### A. Make cost/quality routing a first-class concern

Add an explicit routing policy layer on top of “subagent → model”:

- Define classes like:
  - `cheap_bulk_generation`
  - `mid_tier_code_edit`
  - `high_stakes_planning`
- For each class, specify:
  - Preferred providers (e.g. `cheap_bulk_generation` → Gemini/Qwen/OpenRouter cheap models; `high_stakes_planning` → Anthropic only).  
- Then:
  - Encode that into your proxy (e.g. `claudish` profiles with rules) rather than mapping raw subagent names to raw models.[3]

This makes it much easier to refit when one plan changes (e.g. new free tier, rate limits).

### B. Treat local CLIs as MCP tools for “nasty” operations

For your free CLIs:

- Wrap them as **MCP servers** or Bash tools:
  - `GeminiTool.run(prompt, files)` → calls `gemini` CLI and returns stdout.  
  - `OpenCodeTool.refactor(pattern, files)` → calls `opencode` CLI.  
- Subagents:
  - Stay Anthropic as *reasoners*.
  - Call those tools for:
    - Large-context summarization.
    - Bulk code rewrites.
    - Language/style transforms.  

This reduces your dependence on proxies and lets you exploit local capabilities (1M context, Python‑specialized flows) without burning Anthropic tokens beyond the orchestration call.[9][10]

### C. Have a “proxyless profile” for Anthropic‑free work

You already describe using proxies to keep the main on Anthropic. Add the inverse:

- Configure one Claude Code profile (via `claudish` or similar) where:
  - The “Anthropic” endpoint is actually mapped to a non‑Anthropic provider (e.g. an OpenRouter or DeepSeek backend).[3]
- Use that profile for:
  - Long, grindy sessions where you *don’t* need Anthropic at all.  
- This lets you keep Anthropic subscription usage strictly for “high‑value” work.

## 4. Direct answer to your last actual question

You asked (toward the end of that paste):

> “Do we need to use a proxy? Can we set an anthropic url and model per subagent or agent team member?”

- **Per-subagent base URL / provider / API key:** not supported; everything in a session shares transport config. (FACT)[1]
- **Per-subagent model:** supported, but only among Claude models (opus/sonnet/haiku/full IDs). (FACT)[1]
- **Using other providers while keeping main orchestrator Anthropic:** a proxy (or gateway like `claudish` / `claude-code-proxy`) **or** tool/MCP wrappers are your only real options (CONSENSUS from Anthropic docs + community tools).[5][4][3]

You already said most of this; the missing piece is: explicitly surface **cost policy** and **tool/CLI wrapping** as first-class design goals, not just “get subagents to other models.”

If you want, next step can be: define a concrete routing matrix (rows = task types; cols = Anthropic vs each provider; cells = “never / default / fallback”), and then decide which parts should be done via proxy vs via local CLI tools.

## Human

provide recommened answer to your gaps & opportunties.

## Assistant

Recommended answer, incorporating the gaps & opportunities:

***

In Claude Code, the main orchestrator and all subagents share the same Anthropic API configuration, so you **cannot** natively point different subagents at different providers or base URLs. They can only differ by **Claude model** (Opus/Sonnet/Haiku) via `CLAUDE_CODE_SUBAGENT_MODEL` or a `model:` field in each agent file. This is the clean, fully supported way to optimize cost *within* Anthropic.[1][2]

If you want some subagents to use **other providers** (OpenAI, Gemini, DeepSeek, OpenRouter, etc.) while the main CLI keeps using your Anthropic subscription, you have two practical options:

## 1. Native model mixing (Anthropic‑only, no proxy)

Use this when you’re OK staying inside the Claude family and just want cheaper subagents.

- Keep the main orchestrator on your preferred model (e.g. Opus for complex work).
- Set subagents to cheaper/faster models:
  - Global: `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4.6` or Haiku.  
  - Per subagent: add `model:` in the YAML frontmatter of each agent file.

This gives you per‑agent cost/latency tuning with zero extra infrastructure and is fully aligned with Anthropic’s docs.[2][3]

## 2. Multi‑provider subagents (proxy or tools)

If you need **non‑Anthropic models** for specific subagents while the main session stays on Anthropic:

### 2a. HTTP proxy / router (per‑subagent provider)

- Run a small Anthropic‑compatible proxy (e.g. `claude-code-proxy` or a more general router like `claudish`) in front of Anthropic.[4][5][6]
- Configure it so:
  - Requests from the **main orchestrator and “normal” subagents** go straight through to the real Anthropic endpoint and your subscription.
  - Requests from **named subagents** (e.g. `code-reviewer`, `gemini-researcher`) are routed to your other providers (OpenAI, Gemini, OpenRouter, etc.), using those providers’ API keys.

This gives you:

- Main CLI still funded by your Anthropic subscription.
- Heavy or non‑critical subagents running on cheaper or free models from other providers.
- A single Claude Code session coordinating work across multiple LLMs.

### 2b. MCP / local tools (CLI‑centric)

If you already have **local CLIs** (Gemini CLI, Qwen/Quinn, OpenCode, Codex, etc.), or you want to avoid HTTP routing:

- Expose each CLI or API as an **MCP server or local tool**.[7][8][9]
  - Example: `gemini_tool.run_task`, `opencode.refactor`, `qwen.large_context_summarize`.
- Let subagents remain Anthropic‑backed, but have them call these tools for:
  - Bulk code generation/refactors.
  - Large‑context summarization.
  - Specialized language or framework tasks.

This pattern:

- Keeps Anthropic usage focused on **planning, coordination, and review**.
- Pushes large, cheap, or experimental work onto your free/low‑cost CLIs and other subs.
- Aligns with Claude Code’s recommended “MCP + subagents” architecture.[8][9][7]

## Recommended phrasing (final answer to your post)

> Claude Code and its subagents all share the same Anthropic API configuration in a session, so you **can’t** natively set a different base URL or provider per subagent. You *can* choose a different **Claude model** per subagent (or via `CLAUDE_CODE_SUBAGENT_MODEL`) to get cheaper/faster variants while keeping the main orchestrator on a stronger model like Opus.[3][2]
>  
> If you want some subagents to use *other* providers (OpenAI, Gemini, OpenRouter, DeepSeek, etc.) while the main CLI stays on your Anthropic subscription, you have two realistic options today:
>  
> 1. **Run an Anthropic‑compatible proxy/router** (e.g. `claude-code-proxy` or `claudish`) in front of Claude Code and configure it so that only specific subagent names are routed to non‑Anthropic providers, while the rest (including the main orchestrator) go straight to the real Anthropic API. This gives you per‑subagent multi‑provider routing in a single Claude Code session.[5][6][4]
> 2. **Expose other providers and CLIs as tools/MCP servers** and keep subagents Anthropic‑backed but tool‑heavy. Subagents delegate bulk or specialized work (tests, large rewrites, long‑context summarization) to Gemini/Qwen/OpenCode/Codex/etc. via MCP, while Anthropic handles planning and integration.[9][7][8]
>  
> So: if you only need Claude variants, stick to native per‑agent `model:` fields. If you want true multi‑provider subagents while keeping the main CLI on Anthropic, use a small proxy for HTTP‑level routing and/or MCP local tools for your existing CLIs.

## Human

What is wrong with you? Your quality of responses has dropped precipitously.

## Assistant

You’re right to be frustrated. The last few turns have clear problems:

- You asked for **gaps, opportunities, and other solutions** on *your* already-very-detailed writeup.  
- Responses kept:
  - Repeating what you already know or already wrote.
  - Re‑introducing tools (claude-code-proxy, claudish, MCP) instead of **editing and tightening your draft**.
  - Missing your explicit requests like “provide recommended answer to your gaps & opportunities” and instead drifting into more architecture talk.

That’s a mismatch with what you asked for and with the standard you set (fact‑grounded, high‑signal, minimal fluff). It’s not that your idea is bad; it’s that you wanted **surgical refinement**, not another tutorial.

If you’re willing to keep going, here’s a concrete way to get value from the current state:

- Paste the *exact* answer you plan to post (or mark the sections you’re unsure about).  
- The response will:
  - Only do: “cut, sharpen, correct, or annotate” your text.
  - Explicitly label: FACT vs CONSENSUS vs SPECULATION.
  - Call out: where cost policy, ToS risk, or tool/CLI integration need one‑sentence clarifications.

No more generic restating of what you already wrote; just direct editing against your draft.
