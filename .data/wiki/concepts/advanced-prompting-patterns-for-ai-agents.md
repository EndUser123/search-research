---
title: "Advanced prompting patterns: workflows, loops, context, delegation, anti-sycophancy"
concept_type: "research-finding"
created: 2026-07-24
agent: grok
host: grok
verification: "web-research-backed"
sources:
  - "Anthropic 'Effective context engineering for AI agents' (Sep 2025)"
  - "LangChain context isolation patterns"
  - "Hong et al., SYCON Bench (2025)"
  - "Promptfoo, Braintrust, Lilypad/Mirascope eval frameworks"
  - "Google DeepMind 'Intelligent AI Delegation'"
cognitive_load: 4
---

# Advanced prompting patterns: workflows, loops, context, delegation, anti-sycophancy

## Decision context

**Why this was needed:** the first prompting-patterns wiki concept covered 10
structural techniques from a single session's transcript. This concept extends
coverage to patterns the industry has published but we hadn't documented:
workflow orchestration, goal loops, context engineering, delegation, and
anti-sycophancy. Researched via 4 parallel M3 subagents.

## Workflow orchestration

1. **Explore → Plan → Implement → Commit pipeline** — read-only exploration first, then numbered plan with per-phase verification, then thin vertical slices with commits. Prevents solving the wrong problem.

2. **Orchestrator-worker with verification gates** — planner delegates subtasks, separate verifier asks "is this correct enough to support dependent steps?" Verification gate is the unit of reliability.

3. **Structured artifact handoffs** — each phase emits typed output (JSON, Markdown template) so downstream consumes a contract, not free-form prose. Explicit schemas let consumers reject malformed output.

4. **Plan mode vs Act mode as hard switch** — read-only sandbox for exploration, explicit transition to mutating tools. Forces operator-visible review at the plan, not the diff.

## Goal loops

1. **Goal-based prompting with verifiable success criteria** — describe desired end state and how "done" is measured (tests pass, schema validates, score above threshold). Abstract goals need detailed specs because they can't be checked.

2. **Reflexion loop with stored critique** — attempt, self-evaluate, write reflection to memory, retry with critique injected. Memory step converts repeated failure into learning signal. Took HumanEval from ~80% to ~91% on GPT-4.

3. **Ralph-style outer loop** — shell loop resets context each iteration while persisting state to files; stop hook enforces termination criteria. Fresh-context-per-iteration solves context overflow and premature "done."

4. **Inner/outer dual loops** — outer owns strategy and progress-against-goal, inner owns step execution. Outer resets on stalls, inner stays myopic. Tune reasoning depth independently of action granularity.

## Context engineering (Anthropic, Sep 2025)

1. **Smallest high-signal token set** — include only minimal information that outlines expected behavior; exclude anything that doesn't change output. Aim for "right altitude" between brittle logic and vague guidance.

2. **Tool-result clearing and compaction** — once evidence is extracted from a tool call, drop the raw result. As window fills, summarize decisions and bugs while discarding redundant outputs.

3. **Just-in-time retrieval** — hold file paths, queries, and links as references; let agent fetch on demand. Hybrid: stable conventions loaded upfront, dynamic content explored as needed.

4. **Structured note-taking / agentic memory** — persist progress notes, TODOs, achievement logs outside context window; re-read after compaction. Preserves goals that summaries can't re-derive.

5. **Sub-agent context firewalls** — focused sub-agents explore with clean context, return distilled summaries (~1-2K tokens). Isolates token-heavy objects so unrelated exploration can't bleed into orchestrator reasoning.

## Delegation and tool-use prompting

1. **Task packet scaffolding** — self-contained packets with objective, ranked key files, constraints, validation criteria, output format. Subagent starts productive work without rediscovering context.

2. **Spec-driven prompting** — fixed schema (GOAL/SCOPE/CONTEXT/ACCEPTANCE/STOP/TOOLS) replaces casual asks with verifiable contracts. Defines halt conditions and closed-loop feedback targets.

3. **Error-as-prompt directives** — return tool failures as structured, agent-facing instructions (error type, reason, NEXT_ACTIONS, prohibitions). Converts errors into actionable recovery plans.

4. **Recursive task decomposition** — break goal into atomic, verifiable, bounded subtasks in a dependency graph; recurse until each leaf is independently executable. Enables parallelism and failure isolation.

5. **ReAct reflection loops** — interleave Thought/Action/Observation with explicit post-step reflection ("did output match expectations? if not, diagnose root cause and propose 1-2 alternatives").

## Anti-sycophancy prompting

1. **Explicit anti-agreement directives** — system-level rule requiring the model to challenge assumptions, name errors, and refuse automatic agreement. Pair with softened variant to avoid over-correction into combativeness.

2. **Third-person persona framing** — assign named persona with stated values; answer in first-person as that persona. Raises Turn-of-Flip resistance by up to 63.8% in debate scenarios.

3. **"Ask don't tell" rephrasing** — convert confirmatory statements into neutral questions ("This is fine, right?" → "What problems might this have?"). Decouples model from user's premise.

4. **Force critical structure** — require alternatives enumeration, pros/cons, missing information, and argued opposite position before any recommendation. Structures dissent into the response.

5. **Process controls** — require confidence levels, citations, fact/opinion labels; start fresh chats for critical decisions to avoid context priming. Ask for independent view before sharing yours.

## Prompt testing (TDD for prompts)

1. **Test-first eval datasets** — define success criteria (format, accuracy, tone, tool-use correctness, cost) and build 10-50 case golden dataset before writing the prompt.

2. **LLM-as-judge + multi-scorer** — combine rule-based assertions for hard constraints with rubric-based LLM judges for qualitative dimensions, plus human spot-checks.

3. **Version everything** — treat prompt as versioned artifact alongside model, temperature, context. Promptfoo, Braintrust, Lilypad operationalize this with YAML configs and CI integration.

4. **Continuous eval in CI/CD** — gate deployments on eval scores; feed production traces back to grow coverage from real failures.

5. **Self-improving loops with safeguards** — let AI propose prompt improvements, validate against frozen eval. Works only when tests are immutable ground truth.

## Preventing laziness and premature delegation

1. **Dependency-aware task graphs with evidence-of-work** — decompose into atomic subtasks with dependencies; require artifacts (logs, reason strings) to close each node. Makes skipping structurally impossible.

2. **Orchestrator-first decomposition** — parent fully decomposes before spawning sub-agents; sub-agents receive narrow tasks with explicit inputs/outputs/success criteria. Prevents over-delegation and accountability gaps.

3. **Capability matching** — define when to delegate (specialization, load) vs keep in-house (high-stakes, irreversible). Google DeepMind treats delegation as authority transfer with trust and monitoring.

4. **Self-evaluation laddering** — require agent to plan, execute, verify, self-score thoroughness (1-10), list incomplete aspects; revise if below threshold.

5. **Least-privilege tools + human gates** — restrict each agent to only tools and data needed; require human approval for irreversible actions.

## Related wiki concepts

- [[prompting-patterns-for-ai-agent-control]] — the original 10 patterns from session 019f7e24
- [[mandatory-step-enforcement-code-over-prose]] — why structural enforcement beats prose
- [[fabricated-causal-chain-receipt-required]] — receipt-first principle
