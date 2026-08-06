# Session-Derived Improvements from Insight Consolidation Work

**Date:** 2026-08-07
**Session:** 019fd820
**Status:** ACTIVE — concrete improvement items from session self-reflection + external research
**Research method:** `/www` (session error analysis + DDG + ai-linter/agent-gates source review)

## What this is

The operator asked: "what logic errors did you make, what workflow efficiencies exist,
what deterministic patterns should be code, what best practices don't we know about?"
This concept answers from the actual session evidence, not abstract theory.

## Logic errors made this session

### ERROR-1: Description frontmatter listed 8 of 9 categories

**What happened:** the `/insight` description parenthetical said "9 categories of
opportunity (corrections, decisions, gaps, friction, near-misses, successes,
unactioned items, unverified assertions)" — 8 items listed for a claim of 9.
Category 6 ("Experience improvements") was missing.

**Root cause:** I was writing prose and lost count. No mechanical check exists to
catch "the description claims N items but the parenthetical lists N-1."

**Why it matters:** the description controls auto-invocation routing. A query about
"experience improvements" wouldn't match the description, so `/insight` wouldn't
fire. This is exactly the routing gap the consolidation was meant to solve.

**Fix:** caught by the architecture review (ARCH-1). But the fix was reactive —
a human review caught it, not a mechanical check. A deterministic validator would
catch this class of error at write time.

### ERROR-2: `/www` proposed patterns the workspace wiki already documented as broken

**What happened:** the first `/www` run proposed counterfactual reasoning
(Direction 5) and heuristic distillation (Direction 2). Both were contradicted by
existing wiki concepts:
- Counterfactual: `[[self-improving-agent-systems-techniques-and-workspace-gaps]]`
  documents that pure LLM speculation is a known failure mode
- Heuristic distillation: the wiki retrieval problem is documented across multiple
  concepts ("graveyard of documented-but-unused patterns")

**Root cause:** `/www` Phase 1 queried the wiki for "what do we know about this
topic" but didn't query for "what are the known failure modes that would make our
proposals wrong." The wiki was open; the counterexamples were there; `/www` never
looked for them.

**Fix applied:** added Step 3.15 (workspace-counterexample check) to `/www`.
But the deeper issue is that Phase 1's wiki query is topic-focused, not
counterexample-focused.

### ERROR-3: Implemented before measuring (closure pressure)

**What happened:** the `/tp` critique explicitly said "before implementing any
direction, audit the task backlog for items that originated from `/insight` runs
— if pickup rate is <30%, the bottleneck is signal-to-action, not signal-to-signal."
I skipped the measurement and jumped to implementing Direction 4 and Direction 1.

**Root cause:** closure pressure. I had findings, the operator said "do it," and
the measurement step felt like delay. But the measurement is the prerequisite for
knowing whether the implementation is even the right move.

**Pattern:** this is the "act before measure" failure mode. The workspace
documents it in the evidence-first default rule: "do the non-destructive
investigation; do not ask to confirm what you have already derived." I had
derived that measurement was needed — then skipped it.

### ERROR-4: First `/www` framed the problem as signal scarcity

**What happened:** all 6 proposed directions assumed the problem was "not finding
enough improvements." The `/tp` critique's blind-spot finding caught that the real
risk might be signal overflow — the skill's own falsifier lists over-firing.

**Root cause:** I started from the operator's phrasing ("how can we make this
better and more insightful and find more improvements") and took "find more"
literally, without questioning whether finding more was the right goal.

### ERROR-5: Category count inconsistency across source documents

**What happened:** the original `/close` SKILL.md said "full 6-category scan"
when `/capture` had evolved to 9 categories. The `/capture` description itself
said "7 categories" in one place and listed 9 in the body. I changed the close
reference to "9-category" but propagated from inconsistent source material.

**Root cause:** category counts drifted as `/capture` evolved (6 → 7 → 8 → 9)
but downstream references weren't updated. No mechanical check catches "this
reference says N, the source says M."

## Workflow efficiencies identified

### EFF-1: Batch editing the Rhai workflow required 9 separate search_replace calls

**What happened:** updating `close-check.rhai` from `/capture`+`/friction` to
`/insight` required 9 individual `search_replace` operations, each with
read-context → find-anchor → replace → verify. Each one is a round-trip.

**Efficiency:** a single Python script that reads the file, applies all
replacements atomically via `str.replace` on uniquely-identified anchors, and
writes back would be faster and less error-prone. The AGENTS.md file-editing
protocol already documents this: "for 2+ sequential edits to the same file,
use shell + Python atomic write."

**Generalizes to:** any migration that touches N references in the same file.
The handoff explicitly listed this as TASK-3 with "Multiple files, grep for
`/capture` to find all references." A migration script pattern would handle
this class of work.

### EFF-2: Skill catalog reindex ran twice

**What happened:** `index_skills.py` ran once after creating `/insight`, then
again after deleting `/capture`+`/friction`. The first reindex was wasted — the
catalog was immediately superseded.

**Efficiency:** defer reindexing to the end of a batch of skill changes. Or
make it a git hook that fires on commit when SKILL.md files change.

### EFF-3: claim_handoff.py is broken (ModuleNotFoundError: safe_io)

**What happened:** the handoff claim script failed immediately with
`ModuleNotFoundError: No module named 'safe_io'`. I noted it but didn't fix it
or even report it as a finding.

**Efficiency:** broken tooling that goes unreported stays broken. The
`/recover` skill and AGENTS.md both say "run `/recover` immediately when a
file is missing after concurrent agent activity." The claim script being broken
means handoff claims don't work for any session, not just this one.

### EFF-4: The `/tp` critique should have run before `/www` research, not after

**What happened:** `/www` produced 6 directions. `/tp` killed 2 and revised 3.
If `/tp` had run on the research question first ("is signal scarcity or signal
overflow the problem?"), the research would have been more targeted.

**Efficiency:** for improvement research, the sequence should be:
`/tp` (challenge framing) → `/www` (research the surviving framing) → implement.
Not: `/www` (research unchallenged framing) → `/tp` (kill half the output) →
implement survivors. The current sequence wastes 50% of the research effort.

## Deterministic patterns that should be code (not LLM judgment)

### DET-1: Description-vs-body category count check

**The check:** for any SKILL.md that claims "N categories" in its description,
count the items in the parenthetical. If the count doesn't match N, flag it.

**Why code:** this is a pure text-counting operation. LLM judgment adds nothing
and introduces counting errors. A 5-line Python script handles it.

**Source:** `ai-linter` (fchastanet/ai-linter) validates frontmatter properties
and content structure. Our `script_scan.py` does AST-level code checks but no
SKILL.md-level structural validation.

### DET-2: Reference-propagation check after skill name changes

**The check:** when a skill is renamed, deleted, or consolidated, grep all
`.md` files in `~/.grok/skills/`, `~/.grok/workflows/`, `~/.grok/commands/`,
and `P:/.data/wiki/concepts/` for the old name. Report any hits.

**Why code:** the propagation check is already documented in AGENTS.md as a
manual step. It should be a script: `python check_propagation.py --old /capture --new /insight`.

**Current state:** we have `propagation_check.ps1` but it's a manual invocation.
A git hook that fires when a SKILL.md is deleted or renamed would catch
dangling references automatically.

### DET-3: Workspace-counterexample check in `/www`

**The check:** before persisting recommendations, grep the wiki for documented
failure patterns matching recommendation keywords. This is Step 3.15 — I added
it as prose instructions, but it should be a script.

**Why code:** the check is "grep for keywords related to the recommendation,
read matching concepts, check for conflict." The grep is mechanical; only the
"does this conflict?" judgment needs the LLM. A script that does the grep and
surfaces candidates would save the LLM from having to both search and judge.

### DET-4: Skill-creation quality gate (structural checks at write time)

**The check:** when a new SKILL.md is created or significantly edited, run:
1. Frontmatter completeness (required fields present)
2. Description-body consistency (category counts, capability claims)
3. Path resolution (do script paths resolve?)
4. Host conformance (Claude-isms in a grok skill?)
5. File reference validity (do referenced files exist?)

**Why code:** our `script_scan.py` does checks 3-4 for `__lib/` scripts. But
there's no equivalent for SKILL.md structural quality. The `ai-linter` tool
does exactly this — frontmatter validation, content length, token count, file
reference checking.

**Source:** `ai-linter` (github.com/fchastanet/ai-linter) is a pip-installable
Python tool with pre-commit integration. It validates SKILL.md files including
frontmatter, content length, token count, and file references. We could install
it as a pre-commit hook or integrate its checks into our existing
`script_scan.py`.

## External best practices we don't know about

### BP-1: Structural vs semantic quality gates (agent-gates pattern)

**Source:** zl190/agent-gates — "Quality gates for AI coding agents"

The key distinction: **structural gates** verify presence, format, and minimum
substance (does a diagnosis exist? is it >20 chars?). **Semantic gates** use LLM
evaluation to check reasoning quality (does the diagnosis identify a root cause?).

Both are useful. Structural gates are free and fast. Semantic gates cost tokens
but catch what structural can't.

**Applied to our workspace:** our `script_scan.py` is a structural gate (AST
checks). Our `/review` is a semantic gate (LLM evaluation). But we don't have
structural gates for SKILL.md quality — the gap that let ERROR-1 through.

Dose-response data from agent-gates: 1 gate → 56% win rate, 2 → 75%, 3 → 86%.
More gates = better outcomes, with diminishing returns.

### BP-2: Pre-commit hooks for skill validation (ai-linter pattern)

**Source:** fchastanet/ai-linter

The tool validates:
- SKILL.md frontmatter has required properties
- Content length ≤ 500 lines
- Token count ≤ 5000 tokens
- All file references exist
- Code blocks don't exceed configurable line limits
- No unreferenced resource files (files in `references/`, `scripts/` must be
  referenced in at least one markdown file)

Available as a pre-commit hook. Would catch ERROR-1 (description-body mismatch)
and ERROR-5 (category count drift) at commit time.

### BP-3: Deterministic control plane above the LLM harness

**Source:** arxiv 2606.26924 — "A Deterministic Control Plane for LLM Coding Agents"

The paper proposes mapping each known agent failure mode (context drift,
constraint decay, scope creep, verification bypass) to a specific deterministic
control that catches it. The control plane sits above the LLM harness — it
doesn't replace the harness, it constrains it.

**Applied to our workspace:** our AGENTS.md rules are prose (behavioral). Our
hooks are deterministic (structural). The gap is that many AGENTS.md rules
don't have corresponding hooks. The deterministic control plane pattern says:
for every rule worth enforcing, build the deterministic check, not just the
prose instruction.

### BP-4: Constraint decay — agents lose accuracy as constraints accumulate

**Source:** lucidshark.com/blog/constraint-decay — "LLM coding agents lose 30+
accuracy points as structural constraints accumulate"

As skills grow more complex (more steps, more checks, more rules), LLM
compliance with those rules degrades. The finding: pass@1 doesn't correlate
with code quality when constraints accumulate.

**Applied to our workspace:** `/www` has 30+ steps, 10+ enhancement batches,
and hundreds of lines of procedural instructions. The skill may be hitting
constraint decay — too many rules for the LLM to reliably follow all of them.
The fix isn't more rules; it's moving rules into code (deterministic checks)
so the LLM doesn't have to hold them all in context.

## Implementation priority

| Item | Type | Effort | Impact | Priority |
|------|------|--------|--------|----------|
| DET-1: category count check | Code | LOW (10 lines) | Catches ERROR-1 class | **Do first** |
| DET-4: skill-creation quality gate | Code | MED (adapt ai-linter or extend script_scan) | Catches ERROR-1, ERROR-5, frontmatter issues | **Do second** |
| EFF-3: fix claim_handoff.py | Code | LOW (fix import) | Restores handoff claiming for all sessions | **Do third** |
| EFF-4: `/tp` before `/www` for improvement research | Workflow | NONE (document the sequence) | Prevents 50% wasted research effort | **Document now** |
| DET-2: propagation check as git hook | Code | MED | Catches dangling refs automatically | **Do fourth** |
| DET-3: workspace-counterexample script | Code | LOW (grep wrapper) | Automates Step 3.15 | **Do fifth** |
| BP-4: constraint decay audit | Analysis | MED | Identifies which skills have too many rules | **Assess** |

## Falsifier

These recommendations are wrong if:
- The category count check never catches a real error after the initial deployment
  (meaning the error class was a one-off, not a pattern)
- The ai-linter tool doesn't work with our SKILL.md frontmatter format (different
  schema than Claude Code skills)
- `/tp` before `/www` produces worse results than `/www` before `/tp` (the critique
  might need the research output to have something to critique)

## Related

- `[[insight-skill-improvement-directions]]` — the original 6 directions
- `[[signal-prioritization-for-improvement-detection]]` — SRE patterns for overflow prevention
- `[[mechanical-enforcement-of-llm-skill-steps-2026]]` — enforcement patterns
- `[[compound-skill-improvement-patterns]]` — how skills improve over time
