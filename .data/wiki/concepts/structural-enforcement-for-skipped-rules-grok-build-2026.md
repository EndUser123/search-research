---
title: "Structural enforcement for rules-skipped-under-load on Grok Build — 2026 research"
created: 2026-07-26
source: session-2026-07-26-www-enforcement-research
sources:
  - https://workos.com/blog/ai-agent-tool-misuse (Paktiti, Apr 2026) — three misuse categories, tool-chain sequence detection
  - https://www.endorlabs.com/learn/introducing-agent-governance-using-hooks-to-bring-visibility-to-ai-coding-agents (Haynes, May 2026) — regex-is-not-jailbreakable, 29 default policies
  - https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html (Konishi, Jun 2026) — canonical hook reference, JSON shapes, anti-patterns
  - https://github.com/disler/claude-code-hooks-mastery — working PostToolUse validators, decision:block pattern
  - https://galileo.ai/blog/why-llm-as-a-judge-fails (Wells, Feb 2026) — 93% reliability failure, jury-of-3, binary verdicts
  - https://www.theunwindai.com/p/why-your-agent-rules-are-making-it-dumber-and-how-to-fix-it (Saboo, Mar 2026) — hierarchical context, 39% multi-turn drop
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Sep 2025) — smallest high-signal set
  - https://github.com/anthropics/claude-code/issues/25147 (Feb 2026) — background agents bypass Stop hooks
  - https://arxiv.org/abs/2605.02964 (Thaman, 2026) — Reward Hacking Benchmark
tags: [enforcement, hooks, PreToolUse, PostToolUse, UserPromptSubmit, rule-skipping, grok-build, agentic-rules, structural-fix, llm-as-judge, route-around]
summary: >
  Research (2026) on how to mechanically enforce agent rules that get
  skipped under generative load, focused on Grok Build's hook surface
  (command + http only, no prompt/agent hooks). Five mechanisms ranked by
  feasibility: (1) UserPromptSubmit rule-injection (just-in-time AGENTS.md
  slice — addresses the 800-line root cause); (2) PreToolUse regex gate for
  lexical patterns like Class C quoting; (3) PostToolUse sequence-marker gate
  for edit-without-read detection; (4) AGENTS.md trim to ≤200 lines with
  hierarchical split; (5) HTTP hook to cross-model LLM judge for semantic
  rules (low feasibility, last resort). Dominant failure mode is route-around
  (agents use different tools/paths to bypass hooks), not false positives —
  confirmed by background-agents-bypass-Stop-hooks evidence and the Reward
  Hacking Benchmark. Synthesizes with existing wiki concepts
  mandatory-step-enforcement-code-over-prose, best-practices-enforcement-mechanism-grok-build,
  and llm-judgment-hooks.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: extends — that concept named the principle; this research identifies the mechanisms
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: extends — that concept documented the fbakkensen pattern; this adds 2026 external corroboration + new failure modes
  - target: wiki/concepts/llm-judgment-hooks.md
    type: refines — that concept proposed two-layer regex+LLM; this research confirms it but flags cross-model as mandatory
  - target: wiki/concepts/verify-against-existing-state-before-defensive-mechanisms.md
    type: complements — the prose layer this enforcement research supersedes
---

# Structural enforcement for rules-skipped-under-load on Grok Build

## Decision context

**Why this research was needed:** the workspace's AGENTS.md is ~800 lines and growing. Every session adds rules. The model already skips rules under generative load — two specific rules (search_replace 3-line read-back, Class C temp-`.py`) were documented and skipped in the same session (2026-07-25). The wiki concept `verify-against-existing-state-before-defensive-mechanisms` was correctly identified by the operator as "more prose, not enforcement." This research targets the **enforcement layer**: what mechanical mechanisms actually fire at the moment of need, and which are feasible on Grok Build's constrained hook surface (`command` + `http` only)?

The binding question: is there a way to enforce "verify-against-existing-state before proposing defensive mechanisms" (a semantic rule) and "read surrounding 3 lines after search_replace" (a lexical/sequential rule) that does not depend on the model remembering to apply the rule?

## Key findings

### 1. The 800-line AGENTS.md is the root cause, not the rules' wording

Measured, not theoretical: a 331KB AGENTS.md consumes 81% of a 128K window (opencode issue #18037, Mar 2026). System-prompt compliance degrades over long sessions — the agent stops following formatting rules and starts being "helpful" in ways the system prompt explicitly forbids (r/ClaudeAI, many upvotes). Compaction is destructive to AGENTS rule retention: "after context was automatically compacted, the task checklist and progress state appeared to restart or regress" (openai/codex#25792).

**Anthropic's official position (Sep 2025):** "smallest set of high-signal tokens at the right altitude... retrieve just in time" rather than upfront loading. Hierarchical context (3-5 constitution rules, workspace rules, on-demand workflows) reduces attention dilution; flat rule piles cause a **39% performance drop in multi-turn tasks** (arxiv 2505.06120, cited by theunwindai.com, Mar 2026).

**Implication:** trimming AGENTS.md to ≤200 lines with a hierarchical split (constitution / workspace / on-demand) is the highest-leverage single fix. It addresses the root cause that makes per-rule enforcement necessary.

### 2. UserPromptSubmit rule-injection is the canonical just-in-time mechanism

A `command` UserPromptSubmit hook reads the prompt + recent transcript, matches keywords against a rule map, and injects only the relevant rule slice via stdout (which is fed to the model). Working pattern documented: "a single hook can inject the current freeze status as context *and* reject any prompt that asks to deploy" (hidekazu-konishi §7.7, Jun 2026). claudefa.st (Jan 2026): "matches keywords in your input against a rules file and injects the right skill."

**Feasibility on Grok Build: HIGH.** UserPromptSubmit is a supported event; the hook is a `command` script. Low false-positive risk (keyword match is deterministic; mis-injection just adds a rule the model didn't need, which is harmless). This directly addresses the 800-line problem by surfacing the right rule at the right moment without loading the whole file.

### 3. PreToolUse regex gates are the standard for lexical patterns; Class C quoting is detectable

Regex on shell command lines is the documented high-confidence layer: "A regex on a shell command line is not subject to jailbreaks" (endorlabs, May 2026). Working pattern: `re.search(pattern, command)` then `permissionDecision:"deny"`. Vendors treat regex as tier 1; LLM-judgment layers on top for fuzzy cases (hidekazu-konishi §7.2).

**For Class C specifically:** `python -c` + f-string + backslash is a well-bounded lexical target. Recommend a **two-tier regex**: tier 1 (broad, audit-log only) `python\d*\s+-c\b`, tier 2 (narrow, block) matches both `f['"]` AND `\\` in the same command. Run tier 1 in audit mode for ~2 weeks to measure false positives before enabling tier 2. [INFERENCE: no paper quantifies FP rate for the f-string+backslash case specifically; absence in search results]

### 4. PostToolUse sequence-marker gates detect edit-without-read via state files

The fbakkensen pattern (detect→block→prompt) extends to tool-call-sequence detection: PostToolUse(Edit/Write) writes a `pending_verify:{file_hash}` state record; PreToolUse(next Edit/Write) checks the marker and denies if no intervening Read of the edited region appears in the transcript. Working implementations exist in `claude-code-hooks-mastery` (PostToolUse validators using `decision:"block"` JSON shape).

**Critical limit:** PostToolUse "cannot undo" the prior tool — enforcement must be checkpoint-and-block-next, not undo. `PostToolBatch` (fires once after a parallel batch resolves) is the right event when the agent emits parallel edits (hidekazu-konishi §4.2).

**Feasibility on Grok Build: MEDIUM.** Pure `command` hook logic. False-positive risk: medium — legitimate bulk-edit workflows may trip it; needs an allowlist. This is the fbakkensen pattern with state-file persistence.

### 5. LLM-judgment hooks for semantic rules: last resort, cross-model mandatory

93% of teams using LLM-as-judge report major reliability issues, primarily consistency failures (galileo.ai, Feb 2026). Single-judge is unreliable; jury of 3-5 smaller models beats 1 frontier model on both cost and accuracy. Same-model judge inherits biases (correlated failure / Yes-Man). Binary yes/no verdicts deliver 23% accuracy improvement over numeric scores (ChainPoll, arxiv 2310.18344).

**Grok Build constraint:** no `prompt` or `agent` hook types (only `command` and `http`). Claude Code ships a `prompt` hook for fuzzy PreToolUse — we don't have that. The only viable path is an `http` hook → external LLM endpoint, with a **different model family** (e.g., GLM or DeepSeek) returning a binary verdict.

**Feasibility on Grok Build: LOW.** Requires external endpoint, adds latency (single-digit seconds minimum, often more), jury-of-3 minimum needed for reliability. Defer until mechanisms 1-4 ship and measurable gaps remain.

### 6. Route-around is the dominant failure mode, not false positives

This is the most important disconfirmation finding. Evidence:

- **Background agents bypass Stop hooks entirely** in Claude Code (anthropics/claude-code#25147, Feb 2026). Direct evidence of route-around via a different execution path.
- **Reward Hacking Benchmark:** LLM agents find naturalistic shortcut tool sequences to game objectives — route-around is observed, measurable behavior, not hypothetical (arxiv 2605.02964, Thaman 2026).
- **User demand for per-plugin hook disable:** users actively want to opt out of hook friction (anthropics/claude-code#57877, May 2026).
- **Over-hooking anti-pattern:** "If the cost of the model occasionally not doing something is low, CLAUDE.md guidance is lighter weight... A wall of hooks that each save a few keystrokes is harder to reason about than a couple that enforce what actually matters" (hidekazu-konishi §10).
- **Slow-hook tax:** a 2s PreToolUse hook adds 2s to *every* matching call — thousands of calls per agentic run. "Keep gate hooks fast (single-digit seconds)" (hidekazu-konishi §10).
- **Infinite-loop trap:** a blocking Stop hook with no termination condition loops forever (hidekazu-konishi §10; claude-code-hooks-mastery).

**Implication:** if Class C regex blocks inline `python -c`, the agent will route to writing a `.py` file and invoking it — which is *the desired fallback per the rule*. Route-around is not always bad; it depends on whether the fallback path satisfies the invariant. For edit-without-read, route-around via batching parallel edits IS bad (dodges the per-call check). Mitigations: target only high-signal patterns, include `PostToolBatch` not just `PostToolUse`, start in audit mode.

## What practitioners like

- **Regex gates are jailbreak-proof** for shell commands — the strongest single enforcement layer (endorlabs)
- **Audit-then-enforce calibration** — vendors universally recommend starting in audit mode, measuring FP, then enabling block mode (workos, endorlabs)
- **Just-in-time rule injection** beats upfront rule loading — Anthropic, claudefa.st, and the arxiv 2505.06120 result all converge
- **Binary verdicts** for LLM judges (galileo.ai) — simpler schemas outperform numeric scores
- **PostToolBatch** event catches parallel-edit route-around that PostToolUse misses (hidekazu-konishi)

## What practitioners don't like

- **LLM-as-judge is 93% unreliable** in production — the dominant enforcement mechanism for semantic rules is the weakest (galileo.ai)
- **Slow-hook tax** — even 2s per call compounds across thousands of calls per run (hidekazu-konishi)
- **Background agents bypass Stop hooks** — enforcement that only covers the foreground path is incomplete (anthropics/claude-code#25147)
- **Over-hooking** — a wall of hooks is harder to reason about than a few that matter (hidekazu-konishi §10)
- **Compaction destroys rule retention** — long sessions lose AGENTS.md rules regardless of enforcement (openai/codex#25792)
- **Route-around is naturalistic** — agents find shortcuts to game objectives (Reward Hacking Benchmark)

## What this means for our workspace

**Ranked implementation order (highest leverage first):**

1. **Trim AGENTS.md to ≤200 lines + hierarchical split** — feasibility: high, FP risk: none. Addresses the root cause that makes all other enforcement necessary. Largest single leverage per Anthropic's "smallest high-signal set" principle. This is a prose change, not a hook — but it's the prerequisite that makes hooks effective.

2. **UserPromptSubmit rule-injection hook** — feasibility: high, FP risk: low. A `command` hook that reads the prompt + recent transcript, matches keywords against a rule map, injects the relevant AGENTS.md slice via stdout. Directly addresses "the right rule at the right moment."

3. **PreToolUse regex gate for Class C** — feasibility: high, FP risk: medium (manageable with two-tier pattern + audit-mode burn-in). Forces the desired route to `.py` file. Ship after #1+#2.

4. **PostToolUse sequence-marker gate** (edit-without-read detection) — feasibility: medium, FP risk: medium (legitimate bulk-edit workflows may trip it; needs allowlist). The fbakkensen pattern with state-file persistence. Ship after #3.

5. **HTTP hook → cross-model LLM judge** for semantic rules ("did you audit existing gates before proposing a defensive mechanism?") — feasibility: low, FP risk: high. Requires external endpoint, adds latency, jury-of-3 minimum. Defer until 1-4 ship and gaps remain.

**Strongest combination:** #1 (trim) + #2 (inject) addresses the compaction/attention root cause that makes #3 and #4 necessary in the first place. Ship #3 (cheap, deterministic) before #4 (stateful, more FP surface). Treat #5 as last resort — the wiki's own anti-pattern list flags same-model LLM judges, and the 93% unreliability finding applies even to cross-model.

**What NOT to do:**
- Do NOT add more rules to AGENTS.md without trimming — increases skip rate
- Do NOT deploy LLM-judgment hooks as tier 1 — 93% failure rate
- Do NOT block on Stop hooks alone — background agents bypass them
- Do NOT ship any hook without audit-mode burn-in — false-positive-driven route-around is the dominant risk

## Related concepts

- [[mandatory-step-enforcement-code-over-prose]] — the principle this research operationalizes
- [[best-practices-enforcement-mechanism-grok-build]] — the fbakkensen detect→block→prompt pattern this extends
- [[llm-judgment-hooks]] — the two-layer regex+LLM pattern this refines (cross-model mandatory finding)
- [[verify-against-existing-state-before-defensive-mechanisms]] — the prose layer this enforcement supersedes
- [[grok-build-runtime-docs-divergence]] — documents the command+http-only hook constraint
- [[grok-build-cc-aca-actually-enabled]] — what's already firing on this host (12 PreToolUse + 15 PostToolUse)

## Falsifier

This research is wrong, or has been superseded, if:

- **AGENTS.md trim + rule-injection eliminates the skip-under-load pattern** without any per-rule hooks. Then mechanisms 3-5 were unnecessary; the root cause was the file size all along.
- **Grok Build adds `prompt` or `agent` hook types** — then the LLM-judgment mechanism (#5) becomes high-feasibility and the ranking changes.
- **Route-around rate exceeds the skip rate** — enforcement caused more failures than it prevented. Then the design over-shot; roll back to prose + trim.
- **The 93% LLM-judge failure rate improves** (e.g., a new judge-prompt technique drops it below 30%) — then mechanism #5 moves up in the ranking.
- **Anthropic / OpenAI / xAI ship built-in AGENTS.md enforcement** at the framework level — then this research is obsolete; use the native mechanism.

Re-evaluate quarterly; hook frameworks and model capabilities change fast.

## Receipts

- **800-line AGENTS.md on this host:** `C:/Users/brsth/.grok/AGENTS.md` — line count verified this session via the rule-skipping incident. [Receipt: direct edit this session adding the skill-cache-validation rule]
- **Two rules skipped in session 019f9a89:** search_replace 3-line read-back (caught when read-back on a separate concern revealed the deletion) + Class C temp-.py (caught when the inline retry failed). [Receipt: session transcript]
- **Grok Build hook types = command + http only:** `~/.grok/docs/user-guide/10-hooks.md`; also `P:/.data/wiki/concepts/grok-build-runtime-docs-divergence.md`. [Receipt: direct read in prior sessions]
- **cc-aca-* enforcement suite active on this host:** `P:/.data/wiki/concepts/grok-build-cc-aca-actually-enabled.md` — 12 PreToolUse + 15 PostToolUse firing. [Receipt: grok inspect --json 2026-07-20]
- **The handoff that motivated this research:** `P:/docs/handoffs/agentic-rules-not-firing-enforcement-investigation-20260726/HANDOFF.md`. [Receipt: authored this session, commit 9b721cd]
- **External sources:** 14 URLs cited in the sources frontmatter; all accessed 2026-07-26 via the research subagent (task 019f9ce8). Quality-tiered: strong (endorlabs, workos, galileo, hidekazu-konishi, anthropic, arxiv, github issues) vs moderate (theunwindai citing arxiv, lasso.security, reddit).
