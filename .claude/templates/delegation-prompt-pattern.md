# Delegation Prompt Pattern — composing prompts across capability and contract

Purpose: a single factored template for handing work to another LLM,
regardless of the delegate's capability tier or the kind of work being
delegated. **The prompt supplies what the delegate lacks; the delegate
supplies only the labor.**

The previous version of this document enumerated seven elements tuned
for one specific case (mechanical cleanup done by a simpler model).
That tuning became a liability: the other cases in the same session
(a peer model running setup, this conversation itself) needed different
elements, and the template could not speak to them. Documents that
overlap drift apart — the same failure mode as a generated catalog
maintained by hand. The current factoring — one invariant core, two
orthogonal substitution blocks — covers all observed cases from a
single source of truth. The previous 7-element version is archived at
`P:/.claude/templates/_archive/delegation-prompt-pattern.md.7-element-original`.

## The 2×2

Pick exactly one from each axis; compose at write-time.

|              | **Executor** — produces artifacts          | **Partner** — produces decision material       |
|--------------|--------------------------------------------|------------------------------------------------|
| **Simple** delegate | ✅ mechanical cleanup (audit-driven) | ❌ **don't** — contradicts itself            |
| **Peer** delegate    | ✅ capable model, missing context    | ✅ collaboration on framing/decisions        |

The fourth cell (simple-partner) is excluded on purpose: a thought-
partnership contract is judgment-dense, and judgment is what simple
delegates lack.

**If you must use a simple delegate for partner-shaped work** (cost
constraint, no peer available): split the work into executor-shaped
subtasks (verifier-defined, mechanically checkable) and supply the
judgment yourself in the prompt. The simple delegate becomes a labor
pool; you do the partner work. The escape hatch (core invariant #4)
becomes more important, not less — the simple delegate will invent
if you don't bound the search space, and "investigate vs. recommend"
collapses into "guess" without your framing.

Observed cases that justify these cells, in date order:

- simple-executor — hooks_audit cleanup delegation prompt, 2026-07-09
- peer-executor    — LLM running setup_git.ps1, 2026-07-09
- peer-partner     — the conversation that produced this factoring, 2026-07-09

## Invariant core (all four cells)

These four elements ship in every delegation prompt regardless of cell.
If you find yourself omitting one, you have re-opened a failure mode
the core exists to prevent.

1. **Evidence-cited claims.** Every claim in the delegate's reasoning
   cites its source — file:line, command output, verifier exit code.
   Reasoning without a citation is unanchored. This survives across
   cells because "command ran ≠ result correct" is a property of the
   world, not the model. Executor specializes this as "the verifier
   output"; partner specializes it as "the evidence packet."

2. **Explicit boundaries.** Name what is in scope and what is out.
   The simplest form is a don't-touch list (files, directories, files
   not flagged by the detector). In partner mode the boundary is the
   action line: stop at findings, do not implement unless explicitly
   asked. In peer-executor mode it can be a reversibility gradient
   rather than a flat list.

3. **Written residue.** A report or log saved to a known path. For
   executors it enumerates changes, skipped items, and "needs human"
   findings. For partners it enumerates decisions, recommendations,
   falsifiers, and disagreements. Without residue, auditing the
   delegate means replaying its session — and the requirement itself
   suppresses silent skipping.

4. **Legitimate "I don't know."** An explicit escape hatch when
   evidence is missing or the situation does not match a pre-stated
   pattern. The delegate reports the gap, does not improvise. Simple
   delegates need it to avoid silent invention; peer delegates need
   it to avoid confident guessing.

## Capability axis

Pick one. Substituting incorrectly here is the most common way to
over- or under-prescribe procedure.

### Simple delegate

The binding constraint is **judgment**: simple models do the most
damage when forced to decide in unstructured territory. The prompt
compensates by supplying judgment.

- **Detector-driven scope.** Anchor every task to an existing tool's
  output ("run the audit; fix what it flags"). The detector defines
  the universe of work.
- **Classification buckets with a mechanical rule.** Pre-enumerate
  the categories (fixture / renamed / truly-gone) with a deterministic
  rule for each, plus an escape-hatch bucket ("report, don't decide").
- **One change per verification cycle.** Sequential file operations
  with a check between each. Batch failures in a simple model are
  silent and compounding; a verified intermediate state catches them
  early.

### Peer delegate

The binding constraint is **context**: a peer model can decide as
well as you, but starts cold — no session history, no constraint
rationale, no knowledge of which traps the environment contains.
The prompt compensates by transferring context, not by prescribing
procedure.

- **Context transfer, not procedure prescription.** State what was
  tried, why it failed, which constraints are spec (cannot change)
  vs preference (can change with rationale), and trap documentation
  with detection commands ("the mount truncates writes ~11.6KB —
  verify by checksum", "sandbox is 3.10, prod is 3.13").
- **Decision criteria + decision log.** State the goals and tradeoffs
  ("prefer delete over gate; a kept fallback needs explicit
  justification"), let the delegate decide, require rationale in
  the report. Pre-enumerated buckets cap the delegate's judgment at
  the prompt-writer's; a peer will encounter categories you didn't
  anticipate and handle them better than your buckets would.
- **Reversibility-scaled authorization.** Trivial (config, local
  edit): proceed freely. Irreversible (deletes, production writes):
  propose-then-wait. Replaces the simple delegate's flat don't-touch
  list with a gradient that respects the Reversibility Scale in
  CLAUDE.md.

## Contract axis

Pick one. Substituting incorrectly here changes what the deliverable
is.

### Executor

The delegate produces artifacts. Success is machine-checkable: a
verifier exits 0, a test passes, a file exists with the expected
contents, a detector's count drops.

- **Verifier defines done.** The outcome has a non-self-check that
  establishes done-ness. For simple delegates this is typically a
  detector; for peer delegates it may be a script, a test, or a
  smoke-check. Baseline before, compare after.
- **Act-then-verify, in cycles.** Each task ends with re-running the
  exact check that found the problem ("re-run ast.parse", "CATALOG_DRIFT
  must go to 0"). The delegate cannot claim unverified success because
  success is defined as verifier output, not self-report.
- **Fix the source, not the derived artifact.** For catalogs,
  generated docs, lockfiles, and any other artifact produced by a
  generator: repair the generator until the artifact validates. Hand-
  edits recreate the drift the task exists to remove.

### Partner

The delegate produces decision material. There is no detector for
"was this the right framing" — verification moves from the output
into the reasoning.

- **Evidence-defines-assertability.** Every claim in the analysis
  cites the artifact it came from (file:line, command output, stats
  file). Unknowns are labeled as unknowns rather than filled with
  plausible narrative. A thought partner who hasn't read the evidence
  is a rubber duck.
- **Mandatory position with named criterion and falsifier.** The
  partner commits to a recommendation, names the decision criterion
  (cost, reversibility, reliability-per-complexity, etc.), and states
  what evidence would flip the recommendation. Symmetric pros-and-cons
  lists skip the work; the partner was hired to recommend.
- **Disagreement is a required deliverable.** The partner states
  where the user's framing or question is wrong before answering it.
  Sycophancy — polishing the user's framing instead of testing it —
  is the partner-mode failure mode; the executor failure mode is
  silent skipping. The template should demand the disagreement
  explicitly.
- **Documentation Boundary.** Default to investigate, stop at
  findings, act only on explicit "do it." Same rule as CLAUDE.md;
  restated here because it is the operationalization of the
  partnership contract.

## Composition: the original worked example (simple-executor)

For continuity with the previous version of this document, here is
how the original seven elements map onto the new factoring:

| Original # | Original element               | Maps to                              |
|------------|--------------------------------|--------------------------------------|
| 1          | Detector-driven scope          | Capability: simple                   |
| 2          | Verification closes every task | Invariant core #1 (evidence-cited)   |
| 3          | Classification buckets         | Capability: simple                   |
| 4          | Explicit don't-touch list      | Invariant core #2 (boundaries)       |
| 5          | Fix the generator              | Contract: executor                   |
| 6          | One change per cycle           | Capability: simple                   |
| 7          | Mandatory written residue      | Invariant core #3                    |

The seventh invariant — "legitimate 'I don't know'" — was implicit in
the classification buckets; the factoring makes it explicit as a core
invariant because it applies across cells.

## Skeletons

### Executor skeleton (simple or peer)

```
You are working in <root>. Rules from CLAUDE.md apply: state planned
changes before making them; one file per Read→Edit→Verify cycle; never
claim fixed without re-running the check that detected it.

GOAL: <one sentence — what "done" means>
FILES: <paths you expect to touch>
VERIFY: <the exact command that proves it works, with expected exit 0>
BOUNDARIES: <don't-touch list, or "trivial edits only, propose otherwise">
SIMPLEST FIRST: <one-line smallest version> — <why insufficient>
AMBIGUITIES: <real ones only; "none" if so>

SETUP: run <verifier>, save baseline to <path>.

TASK n — <category from verifier output>
  - For each finding: <mechanical rule, or classification buckets a/b/c
    where one bucket is always "report, don't decide">
  - Verify each fix with: <exact command>

FINISH:
  - Re-run <verifier>, save to <path>, compare to baseline.
  - Write <report path>: baseline vs after counts, every change,
    every skipped/needs-human item with one-line justification.
  - <commit/handoff step>
```

### Peer-executor addition

Prepend a **Context** block before SETUP:

```
CONTEXT:
  - Prior attempts: <what was tried, why it failed>
  - Spec vs preference: <which constraints are spec, which can change>
  - Environmental traps: <known gotchas with detection commands>
  - Decision criteria: <axes to optimize, in priority order>
```

### Partner skeleton

The partner skeleton replaces the executor skeleton entirely; the
shapes are different enough that one cannot serve both.

```
ROLE: <what you are being asked to think about, in one sentence>
EVIDENCE PACKET: <files to read, commands to run, in order>
POSITION: <your committed recommendation, with named decision criterion>
FALSIFIER: <what evidence would flip this recommendation>
DISAGREEMENT: <where the original framing is wrong, or "framing holds">
ACTION LINE: <investigate / propose / act> — default: investigate,
  stop at findings, do not implement unless asked.
RESIDUE: <where to write the decision log; who reads it>
```

## Anti-patterns

| Anti-pattern                                  | Why it fails                                         |
|-----------------------------------------------|------------------------------------------------------|
| Three standalone templates, one per use case  | Drift — same problem as the 275-hook catalog         |
| Pre-enumerated buckets for a peer delegate    | Caps the delegate's judgment at the prompt-writer's  |
| Detector-defines-done for a partner           | No audit script for "is this the right framing?"     |
| Symmetric pros-and-cons in a partner response | Skips the work; the partner was hired to recommend   |
| Skipping the escape hatch to look rigorous    | Forces the delegate to invent instead of admit gaps  |
| Adding a fourth axis before a failure requires it | Speculative generality — evidence-first growth only |
| Quoting this template into the prompt itself  | The template is the meta-doc; copy the skeleton, not the analysis |

## Growth rule

A new axis earns a change to this template (e.g., multi-delegate
coordination becoming a real dimension). A new instance does not —
it is just a new pick of existing switches. **Do not add anything
until an actual delegation fails under the current factoring.** You
have three observed cases and zero observed failures of the composed
template; build for that, not for hypothetical delegates. This mirrors
the Replacement Default in CLAUDE.md: deletion over addition, even in
documents.

## Origin

2026-07-09. Factored from a session that observed three use cases
(simple-executor, peer-executor, peer-partner) sharing an invariant
core and differing on two orthogonal axes. Companion:
`P:/.claude/templates/llm_behavior_contract.md` (behavior contract
for the delegate to operate under).
