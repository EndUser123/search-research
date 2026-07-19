# Plan: `/plan` (plan mode) suggestion rule

**Status:** PLAN — not implementation. No `AGENTS.md` file is modified by this document.
**Author context:** Produced as a focused subagent task. The user requested this work be done in plan mode on the `glm-5-2` model; this file is the plan artifact that a parent session reviews before any rule lands.
**Target host:** Grok Build (global rule primary; workspace mirror secondary).
**Date:** 2026-07-18

---

## 1. Problem statement

In a recent conversation, the parent Grok agent was asked for cleanup
recommendations on the `yt-is` package. The situation had three load-bearing
properties:

1. **Multi-stream coordination** — two parallel worktrees with overlapping C1
   contracts and an unresolved merge decision.
2. **Durable artifact ask** — "cleanup recommendations" is output a future
   session would rely on (it belongs in a plan/handoff path, not chat).
3. **Open-ended framing** — the user phrased it as "what do you suggest," i.e.
   no named target, no acceptance criteria, execution not authorized.

The agent responded with three inline options:

- verify git state,
- give the plan as-is (inline),
- load `/go`.

**Plan mode was not buried among the options — it was missing entirely.** This
is the structural absence problem: every existing rule either (a) governs
*entering* plan mode after the agent has decided to, or (b) asks a yes/no
"plan first or proceed directly?" question that does not force plan mode to
appear as a named option in a recommendation list. No rule inverts the default
bias toward surfacing plan mode, and no rule has an artifact criterion.

The fix is a rule with **objective, falsifiable triggers** that force plan mode
to appear as an explicit named option whenever the recommendation would
otherwise omit it.

### Why the existing rules did not fire (root cause)

| Existing rule | Location | Why it missed |
|---------------|----------|---------------|
| "Plan mode discipline" | `P:\AGENTS.md` L3-20 | Governs *entering* plan mode (approval-language check, Shift+Tab fallback). Says "Plan first or proceed directly?" — a yes/no on entering, not a requirement to *list* plan mode as an option. |
| "Proactive skill suggestions" row: "multiple viable approaches" | `P:\AGENTS.md` L86 | Same yes/no framing ("Plan first, or proceed directly?"). No artifact trigger. No multi-stream trigger. No bias inversion. |
| "Capability gap gate" | `~/.grok/AGENTS.md` L34-48 | Fires on open-ended discovery asks but routes to "load a skill or do a thin first-pass" — it never names plan mode as the structural answer. |
| "Recommendations" (hard-to-reverse → ≥2 options) | `~/.grok/AGENTS.md` L128-134 | Requires ≥2 options but does not require plan mode to be *one of them*. The agent satisfied this rule with three non-plan options. |
| "Grok /go default" | `~/.grok/AGENTS.md` L46-59 | Pushes toward `/go`, which **assumes execution is authorized**. For a "what do you suggest" ask, execution was not authorized — so `/go` was the wrong default and plan mode was the right one. |

The gap is therefore at the **recommendation-construction layer**: nothing
forces plan mode into the option set when the ask is a durable artifact +
open-ended + multi-stream.

---

## 2. Current state of relevant rules (quoted)

### 2a. `~/.grok/AGENTS.md` — global Grok rules

The global file has **no** "Proactive skill suggestions" section and **no**
plan-mode rule. Its closest analogs:

- "Capability gap gate" (L34-48): handles open-ended discovery/improvement
  asks; routes to skill-loading or thin first-pass; never names plan mode.
- "Recommendations" (L128-134): hard-to-reverse → name ≥2 viable options +
  selection criterion; does not require plan mode as one of the options.
- "Grok /go default" (L46-59): prefer `/go` for non-trivial work.

> **Factual correction to the task framing:** the task states the
> "Proactive skill suggestions" section lives in `~/.grok/AGENTS.md`. It does
> not. It lives in `P:\AGENTS.md` (L72-94). The global file is the wrong place
> to "augment/replace" that table; it is the right place to add a new
> self-contained rule that the table can reference.

### 2b. `P:\AGENTS.md` — workspace rules

**"Plan mode discipline" (L3-20), quoted verbatim:**

> Before calling `enter_plan_mode`, check the recent conversation for approval
> language ("do it", "go", "approved", "proceed", "ship it", "yes", "ok"). If
> found → **do not enter plan mode**. Proceed directly to implementation.
>
> If the task is genuinely ambiguous AND no approval was given → ask in chat:
> "This has multiple viable approaches. Plan first or proceed directly?" Respect
> the answer.
>
> […]
>
> Never enter plan mode as a way to delay implementation of approved work.

**"Proactive skill suggestions" table (L72-94), the row to augment (L86), quoted verbatim:**

> | Decision has multiple viable approaches with very different trade-offs | "This has genuine ambiguity. Plan first, or proceed directly?" |

**"Durable artifacts" (L48-62)** — relevant because it is the contract a plan
mode output satisfies and an inline chat output violates:

> When producing a material artifact (charter, review, root-cause program,
> analysis that a future session needs), write it to a durable path immediately:
> […]
> Do NOT leave material output only in chat or `P:/tmp/`.

### 2c. Terminology finding (must be resolved — see Open Questions)

A `/plan` skill **does not exist** in this environment. Verified by enumeration:

- `~/.grok/skills/`: `agy, check-work, code-review, create-skill, debrief, go,
  grok-discovery, grok-go, grok-parallel, grok-route, grok-safe-git, grok-sdlc,
  grok-verify, help, imagine, tp, wiki`
- `P:/.grok/skills/`: `aar, check, refactor, review`
- No `plan` or `planning` directory in either.

Plan mode is the **built-in `enter_plan_mode` / `exit_plan_mode` mechanism**
(confirmed by P:\AGENTS.md "Press Shift+Tab once to cycle modes"). The wiki
references a legacy `/planning` concept (SDLC stack note, 2026-05-10) that is
not installed. **This plan treats `/plan` as the user-facing name for plan
mode** (the `enter_plan_mode` capability). That assumption is flagged in Open
Questions; if a literal `/plan` slash skill is intended, it must be created
before this rule can reference it as a command.

---

## 3. Proposed rule text (literal markdown to add to `~/.grok/AGENTS.md`)

Insert as a new top-level section, immediately **after** the existing
`## Recommendations` section and **before** `## Pre-ship checklist`. Placement
rationale: the rule fires at recommendation-construction time, so it belongs
adjacent to the Recommendations rule that it extends.

```markdown
## `/plan` (plan mode) suggestion rule

**Default bias: when in doubt, surface plan mode as an explicit option.**
Plan mode is structurally better than inline chat whenever the output must
outlive the conversation. The failure mode this rule exists to prevent is
*structural absence* — plan mode was not buried among the options; it was
missing entirely. (Reference incident: a multi-stream `yt-is` cleanup ask that
listed three options and omitted plan mode.)

### Objective triggers (evaluate each; each is falsifiable)

1. **Multi-stream coordination.** ≥2 parallel worktrees, branches, live
   terminals, or agents touch the same files or contracts.
   *Confirm:* count streams with overlapping diff scope. *Refute:* zero overlap.
2. **Durable artifact ask.** The requested output is a charter, design doc,
   plan, review, migration plan, root-cause program, or any artifact destined
   for a `docs/` or handoff path that future sessions will read.
   *Confirm:* the output would be written to `docs/`, `.artifacts/`, or a
   handoff file. *Refute:* output is throwaway / chat-only.
3. **Open-ended framing, no acceptance criteria.** User phrasing such as
   "what do you suggest", "what should we do", "recommend an approach",
   "how should we handle" AND no stated success criterion, target file, or
   named skill.
   *Confirm:* phrase present AND criteria absent. *Refute:* target/criteria given.
4. **Structurally divergent approaches.** ≥2 options that differ on a real
   axis (reversibility, scope, invariant impact, cost) — not the same path at
   different intensities ("do X carefully" vs "do X aggressively" is one option).
   *Confirm:* name the axis each option changes. *Refute:* cannot name a differing axis.
5. **Hard-to-reverse decision.** Acting on the recommendation costs more to
   undo than to do (reversibility ≥1.5: refactor-with-tests, breaking API,
   deleted data).
   *Confirm:* reversibility score ≥1.5. *Refute:* trivial / fully reversible.
6. **Unresolved merge / contract decision.** A merge, contract change, or
   architectural choice is pending and blocks downstream work.
   *Confirm:* a blocking decision the user must make first exists. *Refute:* nothing blocking.

### Fire rule

- **≥2 of triggers 1–6 → plan mode MUST appear as a named item in the
  recommendation list**, alongside the inline and `/go` alternatives, with the
  selection criterion stated. Example wording:
  *"Option A: enter plan mode and produce a durable plan at `P:/docs/<name>.md`."*
  This is a requirement to **include**, not a yes/no question to ask.
- **Trigger 2 (durable artifact) alone is sufficient.** Inline chat output for
  a durable artifact violates the "Durable artifacts" rule, so plan mode is the
  structurally correct surface regardless of how clear the path seems.
- **Exactly one of the other triggers + a judgment call → default to including
  plan mode.** The bias is deliberately inverted: the cost of a spurious extra
  option is one line; the cost of omission is a missing plan a future session
  needed (the original failure).

### Do NOT surface plan mode when

- Approval language already present ("do it", "go", "approved", "ship it") →
  defer to the workspace "Plan mode discipline" rule; proceed.
- Task is trivial / fully reversible (single file, reversibility ≤1.25, no artifact).
- User explicitly asked for a quick or depth-limited answer.
- Plan mode is already active.
- `/go` is already running AND the ask is execution, not artifact production.

### Plan mode vs `/go` (resolve the default)

- `/go` = **execution authorized** + non-trivial work; it auto-routes
  plan/think internally.
- Plan mode = **execution NOT yet authorized**; the user wants a reviewable
  artifact or a decision before any implementation.
- "What do you suggest" / "recommend an approach" framing ⇒ execution is not
  authorized ⇒ **plan mode is the better default than `/go`**. Offering `/go`
  as the only "do work" option for such an ask is the anti-pattern this rule
  corrects.
```

---

## 4. Location strategy (ordered file updates)

The rule is **canonical in the global file**; the workspace file gets surgical
cross-references; the wiki gets a worked example. Order matters: land the
canonical text first so the mirrors have something to point at.

### Step 1 — `C:\Users\brsth\.grok\AGENTS.md` (canonical, do first)

- Insert the full rule block from §3 as a new `## /plan (plan mode) suggestion rule`
  section, positioned **after `## Recommendations`** (ends ~L134) and **before
  `## Pre-ship checklist`** (~L136).
- No other edit to this file. The global file intentionally does **not** get a
  "Proactive skill suggestions" table — that table is workspace-specific and
  stays in `P:\AGENTS.md`.

### Step 2 — `P:\AGENTS.md` (two surgical mirrors)

**2a. Update the "Proactive skill suggestions" table row (L86).**

Replace:

```markdown
| Decision has multiple viable approaches with very different trade-offs | "This has genuine ambiguity. Plan first, or proceed directly?" |
```

with:

```markdown
| Multiple viable approaches, OR a durable artifact requested, OR multi-stream coordination needed (see global "`/plan` suggestion rule") | Include plan mode as a **named option** in the recommendation with the selection criterion — do not omit it. Do not reduce to a yes/no "plan first?" question. |
```

**2b. Add a one-line pointer at the top of "Plan mode discipline" (after L1
heading, before the approval-language paragraph).** Insert:

```markdown
> For when to **suggest** plan mode as an option in a recommendation (vs.
> *entering* it), see the global `/plan` suggestion rule in
> `~/.grok/AGENTS.md`. This section governs entry; that rule governs surfacing.
```

This makes the enter-vs-suggest split explicit and removes the apparent overlap.

### Step 3 — `P:/.data/wiki/concepts/plan-suggestion-rule.md` (worked example)

Create a short wiki entry (≤60 lines) containing:

- One-paragraph statement of the rule and the incident it fixes.
- The trigger table (copied from §3).
- A **worked example** reconstructing the `yt-is` trigger conversation:
  - Situation: two worktrees, overlapping C1 contracts, unresolved merge,
    "what do you suggest" framing.
  - Trigger evaluation: T1 ✓ (two worktrees), T2 ✓ (cleanup recommendations =
    durable artifact), T3 ✓ (open-ended, no criteria), T6 ✓ (unresolved merge).
    4/6 → mandatory.
  - Correct recommendation shape: "Option A: enter plan mode → durable plan at
    `P:/docs/yt-is-cleanup-plan.md`; Option B: inline thin first-pass; Option C:
    `/go` once execution is authorized. Selection criterion: artifact durability
    + unresolved merge ⇒ A."
  - Anti-example: the original three-option response that omitted plan mode.

### Why not also edit `P:\Claude.md` or `P:\.claude\CLAUDE.md`

- `P:\Claude.md` is `@AGENTS.md` — it inherits automatically; no edit needed.
- `P:\.claude\CLAUDE.md` is the Claude Code constitution; this rule is
  Grok-specific (plan mode + `/go`). Mirroring it there is out of scope unless
  the user wants Claude Code to inherit the same behavior (Open Question 2).

---

## 5. Verification approach

A rule that cannot be observed firing is documentation theater. Three layers:

### 5a. Static (greppable anchors)

After landing, these strings must be findable:

```
rg -n "plan mode.*suggestion rule|surface plan mode as an explicit option" "$USERPROFILE/.grok/AGENTS.md"
rg -n "Include plan mode as a \*\*named option\*\*" P:/AGENTS.md
rg -n "see the global .*/plan. suggestion rule" P:/AGENTS.md
test -f P:/.data/wiki/concepts/plan-suggestion-rule.md
```

The trigger phrases ("what do you suggest", "recommend an approach",
"durable artifact", "multi-stream coordination") are deliberately literal so a
future reviewer can grep the rule and the conversation transcript for the same
strings.

### 5b. Behavioral replay (the real test)

Re-run the trigger conversation pattern in a fresh Grok session and assert
plan mode appears as a named option. Test prompt template:

> "I have two worktrees on `yt-is` with overlapping C1 contracts and an
> unresolved merge. Before I do anything, what do you suggest for cleanup?"

**Pass criterion:** the response contains a named plan-mode option (phrase
matching `enter plan mode` / `plan mode` / `produce a durable plan at <path>`)
as one of ≥2 options, with a selection criterion. **Fail criterion:** plan
mode absent, or present only as a yes/no "plan first?" question.

Run the same prompt with approval language added ("…what do you suggest? go
ahead and do it") → **pass criterion flips**: plan mode should NOT be surfaced
(defer to "Plan mode discipline"). This confirms the guard works.

### 5c. Behavioral checklist (per-recommendation self-check)

Before emitting any recommendation with ≥2 options, the agent silently runs:

1. Did I evaluate triggers 1–6? (If none came to mind, re-scan for T2/T3.)
2. If ≥2 fired (or T2 alone), is plan mode a **named item** in the list?
3. If plan mode is absent, can I name the guard that excludes it? (If not, add it.)

This checklist is the falsifier for "the rule is actually being applied, not
just present in the file."

---

## 6. Risks and edge cases

| Risk | Severity | Mitigation (already in rule) |
|------|----------|------------------------------|
| **Over-suggestion** — plan mode surfaces on every mildly complex task, nagging the user. | Medium | Guards: approval-language, trivial/reversibility ≤1.25, quick-answer, already-active, /go-running. Bias inversion is toward *including an option*, not toward *entering* mode — low cost. |
| **Plan mode overhead** — entering plan mode for a 2-minute decision adds a mode cycle + artifact write. | Medium | Reversibility threshold (T5 ≥1.5) and the "trivial / fully reversible" guard. T2-alone path still fires, but plan mode for a genuine durable artifact is not overhead — it is the correct path. |
| **Conflict with "Plan mode discipline"** (`P:\AGENTS.md` L3-20). | Low | Scoping split: that rule governs *entering* (approval check, Shift+Tab fallback); this rule governs *surfacing as an option*. Step 2b makes the split explicit with a pointer. No contradiction. |
| **Thrash vs `/go` default.** Two rules push different defaults (`/go` for non-trivial work; plan mode for unauthorized-execution asks). | Medium | The "Plan mode vs /go" subsection gives a crisp discriminator: execution authorized ⇒ `/go`; not authorized ⇒ plan mode. The `yt-is` incident is the canonical case where `/go` was wrongly defaulted. |
| **Terminology drift** — `/plan` (task wording) vs plan mode (`enter_plan_mode`) vs legacy `/planning` skill (wiki). | High | Flagged in §2c and Open Questions. Rule text uses "plan mode (`/plan`)" to bridge the user's mental model and the real mechanism. If a `/plan` slash skill is later created, the rule text still reads correctly. |
| **Rule becomes a checklist ritual** — agent parrots "Option A: plan mode" without genuine evaluation. | Medium | Triggers are falsifiable (each has a confirm/refute observation). The §5c checklist requires naming the guard if plan mode is omitted, which forces actual evaluation. |
| **Mirror rot** — global rule and `P:\AGENTS.md` table drift apart over time. | Low | The table row explicitly says "see global rule," making the global file the single source of truth. Wiki entry is dated and incident-anchored. |

### Pre-mortem (three plausible failure scenarios)

1. **Most likely:** the rule fires too often on single-trigger judgment calls,
   and the user starts ignoring plan-mode suggestions (alert fatigue). *Evidence
   that would have prevented it:* the ≥2 threshold plus the "T2-alone is
   sufficient" carve-out concentrate fires on genuine artifact asks.
2. **Edge case:** a task that is both durable-artifact AND already-approved
   ("design the migration, then do it") — the approval guard suppresses plan
   mode even though T2 fires. *Resolution:* approval language means the user has
   authorized a path; if they want the artifact via plan mode they can request
   it. Documented as acceptable.
3. **False anchor:** agent treats "/go" and "plan mode" as the same option in
   disguise (both "plan-then-do"), violating the Recommendations rule against
   options sharing a hidden anchor. *Resolution:* the "Plan mode vs /go"
   discriminator names the real axis (execution authorized vs not), so they are
   not disguised duplicates.

---

## 7. Acceptance criteria ("done")

The rule is landed when **all** of the following hold:

1. ✅ The §3 rule text exists verbatim in `~/.grok/AGENTS.md` as a `## /plan
   (plan mode) suggestion rule` section, positioned between `##
   Recommendations` and `## Pre-ship checklist`.
2. ✅ The `P:\AGENTS.md` "Proactive skill suggestions" table row (L86) is
   replaced with the §4-2a wording, and the "Plan mode discipline" section has
   the §4-2b pointer line.
3. ✅ `P:/.data/wiki/concepts/plan-suggestion-rule.md` exists with the trigger
   table and the `yt-is` worked example + anti-example.
4. ✅ Static grep (§5a) returns hits for all three files.
5. ✅ Behavioral replay (§5b): the trigger prompt produces a named plan-mode
   option; the approval-language variant suppresses it. (This requires a live
   session run by the user/parent — the subagent cannot self-verify behavior.)
6. ✅ No regression: the existing "Plan mode discipline" approval-language check
   and Shift+Tab fallback are unchanged in behavior (only a pointer line added).
7. ✅ The §5c self-check checklist is referenced from the rule (or from
   `P:\AGENTS.md`) so it is visible at recommendation-construction time.

Criterion 5 is the only one that cannot be completed by editing files alone —
it is the falsifier that separates "rule present" from "rule works."

---

## 8. Open questions (need user input before/after landing)

1. **Terminology (blocking-ish).** Is `/plan` intended to be (a) plan mode via
   the built-in `enter_plan_mode` tool [assumed here], (b) a new `/plan` slash
   skill to be created, or (c) the legacy `/planning` SDLC skill? None of (b)/(c)
   are installed. If (a), the rule text is correct as-is. If (b), the skill must
   be created first and the rule's example wording updated to invoke it.

2. **Mirror scope.** Should this behavior also apply in Claude Code sessions
   (mirror into `P:\.claude\CLAUDE.md` or a rules file), or is it Grok-only?
   The global `~/.grok/AGENTS.md` is Grok-only by definition; the workspace
   `P:\AGENTS.md` applies to both hosts.

3. **Fire threshold.** Comfortable with "≥2 of 6, and T2 alone is sufficient"?
   Alternatives: stricter "≥3 of 6" (fewer fires, risks re-introducing the gap
   for 2-trigger cases like the `yt-is` incident which had 4); looser "≥1 of 6"
   (more fires, alert-fatigue risk). The `yt-is` incident had T1+T2+T3+T6, so
   any of these thresholds would have caught it — the choice is about
   future-borderline cases.

4. **T2 standalone sufficiency.** Should "durable artifact ask" alone force
   plan mode, or should it require a second trigger? Argued here as
   standalone-sufficient because inline artifact output violates the existing
   "Durable artifacts" rule. Confirm or require a co-trigger.

5. **`/design` vs plan mode for artifact asks.** The legacy SDLC stack had a
   `/design` skill (CAPs). It is not installed in Grok. For design-doc asks
   specifically, is plan mode the right surface, or should the rule defer to a
   (to-be-created) `/design`? Out of scope for this rule but worth deciding
   before the wiki worked example is finalized.

6. **Model selection (`glm-5-2`).** The user requested this work be done on
   `glm-5-2`. The subagent cannot verify which model it is running on. If model
   fidelity matters for the rule text quality, the parent should confirm the
   run model before landing.

---

## 9. Summary of design decisions

- **Canonical home is the global file** (`~/.grok/AGENTS.md`), not the workspace
  table — because the gap is host-general (any Grok session can reproduce it)
  and the global file is the single source the workspace mirrors point at.
- **Bias is inverted explicitly:** "when in doubt, surface plan mode." The
  existing default ("proceed unless ambiguous") is what produced the omission.
- **The rule operates at the recommendation-construction layer**, not the
  mode-entry layer. It forces plan mode *into the option list*, which is the
  exact failure surface ("option missing, not buried").
- **Durable-artifact trigger (T2) is standalone-sufficient**, anchoring the rule
  to the existing "Durable artifacts" contract so plan mode becomes the
  structurally correct surface for any output that must outlive the chat.
- **Plan mode vs `/go` is resolved by execution authorization** — the
  discriminator the `yt-is` incident needed and lacked.
