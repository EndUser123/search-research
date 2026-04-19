<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# "Mistakes I made:

Assumed skill-scoped hooks needed settings.json registration - I didn't know how skill-based hooks work. They're defined in SKILL.md frontmatter and auto-activate when the skill loads. I should have looked this up first instead of assuming.
Claimed daemon latency was 50-200ms without evidence - I speculated. You called me out. The actual DaemonClient timeout is 2.0s but typical response is much faster since the daemon is already running.
Assumed you're a solo dev - You corrected me - you have AI assistants. I shouldn't have made assumptions about your setup.
Didn't verify the receiving LLM's claims - When they said "PreToolUse blocking would break investigation", I initially accepted it without thinking through that the design was about blocking completion without engine execution, not blocking investigation commands.
Created a solution document (v3.2) that drifted from what was actually implemented - The doc said modify skill_enforcement_gate.py, but implementation created a separate file. Then I didn't notice it wasn't registered.
Repeatedly asked "should I do X?" instead of just checking - Multiple times I could have verified state myself instead of asking permission to look things up."

This is what the LLM in Claude code told me.  What are repos or other people doing to prevent this?  XML stuff like we did before?  Others?  I'm also concerned about missing related topics or hooks.

At a high level, the failures in that list are all variants of the same thing: the model improvised where it should have queried a source of truth (repo, runtime, docs, hooks registry) and it treated its own narrative as reality.

Mature setups attack that with a mix of **structure, contracts, and automated verification**, not just better prompting. Concretely:

***

## 1. Structured “contracts” instead of free‑form reasoning (XML/RAIL, JSON schemas, Pydantic)

The “XML stuff” you used before is exactly what a lot of people are doing in more polished form:

- Libraries like Guardrails/RAIL define a **schema + validators** that the model must satisfy, and will automatically re‑ask or reject outputs that don’t conform.[^1_1]
- Typical pattern:
    - Define a JSON or XML schema for what the model is allowed to assert (e.g., `environment_facts`, `latency_claims`, `hook_registration_changes`, `verification_status`).
    - Attach **validators** that:
        - Disallow numeric claims unless tagged `source: "code_search" | "config_file" | "runtime_query"`.
        - Require `verified: true` for anything used to drive a change.
    - Wire this into your agent loop so any non‑conforming response triggers an automatic “try again with stricter instructions” before you ever see it.

For your specific failure modes, you can get very targeted:

- Require a field like:

```json
{
  "claim": "Daemon latency is 50–200ms",
  "verified": false,
  "verification_method": null,
  "evidence_location": null
}
```

and have a validator that **rejects any plan that uses unverified claims** as justification for a code change.
- Similar for “PreToolUse blocking investigation” – the schema can force the model to:
    - Enumerate all affected hooks and files.
    - List which ones it **actually opened** vs inferred.

Guardrails-style specs make this language‑agnostic and work with many models; they’re already widely used to enforce response formats \& policies rather than relying on the model’s self‑discipline.[^1_1]

***

## 2. Source‑of‑truth files that the model must consult (vs “guessing from vibes”)

The biggest pattern in strong repos: they **centralize truth into a few queryable artifacts** and then make the agent use tools to read those artifacts instead of speculating.

Examples you can apply immediately:

### a. Project contracts / facts files

Add machine‑readable “contracts” in the repo, e.g.:

- `project-facts.yaml`
- `hooks-contract.json`
- `architecture/daemon-contract.md`

These contain things like:

- Daemon timeouts / retry policies.
- Which components are allowed to block what.
- Which files are authoritative for hooks, skills, settings.

Then:

- Add a simple tool or script: `read_project_contract(section: string)`.
- Hard‑code into the workflow: **for any architectural or latency assertion, first call this tool or read that file**; if the fact isn’t present there or in code, the model must say “unknown”, not guess.

This is essentially moving from “remember this in my system prompt” to “store it as code and make the agent query it”.

### b. Central hook \& skill registries

A lot of teams avoid situations like “doc says modify X, code created Y and never registered it” by maintaining a **single registry**:

- `hooks/index.json` or `hooks_registry.py`
- `skills/skills-index.json` or `skills/manifest.yaml`

The rule is:

- Every hook/skill must be declared in exactly one manifest file.
- CI has a test: “no hook implementation without registry entry” and “no registry entry that points to a missing file”.

Claude Code itself builds an `<available_skills>` list from `SKILL.md` frontmatter, and newer versions support skill-scoped hooks directly in that frontmatter so they auto‑register when the skill loads. You can mirror that pattern for your custom hook frameworks:[^1_2][^1_3][^1_4]

- Treat the manifest as the **only** place to learn “what hooks exist and are registered”.
- Train your own project‑specific instructions: “Never assume a hook exists; instead, open the hooks manifest and list entries before reasoning.”

This directly targets your “missing related topics or hooks” concern: discovery is manifest‑driven, not guesswork.

***

## 3. Forcing verification steps instead of “assumption narratives”

The mistakes you listed—assuming configs, taking the receiving LLM’s claims at face value, over‑asking instead of checking—are all prevented by **explicit verification workflows**.

Patterns from more mature agent systems:

### a. “Checked vs assumed” fields with a verifier pass

Instead of one monolithic reasoning step, split into:

1. **Planner/analyst step**: model proposes:
    - `assumptions[]`: things it currently believes.
    - `checks[]`: commands or file paths it will inspect.
    - `plan[]`: steps to execute once checks pass.
2. **Verifier/executor step**:
    - Runs `checks[]` via tools (file opens, grep, tests, etc.).
    - Marks each assumption as `verified` or `contradicted`.
    - Rejects any plan that still depends on unverified assumptions.

You can enforce this structurally with the schemas in section 1 so that:

- Any assumption that could be resolved by repo inspection **must** go through a tool call.
- If not, the verifier fails the response.

This would have forced the model to actually inspect:

- `DaemonClient` timeout in code instead of inventing “50–200 ms”.
- Hook registration files instead of assuming “settings.json” for skill‑scoped hooks.


### b. Pre‑execution validation hooks

For code‑changing agents, teams add a **policy/validation layer** that checks any proposed change against rules before the agent can apply it:

- For example:
    - “No new hooks file unless you also update `hooks/index.json`.”
    - “No change to enforcement gate behavior without updating `GATE-CONTRACT.md` and related tests.”
- Some research frameworks even formalize this as a verified policy that intercepts agent actions and checks them against predefined contracts before they run.[^1_5]

You don’t need full formal verification to get value—basic static checks plus tests go a long way.

***

## 4. Reducing doc drift between “solution doc” and implementation

The “v3.2 doc drifted from what was implemented” failure is super common, and there are emerging patterns/ tools specifically for this.

### a. Docs‑as‑code + PR discipline

Mature teams treat design docs like code:

- Doc lives next to the relevant code.
- **Any change to behavior must update the doc in the same PR**.
- CI checks that:
    - If key files change (e.g., enforcement gate, hooks registry), corresponding docs under `docs/` or `architecture/` changed too.
    - Or, they at least require a “no-docs-change-needed” annotation that a human reviewer can question.

This is increasingly paired with docs‑as‑code and static site generators, where all docs are versioned and linked to releases.[^1_6]

### b. Automated doc‑drift detection

There are tools and services now that run in CI/CD to detect “documentation drift”:

- They scan commits, compare code semantics against nearby docs, and propose doc edits via PRs when they detect inconsistencies.[^1_7]
- At a minimum, you can build a lighter‑weight version:
    - On every PR, run an agent that:
        - Reads the changed files.
        - Reads nearby docs and solution specs.
        - Flags anything that looks stale (“doc mentions settings.json but code uses SKILL.md hooks”).
        - Opens a comment or suggested commit with fixes.

The important part is that **doc verification is automated and tied to change events**, not something the conversational model might or might not remember.

***

## 5. Discovery of related topics, skills, and hooks

Your concern about “missing related topics or hooks” is basically a **retrieval / context‑drift** problem.

Patterns that help:

### a. Central skill \& hook metadata with tags

Instead of relying on the assistant to remember relationships:

- Give each skill and hook metadata:
    - `tags: ["enforcement", "hooks", "latency"]`
    - `related_skills: ["skill_enforcement_gate", "repo_state_validator"]`
- Store that in frontmatter or manifests, similar to how Claude Code uses YAML frontmatter in `SKILL.md` to build an `available_skills` list with names and descriptions.[^1_3][^1_2]

Then:

- Add a “discovery” tool: `list_related_skills(topic_or_skill_name)` that:
    - Searches tags.
    - Returns candidates to inject into context.

Make your orchestration layer do this automatically for certain work types:

- If the task touches “hooks”, automatically:
    - Load the “hooks overview” skill.
    - Fetch all skills with `tags` containing `"hooks"` and surface them as options.

That ensures the model doesn’t quietly operate in a narrow slice when related guardrails exist.

### b. Central task spec and role‑scoped context

In multi‑agent setups, a strong pattern is a **central task spec** plus scoped roles, so each agent (coder, tester, doc‑updater, gatekeeper) works from the same source but with focused context.[^1_8]

Quick win for you:

- Create a `TASK.md` per big initiative that defines:
    - Objectives and constraints.
    - Relevant skills/hooks that **must** be considered.
- In your orchestrator, when a session is about “hook enforcement”:
    - Auto‑inject `TASK.md`.
    - Auto‑inject the hooks manifest and related skills.

This reduces the chance of the assistant “forgetting” some hook exists simply because it wasn’t retrieved.

***

## 6. Reducing “asking should I do X?” and increasing repo/tool introspection

The pattern here is moving from **conversational politeness** to **instrumented autonomy with clear limits**:

- Give the agent:
    - A well‑scoped set of tools: open file, search repo, run tests, read manifests, etc.
    - Clear rules:
        - “You do not need permission to inspect code, configs, manifests, or docs.”
        - “You **must** inspect before proposing behavioral changes.”
- If you want a human gate, put it **after** the verification phase:
    - Agent does all checking and prepares a structured report.
    - Human approves/rejects final action, not each observation.

This aligns with the GitOps/devops pattern where humans approve diffs, not every `kubectl get` along the way.

***

## How you could wire this into your current Claude Code setup

Given your context (hooks, skills, multi‑agent workflows), a pragmatic combination that would immediately cut down on these failure modes:

1. **Add a hooks + skills manifest**
    - `skills/manifest.yaml` with per‑skill `tags`, `hooks`, and registration location.
    - CI test to sync manifest ↔ filesystem.
2. **Add a `project-contract.yaml`**
    - Daemon timeouts, blocking rules, “what PreToolUse may/may not block”, etc.
    - Agent must consult this for any architectural or latency claim.
3. **Introduce a Guardrails/RAIL‑style contract for plans**
    - Fields: `assumptions`, `checks`, `verified_claims`, `unverified_claims`.
    - Validator: plans that depend on `unverified_claims` get rejected and re‑asked.
4. **Create a simple “doc drift checker” agent in CI**
    - On PRs that touch hooks/enforcement/daemon:
        - Compare docs/solution spec vs code changes.
        - Comment if they diverge, or push suggested doc edits.
5. **Skill/hook discovery tool**
    - `list_related_hooks(topic)` using your manifest.
    - Auto‑invoke it whenever the natural language task includes “hook”, “enforcement”, “skill”, etc.

This set of patterns makes it structurally hard for the assistant to:

- Invent latency numbers.
- Assume hook locations.
- Drift solution docs away from implementation.
- Miss related hooks/skills that should be in play.

If you want, the next step could be to sketch a concrete `manifest.yaml` + a Guardrails/RAIL spec tailored to your repo so this becomes something you can drop into your current Claude Code setup rather than just a set of abstract ideas.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.guardrailsai.com/blog/guardrails-litellm-validate-llm-output

[^1_2]: https://mikhail.io/2025/10/claude-code-skills/

[^1_3]: https://alexop.dev/posts/understanding-claude-code-full-stack/

[^1_4]: https://github.com/anthropics/claude-code/issues/17688

[^1_5]: https://arxiv.org/html/2510.05156v1

[^1_6]: https://www.reddit.com/r/technicalwriting/comments/1pnovna/how_do_mature_security_orgs_structure_docsascode/

[^1_7]: https://deepdocs.dev/automated-documentation-tools/

[^1_8]: https://lumenalta.com/insights/8-tactics-to-reduce-context-drift-with-parallel-ai-agents

[^1_9]: https://www.datacamp.com/blog/llm-guardrails

[^1_10]: https://www.reddit.com/r/devops/comments/1o78ki5/llm_agents_for_infrastructure_management_are/

[^1_11]: https://blog.mozilla.ai/can-open-source-guardrails-really-protect-ai-agents/

[^1_12]: https://www.datadoghq.com/blog/llm-guardrails-best-practices/

[^1_13]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^1_14]: https://www.agno.com/blog/guardrails-for-ai-agents

[^1_15]: https://github.com/FareedKhan-dev/agentic-guardrails


---

# You misunderstand.  I'm concerned about missing predictable failure modes based on the symptoms I shared with you.  The errors i showed likely fall into known domains, and there solutions for the entire domain, rather than targeted point solutions.

You’re right that those mistakes are not “one‑off bugs.” They’re instances of a few **well‑studied failure domains** in agentic LLM systems. Other people aren’t just patching each symptom; they’re building abstractions around these domains and then enforcing them systematically.

Below is a mapping from your symptoms → known failure domains → the kind of “whole‑domain” solutions people use.

***

## 1. Premature action without grounding (schema / environment hallucination)

**Your symptoms**

- Assumed skill‑scoped hooks needed `settings.json` registration instead of checking how `SKILL.md` frontmatter works.
- Didn’t inspect actual hook registration / SKILL metadata before reasoning about it.
- Asked “should I do X?” instead of just looking at the repo or runtime.

**Domain**

Research on agentic LLMs keeps finding a recurring archetype: **“premature action without grounding”**—the model guesses schemas, APIs, or environment state instead of inspecting them. In multi‑agent analyses this shows up as a primary class of error, especially around tools and configs.[^2_1][^2_2][^2_3]

**Systemic solutions**

People who treat this as a domain problem do things like:

- **Architectural rule: observe‑before‑act**
    - Force an “inspection phase” before any non‑trivial claim about code/config:
        - e.g., always call a `list_hooks()` or open `SKILL.md` / manifest before talking about hooks.
    - This is essentially baking ReAct‑style “think + observe + act” into the framework, not just the prompt.[^2_4][^2_2]
- **Static protocols for tool/schema access**
    - For every resource type (skills, hooks, daemons, configs), define a canonical “how to inspect me” tool.
    - Disallow plans that reference a resource **before** at least one successful inspection tool call has run.
    - In failure taxonomies this is treated as its own error class (planning/action module using ungrounded assumptions), which then can be detected and corrected by debuggers like AgentDebug.[^2_2]
- **Evaluation traces tagged with this failure mode**
    - Systems that log and label runs will explicitly tag episodes where the agent guessed a schema or file instead of reading it.[^2_5][^2_3]
    - Those traces then become regression tests and training data.

Your “settings.json vs SKILL.md” confusion is a textbook instance of this domain, not something idiosyncratic.

***

## 2. Epistemic errors: unjustified certainty / hallucinated facts

**Your symptoms**

- Claimed daemon latency was 50–200 ms with no evidence.
- Treated guesses as facts instead of marking them as “unknown” or “needs verification.”

**Domain**

This sits in the **hallucination / epistemic uncertainty** bucket: models make confident factual claims without evidence and without surfacing uncertainty. In agent systems, these hallucinations can drive entire plans, so they’re treated as a first‑class failure mode.[^2_6][^2_7][^2_8][^2_2]

**Systemic solutions**

People address this domain with:

- **Uncertainty‑aware generation / abstention policies**
    - Techniques like self‑consistency, entropy‑based uncertainty, epistemic heads, or other calibration methods are used to decide when to abstain or hedge instead of assert.[^2_9][^2_7][^2_8][^2_6]
    - At the orchestration level, you don’t need fancy training: you can require that:
        - Quantitative claims (latency, counts, timeout values) are either:
            - Tied to explicit evidence (file, measurement), or
            - Labeled as “speculation / unknown,” and then blocked from driving code changes.
- **Dedicated “claim extraction + verification” circuits**
    - Extract individual factual claims; run them through a verification pipeline (search, tool calls, or other agents) before accepting them.[^2_10][^2_11][^2_4]
    - Architecturally, this is a separate module that owns “is this claim actually true?”, not something left to the chat model’s whims.
- **Taxonomies \& metrics**
    - Frameworks like AgentErrorTaxonomy carve out a specific class for “incorrect factual assertions / hallucinations in planning” to make them measurable and auditable.[^2_2]
    - Once it’s a tracked error class, you can require “no unverified quantitative claims in plans” as a policy.

Your latency guess is a garden‑variety epistemic failure—solutions for that whole family look like: always separate *producing* a claim from *validating* it, and give validation its own machinery.

***

## 3. Cross‑agent error amplification and unverified delegation

**Your symptoms**

- Accepted another LLM’s statement (“PreToolUse blocking would break investigation”) without cross‑checking against your own design/constraints.
- Treated the receiving LLM’s narrative as ground truth instead of running a verification step.

**Domain**

In multi‑agent systems this is the **error amplification / unverified delegation** problem: one agent’s hallucination becomes another agent’s starting point and gets reinforced across the system.[^2_12][^2_1][^2_2]

**Systemic solutions**

Practitioners don’t just “ask models to be more careful”; they introduce architecture around claims:

- **Dedicated claim‑verification agents or layers**
    - Multi‑agent claim verification pipelines separate:
        - Agent(s) that *propose* claims.
        - Agent(s) that *verify* claims against evidence / tools.
        - Agent(s) that *decide* based on verified claims only.[^2_11][^2_4][^2_10]
    - Verification agents have different prompts and often fewer powers (e.g., they can read but not act).
- **Inter‑agent contracts**
    - Clear contracts: “Any assertion about system behavior (e.g., what PreToolUse blocks) must be tagged with: `source`, `confidence`, `evidence`.”
    - Downstream agents are trained (or coded) to **ignore un‑evidenced claims** by contract.
- **Context lineage / provenance tracking**
    - Systems track where each “fact” in the context came from (which agent/tool) and optionally re‑verify high‑impact ones.[^2_13][^2_5]
    - This is treated as a domain: *context lineage \& contamination*—and mitigated with monitors that can rewind or fork once they see contaminated facts.

Your specific mishap—trusting the other LLM about PreToolUse semantics—is a direct instance of this domain. The “whole‑domain” fix is: treat important cross‑agent claims as untrusted until they clear a dedicated verification path.

***

## 4. Specification / contract / documentation drift

**Your symptoms**

- Solution document v3.2 said “modify `skill_enforcement_gate.py`”.
- Actual implementation created a separate file and didn’t register it.
- You didn’t notice the drift between spec and code.

**Domain**

This is classic **specification and system‑design failure**, which multi‑agent system incident reports identify as a large share of failures: the spec, design docs, and implementation diverge, and no one (human or agent) is systematically checking alignment.[^2_14][^2_2]

In agent taxonomies, this sits in the “system‑level operations” / “specification” bucket.[^2_2]

**Systemic solutions**

Mature setups treat this as its own domain with:

- **Single‑source‑of‑truth contracts**
    - Central specs (schemas, interfaces, policy files) that code and agents must conform to, plus automated checks to prevent drift.
- **Docs‑as‑code + contract testing**
    - Docs and solution specs live in the repo; changes to key components require concurrent changes to those specs.
    - CI enforces that for some paths (“hooks/”, “gate/”), either:
        - Related docs updated, or
        - A human explicitly waives the requirement (which surfaces for review).
    - Some systems layer on automatic “doc vs code” checks and use agents to propose doc updates when drift is detected.[^2_5][^2_2]
- **Design‑execution alignment metrics**
    - In agent debugging work, misalignment between plan/spec and actual executed steps is a measured failure class; frameworks like AgentDebug try to detect and correct those before they cause larger cascades.[^2_2]

Your v3.2 drift is an instance of the general “spec drift” domain. The domain‑level answer is to push design docs into machine‑checked contracts (schemas, manifests, tests) and then systematically check them rather than relying on conversational memory.

***

## 5. Role / collaborator mis‑modeling and system‑design misunderstandings

**Your symptoms**

- Assumed you were a solo dev, not “human + AI assistants”.
- Drew conclusions and made recommendations based on the wrong mental model of the team/system.

**Domain**

This aligns with what multi‑agent failure surveys call **specification \& system design issues** and **inter‑agent misalignment**: misunderstanding who is in the system, what their capabilities are, and how responsibilities are divided. It’s also related to “role drift,” where agents slowly depart from their intended roles.[^2_12][^2_14][^2_13]

**Systemic solutions**

This domain gets attacked with:

- **Explicit system models**
    - A machine‑readable “org chart” / system graph of agents and humans, their capabilities, and boundaries.
    - Agents read this at startup and are not allowed to re‑invent roles.
- **Role‑locked prompts and protocols**
    - Strong role prompts plus protocol checks: messages carry role metadata, and execution traces are monitored for role drift.[^2_13]
    - Some systems use handshake protocols (“what is your role?” “what is mine?”) and periodic re‑assertion to keep roles synchronized.
- **Task specs that include actor topology**
    - Tasks describe not just “what to do,” but “who is in the loop” and “who owns which decisions,” so the agent doesn’t have to infer that.

Your solo‑dev assumption falls squarely in this “system‑design misunderstanding” domain. The fix isn’t ad‑hoc reminders; it’s giving the agent a stable actor topology and enforcing adherence.

***

## 6. Execution‑control failures and weak outer control logic

**Your symptoms**

- Repeatedly asked “should I do X?” instead of using tools.
- Failed to notice unregistered files / hooks even though you *could* have checked.

**Domain**

In agent analyses, this shows up as **fragile execution under load** and **tool‑use failures**: agents either under‑use tools, over‑ask humans, or execute steps without following robust control logic (e.g., not checking invariants after modifications).[^2_3][^2_1][^2_13]

**Systemic solutions**

Whole‑domain mitigations are about wrapping the model in a more deterministic shell:

- **Deterministic controllers around stochastic cores**
    - A non‑LLM controller decides:
        - When tools must be invoked.
        - Which invariants must be checked before and after actions.
        - When a human must be consulted.
    - The LLM supplies content (edits, explanations), but the controller enforces process.
- **Execution tracing and regression harnesses**
    - Persistent logging with correlation IDs, replay, and regression tests over entire agent traces is now a standard recommendation to surface and prevent repeat execution errors.[^2_5][^2_13]
- **Rule‑based “must‑check” policies**
    - For domains like hooks and enforcement:
        - “After you create a new hook file, you must verify registration exists in the manifest or SKILL.md.”
    - Violations are treated as policy breaches, not “oops.”

Your “should I do X?” pattern is a symptom of missing outer control logic: you want a controller that simply says “for this type of task, yes, you *always* do X and then Y; asking the user is not part of the protocol.”

***

## How to use this in practice (without living in patch land)

Given those domains, a practical next move is:

1. **Define your own taxonomy**, borrowing from AgentErrorTaxonomy and multi‑agent failure surveys:
    - E.g.:
        - G1: Grounding/observation failures.
        - E1: Epistemic hallucinations.
        - C1: Cross‑agent error amplification.
        - S1: Spec/contract drift.
        - R1: Role/system mis‑modeling.
        - X1: Execution‑control failures.
    - Tag your existing incidents with these codes.
2. **For each code, define system‑level invariants** rather than point fixes:
    - G1 → “Agents must inspect manifests before reasoning about hooks.”
    - E1 → “Quantitative claims require evidence; otherwise they are labeled unknown and cannot drive actions.”
    - C1 → “Claims from other agents must pass a verification pipeline before updating shared state.”
    - S1 → “Any hooks/enforcement change must be accompanied by contract/doc updates and pass doc‑drift checks.”
    - R1 → “Actor topology is stored in a system manifest and loaded on session start; role drift is monitored.”
    - X1 → “Controllers enforce mandatory tool checks and post‑condition tests; asking the user is not a substitute.”
3. **Implement enforcement in the orchestration layer**, not just prompts:
    - Schema/RAIL/XML contracts are one way of encoding these invariants.
    - Controllers, CI checks, and evaluation harnesses make them executable and testable.

Thinking this way ensures you’re covering the **whole classes** of failures your list belongs to, instead of inventing bespoke fixes for each incident. The mistakes you saw are very much in‑family with what others report; the work is to make those domains explicit in your own stack and then wire in enforcement for each.
<span style="display:none">[^2_15]</span>

<div align="center">⁂</div>

[^2_1]: https://huggingface.co/blog/Musamolla/multi-agent-llm-systems-failure

[^2_2]: https://arxiv.org/abs/2509.25370

[^2_3]: https://arxiv.org/html/2512.07497v1

[^2_4]: https://ceur-ws.org/Vol-3962/paper20.pdf

[^2_5]: https://galileo.ai/blog/agent-failure-modes-guide

[^2_6]: https://arxiv.org/html/2312.15576v1

[^2_7]: https://arxiv.org/html/2602.01956v1

[^2_8]: https://arxiv.org/abs/2312.15576

[^2_9]: https://cs224r.stanford.edu/projects/pdfs/Final_Report_CS224r.pdf

[^2_10]: https://www.sciencedirect.com/science/article/abs/pii/S0957417425037194

[^2_11]: https://www.themoonlight.io/en/review/towards-detecting-llms-hallucination-via-markov-chain-based-multi-agent-debate-framework

[^2_12]: https://arxiv.org/pdf/2503.13657.pdf

[^2_13]: https://galileo.ai/blog/multi-agent-llm-systems-fail

[^2_14]: https://www.hakunamatatatech.com/our-resources/blog/why-do-multi-agent-llm-systems-fail

[^2_15]: https://aispaces.substack.com/p/the-failure-modes-of-agentic-ai-no


---

# local LLM came back with this.  Do you think it's optimal?  I don't care about trn effort.

"  IMPROVE_SYSTEM Analysis

Step 1: Current State Analysis

Existing architecture (from actual code):

- domain_checker.py: Domain-based enable/disable with env var override
- domains.json: 4 domains (safety, git, cognitive, process) with hooks lists
- Hook enforcement via domain_check_exit() pattern
- Priority-based execution (-999 to 300)

Documented pain points (from chat):

- Assumed without verifying (skill hooks, latency numbers)
- Accepted external claims without cross-check
- Doc drifted from implementation
- Asked instead of checked

Step 2: Python-Specific Issues

What your system does WELL (existing patterns):

- Domain-based gating already implemented ✅
- Environment variable override for quick disable ✅
- JSON-based configuration (machine-readable) ✅
- Hook-to-domain mapping is explicit ✅

Gaps identified (from the 6 failure domains):

1. G1 (Grounding): No mandatory inspection phase before claims
2. E1 (Epistemic): No claim verification circuit
3. C1 (Cross-agent): No provenance tracking for external claims
4. S1 (Spec drift): No doc/code parity check
5. R1 (Role modeling): No system topology manifest
6. X1 (Execution control): No mandatory tool-use policies

Step 3: Recommended Improvements

Highest-impact, lowest-effort changes (pragmatic filter):
┌──────────┬─────────────────────────────────────────────────┬────────┬────────┬──────────────────────────┐
│ Priority │                     Change                      │ Effort │ Domain │           Why            │
├──────────┼─────────────────────────────────────────────────┼────────┼────────┼──────────────────────────┤
│ P0       │ Add 2 failure domains to domains.json           │ 5 min  │ G1, E1 │ Extend existing pattern  │
├──────────┼─────────────────────────────────────────────────┼────────┼────────┼──────────────────────────┤
│ P0       │ Create SYSTEM_TOPOLOGY.md manifest              │ 15 min │ R1     │ Single source of truth   │
├──────────┼─────────────────────────────────────────────────┼────────┼────────┼──────────────────────────┤
│ P1       │ Add claim verification hook to cognitive domain │ 30 min │ E1, C1 │ Leverage existing domain │
├──────────┼─────────────────────────────────────────────────┼────────┼────────┼──────────────────────────┤
│ P2       │ Add doc parity check to PostToolUse             │ 45 min │ S1     │ Uses existing hook event │
├──────────┼─────────────────────────────────────────────────┼────────┼────────┼──────────────────────────┤
│ P3       │ Add inspection gate to PreToolUse               │ 60 min │ G1, X1 │ New enforcement point    │
└──────────┴─────────────────────────────────────────────────┴────────┴────────┴──────────────────────────┘
Step 4: Detailed Recommendations

P0: Extend domains.json (5 minutes)

Add two new domains to your existing domains.json:

{
"domains": {
...existing...
"verification": {
"enabled": true,
"priority": -500,
"description": "Claim verification and provenance tracking",
"hooks": [
"Stop_claim_verifier.py",
"Stop_provenance_tracker.py"
]
},
"grounding": {
"enabled": true,
"priority": -400,
"description": "Mandatory inspection before claims",
"hooks": [
"PreToolUse_inspection_gate.py",
"Stop_assumption_audit_v2.py"
]
}
}
}

Why this works: Uses existing domain_checker.py infrastructure. Zero new code, just configuration.

P0: Create SYSTEM_TOPOLOGY.md (15 minutes)

Single file at P:\\.claude\\SYSTEM_TOPOLOGY.md:

# System Topology

actors:
- id: "human"
role: "principal"
capabilities: ["approve", "redirect", "override"]
- id: "claude-code"
role: "assistant"
capabilities: ["read", "write", "execute_tools"]
constraints: ["must_verify_before_claim", "no_speculation"]
- id: "subagents"
role: "specialists"
capabilities: ["domain_analysis", "testing"]
constraints: ["claims_require_verification"]

resources:
- id: "hooks"
authority: "P:/.claude/hooks/domains.json"
inspection_method: "Read domains.json or list hooks"
- id: "skills"
authority: "SKILL.md frontmatter"
inspection_method: "Glob SKILL.md, Read frontmatter"
- id: "daemon"
authority: "__csf/src/daemons/daemon_client.py"
inspection_method: "Read DaemonClient class for timeout values"

verification_policy:
quantitative_claims: "require_source_or_mark_unknown"
external_agent_claims: "require_cross_check_before_accepting"
system_knowledge: "must_inspect_authority_file_before_claiming"

Why this works: Single file, authoritative, can be read by hooks. Agents load it at session start.

P1: Add claim verification to cognitive domain (30 minutes)

Your cognitive domain already exists. Add one new hook:

# Stop_claim_verifier.py

"""
Extracts claims from response and validates against evidence.
Blocks if quantitative claims lack evidence source.
"""
import json
import sys
import re

CLAIM_PATTERNS = [
r'\\d+ms',  \# latency
r'\\d+\\.?\\d*%',  \# percentage
r'\\d+ (?:files|hooks|tests)',  \# counts
]

def extract_claims(response_text):
"""Extract quantitative claims from response."""
claims = []
for pattern in CLAIM_PATTERNS:
matches = re.findall(pattern, response_text)
claims.extend(matches)
return claims

def has_evidence_tool(tool_sequence):
"""Check if evidence-gathering tools were used."""
evidence_tools = {'Read', 'Bash', 'Grep', 'Glob'}
return any(t.get('name') in evidence_tools for t in tool_sequence)

def main():
data = json.loads(sys.stdin.read())
response = data.get('response', '')
tools = data.get('tools_used', [])

      claims = extract_claims(response)
      if claims and not has_evidence_tool(tools):
          print(json.dumps({
              "allow": False,
              "reason": "UNVERIFIED_QUANTITATIVE_CLAIMS",
              "message": f"Claims detected without evidence: {claims[:3]}"
          }))
          sys.exit(2)
    
      print(json.dumps({"allow": True, "reason": "VERIFIED"}))
    if __name__ == "__main__":
main()

Why this works: Single Python file, uses existing Stop hook protocol, extends cognitive domain.

P2: Add doc parity check (45 minutes)

PostToolUse hook to catch spec drift:

# PostToolUse_doc_parity.py

"""
Checks if docs match implementation for key file changes.
"""
import json
import sys
from pathlib import Path

DOC_PAIRINGS = {
"skill_enforcement_gate.py": ["skill_execution_enforcement_v3.2.md"],
"Stop_investigation_validator.py": ["investigation-ledger/README.md"],
}

def main():
data = json.loads(sys.stdin.read())
tool = data.get('tool_name')
filepath = data.get('file_path', '')

      if tool in ('Edit', 'Write') and filepath:
          filename = Path(filepath).name
          if filename in DOC_PAIRINGS:
              # Check if doc files exist and were recently updated
              for doc_file in DOC_PAIRINGS[filename]:
                  doc_path = Path("P:/.claude/hooks") / doc_file
                  if not doc_path.exists():
                      print(json.dumps({
                          "warning": f"DOC_MISSING: Expected {doc_file} for {filename}"
                      }))
    
      print(json.dumps({}))
    if __name__ == "__main__":
main()

Why this works: Lightweight check, catches drift at write time, zero CI overhead.

P3: Add inspection gate (60 minutes - optional/skip if time-constrained)

PreToolUse hook for mandatory inspection:

# PreToolUse_inspection_gate.py

"""
Forces inspection of authority files before certain operations.
"""
import json
import sys

INSPECTION_REQUIRED = {
'Edit': ['skill_enforcement_gate.py', 'Stop_router.py'],
'Write': ['.py'],
}

def main():
data = json.loads(sys.stdin.read())
tool = data.get('tool_name')
filepath = data.get('tool_input', {}).get('file_path', '')

      # Check if this is a protected file
      if tool in INSPECTION_REQUIRED:
          for protected in INSPECTION_REQUIRED[tool]:
              if protected in filepath or protected.endswith('.py'):
                  # In real implementation: check if domains.json was read
                  # For now: just warn that inspection should happen first
                  print(json.dumps({
                      "continue": True,
                      "warning": f"For {tool} on {filepath}, consider inspecting domains.json first"
                  }))
                  sys.exit(0)
    
      print(json.dumps({"continue": True, "reason": "OK"}))
    if __name__ == "__main__":
main()

---
Final Output Block

Decision: Extend your existing domain-based system with 2 new domains (verification, grounding) plus a
single SYSTEM_TOPOLOGY.md manifest. This leverages your existing patterns without wholesale rewrite.

Rationale:

- Your domain_checker.py infrastructure already handles domain gating ✅
- Adding domains.json entries is 5 minutes, zero code ✅
- SYSTEM_TOPOLOGY.md solves R1 (role modeling) in one place ✅
- P1/P2 changes reuse existing hook protocol (Stop, PostToolUse) ✅

Alternatives Considered:

- Full AgentErrorTaxonomy implementation: Requires new classification infrastructure, significant overhead
- External Guardrails/RAIL library: Adds dependency, doesn't integrate with existing hook system
- New orchestration layer: Complete rewrite, high cost

Risk:

- New domains disabled by default until tested (mitigation: use HOOK_DOMAIN_VERIFICATION=true)
- Doc parity checks may flag false positives (mitigation: start with warnings only)
- SYSTEM_TOPOLOGY.md may drift from reality (mitigation: read by hooks at runtime)"

No, this is not optimal. It's a good first‑pass extension of your existing domain‑checker infrastructure, but it has several gaps that leave the core failure domains partially addressed. Here's a breakdown of what's solid, what's weak, and what would make it truly robust.

## Strengths (what works well)

- **Leverages your existing patterns**: Adding `verification` and `grounding` domains to `domains.json` is smart—zero new architecture, instant deploy via config. This directly hits G1 and E1 with minimal effort.[^3_1][^3_2]
- **SYSTEM_TOPOLOGY.md**: Excellent single source of truth for R1 (role modeling). Making it readable by hooks ensures it's not just a human doc.
- **Hook‑based enforcement**: Using `Stop_claim_verifier.py` and `PostToolUse_doc_parity.py` fits Claude Code's hook ecosystem perfectly—no external deps.
- **Prioritization and pragmatism**: P0‑P3 with effort estimates shows good judgment.

This covers ~60% of the failure domains with low disruption.

## Critical weaknesses (sub‑optimal parts)

These leave major holes in coverage:


| Domain | Issue | Impact |
| :-- | :-- | :-- |
| **E1 (Epistemic)** | `Stop_claim_verifier.py` only catches regex patterns like `\d+ms` *after* the response. It doesn't prevent the model from reasoning with unverified claims during planning. | Model can still hallucinate latency numbers in its internal plan, even if the final output gets blocked. |
| **G1 (Grounding)** | `PreToolUse_inspection_gate.py` is too weak—just a warning. No enforcement of actual inspection (e.g., "did you read `domains.json`?"). | Model can still assume hook locations without opening files. |
| **C1 (Cross‑agent)** | No provenance tracking for external claims (e.g., "other LLM said X"). Verifier ignores source entirely. | Your "accepted external claims" failure mode remains unaddressed. |
| **S1 (Spec drift)** | `PostToolUse_doc_parity.py` only checks existence/timestamps, not semantic drift (e.g., "doc says modify A, code created B"). | Misses the actual v3.2‑style drift you saw. |
| **X1 (Execution)** | No controller for "ask vs check." Model can still defer to you instead of using tools. | Perpetuates "should I do X?" loops. |

The output also assumes hooks like `Stop_claim_verifier.py` exist (they don't yet), and the regex patterns are brittle (misses "two seconds," "2s," etc.).

## Domain coverage gaps

Here's how it stacks up:

```
Full coverage target: G1 E1 C1 S1 R1 X1

This proposal:     ✓G1  ✓E1  ⨯C1  ⨯S1  ✓R1  ⨯X1
                   (weak)(weak)     (manifest)
```

**Missing**: Cross‑agent verification, semantic spec alignment, execution policies.

## Optimal improvements (minimal additions)

Since you don't care about training effort, here's how to harden it into a truly domain‑complete solution. These are ~2‑3 more hooks, still leveraging your infrastructure:

### 1. **Fix E1/C1: Pre‑planning claim extraction + provenance (P0.5, 20 min)**

Replace the post‑response verifier with a **PreCompletion** or **PreToolUse** hook that inspects the *planning context*:

```python
# PreCompletion_claim_provenance.py  (add to verification domain)
"""
Inspects conversation history for unprovenanced claims before completion.
"""
import json, re, sys
from pathlib import Path

def has_provenance(ctx):
    # Check for evidence in recent tools or SYSTEM_TOPOLOGY.md reads
    recent_tools = ctx.get('recent_tools', [])
    evidence_tools = {'Read', 'Bash', 'Glob', 'Grep'}
    
    # Provenance patterns: "source: code" or "verified in domains.json"
    provenance_pat = r'(source|verified|evidence)[:\s]+(?:domains\.json|daemon_client\.py|SKILL\.md)'
    
    # Scan recent messages for quantitative claims without provenance
    recent_text = ' '.join([m.get('content', '') for m in ctx.get('recent_messages', [])[-5:]])
    claims = re.findall(r'\d+(?:\.\d+)?\s*(?:ms|s|%)', recent_text)
    
    unprovenanced = any(claim for claim in claims if not re.search(provenance_pat, recent_text))
    
    if unprovenanced and not any(t.get('name') in evidence_tools for t in recent_tools):
        return False, f"Unprovenanced claims: {claims[:2]}"
    return True, "OK"

# Hook logic: block if no provenance
```

**Why optimal**: Catches epistemic errors *during planning*, forces provenance for external claims.

### 2. **Fix G1/X1: Mandatory inspection controller (P1.5, 30 min)**

Make `PreToolUse_inspection_gate.py` actually enforce:

```python
# Enforce inspection of authority files first
AUTHORITY_FILES = {
    'hooks': ['domains.json', 'SKILL.md'],
    'daemon': ['daemon_client.py']
}

def recent_inspection(tool_history, authority):
    return any('domains.json' in t.get('input', '') for t in tool_history[-3:])

if tool == 'Edit' and 'hook' in filepath.lower():
    if not recent_inspection(tools_used, 'hooks'):
        return {"allow": False, "reason": "INSPECT_DOMAINS_JSON_FIRST"}
```

**Why optimal**: Turns warnings into hard blocks. Directly solves "assumed without verifying."

### 3. **Fix S1: Semantic doc‑drift detector (P2.5, 45 min)**

Upgrade `PostToolUse_doc_parity.py` to check *content*, not just existence:

- Use a small local model or simple embedding check: "did the doc mention the changed file?"
- Or require explicit `DOC_UPDATE_REQUIRED` tags in changed files.

**Why optimal**: Catches "doc said A, code did B" semantically.

### 4. **Fix X1: No‑ask policy enforcer (P3.5, 15 min)**

Add to `cognitive` domain:

```python
# Stop_ask_permission.py
# Blocks responses containing "should I", "permission to", "do you want me to"
# Forces tool use instead
FORBIDDEN_PHRASES = ["should I", "permission to", "do you want", "confirm before"]
if any(phrase in response.lower() for phrase in FORBIDDEN_PHRASES):
    return {"allow": False, "reason": "USE_TOOLS_INSTEAD_OF_ASKING"}
```

**Why optimal**: Simple regex block on known deferral patterns.

## Revised roadmap (now domain‑complete)

```
P0 (5 min): domains.json + SYSTEM_TOPOLOGY.md  → R1 ✓
P0.5 (20 min): PreCompletion_claim_provenance.py → E1/C1 ✓
P1.5 (30 min): Mandatory_inspection_gate.py → G1/X1(partial) ✓
P2.5 (45 min): Semantic_doc_drift.py → S1 ✓
P3.5 (15 min): Stop_ask_permission.py → X1 ✓
```

**Total effort**: ~115 min vs original 150 min. Now covers **all 6 domains** with hard enforcement.

## Why this is optimal

- **No new architecture**: All hooks, all domains.json, all Claude Code native.
- **Prevents at root**: Blocks bad reasoning *before* it cascades, not just post‑facto.
- **Composable**: Each hook is independent; disable domains individually.
- **Testable**: Each has clear `{"allow": False, "reason": "FAILURE_CODE"}` outputs for debugging.
- **No training needed**: Pure rule‑based + regex + file checks.

The local LLM's version is a solid **starting point** (8/10), but suboptimal because it reacts too late and misses cross‑agent/provenance. With these 4 tweaks, you get a production‑grade guardrail system that systematically closes all the domains your incidents exposed.

<div align="center">⁂</div>

[^3_1]: https://www.datacamp.com/blog/llm-guardrails

[^3_2]: https://paddo.dev/blog/claude-skills-hooks-solution/


---

# This is the actual domains in my hooks.  Is this domain model easier to work with?

"The main functional domains in HOOKS_CATALOG.md are:

# Domain	Hook Count	Description

1	Truth \& Evidence	12	Block diagnostic claims without verification, track evidence
2	Quality \& Behavioral	6	Detect overconfidence, sycophancy, lazy closure, work avoidance
3	Constitutional Patterns	5	Assumption audit, anti-sycophancy, reflexion validation
4	Code Protection	5	Syntax gates, hook protection, TDD enforcement, Catch-22 detection
5	Investigation \& Research	3	Block modifications without reading first, speculation detection
6	Path \& File Safety	5	Path resolution, file locking, shell complexity, semantic routing
7	Task \& Session Management	5	Task coordination, session tracking, CKS accumulation, checkpoints
8	Cognitive Frameworks	2	Solo dev injection, goal anchoring, diagnostic frameworks
9	Skill \& Workflow Enforcement	6	Slash command enforcement, /v workflow state tracking
10	Observability \& Logging	5	System 2 debugging, failure recording, outcome validation
11	Formatting \& Style	2	Auto-formatting (ruff/prettier), command suggestions
12	CKS (Constitutional Knowledge System)	4	Decision capture, memory injection, automatic storage"

Yes, this domain model is easier to work with than the ad‑hoc G1/E1/C1 taxonomy for your concrete system, because it is closer to the **actual levers your hooks operate on** and lines up with how people structure guardrails in production.[^4_1][^4_2][^4_3]

## How well it maps to real failure domains

Your 12 domains already span the major guardrail buckets people use:

- **Truth \& Evidence** – fact‑checking, hallucination rails, epistemic control.[^4_2]
- **Quality \& Behavioral / Constitutional Patterns** – planning/behavioral failures, overconfidence, lazy closure, policy adherence.[^4_4][^4_1]
- **Code Protection / Path \& File Safety** – tool misuse, unsafe actions, environment safety.[^4_3]
- **Investigation \& Research** – “observe before act”, speculation detection.[^4_5]
- **Task \& Session Management / Cognitive Frameworks** – role/task alignment, objective drift.[^4_6]
- **Skill \& Workflow Enforcement** – process/policy adherence.
- **Observability \& Logging** – AgentOps/trace‑based observability.[^4_7][^4_8]
- **Formatting \& Style / CKS** – presentation, knowledge capture.

That means most of the “known failure domains” you care about (grounding, epistemic uncertainty, cross‑agent trust, spec drift, execution control) can be expressed as **rules inside existing domains** instead of adding new ones.

## Practical implications for your earlier failures

You don’t need “verification” and “grounding” as separate domains; you can place the controls like this:

- **Assumed without verifying (hooks, daemon, etc.)**
    - Primary: Truth \& Evidence + Investigation \& Research.
    - Implementation: hooks that block claims and edits when no evidence tools or authority files have been consulted.
- **Unverified latency / quantitative claims**
    - Truth \& Evidence: quantitative‑claim verifier + provenance check.
    - Observability \& Logging: record when these blocks happen for later tuning.
- **Accepting external LLM claims**
    - Truth \& Evidence: provenance requirement (“external_agent” source must be cross‑checked).
    - Cognitive Frameworks: patterns that prefer local authority over peer narratives.
- **Doc/spec drift**
    - Code Protection + CKS + Observability \& Logging:
        - Post‑edit doc checks.
        - Decision capture about which spec applies.
        - Logged mismatches.
- **“Should I do X?” instead of checking**
    - Quality \& Behavioral + Task \& Session Management:
        - Detect work‑avoidance/deferral phrases.
        - Enforce “tool‑first” patterns for certain task classes.

So yes: this domain model is not only workable, it’s **better aligned** with standard guardrail taxonomies (safety/quality/tool‑safety/ops) than the temporary G1/E1 labels.[^4_9][^4_10][^4_11]

## What I’d change (minor refinements)

Two tweaks would make it even more usable as a control surface:

- Make **Truth \& Evidence** explicitly own:
    - Claim extraction.
    - Provenance tracking (including cross‑agent).
    - “Unknown is allowed; unjustified certainty is not.”
- Make **Investigation \& Research** explicitly own:
    - “Read before write” and “inspect authority file before claim” invariants.
    - Mandatory tool‑use patterns for certain resources (hooks, daemon, skills).

Everything else can stay as‑is; you’re already matching how production guardrail frameworks separate **content quality, action safety, and observability**, which is what you want.[^4_1][^4_3][^4_7]
<span style="display:none">[^4_12][^4_13][^4_14][^4_15]</span>

<div align="center">⁂</div>

[^4_1]: https://www.agno.com/blog/guardrails-for-ai-agents

[^4_2]: https://aws.amazon.com/blogs/machine-learning/build-safe-and-responsible-generative-ai-applications-with-guardrails/

[^4_3]: https://galileo.ai/blog/ai-agent-guardrails-framework

[^4_4]: https://arxiv.org/html/2411.12946v2

[^4_5]: https://arxiv.org/html/2601.18491v1

[^4_6]: https://www.linkedin.com/posts/rathanuday_ai-agents-dont-fail-because-theyre-not-activity-7411823219176865792-xB4z

[^4_7]: https://arxiv.org/html/2411.05285v2

[^4_8]: https://agenta.ai/blog/the-ai-engineer-s-guide-to-llm-observability-with-opentelemetry

[^4_9]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12532640/

[^4_10]: https://unit42.paloaltonetworks.com/comparing-llm-guardrails-across-genai-platforms/

[^4_11]: https://skywork.ai/blog/llm-observability-best-practices-haiku-logging-tracing-guardrails/

[^4_12]: https://www.datadoghq.com/blog/llm-guardrails-best-practices/

[^4_13]: https://wandb.ai/onlineinference/genai-research/reports/LLM-evaluation-Metrics-frameworks-and-best-practices--VmlldzoxMTMxNjQ4NA

[^4_14]: https://www.datacamp.com/blog/llm-guardrails

[^4_15]: https://authoritypartners.com/insights/ai-agent-guardrails-production-guide-for-2026/


---

# Suggest improvements to make domains easier for agent development

Yes. To make these domains easier for agent development, you want them to be more **operational**, composable, and mechanically discoverable. Here are concrete improvements, tuned to your current list.

***

## 1. Normalize into “what this protects” vs “how it acts”

Right now each domain mixes:

- Risk type (truth, code safety, doc drift).
- Mechanism (blocking, logging, coordination).

For agents, it helps to split those:

- Add two explicit dimensions in `HOOKS_CATALOG.md`:
    - `risk_type`: `["truth", "behavior", "code_safety", "spec_drift", "session_drift", "observability", "formatting"]`.[^5_1][^5_2]
    - `action_type`: `["block", "warn", "log", "rewrite", "annotate"]`.[^5_3][^5_4]

Then each domain becomes a **cluster of similar risk_types**, but hooks can be filtered by `risk_type` and `action_type`. This makes it trivial for an agent to say “give me all blocking hooks related to truth \& evidence.”

***

## 2. Introduce a “lifecycle phase” axis

Agents reason in phases (interpret → plan → act → reflect). Add a `phase` field per hook:[^5_5]

- `phase`: `["input", "planning", "tool_selection", "tool_execution", "post_execution", "output"]`.

Then:

- Truth \& Evidence can have:
    - `planning` hooks (block unverified assumptions in plans).
    - `output` hooks (block speculative answers).
- Investigation \& Research can enforce “read before write” in `tool_selection` / `tool_execution`.

This helps you target the exact step where each failure domain should be caught, similar to diagnostic frameworks like AgentDoG.[^5_6]

***

## 3. Tighten and merge overlapping domains

For agent dev, fewer but sharper domains are easier. I’d do:

- Merge **Quality \& Behavioral** + **Constitutional Patterns** into:
    - `Behavior & Constitutional` (all “how the model thinks and talks” constraints).
- Merge **Cognitive Frameworks** into **Task \& Session Management**:
    - Make that one “Task, Roles \& Cognitive Frames.”
- Treat **CKS** as a cross‑cutting capability, not a domain:
    - Add a `uses_cks: true/false` flag to hooks instead of a separate domain.

Resulting domains (example):

1. Truth \& Evidence
2. Behavior \& Constitutional
3. Code \& File Safety (Code Protection + Path \& File Safety)
4. Investigation \& Research
5. Task, Roles \& Cognitive Frames
6. Skill \& Workflow Enforcement
7. Observability \& Logging
8. Formatting \& Style

Fewer domains means less routing complexity and clearer mental models, which production guides recommend for maintainable guardrail configs.[^5_2][^5_1]

***

## 4. Add machine‑readable metadata per domain

For each domain, define a small manifest section agents can query:

- `default_autonomy_level`: `["monitor", "warn", "block"]` (maps to risk tiering / HITL triggers).[^5_7][^5_8]
- `blast_radius`: `["low", "medium", "high"]` (how bad if this domain fails).
- `human_escalation`: `true/false` for when hooks in this domain should page you.

Example for Truth \& Evidence:

```yaml
domain: Truth & Evidence
risk_type: truth
default_autonomy_level: block
blast_radius: high
human_escalation: true
```

This lets agents dynamically adjust: e.g., always obey Truth \& Evidence blocks, but treat Behavior \& Constitutional warnings as soft.

***

## 5. Make discovery trivial for agents

To reduce “missing related hooks”:

- Give every hook:
    - `tags`: `["latency", "quantitative_claims", "cross_agent_trust", "read_before_write"]`.
    - `applies_to`: `["code_edit", "daemon_config", "skill_metadata", "task_spec"]`.

Then agents can do:

- “List all `Truth & Evidence` + `tags: ["quantitative_claims"]` + `applies_to: ["daemon_config"]`.”

This aligns with how observability/guardrail frameworks recommend tagging checks so they can be queried and combined programmatically.[^5_9][^5_10][^5_11]

***

## 6. Explicit spec‑drift coverage as a first‑class domain facet

Your current domains imply spec drift (CKS, Observability, Code Protection) but don’t name it. For agent work:

- Add `spec_drift_handling` to relevant domains (Truth \& Evidence, Code \& File Safety, Observability):
    - `["none", "warn", "block"]`.

And add a small separate section in `HOOKS_CATALOG.md` listing the **authoritative artifacts**:

- `authority_files`:
    - `hooks_manifest`: `P:/.claude/hooks/domains.json`
    - `system_topology`: `P:/.claude/SYSTEM_TOPOLOGY.md`
    - `enforcement_spec`: `skill_enforcement_gate.spec.md`

Agents and hooks can then enforce: “if you touch an authority_file target, you must also satisfy spec‑drift hooks.”

This matches “policy‑from‑design‑artifacts” work (turning governance rules into guardrails).[^5_12]

***

## 7. Encode autonomy levels per domain for agents

Borrowing from risk‑tiering/guardrail levels:[^5_8][^5_7]

- Add `autonomy_level` per domain:
    - `0 = log only`
    - `1 = warn, no block`
    - `2 = conditional block`
    - `3 = hard block + HITL`

Then agents can be configured per session:

- For high‑risk sessions (e.g., editing enforcement code), set:
    - Truth \& Evidence = 3
    - Code \& File Safety = 3
    - Investigation \& Research = 2
- For low‑risk (markdown editing), drop some to 1.

This makes your domain model directly usable as a policy control surface, which is how production systems expose guardrail knobs.[^5_13][^5_2]

***

If you want, I can draft a concrete `domains.yaml`/`HOOKS_CATALOG.md` v2 layout with these fields filled in for one or two domains so your agents can start querying them immediately.
<span style="display:none">[^5_14][^5_15][^5_16][^5_17]</span>

<div align="center">⁂</div>

[^5_1]: https://www.agno.com/blog/guardrails-for-ai-agents

[^5_2]: https://www.leanware.co/insights/llm-guardrails

[^5_3]: https://retool.com/resources/ai-guardrails

[^5_4]: https://www.reco.ai/hub/guardrails-for-ai-agents

[^5_5]: https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/

[^5_6]: https://arxiv.org/html/2601.18491v1

[^5_7]: https://galileo.ai/blog/ai-agent-guardrails-framework

[^5_8]: https://skywork.ai/blog/agentic-ai-safety-best-practices-2025-enterprise/

[^5_9]: https://www.montecarlodata.com/blog-what-is-agent-observability/

[^5_10]: https://arxiv.org/html/2411.05285v2

[^5_11]: https://agenta.ai/blog/the-ai-engineer-s-guide-to-llm-observability-with-opentelemetry

[^5_12]: https://arxiv.org/html/2509.23994v2

[^5_13]: https://toloka.ai/blog/essential-ai-agent-guardrails-for-safe-and-ethical-implementation/

[^5_14]: https://arxiv.org/html/2408.01452v1

[^5_15]: https://cleanlab.ai/blog/ai-agent-safety/

[^5_16]: https://www.datadoghq.com/blog/llm-guardrails-best-practices/

[^5_17]: https://about.gitlab.com/the-source/ai/implementing-effective-guardrails-for-ai-agents/


---

# Examples of domain-specific guardrails for AI agents

Here are concrete examples of domain‑specific guardrails, across different verticals and failure types, in the style of the domains you’re already using.

***

## 1. Truth \& Evidence (diagnostic / factual domains)

**Healthcare triage agent**

- Guardrail: “If user asks for a diagnosis, do not provide one; instead, recommend seeing a clinician and provide general educational information only.”[^6_1][^6_2]
- Implementation:
    - Classifier detects medical advice intent.
    - Output filter blocks phrases like “you have X” or “this is likely Y.”
    - Response template redirects to safe guidance.

**Financial advisory agent**

- Guardrail: “Never make specific buy/sell recommendations; restrict to explaining concepts and generic risk factors.”[^6_3][^6_4]
- Implementation:
    - Domain‑specific keyword and pattern list for instruments, tickers, order verbs (“buy”, “short”, “liquidate”).
    - If present with user‑specific context, output is rejected and re‑written into generic education.

***

## 2. Code \& Infra Safety (tool / action domains)

**DevOps deployment agent**

- Guardrail: “Cannot run commands that modify infrastructure state without an approved change ticket.”[^6_5][^6_6]
- Implementation:
    - Map high‑risk actions (`terraform apply`, `kubectl delete`, `helm uninstall`) to policy entries.
    - Pre‑execution check:
        - Verifies change‑ticket ID in input.
        - Verifies ticket in an external system (Jira/ServiceNow).
        - Blocks or routes to human if missing.

**Database maintenance agent**

- Guardrail: “Read‑only access in production; write access only in staging.”[^6_7][^6_5]
- Implementation:
    - Tool layer exposes `prod_db` with `read` methods only, enforces schema‑validated queries.
    - Any attempt to call a `write` operation in prod is blocked and logged.

***

## 3. Compliance \& Policy (regulatory domains)

**K‑12 educational assistant**

- Guardrail: “No sharing of personally identifiable student data; enforce age‑appropriate content.”[^6_8][^6_9][^6_3]
- Implementation:
    - Dedicated guardrail model trained to classify unsafe/age‑inappropriate outputs and PII mentions.
    - Output passes through:
        - PII redaction.
        - Content appropriateness classifier.
        - Block/modify/route‑to‑human based on scores.

**HR or legal agent**

- Guardrail: “Do not provide binding legal or HR decisions; label responses as informational only.”[^6_10][^6_11]
- Implementation:
    - Output wrapper injects disclaimer and strips imperatives like “You must” or “This is legally required” unless backed by verified policy snippets.

***

## 4. Task \& Workflow Enforcement (process domains)

**Customer support triage agent**

- Guardrail: “Must follow escalation playbook before closing a ticket.”[^6_12][^6_5]
- Implementation:
    - State machine:
        - Step 1: Verify account.
        - Step 2: Collect minimal reproducible description.
        - Step 3: Attempt known fixes.
        - Step 4: Escalate if unresolved.
    - Guardrail checks that required fields/tags are set and steps executed before agent can set status to “Resolved.”

**Invoice processing agent**

- Guardrail: “Cannot approve refunds over a threshold without human review; cannot create new vendors.”[^6_13][^6_6]
- Implementation:
    - Map actions like `refund.issue`, `vendor.create` to permission and amount thresholds.
    - For high‑risk actions:
        - Require second factor (manager approval token) or HITL routing.

***

## 5. Investigation \& Research (grounding domains)

**Research assistant agent**

- Guardrail: “Must cite at least N external sources and mark speculative statements as such for scientific questions.”[^6_14][^6_10]
- Implementation:
    - Planning phase:
        - Enforce a minimum number of search/tool calls.
    - Output phase:
        - Check that factual claims are accompanied by citations.
        - Detect phrases like “definitely”, “proven” without evidence and down‑scope them (“likely”, “some evidence suggests”).

**Data analytics agent**

- Guardrail: “No conclusions about trends without running at least one query touching the relevant metric.”[^6_4]
- Implementation:
    - Pre‑conclusion hook:
        - Parse planned explanation.
        - Verify that referenced metrics were queried (via query log).
        - Block if conclusions reference unseen data.

***

## 6. Observability \& Logging (ops domains)

**General AI ops**

- Guardrail: “All high‑risk actions must be traceable with full context.”[^6_15][^6_16][^6_17]
- Implementation:
    - For actions tagged `risk=high`:
        - Enforce logging of:
            - User ID, time, input, plan, tools used, outputs.
        - Refuse to execute if logging backend is unreachable (fail‑safe).

**Behavior drift monitoring**

- Guardrail: “Detect and flag deviations from baseline answer style or tool‑use patterns.”[^6_18][^6_14]
- Implementation:
    - Baseline profiles of:
        - Typical response length, tone, tool mix.
    - Online monitor compares live behavior; if drift exceeds threshold, down‑scopes autonomy or routes to review.

***

## 7. Domain‑specific guardrail model (single‑model layer)

A different pattern (what you were hinting at with domains) is a **separate guardrail model trained per domain**, e.g. K‑12 education:

- Input: `(user_query, candidate_response)`.
- Output: labels like `OK`, `age_inappropriate`, `policy_violation`, `needs_human`, with scores.[^6_3][^6_8]
- Integration:
    - Main agent proposes action/response.
    - Guardrail model scores it.
    - Orchestrator:
        - Accepts, rewrites, or blocks based on domain rules.

This is a full “domain guardrail” in one component rather than many small hooks.

***

If you want, I can map these examples onto your current domains (Truth \& Evidence, Investigation \& Research, Code Protection, etc.) and sketch hook names plus JSON contract shapes so they drop straight into your `HOOKS_CATALOG.md` and domains system.
<span style="display:none">[^6_19][^6_20]</span>

<div align="center">⁂</div>

[^6_1]: https://uxplanet.org/guardrails-for-ai-agents-24349b93caeb

[^6_2]: https://witness.ai/blog/ai-agent-guardrails/

[^6_3]: https://arxiv.org/html/2408.01452v1

[^6_4]: https://www.tredence.com/blog/data-guardrails-in-agentic-ai-deployment

[^6_5]: https://www.reco.ai/hub/guardrails-for-ai-agents

[^6_6]: https://about.gitlab.com/the-source/ai/implementing-effective-guardrails-for-ai-agents/

[^6_7]: https://galileo.ai/blog/ai-agent-guardrails-framework

[^6_8]: https://arxiv.org/abs/2408.01452

[^6_9]: https://warwick.ac.uk/fac/cross_fac/eduport/edufund/projects/yang/projects/building-a-domain-specific-guardrail-model-in-production/

[^6_10]: https://www.qed42.com/insights/ai-guardrails-building-safe-and-reliable-llm-applications

[^6_11]: https://toloka.ai/blog/essential-ai-agent-guardrails-for-safe-and-ethical-implementation/

[^6_12]: https://theagentarchitect.substack.com/p/implementing-guardrails-ai-agent-systems

[^6_13]: https://frontegg.com/blog/ai-agent-governance-starts-with-guardrails

[^6_14]: https://galileo.ai/blog/ai-agent-guardrails-guide

[^6_15]: https://arxiv.org/html/2411.05285v2

[^6_16]: https://agenta.ai/blog/the-ai-engineer-s-guide-to-llm-observability-with-opentelemetry

[^6_17]: https://www.montecarlodata.com/blog-what-is-agent-observability/

[^6_18]: https://arxiv.org/html/2601.18491v1

[^6_19]: https://www.databricks.com/blog/ai-agent-examples-shaping-business-landscape

[^6_20]: https://krnel.ai/blog/2025-10-29-kg-guardrail-example/


---

```
# <q>If you want, I can draft a concrete domains.yaml/HOOKS_CATALOG.md v2 layout with these fields filled in for one or two domains so your agents can start querying them immediately.</q> yes please
```

Here’s a concrete, agent‑friendly v2 layout you can drop in. I’ll show:

- A `domains.yaml` for two domains.
- Matching `HOOKS_CATALOG.md` snippets.
- Field shapes tuned for querying from agents.

You can expand the pattern across the rest.

***

## domains.yaml (v2, example for 2 domains)

```yaml
# P:/.claude/hooks/domains.yaml

domains:
  truth_evidence:
    id: "truth_evidence"
    name: "Truth & Evidence"
    description: "Fact checking, claim verification, provenance, epistemic control."
    risk_type: ["truth", "epistemic"]
    default_autonomy_level: 3          # 0=log,1=warn,2=soft-block,3=hard-block
    blast_radius: "high"
    human_escalation: true
    spec_drift_handling: "block"       # none|warn|block
    phases:                            # lifecycle phases this domain covers
      - "planning"
      - "tool_execution"
      - "output"
    authority_files:                   # where 'truth' lives for system facts
      - path: "P:/.claude/SYSTEM_TOPOLOGY.md"
        description: "System topology and authority mapping"
      - path: "P:/.claude/hooks/domains.yaml"
        description: "Guardrail domain configuration"
    hooks:
      - "Stop_claim_verifier.py"
      - "Stop_cross_agent_unverified_claims.py"
      - "PostToolUse_evidence_audit.py"

  investigation_research:
    id: "investigation_research"
    name: "Investigation & Research"
    description: "Enforces observe-before-act, read-before-write, and anti-speculation patterns."
    risk_type: ["grounding", "planning"]
    default_autonomy_level: 2          # warn+soft-block by default
    blast_radius: "medium"
    human_escalation: false
    spec_drift_handling: "warn"
    phases:
      - "planning"
      - "tool_selection"
      - "tool_execution"
    authority_files:
      - path: "P:/.claude/SYSTEM_TOPOLOGY.md"
        description: "Defines authority inspection methods per resource"
    hooks:
      - "PreToolUse_read_before_write_gate.py"
      - "PrePlanning_observation_required.py"
      - "Stop_speculative_investigation_closure.py"
```

Key points:

- `risk_type`, `phases`, `default_autonomy_level` make it easy for agents to query “which domains apply at this step?”
- `authority_files` is where your “system truth” lives for that domain.

***

## HOOKS_CATALOG.md (v2 excerpts for those domains)

You can keep this as Markdown with YAML frontmatter per hook, or as a big table. Below is a mixed approach: domain section + per‑hook metadata blocks that agents can parse.

### Truth \& Evidence

```markdown
## Domain: Truth & Evidence

Purpose: Fact checking, claim verification, and provenance constraints for agent reasoning and outputs.

- risk_type: truth, epistemic
- default_autonomy_level: 3 (hard block)
- phases: planning, tool_execution, output

### Hook: Stop_claim_verifier.py

```yaml
id: "Stop_claim_verifier"
domain: "truth_evidence"
description: "Blocks responses containing quantitative claims without supporting evidence/tool use."
risk_type: ["truth", "epistemic"]
phase: "output"
action_type: "block"          # block|warn|log|rewrite|annotate
applies_to: ["all_responses"]
tags:
  - "quantitative_claims"
  - "latency"
  - "counts"
  - "percentages"
uses_cks: false
inputs:
  - "response_text"
  - "tools_used"
policy:
  quantitative_claims: "require_source_or_mark_unknown"
  external_agent_claims: "must_have_provenance"
failure_codes:
  - "UNVERIFIED_QUANTITATIVE_CLAIMS"
  - "MISSING_EVIDENCE_TOOL"
```


### Hook: Stop_cross_agent_unverified_claims.py

```yaml
id: "Stop_cross_agent_unverified_claims"
domain: "truth_evidence"
description: "Blocks adoption of claims originating from external agents unless cross-checked."
risk_type: ["truth", "epistemic"]
phase: "planning"
action_type: "block"
applies_to: ["multi_agent_context", "delegated_tasks"]
tags:
  - "cross_agent_trust"
  - "provenance"
  - "delegation"
uses_cks: true
inputs:
  - "conversation_history"
  - "agent_metadata"
policy:
  external_agent_claims: "require_cross_check_before_accepting"
  provenance_required: true
failure_codes:
  - "UNVERIFIED_EXTERNAL_CLAIM"
  - "MISSING_PROVENANCE"
```


### Hook: PostToolUse_evidence_audit.py

```yaml
id: "PostToolUse_evidence_audit"
domain: "truth_evidence"
description: "Audits whether claims made in the step are supported by the tools that were actually used."
risk_type: ["truth"]
phase: "tool_execution"
action_type: "warn"
applies_to: ["analysis_steps", "summaries"]
tags:
  - "evidence_audit"
  - "tool_trace"
uses_cks: false
inputs:
  - "tools_used"
  - "step_summary"
policy:
  unsupported_claims: "emit_warning_and_log"
failure_codes:
  - "CLAIM_TOOL_MISMATCH"
```

```

***

### Investigation & Research

```markdown
## Domain: Investigation & Research

Purpose: Ensure the agent reads/observes before acting, and avoids speculative closure when evidence is missing.

- risk_type: grounding, planning
- default_autonomy_level: 2 (soft block)
- phases: planning, tool_selection, tool_execution

### Hook: PreToolUse_read_before_write_gate.py

```yaml
id: "PreToolUse_read_before_write_gate"
domain: "investigation_research"
description: "Blocks edits to protected resources unless recent inspection of their authority file has occurred."
risk_type: ["grounding", "planning"]
phase: "tool_execution"
action_type: "block"
applies_to: ["code_edit", "config_edit"]
tags:
  - "read_before_write"
  - "observe_before_act"
  - "authority_files"
uses_cks: false
inputs:
  - "tool_name"
  - "tool_input"
  - "recent_tools"
policy:
  protected_resources:
    - type: "hooks"
      authority_files:
        - "P:/.claude/hooks/domains.yaml"
        - "SKILL.md"
    - type: "daemon"
      authority_files:
        - "__csf/src/daemons/daemon_client.py"
  requirement: "must_have_recent_read_of_authority_file"
failure_codes:
  - "AUTHORITY_NOT_INSPECTED"
```


### Hook: PrePlanning_observation_required.py

```yaml
id: "PrePlanning_observation_required"
domain: "investigation_research"
description: "Requires at least one observation/tool call before the agent commits to a non-trivial plan."
risk_type: ["grounding"]
phase: "planning"
action_type: "warn"
applies_to: ["complex_tasks", "code_changes"]
tags:
  - "observe_before_act"
  - "tool_minimum"
uses_cks: true
inputs:
  - "task_spec"
  - "recent_tools"
policy:
  min_observation_tools: 1
  observation_tools:
    - "Read"
    - "Glob"
    - "Grep"
failure_codes:
  - "INSUFFICIENT_OBSERVATION"
```


### Hook: Stop_speculative_investigation_closure.py

```yaml
id: "Stop_speculative_investigation_closure"
domain: "investigation_research"
description: "Prevents the agent from declaring investigations complete when evidence is missing or contradictory."
risk_type: ["grounding", "planning"]
phase: "output"
action_type: "block"
applies_to: ["investigation_reports"]
tags:
  - "speculation_detection"
  - "lazy_closure"
uses_cks: true
inputs:
  - "investigation_summary"
  - "evidence_log"
policy:
  completion_requires:
    - "at_least_one_supporting_evidence"
    - "no_known_contradictions"
failure_codes:
  - "SPECULATIVE_CLOSURE"
  - "CONTRADICTED_BY_EVIDENCE"
```

```

***

## How agents can use this immediately

With this structure, an agent (or hook) can do things like:

- “List all **blocking** hooks for **truth** in the **planning** phase” by filtering:
  - `domain.risk_type contains "truth"`
  - `hook.phase == "planning"`
  - `hook.action_type == "block"`.
- “Before editing a daemon file, check if any `investigation_research` hooks apply to `code_edit` and enforce their `policy.protected_resources`.”
- “For a multi‑agent task, activate `Stop_cross_agent_unverified_claims` automatically because `applies_to` includes `multi_agent_context`.”

If you’d like, next I can:

- Add one more domain (e.g., Code & File Safety) in the same format, or
- Sketch the minimal Python stub for `PreToolUse_read_before_write_gate.py` that reads `domains.yaml` and applies `policy.protected_resources` dynamically.

---

# "The main functional domains in HOOKS_CATALOG.md are:

#	Domain	Hook Count	Description
1	Truth & Evidence	12	Block diagnostic claims without verification, track evidence
2	Quality & Behavioral	6	Detect overconfidence, sycophancy, lazy closure, work avoidance
3	Constitutional Patterns	5	Assumption audit, anti-sycophancy, reflexion validation
4	Code Protection	5	Syntax gates, hook protection, TDD enforcement, Catch-22 detection
5	Investigation & Research	3	Block modifications without reading first, speculation detection
6	Path & File Safety	5	Path resolution, file locking, shell complexity, semantic routing
7	Task & Session Management	5	Task coordination, session tracking, CKS accumulation, checkpoints
8	Cognitive Frameworks	2	Solo dev injection, goal anchoring, diagnostic frameworks
9	Skill & Workflow Enforcement	6	Slash command enforcement, /v workflow state tracking
10	Observability & Logging	5	System 2 debugging, failure recording, outcome validation
11	Formatting & Style	2	Auto-formatting (ruff/prettier), command suggestions
12	CKS (Constitutional Knowledge System)	4	Decision capture, memory injection, automatic storage"

I know my system is organic, but it's confusing.  How can I start making it logical, and plugging the holes it in?

Your domains are powerful but “organic” because they evolved around hooks, not around a clean control model. To make them logical and plug holes, you want to: 1) normalize them into a small, predictable schema, and 2) systematically map them to failure modes and lifecycle phases.

Below is a minimal, high‑leverage way to do that without rewriting everything.

***

## 1. Normalize the domain model (merge, rename, clarify)

First, reduce overlap and make each domain answer one clear question: “What kind of problem do I prevent?”

A concrete simplification of your 12:

| New Domain | Built From | Purpose |
| --- | --- | --- |
| Truth & Evidence | 1 | Factual correctness, verification, provenance. |
| Behavior & Constitutional | 2 + 3 | Reasoning style, overconfidence, assumptions, sycophancy. |
| Code & File Safety | 4 + 6 | Code edits, paths, shell commands, environment integrity. |
| Investigation & Research | 5 | Read‑before‑write, observe‑before‑act, speculation control. |
| Tasks, Roles & Cognitive Frames | 7 + 8 | Task specification, role modeling, goal anchoring. |
| Skill & Workflow Enforcement | 9 | Slash commands, workflow state, process discipline. |
| Observability & Logging | 10 | Traces, debugging, outcome validation. |
| Formatting & Style | 11 | Output shape, formatting, style. |
| CKS (Cross‑cutting flag) | 12 | Mark hooks that use/write CKS, not its own domain. |

Practically:

- Keep your existing “domains” list, but:
  - Merge the above pairs in `HOOKS_CATALOG.md`.
  - Add a `behavior_constitutional` domain and migrate Quality & Behavioral + Constitutional Patterns hooks into it over time.
- Treat **CKS** as a capability flag on hooks (`uses_cks: true`), not a top‑level domain.

This alone makes the mental model far cleaner and matches how guardrail frameworks group safety vs behavior vs tool safety vs observability.[^8_1][^8_2]

***

## 2. Add a small schema per hook (make it machine‑queryable)

Right now domains are descriptive; agents need structure. Add a tiny metadata block per hook (even inline in MD):

- `domain`: one of the normalized domains.
- `phase`: `input | planning | tool_selection | tool_execution | post_execution | output`.
- `risk_type`: `truth | behavior | code_safety | grounding | session | workflow | observability | style`.
- `action_type`: `block | warn | log | rewrite | annotate`.
- `applies_to`: e.g. `["code_edit", "daemon_config", "task_spec", "multi_agent_context"]`.
- `uses_cks`: bool.

Example for a Truth & Evidence hook:

```yaml
id: "Stop_unverified_diagnostics"
domain: "truth_evidence"
phase: "output"
risk_type: ["truth", "epistemic"]
action_type: "block"
applies_to: ["diagnostic_reports"]
tags: ["diagnostic_claims", "verification_required"]
uses_cks: true
```

Once this exists, you can:

- Ask agents: “List all `block` hooks in `truth_evidence` for `phase=planning`.”
- Ensure every failure mode class has at least one hook covering it.

This is exactly what domain‑specific guardrail models do at scale: they attach structured metadata to checks so they can be reasoned over and combined programmatically.[^8_3][^8_4]

***

## 3. Map your domains to failure modes (find holes systematically)

Take the failure domains you care about (based on your earlier incidents and what literature calls out):[^8_5][^8_6]

- G (Grounding/observation): assuming configs, schema, hooks without reading them.
- E (Epistemic): unverified facts, made‑up latencies.
- C (Cross‑agent trust): accepting other LLMs’ claims without verification.
- S (Spec/contract drift): docs/spec vs implementation.
- R (Roles/system): mis‑modeling your setup (solo dev vs “human + AI assistants”).
- X (Execution control): asking instead of checking, skipping invariants.

Now explicitly map them to domains:

- **Truth \& Evidence**: E, C, S (facts + spec as truth).
- **Behavior \& Constitutional**: E (overconfidence), X (lazy closure, work avoidance).
- **Code \& File Safety**: X, S (enforcement invariants, spec‑drift around code).
- **Investigation \& Research**: G, X (read‑before‑write, observe‑before‑act).
- **Tasks, Roles \& Cognitive Frames**: R, X (role modeling, task framing).
- **Skill \& Workflow Enforcement**: X (wrong workflow, skipping states).
- **Observability \& Logging**: all (diagnostics, retrospective).
- **Formatting \& Style**: none of the core logic failures (keep separate).

Then, for each failure mode, literally make a small table and fill with existing hooks:

- G (Grounding):
    - Do I have at least one **block** hook in `Investigation & Research` at `tool_execution` that enforces read‑before‑write?
    - Do I have anything that checks “did you inspect SKILL.md / domains before reasoning about hooks?”
- E (Epistemic):
    - Hooks in `Truth & Evidence` that scan for quantitative claims and demand evidence.
- C (Cross‑agent):
    - Any hook that looks at conversation source metadata and refuses external claims without cross‑check?
- S (Spec drift):
    - Hooks in `Code & File Safety` or `Truth & Evidence` that tie changes in enforcement/hook files to their specs/docs?
- R (Roles/system):
    - Hooks in `Tasks, Roles & Cognitive Frames` that inject/verify SYSTEM_TOPOLOGY and block plans that contradict it?
- X (Execution):
    - Hooks in `Behavior & Constitutional` or `Task & Session` that catch “should I do X?” and other work‑avoidance patterns.

Where you find an empty cell, you’ve discovered a **hole**; that gives you a small, high‑value hook to write.

***

## 4. Add a “default policy” per domain (control surface)

For agents to reason about your system, give each domain a few policy fields in `HOOKS_CATALOG.md`/`domains.yaml`:

Per domain:

- `default_autonomy_level`: `0 log`, `1 warn`, `2 soft-block`, `3 hard-block`.
- `blast_radius`: `low | medium | high`.
- `human_escalation`: `true | false`.
- Optional: `spec_drift_handling`: `none | warn | block`.

Example:

```yaml
domain: "truth_evidence"
default_autonomy_level: 3
blast_radius: "high"
human_escalation: true
spec_drift_handling: "block"
```

```yaml
domain: "behavior_constitutional"
default_autonomy_level: 1
blast_radius: "medium"
human_escalation: false
spec_drift_handling: "none"
```

This gives you knobs:

- For high‑risk work (enforcement, daemons), crank `truth_evidence` + `code_file_safety` to 3, `investigation_research` to 2.
- For low‑risk work (docs), keep them at 1–2.

This pattern mirrors how production systems expose guardrails and risk tiers for agents.[^8_7][^8_8][^8_1]

***

## 5. Start with two domains and one concrete pass

To avoid boiling the ocean, pick two domains that most directly match your recent pain:

- Truth \& Evidence.
- Investigation \& Research.

Actionable steps:

1. For every hook currently in “Truth \& Evidence”, add:
    - `phase`, `risk_type`, `action_type`, `applies_to`, `uses_cks`.
2. For every hook in “Investigation \& Research”, add:
    - Same fields, plus a `policy` section that encodes “read‑before‑write” and “observe‑before‑act.”

Then:

- Build a tiny helper tool that:
    - Loads your hook metadata.
    - Given a task description and current phase, returns “relevant hooks to consider.”
- Have your agents call that tool at the start of a session to see which guardrails are in play.

Once those two domains are structured, repeating the pattern across Code \& File Safety, Tasks \& Roles, etc. is mostly mechanical.

***

If you’d like, I can take one existing hook (e.g. your current “block modifications without reading first” hook) and rewrite its metadata + a slightly refactored version so it fits this normalized model. That gives you a direct before/after template.

<div align="center">⁂</div>

[^8_1]: https://galileo.ai/blog/ai-agent-guardrails-framework

[^8_2]: https://www.qed42.com/insights/ai-guardrails-building-safe-and-reliable-llm-applications

[^8_3]: https://arxiv.org/html/2408.01452v1

[^8_4]: https://arxiv.org/abs/2408.01452

[^8_5]: https://arxiv.org/html/2601.18491v1

[^8_6]: https://cleanlab.ai/blog/ai-agent-safety/

[^8_7]: https://www.leanware.co/insights/llm-guardrails

[^8_8]: https://toloka.ai/blog/essential-ai-agent-guardrails-for-safe-and-ethical-implementation/


---

# please create a detailed handover document.  Leave out the stuff that isn't relevant to understanding ""The main functional domains in HOOKS_CATALOG.md are: \# Domain Hook Count Description 1 Truth \& Evidence 12 Block diagnostic claims without verification, track evidence 2 Quality \& Behavioral 6 Detect overconfidence, sycophancy, lazy closure, work avoidance 3 Constitutional Patterns 5 Assumption audit, anti-sycophancy, reflexion validation 4 Code Protection 5 Syntax gates, hook protection, TDD enforcement, Catch-22 detection 5 Investigation \& Research 3 Block modifications without reading first, speculation detection 6 Path \& File Safety 5 Path resolution, file locking, shell complexity, semantic routing 7 Task \& Session Management 5 Task coordination, session tracking, CKS accumulation, checkpoints 8 Cognitive Frameworks 2 Solo dev injection, goal anchoring, diagnostic frameworks 9 Skill \& Workflow Enforcement 6 Slash command enforcement, /v workflow state tracking 10 Observability \& Logging 5 System 2 debugging, failure recording, outcome validation 11 Formatting \& Style 2 Auto-formatting (ruff/prettier), command suggestions 12 CKS (Constitutional Knowledge System) 4 Decision capture, memory injection, automatic storage" I know my system is organic, but it's confusing. How can I start making it logical, and plugging the holes it in?

"

Below is a focused handover doc for the current domain model and how to make it logical and less leaky, without unrelated background.

***

## 1. Current domain model (what exists today)

Your HOOKS_CATALOG.md organizes hooks into 12 functional domains:

1. Truth \& Evidence – 12 hooks
Block diagnostic claims without verification, track evidence.
2. Quality \& Behavioral – 6 hooks
Detect overconfidence, sycophancy, lazy closure, work avoidance.
3. Constitutional Patterns – 5 hooks
Assumption audit, anti‑sycophancy, reflection validation.
4. Code Protection – 5 hooks
Syntax gates, hook protection, TDD enforcement, Catch‑22 detection.
5. Investigation \& Research – 3 hooks
Block modifications without reading first, speculation detection.
6. Path \& File Safety – 5 hooks
Path resolution, file locking, shell complexity, semantic routing.
7. Task \& Session Management – 5 hooks
Task coordination, session tracking, CKS accumulation, checkpoints.
8. Cognitive Frameworks – 2 hooks
Solo‑dev injection, goal anchoring, diagnostic frameworks.
9. Skill \& Workflow Enforcement – 6 hooks
Slash command enforcement, `/v` workflow state tracking.
10. Observability \& Logging – 5 hooks
System‑2 debugging, failure recording, outcome validation.
11. Formatting \& Style – 2 hooks
Auto‑formatting (ruff/prettier), command suggestions.
12. CKS (Constitutional Knowledge System) – 4 hooks
Decision capture, memory injection, automatic storage.

This evolved organically around specific hooks and problems, so domains partially overlap (e.g., Quality \& Behavioral vs Constitutional Patterns vs Cognitive Frameworks) and some are really *capabilities* (CKS) rather than domains. This makes it harder for agents to reason about “which guardrails should apply when and why,” compared to the more structured guardrail frameworks used in production systems.[^9_1][^9_2]

***

## 2. Target mental model (what “logical” should look like)

The goal is to turn the domains into a **clean control model** that answers three questions:

1. What kind of risk is this about?
(truth, behavior, code safety, grounding, workflow, observability, style).
2. Where in the agent lifecycle does it apply?
(input, planning, tool selection, tool execution, post‑execution, output).[^9_2]
3. How does it act?
(log, warn, block, rewrite, annotate).[^9_1]

Your domains should become “buckets of related risks,” not catch‑alls. This matches how domain‑specific guardrails and multi‑layer architectures are described in recent guides and papers.[^9_3][^9_4][^9_2]

***

## 3. Normalized domain set (minimal structural changes)

You can make your system much more logical by merging a few overlapping domains and reinterpreting CKS as a cross‑cutting flag instead of its own domain.

Recommended normalized domains:

1. Truth \& Evidence
Factual correctness, verification, provenance, “no unverified diagnostics.”
2. Behavior \& Constitutional
Merge Quality \& Behavioral + Constitutional Patterns.
Reasoning style, overconfidence, sycophancy, assumption audits, reflection quality.
3. Code \& File Safety
Merge Code Protection + Path \& File Safety.
Syntax safety, hook protection, path resolution, file locking, shell/sandbox complexity.
4. Investigation \& Research
“Read before write,” “observe before act,” speculation detection.
5. Tasks, Roles \& Cognitive Frames
Merge Task \& Session Management + Cognitive Frameworks.
Task coordination, role modeling (solo vs team), goal anchoring, session checkpoints, CKS accumulation.
6. Skill \& Workflow Enforcement
Slash command enforcement, workflow state tracking, process discipline.
7. Observability \& Logging
System‑2 debugging, outcome validation, failure recording, traces.
8. Formatting \& Style
Output formatting, style, auto‑formatting hooks.

CKS (Constitutional Knowledge System):

- Treat this as a **capability flag** (`uses_cks: true`) on hooks in any domain, not its own domain.

This reduces conceptual duplication while preserving all of your existing behaviors. It also aligns better with external practice, where guardrails are grouped into content/behavior, tool/action safety, and observability layers.[^9_2][^9_1]

***

## 4. Hook metadata schema (make the system queryable)

To plug holes and make the system usable by agents, each hook needs minimal structured metadata. You can embed this as YAML in HOOKS_CATALOG.md or keep a separate `hooks.yaml`.

For each hook, add:

- `id`: stable identifier.
- `domain`: one of the normalized domains.
- `phase`: `input | planning | tool_selection | tool_execution | post_execution | output`.
- `risk_type`: one or more of:
    - `truth`, `behavior`, `code_safety`, `grounding`, `workflow`, `session`, `observability`, `style`.
- `action_type`: `block | warn | log | rewrite | annotate`.
- `applies_to`: e.g. `["code_edit", "daemon_config", "task_spec", "multi_agent_context", "diagnostic_report"]`.
- `uses_cks`: `true | false`.
- Optional `policy`: small, domain‑specific key/values (e.g., “min_observation_tools: 1”).

Example (Truth \& Evidence hook):

```yaml
id: "Stop_unverified_diagnostics"
domain: "Truth & Evidence"
phase: "output"
risk_type: ["truth", "epistemic"]
action_type: "block"
applies_to: ["diagnostic_report"]
tags: ["diagnostic_claims", "verification_required"]
uses_cks: true
policy:
  quantitative_claims: "require_source_or_mark_unknown"
  allowed_sources:
    - "code_search"
    - "domains.yaml"
    - "SYSTEM_TOPOLOGY.md"
```

Once you have this schema, agents and debugging tools can answer questions like:

- “What blocking hooks apply in the planning phase for code edits?”
- “Do we have any grounding hooks that apply before editing hook files?”

This is very close to how domain‑specific guardrail models are described in applied work: a structured layer that scores/filters outputs/actions according to domain rules.[^9_4][^9_3]

***

## 5. Systematic hole‑finding (map domains to failure modes)

You already identified key “failure domains” from your own incidents:

- Grounding/observation: assuming files/configs without reading them.
- Epistemic: unverified facts (latency, counts).
- Cross‑agent trust: accepting other LLMs’ claims without cross‑check.
- Spec/contract drift: docs/solution vs implementation.
- Roles/system: mis‑modeling your setup (solo dev vs “human + assistants”).
- Execution control: asking instead of checking, skipping invariants.

Use the normalized domains and hook metadata as a grid:

1. Create a small table: rows = failure modes above, columns = domains.
2. For each cell, list existing hooks (via `domain`, `risk_type`, `phase`, `applies_to`).
3. If a cell is empty where you expect coverage, that is a **hole**.

Examples:

- Grounding + Investigation \& Research:
    - Expect: at least one `block` hook in `phase=tool_execution`, `applies_to=["code_edit", "config_edit"]` enforcing “read authority file before write.”
    - If missing, design exactly one new hook to fill it.
- Epistemic + Truth \& Evidence:
    - Expect: hook scanning for quantitative claims and checking evidence/tool usage.
- Cross‑agent trust + Truth \& Evidence / Tasks, Roles \& Cognitive Frames:
    - Expect: hook that refuses to adopt claims sourced from external agents without provenance.

This kind of structured mapping (domain → risk → phase) is how external guides recommend designing and validating guardrail coverage.[^9_5][^9_1][^9_2]

***

## 6. Domain‑level defaults (control knobs for agents)

To make it easy for agents and orchestration to work with your domains, add a tiny per‑domain policy block (in `domains.yaml` or top of HOOKS_CATALOG.md):

Per domain:

- `default_autonomy_level`: `0 log`, `1 warn`, `2 soft-block`, `3 hard-block`.
- `blast_radius`: `low | medium | high`.
- `human_escalation`: `true | false`.
- Optional: `spec_drift_handling`: `none | warn | block`.

Example:

```yaml
domain: "Truth & Evidence"
default_autonomy_level: 3
blast_radius: "high"
human_escalation: true
spec_drift_handling: "block"

domain: "Code & File Safety"
default_autonomy_level: 3
blast_radius: "high"
human_escalation: true
spec_drift_handling: "block"

domain: "Behavior & Constitutional"
default_autonomy_level: 1
blast_radius: "medium"
human_escalation: false
```

This lets you:

- Crank safety up (e.g., for editing enforcement hooks or daemon configs).
- Run lighter guardrails for low‑risk tasks (docs, comments).

It also matches how external platforms expose guardrail tiers/autonomy levels for agents.[^9_6][^9_7][^9_1]

***

## 7. Concrete, minimal next steps

To start making the system logical and plug holes without a rewrite:

1. **Normalize the domains on paper**
    - Decide on the merged set (as in section 3).
    - In HOOKS_CATALOG.md, re‑label existing domains accordingly.
    - Mark CKS as `uses_cks: true` per hook instead of its own domain.
2. **Add metadata for one or two domains first**
    - Start with:
        - Truth \& Evidence.
        - Investigation \& Research.
    - For each hook in those domains, add:
        - `phase`, `risk_type`, `action_type`, `applies_to`, `uses_cks`, small `policy`.
3. **Do a quick hole‑finding pass**
    - For your known failure modes:
        - Confirm at least one hook exists in an appropriate domain/phase.
        - If not, create a minimal “patch hook” to fill that specific gap.
4. **Add domain‑level defaults**
    - Create a `domains.yaml` with per‑domain defaults (`default_autonomy_level`, etc.).
    - Wire a tiny helper script/tool that:
        - Reads `domains.yaml` + hook metadata.
        - Given `phase` + `task_type`, tells the agent “these domains and hooks apply.”
5. **Iterate outward**
    - Once Truth \& Evidence + Investigation \& Research are structured, apply the same pattern to:
        - Code \& File Safety.
        - Tasks, Roles \& Cognitive Frames.
        - Skill \& Workflow Enforcement.
        - Observability \& Logging.

You keep your organic, battle‑tested hooks, but wrap them in a **logical, queryable, and complete domain model** that both humans and agents can reason about. This is exactly the trajectory described in domain‑specific guardrail work: start from organic rules, then normalize, tag, and systematically cover your risk surface.[^9_3][^9_4][^9_2]
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://galileo.ai/blog/ai-agent-guardrails-framework

[^9_2]: https://www.qed42.com/insights/ai-guardrails-building-safe-and-reliable-llm-applications

[^9_3]: https://arxiv.org/abs/2408.01452

[^9_4]: https://arxiv.org/html/2408.01452v1

[^9_5]: https://www.confident-ai.com/blog/llm-guardrails-the-ultimate-guide-to-safeguard-llm-systems

[^9_6]: https://aws.amazon.com/bedrock/guardrails/

[^9_7]: https://www.datadoghq.com/blog/llm-guardrails-best-practices/

[^9_8]: https://www.reco.ai/hub/guardrails-for-ai-agents

[^9_9]: https://frontegg.com/blog/ai-agent-governance-starts-with-guardrails

[^9_10]: https://www.tredence.com/blog/data-guardrails-in-agentic-ai-deployment

[^9_11]: https://uxplanet.org/guardrails-for-ai-agents-24349b93caeb

[^9_12]: https://www.agno.com/blog/guardrails-for-ai-agents

[^9_13]: https://www.guardrailsai.com

[^9_14]: https://theagentarchitect.substack.com/p/implementing-guardrails-ai-agent-systems

[^9_15]: https://aclanthology.org/2025.naacl-industry.15/


---

# Example implementation of Truth \& Ethics domain guardrails

Below is a concrete “Truth \& Ethics” domain design you can lift into your system. I’ll keep it implementation‑oriented and close to the way production guardrail frameworks do factual + ethical rails.[^10_1][^10_2][^10_3][^10_4]

***

## 1. Domain definition (Truth \& Ethics)

In your world this would replace/extend **Truth \& Evidence** to explicitly include ethics:

```yaml
# domains.yaml
truth_ethics:
  id: "truth_ethics"
  name: "Truth & Ethics"
  description: "Factual accuracy, provenance, and ethical constraints (harm, bias, privacy)."
  risk_type: ["truth", "epistemic", "ethical"]
  default_autonomy_level: 3          # hard-block by default
  blast_radius: "high"
  human_escalation: true
  phases: ["planning", "tool_execution", "output"]
  authority_files:
    - path: "P:/.claude/SYSTEM_TOPOLOGY.md"
      description: "System authority mapping and ethical principles"
    - path: "P:/.claude/policies/ETHICS_CHARTER.md"
      description: "Project-specific ethics and safety charter"
    - path: "P:/.claude/hooks/domains.yaml"
      description: "Guardrail configuration"
  hooks:
    - "PrePlanning_truth_ethics_scan.py"
    - "Stop_unverified_or_harmful_output.py"
    - "PostToolUse_ethics_evidence_audit.py"
```

The domain owns:

- Truth \& provenance (no unjustified factual claims).[^10_3][^10_5]
- Ethical rules: safety, bias/fairness, privacy, and domain‑specific “do not do X” boundaries.[^10_6][^10_2][^10_4][^10_1]

***

## 2. Hook 1: Pre‑planning truth/ethics scanner (lightweight, cheap)

Purpose: catch obviously unsafe topics and mark where strong rails must apply before you even plan.

```python
# PrePlanning_truth_ethics_scan.py
"""
Lightweight pre-planning scan for high-risk ethical topics and factual sensitivity.
Adds flags into context so later hooks can enforce stricter rules.
"""

import json
import sys
import re

HIGH_RISK_TOPICS = [
    r"\bsuicide\b", r"\bself[- ]harm\b",
    r"\bterrorism\b", r"\bmake a bomb\b",
    r"\bkill (myself|himself|herself|them)\b",
    r"\binsider trading\b", r"\btax fraud\b",
]

SENSITIVE_FACTUAL_TOPICS = [
    r"\bmedical diagnosis\b", r"\bdiagnose me\b",
    r"\binvestment advice\b", r"\bbuy/sell this stock\b",
]

def detect(patterns, text):
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)

def main():
    data = json.loads(sys.stdin.read())
    task = data.get("task_spec", "") or data.get("user_input", "")

    flags = {
        "truth_ethics_high_risk": False,
        "truth_ethics_sensitive_facts": False,
    }

    if detect(HIGH_RISK_TOPICS, task):
        flags["truth_ethics_high_risk"] = True

    if detect(SENSITIVE_FACTUAL_TOPICS, task):
        flags["truth_ethics_sensitive_facts"] = True

    # Hook contract: emit annotations for downstream hooks/orchestrator.
    print(json.dumps({
        "continue": True,
        "annotations": flags
    }))

if __name__ == "__main__":
    main()
```

Effect:

- Marks conversations as `high_risk` or `sensitive_facts` so later guardrails (fact‑checking, content moderation, HITL routing) can be stricter, similar to multi‑layer designs used in industry.[^10_7][^10_1][^10_3]

***

## 3. Hook 2: Stop unverified or harmful output (hard block)

Purpose: block:

- Quantitative/factual claims with no evidence.
- Ethically harmful content (violence, self‑harm, hate, illegal instructions), using a classifier or rules.[^10_2][^10_1][^10_6][^10_3]

Below is a rule‑based skeleton you can later augment with a classifier:

```python
# Stop_unverified_or_harmful_output.py
"""
Blocks outputs that (a) make unverified factual claims in sensitive domains,
or (b) contain clearly harmful or unethical content.
"""

import json
import sys
import re

# Simple patterns – you can swap these for a classifier score later.
HARMFUL_PATTERNS = [
    r"\bkill yourself\b", r"\bhow to make a bomb\b",
    r"\bshoot (them|him|her|someone)\b",
    r"\bcommit suicide\b",
]

HATE_PATTERNS = [
    r"\b(all|most|every) (Jews|Muslims|Christians|Black people|women|men) are\b",
]

QUANT_PATTERNS = [
    r"\b\d+(\.\d+)?\s*ms\b",
    r"\b\d+(\.\d+)?\s*%\b",
    r"\b\d+(\.\d+)?\s*(seconds?|minutes?|hours?)\b",
]

EVIDENCE_TOOLS = {"Read", "Glob", "Grep", "Bash", "HTTP", "Search"}

def has_pattern(patterns, text):
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)

def extract_quants(text):
    quants = []
    for p in QUANT_PATTERNS:
        quants.extend(re.findall(p, text, flags=re.IGNORECASE))
    return quants

def used_evidence_tools(tools_used):
    return any(t.get("name") in EVIDENCE_TOOLS for t in tools_used or [])

def main():
    data = json.loads(sys.stdin.read())
    response = data.get("response", "") or ""
    tools_used = data.get("tools_used", [])
    annotations = data.get("annotations", {})  # from PrePlanning hook

    # 1) Ethical blocking (harm, hate, illegal content)
    if has_pattern(HARMFUL_PATTERNS + HATE_PATTERNS, response):
        print(json.dumps({
            "allow": False,
            "reason": "ETHICAL_VIOLATION",
            "message": "Response appears to encourage harm or hate."
        }))
        sys.exit(2)

    # 2) Truth / evidence blocking for sensitive factual domains
    high_risk = annotations.get("truth_ethics_high_risk", False)
    sensitive_facts = annotations.get("truth_ethics_sensitive_facts", False)
    quants = extract_quants(response)

    if (high_risk or sensitive_facts) and quants and not used_evidence_tools(tools_used):
        print(json.dumps({
            "allow": False,
            "reason": "UNVERIFIED_SENSITIVE_FACTS",
            "message": "Quantitative claims in a sensitive/ethical domain without supporting evidence."
        }))
        sys.exit(2)

    # 3) Otherwise, allow
    print(json.dumps({
        "allow": True,
        "reason": "OK"
    }))

if __name__ == "__main__":
    main()
```

You can later swap the regex‑based ethical checks for:

- A small toxicity / self‑harm / hate speech classifier, or
- A “policy LLM” that labels candidate outputs, as described in domain‑specific guardrail work.[^10_4][^10_1][^10_2]

***

## 4. Hook 3: Post‑tool‑use ethics + evidence audit (soft control)

Purpose: log and optionally warn when actions in high‑risk domains are taken without:

- Looking at authoritative sources.
- Respecting ethical constraints (e.g., trying to edit sensitive data).

```python
# PostToolUse_ethics_evidence_audit.py
"""
Audits tool use for truth/ethics: were authority files consulted, and
were risky actions taken on sensitive resources?
"""

import json
import sys
from pathlib import Path

AUTHORITY_FILES = [
    "P:/.claude/SYSTEM_TOPOLOGY.md",
    "P:/.claude/policies/ETHICS_CHARTER.md",
]

SENSITIVE_RESOURCES = [
    "prod_db://patients",
    "prod_db://financial_accounts",
]

def used_authority_file(tools_used):
    for t in tools_used or []:
        inp = t.get("input", "") or ""
        if any(auth in inp for auth in AUTHORITY_FILES):
            return True
    return False

def touched_sensitive_resource(tool_name, tool_input):
    target = (tool_input or "").lower()
    return any(res.lower() in target for res in SENSITIVE_RESOURCES)

def main():
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input", "")
    tools_used = data.get("tools_used", [])

    warnings = []

    # If we touched a sensitive resource, ensure authority consulted
    if touched_sensitive_resource(tool_name, tool_input) and not used_authority_file(tools_used):
        warnings.append("SENSITIVE_RESOURCE_WITHOUT_AUTHORITY_CONSULTED")

    result = {}
    if warnings:
        result["warning"] = ";".join(warnings)
        result["log"] = {
            "domain": "truth_ethics",
            "issues": warnings
        }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

This matches the “auditability and transparency” requirement in ethical guardrails: you can reconstruct why a decision was made and whether policies were followed.[^10_1][^10_6]

***

## 5. Hook metadata for this domain

In your HOOKS_CATALOG.md, you’d document these hooks with machine‑readable fields so agents can discover and honor them:

```yaml
# Truth & Ethics domain hooks

- id: "PrePlanning_truth_ethics_scan"
  domain: "Truth & Ethics"
  phase: "planning"
  risk_type: ["truth", "ethical"]
  action_type: "annotate"
  applies_to: ["all_tasks"]
  uses_cks: false

- id: "Stop_unverified_or_harmful_output"
  domain: "Truth & Ethics"
  phase: "output"
  risk_type: ["truth", "epistemic", "ethical"]
  action_type: "block"
  applies_to: ["all_responses"]
  uses_cks: true

- id: "PostToolUse_ethics_evidence_audit"
  domain: "Truth & Ethics"
  phase: "post_execution"
  risk_type: ["truth", "ethical", "observability"]
  action_type: "log"
  applies_to: ["tool_execution"]
  uses_cks: false
```

Agents can now:

- Query: “Give me all `block` hooks in ‘Truth \& Ethics’ for `phase=output`.”
- Change behavior when `truth_ethics_high_risk` is set.

***

## 6. How this plugs into your existing domains

Given your current taxonomy:

- This **replaces/extends `Truth & Evidence`** with an explicit ethical layer.
- It cooperates with:
    - **Investigation \& Research** (grounding: read before write).
    - **Code \& File Safety** (don’t touch sensitive systems unsafely).
    - **Observability \& Logging** (log all truth/ethics violations).

This structure aligns with how external systems define fact‑checking, hallucination, moderation, and ethical rails as separate but coordinated layers around agents.[^10_2][^10_3][^10_4][^10_1]

If you want, I can next:

- Add a small `ETHICS_CHARTER.md` skeleton your hooks can reference, or
- Show how to adapt `Stop_unverified_or_harmful_output.py` to consult project‑specific policy tags (e.g., no investment advice, no medical diagnosis).
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://toloka.ai/blog/essential-ai-agent-guardrails-for-safe-and-ethical-implementation/

[^10_2]: https://arxiv.org/html/2408.01452v1

[^10_3]: https://aws.amazon.com/blogs/machine-learning/build-safe-and-responsible-generative-ai-applications-with-guardrails/

[^10_4]: https://www.bluebash.co/blog/ethical-ai-guardrails-customer-facing-agentic-ai/

[^10_5]: https://www.datacamp.com/blog/llm-guardrails

[^10_6]: https://www.tredence.com/blog/ethical-considerations-and-data-guardrails

[^10_7]: https://www.leanware.co/insights/llm-guardrails

[^10_8]: https://towardsai.net/p/machine-learning/the-complete-guide-to-guardrails-building-ai-agents-that-wont-go-rogue

[^10_9]: https://www.electricmind.com/whats-on-our-mind/7-best-practices-for-building-a-responsible-ai-agent-governance-framework

[^10_10]: https://tepperspectives.cmu.edu/all-articles/the-ethical-challenges-of-ai-agents/

[^10_11]: https://arxiv.org/html/2411.14442v1

[^10_12]: https://unit42.paloaltonetworks.com/comparing-llm-guardrails-across-genai-platforms/

[^10_13]: https://www.akira.ai/blog/guardrails-with-agentic-ai

[^10_14]: https://www.examcollection.com/blog/architecting-trust-the-genesis-of-guardrails-in-amazon-bedrock/

[^10_15]: https://www.linkedin.com/posts/luizajarovsky_ai-aiagents-aigovernance-activity-7299874629043580930-5OxT


---

# “Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.

Filename requirements:

Include: product (claude-code), main feature (hooks), key hook (userpromptsubmit), platform if relevant (e.g. windows), and any special focus (e.g. async, debug).

Use kebab-case with underscores between major sections, and append today’s date as YYYY-MM-DD.

Return only one filename string.

Topic index requirements:

5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.

Each bullet: SectionTitle – short description.

Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

claude-code-hooks_userpromptsubmit-windows_guardrails-domain-modeling-truth-evidence-investigation_research-cks_2026-02-09

- DomainModelOverview – Current organic hook domains in HOOKS_CATALOG and why they’re confusing for agents.
- NormalizedDomains – Merging overlapping domains into a smaller, logical set (Truth \& Evidence, Behavior \& Constitutional, Code \& File Safety, etc.).
- HookMetadataSchema – Per-hook YAML fields (domain, phase, risk_type, action_type, applies_to, uses_cks) to make guardrails machine-queryable.
- FailureModesMapping – Mapping agent failure modes (grounding, epistemic, cross-agent trust, spec drift, roles, execution) onto domains and hooks.
- TruthEthicsDomain – Design and example implementation of a Truth \& Ethics/Truth \& Evidence domain with factual and ethical guardrails.
- InvestigationResearchDomain – Read-before-write and observe-before-act guardrails for investigation and research tasks.
- DomainPolicies – Domain-level defaults (autonomy levels, blast radius, spec_drift_handling, human escalation) as a control surface.
- CKSIntegration – Treating CKS as a cross-cutting capability flag rather than a standalone domain.
- ClaudeCodeHooksUsage – Patterns for using PreToolUse, PostToolUse, Stop hooks with domains, especially around userpromptsubmit flows.
- SystemTopologyManifests – Using SYSTEM_TOPOLOGY and authority files (skills, hooks, daemon) as ground truth for agents and hooks.
- DocAndSpecDrift – Guardrails for keeping solution docs, specs, and hook implementations aligned over time.
- AgentWorkflowDesign – Structuring multi-phase agent workflows (planning, tool_selection, execution, output) around the domain model.

