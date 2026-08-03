---
thread_id: a3f2c1d8-7e9b-4f8a-a2d3-1c6e5b7a9f01
parent_handoff_path: P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md
current_session_id: 019f8a66-ce7a-71c3-8655-8d6ee4d2ee4d
current_terminal_id: console
produced_at: 2026-07-22T18:00:00Z
status: CLOSED
handoff_type: plan
assigned_to: unassigned
accurate_as_of_head: a600948
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8a66-ce7a-71c3-8655-8d6ee4d2ee4d\chat_history.jsonl
---

# Handoff: Consolidate skill-improvement and skill-writing skills

## Objective (one sentence)

Reduce 14+ skill-authoring/improvement entry points to the fewest viable set by
creating a single Grok-native orchestration skill that extracts the best
techniques from disabled Claude plugins and third-party skills, with a shared
wiki reference for the transferable methodology.

## Why this exists

The operator asked to consolidate skill-improvement and skill-writing skills
into the fewest needed. Sessions 2026-07-21 and 2026-07-22 documented the
portfolio (`skill-development-portfolio.md` wiki concept), but no consolidation
action was taken. This handoff captures the analysis and the corrected plan.

**Related:** `P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md`
(that program is about slimming individual SKILL.md files; this one is about
reducing the *number* of overlapping skills).

## Critical finding: cc-* plugins are DISABLED on Grok Build

**[FACT]** (source: `~/.grok/active-surface.last.md`, read this session)

All 18 cc-* plugins are disabled in `~/.grok/config.toml [plugins] disabled`:

- `cc-skills-architect` → home of `skill-write`, `skill-from-docs`,
  `skill-to-page`, `evolve`, `prompt_refiner`
- `cc-skills-analysis` → home of `skill-audit`, `skill-similarity`,
  `claude-audit`
- `cc-skills-sdlc` → home of `writing-skills`, `improve-codebase-architecture`
- `improve-partner` → home of `improve`

Their skills ARE discoverable (`claude.skills: ON` compat flag loads SKILL.md
descriptions into the model's skill catalog), but:
- Plugin hooks are NOT firing
- Plugin router.py dispatch is NOT active
- Plugin version cache lifecycle is IRRELEVANT (disabled plugins don't rebuild)
- Referenced scripts MAY NOT WORK (they may depend on Claude Code tool surface)

**The only Grok-native skill-authoring skill is `create-skill`** at
`~/.grok/skills/create-skill/SKILL.md` and `~/.grok/bundled/skills/create-skill/`.

**Implication:** the original consolidation plan (merge skills across plugins,
bump versions, rebuild caches) is wrong for this host. On Grok Build, the
consolidation must happen at the **Grok-native skill layer**.

## The current landscape (14 ownable skills)

### Skill-specific lifecycle skills (the consolidation target)

| Skill | Plugin | Job | Active on Grok? |
|---|---|---|---|
| `create-skill` | `~/.grok/skills/` (Grok-native) | Simple create | **YES** |
| `create-skill` | `~/.grok/bundled/` (Grok-bundled) | Simple create | YES (can't edit) |
| `skill-write` | cc-skills-architect (DISABLED) | Create + eval loop + description optimization | Discoverable only |
| `skill-from-docs` | cc-skills-architect (DISABLED) | Create from docs/URLs/repos | Discoverable only |
| `skill-to-page` | cc-skills-architect (DISABLED) | Document -> HTML artifact | Discoverable only |
| `skill-audit` | cc-skills-analysis (DISABLED) | 8-category rubric audit + 10 subcommands | Discoverable only |
| `skill-similarity` | cc-skills-analysis (DISABLED) | Find similar/duplicate skills | Discoverable only |
| `writing-skills` | cc-skills-sdlc (DISABLED) | TDD-for-skills (thin copy) | Discoverable only |
| `improve` | improve-partner (DISABLED) | General artifact improvement | Discoverable only |
| `evolve` | cc-skills-architect (DISABLED) | Code modernization | Discoverable only |
| `improve-codebase-architecture` | cc-skills-sdlc (DISABLED) | Architecture friction | Discoverable only |
| `claude-audit` | cc-skills-analysis (DISABLED) | Runtime config audit | Discoverable only |
| `prompt_refiner` | cc-skills-architect (DISABLED) | Already deprecated -> /improve | Stub |
| `skillopt` | `~/.codex/skills/` (Codex-native) | Transcript-based optimization | Codex only |

### Third-party skills (ideas to extract, not merge)

| Skill | Source | Key technique |
|---|---|---|
| `writing-skills` | superpowers plugin (ENABLED) | TDD-for-skills: RED-GREEN-REFACTOR, pressure testing, rationalization tables |
| `skill-creator` | Claude marketplace (Anthropic) | Description optimization via 60/40 train/test split, eval viewer |
| `skill-development` | plugin-dev (Anthropic) | Progressive disclosure patterns |

### Not skill-specific (excluded from consolidation)

`improve`, `evolve`, `improve-codebase-architecture`, `claude-audit` — these
are codebase/config improvement tools that happen to be able to target skills.
They belong in a different consolidation conversation.

## Overlap analysis

Three distinct lifecycle jobs:

```
CREATE ----------------- AUDIT ----------------- IMPROVE
(from scratch/docs)     (quality/similarity)   (iterate from evidence)
```

| Capability | skill-write | create-skill | writing-skills | skill-audit | skill-similarity | skillopt |
|---|---|---|---|---|---|---|
| New skill from scratch | full eval loop | simple | TDD | - | - | - |
| Description optimization | 60/40 split | - | - | - | - | - |
| Pressure testing (TDD) | - | - | full | - | - | - |
| Quality rubric audit | - | - | - | 8-cat | - | - |
| Similarity/dedup | - | - | - | prune subcmd | scoring algo | - |
| Eval-loop improvement | full | - | - | improve subcmd | - | - |
| Transcript improvement | - | - | - | - | - | held-out validation |
| Hook generation | - | - | - | gen-hooks | - | - |

**Key overlaps:**
1. `create-skill` is a strict subset of `skill-write` (simple scaffolding, no eval)
2. `writing-skills` (sdlc) is a thin copy of `writing-skills` (superpowers)
3. `skill-similarity` overlaps with `skill-audit prune` subcommand
4. `skillopt` is Codex-specific (different runtime)

## Alternatives considered (per /tp review, 2026-07-22)

### Alternative 1: 5 modes vs 3 modes

**Selection criterion:** fewest catalog entries x maximum capability coverage.

| Option | Modes | Pros | Cons |
|---|---|---|---|
| **A: 5 modes** | create, audit, improve, find-dupes, from-docs | Maximum coverage in one entry | `find-dupes` is a one-shot scan (thin value inside an orchestrator); `from-docs` just points at a disabled plugin (no Grok-native value) |
| **B: 3 modes** | create, audit, improve | Cleanest orchestrator; `find-dupes` is a standalone scan script; `from-docs` stays as pointer | Operator needs to know about the standalone find-dupes script |

**Chosen: B (3 modes).** `find-dupes` is a mechanical scan, not an iterative
workflow — it belongs as a script in `skill-dev/scripts/` or a wiki page, not
a mode. `from-docs` adds no Grok-native capability (the plugin is disabled);
it's a routing pointer, not a mode. The 3 remaining modes (create, audit,
improve) are each genuine multi-step workflows that benefit from orchestration.

### Alternative 2: extend create-skill vs create new skill-dev

**Selection criterion:** fewest catalog entries x clarity of purpose x cold-start discoverability.

| Option | Pros | Cons |
|---|---|---|
| **A: Extend create-skill** | Zero new catalog entries; existing user trust; already active | Description must cover 3 jobs (create + audit + improve) which muddies trigger accuracy; name doesn't suggest audit/improve |
| **B: Create new skill-dev** | Clean trigger: "skill-dev" clearly covers the full lifecycle; create-skill stays simple (its name promises simplicity) | One new catalog entry; cold-start discoverability depends on description quality |

**Chosen: B (create new skill-dev).** The description field is the ONLY signal
the model sees at selection time. A skill named `create-skill` with a
description covering auditing and improvement will mis-trigger — the model
sees "create" and routes there for creation tasks only, missing the audit and
improve capabilities. A dedicated `skill-dev` with a description covering the
full lifecycle has cleaner triggering. The one extra catalog entry is worth
the trigger accuracy. `create-skill` stays as the simple entry point with a
pointer to `skill-dev` for advanced needs.

### Alternative 3: archive (Move-Item) vs DEPRECATED-description for removal

**Selection criterion:** multi-terminal isolation x stale-data immunity x existing-convention alignment.

| Option | Pros | Cons |
|---|---|---|
| **A: Archive (Move-Item)** | Removes entry from catalog entirely (if scanner excludes path) | Windows file-lock risk on open handles; `index_skills.py` has no exclusion logic (confirmed by grep); new pattern deviates from existing convention |
| **B: DEPRECATED-description** | Matches existing convention (`check-work`, `code-review` use this); no file moves (zero lock risk); no scanner changes needed; body stays as fallback (stale-data immune) | Catalog still shows the entry (with DEPRECATED prefix) |

**Chosen: B (DEPRECATED-description).** The existing convention is proven
(`check-work` and `code-review` both follow it). It's simpler (a frontmatter
edit, not a file move), safer (no Windows lock issues), and self-documenting
(the model sees "DEPRECATED -> use /skill-dev audit" in the catalog and
routes automatically). The catalog still shows the entry — but with a clear
redirection, which is better than silent absence.

## Corrected consolidation approach (Grok Build native)

### Design invariants (mandatory)

1. **Multi-terminal isolation**: only additive changes during the consolidation.
   Never move, rename, or body-replace a file another terminal may be reading.
   Copy-first; removal is a separate, deferred step. For removal: use
   DEPRECATED-description convention (frontmatter edit), NOT file moves.
2. **Stale-data immunity**: deprecation pointers keep the original body as
   fallback. Wiki references are self-contained (capture the technique, don't
   just link to a disabled plugin's SKILL.md). No dependency on disabled-plugin
   state for core functionality.
3. **Grok Build native**: the consolidated skill lives at
   `~/.grok/skills/<name>/SKILL.md` where it is fully active — not in a
   disabled plugin where it's only discoverable.

### Target architecture

```
~/.grok/skills/
  create-skill/          <- UPDATED: add pointer to skill-dev for advanced needs
  skill-dev/             <- NEW: single Grok-native skill lifecycle skill
    SKILL.md             <-   instrument (routing + core workflow)
    references/
      create.md          <-   creation patterns (from skill-write + create-skill)
      audit.md           <-   audit rubric (from skill-audit 8-category)
      improve.md         <-   improvement patterns (from skillopt + eval loop)
      tdd-for-skills.md  <-   TDD discipline (from superpowers writing-skills)

P:/.data/wiki/concepts/
  skill-lifecycle-toolkit.md  <- NEW: shared techniques reference + routing table
```

### What the consolidated `skill-dev` skill does

One Grok-native skill with 3 modes (per alternatives analysis above):

| Mode | Trigger | What it does | Techniques sourced from |
|---|---|---|---|
| `create` (default) | "create a skill", "new skill" | Interactive scaffolding + structure guidance | `create-skill` + `skill-write` authoring patterns |
| `audit` | "audit this skill", "review skill quality" | 8-category rubric scoring + recommendations | `skill-audit` rubric (condensed) |
| `improve` | "improve this skill" | Eval loop: baseline -> edit -> compare -> promote/reject | `skill-write` eval loop + `skillopt` held-out validation |

**Not modes (handled differently):**
- **Find duplicates**: a standalone scan procedure in `references/audit.md`
  (or a script in `skill-dev/scripts/`), not an orchestration mode. The
  operator can ask "find duplicate skills" and the skill-dev instructions
  point to the procedure.
- **From-docs**: a routing pointer in the SKILL.md ("if you want to convert
  external documentation, use `/skill-from-docs` if the plugin is enabled;
  otherwise, see `references/create.md` for manual doc-to-skill conversion").
  Not a mode — the plugin is disabled and adds no Grok-native value.

**Key design decision**: the skill is self-contained. It captures the essential
instructions for each mode inline. It references the wiki concept for deep
methodology. It does NOT depend on disabled plugin scripts being executable.

### What happens to the existing skills

| Skill | Action | Isolation-safe? |
|---|---|---|
| `create-skill` (Grok user) | Add pointer to `skill-dev` at top; keep body | additive |
| `create-skill` (Grok bundled) | Leave unchanged (can't edit bundled) | no change |
| cc-skills-* (disabled plugins) | WI-5: mark DEPRECATED in description; keep body | frontmatter edit only |
| `writing-skills` (superpowers, ENABLED) | Leave unchanged — still works | no change |
| `skillopt` (Codex) | Leave unchanged — different runtime | no change |

**The consolidation is additive first (WI-1 through WI-4), then
DEPRECATED-description (WI-5).** No file moves. No body replacements.

## Work items

### Work Item 1: Create wiki concept `skill-lifecycle-toolkit.md`

**Path:** `P:/.data/wiki/concepts/skill-lifecycle-toolkit.md`

**Content:**
- The skill lifecycle map (create -> audit -> improve -> document)
- Routing table: "if you want to X, use mode Y"
- The DEPRECATED-description convention for retiring Grok-native skills
  (from this session's /tp-reviewed analysis: `check-work` and `code-review`
  already use this pattern; it's simpler and safer than Move-Item archiving)
- 5 transferable techniques (extracted, self-contained):
  1. TDD-for-skills (RED-GREEN-REFACTOR) — from superpowers `writing-skills`
  2. Held-out validation — from `skillopt`: only accept improvements that win on unseen examples
  3. Description optimization — from `skill-write`/`skill-creator`: 60/40 train/test split for trigger accuracy (**caveat: the automated backend `run_loop.py` uses `claude -p` CLI which is NOT available on Grok Build; the methodology is captured but execution is deferred**)
  4. Pressure testing — from superpowers: test discipline skills under competing incentives
  5. Rationalization tables — from superpowers: capture and counter agent rationalizations
- Cross-references to source skills (for when plugins are re-enabled)

**Stale-data property:** self-contained. Each technique is documented inline,
not just linked. If a source skill drifts, the wiki technique is still valid.

**Verification:** page exists; `wc -l` > 50; techniques are self-contained.

### Work Item 2: Create `skill-dev` Grok-native skill

**Path:** `~/.grok/skills/skill-dev/SKILL.md` + `~/.grok/skills/skill-dev/references/*.md`

**SKILL.md (instrument, <=15KB):**
- Frontmatter with `name: skill-dev`, description with trigger phrases
- Mode routing table (create / audit / improve)
- Core workflow per mode (condensed — the instrument)
- Pointers to `references/*.md` for deep methodology
- Link to wiki concept for technique reference

**references/create.md:**
- Skill structure conventions (frontmatter, description, progressive disclosure)
- The instrument-vs-reference split (from skill-refactoring-program handoff)
- Directory structure patterns
- Description writing guide (trigger-first, not workflow-summary)

**references/audit.md:**
- 8-category rubric (condensed from skill-audit's scoring-rubric.md)
- Common failure patterns (from skill-audit's prompt patterns P1-P8)
- Capability preservation check (from skill-audit's preserve subcommand)
- Find-duplicates procedure (from skill-similarity scoring algorithm)

**references/improve.md:**
- Eval loop procedure (from skill-write: baseline -> edit -> compare -> iterate)
- Held-out validation gate (from skillopt)
- Description optimization procedure (from skill-write's run_loop.py)
  **NOTE:** the automated `run_loop.py` backend requires `claude -p` CLI
  (Claude Code only). On Grok Build, this procedure is manual: run eval
  cases with and without the skill, compare outputs, iterate. The 60/40
  train/test methodology is captured; automated execution is `DEFERRED`.

**references/tdd-for-skills.md:**
- RED-GREEN-REFACTOR for skill content (from superpowers writing-skills)
- Pressure scenario design
- Rationalization table construction
- Form-matches-failure guide (prohibition vs recipe vs structural)

**Multi-terminal isolation property:** all new files. No existing file modified.

**Stale-data property:** self-contained. Each reference captures the technique,
not a link to a disabled plugin. If the plugin skills drift, the references
are still valid methodology.

**Verification:**
- `~/.grok/skills/skill-dev/SKILL.md` exists and is valid frontmatter
- Skill appears in session-reminder skill list on next session
- `/skill-dev` resolves (or the model auto-invokes on "create a skill" etc.)
- `diffusiongemma_read.py --batch` reads it without truncation (<=15KB)

### Work Item 3: Add pointer to `create-skill` (additive edit)

**Path:** `~/.grok/skills/create-skill/SKILL.md`

**Change:** add one block at the top of the body (after frontmatter):

```markdown
> **For advanced skill authoring** (eval loops, description optimization,
> quality auditing, TDD discipline), use `/skill-dev` instead.
> This skill covers simple scaffolding only.
```

**Multi-terminal isolation property:** additive. The existing body stays
intact. Another terminal reading the file sees one extra line; no content
removed.

**Stale-data property:** the pointer is a suggestion, not a dependency.
`create-skill` still works fully without `skill-dev`. If `skill-dev` doesn't
exist yet, the pointer is just a broken link (cosmetic, not functional).

**Verification:** read back the edited section; confirm pointer present and
original body intact.

### Work Item 4: Update routing docs

**Path:** `P:/.data/wiki/concepts/skill-development-portfolio.md`

Update the "Choosing the right one" table to show the consolidated state:

| If you want to... | Use |
|---|---|
| Create a new skill (simple) | `/create-skill` |
| Create a new skill (advanced, with eval) | `/skill-dev create` |
| Audit an existing skill | `/skill-dev audit` |
| Improve a skill iteratively | `/skill-dev improve` |
| Find duplicate/overlapping skills | `/skill-dev` -> references/audit.md (find-duplicates procedure) |
| Convert docs to skill | `/skill-from-docs` (if plugin enabled) or manual per references/create.md |
| Document a skill as HTML | `/skill-to-page` (if plugin enabled) |
| TDD discipline for skills | `/skill-dev` -> references/tdd-for-skills.md |

Regenerate skill catalog: `python P:/.data/wiki/scripts/index_skills.py`

### Work Item 5: Mark redundant Claude plugin skills DEPRECATED (after skill-dev is proven)

**Prerequisite:** WI-1 through WI-4 complete AND skill-dev has been verified
as a functional superset (cold-start test passes, each mode works).

**Operator authorization:** "we can remove claude skills as long as we replace
the functionality with our improved superset skill" (2026-07-22).

**Method: DEPRECATED-description convention** (per /tp review and existing
convention used by `check-work` and `code-review` in `~/.grok/skills/`).

For each skill below, edit the SKILL.md frontmatter `description` field to
prepend: `DEPRECATED — use /skill-dev <mode> instead.` Keep the body intact
as fallback reference.

**CEC ledger (Completion Evidence Contract per sibling handoff):**

| Skill | Plugin | Replaced by | Old-source | Parent-source | Backend-exists | Behavior evidence | CEC status |
|---|---|---|---|---|---|---|---|
| `skill-write` | cc-skills-architect | skill-dev create + improve | SKILL.md verified | skill-dev SKILL.md (after WI-2) | Eval loop: YES (manual). Description optimization (`run_loop.py`): NO — requires `claude -p` CLI, absent on Grok Build | Cold-start test (WI-2 verification) | `captured` for eval loop; `pending + DEFERRED` for description optimization |
| `skill-audit` | cc-skills-analysis | skill-dev audit | SKILL.md verified | skill-dev SKILL.md + references/audit.md | Rubric scoring: YES (inline instructions). Python scripts (`prune_scan.py`, etc.): NOT vendored — methodology captured, automation deferred | Cold-start test | `captured` for rubric; `pending` for script automation |
| `skill-similarity` | cc-skills-analysis | skill-dev audit (find-duplicates procedure) | SKILL.md verified | references/audit.md | Scoring algorithm: captured as procedure. `skill-similarity.py`: NOT vendored | N/A (procedure, not script) | `captured` (methodology); `pending` (script) |
| `writing-skills` | cc-skills-sdlc | skill-dev references/tdd-for-skills.md | SKILL.md verified | references/tdd-for-skills.md | N/A (pure methodology, no backend) | Cold-start test | `captured` |
| `prompt_refiner` | cc-skills-architect | already deprecated -> /improve | SKILL.md verified (already stub) | /improve (DISABLED plugin) | N/A (already a stub) | N/A | `already_deprecated` |

**What is NOT deprecated (out of scope or genuinely unique):**

| Skill | Why kept |
|---|---|
| `skill-from-docs` | Genuinely unique machinery (doc scraping, AST, OCR) — methodology folded into skill-dev but scripts are non-trivial |
| `skill-to-page` | Genuinely unique (10-stage HTML compiler pipeline) — not an improvement skill |
| `evolve` | Not skill-specific (codebase modernization) |
| `improve` | Not skill-specific (general artifact improvement) |
| `improve-codebase-architecture` | Not skill-specific (code architecture) |
| `claude-audit` | Not skill-specific (runtime config audit) |
| `writing-skills` (superpowers) | Third-party, ENABLED — not ours to deprecate |

**Why DEPRECATED-description, not archive (Move-Item):**

1. **Existing convention:** `check-work` and `code-review` at `~/.grok/skills/`
   already use this pattern. The model is accustomed to seeing DEPRECATED
   entries and routing to the replacement. (Verified: both SKILL.md files
   confirmed to use this pattern, session 2026-07-22.)
2. **Multi-terminal safety:** frontmatter edit is atomic and non-locking.
   No `Move-Item` -> no Windows file-lock IOException risk.
3. **Catalog scanner:** `index_skills.py` has no path-exclusion logic (verified
   by grep, session 2026-07-22). Archiving without scanner changes would leave
   the entries visible anyway. DEPRECATED-description works WITH the scanner
   — the entry stays visible but redirects.
4. **Stale-data immunity:** the body stays as fallback. If `skill-dev` is
   missing or broken, the operator can read the original skill body for
   reference. The DEPRECATED prefix is advisory, not destructive.

**Procedure per skill:**
1. Read the SKILL.md frontmatter
2. Prepend `DEPRECATED — use /skill-dev <mode> instead.` to the `description`
3. Verify the edit persisted (read back)
4. Grep for references to the old skill name in other skills' Suggest blocks
5. Update any routing references found

**Multi-terminal isolation property:** frontmatter edit only. No file move.
No body replacement. Another terminal loading the skill sees a slightly
different description but the same body content.

**Stale-data property:** the DEPRECATED prefix points to `skill-dev`, but the
original body is preserved. If `skill-dev` doesn't exist, the operator can
still read and use the original skill. The pointer is advisory.

## What NOT to do

- **Do NOT deprecate disabled-plugin skills before skill-dev is proven.** The
  deprecation (WI-5) is gated on WI-1 through WI-4 completing and the cold-start
  test passing. Deprecating before proof leaves a capability gap.
- **Do NOT use Move-Item / archive for removal.** Use DEPRECATED-description.
  Archive has Windows lock risk, scanner-exclusion issues, and deviates from
  the existing convention. (Per /tp review, 2026-07-22.)
- **Do NOT deprecate non-skill-specific skills** (`evolve`, `improve`,
  `claude-audit`, `improve-codebase-architecture`). They're out of scope —
  different domain, different consolidation conversation.
- **Do NOT deprecate genuinely unique skills** (`skill-from-docs`, `skill-to-page`).
  They have machinery that can't be condensed into a reference file.
- **Do NOT deprecate third-party skills** (`writing-skills` from superpowers).
  They're not ours to deprecate; they're also still ENABLED on Grok Build.
- **Do NOT depend on disabled-plugin scripts working** in the new skill-dev.
  The new skill must be self-contained instructions, not a wrapper around
  plugin scripts that may not execute on Grok Build.
- **Do NOT claim description optimization is fully captured.** The `claude -p`
  backend does not exist on Grok Build. The methodology is captured; automated
  execution is `DEFERRED`. State this explicitly in the skill and wiki.

## The final picture

```
BEFORE (Grok Build perspective):
  ACTIVE:   create-skill (Grok-native, simple only)
  DISCOVERABLE (disabled plugins): skill-write, skill-audit, skill-similarity,
            writing-skills, skill-from-docs, skill-to-page, evolve, improve,
            claude-audit, improve-codebase-architecture, prompt_refiner
  THIRD-PARTY: writing-skills (superpowers, ENABLED)
  CODEX:    skillopt

AFTER (all work items complete):
  ACTIVE:   create-skill (Grok-native, simple + pointer to skill-dev)
            skill-dev (Grok-native, CREATE + AUDIT + IMPROVE)
  DEPRECATED (disabled plugins, body kept as fallback):
            skill-write, skill-audit, skill-similarity, writing-skills(sdlc),
            prompt_refiner — description now says "DEPRECATED -> /skill-dev"
  REMAINING (disabled plugins, kept): skill-from-docs, skill-to-page, evolve,
            improve, claude-audit, improve-codebase-architecture
  THIRD-PARTY: unchanged
  CODEX:    unchanged

  + wiki: skill-lifecycle-toolkit.md (shared techniques reference)
```

Net result on Grok Build: **1 -> 2 active Grok-native skills** (create-skill
for simple, skill-dev for everything else). **5 redundant Claude plugin skills
marked DEPRECATED** (body preserved as fallback, description redirects to
skill-dev). 5 genuinely-unique or out-of-scope skills kept. The operator has
ONE new entry point to learn instead of 14.

## Verification (falsifiable)

1. After WI-1: wiki page exists at the named path; content is self-contained
2. After WI-2: `skill-dev` appears in session-reminder skill list; SKILL.md
   is <=15KB; `diffusiongemma_read.py --batch` reads without truncation
3. After WI-3: `create-skill` body still works; pointer line is present
4. After WI-4: portfolio wiki page updated; skill catalog regenerated
5. Cold-start test: a fresh agent reading only `skill-dev/SKILL.md` can
   correctly route to the right mode and find detailed instructions
6. After WI-5 (per skill): DEPRECATED prefix present in description; original
   body intact; grep for old skill name shows routing references updated

## Falsifier

This consolidation is wrong if:
- The `skill-dev` skill becomes a monolith that violates the instrument-vs-
  reference split (the refactoring-program handoff's target pattern)
- Agents can't discover `skill-dev` because the description isn't triggering
  correctly on Grok Build (description optimization needed)
- The disabled-plugin skills' techniques can't be faithfully condensed into
  wiki/references without losing load-bearing detail
- The operator re-enables the cc-* plugins, making the Grok-native
  consolidation redundant (in which case the plugin-level merge from the
  original plan becomes viable)
- A cold-start agent, given only `skill-dev/SKILL.md` + references, cannot
  produce a working description-optimization loop because the `claude -p`
  backend is absent (CEC status should be `pending + DEFERRED`, not `captured`)

## Resumption protocol

1. Read this handoff (the analysis + corrected approach + /tp review changes)
2. Read `P:/.data/wiki/concepts/skill-development-portfolio.md` for the
   prior portfolio analysis
3. Read `~/.grok/active-surface.last.md` to confirm current plugin state
4. Start with WI-1 (wiki concept — no isolation risk, pure additive)
5. Then WI-2 (skill-dev — new files, no isolation risk)
6. Then WI-3 (create-skill pointer — one additive edit)
7. Then WI-4 (doc updates)
8. Then WI-5 (DEPRECATED-description edits — ONLY after WI-1-4 verified and
   cold-start test passes; edit one skill description at a time with grep
   verification of routing references)

## /tp review history

- **2026-07-22 /tp (two-lens, parent-inherited model):** REVISE -> REVISE.
  Three findings changed the plan: (1) CEC ledger gap — description optimization
  backend (`claude -p`) absent on Grok Build, confidence downgraded to
  `pending + DEFERRED`; (2) 5 modes asserted without justification -> reduced
  to 3, with `find-dupes` as a procedure and `from-docs` as a pointer;
  (3) archive (Move-Item) has Windows lock + scanner issues -> switched to
  DEPRECATED-description convention matching existing `check-work` and
  `code-review` pattern. All three findings verified against source files
  by the orchestrator (3 confirming tool calls).

## Related artifacts

- `P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md` — sibling
  program (slim individual SKILL.md files)
- `P:/.data/wiki/concepts/skill-development-portfolio.md` — portfolio analysis
- `P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md` — patterns
- `P:/.data/wiki/concepts/compound-skill-improvement-patterns.md` — compound skill patterns
- `~/.grok/active-surface.last.md` — confirms cc-* plugins disabled
