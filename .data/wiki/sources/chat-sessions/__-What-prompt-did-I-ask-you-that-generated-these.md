<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# "

❯ What prompt did I ask you that generated these new findings?

● Your prompt was:

▎ "Can you do a critical thinking, logical review of all the code in handoff to make sure that states and edge cases are
accounted for properly?"

That request generated the critical review findings I just presented, including:

- 🔴 State transition validation missing in mark_snapshot_status()
- 🟠 TOCTOU in evidence freshness check
- 🟠 Decision ID collision possibility
- 🟢 Transcript path existence validation gap
"

I thought we had finished a project, and then it occurred to me to ask the above question to Claude Code. And it came up with new findings. Why

Because you changed the *question*, you changed what the model was optimizing for, which in turn changed which parts of the code it attended to and what kinds of flaws it searched for.[^1_1][^1_2]

### What changed cognitively for the model

When you asked something like “is this finished?” or implicitly treated the project as done, the model’s job was close to “sanity-check and confirm adequacy.” That tends to produce:

- Shallow pattern-matching: “Does this look like typical, reasonable code for this domain?”[^1_3]
- Local correctness focus: individual functions, obvious bugs, style, simple invariants.
- Confirmation bias analogue: searching mostly for evidence that the code is acceptable rather than for ways it might still fail.[^1_4]

When you then asked:

> “Can you do a **critical thinking, logical review** of all the code in handoff to make sure that **states and edge cases are accounted for properly**?”

you:

- Gave it an explicit *task frame*: “systematic logical review,” not “quick review”.[^1_1]
- Specified **states** and **edge cases**, which primes it to look for: missing state transitions, unreachable states, illegal transitions, gaps in validation, race/TOCTOU windows, identifier uniqueness, etc.[^1_5][^1_6]
- Shifted it into a “find failure modes” mindset, more like a tester using heuristic oracles than a stylistic reviewer.[^1_5]

So it started asking itself different internal questions, like:

- “What are the allowed states? Are all transitions legal and validated?” → “State transition validation missing in `mark_snapshot_status()`.”
- “Can timing or ordering create inconsistent views?” → “TOCTOU in evidence freshness check.”
- “What invariants should hold across calls?” → “Decision ID collision possibility.”
- “What external contracts might be assumed but not enforced?” → “Transcript path existence validation gap.”

There’s empirical work on code review that backs this up: the *questions* a reviewer asks strongly shape which defects they notice. When the “question set” shifts from “is this fine?” to “where can this break under different state timelines?” you expose a different defect surface.[^1_2]

### Why these particular issues appeared “late”

A few specific reasons those findings tend to only surface under a more adversarial / logical prompt:

- **State-transition bugs are emergent**: They rarely show up in isolated snippets; you have to track the state machine over time and across functions, which is exactly what your “states and edge cases” wording told it to do.
- **TOCTOU and race-like issues are non-local**: You need to reason about time, ordering, and concurrent actors, not just code paths; that almost never happens under a generic “does this look good?” review.[^1_6]
- **Identifier collisions require model-based thinking**: You have to imagine sequences (multiple decisions created over time, ID spaces, storage guarantees) instead of just checking syntax and basic logic.
- **Validation gaps (like transcript paths)** require imagining the environment being hostile or imperfect, i.e., treating every external input and file path as untrusted. That’s a different mental mode than “assuming happy-path correctness.”[^1_3]

Those are exactly the kinds of defects human reviewers also miss until they adopt a different review strategy or checklist.[^1_6][^1_3][^1_5]

### What this implies for how you should work with Claude Code

FACT (high confidence, based on software testing and code-review literature, plus LLM behavior analyses): The way you phrase prompts materially changes the *defect class* the model searches for; broad, generic review prompts systematically miss deeper state, timing, and adversarial issues that more targeted prompts can reveal.[^1_2][^1_3][^1_1][^1_5][^1_6]

CONSENSUS: Treating LLMs like junior reviewers/testers benefits from the same tools we use with humans: explicit review checklists, multiple passes with different “lenses” (API contracts, states, concurrency, security, I/O validation, failure handling), and adversarial framing.[^1_3][^1_1][^1_5][^1_6]

SPECULATION (moderate confidence, but fits your experience): Your earlier interactions likely gave Claude Code a “wrap this up” frame—maybe you were asking for final touches, documentation, or a last quick review. That nudged it toward endorsement rather than deep adversarial analysis, so the model *didn’t even look* at the handoff code from a state-machine and TOCTOU perspective until you explicitly requested that lens.

### Concrete next step you can systematize

If you want this kind of thing to *not* depend on you having a late-stage idea for a better prompt, you can bake the “lens” into your workflow:

- Maintain a short, reusable **checklist of review prompts**, each targeting a different defect class (states/edges, concurrency/TOCTOU, ID/uniqueness/invariants, I/O and validation, failure and rollback, security/abuse).
- Run Claude Code through multiple passes (possibly as separate tools or hooks) with each lens, and log findings per lens. This mimics multiple human reviewers with different specialties and reduces the chance that a single “finish this up” prompt leaves whole categories of bugs untouched.[^1_1][^1_5][^1_6]

Would it be useful if I drafted a minimal, re-usable prompt/checklist set for Claude Code that you can wire into a hook so that these deeper reviews run *by default* near the end of a project rather than ad hoc?
<span style="display:none">[^1_10][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.linkedin.com/pulse/prompting-purpose-critical-thinking-from-concept-code-brandee-nielsen-f2gme

[^1_2]: https://arxiv.org/html/2507.09637v1

[^1_3]: https://dzone.com/articles/ai-generated-code-critical-thinking

[^1_4]: https://www.youtube.com/watch?v=l7yxrXLoPJk

[^1_5]: https://www.linkedin.com/pulse/test-oracles-heuristic-strategies-software-testing-terrificminds-htn2c

[^1_6]: https://www.richard-seidl.com/en/blog/test-oracle-reference

[^1_7]: https://www.reddit.com/r/ChatGPT/comments/1jb3wft/the_leaked_system_prompt_has_people_extremely/

[^1_8]: https://www.thesignal.club/p/prompts-are-the-new-code

[^1_9]: https://www.dbreunig.com/2025/06/03/comparing-system-prompts-across-claude-versions.html

[^1_10]: https://simonwillison.net/2025/May/25/claude-4-system-prompt/


---

# yes please

Here’s a concrete, multi‑lens review checklist you can reuse as prompts or wire into hooks. Each “lens” is a separate pass you ask Claude Code to run.

***

## Overview: how to use this

Run these as distinct prompts on the same codebase:

1. State \& edge‑case lens
2. Identity \& invariants lens
3. I/O \& validation lens
4. Concurrency \& TOCTOU lens
5. Errors, logging \& observability lens
6. Tests \& coverage lens

This mirrors human code‑review checklists and testing oracles that deliberately look for different defect classes.[^2_1][^2_2][^2_3][^2_4][^2_5][^2_6]

***

## 1) State and edge‑case lens

Prompt:

> Take a **critical, adversarial pass** over the following code that implements handoff / workflows.
>
> 1. Enumerate all **states** and possible **state transitions** in this code (including implied ones).
> 2. For each transition, answer:
>    - Is this transition explicitly validated at the call site?
>    - Can this function be called in an **illegal state**, and what happens if it is?
> 3. List any missing validation, illegal or ambiguous transitions, or unreachable states.
> 4. For each issue, propose **minimal, concrete code changes** (checks, guards, or refactors) to enforce valid transitions and surface misuse early.
> 5. Pay special attention to “mark” / “update” functions like `mark_snapshot_status`, ensuring they cannot silently accept invalid state transitions.

This is tuned to catch exactly the kind of “state transition validation missing in `mark_snapshot_status()`” issue you saw.[^2_2][^2_5]

***

## 2) Identity and invariants lens (IDs, uniqueness, referential integrity)

Prompt:

> Perform a **logical review focused only on identifiers and invariants** in this codebase (decisions, snapshots, evidence, transcripts, jobs, etc.).
>
> 1. List all entities that have some sort of **ID** or key (decision IDs, snapshot IDs, run IDs, etc.).
> 2. For each, answer:
>    - How is the ID generated?
>    - What guarantees of **uniqueness** or stability exist (in code or storage)?
>    - What are the **invariants** that should always hold between related entities (e.g., 1‑to‑1 decision↔snapshot, 1‑to‑many, etc.)?
> 3. Identify any plausible **collision**, dangling reference, or invariant‑violation scenarios across calls, processes, or restarts.
> 4. Propose precise changes (e.g., switching to stronger ID sources, adding uniqueness checks, or enforcing referential integrity) with small diffs.

This aims straight at “decision ID collision possibility” and related invariant issues.[^2_3][^2_5]

***

## 3) I/O, paths, and validation lens

Prompt:

> Review this code **only from an I/O and validation perspective** (files, paths, network calls, user inputs, environment variables).
>
> 1. Enumerate all inputs and outputs: file paths, JSON, env vars, external services, CLI args, etc.
> 2. For each input:
>    - What assumptions does the code make (exists, readable, valid JSON, non‑empty, etc.)?
>    - Is that assumption checked explicitly and early?
> 3. Identify every place where:
>    - A path or resource (e.g., transcript path) is **used without verifying** it exists and is accessible.
>    - Errors are swallowed, logged vaguely, or converted into misleading states.
> 4. Propose concrete checks and error paths, especially for any transcript/evidence file handling, so that missing resources fail fast with clear diagnostics instead of silent corruption.

This is the lens that should repeatedly rediscover things like “transcript path existence validation gap.”[^2_5][^2_2][^2_3]

***

## 4) Concurrency and TOCTOU lens

Prompt:

> Assume this code might run in **concurrent or multi‑process** contexts, or in the presence of other tools modifying the same resources.
>
> 1. Identify all operations that have a **time gap** between “check” and “use” (e.g., freshness checks, existence checks, authorization checks).
> 2. For each, describe potential **TOCTOU** (Time‑Of‑Check / Time‑Of‑Use) problems: how could another process or later operation change the world between the check and the use?
> 3. Highlight code paths where multiple actors might read/write the same file, DB record, or directory.
> 4. Propose practical mitigations appropriate to this code (e.g., atomic writes, versioning, stronger freshness semantics, locks, or collapsing check+use).
> 5. Explicitly revisit any “evidence freshness” logic and describe failure modes if clocks drift, other components rewrite files, or checks are racy.

This focuses Claude on the “TOCTOU in evidence freshness check” and similar race‑style issues.[^2_4][^2_6][^2_5]

***

## 5) Errors, logging, and observability lens

Prompt:

> Review the code focusing **only** on error handling, logging, and observability.
>
> 1. For each public‑ish function or entrypoint, describe:
>    - What are its possible **failure modes**?
>    - How are they signaled (exception types, return values, logs)?
> 2. Flag any place where errors are swallowed, converted to generic messages, or where logs are too weak to debug a production issue.
> 3. Suggest specific, minimal improvements:
>    - More precise exceptions,
>    - Structured log messages with enough context (IDs, states, paths),
>    - Clear separation between operational logs and debugging noise.
> 4. Ensure that state‑transition or I/O failures cannot masquerade as success.

This ties into standard code‑review checklists around error handling and logging.[^2_1][^2_3][^2_5]

***

## 6) Tests and coverage lens

Prompt:

> Take a **test‑designer’s** view of this code. Do not propose refactors except where needed to make testing feasible.
>
> 1. List the **critical behaviors and invariants** that absolutely must be protected by tests (e.g., state machine rules, uniqueness of IDs, evidence freshness behavior, correct handling of missing transcripts).
> 2. For each, design minimal but strong **unit and integration tests**, including key edge cases (empty inputs, invalid states, concurrent modifications, restarts).
> 3. Identify any logic that is effectively **untested** or test‑hostile (e.g., tightly coupled to wall‑clock, filesystem, or globals) and propose targeted seams (injection, wrappers) to allow testing.
> 4. If tests already exist, map them to the behaviors above and note where important branches or failure modes remain untested.

This aligns with mainstream guidance that explicit coverage of edge cases and failure modes is part of a robust review.[^2_2][^2_3][^2_5]

***

## How to wire this into Claude Code hooks

Minimal, low‑friction pattern:

- Add a **UserPromptSubmit** hook that:
    - Detects when your message includes something like “final review”, “handoff done”, “project finished”, etc.
    - Injects a follow‑up instruction block telling Claude: “Before concluding this is finished, you must run through the following lenses as separate passes: [list lenses]. Ask me which lenses to run now.”
- Optionally add a **PreToolUse** or **PostToolUse** hook for Write/Read operations that:
    - Detects large or cross‑cutting edits to handoff code,
    - Drops in a short reminder like: “Once you think the handoff is ready, perform at least the State \& Edge‑case lens and the I/O \& validation lens before saying it’s complete.”

This uses checklists as “review oracles” embedded in your workflow, which is a well‑established technique in both testing and human code review.[^2_7][^2_6][^2_4][^2_1]

If you’d like, I can next give you a concrete `hooks.json` + a small Python dispatcher that recognizes “finalize/complete/handoff” prompts and programmatically appends whichever of these lens prompts you choose to enforce.
<span style="display:none">[^2_10][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://jellyfish.co/library/developer-productivity/peer-code-review-best-practices/

[^2_2]: https://blog.codacy.com/code-review-checklist

[^2_3]: https://www.gocodeo.com/post/the-ultimate-code-review-checklist

[^2_4]: https://www.softwaretestingmagazine.com/knowledge/oracles-in-software-testing/

[^2_5]: https://www.codeant.ai/blogs/code-review-process-guide

[^2_6]: https://www.ministryoftesting.com/articles/the-quality-and-testing-information-model

[^2_7]: https://docs.gitlab.com/development/code_review/

[^2_8]: https://dev.to/everettbutler/code-review-checklist-a-comprehensive-guide-cfh

[^2_9]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12306261/

[^2_10]: https://dl.acm.org/doi/10.1145/3756681.3756938


---

# I feel like I kind of got lucky What other best practice type questions should we ask for this context?

You can absolutely systematize this so it’s not “luck” next time. Here’s a compact set of high‑leverage, best‑practice questions tailored to handoff / workflow / stateful systems that you can turn into prompts or checklists.

***

## 1) Context and intent

Before deep review, force the model to align on the problem and design:

- “Summarize in your own words what this handoff/workflow system is supposed to do, who calls it, and what ‘done’ means for a run.”[^3_1][^3_2]
- “List the primary business workflows and the key states each one passes through.”[^3_3]
- “Does the current implementation actually match that intent, or are there mismatches or missing steps?”[^3_2][^3_1]

This prevents it from rubber‑stamping an implementation that doesn’t match the conceptual workflow.

***

## 2) State machine and lifecycle

For your context, this is core:

- “Enumerate all states and transitions for decisions/snapshots/evidence. Are there initial and terminal states clearly defined?”[^3_4][^3_3]
- “Are any transitions:
    - allowed but not validated,
    - impossible by design,
    - or missing but implied by requirements?”[^3_3]
- “Is there a single trusted place responsible for validating state transitions, or is this logic scattered?”[^3_4]

These questions drive the model to find the exact kind of state‑transition and ‘mark’‑function issues you just hit.

***

## 3) Data and identity (IDs, invariants, duplication)

To avoid silent corruption and collisions:

- “List all key entities and their identifiers. For each, what invariants must always hold (1‑1, 1‑many, uniqueness, monotonicity)?”[^3_5][^3_6]
- “Where could those invariants be violated across multiple runs, processes, or restarts?”
- “Is there any duplication of logic or data that could drift out of sync instead of relying on a single source of truth?”[^3_7]

You can phrase it as: “Act as an invariant checker. Hunt only for ID/invariant/duplication issues.”

***

## 4) I/O, validation, and contracts

To catch missing checks like the transcript path:

- “List every external dependency: files, paths, env vars, external services, CLI inputs.”[^3_6][^3_5]
- “For each, what assumptions are made, and where are they enforced vs. implicitly trusted?”
- “Which failure modes are currently:
    - validated and surfaced clearly,
    - silently ignored,
    - or converted into misleading ‘success’ states?”[^3_5]

Make it explicitly adversarial: “Assume paths might be missing or corrupted; how does the system behave?”

***

## 5) Concurrency, sequencing, and TOCTOU

For evidence freshness and similar:

- “Identify all points where the system does ‘check then act’ with a time gap. What can change between those steps?”[^3_8][^3_9]
- “Describe possible TOCTOU races involving evidence files, status flags, or decision records, especially when multiple workers/tools run concurrently.”[^3_8]
- “What minimal changes would make these operations atomic or at least detect staleness reliably?”[^3_9][^3_8]

This is just turning TOCTOU into an explicit question class the model must answer.

***

## 6) Security, abuse, and mis‑use

Even if this is “internal only,” it’s a rich source of bugs:

- “If a malicious or buggy caller tried to abuse this handoff API, how could they:
    - put the system into an invalid state,
    - cause data loss,
    - or exfiltrate sensitive info?”[^3_10][^3_6][^3_5]
- “What minimal guardrails or checks should be added to defend against obvious misuse?”

Security‑style questions often uncover validation and invariant gaps.

***

## 7) Simplicity, readability, and maintainability

To avoid clever but fragile workflows:

- “Is the intent of each module/function obvious? If not, what makes it hard to understand?”[^3_2][^3_7][^3_6]
- “Where is complexity accidental rather than essential to the workflow? What can be simplified or isolated?”[^3_7][^3_6]
- “Could existing utilities or patterns in this repo have been reused instead of re‑invented?”[^3_7]

These questions reduce entropy and future bug risk.

***

## 8) Tests and coverage

Turn “best practices” into concrete test‑design prompts:

- “What are the critical behaviors and invariants that must be protected by tests for this handoff system?”[^3_10][^3_6][^3_2]
- “For each, specify edge‑case tests: invalid states, double submissions, concurrent updates, missing files, restarts mid‑run.”[^3_2][^3_10]
- “Which important paths and failure modes currently lack test coverage, based on this design?”[^3_1][^3_2]

You can then ask: “Generate a minimal test matrix table for these behaviors.”

***

## 9) Meta‑questions to ask the model about itself

To avoid over‑trusting a single pass:

- “For this handoff code, which areas are you **least confident** about, and why?”[^3_11][^3_12]
- “If this system failed in production, what are the top 5 most likely root causes based on this code?”[^3_12][^3_11]
- “Given these findings, what new checklist items or prompts should we add so that similar issues are caught earlier next time?”[^3_11][^3_12]

These are prompt patterns (reflection, fact‑check list, retrospective) that improve LLM output quality over time.[^3_12][^3_11]

***

## One way to operationalize this

You could define a fixed set of “review modes” and then ask:

> “Run a **handoff review in modes: [states, invariants, I/O, TOCTOU, security]** and present issues grouped by mode, with severity and minimal fixes.”

Or wire them into hooks so that whenever you type something like “final handoff review,” Claude is instructed to run through a subset of these modes before telling you it’s done.

Would you prefer I now:
a) compress these into a single “master prompt” you can paste into Claude Code, or
b) structure them as JSON/markdown that a hook can inject as options (e.g., `mode: "state_machine"` etc.)?

<div align="center">⁂</div>

[^3_1]: https://google.github.io/eng-practices/review/reviewer/standard.html

[^3_2]: https://beyondtheloop.dev/code-review-checklist/

[^3_3]: https://learn.microsoft.com/en-us/archive/msdn-magazine/2008/february/building-state-machines-with-windows-workflow-foundation

[^3_4]: https://stackoverflow.com/questions/1966950/workflow-design-dilemma-state-machine-yes-or-no

[^3_5]: https://www.legitsecurity.com/aspm-knowledge-base/best-practices-for-code-review

[^3_6]: https://appfire.com/resources/blog/code-review-checklist

[^3_7]: https://www.darraghoriordan.com/2021/12/28/21-questiosn-how-to-do-valuable-code-reviews

[^3_8]: https://www.softwaretestingmagazine.com/knowledge/oracles-in-software-testing/

[^3_9]: https://www.ministryoftesting.com/articles/the-quality-and-testing-information-model

[^3_10]: https://axify.io/blog/code-review-checklist

[^3_11]: https://www.prompthub.us/blog/prompt-patterns-what-they-are-and-16-you-should-know

[^3_12]: https://dev.to/lymah/building-effective-prompts-and-workflows-for-code-review-with-goose-51m1


---

# Why certain code review checklist questions uncover bugs others miss and how to prioritize them

How to implement multi-pass code reviews effectively

Best tools for automating code review checklists

Common pitfalls to avoid in code review processes

Certain checklist questions expose different *categories* of bugs because they force reviewers (human or AI) to look at the code through distinct “lenses” instead of doing one blended, shallow pass. Below is a compact, practical breakdown answering all four of your bullets.[^4_1][^4_2][^4_3]

***

## 1) Why some questions find bugs others miss

Different questions activate different mental models and oracles:

- **Dimension‑specific focus**: A “Does this handle all states and transitions?” question makes you trace workflows and state machines, while “Are all inputs validated?” pushes you to hunt I/O and contract bugs.[^4_2][^4_4][^4_5]
- **Non‑local reasoning**: Questions about concurrency (“What can change between check and use?”) or invariants (“Can this ID collide?”) force you to think across files, time, and processes, catching bugs a line‑by‑line style review misses.[^4_6][^4_7][^4_1]
- **Perspective shift**: Security, performance, and testing questions are adversarial by design (“How could this be abused?” “What if input is worst‑case?”), which highlights issues you won’t see from a happy‑path or readability lens.[^4_8][^4_9][^4_10]

Prioritization strategy (for a workflow/handoff system like yours):

1. **Correctness \& safety first**
    - State/lifecycle questions
    - I/O \& validation
    - Concurrency/TOCTOU \& invariants[^4_10][^4_6][^4_8]
2. **Risk‑driven extras**
    - Security if any external input or secrets
    - Performance if it’s on hot paths or batch workflows[^4_9][^4_8][^4_10]
3. **Quality of life**
    - Readability, duplication/DRY, documentation, tests.[^4_11][^4_12][^4_13]

You prioritize questions by *impact if missed* (prod data loss vs. minor style issue) and *likelihood* in that code area (e.g., workflows = state/TOCTOU heavy).

***

## 2) How to implement multi‑pass code reviews effectively

Multi‑pass = several small reviews, each with a single focus, instead of one giant everything‑review.[^4_3]

Concrete pattern:

1. **Define 3–5 core lenses** for this repo (e.g., State \& invariants, I/O \& contracts, Concurrency/TOCTOU, Security, Tests). Each lens has 3–6 questions max.
2. **Apply them sequentially** to the same PR / code:
    - Pass 1: “Only state \& invariants; ignore naming/formatting.”
    - Pass 2: “Only I/O, validation, and external contracts.”
    - Pass 3: “Only concurrency/TOCTOU; assume multi‑worker.”
    - Pass 4: “Only tests \& observability.”[^4_1][^4_2][^4_3]
3. **Bookend with tests**: Many multi‑check systems run tests before and after automated review to ensure fixes didn’t regress behavior.[^4_3]
4. **Assign ownership**: In teams, different people or AIs own different passes (e.g., security specialist, performance reviewer).[^4_14][^4_15]

For AI‑assisted workflows:

- Use **separate prompts** or tools per lens, not one mega‑prompt. Tools like “dimension‑specific checks” are built exactly this way: 10–20 narrow checks run in sequence, each with a small spec.[^4_3]
- Enforce a **gate**: no “LGTM” until at least some mandatory passes are done (e.g., correctness + tests + security). This mirrors human quality gates and multi‑agent setups.[^4_15][^4_3]

***

## 3) Best tools for automating code review checklists

You want two layers: static/automated checks and AI‑assisted, checklist‑driven reasoning.

Static / automated layer (non‑AI):

- **Linters \& formatters** (ESLint, flake8/ruff, etc.): offload formatting, simple smells.
- **Static analyzers \& SAST**: SonarQube, Snyk Code, Codacy, etc., for patterns, security, and complexity metrics.[^4_16]
- **CI quality gates**: Many platforms (SonarQube, Codacy, GitLab CI rules) support blocking merges unless thresholds are met (coverage, vulnerabilities, code smells).[^4_17][^4_16]

AI‑assisted layer:

- **PR‑centric AI reviewers**:
    - GitHub Copilot PR review agent (inline suggestions, security/perf hints).[^4_16]
    - CodeRabbit, Qodo, and similar AI PR tools (summaries, smell detection, test suggestions).[^4_18][^4_16]
- **Multi‑check AI runners**: Frameworks that run multiple dimension‑specific AI checks in sequence (security, DRY, tests, performance, etc.), using different prompts per dimension.[^4_15][^4_3]

Where checklists fit:

- Many of these tools let you **configure rules or templates**, which you can align with your written checklist (e.g., “reject PR if no new tests for new behavior,” “warn if external input has no validation near the boundary”).[^4_10][^4_17][^4_16]
- For something like your Claude Code setup, you can emulate this with hooks or a multi‑agent script orchestrating different review prompts.[^4_15][^4_3]

***

## 4) Common pitfalls to avoid in code review processes

From industry practice and analyses of where reviews fail:[^4_19][^4_2][^4_14][^4_1]

- **Too broad, vague review passes**
    - “Take a look” produces shallow scanning; narrow questions produce deeper bug finding.
- **Checklists that are too long or unfocused**
    - 30+ items leads to checkbox fatigue; people skim or skip. Effective checklists are short and purpose‑specific.[^4_20][^4_2]
- **Over‑focusing on style, under‑focusing on behavior**
    - Lint can handle style; humans/LLMs should spend most time on correctness, invariants, and risks.[^4_21][^4_2]
- **No integration with tests and CI**
    - Reviews without enforced tests/coverage tend to approve code that compiles but isn’t robust.[^4_19][^4_1][^4_3]
- **Late, overloaded reviews**
    - Huge PRs and last‑minute reviews cause rubber‑stamping; smaller, continuous reviews (or multi‑pass automated checks) are more effective.[^4_14][^4_1]
- **Letting the same agent both write and sign off**
    - Multi‑agent systems and human processes work better when the reviewer is independent from the author, especially for risky changes.[^4_15]

***

## A concrete prioritization recipe for your context

For a workflow/handoff, stateful system:

1. **Mandatory questions per change** (block merge if not addressed):
    - “Are all state transitions valid, validated, and logged?”
    - “Are all external inputs/paths validated with clear failures?”
    - “Are new behaviors covered by tests, including edge cases?”[^4_12][^4_9][^4_11][^4_10]
2. **High‑risk features add**:
    - “Any TOCTOU or concurrency risk here?”
    - “Any security/privacy risks?”[^4_6][^4_8][^4_10]
3. **Continuous/lower‑priority**:
    - Readability, duplication, micro‑performance, docs.[^4_13][^4_12][^4_10]

Then build multi‑pass AI or human review around those tiers.

Would it help if I turned this into a small, repo‑agnostic YAML/JSON checklist schema (with “dimension”, “questions”, “priority”) that you could feed to your own Claude/Perplexity hooks or CI step?

<div align="center">⁂</div>

[^4_1]: https://blog.3d-logic.com/2024/09/06/do-code-reviews-find-bugs/

[^4_2]: https://smallbusinessprogramming.com/code-review-checklist-prevents-stupid-mistakes/

[^4_3]: https://alexmarquardt.com/ai-tools/checkloop-autonomous-code-review/

[^4_4]: https://learn.microsoft.com/en-us/archive/msdn-magazine/2008/february/building-state-machines-with-windows-workflow-foundation

[^4_5]: https://stackoverflow.com/questions/1966950/workflow-design-dilemma-state-machine-yes-or-no

[^4_6]: https://www.softwaretestingmagazine.com/knowledge/oracles-in-software-testing/

[^4_7]: https://www.ministryoftesting.com/articles/the-quality-and-testing-information-model

[^4_8]: https://www.legitsecurity.com/aspm-knowledge-base/best-practices-for-code-review

[^4_9]: https://axify.io/blog/code-review-checklist

[^4_10]: https://appfire.com/resources/blog/code-review-checklist

[^4_11]: https://google.github.io/eng-practices/review/reviewer/standard.html

[^4_12]: https://beyondtheloop.dev/code-review-checklist/

[^4_13]: https://www.darraghoriordan.com/2021/12/28/21-questiosn-how-to-do-valuable-code-reviews

[^4_14]: https://news.ycombinator.com/item?id=40851895

[^4_15]: https://www.reddit.com/r/ClaudeAI/comments/1qdgi36/i_built_a_multiagent_system_that_enforces_code/

[^4_16]: https://www.digitalocean.com/resources/articles/ai-code-review-tools

[^4_17]: https://docs.gitlab.com/development/code_review/

[^4_18]: https://www.youtube.com/watch?v=-cjqqXGN-0E

[^4_19]: https://ardalis.com/when-qa-keeps-finding-bugs/

[^4_20]: https://www.youtube.com/watch?v=jINoa1g8Gf8

[^4_21]: https://www.reddit.com/r/devops/comments/w5y7uc/to_make_code_review_better_shouldnt_we_have_a/


---

# Would using subagents, what specific roles with an adversarial perspective help with our outcomes?  How would we apply the sub-agent idea to the above discussion optimally.

Yes—subagents with explicitly adversarial roles map almost perfectly onto the lenses and checklists we’ve been talking about, and they help by specializing, disagreeing, and forcing justification.[^5_1][^5_2][^5_3][^5_4]

***

## 1) Which adversarial subagent roles are useful

For your workflow / handoff context, I’d define a small, **fixed team** of specialized agents, each instructed to be a bit hostile to “it’s fine”:

- **State Machine Prosecutor**
    - Mandate: Assume the state model is wrong; hunt for illegal transitions, missing states, and ambiguous lifecycles.
    - Adversarial angle: “Show me how this system can end up in a state that the code ‘thinks’ is valid but is actually impossible or unsafe.”
    - Backed by the idea that different review perspectives catch different bugs, especially in complex workflows.[^5_5][^5_6][^5_7]
- **Invariants \& Identity Auditor**
    - Mandate: Attack IDs, uniqueness, and relationships.
    - Adversarial angle: “Pretend you’re trying to create collisions, duplicate decisions, or dangling references. Where can you succeed?”
    - Mirrors how specialized security/static tools catch invariant violations general reviewers miss.[^5_8][^5_9][^5_10]
- **I/O \& Contracts Breaker**
    - Mandate: Break assumptions about files, paths, external services, env vars.
    - Adversarial angle: “Assume paths are missing, formats are wrong, and services are flaky; show how the system misbehaves or corrupts state.”
    - Similar to adversarial/fuzz testing for external interfaces.[^5_11][^5_12][^5_13]
- **Concurrency \& TOCTOU Attacker**
    - Mandate: Craft interleavings that defeat “check then act” logic (evidence freshness, file writes, flags).
    - Adversarial angle: “Assume multiple workers and crashes; where can timing create inconsistent or stale decisions?”
    - Inspired by how concurrency bugs are best surfaced by dedicated testing strategies.[^5_7][^5_12][^5_11]
- **Security \& Abuse Adversary**
    - Mandate: Treat all inputs as hostile; look for abuse of the handoff system itself (prompt injection, path traversal in transcripts, abusing IDs to access others’ data).
    - Adversarial angle: “What would a mildly talented attacker do to cause maximum damage with minimum access?”
    - Reflects security‑focused AI and human review roles.[^5_14][^5_15][^5_9][^5_16][^5_8]
- **Test Designer / QA Nemesis**
    - Mandate: Assume existing tests are insufficient.
    - Adversarial angle: “Design the smallest number of tests that would break this system if it’s fragile. Where are the blind spots?”
    - Based on multi‑check AI review setups where one agent only designs tests.[^5_4][^5_17][^5_7]

You can add softer roles (Readability/Docs, Performance) later, but the ones above are the heavy hitters for defects.

***

## 2) How to apply subagents optimally to this workflow

You want a **central orchestrator** (you or a top‑level agent) plus a small, stable team of subagents with well‑defined contracts.[^5_18][^5_19][^5_20][^5_4]

### Step 1: Orchestrator plan

- Orchestrator builds a simple **review plan** for each major change:
    - E.g., “Run State → I/O → TOCTOU → Security → Tests.”
- It passes the **same diff / context** to each subagent with its role description and checklist.
- It later **aggregates** findings, de‑duplicates, and asks agents to clarify conflicts or missing evidence.[^5_2][^5_18][^5_4]


### Step 2: Parallel or sequential passes

- **Parallel** when changes are localized and small:
    - Run all adversarial agents concurrently on the same diff, then merge results; this is how some AI PR tools and experimental multi‑check systems improve coverage.[^5_17][^5_21][^5_4]
- **Sequential** when there are deep interactions:
    - E.g., State Machine Prosecutor runs first, its findings are fed into Invariants Auditor and Concurrency Attacker so they can build on the state model rather than rediscover it.
    - Research on multi‑agent systems suggests a central planner plus sequential specialization improves reliability vs. free‑for‑all dialogue.[^5_19][^5_20][^5_18]

Given your complexity, I’d do:

1. State Machine Prosecutor
2. Invariants \& Identity Auditor (consumes 1’s state diagram)
3. I/O \& Contracts Breaker
4. Concurrency \& TOCTOU Attacker
5. Security \& Abuse Adversary
6. Test Designer / QA Nemesis

with 1–3 possibly in parallel for small patches.

### Step 3: Adversarial but *bounded* behavior

Multi‑agent research repeatedly warns that unconstrained adversarial agents can derail systems. For your use case:[^5_22][^5_18][^5_19]

- Give each subagent a **clear scope** (“Only comment on state transitions,” “Only comment on I/O and external contracts”).
- Require **evidence**: each finding must reference lines, functions, or explicit scenarios.
- Add a **credibility/weighting** layer in the orchestrator:
    - E.g., if multiple agents disagree, ask them to argue with concrete examples and then have the orchestrator or a “Referee” agent choose based on specificity and consistency.[^5_18][^5_22][^5_19]

This aligns with adversary‑resistant multi‑agent frameworks that use credibility scores and evaluation to avoid being misled.[^5_22][^5_19][^5_18]

***

## 3) Concrete wiring to your existing setup

Based on how you’re already using Claude Code:

- Define **subagent specs** (YAML or similar) for each role, like the `code-reviewer` and `security auditor` examples others use, but with your adversarial checklists baked in.[^5_3][^5_4]
- Implement a **“review coordinator”** script or hook that:
    - Detects when you ask for a “handoff review” or when a PR touches the workflow/handoff modules.
    - Invokes the relevant subagents (via CLI or API) with the diff and a role‑specific prompt.
    - Aggregates findings into a single report grouped by agent and severity.
- Optionally, integrate into CI:
    - For critical repos, CI runs a non‑interactive version of these agents on each PR and fails the pipeline when “Critical” issues are found.[^5_4][^5_17]

This is very close to the “autonomous multi‑check AI code review” setups described in recent guides and blog posts.[^5_17][^5_4]

***

## 4) How this improves outcomes vs. a single agent

Compared to one generalist agent with a long checklist, a multi‑subagent setup gives you:

- **Coverage**: Different agents focus on different risk surfaces; empirical reports show multi‑check systems catch more real bugs than single‑pass reviews.[^5_7][^5_4][^5_17]
- **Adversarial pressure**: It becomes normal for at least one agent to say “this is unsafe” and force justification or refactor, which is exactly what you want near “we’re done.”[^5_1][^5_2]
- **Scalability**: You can grow from 3 to 6+ lenses as needed without overloading any single prompt or human reviewer.[^5_21][^5_4][^5_17]

If you’d like, next I can sketch a concrete set of subagent “system prompts” for exactly these six roles, phrased so you can drop them into Claude Code subagent configs or an orchestrator script with minimal editing.

<div align="center">⁂</div>

[^5_1]: https://www.reddit.com/r/ClaudeCode/comments/1rnfn9p/protip_adversarial_reviews_are_stupidly_easy_and/

[^5_2]: https://www.linkedin.com/posts/joel-key_i-asked-an-ai-if-its-code-reviewer-was-doing-activity-7429876098013814784-vG-w

[^5_3]: https://www.eesel.ai/blog/claude-code-subagents

[^5_4]: https://www.digitalapplied.com/blog/ai-code-review-automation-guide-2025

[^5_5]: https://learn.microsoft.com/en-us/archive/msdn-magazine/2008/february/building-state-machines-with-windows-workflow-foundation

[^5_6]: https://stackoverflow.com/questions/1966950/workflow-design-dilemma-state-machine-yes-or-no

[^5_7]: https://blog.3d-logic.com/2024/09/06/do-code-reviews-find-bugs/

[^5_8]: https://www.legitsecurity.com/aspm-knowledge-base/best-practices-for-code-review

[^5_9]: https://appfire.com/resources/blog/code-review-checklist

[^5_10]: https://www.digitalocean.com/resources/articles/ai-code-review-tools

[^5_11]: https://www.softwaretestingmagazine.com/knowledge/oracles-in-software-testing/

[^5_12]: https://www.ministryoftesting.com/articles/the-quality-and-testing-information-model

[^5_13]: https://ardalis.com/when-qa-keeps-finding-bugs/

[^5_14]: https://onsecurity.io/article/a-guide-to-adversarial-testing-for-ai/

[^5_15]: https://journeyofquality.wordpress.com/2025/11/09/adversarial-security-testing-for-ai-agents/

[^5_16]: https://axify.io/blog/code-review-checklist

[^5_17]: https://alexmarquardt.com/ai-tools/checkloop-autonomous-code-review/

[^5_18]: https://arxiv.org/html/2505.24239v1

[^5_19]: https://arxiv.org/html/2511.05269v1

[^5_20]: https://github.com/kyegomez/awesome-multi-agent-papers

[^5_21]: https://www.reddit.com/r/ClaudeAI/comments/1qdgi36/i_built_a_multiagent_system_that_enforces_code/

[^5_22]: https://aclanthology.org/2025.ijcnlp-long.90.pdf

