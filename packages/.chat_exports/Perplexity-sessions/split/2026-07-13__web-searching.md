---
title: "Web searching"
date: "2026-07-13"
mode: "COPILOT"
uuid: "de568147-ff62-4b51-89df-8b2ccb248c53"
entry_count: 2
---

## Human

Please review this conversation.  How would you improve the web searching solution?

## Assistant

Yes: the web-searching solution should be improved, mainly by turning it from a good **policy block** into an executable, capability-aware routing system with clearer lane selection, runtime verification, and evidence normalization. The current conversation shows strong instincts—parallel retrieval, authority ordering, explicit uncertainty, and local knowledge first—but it still relies too much on prose rules and ad hoc operator judgment instead of a deterministic search planner.[1][2]

## Main gaps

The current design is strong on principles but weaker on enforcement: it defines source authority, MMX usage rules, quota cautions, and provider selection guidance, yet most of that remains declarative text in AGENTS.md rather than a runtime mechanism that can actually detect capabilities, pick lanes, verify readiness, and standardize outputs.  That means different harnesses or agents can still interpret the same policy differently, skip preflights, over-search, misclassify a lane as active just because config exists, or fail to preserve lane-separated evidence cleanly.[2][1]

A second gap is that “web search” is currently treated as one decision, when the conversation itself shows at least five distinct retrieval modes: local wiki/QMD for workspace truth, NotebookLM for deep source-grounded research, MMX for broad independent recall, harness-native search for current grounded retrieval, and specialty providers like Exa/Tavily/Brave for semantic, extraction, or independent coverage.  Those are not interchangeable, so the system should classify the research task first and only then choose one or more lanes.[1][2]

## Better architecture

I would replace the current mostly textual policy with a three-layer search architecture: **planner**, provider registry, and evidence normalizer. The planner decides what kind of question this is; the registry says which lanes are actually available now; the normalizer forces all lanes to emit the same result schema so synthesis becomes deterministic instead of handcrafted.[2][1]

The planner should classify each request into a small number of task types such as:
- Workspace-history question.
- Current factual lookup.
- Technical verification.
- Deep research / source collection.
- Contested or omission-sensitive research.[1][2]

Then map those to lane bundles, for example:
- Workspace-history → QMD first, external only if needed.[2]
- Current factual lookup → harness-native search or MMX.[2]
- Technical verification → MMX plus official docs / repo verification, optionally Exa.[2]
- Deep research → NotebookLM plus MMX for independent recall.[2]
- Contested/high-stakes → at least two independent external lanes plus local context when relevant.[2]

That is a materially better model than “use the best verified capability” alone, because it turns vague preference into routing logic.[2]

## Provider routing

The provider selection logic should be adaptive, but not soft or hand-wavy. The conversation already moved in the right direction by rejecting dollar price as the primary ranking and instead prioritizing source fit, quota availability, freshness, independence, evidence quality, and failure behavior.  The next step is to make that a scored registry with live preflight checks rather than a descriptive table.[2]

Each provider should have machine-readable fields like:
- `capabilities`: broad_search, semantic_search, extraction, local_knowledge, source_grounding, browser_open.
- `freshness_mode`: live, indexed, notebook-bound, local-only.
- `independence_group`: MMX, OpenAI-native, Google-grounded, local-wiki, notebooklm, etc.
- `quota_state`: healthy, degraded, exhausted, unknown.
- `readiness_state`: active, configured-only, unauthenticated, broken.
- `evidence_strength`: URLs only, extracted content, citations, notebook-grounded, workspace-local.[1][2]

That would solve a recurring failure mode shown in the conversation: several times a provider looked available from config, but later inspection showed it was not actually active or authenticated.  The policy already warns not to infer activation from presence, so the improvement is to encode that warning into provider admission rules: no lane is eligible until it passes a preflight suitable to that lane.[1][2]

## Enforcement upgrades

The biggest practical improvement is to stop relying on AGENTS text alone and add wrappers or subcommands that force correct behavior. The conversation itself suggested this earlier for MMX, including a canonical research skill, wrapper, and tests.  I would expand that into a small search orchestration layer:[1]

1. `search plan <task>` classifies the task and proposes lanes.
2. `search preflight` checks readiness, auth, quota, and live invocation safety.
3. `search run` executes one or more lanes with lane-separated logs.
4. `search synthesize` merges normalized results into a decision packet.[1][2]

For MMX specifically, the current rule “run `mmx --help`, then `mmx search query --help`, then use only `mmx search query --q ... --output json --quiet`” is good as a safety contract, but it is too low-level for repeated real use.  Wrap it so agents cannot drift into snippets-as-evidence, broad repetitive queries, or silent provider switching.[1][2]

I would also enforce these hard rules in code:
- Every consequential search must record the lane, query, timestamp, readiness result, and quota snapshot when available.[2]
- Every lane must preserve failures explicitly; one lane’s success cannot mask another lane’s failure.[2]
- Search snippets are never promoted to evidence unless independently opened or verified.[1][2]
- Claims must be tagged as verified fact, inference, or unknown before synthesis.[2]

## Query strategy

The current approach values targeted queries, site filters, and stopping when decision-relevant claims are supported, which is correct.  What is missing is a repeatable query-generation strategy per task type, so agents do not over-search or under-search.[1][2]

I would add a deterministic query policy:
- Generate 2 to 5 atomic queries, never one bloated query.[1][2]
- Start with an official-source query when the claim could be in docs, specs, pricing, policies, or repos.[1][2]
- Add one falsifier query, such as “issue”, “limitations”, “quota”, “auth”, “rate limits”, “deprecated”, depending on domain.[1]
- Add one independent recall query without the official site filter to catch omissions or contradictory sources.[2]

For technical claims, the system should explicitly separate:
- discovery query,
- authority query,
- falsifier query,
- implementation/runtime verification query.[1][2]

That is better than the current mostly narrative guidance because it makes omission detection systematic.

## Local-first search

One of the best corrections in the conversation was recognizing that local wiki and NotebookLM are first-class lanes, not afterthoughts.  I would push that further: the planner should default to QMD before web search whenever the question mentions workspace history, prior decisions, established terminology, or previously investigated tooling, because the local wiki is evidence about the workspace and often the fastest way to avoid redundant web research.[2]

NotebookLM should be treated as a deep-research and source-grounding lane when the task needs source collection, cross-document synthesis, or persistent research context.  The conversation also corrected an earlier mistake by verifying that there are two NotebookLM methods with automated authentication paths, and that the earlier conclusion based on only one CLI was incomplete.  That suggests a concrete improvement: provider preflight must support multiple auth paths per provider rather than assuming one CLI check is authoritative.[1][2]

## Recommended changes

Here is the prioritized improvement list.

| Priority | Change | Why |
|---|---|---|
| Required now | Add a search planner and machine-readable provider registry. [2] | Prevents policy drift and makes lane selection deterministic. [2] |
| Required now | Add runtime preflight for every provider: auth, readiness, quota, safe live invocation. [1][2] | Fixes the “configured but not active” problem seen repeatedly. [1][2] |
| Required now | Normalize all lane outputs into one schema with query, URL, source type, date, evidence class, lane, uncertainty, and failure fields. [1][2] | Makes synthesis reliable and auditable. [1][2] |
| Required before pilot | Implement lane bundles by task type instead of one generic web-search policy. [2] | Better routing, less cost in time/quota, fewer unnecessary searches. [2] |
| Required before pilot | Encode query templates for official, falsifier, and independent-recall searches. [1][2] | Improves omission detection and reduces random search behavior. [1][2] |
| Later opportunity | Add learning/telemetry on which lane combinations most often changed conclusions or caught omissions. [1] | Lets you optimize the planner empirically instead of by intuition. [1] |

## Concrete policy rewrite

I would compress the current long policy into something more operational:

- Classify the question before searching.[2]
- Use QMD first for workspace-history or terminology questions.[2]
- For consequential external research, run at least two independent retrieval lanes when practical, one of which should usually be MMX.[2]
- Treat provider presence as non-evidence; only preflighted lanes count as available.[2]
- Prefer authoritative primary sources, then verify key claims by opening the strongest source or checking runtime/repo evidence.[1][2]
- Preserve lane-separated failures, quota state, and uncertainties until synthesis.[2]
- Stop when authoritative support exists and main falsifiers have been checked; do not keep searching for volume.[1][2]

FACT: the conversation already contains most of these ideas in pieces; the missing improvement is converting them from human-readable doctrine into a routing and validation mechanism.[1][2]

My confidence is high on the architectural recommendation and medium on exact provider scoring, because the provider landscape and auth/readiness state are environment-specific and can change over time.  The most useful next step is to implement a small `search-plan + preflight + run + normalize` wrapper around your existing lanes, starting with QMD, MMX, harness-native search, and NotebookLM.[1][2]

## Human

do you agree with this?  "Verdict
The existing solution has good epistemic rules but too much operational detail in AGENTS.md. The proposed planner–registry–normalizer architecture is directionally right, but it is one abstraction layer too ambitious as the next step.
For a solo director with many disposable AI coders, the optimal design is:
A short governing policy, one thin research runner, one evidence contract, and a small regression corpus.
Not a universal search platform, not a large provider-ranking engine, and not another agent orchestration framework.
The goal is to make good research hard to skip, cheap to invoke, and easy for you to audit, without making every lookup behave like a research project.
1. What the existing solution gets right
The current AGENTS.md correctly establishes several important principles:
Search systems locate evidence; they are not evidence themselves.
Local/runtime truth, official documentation, repositories, specifications, and primary sources outrank summaries and snippets.
Presence in configuration does not prove a provider is active.
Important claims should be opened or independently verified.
Failed retrieval lanes should remain visible rather than being concealed by another lane’s success.
Consequential or omission-sensitive research may merit independent retrieval lanes.
Those rules directly address common AI-coder failures: invented sources, snippet laundering, stale-provider assumptions, unjustified confidence, and false claims that a configured tool was actually exercised.
The broader AGENTS.md also already contains the right conceptual machinery:
presence versus activation;
canonical source versus cache or mirror;
evidence levels;
runtime-path verification;
claim typing;
explicit failure behavior;
protection against concurrent work.
That means you do not need to invent a second governance system for research. Research should reuse those existing concepts.
2. Problems in the existing implementation
A. AGENTS.md is becoming both constitution and operations manual
The web-search section mixes:
Durable principles.
Exact MMX command syntax.
Current MiniMax quota behavior.
Provider pricing.
Installed paths and authentication methods.
Provider-specific routing preferences.
NotebookLM and Perplexity policy.
Multi-agent execution guidance.
These have radically different rates of change.
“Search snippets are not evidence” is durable.
“Exa gives this many credits” and “this CLI currently supports this authentication mode” are volatile.
Putting both in the same governing document creates two risks:
stale operational facts acquire the authority of policy;
agents consume a large instruction surface even when no research is needed.
The conversation itself demonstrates this maintenance burden: duplicate DuckDuckGo rows appeared, the routing wording changed repeatedly, and provider activation had to be corrected after configuration was mistaken for availability.
Better division
AGENTS.md
  Durable policy and activation conditions only

research/SKILL.md
  Research workflow and query strategy

providers.yaml
  Machine-readable provider capabilities and declared costs

runtime preflight
  Current readiness, credentials, version and quota

run artifact
  What actually happened in this research run

B. Running help commands before every research session is ceremony, not safety
The rule requiring:
mmx --help
mmx search query --help

before researching is useful during initial integration or after a CLI upgrade. Repeating it for every research task produces noise and cost without proving that the actual search path works.
A help response proves only that the executable starts and exposes a command. It does not prove:
authentication;
quota availability;
endpoint health;
valid JSON output;
useful results;
source URLs;
browser/open capability.
Use a version-scoped capability check, cached until one of these changes:
executable path;
executable version or hash;
configuration hash;
credential-presence state;
declared provider adapter version.
Then use a tiny harmless live query when runtime readiness matters.
C. The current two-lane rule can cause systematic over-research
The current policy says consequential, freshness-sensitive, contested, or omission-sensitive work should use at least two independent lanes when practical.
That is reasonable, but these categories are broad enough to cover most interesting work. AI agents are likely to interpret them expansively and launch parallel searches by default.
For you, the main cost is not just API spending. It is:
more output to inspect;
longer sessions;
duplicated evidence;
more opportunities for inconsistent conclusions;
more control surfaces for agents to misunderstand.
A previous critique of your larger system identified the same core tension: under-enforcement plus over-analysis. Adding more ceremony fixes only the first problem and can worsen the second.
Better rule
Use a second retrieval lane only when at least one trigger is present:
the decision is difficult or costly to reverse;
the first lane has weak recall or lacks direct-source access;
the claim is contested;
omission would materially change the decision;
the first lane returns conflicting or suspicious evidence;
the user explicitly requests broad research;
the system is evaluating search quality itself.
A second source is often needed. A second search engine often is not.
For example, MMX discovery followed by opening official documentation is two-stage verification, but not necessarily two independent retrieval lanes.
D. The output contract is too verbose for normal use
The policy asks for every result to include query, title, URL, date, relevance, evidence classification, and uncertainty. That is useful for an evidence artifact, but expensive to place in every human-facing answer.
Your desired interface should be:
concise decision-oriented synthesis for you;
complete provenance stored for agents, audits, and later review.
Otherwise you become the deduplication and evidence-normalization layer.
Better behavior
The runner writes a structured artifact such as:
.artifacts/research/<run_id>/research-results.json

The AI response shows only:
conclusion;
strongest supporting sources;
material contradictions;
missing evidence;
confidence;
artifact path when useful.
E. Cost order is not a sound routing strategy
The earlier conversation spent considerable effort ordering providers from least to most expensive. That is not the correct primary routing axis.
The cheapest tool is expensive when it:
misses the decisive source;
returns only snippets;
cannot open results;
duplicates the primary lane;
consumes your attention;
produces a false conclusion that an AI coder implements.
The routing objective should be:
Minimum expected total decision cost, not minimum query price.
A simple decision score is enough:
expected value
= task fit
× probability of decision-relevant evidence
× source authority
× independence value
× runtime reliability
÷ total cost

“Total cost” includes latency, quota, money, synthesis burden, and failure risk.
Do not implement that as a pseudo-precise numerical optimizer initially. Use it as an ordered decision rule.
F. “Web search” is conflated with several different activities
The proposed review correctly notices that the system has multiple lanes: workspace/local retrieval, NotebookLM, broad web discovery, native grounded search, semantic retrieval, and extraction.
But the classification needs one additional separation:
Context retrieval — What have we already decided or stored?
Discovery — Where might relevant evidence exist?
Acquisition/opening — What does the actual source say?
Verification — Does primary evidence support the claim?
Synthesis — What conclusion follows?
Runtime validation — Does the software or mechanism actually behave that way?
Search providers mainly solve steps 2 and sometimes 3. They do not establish steps 4 or 6 by themselves.
That distinction should be central. Otherwise the new planner may select providers intelligently while agents still mistake retrieved claims for verified behavior.
3. Critical review of the proposed architecture
The proposal recommends:
a search planner;
a scored provider registry;
runtime preflight;
evidence normalization;
commands such as search plan, search preflight, search run, and search synthesize.
What is worth adopting
Evidence normalizer
This is the strongest component. Every retrieval lane should produce a common minimum schema.
Runtime preflight
Also necessary. It directly prevents the already-observed “configured means available” mistake.
Task-sensitive routing
Correct in principle. Workspace-history, technical verification, deep source synthesis, and contested research should not use identical workflows.
Lane-separated failures
Essential. One successful provider must not erase evidence that another provider failed.
What is overbuilt or underspecified
A. A standalone planner risks becoming another fallible agent
A planner that classifies the research task may:
overclassify routine questions as consequential;
launch unnecessary lanes;
select tools based on stale capability descriptions;
produce elaborate plans instead of research;
become another prompt and model behavior you must debug.
Most routing can initially be handled with five deterministic predicates, not a planner model.
For example:
mentions local project/history?       → local retrieval first
requires current external facts?      → live external retrieval
technical implementation claim?       → primary docs/repo + runtime where possible
high-impact/contested/low-confidence?  → independent second lane
large fixed source set?                → NotebookLM or corpus workflow

Use an LLM planner only for ambiguous, broad research decomposition—not every query.
B. A scored provider registry can create false precision
Fields such as evidence_strength, freshness_mode, and quota_state are useful. A single aggregate score is dangerous.
Provider suitability is query-dependent:
Exa might be excellent for semantic discovery but poor for a specific current pricing fact.
Brave might find the official page immediately.
Native search might retrieve and open content in one operation.
MMX might provide complementary recall.
NotebookLM may be strongest only after a relevant corpus has already been populated.
Use hard eligibility filters followed by simple ordered preferences, not a universal score.
C. The proposal does not fully define the authority path
It says the registry tells the planner what is available, but several questions remain:
Who writes the registry?
Are provider capabilities declared manually or discovered?
Which fields are static and which are runtime observations?
How long is a successful preflight valid?
Can one terminal reuse another terminal’s readiness result?
Where are credentials resolved?
What happens when the registry says healthy but a call fails?
Which artifact authorizes a later agent to claim a lane was exercised?
How is a native harness capability represented when there is no callable CLI wrapper?
Without those answers, the registry risks becoming another presence artifact rather than runtime authority.
D. Universal orchestration across harnesses may be impossible or counterproductive
Codex, Claude Code, Gemini tooling, ChatGPT, PI, and OpenCode do not expose identical native retrieval surfaces. Some native tools can only be called by the model inside that harness. A local Python runner cannot necessarily invoke or inspect them uniformly.
Therefore, do not require every lane to be owned by one executable.
Use two adapter categories:
Executable adapters
  MMX, Brave API, Tavily, Exa, local QMD, NotebookLM CLI

Harness-native adapters
  Declared and executed by the current host model/tool environment

Both emit the same evidence artifact, but they need not share the same invocation mechanism.
4. The better design
Layer 1: Short policy in AGENTS.md
Keep roughly 25–40 lines containing only invariants:
classify retrieval need before searching;
distinguish discovery from evidence verification;
prefer primary and runtime evidence;
do not infer activation from configuration;
use one adequate lane by default;
add an independent lane when explicit risk triggers apply;
preserve failures and uncertainty;
stop when the decision is supported and main falsifiers are checked;
do not expose credentials;
use the canonical research skill for consequential work.
Remove pricing tables, detailed provider descriptions, exact installed paths, and frequently changing quota claims.
Layer 2: Canonical research skill
The skill should define:
task categories;
query decomposition;
second-lane triggers;
source-opening requirements;
falsifier checks;
stopping rules;
output and evidence schema;
fallback behavior.
This is where the current MMX command constraints belong.
A key instruction should be:
Do not run more retrieval lanes merely because they are available. Every additional lane must have a stated information gain: improved recall, independence, source access, extraction, freshness, or falsification.
Layer 3: Thin runner and adapters
Start with a small Python or PowerShell implementation—not LangGraph, CrewAI, or a general agent framework.
Suggested path:
research/
  providers.yaml
  research.py
  adapters/
    mmx.py
    qmd.py
    notebooklm.py
  schemas/
    research-run.v1.json
  tests/

Initial commands could be only:
research capabilities
research run --provider mmx --query "..."
research verify <run_id>

Do not build separate plan and synthesize commands until real usage proves they are needed.
5. Minimal artifact contract
{
  "schema": "research-run.v1",
  "run_id": "uuid",
  "created_at": "ISO-8601",
  "task": {
    "question": "string",
    "category": "lookup|technical_verification|deep_research|contested|local_context",
    "risk": "low|medium|high",
    "second_lane_reason": null
  },
  "lanes": [
    {
      "lane_id": "mmx",
      "adapter_version": "string",
      "independence_group": "minimax",
      "preflight": {
        "status": "ready|degraded|unavailable|unknown",
        "checked_at": "ISO-8601",
        "valid_until": "ISO-8601"
      },
      "queries": [],
      "results": [],
      "failure": null
    }
  ],
  "claims": [
    {
      "claim": "string",
      "status": "verified|supported|contradicted|unverified",
      "source_ids": [],
      "verification_method": "opened_primary|repository|runtime|secondary_only",
      "falsifier_checked": true
    }
  ],
  "stop_reason": "authoritative_support_and_falsifiers_checked",
  "limitations": []
}

Important: the artifact should record opened-source evidence separately from search-result evidence.
6. Failure policy
Use risk-sensitive degradation rather than one global “fail open” or “fail closed” rule.
SituationBehavior
Low-risk lookup, preferred lane unavailable
Use another preauthorized zero/low-cost lane and disclose substitution
Technical recommendation, one lane unavailable
Continue with primary-source verification when sufficient; downgrade omission confidence
Contested or omission-sensitive decision requiring independence
Do not claim triangulation if the second lane fails
High-impact decision lacking primary evidence
Stop at a partial or blocked verdict
Provider returns snippets but source cannot be opened
Treat as discovery only
Quota state unknown
Permit a bounded call only if cost policy allows; otherwise mark unavailable
Native lane unavailable to current harness
Do not simulate it with another provider while retaining the native lane label
This is more useful than requiring explicit user authorization for every fallback. You can preauthorize bounded free/included-cost substitutions while still requiring approval for paid or high-volume escalation.
7. The missing component: evaluation
The proposal mentions telemetry, but it should be elevated from “later opportunity” to required before claiming the router is better.
Without an evaluation corpus, a planner or registry merely looks sophisticated.
Build 20–40 representative cases from your real work:
current product capability;
obscure technical documentation;
GitHub implementation discovery;
negative evidence or limitations;
workspace-history question;
contested claim;
provider outage;
empty MMX result;
official source that contradicts search snippets;
a query where a second lane catches a meaningful omission.
Measure:
decisive-source recall;
unsupported-claim rate;
primary-source rate;
false “provider active” claims;
unnecessary second-lane rate;
time to usable conclusion;
query count;
human review burden;
percentage of second lanes that materially change the answer;
quota/cost consumed.
The system is improved only when it produces better decisions or meaningfully reduces your workload—not when it emits more complete research logs.
This matches the broader principle already present in your ecosystem: improvements should be judged through measured outcomes and durable regression cases, not agents describing themselves as improved.
8. Priority order
Required now
Shrink the AGENTS.md section to durable principles.
Move operational MMX/provider details into a research skill.
Create research-run.v1 with lane-separated results and opened-source verification.
Implement MMX as the first real adapter.
Define deterministic second-lane triggers and stop conditions.
Required before an adaptive pilot
Add live readiness checks with bounded freshness.
Add one harness-native lane contract.
Add QMD/local retrieval as a separate context lane.
Build the initial real-world evaluation corpus.
Test degraded and failed-provider paths.
Later, only if evidence justifies it
Add more provider adapters.
Learn routing preferences from measured outcomes.
Introduce a planning model for genuinely broad research.
Add graph orchestration only when retries, resumability, or parallel state become difficult in simple code.
Recommended decision
Do not implement the full proposed planner–registry–normalizer platform yet.
Implement this narrower vertical slice:
Question
  ↓
deterministic research classification
  ↓
MMX or local/native lane
  ↓
source opening and verification
  ↓
research-run.v1 artifact
  ↓
compact synthesis
  ↓
evaluation against real cases

This preserves nearly all of the proposal’s value while avoiding a new orchestration subsystem that your AI coders can expand faster than you can mentally govern.
The design succeeds when you can ask an AI coder to investigate something and receive:
the correct conclusion;
the decisive evidence;
explicit missing evidence;
no silent provider substitution;
a reproducible artifact;
and no unnecessary research ceremony for you to supervise."

## Assistant

Yes — I agree with it **substantially**, and I think it is better than my earlier recommendation as a next-step implementation plan. It keeps the core epistemic strengths while cutting back to a smaller, more governable system: short policy, thin runner, one evidence artifact, deterministic triggers, and a regression corpus. That is much more compatible with the existing AGENTS discipline and with the fact that your workspace already treats wrappers, registries, adapters, orchestration, and shared state as boundary-affecting work that needs heavier review rather than casual expansion.[1]

## Where I agree

The strongest part of the critique is that AGENTS.md already contains the right governing concepts — evidence levels, presence-versus-activation, runtime-path verification, claim typing, and explicit failure behavior — so research should reuse that governance instead of creating a second conceptual system.  I agree that the next step should be a thin operational layer built under that policy, not a new universal “search platform.”[1]

I also agree that the proposed planner–registry–normalizer architecture is directionally right but too ambitious as the immediate next increment. Your own material already shows that even the current web-search section became operationally heavy and needed repeated correction for duplicate rows, stale path assumptions, provider activation mistakes, and incomplete NotebookLM investigation.  Given that history, adding a planner, scored registry, and multiple orchestration commands too early would likely create another fallible control layer before the simple path is hardened.[2][1]

## What I would keep

I would still keep four elements from the earlier architecture, but in reduced form:
- Evidence normalization.
- Runtime preflight.
- Task-sensitive routing.
- Lane-separated failure recording.[2][1]

Those are already justified by the observed failure modes in the conversation: config was mistaken for runtime availability, one NotebookLM path was checked while another authenticated path existed, stale wiki path guidance persisted until traced to the real QMD configuration, and the policy kept expanding with volatile operational facts.  So I would not abandon those ideas; I would just implement them as a thin runner and artifact schema instead of as a generalized planner platform.[1][2]

## Where I would refine the critique

I agree with the statement that “a second source is often needed; a second search engine often is not,” with one refinement: sometimes two independent retrieval lanes are still the right default for consequential external research, but only when the second lane has a clear information-gain role such as independent recall, omission detection, different indexing, or better source-opening ability.  That matches the later policy shift in the conversation, where MMX stopped being treated as mere fallback and became an intentional independent lane for omission-sensitive work.[2][1]

I also agree that cost-ordering is the wrong routing axis for your situation because your practical constraint is not marginal dollars but quota, reliability, evidence quality, freshness, and review burden. That conclusion is explicitly supported by the later AGENTS guidance, which says not to rank tools by dollar price and instead rank them by source fit, quota availability, freshness, independence, evidence quality, and failure behavior.[1]

## Best next step

If I were revising my recommendation, I would now say: do **not** build `search plan`, `search preflight`, `search run`, and `search synthesize` as separate user-facing subsystems yet. Instead, implement one canonical research runner with:
- Deterministic classification.
- A small adapter interface.
- A cached readiness/preflight check.
- A single `research-run.v1` artifact.
- Compact synthesis rules.
- A regression corpus.[1]

That narrower design fits your existing governance better because AGENTS already demands explicit authority paths, runtime verification, and evidence-bearing artifacts when a mechanism could later authorize implementation or operational claims.  A thin runner plus artifact is also easier to audit, easier to regression-test, and less likely to become another agentic abstraction layer that your disposable coders elaborate faster than you want to supervise.[1]

## My actual verdict

So: **yes, mostly**. I think the critique is stronger than my previous answer on sequencing, implementation scope, and operator burden, and I would adopt its recommendation as the better next move.  The only thing I would preserve from my earlier answer is the idea that normalization, preflight, and task-sensitive routing are still the right long-term primitives — but they should first appear inside one thin research runner and one evidence contract, not as a broad planner–registry–normalizer platform.[2][1]

My confidence is high on that conclusion because it aligns with both the observed maintenance problems in the conversation and the workspace’s own review doctrine for boundary-affecting systems.  The concrete next action I would endorse is: shrink AGENTS.md to durable search invariants, move volatile operational detail into a research skill, implement one MMX-first runner with opened-source verification and lane-separated artifacts, then test it against a real evaluation corpus before adding more adapters or planning logic.[2][1]
