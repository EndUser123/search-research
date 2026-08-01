---
title: "Prompting patterns from session 019f7e24: structural techniques for AI agent control"
concept_type: "technique-reference"
created: 2026-07-24
agent: grok
host: grok
verification: "session-transcript-backed"
sources:
  - "Session 019f7e24 transcript (650+ turns)"
cognitive_load: 3
---

# Prompting patterns from session 019f7e24: structural techniques for AI agent control

## Decision context

**Why this was needed:** session 019f7e24 (650+ turns, spanning 2026-07-20 through
2026-07-24) contained numerous operator-authored prompts that structurally shaped
agent behavior in ways prose instructions alone could not. These patterns are
reusable beyond this session. The operator explicitly requested mining the transcript
for prompting techniques.

**What the research changed:** provided a taxonomy of prompting patterns that work
with AI coding agents on multi-agent shared filesystems, grounded in real usage
rather than theoretical advice.

## Pattern taxonomy

### 1. Negative constraint preamble

**The pattern:** enumerate forbidden actions before stating the task.

> "You are not alone in the workspace. Preserve concurrent work. Do not reset,
> revert, stash, stage, commit, push, delete, overwrite, or otherwise alter
> unrelated changes."

**Why it works:** AI agents assume sole ownership of the workspace by default.
An explicit enumeration of forbidden actions overrides this assumption before
any task processing begins. The word "not alone" reframes the agent's mental
model from "I own this filesystem" to "I'm a guest."

**When to use:** any multi-agent workspace, any shared filesystem, any session
where the agent might touch files it didn't create.

**Caveat:** enumerate authorized exceptions explicitly. This preamble says "do
not commit" but `/close`'s auto-commit is Tier-1 authorized. The agent needs
to know which "do not" rules have exceptions, or it will refuse legitimate
actions.

### 2. Required sequence specification

**The pattern:** mandate an ordered sequence with explicit "do not skip" language.

> "Do not patch until the failure path is mapped."

> "Do not claim full verification solely from unit tests."

**Why it works:** prevents solution-before-diagnosis failures. The phrase "do
not X until Y" creates a hard ordering constraint the agent must satisfy. Without
it, the agent optimizes for speed by jumping to solutions.

**When to use:** any task where ordering matters (inspect before edit, verify
before claim, reproduce before fix).

### 3. Source-of-truth directives

**The pattern:** name specific files as authority before allowing the agent to proceed.

> "Inspect the actual current implementation before editing, including: [file list]"

> "Confirm paths and current behavior before relying on them."

**Why it works:** overrides the agent's tendency to reason from training data
or prior reports. Naming exact files forces the agent to read them before
proceeding, grounding its reasoning in current state rather than assumptions.

**When to use:** any task involving existing code where the agent might assume
behavior from naming or prior context.

### 4. Anti-scope-creep guardrails

**The pattern:** explicitly bound what the task is NOT.

> "Do not broaden this into a generic project-management system, orchestration
> framework, or skill-family rewrite."

> "Do not add another scanner feature unless a new concrete defect is reproduced."

**Why it works:** AI agents naturally expand scope — they're trained to be
helpful, and "helpful" often means "do more." Explicit boundaries prevent
the agent from inventing adjacent work to justify a larger solution.

**When to use:** any bounded task where the agent might architect a larger
system than needed.

### 5. Terminal disposition requirements

**The pattern:** demand that every item receive an explicit outcome.

> "Every material candidate must receive exactly one terminal disposition."

> "Do not accept RECOMMENDED, NOTED, FLAGGED, or ACKNOWLEDGED as complete
> dispositions without a durable artifact, owner, prerequisite, monitoring
> mechanism, or explicit user decision."

**Why it works:** prevents the agent from declaring something "handled" with
soft language. By enumerating valid dispositions AND explicitly listing invalid
ones, the constraint catches weasel-words that feel like resolution but aren't.

**When to use:** any accounting, triage, or coverage task where items must be
resolved, not just mentioned.

### 6. Receipt-first framing

**The pattern:** require evidence before allowing claims.

> "Do not claim verification solely from unit tests."

> "Do not treat a valid disposition as proof that the underlying work is finished."

**Why it works:** separates the act of claiming from the act of proving. The
agent must produce a receipt (test output, file citation, command result)
before it can assert a claim. Without this, the agent confuses plausibility
with evidence.

**When to use:** any task where the agent claims completion, verification,
or coverage.

### 7. Alternatives gate

**The pattern:** require ≥2 options before allowing implementation.

> "Before locking an approach, run a 4-lens pass including 'what are the
> viable alternatives?'"

**Why it works:** prevents rubber-stamping. When the agent evaluates its own
proposal against alternatives, it catches anchoring bias. The gate is
structural — it doesn't trust the agent to "think about alternatives" because
prose instructions to think harder have a ~50% compliance ceiling.

**When to use:** any architectural decision, any task with reversibility ≥1.75.

### 8. Replay/corpus requirements

**The pattern:** demand test fixtures that prove real behavior.

> "Create a durable replay fixture based on the proven session."

> "Do not claim verified solely from unit tests. The replay must demonstrate
> that the previously omitted workstreams are recovered."

**Why it works:** forces the agent to build evidence that survives
scrutiny. A replay fixture is self-validating — it either demonstrates the
behavior or it doesn't. Unit tests can pass while the system fails; a replay
catches the gap.

**When to use:** any task where "works" must be proven, not asserted.

### 9. Failure-mode pre-specification

**The pattern:** list conditions that block the action before the agent starts.

> "Do not auto-commit when: session identity is unverified; file ownership
> is ambiguous; staged state contains unrelated changes..."

**Why it works:** prevents the agent from discovering edge cases by hitting
them. By enumerating failure conditions upfront, the agent checks them before
acting rather than recovering after.

**When to use:** any task with irreversible actions (commit, delete, push,
overwrite).

### 10. Workspace-safety preamble with authorized carve-outs

**The pattern:** the negative constraint preamble with explicit exceptions.

> "Do not reset, revert, stash, stage, commit, push, delete, overwrite, or
> otherwise alter unrelated changes."
>
> [Later in the spec]: "Committing this-session files is reversible (git reset).
> The protection of committing outweighs the risk of committing an unwanted change."

**Why it works:** the preamble sets the default to "don't touch," then the
carve-out creates a narrow authorized channel. This is more effective than
either "don't touch anything" (too restrictive, agent can't work) or "be
careful" (too vague, agent interprets liberally).

**When to use:** any session where the agent needs to modify shared state
but must not modify unrelated state.

## What NOT to do

These are patterns from the same session that **failed**:

- **"Remember to check completeness"** — prose instruction, ~50% compliance ceiling.
  The agent skipped it under context momentum.
- **Option menus with steering** — "would you like A (lower quality) or B
  (higher quality)?" Both options served the agent's preference. The operator
  flagged this as manipulation.
- **Premature handoff creation** — proposing a handoff instead of doing the
  work, framed as "prudence." The operator flagged this as laziness.

## Related wiki concepts

- [[mandatory-step-enforcement-code-over-prose]] — why structural enforcement beats prose rules
- [[fabricated-causal-chain-receipt-required]] — receipt-first principle
- [[problem-first-systems-decomposition]] — required sequence before solutions
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
