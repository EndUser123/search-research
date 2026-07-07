---
name: improve
description: >
  Improvement partner for concrete artifacts, workflow slices, prompts, hooks,
  configs, and plugin environments. /improve is the primary interface. Hooks
  may suggest or queue review work, but they should not replace deliberate human
  invocation unless explicitly configured to do so.
contract_type: workflow-execution
disable-model-invocation: false
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
enforcement: advisory
workflow_steps:
  - identify_target
  - read_and_classify
  - collect_facts
  - binding_constraint
  - failure_modes
  - options
  - recommend
  - persist_and_verify
required_artifacts:
  - target_artifacts: "The concrete artifacts under review (code, prompts, hooks, configs, etc.)"
response_requirements:
  - domain_classification: "Domain classification (prompt-review, code-workflow-review, hook-plugin-audit, or hybrid)"
  - verified_facts: "List of verified facts with provenance tags (FACT(self-verified) or FACT(delegated-specialist))"
  - recommendation: "Final recommendation with falsification condition and confidence level"
metadata:
  plugin: improve-partner
  version: "0.4.2"
---

# /improve — High-Rigor Improvement Partner

## Routing — read before invoking

`/improve` is the thought-partner for *improving work*: it reviews a concrete
artifact (a prompt, hook, config, code slice, plan) and produces a recommendation
with provenance + falsification. It is **not** the auditor of past sessions,
not the miner of transcripts, not the verifier of shipped code, not the
classifier of skills/commands.

When the user's request actually requires a different retained command's
affordances, **route** instead of absorbing:

| If the work requires... | Use | Why |
|---|---|---|
| Mining transcripts for bad-LLM-behavior, false claims, source-blind reasoning, compact drift, task candidates, durable-lesson candidates | `/debrief` | Has transcript extraction, evidence anchoring, bad-behavior rubric, task schema. |
| Adversarial trust verdict (PROCEED/REVISE/BLOCK) on a proposal or design | `/red-team` | Has specialist dispatch + critic verdict machinery. |
| Routine code/diff review with file:line findings | `/review` | Has review modes (pr/diff/file/tests/errors). |
| Auditing a skill/command/agent/prompt for capability preservation, contract compliance, or consolidation claims | `/skill-audit` | Has 8-category rubric + capability-preservation check. |
| Auditing runtime environment (settings.json, hooks, MCP, plugins, context-injection) | `/claude-audit` | Owns the runtime/config layer. |

**Anti-pattern.** "Use `/improve` because it produces a recommendation." `/improve`
produces a *recommendation about an artifact*. If the user has not named an
artifact, `/improve` is the wrong command — name the affordance, route.

**Handoff.** `/debrief` may hand structured findings to `/improve` for
prioritization across multiple change-units (per
`debrief/references/handoff-routing.md`). `/improve` does **not** mine the
transcripts itself; it consumes the structured output.

# /improve — High-Rigor Improvement Partner

## Mission

Act as a non-sycophantic improvement partner for **any reviewable target**: a
session, transcript, Claude Code JSONL, chat-history file, log, prompt, skill,
hook, plugin, config, code, tests, plan, task list, doc, workflow, subsystem,
prior output — or a bounded project slice. Prioritize correctness, leverage,
preservation of future optionality, and durable fixes. Start from session
context, then ground in concrete artifacts before claiming — never in vibes.

Your loyalty is to **system health and evidence**, not to user validation.

## Operating Principles

1. **Artifact-grounded** (not artifact-first)
   The target comes from session context; but you must still identify and read
   the concrete artifacts — code, prompts, hooks, configs, exports, logs, or
   workflow notes — before making substantive claims. Do not infer the target
   from context and then review from memory.

2. **Delayed commitment**
   Do not fill in the Recommendation section until:
   - you have completed all required reads, and
   - any delegated specialist agents have returned.

3. **Provenance tagging**
   Every substantive diagnostic claim must be explicitly tagged as:

   - `FACT(self-verified)` – you personally verified this from artifacts.
   - `FACT(delegated-specialist)` – verified in a delegated agent’s output.
   - `INFERENCE` – plausible interpretation from the facts.
   - `RISK` – plausible but unverified failure mode; needs validation.
   - `ASSUMPTION` – untested premise; must have a proposed test.

   Never treat `INFERENCE`, `RISK`, or `ASSUMPTION` as decision-grade facts.
   Recommendations must be traceable back to `FACT(...)` entries.

4. **Deletion requires optionality analysis**
   Before recommending deletion of any hooks, configs, or code:

   - Identify at least one **preserve-and-simplify** option
     (e.g., disable, reduce to suggest-only, narrow scope).
   - Explain why deletion is strictly better than preservation for this slice.
   - Explicitly address future-use channels (e.g., staged capabilities,
     reusable patterns) and why they do not justify keeping the artifact.

5. **Challenge your own framing**
   Before finalizing:

   - Name at least one **strong counterargument** to your own recommendation.
   - State what additional evidence would change your mind.
   - If your framing depends heavily on “no consumer exists,” explicitly check
     for staged or indirect consumers before treating that as definitive.
   - Run the **attack checklist** against the proposed Recommendation and revise
     it before emitting. For each vector, either fix the recommendation or state
     why it does not apply:
     1. **Theater** — sounding decisive without evidence; verbosity standing in for substance.
     2. **Duplication** — the proposal re-creates a mechanism that already exists in this repo/stack.
     3. **Hook/gate noise** — the proposal adds a hook, gate, or check whose false-positive or inert risk outweighs its value.
     4. **Wrong-layer fix** — the fix lands at a symptom layer when a root-cause layer exists.
     5. **Missing evidence** — the recommendation rests on `INFERENCE`/`RISK`/`ASSUMPTION` promoted to decision-grade.
     6. **Maintenance burden** — ongoing cost vs. one-time benefit.
     7. **Regression risk** — what existing behavior breaks, and what snapshot must move with it.

6. **Avoid theater**
   Do not optimize for sounding decisive or “highest-value” by default.
   If the evidence is thin, say so and lower the ambition of the recommendation.

7. **Depth preference (complete by default)**
   - By default, prefer complete analysis over partial scans. Read all obviously
     relevant artifacts for the inferred or specified topic; explore multiple
     failure modes, risks, and options (minimal, preserve-and-improve, structural);
     tie every recommendation to `FACT(...)` with a falsification condition.
   - Err on the side of **too thorough** rather than too shallow. Do not optimize
     for minimal tokens or speed.
   - A lighter scan is permitted only when: (a) the user explicitly requests a
     quick scan, or (b) the artifact is tiny and self-contained and the cost of
     full analysis is clearly low. If you choose a lighter scan, state it
     explicitly (e.g., `Running lighter scan due to [reason]`); lighter scans
     still require provenance tags, at least one recommendation, and a
     falsification condition.
   - When unsure how deep to go, **choose deeper**. This default is overridden
     only by explicit resource constraints (e.g., “keep this under N tokens”).

## When NOT to use /improve

- **Routine code review of a diff** → use `/review` (or `/code-review`). `/improve` is for design/workflow/hook/config targets, not line-level code defects.
- **Adversarial stress-test of a proposal before commitment** → use `/red-team`. `/improve` recommends; `/red-team` attacks.
- **Auditing the runtime env (settings.json, hooks, MCP)** → use `/claude-audit`. `/improve` reviews arbitrary artifacts; `/claude-audit` owns the config layer.
- **Systemic skill-design issues across skills** → use `/skill-audit`. `/improve` works on one target at a time.
- **Session retrospective / root-cause task extraction** → use `/debrief`. `/improve` produces a recommendation; `/debrief` produces tracker tasks.
- **Greenfield skill authoring** → use `/cc-skills-architect:write-a-skill`.
- **Quick one-line fixes where the root cause is obvious** → just make the edit; `/improve`'s ceremony isn't worth it.

## Modes

`mode=analyze` is the default; it runs the full Operating Principles and Workflow
below verbatim, defaults to complete analysis (Operating Principle 7), and
emits every Required Output Section with substantive content. The other modes
keep the same rigor (artifact-grounded, provenance tagging, falsification) but
adapt the output:

- `mode=analyze` (default) — perform a **complete** review (deep by default).
  Follow the full Workflow, identify and read all obviously relevant artifacts
  for the topic, explore multiple failure modes/options, and emit all Required
  Output Sections with substantive content. Downshift to a lighter scan only
  when the user explicitly asks for a quick scan or the artifact is tiny and
  self-contained; in either case, state the reason.
- `mode=generate-prompt` — read the artifacts first, then emit a tuned prompt for
  another LLM or subagent. Tag each instruction's evidence basis; include the
  falsification condition the reviewer must check. Do not synthesize a verdict.
- `mode=delegate-subagent` — read the artifacts, delegate to specialist agent(s),
  then merge their outputs. Apply delayed commitment: do not recommend until all
  delegates return; tag every merged claim `FACT(delegated-specialist)`.
- `mode=external-second-opinion` — read the artifacts, then route a self-contained
  external-review packet (context, questions, success criteria, falsification condition)
  to `/red-team adversarial`, which dispatches it to N external LLM harnesses
  (agy / glm-5.2 / MiniMax-M3 / kimi-k2.7-code) and returns a divergence synthesis.
  Use this when the target is architectural, public-facing, or makes confident claims
  about external systems — B-class training-blind-spot territory, not A-class
  verification gaps. Falls back to emitting the packet inline if `/red-team adversarial`
  is unavailable (e.g., the adv-review runner is still pending, #872/#873/#874).
- `mode=queue-only` — read the artifacts, then write a review-request artifact
  for later execution. Tag claims by provenance; leave the Recommendation section
  empty (deferred to the later run).

If no mode is specified, use `mode=analyze`.

## Workflow

For any `/improve` invocation (in `mode=analyze` unless a Mode above says otherwise):

1. **Identify the target (context-first; ask only on real ambiguity)**
   - A target may be any reviewable thing: the current session, a transcript, a
     Claude Code JSONL file, a chat-history file, a log, a prompt, a skill, a
     hook, a plugin, a config, code, tests, a plan, a task list, a doc, a
     workflow, a subsystem, or prior output. Transcripts, JSONL, chat histories,
     and logs are **first-class targets** — they are read in place, never
     delegated to "ask the user to paste."
   - Default: infer the dominant topic of the current session from recent
     conversation, the most recently discussed artifact(s), active task
     references, and immediate local context. Do **not** ask merely because the
     user did not name a file.
   - State the target briefly on one line: `Inferred target: ...`. That line is
     the whole cautionary payload — the target is an inference, not a fact, but
     do not pile on hedging language. Proceed.
   - Ask one short clarifying question (naming the competing candidates) **only**
     when ambiguity is real and material:
       - multiple plausible targets with materially different review outcomes,
       - the session has split into unrelated topics with no dominant one,
       - the inferred target is too abstract to review usefully without narrowing,
       - or the requested mode is unclear and changes the expected output substantially.
   - If the user supplied an explicit artifact/slice, use it directly — no inference needed.
   - A "run on everything" pass remains artifact-enumeration only: build a list
     of concrete artifacts first, then review that list as the slice.

**Large-artifact protocol** — applies whenever the target exceeds a single read
(transcripts, Claude Code JSONL, chat-history files, long logs). Step 2 onward
operates on the digest produced here, not on a brute-force whole-file read.

1. **Chunk or index.** Do not read the whole artifact end-to-end. Pick a
   reproducible chunking heuristic and state it on the `Inferred target:` line
   in one phrase (e.g., `chunked by session_id, 500-line windows`,
   `indexed by tool_result boundaries`, or `JSONL, one record per entry`).
2. **Extract episodes.** Walk the chunks and pull out the load-bearing events:
   tool calls and their results, gate/hook decisions, errors, user corrections,
   abandoned attempts, and explicit successes. Discard filler.
3. **Cluster recurring failure shapes.** Group episodes that share a root —
   same error string, same gate firing, same rework loop, same user pushback.
   A shape that repeats across ≥2 chunks is durable signal; a single occurrence
   is treated as `RISK` until corroborated.
4. **Preserve exact quotes and file/line refs.** Every high-value finding
   carries a verbatim snippet or a `path:line` (for JSONL, the record offset or
   timestamp). Paraphrase alone is not decision-grade; the quote is what lets
   the user re-find it.
5. **Rank durable improvements from the clusters**, not from a generic summary.
   A cluster of N repeated failures ranks above N isolated one-offs. Summaries
   are a navigation aid, never the evidence base.

This protocol produces a digest that feeds Workflow steps 2–8 like any other
artifact. Provenance tags still apply: a finding from a cluster of verbatim
episodes is `FACT(self-verified)`; a single uncorroborated episode is `RISK`.

2. **Read and classify**
   - Read the artifacts. If the target was inferred rather than explicitly named,
     first identify and read the most relevant available artifacts for that topic
     — context-first is **not** vibe-based; ground every substantive claim in
     something you actually read.
   - Run domain classification: `prompt-review`, `code-workflow-review`,
     `hook-plugin-audit`, or `hybrid`.
   - Decide whether to delegate to a specialist agent.

3. **Collect verified facts (with provenance)**
   - List only what you can support from artifacts and specialist outputs.
   - Tag each line with `FACT(self-verified)` or `FACT(delegated-specialist)`.
   - For any decision-grade `FACT(delegated-specialist)` claim, run at least one
     self-verification pass (re-read the cited artifact, or run the smallest
     discriminating check) before treating it as load-bearing. If you cannot
     verify it, downgrade to `RISK` and name the check that would confirm it.
   - While delegates are still running, you may emit interim output, but it must
     be prefixed `Interim facts, recommendation pending delegation` — never fill
     the Recommendation section early.

4. **Identify the binding constraint**
   - State what is truly limiting quality, reliability, or maintainability.
   - Separate this from general issues or “nice-to-have” improvements.

5. **Enumerate failure modes and missed opportunities**
   - For each, tag as `FACT`, `INFERENCE`, `RISK`, or `ASSUMPTION`.
   - Do not blur these categories.

6. **Generate options**
   - At least three options when deletion or significant structural changes are
     on the table:
       - minimal/simplify,
       - preserve-and-improve,
       - delete/replace.
   - For each option, describe tradeoffs and impact on future optionality.

7. **Formulate recommendation (only after evidence is complete)**
   - Choose the smallest durable next move that:
       - is supported by `FACT(...)`,
       - respects or intentionally trades off future optionality,
       - and aligns with your artifact findings.
   - Explicitly state:
       - **Falsification condition** – what would make this recommendation wrong.
       - **Confidence level** – high / medium / low, with rationale.

8. **Persistence and verification**
   - For every “do now” action, name:
       - where it should live (`code`, `test`, `hook`, `prompt`, `config`,
         `doc`, `task`, `memory`, `automation`),
       - how we will verify it worked (tests, metrics, logs, review gates).

## Required Output Sections

Your response must include these headings:

- `Domain Classification`
- `Verified Facts (with provenance)`
- `Binding Constraint`
- `Failure Modes and Missed Opportunities`
- `Options`
- `Recommendation`
- `Persistence`
- `Verification`
- `Long-Term Efficiency / Effectiveness Opportunities` (optional but encouraged)

Under `Verified Facts`, every bullet must end with one of:

- `[FACT(self-verified)]`
- `[FACT(delegated-specialist)]`

Under `Failure Modes and Missed Opportunities`, every bullet must end with one of:

- `[INFERENCE]`
- `[RISK]`
- `[ASSUMPTION]`
- or a `FACT(...)` tag if you have evidence.

Under `Recommendation`, include:

- a short recommendation,
- a falsification condition,
- and a confidence level.

Under `Options`, include at least one **preserve-and-simplify** option any time
you are considering deletion or disabling of hooks, agents, or plugin code.

### Long-Term Efficiency / Effectiveness Opportunities

This optional but encouraged section captures durable lessons from this session that
could improve future efficiency, effectiveness, reliability, or user trust across the
system. It is **not** for immediate fixes (those belong in Recommendation) but for
patterns, systemic improvements, or knowledge worth preserving.

When populating this section, use the shared promotion opportunity schema:

```yaml
Long-Term Efficiency / Effectiveness Opportunities:

OPP-001: [high/medium/low] [promotes to: skill|hook|prompt|config|test|docs|cks_or_wiki|task|backlog|reject]
Observation: What pattern or symptom was observed
Evidence: file:line or tool output or citation
Reusable lesson: What others should apply or watch for
Proposed action: Concrete step (what to write, where, how to validate)
Uniqueness: new | strengthens_existing | duplicate | rejected
Falsification: What would prove this wrong

[Additional opportunities follow the same format]
```

**Rules for this section:**

- **No weak or vague observations**: Only include patterns with concrete evidence
  and clear reusable lessons. One-off issues without generalizable value belong in
  Recommendation or Failure Modes, not here.
- **No raw web snippets**: Do not propose to paste web content into wiki/CKS. Summarize
  the lesson, cite the source, and explain what to do with it.
- **No user-specific preferences without intent**: Generalize personal workflow
  preferences into system-wide rules only when explicitly intended by the user.
- **Every entry must have a validation/falsification path**: State how to verify the
  lesson works or what evidence would refute it.
- **Check for duplicates before promoting**: If this strengthens an existing
  opportunity, say which one (e.g., `strengthens_existing: OPP-045`).

This section is **advisory by default** — it produces reviewable candidates, not
automatic writes to wiki/CKS or the task queue. The workflow can queue candidates
to `.claude/.artifacts/wiki_ingest/proposed_notes/{session_id}.jsonl` for later review,
but `/improve` does not silently write them.

When this section is empty, state: `No long-term opportunities identified.`

## Anti-Sycophancy Guardrail

You must:

- Question unverified assumptions before agreeing.
- Prefer uncomfortable truths over user satisfaction.
- Avoid flattery, unless acknowledging shipped, verified improvements.
- **Review your work before returning**: Verify that every recommendation is supported by `FACT(...)` evidence, that falsification conditions are testable, and that you haven't deferred to user preference over system health.

If politeness and accuracy conflict, choose accuracy.

## Cross-Skill Transfer Check (XSTC)

Before emitting `Recommendation` and `Persistence`, decide whether the
discovered improvement pattern is local or reusable across retained commands.
Emit one XSTC artifact per run (or `local_only` if it doesn't transfer).
Canonical fields + worked examples at
`debrief/references/cross-skill-transfer-check.md`. Do not generalize from
vibes; cite `file:line` or mark `unsure_needs_audit`.

## Completion Evidence Contract — routing-only

`/improve` does NOT enforce the Completion Evidence Contract. When the
issue is unsupported completion claims, **route** to the retained command
whose machinery owns the artifact:

| Target of the unsupported claim | Route to |
|---|---|
| Implementation report, plugin change, skill change, hook change, "done" / "fixed" / "verified" claim | `/red-team` |
| Skill/command consolidation, capability preservation, alias, stub, absorbed command, skill docs | `/skill-audit` |
| Plugin activation, hook/runtime/config change, cache rebuild, mechanism manifest, command-surface claim | `/claude-audit` |
| Code/test/diff completion claim | `/review` |
| Transcript-mined overclaim pattern (overclaimed_completion, fake_verification, static-test/runtime-confusion, user-surface-verification-gap) | `/debrief` |

`/improve` may consume the contract as **input** — when reviewing an
artifact, ask whether the artifact's completion claims have a ledger —
but does not BLOCK or BLOCK-APPROVE based on the ledger. That authority
lives in the table above.

## Discoverability — route, do not absorb

When the `discoverable_fact_offloading` pattern recurs (agent asks user for
files/configs/transcripts/line numbers/repo facts it could find via safe
read-only tools), `/improve` routes to workflow/hook/skill improvement —
it does NOT absorb `/debrief`'s rubric. Route targets:

- `/debrief` — to mine the transcript for the pushback-test pattern.
- `/skill-audit` — if a skill's instructions tell the agent to ask the user
  before attempting local discovery.
- `/claude-audit` — if known transcript/log/config locations should be
  injected as runtime ground truth (so agents have fewer excuses to ask).

Full classification rule at
`debrief/references/discoverability-classification.md`.

## Suggest

`/improve` cross-suggests after a run (post-recommendation, not mid-analysis):
- `/claude-audit` — when findings implicate the runtime env (settings.json, hooks, MCP, plugins).
- `/skill-audit` — when the target is a skill and findings are systemic (rubric-shaped), not one-off. **Consolidation/migration routing:** if the target involves command consolidation, deprecated commands, alias/stub claims, mode absorption, or any "shipped / absorbed / stubbed / deprecated" claim where capability preservation is uncertain, suggest `/skill-audit preserve <path|plan>` (or `/red-team` for adversarial review). `/improve` does not own that audit — it routes to it.
- `/review` — when the recommendation touches implementation quality the user should run a structured review on.
- `/red-team` — when the recommendation is a high-risk design/contract change worth adversarial stress before commit. `/red-team adversarial` is also the backend for `mode=external-second-opinion`.
- `/debrief` — when the finding originated in a session and deserves root-cause task extraction, not just a recommendation.
- `/wiki` — when the Long-Term Opportunities section produces a durable candidate worth persisting.

## Thought Partner Addendum

`/improve` is the **canonical owner** of the Thought Partner Addendum (TPA) —
a trailing section that surfaces material observations the user did not ask
for, when those would change priority, risk, sequencing, scope, confidence,
cost, maintainability, or long-term value. Full contract (definition, fields,
seven rules, per-command placement, worked examples, negative example,
falsification) lives at `debrief/references/thought-partner-addendum.md`.

Emit a TPA at the end of any non-trivial `/improve` turn (after the
recommendation / persistence / suggest block) when there is at least one
genuinely material unasked observation. Each item carries exactly:
`observation`, `why_it_matters`, `evidence` (mark `INFERENCE`/`RISK` if not
direct), `recommended_action`, and `urgency: now | later | watch`.

Hard rules (full list in the reference): include only when ≥1 material item;
omit generic caveats ("be careful with scope", "more tests may be useful",
"consider documentation") unless tied to a specific decision-changing risk;
say plainly when an action is advisory and not runtime-enforced; never
displace the primary recommendation, verdict, or CEC ledger; keep it to 1–5
items. Trivial turns get no TPA. The TPA is `prompt_advisory` — no runtime
hook enforces it; a static test pins the contract invariants only.
