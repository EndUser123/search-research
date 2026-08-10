---
thread_id: 019fe7e9-cd04-7a63-9436-1b446826024a
parent_handoff_path: none
current_session_id: 019fe7e9-cd04-7a63-9436-1b446826024a
current_terminal_id: grok-build-019fe7e9
produced_at: 2026-08-09T23:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Fleet hygiene backlog: scanner path coverage, maintain defects, config.toml, deferred wikilinks

## Objective

Clear the fleet hygiene backlog surfaced by the `/todo` scan and `/skill-dev measure` runs in session 019fe7e9. Four independent items, none blocking each other — can be worked in parallel or across sessions.

## Status

OPEN — measured and triaged in session 019fe7e9; none implemented.

## Producing context

2026-08-09, session `019fe7e9`. The `/todo` scan (141 items) surfaced 52 spec-drift findings + 6 broken skill dependencies + config.toml size. Investigation revealed most spec-drift and dependency findings were **scanner false positives** (checking only one path). The real items are: maintain skill's blocking defects, the scanner path bug itself, config.toml size, and 19 deferred broken wikilinks.

## Read-first list

1. `C:/Users/brsth/.grok/skills/maintain/__lib/fleet_health.py` — has 4 blocking defects. Run `script_scan.py` for current findings.
2. `C:/Users/brsth/.grok/skills/todo/__lib/scan_functions.py` — the scanner that has the path-coverage bug (checks only `~/.grok/skills/`).
3. `C:/Users/brsth/.grok/config.toml` — 45KB, 1323 lines, 30+ sections.
4. `P:/.data/wiki/concepts/` — 19 deferred broken wikilinks from the batch fix (commit `22470f4`).

## Verified facts

- [FACT] The fleet-health scanner (`scan_functions.py` / `fleet_health.py`) checks only `~/.grok/skills/` for skill existence. It misses `P:/.grok/skills/` (where `check` lives), `P:/.agents/skills/` (where `skill-prune`, `preflight`, `recover` live), and `~/.grok/installed-plugins/` (where `test-driven-development`, `using-git-worktrees` live). This produces ~50 false-positive spec-drift findings + 5 false-positive broken-dependency findings per scan.
- [FACT] `maintain/__lib/fleet_health.py` has 4 blocking defects per `script_scan.py`: SILENT-NO-OP at line 984 (returns `[]` silently when external resource unavailable), UNGUARDED-FILE-NOT-FOUND at lines 672, 758, 794 (silently skips checks when files are renamed/deleted). These mean fleet health checks can silently pass when they should fail.
- [FACT] `maintain/SKILL.md` references `P:/tmp/purge_artifacts.py` at lines 198, 223 but the script doesn't exist. Step 2c instructs the operator to use it but no creation step is provided.
- [FACT] config.toml is 45,738 bytes, 1,323 lines, with 30+ top-level `[section]` blocks including 12+ MCP server configs, model configs, permission rules, plugin/skill lists.
- [FACT] 19 broken wikilinks remain after the batch fix (commit `22470f4` fixed 1970/1989). These are single-instance references with no clean fuzzy match — need manual review.
- [FACT] The `close` skill is shippable — 0 blocking defects, 1 advisory cross-skill-dep (intentional). Only gap: missing `version:` frontmatter field.

## Current state

**Done (this session):**
- Triaged all 4 items — know what needs fixing and why
- Fixed the one truly-wrong depends_on (`agy → debrief`, commit `34efa56`)
- Ran `/skill-dev measure` on close + maintain (receipts in the session transcript)
- Batch-fixed 1970 wikilinks (item 4 is the residual 19)

**Not done (this handoff):**
- FLEET-01: scanner path coverage fix
- FLEET-02: maintain skill 4 blocking defects
- FLEET-03: config.toml refactor
- FLEET-04: 19 deferred wikilinks

## Task packets

### FLEET-01: Scanner path coverage fix
- **goal:** Extend the fleet-health scanner to check all 4 skill paths before declaring a skill "missing"
- **in scope:** `scan_functions.py` and/or `fleet_health.py` — wherever skill-existence checks run. Add path fallbacks: `~/.grok/skills/`, `P:/.grok/skills/`, `P:/.agents/skills/`, `~/.grok/installed-plugins/`
- **out of scope:** the skills being referenced (they exist — this is a scanner bug, not a skill bug)
- **files:** `C:/Users/brsth/.grok/skills/todo/__lib/scan_functions.py`; possibly `C:/Users/brsth/.grok/skills/maintain/__lib/fleet_health.py`
- **acceptance:** re-run `/todo` scan — false-positive count drops from ~50 to <5; the 6 "broken dependencies" drop to 0 (agy already fixed) or 1 (chrome-devtools-mcp is a plugin, not a skill — may need declaration change instead)
- **falsifier:** legitimate missing skills get masked by the broader path search (unlikely — if a skill is truly missing, it won't be at any path)
- **verification level:** RUNTIME

### FLEET-02: Fix maintain skill blocking defects
- **goal:** Fix the 4 blocking defects in `fleet_health.py` that cause silent false-passes
- **in scope:** `maintain/__lib/fleet_health.py` lines 672, 758, 794 (UNGUARDED-FILE-NOT-FOUND → add rename resolution or explicit warning), line 984 (SILENT-NO-OP → warn instead of returning `[]`); create `P:/tmp/purge_artifacts.py` or change SKILL.md to not reference a non-existent script
- **out of scope:** the 5 advisory false-positive BROKEN-PATH findings (regex patterns in string literals — not real defects); the CRAFT-NO-TRIGGERS finding (description trigger phrases — low priority)
- **files:** `C:/Users/brsth/.grok/skills/maintain/__lib/fleet_health.py`; `C:/Users/brsth/.grok/skills/maintain/SKILL.md` (if purge_artifacts.py reference needs updating)
- **acceptance:** `script_scan.py` on maintain reports 0 blocking defects; re-run `/maintain` and verify it doesn't silently skip checks on renamed files
- **falsifier:** the fixes introduce new false positives or break existing check behavior
- **verification level:** RUNTIME

### FLEET-03: config.toml refactor
- **goal:** Split config.toml into manageable sections or includes — 45KB / 1323 lines exceeds the 500-line threshold
- **in scope:** config.toml structure — evaluate whether Grok Build supports config includes/imports; if yes, split into `config-mcp.toml`, `config-models.toml`, `config-permissions.toml` etc.; if no, at minimum add section comments and remove dead/redundant entries
- **out of scope:** changing actual config values (this is structural, not behavioral)
- **files:** `C:/Users/brsth/.grok/config.toml`
- **acceptance:** config.toml is under 500 lines OR split into includes that are each under 500 lines; Grok Build still starts cleanly with the restructured config; no config values lost
- **falsifier:** Grok Build doesn't support config includes and the file can't be meaningfully shortened without losing function
- **verification level:** RUNTIME
- **note:** this is the highest-effort item — verify Grok Build's config format supports includes before attempting the split

### FLEET-04: 19 deferred broken wikilinks
- **goal:** Manually review and fix the 19 remaining broken wikilinks from the batch fix
- **in scope:** the 19 specific `[[target]]` references listed in the wiki-lint subagent output (commit `22470f4`). Each is a single-instance reference with no clean fuzzy match.
- **out of scope:** the 1970 already-fixed links
- **files:** the 19 source concept files containing the broken links (listed in the subagent report)
- **acceptance:** `wiki_health_check.py` reports 0 broken wikilinks (excluding SCHEMA template placeholders)
- **falsifier:** a broken link is actually a legitimate reference to a concept that should be written (not just converted to plain text)
- **verification level:** STATIC_INSPECTION

## Open decisions

- **FLEET-03 (config.toml):** does Grok Build support config includes/imports? If not, the refactor is just "remove dead entries + add comments" which won't get under 500 lines. **Status: unresolved — check `~/.grok/docs/user-guide/05-configuration.md` first.**

## Hard constraints

- Scanner changes must not mask legitimate missing skills (FLEET-01)
- maintain fixes must not change existing check semantics, only failure-mode behavior (FLEET-02)
- config.toml changes must preserve all functional config values (FLEET-03)
- Wiki fixes must not delete concepts (FLEET-04)

## Cross-reference couplings

- FLEET-01 and FLEET-02 both touch fleet health scanning — work them in the same session if possible
- FLEET-04 depends on the batch-fix commit `22470f4` being the baseline
- The `structural-error-prevention-deterministic-gates-20260809` handoff's ERR-PREVENT-01 (gate-log audit) is independent but related — both are "audit existing infrastructure" tasks

## Explicit non-goals

- Fixing the 52 spec-drift findings individually — they're false positives until FLEET-01 is fixed
- Adding `version:` to the close skill — it's shippable without it (minor craft gap)
- Touching other sessions' uncommitted work (wiki-yt, review-relay — owned by `review-relay-improvements-impl-20260809`)

## Resumption protocol

1. Read this handoff + the read-first files
2. FLEET-01 and FLEET-02 are highest-ROI (they eliminate ~50 false positives per `/todo` scan + make `/maintain` reliable)
3. FLEET-03 requires checking Grok Build config format support first — verify before investing
4. FLEET-04 is lowest-priority mechanical work — can be batched with any other wiki session

## Suggested next invocation

`/handoff claim P:/docs/handoffs/fleet-hygiene-backlog-20260809` then start with FLEET-01 (scanner path coverage).

## Last user message (verbatim)

> /handoff

## Epistemic labels

- Scanner path-coverage bug is `[FACT]` — verified by checking all 4 paths with `Test-Path` this session
- maintain skill blocking defects are `[FACT]` — measured by `script_scan.py` via the skill-dev subagent (36 tool calls, 150s)
- config.toml size is `[FACT]` — `Get-Item` + `Select-String` on section headers
- 19 deferred wikilinks are `[FACT]` — from the wiki-lint subagent output (commit `22470f4`)
- The config.toml refactor being "highest-effort" is `[INFERENCE]` — based on the file size and shared-config risk, not measured
