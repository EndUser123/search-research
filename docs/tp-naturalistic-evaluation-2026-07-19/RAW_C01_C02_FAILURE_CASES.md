# Prior Evaluation — Raw C01 and C02 Responses (recovered 2026-07-19)

Source: session transcript of evaluation run 2026-07-19.
These are the two cases where /tp lost to baseline. They are the focus of the new investigation.

---

## C01 — case prompt

> My PreToolUse hook for guarding CLAUDE.md edits has grown to about 250 lines and now does three different checks (path format, content blacklist, version bump). Is it worth splitting into three separate hooks, or just tidying up the internals?

## C01 — Baseline response (winner, score 37/50)

**Stance:** Tidy first, split only if one of the three checks has independent ownership, independent bypass needs, or independent bug history. For three guards on the same event with the same input/output shape, the deciding factor is **atomic failure reporting** — and that pulls toward keeping them together.

[Two real options laid out: Option A tidy internals, Option B split into three. Option A wins on atomic failure reporting (user sees all three problems in one block message); Option B has failure-reporting semantics the responder hasn't verified.]

[Names the pivot that would flip the recommendation: whether the three checks ever need to fire independently. If co-triggered, tidying wins.]

[Lists three things unverified that would sharpen the answer: hook dispatch after exit 2, whether 250 lines is duplication vs distinct, failure co-occurrence.]

Default to tidying — splitting a working PreToolUse chain for organization reasons without a concrete ownership or bypass need usually costs more in dispatch overhead and broken atomic reporting than it saves in line count.

## C01 — /tp response (loser, score 28/50)

[Opened by claiming to have searched for the hook and found nothing matching — "no PreToolUse hook in `P:/.claude/hooks/` or `P:/packages/.claude-marketplace/plugins/` combines `CLAUDE.md` guarding with both a blacklist and version bump logic"]

## Stance: **Split.** Tidying internals is the wrong fix here.

**Goal:** Decide whether one 250-line PreToolUse hook doing three orthogonal checks should become three hooks or be reorganized internally.

### Why the 250-line threshold is the wrong frame
The question isn't size — it's **cohesion**. Three checks can be:
- **Cohesive** (they share state, parsing, or invariants) → keep together
- **Coincidentally coupled** (only the trigger event ties them) → split

Your three checks share **only the trigger** (`Edit/Write` to a CLAUDE.md path). They don't share parsing, state, or invariants. That is the textbook case for splitting.

[Asserts: "process isolation is free failure isolation" — this is the unsupported claim. Asserts: "3× process startup on every CLAUDE.md edit (≈300ms cumulative vs ≈100ms on Windows)" — this is the unsupported timing number.]

### Confidence & assumptions
- **[INFERENCE]** That the three checks are truly orthogonal. I haven't read the file.
- **[FACT]** `P:/.claude/rules/hook-development.md` mandates dispatch-chain awareness and stderr-on-block.

### Smallest evidence-producing next step
If you want me to be more concrete, paste the three check function bodies (or the whole file).

---

## C01 — Judge's most important reason

> "Response A identifies the actual decision criterion (atomic failure reporting depends on hook dispatch semantics after exit 2) and grounds its recommendation in that real architectural constraint; Response B's central claim ('process isolation is free failure isolation') is actually wrong under sequential-stop dispatch and rests on an unverified orthogonality inference plus an unsupported 300ms vs 100ms timing number."

## C01 — Why this is the focus of the new investigation

The /tp response:
1. Searched for the file (good) and reported not finding it (good).
2. Then reasoned ABOUT the file's structure WITHOUT reading it (the failure).
3. Asserted orthogonality ("they don't share parsing, state, or invariants") — unsupported.
4. Asserted a specific timing number (300ms vs 100ms) — unsupported.
5. Concluded "split" — a specific architectural recommendation grounded in unsupported premises.

The baseline response:
1. Did not search.
2. Reasoned about the architectural trade-off (atomic failure reporting).
3. Explicitly named what it hadn't verified and how that would sharpen the answer.
4. Recommended tidying as the default, with explicit pivots.

The failure mode: **/tp reasoned about workspace-dependent facts (orthogonality of checks, timing of dispatch) without inspecting the workspace, AND presented unsupported inferences with confident specificity.**

---

## C02 — case prompt

> I want to rip out the legacy v1 lookup path in the dispatcher module. We kept it around as a fallback in case v2 broke during a deploy, but it hasn't been hit in eight months and the code is in the way of a refactor I want to do. Just delete it, right?

## C02 — /tp response (loser, score 33/50)

**Stance: not yet, and "just delete it" is the wrong frame.**

Three things to push back on:

**1. "Hasn't been hit in eight months" is an unverified absence claim.** It's almost always inferred from "I haven't seen it" — not measured. Convert it to a fact with a log/metric check or a static audit of call sites.

**2. The fallback exists for a stated reason, and that reason doesn't expire on a calendar.** "v2 broke during a deploy" is exactly the failure mode v1 protects against.

**3. "In the way of a refactor" is the weakest reason to delete a fallback.**

[Two paths: Path A verify-then-delete, Path B gate-don't-delete. Default: B.]

What I need to ground this: Where is the dispatcher module? Is v1 reachable via flag/config? What does "hasn't been hit" rest on — logs, metrics, or memory? What's the deploy verification story?

## C02 — Baseline response (winner, score 36/50)

[Opened by saying: "I started searching and I need to stop and ask — the workspace has multiple things that could be called 'the dispatcher' and none of them obviously match the v1-fallback pattern you described."]

[Provided a table of three actual grep results:]
- cc-model-router/__lib/classifier/deterministic.py:68 — regex matching "v1" or "v2" — a classifier pattern, not a lookup path
- snapshot/scripts/config.py:186,223 — cleanup logic for V1-format handoff files
- cc-skills-sdlc/skills/planning/references/artifact-contract.md:44 — migration note about normalizing legacy v1 section headings

[Then: "Which dispatcher? Give me the file path and I can do the rest."]

[Asked for: where does the 8-months claim come from; is the fallback wired through config, runtime check, or hard-coded]

[Offered the 5-step removal audit protocol conditional on the user providing the path]

**The framing "just delete it" is the part I'd push back on — not the deletion itself.**

## C02 — Judge's most important reason

> "Response B grounds its pushback in attempted evidence (concrete grep results across the workspace) and honestly reports what it could not find, while Response A delivers the same philosophical pushback entirely in the abstract — no search, no grounding in the user's actual codebase. B reduces the user's next-step burden by surfacing that the 'dispatcher' they describe doesn't obviously exist in the searched locations, which is actionable; A just asks for the same info without doing the homework."

## C02 — Why this is the focus of the new investigation

The /tp response:
1. Pushed back on the user's framing (good — this is what /tp should do).
2. Named what evidence it would need (good).
3. Did NOT actually search for the dispatcher (the failure) — even though the same tools were available to baseline.
4. Delivered the pushback in the abstract.

The baseline response:
1. Ran grep.
2. Reported findings honestly (including that the search was inconclusive).
3. Asked the user to point at the file.

The failure mode: **/tp produced structured pushback that was correct in principle but ungrounded in workspace state. Baseline did the same pushback AND searched, producing a more useful answer.**
