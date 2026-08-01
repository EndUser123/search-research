---
title: "Mutation receipt patterns for AI agent file ownership"
concept_type: "research-finding"
created: 2026-07-24
agent: grok
host: grok
verification: "web-research-backed"
sources:
  - https://ranthebuilder.cloud/blog/agentic-coding-hooks-deterministic-ai-guardrails/
  - https://dotzlaw.com/insights/claude-hooks/
  - https://www.youtube.com/watch?v=irK4G2SzhpA (Git AI by Aidan Cunniffe, DevCon Fall 2025)
  - https://www.reddit.com/r/AI_Agents/comments/1qtdppm/git_ai_coding_how_do_we_track_who_wrote_this/
cognitive_load: 3
---

# Mutation receipt patterns for AI agent file ownership

## Decision context

**Why this research was needed:** we built a mutation-receipt system (PreToolUse + PostToolUse hooks that record file hashes before and after write-capable tool calls) to prove file-change ownership for `/close` auto-commit. We needed to know: (1) whether this pattern exists elsewhere, (2) what the industry knows about hook-based file tracking that we might be missing, and (3) what libraries or standards we should be aware of.

## Key findings

### 1. Git AI — open-source git extension for AI code attribution

**Git AI** (by Aidan Cunniffe, DevCon Fall 2025) is an open-source git extension that tracks which lines of code were AI-generated. It:

- Attaches **git notes** to every commit storing line-level AI attribution + the prompt that generated each block
- Integrates via **hooks** with Cursor, Claude Code, Copilot, and other agents
- Survives rebase, merge, cherry-pick — notes sync through real-world git workflows
- Is **explicit, not heuristic** — requires agents to mark their own output; doesn't guess
- Tracks prompts alongside code lines for future context recovery

**Relationship to our system:** Git AI tracks *which lines* an agent wrote (attribution analytics). Our mutation receipts track *which session owns which file changes* (commit safety). Both use hooks and explicit attribution. Git AI's git-notes approach is complementary — it could coexist with our receipt system for richer attribution.

**[HIGH]** confidence — demonstrated live at DevCon, working with multiple agents, open source.

### 2. Four hook architectural patterns (dotzlaw.com)

The industry recognizes four hook patterns for AI coding agents:

| Pattern | Event | Purpose | Our equivalent |
|---------|-------|---------|---------------|
| Safety Layer | PreToolUse | Block dangerous actions (deny/allow) | Our PreToolUse hook for pre-state capture |
| Quality Feedback Loop | PostToolUse | Inject quality feedback (lint errors) | Our PostToolUse hook for post-state + receipt |
| Observability | All events | Log everything for debugging | Our trace log + receipt accumulation |
| Completion Gate | Stop | Block session end until condition holds | Our quality-gate Stop hook |

**[HIGH]** confidence — multiple independent sources (dotzlaw, ranthebuilder.cloud, Reddit threads) describe the same pattern taxonomy.

### 3. Our mutation-receipt pattern is novel

None of the researched sources describe our specific pattern: **Pre/Post hooks for evidence accumulation that feeds a later safety decision** (not real-time gating). The industry pattern is:

- PreToolUse = deny/allow at the point of action
- PostToolUse = quality feedback injected back into context

Our pattern is:
- PreToolUse = capture pre-state (file hash, git dirty list)
- PostToolUse = capture post-state, write receipt (not injected back into context)
- Stop (/close) = consume accumulated receipts for commit-safety decision

This is a **fifth pattern**: evidence accumulation for deferred safety decisions. It sits between Observability (passive logging) and Safety Layer (real-time gating).

**[MEDIUM]** confidence — the novelty assessment is based on absence in searched sources, not exhaustive proof.

### 4. Best practices we should know about

From Ran Isenberg (AWS Serverless Hero) and dotzlaw.com:

- **Use hooks sparingly:** every matching tool call pays the hook cost. Keep hooks for "the critical few" — destructive commands, secrets, ownership.
- **Keep hook scripts fast:** hooks execute synchronously. Linting a single file should take <5 seconds. Heavyweight analysis belongs on Stop hooks, not PostToolUse.
- **Per-agent hooks more effective than global:** a CSV agent needs CSV validation; a build agent needs linting. Global hooks waste computation on irrelevant checks.
- **additionalContext > deny/allow:** the most powerful hook pattern is injecting context that helps the agent self-correct, not just blocking.
- **PreCompact hooks reveal lost context:** if agents seem confused after long sessions, PreCompact logs show what was forgotten.
- **File ownership boundaries via directory maps:** PreToolUse can enforce that "frontend-dev" agent only writes to `src/components/` — directory-based ownership, not content-based.

**[HIGH]** confidence — multiple independent practitioners report the same practices.

## What this changes

1. **Our mutation-receipt system is not redundant** with Git AI — they solve different problems (commit safety vs attribution analytics). But the git-notes approach Git AI uses could enhance our receipts by making them git-native (stored in notes rather than JSONL state files).

2. **The "evidence accumulation" pattern should be named.** It's structurally distinct from the four recognized patterns. Future sessions building similar systems should know it exists.

3. **Hook performance matters.** Our PreToolUse adds 110ms (search_replace) to 480ms (terminal command). The 480ms is at the edge of acceptable per Isenberg's <5s guidance but is fine for terminal commands (which themselves take seconds). We should keep monitoring.

4. **The `additionalContext` pattern** could improve our quality-gate hook — instead of just blocking with "verification stale," it could inject specific feedback like "run pytest tests/test_mixed_diff.py" based on which files were modified.

## Related wiki concepts

- [[mandatory-step-enforcement-code-over-prose]] — the code-over-prose principle our hooks implement
- [[quality-gate-hook-system-implementation]] — the existing quality-gate system
- [[auto-commit-authority-isolation]] — the concurrency-gating approach
- [[grok-pretooluse-deny-contract-verified]] — PreToolUse is the verified enforcement point
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
