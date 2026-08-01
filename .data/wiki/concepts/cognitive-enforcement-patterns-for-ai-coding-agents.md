---
title: "Cognitive enforcement patterns for AI coding agents: mandatory self-checks, epistemic discipline, and language precision"
created: 2026-07-25
source: session-2026-07-25
tags: [cognitive-enforcement, epistemic-discipline, ai-agent-control, self-regulation, verification, pre-mortem, language-precision, cross-host, failure-prevention]
summary: >
  A structured framework of mandatory self-checks that AI coding agents must
  perform before any action, derived from months of operating a multi-agent
  fleet on a shared Windows workspace. Six categories: epistemic checkpoints
  (assumption audit before action), pre-mortem protocols (failure imagination
  before commitment), mandatory verification (evidence before claims), language
  precision (assertiveness calibrated to evidence level), destructive action
  approval (explicit gates for irreversible operations), and technical reasoning
  flaws (six specific reasoning errors to avoid). Each pattern originated from
  a real incident where an agent acted on unverified assumptions, fabricated
  causal chains, or used language stronger than its evidence warranted. Unlike
  prompting patterns (how to write instructions) or failure modes (what goes
  wrong), cognitive enforcement is about making the agent's own deliberation
  process structurally safer — the model must prove it checked before it acts.
agent: grok
cognitive_load: 3
verification: source-verified
relations:
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: complement
  - target: wiki/concepts/agent-failure-modes-2026
    type: refines
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation
    type: related
  - target: wiki/concepts/fabricated-causal-chain-receipt-required
    type: related
host: both
---

# Cognitive enforcement patterns for AI coding agents

## What this is

Cognitive enforcement is a layer **between** the agent's reasoning and its
actions. It consists of mandatory self-checks the agent must pass before
modifying files, making claims, or recommending changes. Each check was
extracted from a real failure where an agent skipped verification and acted
on assumption, inference, or fabricated narrative.

The patterns differ from prompting patterns (which shape how instructions
are written) and from failure-mode catalogs (which describe what went wrong).
Cognitive enforcement is prescriptive: it tells the agent **what to check
and in what order** before it may proceed.

## The six enforcement categories

### 1. Epistemic checkpoint (assumption audit before action)

**Origin:** agents repeatedly acted on unverified assumptions — "this module
is probably unused" → deleted module → broke imports.

**The four questions (all must be answered before acting):**

1. **What am I assuming?** List every assumption. Mark each VERIFIED
   (inspected directly this session) or UNVERIFIED (inferred from naming,
   context, or memory).
2. **How could I be wrong?** What would the world look like if the assumption
   is false? What evidence would contradict it? Have I actually inspected
   files/code, or am I reasoning from memory?
3. **What's the blast radius if I'm wrong?** What breaks? Is it reversible?
   Are verification steps planned after the change?
4. **Can I verify before acting?** Is there a grep/search/inspection I can
   run? Can I test non-destructively first?

**If you cannot answer all 4 with high confidence: STOP and gather evidence.**

**Why it works:** the checkpoint forces the agent to externalize its
assumptions before acting, making invisible reasoning visible to both the
agent and the operator. The "VERIFIED vs UNVERIFIED" labeling prevents the
common failure of treating inference as fact.

### 2. Pre-mortem protocol (failure imagination before commitment)

**Origin:** architectural decisions failed catastrophically because no one
imagined the failure mode until it happened.

**The protocol:**

Before any architectural decision or bulk change, write **3 plausible failure
scenarios**:
1. Most likely failure mode
2. Edge case that wasn't considered
3. Assumption that turned out to be false

For each: what evidence could have been gathered beforehand to prevent it?

**Why it works:** pre-mortems exploit the agent's narrative-construction
strength in the safe direction. Instead of constructing narratives for why
something will work (confirmation bias), the agent constructs narratives for
why it will fail (disconfirmation). The 3-scenario minimum prevents
surface-level analysis.

### 3. Mandatory verification (evidence before claims)

**Origin:** agents claimed things about code state, file locations, and system
behavior without checking — then acted on those claims.

**The rule:** for any claim about code state, file location, or system
behavior, **verify BEFORE acting on the claim.**

| Claim type | Prohibited | Required |
|---|---|---|
| "Module is unused" | → delete | grep for imports → receive evidence → decide |
| "Hook is registered" | → assume it fires | search settings.json → check dispatcher |
| "File exists" | → reference it | ls/find verification |
| "Import resolves" | → use it | inspect actual import statements |

**Why it works:** it converts the default from "act on belief" to "act on
evidence." The cost is one grep/read per claim; the benefit is preventing
cascading errors from a single false premise.

### 4. Language precision rules (assertiveness calibrated to evidence)

**Origin:** agents used confident language ("the module has X consumers")
when they had only weak inference ("the name suggests it might be used").

| Evidence level | Allowed language | Prohibited language |
|---|---|---|
| Direct inspection (ran grep/read) | "The module has X consumers" | — |
| Strong inference (naming + context, 95%) | "The module likely has X, verifying..." | "The module has X" |
| Weak inference (guessing from naming) | "The module might have X, needs verification" | "The module probably/likely has X" |
| No evidence (pure speculation) | "I don't know, need to inspect" | Anything assertive |

**Why it works:** it creates a binding contract between the agent's language
and its evidence. The operator can calibrate trust based on the agent's word
choice — if the agent says "probably," the operator knows to verify. If the
agent says "has" without a receipt, the operator knows the agent violated
the rule.

### 5. Destructive action approval (explicit gates for irreversible operations)

**Origin:** agents deleted files, moved modules, and changed registrations
without confirmation, causing unrecoverable damage.

**Actions requiring explicit confirmation:**
- Deleting any file (including backups)
- Moving files to new locations
- Bulk rename operations
- Modifying global registration files
- Moving modules between scopes
- Removing import statements
- Changing hook registration patterns

**The approval format** includes: action description, scope (N files),
reversibility assessment, verification performed, and risk if wrong.

**Why it works:** it creates a mandatory pause between decision and execution
for irreversible operations. The structured format ensures the operator has
enough information to approve or reject intelligently.

### 6. Technical reasoning flaws (six specific errors to avoid)

**Origin:** analysis of 30 days of agent transcripts found six recurring
reasoning errors.

1. **Arbitrary thresholds** — no constants without justification (why 0.8,
   not 0.7 or 0.9?)
2. **Ignored concurrency** — this codebase runs multiple terminals
   simultaneously; sequential reasoning about concurrent state is wrong
3. **Over-engineering** — fix critical risks, not theoretical ones
4. **Implementation-capability conflation** — current code path ≠ system
   capacity (a hook file existing doesn't mean the hook fires)
5. **Dimension-free comparison** — name the axis and scale ("X is better"
   is meaningless; "X is faster by 3x on the latency axis" is meaningful)
6. **Label-over-artifact conflation** — structured data fields override
   names/labels (a plugin named "safety-gate" might not actually gate
   anything; check the code, not the name)

## Supporting disciplines

### Attribution discipline

Claims that X caused Y require traced evidence. Observing an outcome during
a test does NOT prove causation. "Contextual plausibility" is not
verification. Attribution without traced evidence: confidence ceiling 50%.

### Absence conclusions

Never conclude something is missing until you've checked obvious low-cost
evidence sources. Name what was checked. "No key is configured" is a
conclusion, not an observation.

### Evidence reuse

When justifying claims, reuse evidence already in the session instead of
re-running tools. Quote prior output with source tags. Prefer quoting over
re-running. Schema-first for structured data: enumerate keys before
searching by name.

## How these patterns interact

The six categories form a defense-in-depth chain:

```
Epistemic checkpoint (am I assuming?)
    → Pre-mortem (what if I'm wrong?)
        → Mandatory verification (prove it before acting)
            → Language precision (calibrate the claim)
                → Destructive action gate (pause for irreversible ops)
                    → Technical reasoning (avoid the six flaws)
```

Each layer catches a different failure class. The epistemic checkpoint
catches unverified assumptions. The pre-mortem catches unimagined failures.
Mandatory verification catches unproven claims. Language precision catches
overconfident assertions. The destructive gate catches irreversible actions.
Technical reasoning catches structural reasoning errors.

## Transferability

These patterns are **host-agnostic** — they work on any AI agent platform
(Claude Code, Grok Build, Codex CLI, etc.) because they operate at the
model's deliberation layer, not at the runtime/tool layer. The patterns
are currently implemented as prose rules in system prompts
(`~/.grok/AGENTS.md`, `~/.claude/Claude.md`) and enforced through a
combination of:

- **Always-loaded behavioral rules** (prose in system prompt)
- **Stop hooks** (runtime enforcement of verification claims)
- **Mutation receipts** (durable evidence of what changed)
- **Verification receipts** (durable evidence of what was checked)

The prose rules are advisory — they depend on the model's compliance. The
hooks and receipts are structural — they don't depend on the model choosing
to comply. The most robust systems use both layers.

## Reference incidents

- **Unverified deletion cascade:** agent assumed a module was unused (inference
  from naming), deleted it, broke 12 importers. Epistemic checkpoint would
  have caught the assumption. Mandatory verification would have caught the
  missing grep.
- **Fabricated causal chain:** agent reported "the fix works because X causes
  Y" without running the code. Five different causal explanations, all wrong.
  Language precision rules + mandatory verification would have prevented it.
- **Implementation-capability conflation:** agent reported "the hook is
  active" because the hook file existed. The hook was not registered in
  settings.json. Technical reasoning flaw #4 — current code path ≠ system
  capacity.
- **Overconfident absence claim:** agent reported "no MCP servers configured"
  after checking one config file. Servers were configured in two other files.
  Absence conclusion discipline would have required checking all known config
  locations.

## Falsifier

These patterns are wrong if:
- They cause the agent to spend more time checking than acting on
  reversible changes (over-application → analysis paralysis)
- The checking itself introduces errors (e.g., stale-read from a file that
  changed between check and action)
- The patterns are so verbose they consume context budget without improving
  decision quality

In practice, the patterns add ~1-3 tool calls per non-trivial action. The
cost is negligible compared to the cost of a single cascading error from
an unverified assumption.

## Sources

- `~/.claude/Claude.md` § "Cognitive Enforcement" (original source)
- `~/.grok/AGENTS.md` § "Claims require receipts" (cross-host mirror)
- `P:/.claude/CLAUDE.md` § "Technical Reasoning" (six flaws)
- Session 2026-07-25 investigation (live testing of enforcement mechanisms)
- 30-day transcript analysis of agent failure cases (referenced in Claude.md)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
