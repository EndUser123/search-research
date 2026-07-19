# Stream 4: Prompt + schema enhancements handoff

| Field | Value |
|---|---|
| **Stream** | Text-level edits across /tp, /review or /red-team, wiki SCHEMA.md |
| **Priority** | LOWER — all text edits, no code, no plugin mutation (except red-team agents) |
| **Status** | Not started; all designs complete |
| **Effort** | ~1 hour (single subagent, batched edits) |
| **Delegation** | One subagent (`capability_mode: read-write`); benefits from Stream 3's research |

## Goal

Five prompt/schema enhancements that improve quality of existing skills without code changes. All are text edits to SKILL.md files or agent prompts.

## Background

From the session's research and critical review:
- `/tp` lacks a disconfirmation-search step (the user identified this gap)
- `/review` and `/red-team` lack Simplification and Test Quality lenses (HAMY's 9-agent pattern has these; we don't)
- `/red-team` findings don't use `@contradicts` typed links for cross-specialist conflicts
- QMD reindex ritual is documented in SCHEMA.md §11 but lacks a quarterly cadence note
- Stream 3's ultrathinks research may surface additional patterns to port

## Deliverables

### 1. Disconfirmation search in /tp (~10 lines)

**File:** `C:/Users/brsth/.grok/skills/tp/SKILL.md` or `protocol.md`

**Change:** Add as a **separate post-correction step** — NOT inside the 5-line circuit breaker. The circuit breaker stays fast and behavioral (instant, no tool dependency). The disconfirmation search fires only when the correction produces a recommendation worth verifying:

> **Post-correction disconfirmation step (conditional):** After the circuit breaker completes and you've stated your correction, IF the correction includes a factual claim or recommendation the user might act on, run a **disconfirmation search**: phrase a query that would REFUTE the hypothesis ("does this actually work?", "is this bug already fixed upstream?", "what evidence would prove this wrong?"). Use `minimax-search__web_search` (primary) or `web-search-prime__web_search_prime` with `search_recency_filter=oneMonth` (for version-sensitive questions). If disconfirmation evidence exists, surface it before the user acts. Skip this step for purely behavioral corrections (e.g., "you agreed too fast") — only factual claims warrant disconfirmation.

**Context:** This session's biggest single improvement to /tp methodology. The user identified it; the research validated it (Popperian falsificationism; Karpathy reviewers emphasize "honesty about what you didn't find"). The separation from the circuit breaker preserves /tp's speed for the common case (behavioral drift) while adding rigor for the less-common case (factual claims).

### 2. Simplification lens (~20 lines)

**File:** Either `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-logic.md` (extend existing logic specialist) or create `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-simplification.md` (new specialist).

**Change:** Port HAMY's Simplification & Maintainability Reviewer:

> Ask "could this be simpler?" Check for:
> - Premature abstractions (helpers used once, unnecessary indirection)
> - Over-configured solutions when simple would suffice
> - Framework-level solutions for one-off problems
> - Clever code that sacrifices clarity
> - Change atomicity: is this one logical unit? Are unrelated changes mixed in?

**Source:** `https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents` — Agent 9.

### 3. Test Quality lens (~20 lines)

**File:** Same location as #2 (either extend or new specialist).

**Change:** Port HAMY's Test Quality Reviewer:

> Evaluate test coverage ROI:
> - Are critical paths tested? (auth, payments, data integrity)
> - Do tests verify behavior, not implementation details?
> - Will tests break for the wrong reasons? (brittle selectors, testing internals)
> - Is coverage proportionate to risk? (not all code needs equal coverage)
> - Flakiness risk: timing dependencies, race conditions, order-sensitive assertions

**Source:** Same HAMY blog post — Agent 6.

### 4. @contradicts in /red-team findings schema (~5 lines)

**File:** `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` — findings schema section.

**Change:** Add to the findings JSON schema:

> When a finding contradicts another specialist's finding, add `"contradicts": "<FINDING-ID>"` to the finding object. The critic should surface these as contradiction resolutions (already handled by the tiebreaker, but the typed link makes the conflict machine-readable).

**Also:** Update the critic agent prompt to look for `contradicts` fields and prioritize resolving them.

### 5. QMD quarterly reindex note (~3 lines)

**File:** `P:/.data/wiki/SCHEMA.md` §11 (Recommended cadence).

**Change:** The quarterly bullet already exists but says "re-baseline the QMD relevance score." Add:

> Also run `qmd update` (not `qmd update --collection wiki` — that syntax is wrong; `update` takes positional or no args) to refresh the full index against any corpus growth since the last reindex.

**Note:** This fix depends on Stream 2's QMD syntax fix being applied first. If Stream 2 hasn't run, the syntax in this addition will be correct but the rest of SCHEMA.md §11 may still have the old wrong syntax.

### 6. Per-file commit scoping in grok-safe-git (~10 lines)

**File:** `~/.grok/skills/grok-safe-git/SKILL.md`

**Change:** Add a commit-safety rule:

> **Multi-session commit safety:** Never use `git add -A` or `git add .` when other sessions may be working in the same tree. Stage only the specific files this session created or modified. Extract the file list from the session's edit log or `git diff --name-only <session-start-SHA>..HEAD`. If any file outside this session's scope appears in `git status --short`, do NOT commit it — report it as "foreign dirty" and let the owning session handle it.
>
> **Why:** In a shared tree, `git add -A` captures ALL dirty files including another session's in-progress edits. Per-file scoping (`git add <file1> <file2>`) prevents cross-capture. This is the safety net when worktrees aren't used. The ecosystem-proven structural fix is worktree-per-task (see `multi-terminal-worktree-execution-pattern.md`), but per-file scoping is sufficient when sessions touch non-overlapping file sets.

**Context:** Validated by Augment Code's parallel agent guide ("assign agents to strictly non-overlapping file domains before work begins") and our existing wiki page `auto-stage-commit-strategies.md` ("No 'diff-only commit' primitive exists"). The per-file approach is what practitioners default to when worktree isolation isn't warranted.

### 7. UPDATE existing wiki page: multi-terminal-git-coordination-primitives.md (~30 lines added)

**File:** `P:/.data/wiki/concepts/multi-terminal-git-coordination-primitives.md` (ALREADY EXISTS — created earlier this session by another session; has 3 coordination primitives)

**Change:** The page was updated during this session's `/wiki` ingest to add Primitive 4 (per-file commit scoping) and ecosystem tool sources. **Verify the update landed.** If Primitive 4 is present and the ecosystem sources are cited, this deliverable is DONE. If not, add:

- Primitive 4: Per-file commit scoping section (the text is already in the page from the `/wiki` ingest — check it exists)
- Ecosystem tools in Sources: `augmentcode/auggie`, `jayminwest/overstory`, `hiragram/agent-workspace`, `block/agent-task-queue`, Dagger Container-Use, `obra/superpowers` issue #597

**Note:** Deliverable #6 (per-file commit scoping rule in grok-safe-git) and this deliverable (#7) are related but distinct: #6 puts the rule in the skill prompt; #7 puts it in the wiki page. Both should exist. The wiki page is the reference; the skill prompt is the enforcement.

### 8. Execution-status block in /go Step 6 (~15 lines)

**File:** `C:/Users/brsth/.grok/skills/go/SKILL.md` — Step 6 (Progress + final report)

**Change:** After the final report, add:

> **Execution status (when input was a file path):** If `/go` was invoked with `/go execute <file>`, append a `## Execution Status` block to the END of that file. Leave all original content above intact. Format:
>
> ```markdown
> ## Execution Status
>
> Updated: <UTC ISO-8601>
> Session: <session-id>
> Agent: grok
>
> | # | Deliverable | Status | Evidence |
> |---|---|---|---|
> | 1 | <name> | ✅ DONE \| ⚠️ PARTIAL \| ❌ BLOCKED \| ❌ NOT STARTED | <command or file:line proof> |
>
> ### Key findings during execution
> - <each notable finding or blocker, one bullet per item>
> ```
>
> **Why:** crash recovery needs machine-readable pass/fail per deliverable; parallel sessions need to check dependency completion; findings discovered during execution must persist to disk, not just transcript. Status without findings = checkpoint without context. Findings without status = context without signal. Both are needed.
>
> **Convention:** original content above `## Execution Status`; results below. A future session reading the handoff knows: above = what to do; below = what happened. Never mutate the original content.

**Note:** This deliverable is text-only (one paragraph in the /go SKILL.md). No code, no script. The block is hand-written by the agent at GO DONE, not auto-generated by a hook.

### 9. Fix wiki_after_write.py Loguru stdout bug (~10 lines)

**File:** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_after_write.py` (around line 88-99)

**Problem (discovered by Stream 2 execution, Finding #2):** The script checks `out.startswith("[")` to gate JSON parsing of QMD output. But `qmd search` emits Loguru INFO lines to stdout BEFORE the JSON array, so this strict-prefix check always fails and the script falls back to grep. **This means auto-link has NEVER actually worked in practice** — every "auto-link returned empty" observation this session was masking this bug, not just corpus redundancy.

**Fix:** Replace `out.startswith("[")` with `out.find("[")` then slice from there:

```python
# Before (broken):
if out.startswith("["):
    results = json.loads(out)

# After (fixed):
idx = out.find("[")
if idx >= 0:
    results = json.loads(out[idx:])
```

Apply the same fix to `wiki_contradiction_scan.py` (around line ~149) which has the same pattern.

**Why this matters:** This is the single bug that has been masking auto-link functionality across the entire wiki. Fixing it means auto-link may actually start injecting `## Auto-related` sections — which would partially resolve the "QMD returns empty" problem we've been investigating all session. The corpus-redundancy conclusion (0.083 scores) may be partially confounded by this parsing failure.

**Also note:** As of this session, `P:/.data/wiki/` is now git-tracked (`.gitignore` updated: `.data/*` + `!.data/wiki/`). New wiki files will appear in `git status` and can be committed. The `_incoming/` staging directory remains excluded.

## Dependencies

- Benefits from Stream 3 deliverable #1 (ultrathinks research) — may surface additional patterns to port. If Stream 3 hasn't returned, proceed without it and add later.
- Item 5 (QMD reindex note) depends on Stream 2's QMD syntax fix.

## Verification criteria

1. `/tp` SKILL.md or protocol.md has the disconfirmation-search paragraph
2. Red-team has either a new simplification specialist or extended logic specialist with simplification lens
3. Same for test quality lens
4. Red-team findings schema includes `contradicts` field
5. SCHEMA.md §11 quarterly note mentions `qmd update` (correct syntax)
6. `~/.grok/skills/grok-safe-git/SKILL.md` has multi-session commit safety rule (no `git add -A`; per-file scoping)
7. `P:/.data/wiki/concepts/multi-terminal-git-coordination-primitives.md` has Primitive 4 (verify already landed)
8. `/go` SKILL.md Step 6 has execution-status block instruction
9. `wiki_after_write.py` uses `out.find("[")` instead of `out.startswith("[")`; same fix in `wiki_contradiction_scan.py`
10. Plugin cache rebuilt for any red-team or cc-skills-sdlc plugin changes

## Source references

- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — /tp skill to edit
- `P:/packages/.claude-marketplace/plugins/red-team/agents/` — specialist agent prompts
- `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` — findings schema
- `P:/.data/wiki/SCHEMA.md` §7 (typed wikilinks) and §11 (cadence)
- `https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents` — HAMY's 9-agent review pattern (source for lenses #2 and #3)
- Stream 3 handoff: `P:/docs/stream-3-research-infrastructure-handoff-2026-07-19.md` — ultrathinks research that may inform additional enhancements
- Augment Code parallel agent guide: `https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution` — primary source for deliverable #7
- James Phoenix "3x Throughput": `https://understandingdata.com/posts/git-worktrees-parallel-dev/` — secondary source for #7
- `obra/superpowers` issue #597: `https://github.com/obra/superpowers/issues/597` — worktree-aware environment isolation
- `augmentcode/auggie` repo: `https://github.com/augmentcode/auggie` — worktree creation script with port assignment
- `jayminwest/overstory` repo: `https://github.com/jayminwest/overstory` — FIFO merge queue for agent fleets
- Existing wiki: `auto-stage-commit-strategies.md` — confirms no diff-only-commit primitive exists; Stop hook wins for auto-commit

---

## Execution Status

Updated: 2026-07-19T19:55:00Z
Session: console_12092a49-e448-4be3-b146-79309cfba3d2
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | Disconfirmation search in /tp | ✅ DONE | `~/.grok/skills/tp/SKILL.md` L94-108 (new section "Post-correction disconfirmation step (conditional)") — 14 lines added after `/tp <mode>` section, before "Reference" |
| 2 | Simplification specialist | ✅ DONE | `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-simplification.md` (NEW, 4,565 B) — HAMY Agent 9 pattern, premature-abstraction/over-configured/framework-for-one/cleverness/atomicity |
| 3 | Test Quality specialist | ✅ DONE | `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-test-quality.md` (NEW, 5,394 B) — HAMY Agent 6 pattern, distinct from existing `red-team-testing.md` (existence gaps vs quality ROI) |
| 4 | @contradicts in findings schema | ⚠️ PARTIAL | Critic updated: `red-team-critic.md` Step 3 now has "Explicit `contradicts` field (machine-readable conflict resolution)" section. **DEFERRED:** the formal schema in `commands/red-team.md` L120-142 and the codified schema in `__lib/findings_schema.py` were dirty (`M`) from Stream 1 red-team reliability work — deferred to avoid cross-stream conflict. |
| 5 | QMD quarterly reindex note | ✅ DONE | `P:/.data/wiki/SCHEMA.md` L461 — extended the existing quarterly bullet with `qmd update` (correct syntax) call |
| 6 | Per-file commit scoping in grok-safe-git | ✅ DONE | `~/.grok/skills/grok-safe-git/SKILL.md` — new "Step 4.5 — Multi-session commit safety (per-file scoping)" section with examples + cross-reference to `multi-terminal-git-coordination-primitives.md` Primitive 4 |
| 7 | multi-terminal-git-coordination-primitives.md Primitive 4 | ✅ ALREADY DONE (skipped) | Wiki page verified at L134 ("Primitive 4: Per-file commit scoping"), L38 (table row), L141 (rule), L214-215 (ecosystem sources: augmentcode, overstory, hiragram, block, Dagger, obra/superpowers #597). Parent session's `/wiki` ingest landed all required content. |
| 8 | Execution-status block in /go Step 6 | ✅ DONE | `~/.grok/skills/go/SKILL.md` — new "Execution status block (when input was a file path)" subsection between "Recommended next" and "Step 6.5" |
| 9 | Fix wiki_after_write.py Loguru stdout bug | ✅ DONE | `wiki_after_write.py` L92 and `wiki_contradiction_scan.py` L150 — both `out.startswith("[")` → `idx = out.find("[") if out else -1; if idx < 0: ...; json.loads(out[idx:])`. Syntax-checked (parses cleanly). Plugin bumped 1.0.236 → 1.0.237, cache rebuilt. |

**Plugin version bumps + cache rebuilds:**
- red-team: 0.2.26 → 0.2.28 (script auto-bumped; my new specialist files + critic edit are in cache at `C:\Users\brsth\.claude\plugins\cache\local\red-team\0.2.28`)
- cc-skills-sdlc: 1.0.236 → 1.0.237 (cache rebuilt; both Python fixes verified at cache paths)

### Key findings during execution

- **Subagent fan-out failed mid-session** with MiniMax API quota exhaustion (`Token Plan usage limit reached`, status 429 code 2056). 4 parallel subagents were spawned; all 4 hit the quota wall on first LLM call. Pivoted to **serial parent execution** for all 9 deliverables. Parent session retained capacity throughout — the quota gate appears to apply to subagent session spawning specifically, not parent API calls.
- **Stream 3 ultrathinks research read before implementation** (per user instruction). 3 BUILD recommendations (Hierarchical Rule Inheritance / Auto Memory / Hypothesis Ledger) were noted but are correctly **out of scope** for Stream 4 — they're each multi-day builds, not the ~hour of text edits Stream 4 calls for. Deliverable #1 (disconfirmation search) was kept tightly scoped to the 14-line /tp addition, not inflated into a Hypothesis-Ledger-style build.
- **#7 was verified done before implementing** (per user instruction). The wiki page had Primitive 4 + all ecosystem tool sources. Skipped cleanly — no duplicate work.
- **Concurrency hazard on red-team plugin:** all 10 existing specialist files were `MM` (staged + unstaged modified from Stream 1 red-team reliability work) at session start. Created NEW specialist files (#2, #3) rather than extending existing ones to avoid clobbering another stream's work. For #4, the critic (`red-team-critic.md`) was clean so it was edited; the schema doc + `__lib/findings_schema.py` were dirty and deferred.
- **cc-skills-sdlc is a git submodule**, not a regular directory. Submodule-internal `git status` was clean for both target .py files (the superproject-level `Mm` was submodule-pointer drift, not in-submodule modifications). Edits to the .py files were safe and landed cleanly; `plugin-audit-and-fix.py --bump cc-skills-sdlc` handled the cache rebuild without issue.
- **Auto-version-bump behavior:** `plugin-audit-and-fix.py --bump <name>` auto-increments the patch version from whatever it detects as current. For red-team, my manual pre-bump to 0.2.27 was further bumped to 0.2.28 by the script. For future runs: let the script do the bump; don't pre-bump manually.
- **No commits made.** All work is in working tree (or user-home for ~/.grok edits). User decides commit timing.

### Deferred items (require parent decision or cross-stream coordination)

1. **#4 schema formalization** — `commands/red-team.md` §"Findings schema" L120-142 needs `"contradicts": "<FINDING-ID>"` added as an optional field. `__lib/findings_schema.py` needs the field codified. Both files are dirty from Stream 1's red-team reliability work; coordinate with that stream before editing, or wait for it to complete.
2. **Cross-stream commit hygiene** — multiple streams have unstaged work in the same tree (929 dirty files at session start, including 13 staged). Per the new grok-safe-git Step 4.5 (deliverable #6), commits should use per-file scoping. The new red-team specialists + cc-skills-sdlc submodule changes will need careful per-file staging when commit time comes.
3. **Plugin reload** — both red-team (0.2.28) and cc-skills-sdlc (1.0.237) cached versions require `/reload-plugins` or a session restart to activate. Until then, the new specialists and the Python fix exist in cache but aren't loaded by the running session.

### Verification status

Per /go Step 6 final-report format:
- **profile**: parallel-change (intended) → serial parent execution (actual, due to subagent quota failure)
- **horsepower**: H0-safety ✅, H1-think ✅ (read Stream 3 research, scoped #1 correctly), H3-discover ✅ (verified #5/#7/#9 current state before implementing), H4-parallel ❌ (subagent quota blocked; would have fanned out to 4 SAs), H6-verify ✅ (syntax-checked Python, verified cache contents, read back every edit)
- **verify**: PASS on all 8 implemented deliverables; DEFERRED on the #4 schema-formalization half (cleanly documented)
- **goal**: n/a (single wave)

**Recommended next:** `/check` on the 9 deliverables — verify each edit landed and the plugin cache is consistent. Specifically: `/check ~/.grok/skills/tp/SKILL.md ~/.grok/skills/grok-safe-git/SKILL.md ~/.grok/skills/go/SKILL.md P:/.data/wiki/SCHEMA.md` for the text edits, and `/check red-team@0.2.28 cc-skills-sdlc@1.0.237` for the plugin changes.
