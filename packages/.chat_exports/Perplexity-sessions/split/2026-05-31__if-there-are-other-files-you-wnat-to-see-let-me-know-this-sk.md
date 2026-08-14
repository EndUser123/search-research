---
title: "If there are other files you wnat to see let me know.  This skill is to call external LLMs from inside claude code or co"
date: "2026-05-31"
mode: "COPILOT"
uuid: "7e7eff66-955e-4c75-b89e-d6245dd07d81"
entry_count: 14
---

## Human

If there are other files you wnat to see let me know.  This skill is to call external LLMs from inside claude code or codex to answer questions or make file changes.  like coding.  What improvments can we make based on popular repos and your own ideas.

## Assistant

You can improve this skill a lot, and the biggest gains are not “more models” but better **selection**, stronger edit safety, and tighter repo/context handling. From the files you shared, the current system already has useful building blocks—parallel multi-CLI orchestration, simple routing, task classification, health checks, auto-context, repo-map generation, and a post-run critic—but it is still biased toward “ask several CLIs and aggregate text” rather than “reliably complete coding tasks inside a real repository.”[1][2][3][4][5]

## Current shape

The skill today appears to center on `ai_cli.py` as the orchestrator, with `SKILL.md` defining the user-facing workflow, `cli.py` and `cli_detector.py` handling health/model availability, and `file_context.py` building file or repo-map context for model calls. The code already includes rule-based routing, task classification, target/context resolution, git-changed-file detection, session-aware auto-context, quality-gate filtering, and multiple output modes such as aggregate, diff, and complete.[2][3][4][5][1]

That is a solid base, but a few limitations stand out:
- Routing is mostly keyword-based and fairly coarse, for example preferring Codex for “api/function/code/implement/refactor” and agy for “whole codebase/entire project/all files/large context.”[3]
- Context selection often picks the first detected file or a repo map once file count exceeds a threshold, which is better than nothing but still weak for multi-file edits and cross-cutting refactors.[5][3]
- The system has review and aggregation paths, but I do not yet see a robust “plan → patch → validate → rollback/retry” loop as a first-class execution primitive.[2][3]

## High-value improvements

### 1. Make routing evidence-based, not keyword-based

Popular agentic coding tools increasingly win by choosing the right model or toolchain per task, not by using the same bundle everywhere. Your current routing rules are explicit and understandable, but they are shallow and likely brittle for mixed intents like “refactor this API and update tests” or “analyze the architecture, then patch only the bug.”[3]

Improve this by adding a two-stage router:
- Stage 1: classify task dimensions, for example `read-only review`, `single-file edit`, `multi-file refactor`, `repo-wide architecture`, `test repair`, `doc update`, `security audit`.
- Stage 2: choose execution mode, not just model, such as `single-fast model`, `paired proposer+critic`, `planner+editor`, `parallel voting`, or `human-confirmed patch mode`.

This would be more aligned with how strong repos/tools differentiate between analysis tasks and mutation tasks. My confidence is high here because your code already has `classifytask(...)`, domain routing, and prompt-template support, so this is an extension of what exists rather than a rewrite.[3]

### 2. Introduce a first-class patch pipeline

For coding and file changes, the core abstraction should be a patch lifecycle:
1. Read target and adjacent files.
2. Build a scoped edit plan.
3. Generate a unified diff or exact patch.
4. Apply patch in a sandbox/worktree.
5. Run validation, for example lint, tests, typecheck, compile.
6. If validation fails, feed structured errors back for one or two repair loops.
7. Only then present or commit the final patch.

Right now the skill description emphasizes answering questions and making changes through external CLIs, but the visible architecture seems more optimized for text output aggregation than deterministic code modification.[2][3]

This matters because popular coding repos tend to be strongest where they:
- emit explicit diffs,
- constrain edits to named files,
- validate before finalizing,
- preserve rollback paths.

Your own prompt grounding text in `ai_cli.py` already points in this direction by forcing file reads before code generation and recommending syntax checking. That is good, but it should become enforced execution logic, not just prompt guidance.[3]

### 3. Add repository-aware context ranking

`file_context.py` already supports recursive collection, extension filtering, size limits, and repo-map generation inspired by Aider/Cursor-style patterns. That is a good baseline.[5]

The next jump is ranking relevance, not just collecting files:
- Prioritize import neighbors, callers/callees, test files touching the same module, recent git diff adjacency, and symbols mentioned in stack traces or diagnostics.
- Build a symbol graph or at least a cheap heuristic index: filenames, classes, functions, imports, exports, test names.
- Return context tiers: `must-read`, `helpful`, `background`, instead of one flat concatenated blob.

This would sharply reduce wasted tokens and hallucinated edits in large repos. Factually, your current implementation can produce repo maps when too many files are present and does collect changed files from git, but I do not see deeper dependency-aware ranking in the shared snippets.[5][3]

### 4. Separate “analysis mode” from “edit mode”

A common failure mode in coding agents is mixing broad advisory analysis with mutation authority. Your skill should have explicit modes:
- Analysis mode: no edits, broad repo context, multiple models allowed, compare opinions.
- Edit mode: narrow scope, one primary editor, strict file allowlist, validator loop required.
- Review mode: changed files and tests only, severity-ranked findings, no speculative architecture rewrites.
- Repair mode: start from validator output, minimize change set.

This is especially important because your system currently includes broad auto-context detection from query text, git status, and session activity. That is useful, but in edit mode it can accidentally expand scope too much.[3]

### 5. Replace “verbatim aggregate outputs” with structured consensus objects

`SKILL.md` says combined outputs are reported verbatim and then optionally reviewed by a critic. That is helpful for transparency, but not ideal for actionability in coding workflows.[2]

A stronger pattern is to normalize each model’s response into a schema such as:
- claim / recommendation
- affected files
- patch or pseudopatch
- confidence
- assumptions
- validation commands
- risks

Then do deduplication and consensus over those structured units. Your quality-gate code already extracts findings and filters by confidence, so you have the beginnings of this architecture.[3]

The improvement is to move from “post hoc text filtering” to “schema-first orchestration.” That makes disagreement handling much cleaner:
- same diagnosis, different fixes;
- different diagnosis, same files;
- unsupported recommendation;
- recommendation outside allowed scope.

### 6. Add worktree-based safe editing

For real code changes, use git worktrees or temporary branches for every edit session. That gives:
- clean rollback,
- isolated validation,
- clearer diffs,
- safer concurrent use across terminals.

Given your user profile and the likely environment—multi-terminal, iterative, repo-heavy—this is especially valuable. This is my own design recommendation rather than something evidenced in your files, so I’m labeling it as **SPECULATION with high confidence** based on common agentic coding failure modes and the repo-centric nature of this tool. The nearby fact is that your current code already uses git status and diffs for context detection, so git-aware isolation would fit naturally.[3]

## Popular-repo inspired additions

I cannot responsibly claim detailed current features of specific external repos without checking them directly, and I did not inspect external repos here, so treat this section as **CONSENSUS / design pattern synthesis**, not repo-specific fact. Still, these are the patterns that repeatedly show up in strong coding-agent tools:

- Repo map plus symbol search, not raw whole-repo stuffing.
- Diff-first edits instead of free-form rewritten files.
- Explicit file allowlists and edit budgets.
- Tight validator loops with machine-readable failures.
- A planner/editor/reviewer split for larger tasks.
- Strong treatment of tests as first-class context and validation inputs.

Those patterns line up with what your codebase already partially supports through repo maps, changed-file detection, routing, and quality gates.[5][3]

## Concrete feature roadmap

### Priority 1

- Add `--mode analysis|edit|review|repair`.
- Add `--apply-patch` and `--dry-run` paths that produce unified diffs.
- Add validator hooks: `pytest`, `npm test`, `ruff`, `mypy`, `tsc`, `eslint`, configurable per repo.
- Add file allowlist and max-edit-count guardrails.
- Require structured output schema from every model in edit/review mode.

These are the fastest path to making the skill safer and more useful for actual coding work. The current code already has argument parsing, output modes, and context machinery, so these fit the existing CLI design.[2][3]

### Priority 2

- Build a cheap symbol indexer for Python and TypeScript.
- Rank context by imports, references, and related tests.
- Add stack-trace-aware retrieval.
- Add “smallest sufficient context” selection before model invocation.

This would improve accuracy under token pressure and help the system behave more like the better repo-aware coding tools. Your current context builder is path- and size-aware, but not yet symbol-aware.[5]

### Priority 3

- Replace fixed keyword routing with benchmark-backed policy routing.
- Persist per-task performance stats by repo, language, and task subtype.
- Learn preferred model bundles from observed pass rates, not just latency and generic “quality.”

You already have performance stats/config concepts and domain routing hooks, which makes this an obvious next step.[2][3]

## Architecture ideas

A clean internal architecture would look like this:

| Layer | Responsibility | Why it helps |
|---|---|---|
| Intent classifier | Determine analysis/edit/review/repair and task subtype. [3] | Prevents broad prompts from triggering unsafe edits. |
| Context engine | Resolve target, rank related files, build tiered context. [3][5] | Reduces token waste and wrong-file edits. |
| Execution planner | Choose model topology: single, parallel, planner/editor, proposer/critic. [3] | Matches cost and risk to task type. |
| Patch engine | Generate/apply diff in isolated workspace. | Makes edits auditable and reversible. |
| Validator loop | Run tests/lint/typecheck and feed failures back. | Converts “looks good” into “actually works.” |
| Result synthesizer | Emit structured consensus, risks, assumptions, next actions. [3][2] | Better than raw transcript dumps for coding work. |

## Assumptions and uncertainty

- **FACT:** The current skill already has parallel orchestration, simple routing, task classification hooks, context auto-detection, repo-map generation, and a quality-gate/critic concept.[5][2][3]
- **FACT:** I did not inspect external popular repos in this pass, so I am not making repo-by-repo claims.[2][5][3]
- **CONSENSUS:** Strong coding-agent systems tend to perform best with diff-based edits, constrained context retrieval, validation loops, and explicit mode separation.
- **SPECULATION, high confidence:** Worktree isolation, schema-first model output, and task-topology routing would produce the biggest reliability gains for your skill.

## Next files to inspect

To make the next round much more concrete, the most useful additional files would be:
- any prompt-template or prompt-builder module,
- task classifier implementation,
- patch/apply/write module if one exists,
- critic agent prompt,
- benchmark/performance router module,
- any config schema examples,
- tests for `ai_cli.py` and `file_context.py`.

Most specifically, I’d want to inspect whatever defines:
- `classifytask(...)`,
- `buildprompt(...)`,
- the actual parallel runner for CLIs,
- any file-writing path,
- critic logic and schema expectations,
- benchmark-driven router code referenced by domain routing.[3]

Please attach those modules next, especially the prompt builder, task classifier, and any patch/apply logic.

## Human

prompt_templates.py

## Assistant

`prompt_templates.py` is reasonably well-structured, but it is still a prompt-layer system, not yet an execution-contract system. Its strengths are: a typed `PromptEnvelope`, per-task contracts in `_TASK_CONTRACTS`, a separate human-readable `PROMPT_TEMPLATES` dictionary, and a `build_prompt(...)` function that combines request contract, optional context, query, and global solo-dev constraints.[1]

## What it does well

The file separates three concerns better than many prompt systems do:
- task metadata and enforcement hints in `_TASK_CONTRACTS`,
- stylistic/output prompting in `PROMPT_TEMPLATES`,
- rendering in `_render_request_contract(...)` and `build_prompt(...)`.[1]

That separation is useful because it gives you one place for output expectations, one place for behavioral guidance, and one place for composition logic. It also explicitly tracks `target` and `target_source`, which is a strong design choice for coding workflows because it preserves provenance instead of pretending every prompt is equally grounded.[1]

The evidence/fallback language is also better than generic prompt boilerplate. Several task types explicitly say “use only supplied target/context,” “do not invent file names/APIs/behavior,” and “ask for missing info instead of guessing,” which fits the reliability goals you described.[1]

## Main weaknesses

The biggest issue is duplication. `_TASK_CONTRACTS` and `PROMPT_TEMPLATES` encode much of the same information twice—focus areas, output structure, fallback behavior—which will drift over time and create inconsistent prompts as one side gets updated but the other does not.[1]

The second issue is that the system still produces a single large free-form text prompt rather than a structured machine-readable contract. That means downstream components cannot reliably enforce things like “must cite file paths,” “must return patch plan,” or “must distinguish assumptions from evidence” except by post hoc parsing.[1]

The third issue is that edit-oriented tasks are underspecified. You have task types like `DEBUG`, `REFACTOR`, and `CODE_REVIEW`, but I do not see explicit prompt modes for `PATCH`, `APPLY_CHANGE`, `TEST_REPAIR`, `MULTI_FILE_EDIT`, or `SAFE_REWRITE`, which are exactly the tasks that benefit from the strictest constraints.[1]

## Best improvements

### 1. Collapse contracts and templates into one schema

Right now you have a “contract” dict and a “template” dict for the same task. A cleaner design is one `TaskPromptSpec` dataclass:
- `goal`
- `instruction`
- `focus`
- `required_inputs`
- `forbidden_behaviors`
- `output_schema`
- `fallback`
- `few_shot_examples` optional
- `mode_flags`, for example `read_only`, `edit_allowed`, `requires_target`

That removes duplicate truth sources and makes prompt assembly deterministic. This is the most important structural cleanup because drift between `_TASK_CONTRACTS` and `PROMPT_TEMPLATES` is otherwise almost guaranteed.[1]

### 2. Add execution-mode prompts, not just task-type prompts

Task type alone is too coarse. You should also branch on execution mode:
- `analysis`
- `review`
- `edit-plan`
- `patch-generation`
- `repair-from-failure`
- `final-synthesis`

For example, `REFACTOR + analysis` should produce “identify smallest safe refactor,” while `REFACTOR + patch-generation` should produce “emit file-by-file diff plan and validation steps.” The current file does not seem to encode that distinction.[1]

### 3. Make outputs schema-first

Instead of asking for markdown headings only, require explicit labeled fields such as:
- `summary`
- `findings[]`
- `affected_files[]`
- `assumptions[]`
- `risks[]`
- `validation_steps[]`
- `patch_strategy`

This could still be human-readable, but should be parser-friendly. Your broader codebase already has `structured_response.py`, so this prompt file should align tightly with that schema rather than relying on markdown section names alone. I have not inspected `structured_response.py` in this turn, so that alignment point is a design recommendation based on its filename, not a confirmed current integration.[2][1]

### 4. Add negative constraints for coding edits

For edit-capable tasks, add hard bans such as:
- Do not rename files unless requested.
- Do not change public interfaces unless required.
- Do not introduce new dependencies without explicit justification.
- Do not widen scope beyond named target files without citing the dependency reason.
- Do not output invented line numbers.
- If proposing a patch, separate required changes from optional cleanup.

Your current evidence rules say “do not invent,” which is good, but coding agents improve when the constraints are concrete and scoped to mutation risks.[1]

### 5. Split context types

The file currently treats `context` mostly as one text block and avoids double-wrapping if the query already contains `--- Context ---`. That is pragmatic, but fragile.[1]

A stronger design is to distinguish:
- `repo_context`
- `target_files`
- `diagnostics`
- `user_request`
- `prior_attempts`
- `validation_failures`

Then render each section separately. This matters because debugging prompts should weight logs differently than source files, and review prompts should privilege changed files over ambient repo context. The current “single context blob” approach can blur those boundaries.[1]

## Specific issues in this file

- `SOLO_DEV_CONSTRAINTS` is globally appended to every prompt, including `RESEARCH` and `GENERAL`. That may sometimes distort answers by over-biasing toward simplicity even when the user is asking a conceptual or comparative question rather than implementation advice.[1]
- The prompt builder checks for `"--- Context ---"` substring in the query to avoid nesting. That is clever but brittle; delimiter collision is possible and string-based detection is weaker than carrying structured sections separately.[1]
- `target_required` is represented in the contract, but `build_prompt(...)` does not appear to enforce it beyond rendering text. In other words, the prompt says target is required, but there is no hard failure path in this file when it is absent.[1]
- The output formats are markdown-oriented and helpful for humans, but too loose for reliable aggregation, comparison, and validator-loop feedback.[1]

## Recommended redesign

A good next version would look like this:

1. Replace `_TASK_CONTRACTS` and `PROMPT_TEMPLATES` with one typed task spec registry.[1]
2. Add a second dimension: `task_type x execution_mode`.[1]
3. Render structured sections explicitly: `Request`, `Targets`, `Context Files`, `Diagnostics`, `Constraints`, `Required Output`.[1]
4. Require schema-compatible outputs that `structured_response.py` can parse consistently.[2][1]
5. Move policy constraints like “must read files first,” “must propose smallest patch,” and “must include validation commands” into executable orchestration when possible, not prompt text only.[1]

## Concrete next step

The next thing I’d inspect is `structured_response.py` and `parallel_llm.py`, because the quality of this prompt system now depends less on prose quality and more on whether the downstream parser/executor can consume structured outputs and run correction loops. `prompt_templates.py` is already decent as a prompt authoring layer; the real opportunity is to bind it much more tightly to execution and validation.[3][2][1]

If you want, send `structured_response.py` next and I’ll map exactly how to redesign `prompt_templates.py` so the prompt contract and response parser become one coherent system.

## Human

What the target LLM says: "They’re mostly good ideas, and the strongest ones are the ones that move /ai-cli from “better prose” to “better contract.”
What I agree with most:
Collapse prompt contracts and templates into one typed spec. That’s the biggest structural win. Right now the duplication risk is real, and the review is right to flag it.
Add an execution-mode dimension. review vs patch-generation vs repair-from-failure is a better boundary than task type alone.
Make outputs schema-first. That will help both the critic and the aggregator.
Push hard constraints into orchestration where possible. A prompt saying “read files first” is weaker than code that actually attaches the files.
What I’d treat as especially important:
target_required should not just be rendered in text. If a task needs a target, the launcher should fail or auto-bind one before the model is called.
The “single large free-form prompt” critique is valid. That’s why I think the next real step is structured sections or a machine-readable envelope, not more prompt polish.
What I’d soften:
The suggestion to add lots of new task modes like PATCH, SAFE_REWRITE, MULTI_FILE_EDIT is directionally right, but I would not rush to add a dozen labels. Start with the execution modes that map to actual orchestration behavior.
The note about prompt_templates.py being “not yet an execution-contract system” is fair, but it’s also slightly overstated. It already has target/source awareness and task-specific structure. The real gap is enforcement and downstream structure, not total absence of contract semantics.
Some of the “missing modules” language looks like a generic review script rather than a precise assessment of this codebase. The useful part is the direction, not every specific module suggestion.
My ranking of the ideas:
Best: unify contract + template into one spec.
Best: schema-first outputs.
Best: execution-mode dimension.
Good: move policy checks into code.
Good but later: add richer edit/patch task modes.
Lower priority: more examples and more prose in the prompt file.
If you want the blunt version: the review is right about the architecture, and the main thing it misses is that /ai-cli already has some of the right ingredients. The problem is less “write better prompts” and more “make the prompt builder, target resolver, and result parser behave like one system.”"

## Assistant

Yes — that target LLM assessment is mostly right, and `structured_response.py` makes the core point even stronger: your system already has the beginnings of a contract layer, but the prompt builder and response parser are still only **loosely coupled** rather than behaving like one coherent protocol.[1][2]

## Where it is right

The best part of that assessment is the distinction between “better prose” and “better contract.” `structured_response.py` already defines explicit dataclasses for `Finding`, `CliResponse`, `QualityGateResult`, and `AggregatedResponse`, with fields for severity, confidence, location, tags, source metadata, token usage, and aggregation metadata. That means the codebase is not missing structure in general; it is missing a tighter handshake between prompt generation, model output, and parser expectations.[1]

It is also right that `target_required` should not remain a textual hint. In `prompt_templates.py`, target requirement is rendered into the “Task Brief,” but there is no enforcement in that file itself; meanwhile, the critic explicitly treats hallucinated file paths, flags, commands, and unsupported claims as serious failures, which means the orchestration layer should prevent under-scoped launches rather than rely on the model to behave.[3][2]

The recommendation to add an execution-mode dimension is also strong. Right now `prompt_templates.py` organizes behavior mostly by `TaskType`, while `structured_response.py` normalizes results into shared response/finding structures independent of task mode, so there is a mismatch: task intent is specialized on the way in, but response structure is mostly generic on the way out. Adding modes like `analysis`, `review`, `patch-generation`, and `repair-from-failure` would give both ends a stronger common contract.[2][1]

## What the code shows

`structured_response.py` is more capable than a superficial review would suggest. It does not just dump text; it extracts token usage, tries to infer model IDs, parses findings from either JSON or text, wraps each CLI run in a `CliResponse`, and calculates an agreement score across responses before producing an `AggregatedResponse`. That supports your target LLM’s claim that `/ai-cli` already has some of the right ingredients.[1]

At the same time, the weaknesses are visible:
- text extraction falls back to heuristic parsing with default confidence values,
- agreement is based on simple overlap of the first 500 output characters,
- consensus is essentially “first successful response” when agreement is high,
- and the parser accepts multiple loose shapes rather than requiring one authoritative schema.[1]

That combination is exactly why “schema-first outputs” is such a good recommendation. The parser is trying hard to recover structure after the fact, which is useful as a fallback but weaker than instructing models to emit a stable schema that directly maps onto `Finding`, `CliResponse`, and aggregation fields.[1]

## What I would sharpen

I would sharpen one point even more than the target LLM did: the key missing abstraction is not just “execution mode,” but a **shared protocol object** used by resolver, prompt builder, runner, parser, and critic. Right now you effectively have fragments of that protocol in different places:
- target/context semantics in `prompt_templates.py`,[2]
- output schema concepts in `structured_response.py`,[1]
- critic evidence rules in `ai-cli-critic.md`.[3]

Those should really be one system. For example, a single typed request/response contract could define:
- required inputs,
- allowed evidence sources,
- expected output fields,
- whether free-form markdown is allowed,
- whether a target is mandatory,
- whether findings must include location/confidence,
- whether patch suggestions are permitted or required.

That would turn the current “prompt builder, target resolver, and result parser behave like one system” insight into an actual implementation plan. The target LLM is directionally correct here, but the strongest form of the idea is: unify them around one typed protocol, not just better prompt specs.[3][2][1]

## What I would soften

I agree with softening the push for a large number of new task labels. The evidence in your files supports that caution. `structured_response.py` currently normalizes broad finding-oriented outputs well enough for review/research/debug-style tasks, but it is not yet obviously built around a rich family of mutation-specific schemas. That means adding many new labels before adding orchestration behavior would mostly create naming complexity.[2][1]

I also agree that the earlier criticism may have slightly understated what already exists. `prompt_templates.py` does carry real contract semantics: it tracks `target`, `target_source`, `target_required`, evidence rules, output expectations, and fallback rules. Calling it “not yet an execution-contract system” is fair, but only if the emphasis is on **enforcement gap**, not absence of structure.[2]

## Best next move

The most leverage now is to redesign around one typed spec that both prompt generation and response parsing understand. Concretely:

- Replace duplicated task contract + prose template definitions with a single typed prompt spec.[2]
- Add `execution_mode` as a first-class field in the request envelope.[2]
- Add a schema identifier or output contract version to prompts and require JSON for modes where parsing matters.[3][1]
- Make `structured_response.py` the canonical response model, not just a recovery parser.[1]
- Treat text parsing and markdown heading extraction as fallback compatibility mode only.[1]

That would align with the critic too, because the critic asks for JSON-only output and reasons about evidence support, contradictions, unsupported assertions, and grounding status. A schema-first contract would make critic passes much more reliable and easier to automate.[3][1]

## My ranking

Your target LLM’s ranking is good, and the code supports it:

1. Unify contract + template into one typed spec. The duplication in `prompt_templates.py` is real.[2]
2. Make outputs schema-first and align them directly with `structured_response.py`.[1]
3. Add execution mode as an orthogonal dimension to task type.[2][1]
4. Move policy checks like target enforcement and evidence gating into orchestration instead of relying on prompt prose.[3][2]
5. Add richer edit-specific modes later, once there is orchestration behavior to justify them.[2][1]

## Practical conclusion

Bluntly: I agree with the target LLM. The architecture problem is not “write fancier prompts”; it is “stop treating prompt text, target resolution, parser heuristics, and critic logic as adjacent components and make them one protocol.” That conclusion is strongly supported by the fact that `prompt_templates.py`, `structured_response.py`, and `ai-cli-critic.md` already each encode different slices of the same contract, but do so independently.[3][1][2]

If you want the most useful next artifact, I’d suggest I draft the actual replacement design: a `TaskSpec` / `ExecutionMode` / `ResponseSchema` model plus a migration plan showing exactly how to refactor `prompt_templates.py` and `structured_response.py` with minimal churn.

## Human

Note that we are using agy for gemini models and PI for other models.  What prompt should we give to the target LLM?

## Assistant

You want one prompt that works well when sent through agy (Gemini) and PI (other models) as the *target LLM* for `/ai-cli`, and that reinforces the “contract-first” behavior you and the other model just aligned on. A good fit is a short, schema-first system prompt that:

- Describes the protocol (request envelope, context, question).
- States what outputs are allowed and required.
- Aligns with your existing `structured_response.py` `Finding` and `CliResponse` shapes.[1]
- Makes clear that the model must not improvise structure or ignore missing targets.[2][3]

Below is a concrete candidate you can drop in as the “system” or “prelude” prompt for both agy and PI.

***

## Proposed target LLM prompt

> You are the target LLM for the `/ai-cli` system.  
> All requests you receive follow this protocol:
> 
> 1. A **Task Brief** section that describes:
>    - the task type and goal (for example CODE REVIEW, DEBUGGING, REFACTORING, RESEARCH)  
>    - the target object, if any (file, directory, proposal, question)  
>    - where the target came from (explicit flag, query heuristic, session context)  
>    - focus points, expected output, evidence rules, and fallback behavior.  
> 2. An optional **Context** section delimited by:
> 
>    `--- Context ---`  
>    `<context payload>`  
>    `---`
> 
>    The context may contain code, configuration, logs, stack traces, or other text packets that you must treat as the **only authoritative source of truth** for this request unless the Task Brief explicitly allows outside knowledge.  
> 3. A **Question** section that contains the user’s actual request.
> 
> Your job is to produce a **single JSON document** that conforms to the `/ai-cli` structured response contract.  
> Do not return free-form prose or Markdown unless the Task Brief explicitly says that JSON is not required.
> 
> The top-level JSON must have this shape:
> 
> ```json
> {
>   "summary": "short high-level answer or diagnosis",
>   "findings": [
>     {
>       "category": "bug | security | performance | best_practice | design | test | general",
>       "severity": "critical | high | medium | low | info",
>       "title": "one-line description of the issue, idea, or answer",
>       "description": "detailed explanation, including reasoning and evidence",
>       "location": "optional file:path[:line-range] or logical location",
>       "code_snippet": "optional excerpt from the Context that supports this finding",
>       "confidence": 0,
>       "tags": ["optional", "labels"]
>     }
>   ],
>   "steps": [
>     {
>       "type": "plan | patch | test | rollback | question",
>       "description": "what to do and why",
>       "commands": ["optional shell commands or test invocations"],
>       "depends_on": ["optional step ids or descriptions this step depends on"]
>     }
>   ],
>   "assumptions": [
>     "assumption 1",
>     "assumption 2"
>   ],
>   "risks": [
>     "risk 1",
>     "risk 2"
>   ]
> }
> ```
> 
> Rules:
> 
> - **No extra top-level fields**. If you need to omit `steps`, `assumptions`, or `risks`, return them as empty arrays.
> - **Do not invent file names, APIs, flags, commands, or line numbers** that do not appear in the Context or Task Brief. If you need additional information, add a `Finding` with `category:"general"`, `severity:"info"`, and a `title` prefixed with `"NEEDS_INPUT:"`.
> - If the Task Brief marks the target as **required** but the `Target` field is `Not provided` or the Context is empty, you **must not** fabricate an answer. Instead, return:
>   - `summary`: a short explanation of what is missing.
>   - `findings`: a single `NEEDS_INPUT` finding describing exactly what you require (for example specific file path, stack trace, or configuration).
>   - Empty `steps`, `assumptions`, and `risks`.
> - When you extract evidence from the Context, include a `code_snippet` or `location` whenever possible so that downstream tools can verify your claim.
> - Use the **Task Brief** to specialize behavior:
>   - For CODE REVIEW and REFACTORING tasks, treat each `Finding` as a review item for the target code.
>   - For DEBUGGING tasks, use `category:"bug"` or `category:"design"` and populate `steps` with diagnostic and fix steps.
>   - For PLANNING tasks, put the plan into `steps` and use `findings` for major decisions or trade-offs.
>   - For RESEARCH and GENERAL tasks, treat `findings` as key points and `steps` as suggested next actions.
> - If you are unsure or the evidence is weak, lower the `confidence` field and explain why in `description`.
> - Do **not** output comments, explanations, or Markdown outside the JSON. The entire response must be parseable JSON.
> 
> If the Task Brief explicitly says that Markdown sections are required and JSON is not, you may follow the specified Markdown format instead, but you must still:
> - respect the evidence rules,
> - avoid inventing unsupported details,
> - and clearly separate **facts from speculation** in your wording.

This gives you:

- A single prompt that works for both agy (Gemini) and PI CLIs, because it is model-agnostic and aligns with generic Gemini prompting guidelines (context first, task then constraints).[4][5]
- A schema that lines up with your `Finding` and `CliResponse` dataclasses (`category`, `severity`, `title`, `description`, `location`, `code_snippet`, `confidence`, `tags`).[1]
- Clear behavior for missing targets, which enforces `target_required` semantics without relying on prompt prose alone.[2]
- A structure that your critic (`ai-cli-critic`) can read easily: it can count findings, inspect categories, severities, confidence, and evidence snippets.[3][1]

You can inject this as a fixed prefix for both agy and PI runs, and then let `prompt_templates.build_prompt(...)` supply the Task Brief, Context, and Question sections underneath it.[1][2]

Would you prefer a slightly narrower schema (for example, only `summary` and `findings`) for review/debug-only runs, or is this richer shape acceptable for all modes?

## Human

"What’s useful is the contract shape, not the long prose.

Most useful parts:
- `Task Brief` / `Context` / `Question` separation. That is the right mental model for `/ai-cli`.
- The explicit `target_required` behavior. Missing target should be a hard failure or a `NEEDS_INPUT` response, not a guess.
- Evidence-first fields like `location` and `code_snippet`. Those make downstream verification possible.
- The `confidence` field. That helps separate strong findings from weak ones.
- The idea of aligning the target LLM contract with the existing structured response schema. That is the most durable part.
- The “do not invent file names/APIs/line numbers” rule. That is exactly the kind of guardrail this tool needs.

What is less useful:
- Forcing one huge JSON schema for every mode. It’s clean on paper, but it may be too rigid for models that do better with smaller contracts.
- The extra `steps / assumptions / risks` fields for every run. Useful sometimes, but not always necessary.
- The Markdown fallback clause. It muddies the contract if the goal is strict machine-readable output.

My take:
- Useful as a design direction: yes.
- Useful as a literal prompt to ship unchanged: no.
- The strongest idea is to make `/ai-cli` build and enforce a structured request envelope, then render a smaller mode-specific contract from it.

So if you want the short answer: keep the protocol, target handling, evidence rules, and schema alignment. Trim the rest."

## Assistant

I agree with that critique. The right thing to ship is a **small mode-specific contract prompt**, not the long universal prompt. Best practice for structured outputs is to keep schemas simple, stable, and validated in code, because larger schemas are more failure-prone and should be broken into smaller contracts when possible.[1][2][3][4]

## Recommended prompt

Use this as the base prompt for the target LLM, with `/ai-cli` injecting the Task Brief, optional Context, and Question beneath it:

```text
You are the target LLM for /ai-cli.

Follow this protocol exactly:

1. TASK BRIEF
Read the Task Brief first. It defines:
- goal
- target
- target source
- whether target is required
- focus
- evidence rules
- expected output shape

2. CONTEXT
If a --- Context --- block is present, treat it as the authoritative source for code, logs, config, and file content unless the Task Brief explicitly allows outside knowledge.

3. QUESTION
Answer the Question using the Task Brief and Context.

Output rules:
- Return a single JSON object only.
- Do not return Markdown.
- Do not add commentary before or after the JSON.
- Do not invent file names, APIs, flags, commands, or line numbers.
- If evidence is weak or incomplete, lower confidence and say why.

If target is required but missing, or the Context is empty when the task depends on it, return:

{
  "summary": "Missing required target or context.",
  "findings": [
    {
      "category": "general",
      "severity": "info",
      "title": "NEEDS_INPUT",
      "description": "State exactly what is missing and what is needed to continue.",
      "location": null,
      "code_snippet": null,
      "confidence": 100,
      "tags": ["needs_input"]
    }
  ]
}

Otherwise return:

{
  "summary": "Short direct answer or diagnosis",
  "findings": [
    {
      "category": "bug | security | performance | best_practice | design | test | general",
      "severity": "critical | high | medium | low | info",
      "title": "One-line finding",
      "description": "Explanation grounded in the provided evidence",
      "location": "optional file path or logical location",
      "code_snippet": "optional supporting excerpt from Context",
      "confidence": 0,
      "tags": ["optional labels"]
    }
  ]
}

Requirements:
- summary must always be present.
- findings must always be present, even if empty.
- Use location and code_snippet when available from Context.
- Keep confidence on a 0-100 scale.
- facts from Context > inference > speculation.
- If the task is planning or debugging, put the concrete next actions into finding descriptions instead of adding extra top-level fields.
```

This keeps the most valuable parts from the earlier draft:
- `Task Brief / Context / Question` separation,
- strict missing-target behavior,
- evidence-bearing fields,
- confidence,
- and alignment with your existing finding schema.[5][6]

## Why this shape fits your code

This smaller contract maps cleanly onto `structured_response.py`, whose core normalized unit is already `Finding` with `category`, `severity`, `title`, `description`, `location`, `code_snippet`, `confidence`, and `tags`. It also avoids forcing extra top-level fields like `steps`, `assumptions`, and `risks` on every task, which matches your concern about overly rigid universal schemas.[6]

It also fits your critic better. The critic expects grounded claims, flags unsupported assertions and hallucinated references, and prefers machine-readable outputs; a compact `summary + findings[]` contract makes those checks easier and less ambiguous than a larger mixed schema.[7]

## AGY and PI note

Because you are sending this through agy for Gemini and PI for other models, I would keep the **semantic contract identical** across both, and only vary transport-level hints if needed. Gemini supports structured outputs with schema constraints, and current structured-output guidance generally recommends small schemas with stable keys and validator-backed enforcement rather than verbose prompt-only contracts.[2][3][4]

So the practical split should be:
- Same logical contract for agy and PI.[6]
- If agy/Gemini can take a response schema natively, enforce this JSON shape there.[4]
- If PI models cannot, keep the prompt strict and validate/repair in orchestration.[3][2]

## Best implementation pattern

I’d implement it as:
- a structured internal request envelope in `/ai-cli`,
- rendered into a small mode-specific prompt,
- with a validator that accepts only the contracted JSON shape,
- plus a repair pass for malformed JSON.

That matches your own conclusion and the broader best practice pattern of prompt → generate → validate → repair → parse.[2][3]

My recommendation is to standardize on just two initial output contracts:
- `summary_findings` for review/debug/research/general,
- `needs_input` as the hard fallback when required inputs are missing.

That gives you a much cleaner system than trying to solve everything with one giant universal schema.[5][6]

Would you like me to draft the exact Python dataclasses / Pydantic models for this minimal contract next?

## Human

"
Useful parts:
Task Brief / Context / Question separation. That is the right contract shape.
summary + findings[] as the core output. That is small enough to validate and easy for the critic to consume.
Hard NEEDS_INPUT fallback when target/context is missing. That prevents guessing.
Evidence rules: no invented paths, APIs, flags, or line numbers.
location, code_snippet, and confidence. Those make the output auditable instead of just persuasive.
Keeping the same semantic contract for agy and pi, while changing only transport details if needed.
What I would not keep as-is:
The long universal schema for every mode.
Extra top-level fields like steps, assumptions, and risks on every run.
The Markdown fallback clause.
Any wording that makes the prompt itself the main enforcement mechanism instead of the orchestrator.
My read:
This is useful as the minimal target-LMM contract.
It is not useful as a literal drop-in prompt without trimming.
Best version:
standardize on summary and findings
add NEEDS_INPUT as the only hard fallback
enforce the shape in code
let /ai-cli render mode-specific instructions around that
If you want, I can turn this into the exact contract I’d ship for /ai-cli, in one compact schema.
4:44 PM
yes please

4:44 PM
I’d ship this as the default target-LLM contract for /ai-cli:
You are the target LLM for /ai-cli.

You will receive:
1. A Task Brief
2. Optional Context
3. The user Question

Follow this protocol exactly.

TASK BRIEF
- Defines the goal, target, target source, whether the target is required, focus, evidence rules, and expected output shape.
- Treat it as authoritative.

CONTEXT
- If a --- Context --- block is present, treat it as the authoritative source for code, logs, config, and file content.
- Do not use outside knowledge when the Task Brief or Context is sufficient.
- If the Task Brief says the target is required and the Context is missing or empty, do not guess.

QUESTION
- Answer the Question using the Task Brief and Context.
- Be concrete and evidence-based.

OUTPUT RULES
- Return a single JSON object only.
- Do not return Markdown.
- Do not add commentary before or after the JSON.
- Do not invent file names, APIs, flags, commands, or line numbers.
- If evidence is weak or incomplete, lower confidence and explain why.

RESPONSE SHAPE
{
  "summary": "short direct answer or diagnosis",
  "findings": [
    {
      "category": "bug | security | performance | best_practice | design | test | general",
      "severity": "critical | high | medium | low | info",
      "title": "one-line finding",
      "description": "grounded explanation",
      "location": "optional file path or logical location",
      "code_snippet": "optional supporting excerpt",
      "confidence": 0,
      "tags": ["optional"]
    }
  ]
}

HARD FALLBACK
- If the target is required but missing, or the Context is empty when the task depends on it, return:
  - summary: what is missing
  - findings: one `NEEDS_INPUT` finding with exactly what is needed
- In that case, do not fabricate any findings.

RULES OF INTERPRETATION
- Facts from Context outrank inference.
- Inference outranks speculation.
- If uncertain, say so explicitly.
Why this is the right size:
It is small enough that weak models can follow it.
It is strict enough that the orchestrator can validate it.
It gives you one stable contract across agy and pi.
It does not force every mode to carry irrelevant fields.
What I would keep in /ai-cli itself:
Task Brief / Context / Question separation
summary + findings[]
NEEDS_INPUT fallback
confidence, location, code_snippet
no invented references
What I would not keep as universal:
steps
assumptions
risks
Markdown fallback
giant multi-purpose schemas
If you want, I can next turn this into the exact Python dataclass / Pydantic model layout for /ai-cli."

## Assistant

Yes — that compact contract is the one I’d ship, with one small refinement: make `NEEDS_INPUT` an explicit allowed `category` or at least a reserved `title` convention, so your validator and critic can recognize it deterministically instead of inferring it from free text. Small, validator-friendly schemas are more reliable than large universal ones, and Gemini can be constrained with JSON schema directly when supported.[1][2][3][4]

## Shippable contract

This is the exact target-LLM contract I would ship for `/ai-cli`:

```text
You are the target LLM for /ai-cli.

You will receive:
1. A Task Brief
2. Optional Context
3. The user Question

Follow this protocol exactly.

TASK BRIEF
- Defines the goal, target, target source, whether the target is required, focus, evidence rules, and expected output shape.
- Treat it as authoritative.

CONTEXT
- If a --- Context --- block is present, treat it as the authoritative source for code, logs, config, and file content.
- Do not use outside knowledge when the Task Brief and Context are sufficient.
- If the Task Brief says the target is required and the Context is missing or empty, do not guess.

QUESTION
- Answer the Question using the Task Brief and Context.
- Be concrete and evidence-based.

OUTPUT RULES
- Return a single JSON object only.
- Do not return Markdown.
- Do not add commentary before or after the JSON.
- Do not invent file names, APIs, flags, commands, or line numbers.
- If evidence is weak or incomplete, lower confidence and explain why.

RESPONSE SHAPE
{
  "summary": "short direct answer or diagnosis",
  "findings": [
    {
      "category": "bug | security | performance | best_practice | design | test | general | needs_input",
      "severity": "critical | high | medium | low | info",
      "title": "one-line finding",
      "description": "grounded explanation",
      "location": "optional file path or logical location",
      "code_snippet": "optional supporting excerpt",
      "confidence": 0,
      "tags": ["optional"]
    }
  ]
}

HARD FALLBACK
- If the target is required but missing, or the Context is empty when the task depends on it, return:
  - summary: what is missing
  - findings: one finding with:
    - category: "needs_input"
    - severity: "info"
    - title: "NEEDS_INPUT"
    - description: exactly what is needed to continue
    - location: null
    - code_snippet: null
    - confidence: 100
    - tags: ["needs_input"]
- In that case, do not fabricate any substantive findings.

RULES OF INTERPRETATION
- Facts from Context outrank inference.
- Inference outranks speculation.
- If uncertain, say so explicitly.
```

That preserves the useful parts you highlighted: `Task Brief / Context / Question`, `summary + findings[]`, hard `NEEDS_INPUT`, evidence-bearing fields, and one shared semantic contract across agy and PI. It also removes the parts you correctly rejected: giant universal schema, always-on extra fields, and Markdown fallback.[5][6]

## Why this is the right size

This shape fits your existing parser almost directly. `structured_response.py` already centers on a `Finding` object with `category`, `severity`, `title`, `description`, `location`, `confidence`, and `tags`, plus source metadata and aggregation around it, so `summary + findings[]` is a natural stable contract rather than a new abstraction.[6]

It also fits the critic’s job better than prose-heavy answers. The critic is designed to flag unsupported claims, contradictions, overconfidence, and hallucinated references, and a compact JSON contract with evidence-bearing finding fields makes those checks clearer and more automatable.[7]

## AGY vs PI

Use the **same contract text** for both agy and PI. The difference should be transport and enforcement:
- For agy/Gemini, prefer native structured output with JSON schema when available. Gemini supports schema-constrained JSON responses, and Google documents using JSON schema or Pydantic/Zod-backed schema definitions for predictable structured outputs.[3]
- For PI and other models, use the same prompt contract, then validate in code and run one repair pass if parsing fails. Validator-backed retries are a common and effective pattern for LLM structured output pipelines.[8][9]

## One implementation improvement

I would slightly adjust your internal schema so `location` and `code_snippet` are nullable fields explicitly, because Gemini’s structured output mode supports `null` in schema type arrays and your fallback case needs that cleanly.[3]

I would also enforce:
- `summary: str`
- `findings: list[Finding]`
- `confidence: int` constrained to 0–100
- `severity` and `category` as enums

That is exactly the sort of thing Pydantic models and generated JSON schema are good at, and it gives you a single contract source for validation and, where possible, provider-native schema enforcement.[2][1]

## Recommendation

So the final answer is: **yes, ship that compact contract**, with only these tweaks:
- add `needs_input` as an explicit category,
- make nullable evidence fields explicit,
- and enforce the schema in orchestration rather than trusting the prompt alone.[1][6][3]

The next step should be to define one `FindingModel` and one `TargetLLMResponseModel`, generate JSON schema from them, use that schema for agy/Gemini where possible, and use the same models for validation/repair on PI responses.[6][1][3]

Would you like the exact Pydantic model definitions and the `model_json_schema()` output shape next?

## Human

Yes, show me the Pydantic models for this structure

## Assistant

Yes — for this contract, I’d keep the models very small and strict. Pydantic can generate JSON Schema directly from your models, and that schema can then be used both for local validation and, where supported, provider-side structured output enforcement. Gemini’s structured output mode supports JSON Schema, though it uses a subset, so simpler nested models and enums are the safer choice.[1][2][3][4]

## Pydantic models

Here is a clean Pydantic v2 version for the `summary + findings[]` contract:

```python
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FindingCategory(str, Enum):
    bug = "bug"
    security = "security"
    performance = "performance"
    best_practice = "best_practice"
    design = "design"
    test = "test"
    general = "general"
    needs_input = "needs_input"


class FindingSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class FindingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: FindingCategory = Field(
        ...,
        description="High-level finding type."
    )
    severity: FindingSeverity = Field(
        ...,
        description="Relative importance of the finding."
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short one-line finding title."
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Grounded explanation of the finding."
    )
    location: Optional[str] = Field(
        default=None,
        description="Optional file path, file:line reference, or logical location."
    )
    code_snippet: Optional[str] = Field(
        default=None,
        description="Optional supporting excerpt from the provided context."
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score from 0 to 100."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional labels for filtering or downstream processing."
    )


class TargetLLMResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        min_length=1,
        description="Short direct answer, diagnosis, or summary."
    )
    findings: list[FindingModel] = Field(
        default_factory=list,
        description="Structured findings extracted from the task."
    )
```

This is the smallest version I would actually ship. It directly reflects the useful contract shape you settled on: compact, auditable, and easy to validate.[5]

## Optional helper for NEEDS_INPUT

I would also add one constructor/helper so the orchestrator has one canonical fallback object instead of rebuilding it ad hoc:

```python
def build_needs_input_response(message: str) -> TargetLLMResponseModel:
    return TargetLLMResponseModel(
        summary=message,
        findings=[
            FindingModel(
                category=FindingCategory.needs_input,
                severity=FindingSeverity.info,
                title="NEEDS_INPUT",
                description=message,
                location=None,
                code_snippet=None,
                confidence=100,
                tags=["needs_input"],
            )
        ],
    )
```

That makes the hard fallback explicit in code instead of only in prompt text, which is exactly the direction you said you wanted.[6][5]

## JSON schema generation

With Pydantic v2, you can generate the schema like this:

```python
schema = TargetLLMResponseModel.model_json_schema()
```

That is the correct built-in path for generating a JSON-schema dictionary from a model in Pydantic v2.[2][7][1]

If you want JSON text to pass to a provider SDK or save to disk:

```python
import json

schema_json = json.dumps(TargetLLMResponseModel.model_json_schema(), indent=2)
```

## Example valid output

This is the kind of payload your parser should accept:

```json
{
  "summary": "The target file likely has an unsafe shell command construction path.",
  "findings": [
    {
      "category": "security",
      "severity": "high",
      "title": "Unsanitized shell input reaches subprocess execution",
      "description": "User-controlled input appears to be interpolated into a command string before execution, which can permit command injection if not strictly validated.",
      "location": "cli.py:120-144",
      "code_snippet": "subprocess.run(user_cmd, shell=True)",
      "confidence": 88,
      "tags": ["subprocess", "command-injection"]
    }
  ]
}
```

And the canonical fallback:

```json
{
  "summary": "Missing required target or context.",
  "findings": [
    {
      "category": "needs_input",
      "severity": "info",
      "title": "NEEDS_INPUT",
      "description": "Provide the target file path or attach the relevant context block so the task can be grounded.",
      "location": null,
      "code_snippet": null,
      "confidence": 100,
      "tags": ["needs_input"]
    }
  ]
}
```

## Small implementation notes

A few choices here are intentional:

- `extra="forbid"` prevents silent acceptance of hallucinated keys, which is important when the whole point is strict contract enforcement.[1][2]
- `Enum` types give you stable categories and severities and generate clean schema enums.[2]
- `confidence` as `int` with `ge=0, le=100` matches your stated contract and is easy to validate and score downstream.[8]
- `location` and `code_snippet` are nullable because the `NEEDS_INPUT` path needs that cleanly, and nullable fields are common in provider-side structured output schemas.[3][4]

## Fit with your codebase

This model aligns well with `structured_response.py`, which already centers on a `Finding` object with nearly the same fields, plus aggregation metadata around it. In practice, I would either:
- replace the existing `Finding` dataclass with a Pydantic model, or
- keep the dataclass and add converters to/from `FindingModel` so that prompt contract validation and internal aggregation use the same semantic shape.[5]

The second path is lower-risk if you want minimal changes. The first path is cleaner if you want one unified schema source.

## Recommendation

I would ship exactly these two models first:
- `FindingModel`
- `TargetLLMResponseModel`

Then add only one helper:
- `build_needs_input_response(...)`

That is enough to:
- validate PI responses locally,
- generate Gemini schema for agy-backed runs,
- simplify critic input,
- and reduce prompt/output drift.[4][1][5]

Would you like me to next show:
1. the exact `model_json_schema()` output these models will produce, or  
2. how I would wire them into your existing `structured_response.py` and `ai_cli.py` flow?

## Human

"Implemented.
What changed:
Added a canonical needs_input fallback path in structured_response.py:
build_needs_input_finding(...)
build_needs_input_payload(...)
build_needs_input_response(...)
needs_input is now a first-class finding category
Added task_requires_target(...) in prompt_templates.py.
Updated the code-review/debug/refactor fallback text so the target LLM is told to return the canonical NEEDS_INPUT response instead of guessing.
Added orchestration preflight in ai_cli.py:
target-required tasks now short-circuit before model execution when there is no explicit target and no target-bound packet
incidental auto-detected git/session context no longer bypasses the missing-target guard
JSON output now emits the deterministic summary + findings[] NEEDS_INPUT payload
Added regression coverage in tests/test_pcli_bugfixes.py:
needs_input payload shape
target-required gating
missing-target short-circuit behavior
Verification:
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-cli\tests -q
Result: 80 passed
Behavior change in practice:
If you ask for a code review/debug/refactor without a grounded target, /ai-cli now returns the deterministic NEEDS_INPUT contract instead of wandering off into unrelated auto-context.
If you do provide a real target packet, it proceeds normally."

## Assistant

This is exactly the kind of change set that moves `/ai-cli` from “nicer prompts” to “actual contract enforcement,” and it’s aligned with both your design goals and the existing `structured_response.py`/critic architecture.[1][2][3]

## Why these changes are high‑value

- Making `needs_input` a **first-class finding category** and providing canonical builders (`build_needs_input_finding/payload/response`) turns what used to be an informal pattern into an explicit protocol the critic, orchestrator, and callers can all rely on.[1]
- Introducing `task_requires_target(...)` in `prompt_templates.py` and updating fallback wording means the target LLM is no longer encouraged to guess when it lacks a grounded target; instead it is steered toward the deterministic `NEEDS_INPUT` contract you now enforce in orchestration.[2]
- The orchestration preflight in `ai_cli.py` closes a real hole: previously, auto-detected git/session context could act as “good enough” grounding even when the task logically required an explicit target. Now, missing-target is a first-class error condition, not an invitation to auto-context wander.[4]
- Regression coverage in `tests/test_pcli_bugfixes.py` for payload shape, gating, and short‑circuit behavior is the right enforcement level: it protects the contract from silent drift, especially once other contributors start adding modes and templates.[5][4]

With 80 tests passing, you have evidence that the new behavior integrates cleanly into the existing flow, at least for the covered paths.

## Behavioral effect (as designed)

Your new behavior description is coherent with the contract:

- Code review / debug / refactor now behave like **strict tools**: no explicit target + no target‑bound packet → deterministic `NEEDS_INPUT` response. That’s exactly what your critic wants (no speculative findings) and what your structured response schema is oriented around.[3][2][1]
- When the user provides a real target packet (explicit `--target`, explicit `--context`, or a properly bound packet from session), the system proceeds normally and the target LLM sees a Task Brief + Context + Question triad consistent with the prompt contract.[2][4]

In other words, you’ve materially reduced the “AI went off and analyzed the wrong thing” failure mode without adding much friction: missing-critical-input is now a clearly signaled, machine‑readable state rather than a silent degrade into low‑value guesses.

## Next leverage point

Given these changes, the next high-leverage move is small:

- **Propagate the new contract into `structured_response.py`’s extraction path**: when `category == needs_input`, the aggregator and critic can treat it as a special case and avoid aggregating it with substantive findings.[3][1]
- **Align prompt templates for non‑edit tasks** (planning, research, brainstorm) with the same `summary + findings[]` envelope where it makes sense, while still allowing more free-form outputs where structured findings are not useful.

You’ve now enforced the critical guardrail (don’t act without a target) and made `NEEDS_INPUT` first-class. The system is in a good place to start tightening the “happy path” schema (for example requiring `location`/`code_snippet` when they exist) without risking brittle behavior.

If you want to keep iterating, the single most impactful next step would be to integrate these Pydantic models (or equivalent) directly into `structured_response.py` so that every JSON mode is guaranteed to conform to this contract before it hits the critic or callers.[6][1]

## Human

please show me the prompt tot give ot the other llm

## Assistant

You can give the other LLM this compact, contract-focused prompt. It assumes `/ai-cli` is already constructing the **Task Brief / Context / Question** envelope around the user’s request.

```text
You are the target LLM for /ai-cli.

You will receive:
1. A Task Brief
2. Optional Context
3. The user Question

Follow this protocol exactly.

TASK BRIEF
- Defines the goal, target, target source, whether the target is required, focus, evidence rules, and expected output shape.
- Treat it as authoritative.

CONTEXT
- If a --- Context --- block is present, treat it as the authoritative source for code, logs, config, and file content.
- Do not use outside knowledge when the Task Brief and Context are sufficient.
- If the Task Brief says the target is required and the Context is missing or empty, do not guess.

QUESTION
- Answer the Question using the Task Brief and Context.
- Be concrete and evidence-based.

OUTPUT RULES
- Return a single JSON object only.
- Do not return Markdown.
- Do not add commentary before or after the JSON.
- Do not invent file names, APIs, flags, commands, or line numbers.
- If evidence is weak or incomplete, lower confidence and explain why.

RESPONSE SHAPE
{
  "summary": "short direct answer or diagnosis",
  "findings": [
    {
      "category": "bug | security | performance | best_practice | design | test | general | needs_input",
      "severity": "critical | high | medium | low | info",
      "title": "one-line finding",
      "description": "grounded explanation",
      "location": "optional file path or logical location",
      "code_snippet": "optional supporting excerpt",
      "confidence": 0,
      "tags": ["optional"]
    }
  ]
}

HARD FALLBACK
- If the target is required but missing, or the Context is empty when the task depends on it, return:
  - summary: what is missing
  - findings: exactly one finding with:
    - category: "needs_input"
    - severity: "info"
    - title: "NEEDS_INPUT"
    - description: exactly what is needed to continue
    - location: null
    - code_snippet: null
    - confidence: 100
    - tags: ["needs_input"]
- In that case, do not fabricate any other findings.

RULES OF INTERPRETATION
- Facts from Context outrank inference.
- Inference outranks speculation.
- If uncertain, say so explicitly.
```

This prompt matches the contract you just implemented:

- It uses the Task Brief / Context / Question separation your `prompt_templates.py` and `ai_cli.py` already respect.[1][2]
- It enforces `summary + findings[]` as the canonical output envelope that `structured_response.py` and your critic can consume.[3][4]
- It encodes `needs_input` as a first-class category and defines the deterministic fallback payload your new `NEEDS_INPUT` helpers emit.[3]

You can pass this as the “system” or prelude prompt to both agy (Gemini) and PI, and rely on `/ai-cli` to inject the per-task Task Brief, Context, and Question underneath it.

## Human

what's missing from the recommendations you think are still relevant?

## Assistant

Two important ideas from the earlier recommendations are still relevant and not fully covered by your current changes: **execution modes** and **stronger edit/validation loops**.

## Execution modes, not just task types

Right now, behavior is mostly keyed on task type (code review, debug, refactor, etc.) plus the new `target_required` guard.[1][2]

Still missing but valuable:

- A small set of **execution modes** orthogonal to task type, for example:
  - `analysis` (read-only, no patches)
  - `edit_plan` (plan-only, no diff)
  - `patch_generation` (emit diffs or patch instructions)
  - `repair_from_failure` (start from test/lint errors)
- Mode-aware orchestration decisions:
  - `analysis`: run multiple CLIs in parallel, aggregate findings, never write.
  - `patch_generation`: choose one primary editor model, narrow context, require structured patch/plan, run validators.
  - `repair_from_failure`: feed in failing tests/stack traces as primary context, limit scope to affected files.

Why it still matters:
- Task type alone (e.g., `REFACTOR`) does not distinguish between “tell me what is wrong” vs “generate edits,” but the risk profile is very different.
- Modes let you keep the **same summary + findings contract** while changing model topology and downstream behavior based on whether edits are allowed.

## Stronger patch + validation loop

Your current changes lock down **when it is safe to run** (target required), but they do not yet strengthen **what happens when you do run**:

Missing but still useful:

- A **first-class patch pipeline** (even if initial patches are just textual suggestions):
  - plan: describe the change per file,
  - patch: emit diff-like snippets or line-scoped edits,
  - validate: run a configured validator and capture structured failures,
  - repair: feed those failures back for one or two repair attempts.
- A tighter **validation integration** between:
  - `structured_response.py` findings (category, location, confidence),[3]
  - your critic (evidence hierarchy, unsupported claims),[4]
  - and whatever test/lint/compile commands you run per repo.

Why it still matters:
- The contract you just enforced (summary + findings, needs_input) is ideal for *analysis* and *review*.
- For *editing*, you still need guardrails around “did we actually run tests?”, “did edits stay scoped?”, “did we break something obvious?” — and that requires a validation loop, not just better prompts.

## Router and stats integration

Less critical but still relevant from earlier ideas:

- Using your existing **performance logger and domain router** to:
  - prefer models per task+mode based on observed pass/fail rates, not just latency.[2][5]
  - record per-domain performance (codegen vs review vs debug) and feed that back into routing decisions.

You already have:
- task classification,[6]
- routing rules,[2]
- and performance logging.[5]

What’s missing is tying those into:
- “for this repo and task type, which model or bundle actually worked best over time?”,
- and routing based on that rather than static keyword rules.

## Where I’d focus next

Given what you’ve already shipped, I’d prioritize:

1. **Add a minimal execution-mode enum** (`analysis`, `patch_generation`, `repair`) and thread it through:
   - task classifier → prompt_templates → ai_cli orchestrator → target LLM contract.[1][6][2]
2. **Introduce a simple patch+validate path** for one mode:
   - even if patches are just suggested diffs in `findings.description`,
   - and validators are a configurable command per repo.
3. **Align `structured_response.py` more tightly** with the new contract:
   - special-case `needs_input` in aggregation,
   - and begin to treat high-confidence `bug`/`security` findings as candidates for patch-generation mode.[3]

Everything else (more task labels, richer schemas, extra fields like `steps`) can wait. The key remaining gaps are **mode-awareness for risk** and **validation loops for edits**; everything you’ve just implemented around `needs_input` and strict output contracts is the right foundation for those.

## Human

what about qa or validation?  should we have the orchestrator understand that it needs to check the work, or use a subagent to do that, or something about validating what the findings or actions were?

## Assistant

Yes — **the orchestrator should understand validation as a first-class phase**, and you may still want a subagent, but only as a *secondary* verifier, not the primary one. The strongest pattern in production agent systems is: generate → run deterministic checks → inspect results → optionally use an LLM verifier/judge → retry or stop; deterministic validators should be mandatory, while LLM judges are best used to interpret ambiguous results or catch scope/quality issues that tests miss.[1][2][3][4]

## Recommendation

Use a **layered validation model**:

1. **Orchestrator-owned deterministic validation** as the default and mandatory path.[2][4][1]
2. **LLM verifier / critic subagent** only when deterministic checks cannot fully answer “is this good enough?” or when you need to reconcile findings, scope, or evidence gaps.[5][6][1]
3. **Human stop points** for high-risk or high-impact actions.

That means the orchestrator should not just “know validation exists”; it should explicitly model validation states and refuse completion until required checks pass or a controlled exception is emitted.

## What the orchestrator should own

The orchestrator should directly manage the following:

- **Validation plan selection**: choose which checks apply for this task, for example parse, lint, typecheck, targeted tests, full tests, diff-scope review, or output-schema validation.[3][2]
- **Execution of deterministic validators**: run commands, capture exit codes, stderr/stdout, changed files, and artifacts.[1][5]
- **Validation gating**: mark work as `passed`, `failed`, `inconclusive`, or `needs_input`.
- **Retry policy**: if a validator fails, feed the failure back into repair mode for one or two attempts instead of calling the run “done.”[7][2]
- **Scope enforcement**: ensure the model did not drift outside the intended files or task boundaries. This is especially important because tests can pass even when the agent changed the wrong thing.[4][1]

In short: validation should be part of orchestration state, not just a suggestion in a prompt.

## When to use a subagent

A subagent is useful, but not as the first line of QA.

Use a verifier subagent for:
- Reviewing whether findings are actually grounded in the provided context.
- Checking whether a proposed action is out of scope even if tests pass.
- Comparing validator output to the model’s claims and producing a reconciliation report, for example confirmed / revised / unsupported.[5]
- Assessing code review findings where there may be no executable test for “this is a dubious architectural decision” or “this recommendation is overconfident.”[6][8]

Do **not** use a subagent as a substitute for:
- syntax validation,
- linting,
- type checking,
- running tests,
- or schema validation.

Those should stay deterministic whenever possible.[9][2][1]

## Best validation architecture for `/ai-cli`

For your system, I would use this minimal loop:

### 1. Plan
The target LLM returns `summary + findings[]` or a patch/action proposal.

### 2. Deterministic validation
The orchestrator runs task-appropriate checks:
- For structured output: JSON/schema validation against your Pydantic contract.
- For code edits: formatting, syntax/parse, lint, typecheck, targeted tests, optionally full tests.
- For code review findings: verify referenced files/lines actually exist; verify cited snippets match provided context.
- For repo-scoped work: verify edit scope and diff boundaries.[2][3][1]

### 3. Reconciliation
If checks fail or are inconclusive:
- feed exact validator results back into a repair or review pass;
- optionally invoke a verifier subagent to classify failures:
  - real defect,
  - bad test,
  - missing context,
  - out-of-scope change,
  - unsupported claim.[6][5]

### 4. Stop condition
Only mark complete when:
- deterministic validation passes, and
- no critical unsupported claims remain, and
- required evidence is present.

That is the core loop production systems keep converging on: deterministic verification first, LLM judgment second.[4][1][2]

## Findings vs actions

You specifically asked about validating “the findings or actions.”

These need slightly different treatment:

| Thing being validated | Best validator | Why |
|---|---|---|
| JSON response shape | Pydantic / schema validation [10][11] | Deterministic, binary pass/fail |
| File/line/path references | Deterministic path and snippet checks | Prevents hallucinated references |
| Code change correctness | Lint, typecheck, tests, compile [3][2] | Evidence that code works |
| Architectural soundness | LLM verifier + rules + maybe human | Often not fully testable |
| Recommendation grounding | Critic/verifier against context [5][6] | Detects unsupported claims |
| Scope compliance | Diff/path guardrails + verifier | Tests alone won’t catch drift |

So yes, you should validate both findings and actions, but with different tools.

## Practical design for your codebase

Given your current architecture, I would add a small validation subsystem in the orchestrator with explicit result types like:

- `VALIDATION_PASS`
- `VALIDATION_FAIL`
- `VALIDATION_INCONCLUSIVE`
- `NEEDS_INPUT`

And a validation record like:
- validator name,
- input artifact,
- result,
- evidence,
- blocking or non-blocking,
- repairable yes/no.

Then:

- `structured_response.py` validates target-LLM output shape first.
- `ai_cli.py` decides which validators apply based on task type + execution mode.
- `ai-cli-critic` becomes the semantic verifier layer after deterministic checks, not the only QA layer.[12][13][14]

## My concrete answer

So: **yes, the orchestrator should understand QA/validation directly**. It should own deterministic validation, retry logic, and completion gates. A subagent is still useful, but mainly for semantic verification, reconciliation, and scope review where tests or schema checks are insufficient.[1][2][5][4]

If I were prioritizing implementation, I’d do it in this order:

1. Add deterministic validator hooks to the orchestrator.
2. Add validation state/result objects.
3. Add one repair loop based on validator output.
4. Reposition the critic as a semantic verifier after deterministic checks.
5. Add a small rubric for “validated findings” vs “unverified findings.”

That gives you a much more reliable `/ai-cli` than relying on prompt instructions or a reviewer LLM alone.

## Human

I think this is our latest version.  What shoudl we do?

## Assistant

You’re in a good place: the latest pack shows `/ai-cli` has clear contracts, context handling, routing, logging, and tests wired up.  The question now is what to do next that actually moves reliability, not just adds surface area.[1]

Here’s what I’d do, in order of impact, given this version.

## 1. Add execution modes (small, but structural)

Right now everything flows through `TaskType` and the new `task_requires_target(...)`/`NEEDS_INPUT` gating, but there’s no explicit notion of “this is analysis vs this is editing vs this is repair.”[2][3][1]

I’d introduce a minimal enum:

- `ExecutionMode.ANALYSIS` – read-only review/research/debug diagnosis
- `ExecutionMode.PATCH_PLAN` – propose changes (plan/diff) but don’t apply
- `ExecutionMode.REPAIR` – start from validator/test failures and generate fixes

Wire it through:

- `task_classifier.py`: map query → `(TaskType, ExecutionMode)` instead of just `TaskType`.[4][1]
- `prompt_templates.py`: choose slightly different Task Briefs depending on mode (e.g., ANALYSIS vs PATCH_PLAN).[1][2]
- `ai_cli.py`: pass mode into `_process_llm_results` and downstream formatting, so you can treat findings differently when they are suggesting edits vs just reviewing.[3][1]

This doesn’t change behavior by itself, but it gives you a clean axis to hang validation and patch logic on.

## 2. Make structured_response the canonical schema

Right now `structured_response.py` builds `Finding`, `CliResponse`, `AggregatedResponse` and has your new `build_needs_input_*` helpers.  You’ve effectively implemented the `summary + findings[]` contract in code, but the orchestrator still treats structured vs plain-text output as a choice.[5][1]

Next steps:

- Treat `CliResponse` / `AggregatedResponse` as the **canonical in-memory schema** for all JSON mode runs.
- Ensure `ai_cli.py` always goes through `build_structured_response(...)` for any JSON output from the target LLM, even when you don’t need aggregation.[3][5][1]
- Make the critic (`ai-cli-critic`) expect this schema by default, and treat free-form text as a fallback path only.[6][1]

You’ve already normalized NEEDS_INPUT at this layer; making it the one canonical schema closes a lot of drift risk.

## 3. Add a validation state machine in ai_cli

You’ve tightened the input side (targets, context, NEEDS_INPUT) and output shape, but validation is still an implicit phase.[1][3]

I’d introduce a minimal validation state machine in `ai_cli.py`:

- States:
  - `UNVALIDATED`
  - `VALIDATION_PASS`
  - `VALIDATION_FAIL`
  - `VALIDATION_INCONCLUSIVE`
  - `NEEDS_INPUT` (you already model this via findings)[5]
- For each run in `run_parallel_llm(...)` or the domain-specific path:
  - After LLM outputs are collected and parsed to `CliResponse`, run task-appropriate validators:
    - JSON/schema validity for the target contract,
    - path/snippet existence for locations in findings,
    - code-level checks (lint, tests, etc.) when the task+mode implies edits.[3][5][1]
  - Store validation results alongside the `CliResponse`/`AggregatedResponse` metadata.
  - Gate final formatting/printing on validation state:
    - If `VALIDATION_FAIL` and the task is `PATCH_PLAN` or `REPAIR`, either:
      - run one repair loop, or
      - return a clear failure with findings representing validator errors.

This is what turns `/ai-cli` into a system that “knows it must check the work” rather than hoping the critic or the user catches issues.[7][8][9][10]

## 4. Reposition the critic as semantic QA, not the only QA

`ai-cli-critic.md` is already written like a semantic verifier: it cares about unsupported claims, contradictions, overconfidence, and grounding.  Now that you have:[6][1]

- strict target/NEEDS_INPUT gating,[2][5][1][3]
- a normalized `Finding` schema, and
- tests ensuring canonical payloads,[1]

you can use the critic in a more focused way:

- Only invoke the critic **after** deterministic validation passes or is inconclusive.
- Feed the critic the structured findings plus validator metadata, not raw CLI logs, so it can reason over:
  - which findings lack evidence,
  - whether scope drift occurred,
  - whether the most severe findings have adequate grounding.[5][6]
- Have the critic output its own structured assessment (e.g., `critic_findings` with `grounding_status`, `overconfidence_flags`) and attach that to `AggregatedResponse.metadata` rather than interleaving it with primary findings.[5][1]

This keeps deterministic tests authoritative and makes LLM QA a second-layer check, which aligns with best practices for agent verification loops.[8][9][10][7]

## 5. Add minimal patch/repair plumbing (but don’t overbuild)

You don’t need a full patch engine yet, but your current design is ready for a **small** step:

- For `ExecutionMode.PATCH_PLAN` or `REPAIR`:
  - encourage the target LLM (via Task Brief) to put patch instructions or diff summaries into `findings.description` and tag those with `tags: ["patch_plan"]`.
  - run validators on a check-out or worktree copy after you apply those patches manually or with a simple script.
  - treat validator failures as either:
    - new `bug` findings (if you want the LLM to repair),
    - or a `needs_input` / `VALIDATION_FAIL` state if you require human intervention.

This gets you into a **generate → validate → repair** loop for at least one mode without changing your base contract or adding new schemas.[11][7][8]

## 6. Turn performance_logger into a router signal

`performance_logger.py` is already logging per-CLI stats and has `get_performance_stats`/`get_performance_stats_by_domain`.[12][1]

Next step:

- Surface those stats into routing decisions in `route_query_to_clis(...)` or `_determine_active_llms(...)`:
  - if a given CLI consistently underperforms for `TaskType.CODE_REVIEW` in your environment, de-prioritize it there,
  - while still using it for, say, `TaskType.RESEARCH` if it does well.[12][3][1]
- Start with a simple rule: prefer the top N CLIs by success rate/quality score for a given `TaskType` and domain, but keep at least one “exploration” CLI to maintain metrics.

This closes the loop between observation (performance logging) and behavior (routing), which is something your current pack has all the pieces for but doesn’t fully exploit yet.[12][3][1]

## If you want one concrete next ticket

Given everything in `ai-cli_full.md`, the single next thing I’d actually implement is:

- **Introduce a `ValidationResult` struct and wire deterministic validation into `run_parallel_llm(...)`**:
  - define `ValidationResult` with fields like `state`, `validators_run`, `failures`, `artifacts`,
  - attach it to `CliResponse.metadata` and `AggregatedResponse.metadata`,[1][5]
  - ensure that any `ExecutionMode` that implies edits cannot complete without a `VALIDATION_PASS` or explicit `VALIDATION_FAIL` surfaced to the user.

That gives you a visible, testable QA loop anchored in code, not just in prompt language or docs — and it uses tools you already have (`structured_response`, critic, tests, perf logger) rather than inventing new ones.[6][12][5][1]

If you share one of the concrete validator commands you’re using today (e.g., `pytest`, `ruff`, `mypy`, `tsc`), I can sketch exactly how to plug that into `ai_cli.py`’s flow with minimal disruption.

## Human

"Implemented the core recommendations that actually change /ai-cli behavior.
What changed:
Added a first-class ExecutionMode in task_classifier.py and threaded it through classification results.
Updated prompt_templates.py so the Task Brief now carries Execution mode: analysis|patch_plan|repair.
Added a compact validation state machine in structured_response.py:
ValidationResult
validate_response_shape(...)
the canonical NEEDS_INPUT payload helpers
Wired validation into ai_cli.py:
JSON-mode results now get validation metadata
malformed JSON or missing required keys are marked explicitly
target-required tasks still short-circuit to NEEDS_INPUT when no grounded target packet exists
Added execution-mode logging to performance_logger.py so we can later use it as a routing signal.
Updated the docs for the next person in:
SKILL.md
references/output-template.md
references/examples.md
references/context-handling.md
references/troubleshooting.md
references/cli-reference.md
Verification:
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-cli\tests -q
Result: 84 passed
What I intentionally did not build yet:
a full patch/appply engine
automatic routing decisions based on performance stats
Those are the next layer if you want to turn the new signal into active behavior. The current change set gets the contract, validation, and logging pieces in place first."

what should we do next?

## Assistant

You’ve done the right foundational work. The next step should be to turn the new signals into **active control flow**, not add more schema or docs. The two highest-value moves now are: add a real validation/repair loop, and start using your logged execution mode + validation outcomes to influence routing. Production agent workflows consistently converge on plan/implement/validate loops, with verification as the bottleneck and CI-style checks as the main guardrail.[1][2][3][4]

## Next build

### 1. Add a repair loop

You already have:
- `ExecutionMode`,
- validation metadata,
- NEEDS_INPUT gating,
- and execution-mode logging.[5]

So the next logical step is a bounded repair loop:

1. Run the target LLM.
2. Validate response shape and task-specific checks.
3. If validation fails and the mode is `patch_plan` or `repair`, feed the exact validator failures back into one repair pass.
4. Re-validate.
5. Stop after 1–2 retries max.

That gives `/ai-cli` a real **generate → validate → repair** cycle instead of just emitting a labeled failure. This pattern is widely recommended because cheap deterministic validation should happen before more expensive or ambiguous evaluation.[6][7][8]

## Validation design

### 2. Separate cheap and expensive validators

Right now you have the beginnings of a validation state machine. The next refinement is to classify validators by cost and confidence:

- **Cheap deterministic validators**: JSON/schema validity, required keys, path existence, line/snippet grounding, command construction sanity.
- **Medium validators**: syntax parse, lint, typecheck, targeted tests.
- **Expensive validators**: full test suites, semantic critic review, multi-model agreement passes.

Run them in that order, and bail early on hard failures. That avoids spending LLM or test budget on outputs that already fail basic contract checks. This cheap-before-expensive pattern is a recurring reliability recommendation in production agent systems.[2][9][7]

## Routing

### 3. Start using performance/validation as routing inputs

You explicitly did not build automatic routing yet, and that’s fine. But this is now the right next lever because you already log the relevant data.[5]

Start simple:
- For each `(task_type, execution_mode, cli_name)`, track:
  - success rate,
  - validation pass rate,
  - mean latency,
  - malformed-output rate,
  - NEEDS_INPUT rate.
- Prefer CLIs with the best validation pass rate for that mode.
- Keep one fallback/exploration CLI so the router does not get stuck in stale preferences.

This is better than static keyword routing because it uses observed behavior in *your* environment. Instrument-first, then route, is also a standard recommendation for production systems.[9][10]

## Editing safety

### 4. Add worktree-scoped patch execution before full apply

You said you did not build a full patch/apply engine yet. I still would not jump straight to “edit files in place.” Instead, add a **worktree or temp-copy execution layer** first:

- `patch_plan` mode should produce candidate edits or diffs.
- Apply them only in an isolated worktree / temp repo copy.
- Run validators there.
- Surface the validated diff back to the user.
- Only later consider auto-apply to the main workspace.

This gives you safety, rollback, and clearer validation artifacts. Worktree-based checkpointing and isolated execution are common practical patterns in agentic coding workflows.[11][2]

## QA roles

### 5. Make the critic a post-validator semantic verifier

You already have a critic prompt and now a validation state machine. The critic should not be the primary QA layer; it should sit *after* deterministic validation and answer narrower questions:

- Are the findings actually supported by the provided context?
- Did the model overstate confidence?
- Did it drift out of scope?
- Are proposed actions coherent with validator output?

That makes the critic far more useful and reduces false positives from using an LLM to judge things a parser or test runner could decide unambiguously. Verification-loop guidance strongly supports deterministic checks first, judge/verifier second.[8][12][13]

## Productization

### 6. Add release-gate style metadata and traces

Before you add more autonomy, add one more layer of operational discipline:
- version prompt contract and validator set,
- store validation outcomes with execution traces,
- include execution mode, task type, model, and validator results in the persisted artifact,
- make failures easy to inspect later.

Production guidance repeatedly emphasizes full traceability, versioning, and visible evidence over informal recollection when tuning agent systems.[7][10][9]

## What I would do next week

If you want the most practical sequence, I’d do this:

1. Implement one bounded repair loop for `ExecutionMode.REPAIR`.[5]
2. Add a validator registry with ordered cheap → expensive validators.
3. Record `validation_pass_rate` per `(task_type, execution_mode, cli)` in `performance_logger.py`.[5]
4. Use that metric in routing as a soft preference, not a hard rule.
5. Add isolated patch execution in a temp/worktree environment.
6. Reposition the critic as semantic QA only after deterministic checks.

That order gives you the biggest reliability gain with the least architectural churn. The foundation you just built is enough; now the goal is to convert those signals into **closed-loop behavior**.

## Human

what next?  "Implemented the higher-leverage reliability step, not just a narrow fix.
What changed:
Added a bounded one-time repair retry for malformed or empty structured responses in ai_cli.py.
The retry triggers for structured JSON runs, and for patch_plan / repair execution modes it enforces the JSON contract even if the outer output mode is text.
The retry prompt includes the exact validation failures plus a capped preview of the bad output.
Retry commands reuse the same lane and rewrite the prompt for list-form CLIs, so the repaired run is still written per model.
Added validation-state logging to performance_logger.py so the model history now records whether a lane passed validation.
Updated the source-of-truth docs in:
SKILL.md
references/cli-reference.md
references/troubleshooting.md
Verification:
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-cli\tests -q
Result: 88 passed
So the current behavior is:
one invalid structured response gets one repair retry
if that still fails, it stops and reports the failure cleanly
the retry attempt is still captured per model, so the orchestrator keeps full evidence"

## Assistant

The next step is to make failure handling and validation outcomes affect **routing and escalation**, not just repair. You now have a solid closed-loop foundation: one repair retry, validation metadata, and per-model evidence capture. Best practice after that is to make failure paths first-class, cap retries, distinguish transient vs permanent errors, and record repair/rollback rates so the system can adapt rather than just retry and report.[1][2][3]

## Highest-value next move

Build a **failure taxonomy + routing policy**.

Right now you have:
- one repair retry,
- validation state,
- per-lane evidence,
- and logging.[4]

What’s still missing is the policy layer that answers:
- When should we retry the same lane?
- When should we try a different model lane?
- When should we stop and emit `NEEDS_INPUT`?
- When should we escalate to critic review vs deterministic failure?

That policy layer is the biggest leverage point now, because otherwise you only have “retry once, then stop,” which is safe but not yet adaptive.

## What to implement next

### 1. Add explicit failure classes

Define a small internal enum like:

- `MALFORMED_OUTPUT`
- `EMPTY_OUTPUT`
- `SCHEMA_INVALID`
- `MISSING_REQUIRED_TARGET`
- `INSUFFICIENT_CONTEXT`
- `TRANSIENT_CLI_ERROR`
- `QUOTA_OR_CAPACITY`
- `TIMEOUT`
- `VALIDATION_FAIL_HARD`
- `VALIDATION_FAIL_SOFT`

This matters because different failure classes should trigger different policies. Production guidance consistently recommends separating transient, permanent, and policy failures rather than treating all failures as generic retry candidates.[5][6][3]

### 2. Add a retry/escalation policy table

Then map failure class × execution mode → action.

For example:

| Failure class | Analysis | Patch_plan | Repair |
|---|---|---|---|
| MALFORMED_OUTPUT | Repair once same lane | Repair once same lane | Repair once same lane |
| EMPTY_OUTPUT | Repair once same lane | Repair once same lane | Repair once same lane |
| QUOTA_OR_CAPACITY | Switch lane/model if available | Switch lane/model if available | Switch lane/model if available |
| MISSING_REQUIRED_TARGET | NEEDS_INPUT immediately | NEEDS_INPUT immediately | NEEDS_INPUT immediately |
| INSUFFICIENT_CONTEXT | NEEDS_INPUT or broaden context | NEEDS_INPUT | NEEDS_INPUT |
| VALIDATION_FAIL_SOFT | Return findings with warning, maybe critic | Critic or stop | Retry with validator feedback |
| VALIDATION_FAIL_HARD | Stop cleanly | Stop cleanly | Stop cleanly |

This is the moment where `/ai-cli` becomes a workflow engine instead of just a better wrapper. Agent reliability guidance strongly favors bounded, context-aware recovery paths over blanket retry logic.[2][3][1]

## After that

### 3. Use validation pass rate as a routing signal

You already log validation state. The next step is to route based on it:

- Prefer models with the best `validation_pass_rate` for `(task_type, execution_mode)`.
- Track:
  - first-pass success rate,
  - repair success rate,
  - malformed-output rate,
  - timeout rate,
  - NEEDS_INPUT rate,
  - average latency.[2]

Do not overcomplicate it yet. Start with a weighted score like:

- 50% validation pass rate
- 20% first-pass success
- 15% repair success
- 10% latency
- 5% cost or output size if you track it

This gives you adaptive routing with minimal complexity.

## Semantic QA

### 4. Add a verifier only for soft failures and high-risk outputs

A critic/verifier subagent is still useful, but now you can use it much more selectively:

- run it for `VALIDATION_FAIL_SOFT`,
- run it when findings are high severity but low evidence,
- run it when multiple lanes disagree materially,
- skip it for hard deterministic failures and obvious malformed outputs.

That keeps cost and latency down while still catching “looks plausible but unsupported” cases. Verification-loop patterns generally recommend deterministic gates first, human/LLM judgment second.[7][8][2]

## If you want one concrete ticket

If I had to pick **one** implementation next, it would be:

**Add `FailureClass` and `RecoveryAction` enums plus a `decide_recovery(...)` function in `ai_cli.py`.**

Inputs:
- execution mode,
- validation result,
- CLI error classification,
- retry count,
- lane availability.

Outputs:
- `RETRY_SAME_LANE`
- `RETRY_ALT_LANE`
- `EMIT_NEEDS_INPUT`
- `RUN_CRITIC`
- `STOP_CLEANLY`

That one abstraction will let the rest of the system grow without becoming a pile of `if/else` branches.

## After that, in order

1. Failure taxonomy + recovery policy.
2. Validation-pass-based routing.
3. Alternative-lane fallback for transient/quota failures.
4. Selective critic invocation for soft semantic failures.
5. Worktree/temp-copy patch validation before any auto-apply path.

That is the highest-leverage path from where you are now: not more prompting, not more schema, but **policy-driven recovery and routing**.
