---
title: "Pipeline defect fixes from /tp analysis + spec drift scanner finding"
session_id: 019ff1a0-26ab-7003-8192-7e653852f6bf
created_at: 2026-08-12T12:35:00Z
status: OPEN
assignee: unassigned
current_session_id: 019ff1a0-26ab-7003-8192-7e653852f6bf
produced_at: 2026-08-12T12:35:00Z
accurate_as_of_head:
  P:/: 116d86c
  ~/.grok: 4c8c3d8
source_transcript: ~/.grok/sessions/P%3A%5C/019ff1a0-26ab-7003-8192-7e653852f6bf/
---

# Pipeline defect fixes from /tp analysis

## Goal

Fix the three confirmed defects identified by `/tp what improvements should we make?`
and the `/todo` execution batch. All three are now fixed, committed (`6b73818`),
and verified via test suites. One open finding remains: the spec drift scanner
itself produces false positives.

## Status

Three defects FIXED. One scanner defect OPEN. Two wiki concepts written.

## What now works

Three pipeline defects fixed in commit `6b73818`:

1. **close-py resolve→verdict state propagation** — resolve phase now documents
   the JSON schema in the pause-phase instruction AND accepts multiple resolution
   shapes (`resolutions`, `resolved_gates`, `gates` dict). The propagation loop
   was already present (commit `71282b6`) but silently no-op'd when the LLM wrote
   a different schema shape. Close-py tests 26/26 pass.

2. **ship-py cross-validate empty-findings gate** — added DEC-09c skip: when
   review found 0 bugs and 0 risks, skip the validator model call entirely.
   Prevents false blocks when the validator is unavailable but review was clean.
   Cross-validate tests 27/27 pass.

3. **AAR unused_capability detector** — added `_DIR_LISTING_TOOLS` filter +
   `tool_call_id → tool_name` map. Directory-listing results (`list_dir`,
   `Get-ChildItem`, `glob`, `find`) are skipped before scanning. AAR tests 16/16
   pass.

## Open work

### O1 — Spec drift scanner false positives (OPEN, INVESTIGATE)

The `/todo` fleet_health scanner reported 22 SKILL.md files referencing scripts
"not found." Manual investigation confirmed these are **scanner false positives**:

- `execute-plan/SKILL.md` line 233 references the IMPLEMENT skill's `memory.py`
  (cross-skill reference, not its own)
- Plugin skills resolve paths relative to their plugin root, not the SKILL.md
  directory, but the scanner checks relative to SKILL.md only

**Scope:** the scanner needs to understand cross-skill references and plugin
path resolution. This affects the reliability of the `/todo` NOW section (22
false positives pollute the high-severity signal landscape).

**Investigation path:**
- Scanner source: `~/.grok/skills/todo/__lib/scan_functions.py` (fleet_health source)
- The script-existence check matches `.py`/`.sh`/`.js` filenames in SKILL.md
  text without distinguishing local references from cross-skill references
- Fix options: (a) resolve paths relative to the skill's actual script directory,
  (b) ignore script references inside prose/code blocks that mention other skills,
  (c) add a "cross-skill reference" pattern exclusion

**Why not fixed this session:** the fix needs design (which paths to resolve
where for plugin skills vs workspace skills vs bundled skills). Not a one-liner.

### O2 — Shared-directory `--out` audit (OPEN, INVESTIGATE, carried from prior handoff)

See `P:/docs/handoffs/aar-followups-019ff1a0/HANDOFF.md` O1. Still not scanned.

## Decisions captured

1. **Pipeline pause-phase schema contract** — pause-phase instructions must
   document the JSON schema inline. Wiki: `[[pipeline-pause-phase-schema-contract]]`
2. **AAR detector tool filtering** — any detector pattern-matching against
   tool_result text must filter by producing tool_name. Wiki: `[[aar-detector-false-positives-directory-listing-tool-results]]`

## Evidence

| Claim | Receipt |
|-------|---------|
| close-py resolve propagation fix | `~/.grok/skills/close-py/__lib/phases/resolve.py` lines 60-93, 115-125 |
| ship-py cross-validate skip | `~/.grok/skills/ship-py/__lib/phases/cross_validate.py` lines 65-84 |
| AAR detector filter | `~/.grok/skills/aar/__lib/detectors.py` lines 1185-1215 |
| All three fixed in one commit | `6b73818` (2026-08-12) |
| close-py tests pass | 26/26 (`pytest tests/ -x -q`) |
| ship-py cross-validate tests pass | 27/27 (`pytest tests/ -q -k "cross"`) |
| AAR tests pass | 16/16 (`pytest tests/test_opportunity_detectors.py`) |
| Spec drift false positive confirmed | `execute-plan/SKILL.md` line 233 references implement's `memory.py` |
| Pre-existing provenance test failures | ship-py has 5 pre-existing failures in `test_provenance.py` unrelated to this session's changes (design_check missing from test's dispatch_log) |

## Falsifier

The three fixes would be wrong if:
- close-py: the LLM always wrote the exact schema the code expected (fix unnecessary)
- ship-py: there exist legitimate cases where cross-validation should run even with 0 findings (there aren't — nothing to validate)
- AAR: directory listings sometimes contain genuine capability discoveries (possible but the 55-76% false-positive rate justifies the filter)

## Read-first list

1. `~/.grok/skills/close-py/__lib/phases/resolve.py` — the propagation fix
2. `~/.grok/skills/ship-py/__lib/phases/cross_validate.py` — the empty-findings skip
3. `~/.grok/skills/aar/__lib/detectors.py` — the directory-listing filter (function `detect_unused_capability`, line 1173)
4. `P:/.data/wiki/concepts/pipeline-pause-phase-schema-contract.md` — the schema contract pattern
5. `P:/.data/wiki/concepts/aar-detector-false-positives-directory-listing-tool-results.md` — the false-positive pattern

## Related wiki concepts

- [[pipeline-pause-phase-schema-contract]] — the inter-phase schema contract pattern
- [[aar-detector-false-positives-directory-listing-tool-results]] — the detector false-positive pattern
- [[ship-py-session-scoped-state-multi-terminal-isolation]] — ship-py state architecture
- [[close-runner-verdict-staleness-across-phases]] — related phase-staleness pattern

## Suggested skills for resumption

- `/skill-dev measure todo` — verify the spec drift scanner defect, design a fix for cross-skill path resolution
- `/review close-py` — fresh-eyes review of the resolve→verdict phase chain (deferred from HYGIENE-6; manual review done this session, full /review deferred)

## Last user message (verbatim)

```
/handoff
```
