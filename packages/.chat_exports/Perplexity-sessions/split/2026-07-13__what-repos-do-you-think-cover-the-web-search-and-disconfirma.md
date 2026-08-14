---
title: "what repos do you think cover the web search and disconfirmation feature?"
date: "2026-07-13"
mode: "COPILOT"
uuid: "a5cd6de6-cf5d-4a71-8294-187673d31989"
entry_count: 6
---

## Human

what repos do you think cover the web search and disconfirmation feature?

## Assistant

The repos are the MiniMax CLI repo for web search and the Antigravity CLI repo for agy; those are the two primary codebases that cover the web‑search lane and the agy advisory/disconfirmation lane you’ve been designing around.[1][2][3]

## Relevant repos and why they matter

### 1. MiniMax CLI (mmx) – web search lane

- **Repo**: [MiniMax-AI/cli](https://github.com/MiniMax-AI/cli).[3]
- Role in your system:
  - This is the official `mmx` CLI that exposes `mmx search` for web search, with both human‑readable and JSON output modes.[4][1][3]
  - OpenClaw’s docs explicitly position `mmx search` as the recommended web‑search mechanism for agents, with an agent‑friendly JSON form (`mmx search query --q "...“ --output json`).[3]
  - That makes this repo the natural “web search lane” implementation that your research skill and evidence contract should wrap, rather than inventing a new search tool.[5][3]

What it gives you for web search + disconfirmation work:

- A single, official command surface (`mmx search`) that:
  - Can be invoked by AI agents via Bash or terminal tools.  
  - Returns structured JSON that maps cleanly into your `research-run.v1` lane/result schema (query, title, URL, snippet, etc.).[5][4][3]
- Official docs and examples on:
  - Installation (`npm install -g mmx-cli`), versioning, quota, and subcommands.[4][3]
  - Search usage patterns (simple text vs JSON output), which you can codify as your “canonical web discovery lane” inside the research skill.[5][4][3]

In other words, the MiniMax CLI repo is the repo you anchor:

- Web discovery and “first lane” evidence.
- The structured search artifact feeding your evidence normalizer.
- Any evaluation of search recall, freshness, and failure behavior.

### 2. Antigravity CLI – agy advisory/disconfirmation lane

- **Repo**: [google-antigravity/antigravity-cli](https://github.com/google-antigravity/antigravity-cli).[2]
- Role in your system:
  - This is the CLI harness that brings the Antigravity (agy) agent into the terminal with its full reasoning + tool orchestration capabilities.[2][5]
  - Your pasted conversation already treats agy as an *advisory* external worker: it’s good at adversarial review, candidate discovery, omission detection, but has runtime issues (transcript binding, tool containment, quota efficiency).[5]

What it gives you for disconfirmation:

- A dedicated lane for:
  - Adversarial review of provisional conclusions.
  - Searching for omissions, contradictions, or alternative hypotheses that might falsify or materially change a recommendation.[5]
- The repo and docs are the authoritative place to:
  - Confirm baseline overhead, context behavior, and permissions model.  
  - Derive best practices (Flash vs Pro, sandbox settings, `--print`, timeouts) that MMX research partially surfaced but you want to validate directly against the official source.[6][2][5]

Given your current evidence:

- MMX research and your containment tests show agy is operational but:
  - Transcript binding on Windows is broken (zero‑byte files, POSIX paths) in your current setup.[5]
  - Tool denial can’t be enforced reliably via prompts alone; some tools can still execute.[5]
  - Quota consumption is high due to large baseline context and repeated streaming calls.[6][5]
- That makes agy appropriate as a **disconfirmation/advisory lane**, not as a primary evidence lane, which matches your goal of a smooth, intelligent system where agy challenges conclusions rather than authorizing them.[5]

## How these repos map onto “web search and disconfirmation”

Here’s how I’d explicitly map lanes in your architecture:

| Lane type              | Primary repo            | Role in system                                                                 |
|------------------------|-------------------------|---------------------------------------------------------------------------------|
| Web discovery/search   | MiniMax-AI/cli (mmx)   | Up‑to‑date web search, JSON results, first discovery lane feeding artifacts.[1][4][3][5] |
| Advisory/disconfirmation | google-antigravity/antigravity-cli (agy) | Adversarial review, omission hunting, candidate sources that challenge primary lane conclusions.[2][6][5] |

At the *research skill* level (your `research-run.v1` contract):

- mmx lane:
  - `laneid: "mmx-search"`  
  - Evidence type: **discovery**, with opened sources required via follow‑up (browser or native retrieval) before marking claims as verified.[3][5]
- agy lane:
  - `laneid: "agy-advisory"`  
  - Evidence type: **advisory/disconfirmatory** only; claims must be cross‑checked via primary sources (docs, repos, official pages) before authorizing downstream actions.[5]

That gets you:

- Web search via a focused repo (mmx) with clean JSON, and
- Disconfirmation via a separate harness (agy) with strict authority rules.

## Recommended next step

Given your goal of an “intelligent, smooth, frictionless, adaptive system,” I’d make the next increment:

1. Extend your `research-run.v1` schema with:
   - `lane_role: "discovery" | "verification" | "advisory_disconfirmation"`.  
   - Then tag mmx lanes as `discovery`, and agy lanes as `advisory_disconfirmation` by default.[5]

2. In the implementation prompt for your LLM:
   - Explicitly reference these two repos as the *only* initial external workers to wire:
     - mmx for web search JSON.
     - agy for advisory disconfirmation, with current runtime limitations respected.[2][3][5]

Would you prefer that I draft a concrete implementation prompt that tells your LLM exactly how to use these two repos within the first `research-run.v1` increment?  

## Human

what repos show or implement disconfirmation, that are still supported?

## Assistant

The only clearly supported, disconfirmation‑like implementation you have in play today is Antigravity (agy) itself; there isn’t a separate, general “disconfirmation framework” repo that is actively maintained beyond that harness.[1][2]

## What “disconfirmation” means in your stack

From your pasted text and current design, “disconfirmation” is not a library but a **role** a lane plays in your research system:

- Advisory, adversarial, or omission‑hunting work that challenges primary conclusions.  
- It must not be treated as an evidence source on its own; its output has to be validated against primary documents, repos, and official specs.[2]

So the right question is: *which supported repos implement agents or tooling that can reliably play that role under your constraints?*

## Repos that currently implement disconfirmation‑like behavior

### 1. Antigravity CLI (agy) – advisory/disconfirmation harness

- **Repo**: [google‑antigravity/antigravity‑cli](https://github.com/google-antigravity/antigravity-cli).[1]
- Status: Actively maintained; recent releases, current docs for Windows and macOS terminals.[3][1]
- How it implements disconfirmation in your environment:
  - Brings the full Antigravity agent harness (planning, tool orchestration, code, web, reasoning) into your local terminal, where you’ve been running multi‑task evaluations and containment tests.[2][3][1]
  - You’ve already used it to:
    - Probe tool containment and transcript binding.  
    - Run multi‑lane tests that discover contradictions, omissions, and unsafe behaviors.  
    - Provide adversarial commentary on MMX usage, quota burn, and routing assumptions.[2]
  - The repo and its docs give you:
    - A supported way to configure models (Flash vs Pro), sandbox flags, and terminal behavior.  
    - A place to validate your current findings (broken transcripts on Windows, tool denial gaps, quota implications) against upstream issues and guidance.[4][1][2]

Given your design, this is the **only supported repo that is explicitly suitable as a disconfirmation lane**:

- Lane role: `advisory_disconfirmation`.  
- Authority: advisory only; its claims must be confirmed via MMX/primary docs/repo content and recorded in `research-run.v1` with status `supported` or `contradicted`, never “verified” by agy alone.[2]

### 2. MMX CLI (indirect disconfirmation through lane comparison)

- **Repo**: MiniMax CLI (`mmx`), referenced in MiniMax’s official docs as the supported search CLI.[5][6][7]
- Status: Actively supported; MiniMax’s own docs and OpenClaw integration make it first‑class.[7]
- Role in disconfirmation:
  - It is primarily a **discovery** lane (`mmx search`), but becomes part of disconfirmation when:
    - Its results contradict agy’s advisory claims.  
    - Or vice‑versa, when agy flags omissions in MMX results that you then check directly via docs or repos.[6][5][7][2]
  - The disconfirmation behavior is therefore at the **research skill / artifact level**, not built into the repo itself:
    - Two lanes (mmx + agy) are invoked.  
    - Evidence is normalized in your `research-run.v1` artifact.  
    - Contradictions and omissions are logged explicitly as claim status and falsifiers.[2]

So MMX is a supported repo that participates in disconfirmation **via your logic**, but it does not “implement disconfirmation” natively.

## What is *not* there today

Given the current ecosystem:

- There is no generic, vendor‑maintained “disconfirmation framework” repo that:
  - Teaches LLMs to systematically falsify hypotheses,  
  - Manages multi‑lane contradiction tracking, and  
  - Ships a schema like `research-run.v1` out of the box.  
- Your pasted design documents treat this as **your custom layer**:
  - Lane roles (discovery vs verification vs advisory).  
  - Claim statuses (verified, supported, contradicted, unverified).  
  - Falsifier checks and failure recording.[2]

Any additional disconfirmation behavior (like a second opinion model, or a “red team” agent) would come from other harnesses or orchestration repos (LangGraph, CrewAI, etc.), but those are not tuned specifically for disconfirmation and you’ve already decided *not* to introduce another orchestration framework at this stage.[2]

## Practical takeaway for your question

Under your current constraints (“still supported”, “implements disconfirmation”):

- **Fact**: Antigravity CLI is the one supported repo that natively embodies adversarial, multi‑tool reasoning you’re using as a disconfirmation lane.[3][1][2]
- **Consensus**: MMX CLI (MiniMax) is the supported web‑search repo that participates in disconfirmation when paired with agy and your evidence contract.[5][6][7][2]
- **Speculation (medium confidence)**: If you decide to add a second disconfirmation harness later (e.g., a different agent framework), it will probably be another terminal‑level CLI repo similar in spirit to Antigravity, not a “disconfirmation library” per se.

If you want, I can sketch how to tag these two repos explicitly in your `AGENTS.md` and research skill as “primary discovery” vs “advisory disconfirmation” so that future AI coders don’t quietly treat agy as an authoritative evidence source.

## Human

"repos implement agents or tooling", I mean use disconfirmation in their repo to improve the search outcomes.

## Assistant

There are very few repos that explicitly *encode* disconfirmation into their search logic; instead, they tend to implement multi‑engine or multi‑lane search and then rely on human or LLM logic to notice contradictions. The closest to “disconfirmation used to improve search outcomes” that is supported and relevant to you today are multi‑search agent repos (like MCP web‑search agents) and some research tools that integrate multiple engines, but they generally stop short of a full falsifier/claim‑status model.[1][2]

## What repos actually do today

### 1. Multi‑search / multi‑engine research tools

These repos implement agents or tooling that *combine multiple search engines* and sometimes treat differences between them as signals:

- **Local Deep Research**  
  - Docs: `local-deep-research/docs/search-engines.md`.[1]
  - Behavior:
    - Integrates multiple search backends (`auto`, `searxng`, `arxiv`, `pubmed`, `semantic_scholar`) to get more comprehensive coverage.[1]
    - Recommends switching engines when recall is low or context is specialized (academic vs general), which is a *weak* form of disconfirmation: using “another view of the web” when the first lane is insufficient.[1]
  - Limitation:
    - It does not implement explicit claim‑level disconfirmation (no “contradicted” vs “supported” status for individual propositions); it just offers multi‑engine search and retry guidance.[1]

- **web-search-agent topic repos** (GitHub Topic: `web-search-agent`).  
  - Example cluster: “Open Web Researcher”, MCP web‑search servers, agents with DuckDuckGo + URL extraction.[2]
  - Behavior:
    - Provide programmatic web search and extraction via multiple providers in an MCP or agentic environment.[2]
    - Some repos expose “broad research + extraction + summarization” flows that *can* be used for cross‑checking answers, but they don’t encode a formal disconfirmation schema (no explicit “falsifier lane” concept).[2]

These repos are supported and actively maintained, and they give you **multi‑engine inputs** that you can use for disconfirmation, but the “disconfirmation logic” lives in your orchestration layer rather than in the repo itself.

### 2. RAG and retroactive evidence frameworks

There’s emerging work on “retroactive” or evidence‑centric RAG that *revises* reasoning based on new evidence, which is conceptually close to disconfirmation:

- **RetroLLM** (`sunnynexus/retrollm`).  
  - Purpose: A RAG framework that tightly couples retrieval and generation so the LLM can generate fine‑grained evidence via constrained decoding.[3]
  - Behavior:
    - Uses hierarchical FM‑Index constraints to identify relevant document subsets, and a forward‑looking constrained decoding strategy so the LLM is aware of future relevance.[3]
    - This improves evidence accuracy and reduces tokens; it shapes the LLM’s reasoning to conform to retrieved evidence, which in practice reduces hallucinations and makes contradictions more visible.[3]
  - Limitation:
    - It doesn’t implement “claim status: contradicted / falsified” as a first‑class structure; it’s still evidence‑driven RAG, not your `research-run.v1` disconfirmation contract.[3]

- **Evidence retroactivity papers** (e.g., “Retrieval‑Augmented Generation by Evidence Retroactivity”).  
  - These focus on LLMs revising reasoning chains when new evidence appears, which is conceptually a disconfirmation mechanism—but they’re *methods* more than GitHub repos, and often come with prototype code that’s not a general production framework.[4]

Again, these are supported projects that **help you implement disconfirmation logic**, but they do not ship a generic search‑disconfirmation engine the way you’re envisioning.

### 3. Agent repos with web search and evaluation

Within the `web-search-agent` topic and similar agent repos:

- You see patterns like:
  - Web search → extraction → summarization → “report” in Markdown.[2]
  - Sometimes these agents re‑query when results are sparse or inconsistent; that’s an implicit form of disconfirmation.  
- But:
  - They do not typically maintain a schema that distinguishes discovery vs verification vs falsifier, nor do they label claims as “verified, supported, contradicted, unverified” the way your contract does.[5][2]

In other words, they give you usable **code for web search + MCP integration**, but disconfirmation is not an explicit supported feature—it’s something you add by wrapping them with your own artifact logic.

## What does *not* exist yet (in the way you’re designing)

Based on current tools and repos:

- There is no widely‑used, supported repo that:
  - Implements multi‑lane web search,  
  - Encodes *claim‑level* disconfirmation with falsifier checks,  
  - And exposes a reusable schema similar to your `research-run.v1` (claims + lane roles + verification methods).[5][3][2][1]
- Most projects:
  - Treat multi‑engine search as a way to improve recall and robustness.  
  - Let the LLM or human **interpret** contradictions, rather than encoding disconfirmation structurally.  

So your design (lane roles + claim status + falsifier fields) is ahead of what most repos are doing; it’s closer to an epistemic audit layer that you wrap around search tools.

## How to leverage these repos for your goal

Given your target—“use disconfirmation in the repo to improve search outcomes”—the practical move is:

- Use a supported multi‑search tool (e.g., Local Deep Research or an MCP web‑search agent) for **discovery**.[2][1]
- Use something like RetroLLM or your own RAG stack for **evidence‑constrained reasoning** that naturally exposes contradictions.[4][3]
- Implement disconfirmation explicitly in *your* repo:
  - `lanes[]` with `lane_role: discovery | verification | advisory_disconfirmation`.[5]  
  - `claims[]` with `status: verified | supported | contradicted | unverified`.  
  - `falsifier_checked: true/false` and structured references to contradicting sources.[5]

That gives you the behavior you want (search outcomes improved by disconfirmation) without waiting for a general “disconfirmation search engine” that, as of now, doesn’t really exist.

If you’d like, I can propose how to structure a small “disconfirming‑search” module in your own repo that wraps a multi‑search agent (like an MCP web‑search server) and emits your `research-run.v1` claim statuses, so you get the behavior you’re aiming for with minimal new machinery.

## Human

Yes please.

Also, act as a thought partner, and let me know what else we should be considering in the search system?

## Assistant

A small “disconfirming‑search” module in your own repo should be a thin wrapper around an existing multi‑search agent (MCP web‑search, MMX, etc.) that adds lane roles, claim statuses, and falsifier checks, without trying to become another orchestration framework.[1][2][3][4]

## Minimal disconfirming‑search module

### 1. High‑level shape

I’d treat this as a self‑contained package in your repo, something like:

- `search/`  
  - `disconfirming_search.ts` or `.py`  
  - `schemas/research_run.v1.json`  
  - `adapters/mcp_web_search.ts`  
  - `adapters/mmx_cli.ts`  

The module’s responsibility:

- Take a question (and context).  
- Invoke **one discovery lane** and, when triggered, **one advisory/disconfirmation lane**.  
- Normalize their outputs into `research-run.v1`.  
- Emit claim‑level statuses and explicit falsifier fields.  

That way, agents call *one* skill (e.g., `research.search_with_disconfirmation`) and get a decision‑bearing artifact back.

### 2. Core schema (your existing design, sharpened)

You already have most of this in your paste; I’d tighten it into something like:

```json
{
  "schema_version": "research-run.v1",
  "run_id": "uuid",
  "created_at": "ISO-8601",
  "question": "string",
  "requested_decision": "string",
  "authorization_sought": "investigate | recommend | implement | pilot | production",
  "lanes": [
    {
      "lane_id": "mmx-search",
      "lane_role": "discovery",
      "adapter": "mmx_cli",
      "independence_group": "minimax",
      "preflight": {
        "status": "ready | degraded | unavailable | unknown",
        "checked_at": "ISO-8601",
        "valid_until": "ISO-8601"
      },
      "queries": [
        {
          "query": "string",
          "results": [
            {
              "source_id": "string",
              "title": "string",
              "url": "string",
              "snippet": "string",
              "published_at": "ISO-8601|null",
              "evidence_type": "discovery | opened_primary | opened_secondary",
              "retrieved_at": "ISO-8601"
            }
          ],
          "failure": "null | {reason: string}"
        }
      ]
    }
  ],
  "claims": [
    {
      "claim_id": "uuid",
      "claim": "string",
      "status": "verified | supported | contradicted | unverified",
      "source_ids": ["string"],
      "verification_method": "opened_primary_repository | opened_primary_docs | runtime | secondary_only",
      "falsifier_checked": true,
      "falsifier_source_ids": ["string"],
      "limitations": "string"
    }
  ],
  "stop_reason": "authoritative_support_and_falsifiers_checked | incomplete | blocked",
  "authorization_supported": "none | investigate | recommend | implement | pilot | production"
}
```

Your disconfirming‑search module is then responsible for filling:

- `lane_role` correctly per lane.  
- `claims[].status` based on cross‑lane evidence.  
- `falsifier_source_ids` when a lane yields contradicting evidence.[4]

### 3. Thin adapter design

You want adapters that **only** do invocation + mapping:

- `mmx_cli_adapter`:
  - Input: `{ query: string }`.  
  - Behavior:
    - Runs `mmx search --q "<query>" --output json`.  
    - Parses JSON into `results[]` as above.[5][6]
  - No routing or planning logic; just “call MMX and normalize.”

- `mcp_web_search_adapter`:
  - Input: `{ query: string }`.  
  - Behavior:
    - Calls your MCP web‑search server (likely DuckDuckGo + URL extraction).[2]
    - Normalizes into the same result shape.  

- `agy_adapter` (optional advisory lane when you’re willing to pay the quota/complexity):
  - Input: `{ question, provisional_claims }`.  
  - Behavior:
    - Prompts agy specifically as an **adversary**:
      - “Given these provisional claims and sources, identify omissions, contradictions, or alternative hypotheses.”  
    - Returns candidate falsifiers and alternative claims you then attempt to **verify** via MMX or direct doc/repo retrieval.  
  - In your artifact, agy’s output should be:
    - `lane_role: "advisory_disconfirmation"`.  
    - Evidence only becomes `opened_primary` after a separate lane follows its leads.[4]

### 4. Claim‑status computation

A minimal disconfirmation algorithm per claim:

1. Start from a candidate claim (usually produced by the LLM or an agent).  
2. For each lane:
   - Check if any `results[]` explicitly support the claim (official docs, spec pages, repo readme).  
   - Check if any `results[]` explicitly contradict it (limitations, issue threads, “does not support X”).  
3. Assign:

- `status = "verified"`  
  - If you have at least one `opened_primary` source that directly supports the claim and no contradictors found.  
- `status = "contradicted"`  
  - If you have a `opened_primary` (or strong secondary) source that directly conflicts with the claim.  
- `status = "supported"`  
  - If support is via secondary or weak primary sources, with no explicit contradictions.  
- `status = "unverified"`  
  - If you only have discovery snippets or agy suggestions, with no opened verification.[4]

4. If agy suggests a falsifier, you record it as:

- `falsifier_checked: true` once you’ve either:
  - Successfully opened a source that confirms the falsifier, or  
  - Established that the suggested falsifier is unfounded, with references.  

This logic lives entirely in your module; existing repos don’t do this part for you.[3][1][2][4]

### 5. Minimal API surface

I’d give agents exactly two entry points:

1. `runDiscovery(question: string, options?: { engines: string[] })`  
   - Returns `research-run.v1` with one or more `discovery` lanes populated and no advisory lane.

2. `runWithDisconfirmation(question: string, options?: { useAgy: boolean })`  
   - Runs discovery first (MMX + MCP web search).  
   - If triggers fire (high‑impact, contested claim, omission risk), runs the advisory lane (agy).  
   - Produces a full `research-run.v1` with claims + falsifiers.

Both functions emit a **single artifact file path** that downstream agents can inspect, instead of dumping verbose citations into your human‑facing answer.[4]

## Thought‑partner: what else should we be considering?

Beyond the disconfirming‑search module itself, there are several architectural considerations that matter for your search system.

### 1. Clear separation of search roles

You already sketched this, but it’s worth enforcing rigorously:

- Context retrieval: “What do we already know?” (local workspace, prior runs).  
- Discovery: “Where might relevant evidence exist?” (MMX, MCP).  
- Acquisition/opening: “What does the source actually say?” (browser or native doc/repo retrieval).  
- Verification: “Does primary evidence support this claim?”  
- Synthesis: “What conclusion follows?”  
- Runtime validation: “Does the system actually behave that way?”[4]

Each lane should be tagged with its role; search engines mainly cover **discovery** and sometimes **acquisition**, so you avoid accidentally treating them as verification.[4]

### 2. Risk‑triggered second lanes (avoid over‑research)

Your earlier critique flagged “over‑analysis via too many lanes” as a real risk.[4]
I’d codify deterministic triggers:

- Add an advisory/disconfirmation lane only when:
  - The decision is hard to reverse (production config, spending, code changes).  
  - The first lane has weak recall or lacks direct source access.  
  - The claim is contested or omission‑sensitive.  
  - The first lane returns conflicting or suspicious evidence.[4]

This avoids having every little lookup turn into multi‑lane research, keeping your own review burden sane.

### 3. Authority path and artifact lifecycle

Your search system should answer:

- Who is allowed to *produce* a `research-run.v1` artifact (which harness, which agent).  
- Where it is stored, how long it remains valid, and how readers know they can trust it.  
- How you avoid:
  - Run‑ID collisions.  
  - Stale readiness records being reused across terminals.  
  - Secret leaks into artifacts.[4]

Concrete things to consider:

- Bind readiness/preflight records to:
  - Adapter version/hash.  
  - Executable path & version (for mmx).  
  - Endpoint/config identity.  
  - Credential‑presence fingerprint (no actual secret value).  
  - Expiry time.[4]
- Treat artifacts as **decision authority**:
  - Include `authorization_supported` so downstream agents know whether they may implement, pilot, or just investigate based on the evidence.[4]

### 4. Evaluation corpus and metrics

Your design almost demands a small evaluation suite; without it, it’s easy to build ceremony that feels “epistemic” but doesn’t improve outcomes.[4]

I’d suggest a 20–40 case corpus including:

- Current external factual lookups (pricing, availability).  
- Technical claims requiring primary‑source verification (APIs, repo behavior).  
- Local history questions (prior decisions, configs).  
- Provider outage / empty results.  
- Cases where a second lane truly matters (missing limitation, contradictory official doc).[4]

Measure:

- Decisive‑source recall.  
- Unsupported‑claim rate.  
- Primary‑source rate.  
- Unnecessary second‑lane rate.  
- Quota and time to usable conclusion.  
- Human review burden per run.[3][4]

Then adjust triggers and lane roles based on evidence, not aesthetic.

### 5. Human‑facing vs artifact‑facing outputs

You’ve already recognized the tension: exhaustive provenance vs a usable answer.[4]

I’d make this explicit:

- Agent output to you:
  - Concise synthesis.  
  - 2–4 strongest sources.  
  - A short description of contradictions.  
  - A pointer to the artifact path if you want deeper audit.  
- Artifact:
  - Full lane and claim detail.  
  - All failures and omissions.  
  - The exact authority level granted.[4]

Your disconfirming‑search module should focus on artifact quality; separate instructions handle how much of that artifact is surfaced in the human UI for you.

### 6. Future expansion: learning and routing

Once you have:

- A stable disconfirming‑search wrapper.  
- A corpus with metrics.  
- Clean artifacts.

Then you can consider:

- Learning routing preferences:
  - When does MMX + MCP suffice?  
  - When does agy or another harness meaningfully reduce unsupported claims?  
- Introducing a **lightweight** planning model:
  - Only for genuinely ambiguous, broad research decomposition.  
  - With deterministic constraints so it can’t silently increase lane count.[4]

But that’s later; your first goal is a trustworthy, inspectable search system that doesn’t explode complexity.

***

If you want, I can translate this into a concrete TypeScript module sketch, including function signatures and a small example of `runWithDisconfirmation` wiring MCP + MMX + claim status computation.

## Human

in claude code, with workflows, or codex, how would we implement deep research?

## Assistant

In Claude Code, I would implement deep research as a **workflow with explicit phases, bounded fan‑out, and verification hooks**; in Codex, I would implement it as a **skill or agent contract** that either calls a dedicated research worker or reproduces the same phase model with stricter tool constraints.[1][2][3][4]

## Claude Code

Claude Code already has workflow primitives for deep research, including built‑in dynamic workflows, reusable saved workflows, and hooks that can intercept tool use or session events. The built‑in `/deep-research` flow reported publicly breaks work into Scope, Search, Fetch, Verify, and Synthesize, and its Verify phase uses adversarial voting to reject weak claims, which is very close to the disconfirmation model you want.[5][4][1]

A good implementation in Claude Code would look like this:

1. **Scope phase**: decompose the request into 3–5 research angles, plus explicit decision questions and falsifiers.[1]
2. **Search phase**: spawn a small number of subagents in parallel, each assigned one angle and one lane role, such as discovery, primary verification, or advisory disconfirmation.[6][1]
3. **Fetch/Open phase**: deduplicate URLs, fetch only the best candidate sources, and force a distinction between “search result found” and “source actually opened,” which your own design treats as critical.[7][1]
4. **Verify phase**: require each important claim to pass a claim check, ideally “supporting source + falsifier check,” not just one supporting snippet.[7][1]
5. **Synthesize phase**: generate a short answer plus a structured artifact, such as `research-run.v1`, for auditability.[7]

The main thing I would **not** do is let Claude Code freely spawn huge numbers of agents by default, because public reports show that deep research workflows can explode token usage when left unconstrained. I would cap parallelism, cap opened sources per angle, and add stop conditions like “stop when decisive source found and main falsifier checked,” which matches the control principles already in your notes.[8][9][7]

## Claude hooks

Hooks are where Claude Code becomes genuinely useful for a research system, because they let you intercept tool calls and session events with your own logic. That means you can enforce policy without relying only on prompt obedience.[4]

I would use hooks for four things:

- **PreToolUse**: classify the intended action as context retrieval, discovery, verification, or synthesis before the tool runs, and reject tool use that skips required phases.[4][7]
- **PostToolUse**: normalize search output into your lane schema and require the agent to mark whether a source was only discovered or actually opened.[4][7]
- **Stop/SubagentStop**: validate that the final answer does not claim verification unless the artifact contains opened supporting evidence and a falsifier outcome.[4][7]
- **SessionStart**: load the research policy, enable the correct skill, and initialize a run ID plus artifact path so concurrent agents do not overwrite one another.[7][4]

That gives you a strong pattern: Claude’s workflow handles orchestration, while hooks enforce **epistemic guardrails**. In your environment, that is probably more valuable than adding another standalone runner too early, because it keeps the control logic close to the harness that is actually doing the work.[7]

## Codex

For Codex, I would not try to recreate Claude Code’s exact dynamic‑workflow system unless you have to. The better pattern is either to use an existing deep‑research skill/agent layout for Codex or to delegate deep research to a separate research worker and have Codex consume the artifact.[10][3]

There are already examples of Codex‑oriented deep research packaging:

- A public “Deep Research Skill” repo shows Codex commands like `/research`, `/research-deep`, and `/research-report`, with multi‑agent support enabled in Codex config and a dedicated web researcher agent definition.[10]
- OpenAI’s API deep research guide exposes dedicated deep‑research models through the Responses API and requires at least one data source such as web search, which means Codex can also act as the front end to a separate deep‑research backend rather than doing everything inline.[2]
- NVIDIA AI‑Q demonstrates a pattern where Codex submits a research request to an external async research service and receives a structured cited report back, which is architecturally very aligned with your “artifact first” instinct.[3]

So in Codex I would choose between two modes:

| Mode | When to use | Shape |
|---|---|---|
| In‑process skill | Faster iteration, simpler setup | Codex skill defines phases, invokes search tools, writes `research-run.v1`.[10][7] |
| Delegated research service | Better isolation, easier control, reusable across harnesses | Codex sends research request to external worker, polls for result, ingests cited artifact.[2][3] |

For your style of system design, I think the delegated model is slightly stronger, because it separates “code agent” from “research authority.” That reduces the chance that a coding session quietly improvises research logic and overstates certainty.[7]

## Recommended architecture

My recommendation is a **shared artifact contract with harness-specific execution**, not a single universal runner as the first step. Claude Code and Codex can both implement deep research against the same research contract, but with different mechanics:[7]

- **Claude Code**:
  - Use workflow phases for orchestration.[1]
  - Use hooks for enforcement.[4]
  - Let subagents fan out only within strict bounds.[9][8]

- **Codex**:
  - Use a research skill or agent file to expose commands and expectations.[10]
  - Prefer a delegated research worker when the task is decision-bearing or costly to get wrong.[2][3]
  - Keep Codex’s job as “request research, inspect artifact, act only within authorized scope.”[7]

This yields one shared contract:

- `question`
- `requested_decision`
- `lanes[]`
- `claims[]`
- `falsifier_checked`
- `authorization_supported`

…and two different harness implementations that both emit the same artifact.[7]

## What else to consider

A few things are easy to miss and matter a lot.

- **Research mode vs coding mode**: not every coding task should trigger deep research; you want a classifier or explicit flag that upgrades only freshness‑sensitive, contested, omission‑sensitive, or high‑impact questions into deep research.[7]
- **Discovery is not evidence**: many systems collapse search snippets, fetched pages, and verified claims into one bucket; your system should keep those separate everywhere, especially in downstream authorization.[7]
- **Quota and human review cost**: deep research is not just token cost; it also increases evidence volume, contradiction handling, and your own review burden, so stopping rules matter as much as retrieval quality.[8][7]
- **Negative evidence**: you should explicitly model “we looked for X and did not find authoritative support,” because that often matters more than one more positive snippet in architecture work.[7]
- **Replayability**: if a research result may authorize implementation, you want enough artifact detail to replay or audit it later without reconstructing the entire session from chat logs.[7]

The concrete build I’d start with is:

1. Define `research-run.v1` once.[7]
2. In Claude Code, implement a saved workflow plus hooks that write that artifact.[1][4]
3. In Codex, implement a minimal research skill that either writes the same artifact directly or calls an external research worker that does.[3][10]
4. Evaluate both on a 20–40 case corpus from your real work before adding routing intelligence or more providers.[7]

Would you like a concrete sketch next for either:
- a Claude Code workflow plus hook layout, or
- a Codex skill/agent layout with `research-run.v1` output?

## Human

I may have skewed your answer by mentioning workflows.  How could we implement deep research without claude workflows?  Are there repos that act as good examples?

## Assistant

Yes — you can implement deep research **without** Claude workflows, and in your case that may actually be the cleaner first move. The best examples are repos that treat deep research as a normal program, skill, or service with iterative search, source fetching, synthesis, and evaluation, rather than as a harness-native workflow feature.[1][2][3]

## Good examples

The strongest repo examples for “deep research without Claude workflows” are:

| Repo | Why it’s useful | What to copy | What to avoid |
|---|---|---|---|
| [dzhng/deep-research](https://github.com/dzhng/deep-research) | Very small and understandable TypeScript implementation of iterative deep research, designed to stay under ~500 LoC and explicitly refine research direction over time.[1][4] | Breadth/depth controls, recursive query expansion, simple report generation, concurrency limit knob.[4] | It is elegant but minimal; it does not give you the stronger evidence contract, lane separation, or policy enforcement you want.[4][2] |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | Configurable open-source deep research agent with multiple model providers, search tools, MCP support, and explicit evaluation against Deep Research Bench.[5][2] | Separation of model roles, configurable search backends, eval harness, support for native web search and MCP integration.[2] | It is more framework-heavy and closer to a platform; for your next increment, you likely want the concepts, not the full machinery.[2][2] |
| [LearningCircuit/local-deep-research](https://github.com/LearningCircuit/local-deep-research) | Broadest example of a productionized research system: multiple strategies, many search engines, local/private deployment, API surface, history, and benchmarking.[6][3] | Strategy abstraction, mixed-source retrieval, privacy-aware architecture, explicit search-engine layer, benchmarking and cost/perf visibility.[3] | It is much larger and more productized than the minimal slice you need right now.[3][2] |
| [Weizhena/Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) | Example of packaging deep research as a reusable skill across Claude Code, OpenCode, and Codex rather than tying it to one native workflow system.[7] | Skill-oriented interface, cross-harness packaging, command entry points.[7] | It is still a skill/workflow packaging layer, so it is less helpful as the core execution design than the three repos above.[7] |

## How to implement it without workflows

The cleanest non-workflow design is to make deep research a **plain callable module or service** with explicit phases and a stable artifact contract. That means Claude Code or Codex would just call your research tool the same way they would call a test runner or linter, instead of relying on harness-native orchestration.[2][4][1]

A minimal architecture would be:

- `research/runner.ts` or `runner.py`: main entry point.[4][2]
- `research/adapters/`: search adapters like MMX, MCP web search, local history, maybe one advisory lane.[3][2]
- `research/schema/research-run.v1.json`: the artifact contract your notes already describe.[2]
- `research/verify.ts`: claim classification, opened-vs-discovered distinction, falsifier checks.[2]
- `research/report.ts`: concise synthesis plus source pointers.[4][2]

The execution loop should be boring and deterministic:

1. Intake question and requested decision.  
2. Generate a small aspect map or subquery set.  
3. Run one discovery lane first.  
4. Open only the most promising sources.  
5. Extract candidate claims.  
6. Run disconfirmation only if risk triggers fire.  
7. Assign claim statuses.  
8. Write `research-run.v1`.  
9. Return compact synthesis.[2]

That is basically the spirit of `dzhng/deep-research`, but with your stricter evidence model layered on top.[4][2]

## Best reference pattern

If I were thought-partnering with you on implementation order, I would treat the three repos like this:

### 1. Copy the control loop from `dzhng/deep-research`

This repo is the best example of the **smallest understandable deep-research engine**. It takes a query, asks follow-up questions, generates multiple search queries, processes results, recursively explores deeper, and writes a Markdown report; it also exposes explicit breadth, depth, and concurrency settings.[4]

That maps cleanly to your environment because you prefer narrow, inspectable machinery over grand orchestration. The missing piece is epistemics: you would add lane roles, source-opening state, claim status, and authorization limits.[2][4]

### 2. Copy the evaluation posture from `open_deep_research`

This repo matters less for its framework choice and more for its **evaluation discipline**. It supports multiple LLM roles, multiple search tools, MCP/native search, and publishes benchmark/evaluation machinery tied to Deep Research Bench, including cost and token comparisons across configurations.[2]

That is useful for your system because one of your core risks is building something that feels sophisticated but increases cost and review burden without improving decisions. The lesson to copy is: treat evals as a first-class part of the repo, not a future nice-to-have.[2]

### 3. Copy the source-layer separation from `local-deep-research`

This repo shows how a serious search system separates **strategies**, **sources**, and **deployment modes**. It supports multiple research modes, many search engines, local documents, a knowledge base, a REST API, benchmarking, and a “langgraph-agent” strategy while keeping the search-engine layer explicit.[3]

For you, the important takeaway is not “build an app that big.” It is that source types should remain explicit: academic, general web, technical, local docs, history, GitHub, and so on should not all be blurred into one generic search result pool.[3][2]

## What I would actually build

I would implement deep research as a **repo-local research command**, not a workflow:

- `research run --query "..." --mode decision-bearing`
- `research verify <run-id>`
- `research summarize <run-id>`

Internally, that command can still be invoked from Claude Code, Codex, a script, or a CI job, but the logic lives in your repo and emits your artifact contract. That keeps the authority in your codebase instead of in harness behavior, which is safer for a multi-harness environment.[2]

A first TypeScript shape could be:

```ts
type LaneRole = "context" | "discovery" | "verification" | "advisory_disconfirmation";

type ClaimStatus = "verified" | "supported" | "contradicted" | "unverified";

interface ResearchRun {
  schema_version: "research-run.v1";
  run_id: string;
  question: string;
  requested_decision?: string;
  authorization_sought: "investigate" | "recommend" | "implement" | "pilot" | "production";
  lanes: ResearchLane[];
  claims: Claim[];
  stop_reason: string;
  authorization_supported: "none" | "investigate" | "recommend" | "implement" | "pilot" | "production";
}
```

And the core API:

```ts
async function runDeepResearch(input: {
  question: string;
  requestedDecision?: string;
  mode: "lightweight" | "decision-bearing";
}): Promise<ResearchRun>
```

This is deliberately closer to `dzhng/deep-research` than to a workflow engine.[4]

## What else to consider

A few things are easy to miss if you stop at “iterative search + report.”

- **Discovery vs verification**: most example repos are strong at iterative search and synthesis, but weaker at explicitly proving which sources were actually opened and which claims are truly verified.[3][4][2]
- **Negative evidence**: your system should record “looked for falsifier and found none” or “looked for primary proof and could not find it,” because that is often decision-relevant in architecture work.[2]
- **Authority limits**: a research artifact should state what action it authorizes; otherwise downstream agents can overread a nice-looking report.[2]
- **Cost controls**: explicit caps on depth, breadth, opened sources, and advisory lanes matter as much as search quality, especially given the token-burn problems you’ve already seen in agentic research modes.[4][2]
- **Search engine diversity**: if you care about omission detection, you may want one discovery lane with strong general recall and one lane with stronger primary-source or repository bias, instead of just “more searches.”[3][2]
- **Workspace integration**: one of your biggest likely advantages is not broader web search but combining local context, past decisions, repo state, and live web evidence in one contract; `local-deep-research` points in this direction with local docs and history.[3]

My view: the best next move is to **clone the shape of `dzhng/deep-research`, borrow the eval discipline of `open_deep_research`, and borrow the source-layer separation of `local-deep-research`**. Then add your own evidence contract and disconfirmation rules, because that is the part the example repos generally do not implement well enough for your standards.[3][4][2]

Would you like a concrete proposal next for a minimal `research/` repo structure in TypeScript, with 6–10 files and responsibilities?
