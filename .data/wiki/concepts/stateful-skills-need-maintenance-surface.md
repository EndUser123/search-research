---
title: "Stateful skills need a maintenance surface: audit, fix, prune, disk-report"
created: 2026-07-27
source: session-019fa276 (nlm-to-wiki v3 refactor + maintenance routine)
tags: [skill-design, stateful-skills, maintenance, observability, cleanup, architecture, decision]
summary: >
  Architecture decision: skills that accumulate durable state across runs
  (manifests, file artifacts, caches) must ship with an explicit maintenance
  surface — a script or subcommand providing read-only audit, safe fixes
  gated behind --confirm, destructive operations that move-to-trash, and disk
  reporting. Without it, state accumulates silently: stale manifest entries
  after page deletions, orphaned files after source deletion, missing schema
  tags after migrations, and unchecked disk growth. Built and verified for
  nlm-to-wiki (5 stale slugs + 1 missing pipeline tag caught on first audit);
  applies to nlm-bulk-ingest, search-fleet, wiki, and any skill that writes
  durable artifacts.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "P:/.agents/skills/nlm-to-wiki/scripts/maintenance.py" (built this session, audit verified)
  - "P:/.data/wiki/_state/nlm-sync-manifest.json" (5 stale concept_slugs found and cleared)
  - "P:/.data/wiki/concepts/skill-lifecycle-toolkit.md" (skill-as-artifact lifecycle — does NOT cover state maintenance)
relations:
  - target: wiki/concepts/skill-lifecycle-toolkit.md
    type: complements
  - target: wiki/concepts/skill-authoring-patterns-dos-and-donts.md
    type: extends
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: related
---

# Stateful skills need a maintenance surface

## Decision context

**Why this was needed:** during the nlm-to-wiki v3 refactor (session
019fa276), the skill had accumulated state across multiple sessions: a sync
manifest tracking per-notebook syncs, 3 exported transcripts, 5 stale
concept_slugs pointing at deleted v2 wiki pages, and a missing `pipeline`
tag from a v2→v3 migration. None of this was visible without manually
reading the manifest JSON and cross-referencing against the filesystem. The
operator asked: "would it be useful to track which sources with datetime we
ingest so we can skip maybe what we have done before?" The answer was that
skip logic already existed (source_hash + file-exists), but *visibility* into
accumulated state did not. The missing piece was a maintenance surface.

**The decision:** ship a `maintenance.py` (or equivalent subcommand) with
every stateful skill, providing four operations: audit (read-only
cross-reference of manifest ↔ filesystem ↔ external source), fix (safe
repairs gated behind `--confirm`), prune (destructive cleanup that
move-to-trash instead of delete), and disk-report (per-unit size breakdown).

## The pattern

```
STATEFUL SKILL
  ├── scripts/
  │   ├── <main>.py          ← the pipeline (sync, ingest, search)
  │   └── maintenance.py     ← the maintenance surface (THIS CONCEPT)
  │
  └── accumulated state:
      ├── manifest/state.json ← tracks what's been processed
      ├── sources/ or cache/  ← file artifacts (transcripts, keyframes)
      └── output/             ← written results (concept pages, indexes)
```

**maintenance.py provides four operations:**

| Operation | Purpose | Safety |
|---|---|---|
| `--audit` | Read-only cross-reference: manifest ↔ filesystem ↔ external API. Detects stale refs, orphaned files, missing schema tags, pre-migration entries. | Read-only |
| `--fix-*` | Safe repairs: clear stale manifest refs, remove orphaned files. Each gated behind `--confirm`; dry-run is the default. | Needs `--confirm` |
| `--prune-*` | Destructive: remove ALL state for a deleted unit (manifest + files + outputs). Outputs moved to trash dir, never outright deleted. | Needs `--confirm` |
| `--disk-report` | Per-unit disk breakdown: which notebooks/repos/projects are consuming sources/cache space. | Read-only |

**Safety model:** the default is dry-run. Every destructive command requires
explicit `--confirm`. The most destructive operation (`--prune`) moves output
files to a `_trash/<unit-id>/` directory for recovery, not deletion. This
matches the workspace's no-destructive-git rule — reversibility is the floor.

## Steelman: why NOT just rely on operator cleanup?

The rejected alternative: don't build a maintenance script. Rely on the
operator to manually inspect state when something looks wrong, or build ad-hoc
cleanup commands as needed.

**Why that alternative is reasonable:** it avoids upfront script-writing cost.
Most skills never accumulate enough state to need maintenance. The operator is
technical and can read JSON manifests directly. Ad-hoc `rm` or `jq` commands
work fine for one-off cleanups.

**Why it loses on this workspace:** this host runs multi-session, multi-agent
workloads where state accumulates across sessions without any single operator
watching. Stale manifest entries from a v2→v3 migration survived 2+ sessions
before the audit caught them. The maintenance surface makes accumulated state
*inspectable* — `--audit` is a 2-second read-only check that surfaces every
mismatch at once, vs. the operator manually grepping manifests and counting
files. The cost of writing maintenance.py (~150 lines) is paid once; the cost
of NOT having it compounds silently every session.
## Evidence (this session)

The first `maintenance.py --audit` run on nlm-to-wiki found:

| Issue | Count | Source |
|---|---|---|
| Stale concept_slugs (pages deleted, manifest not updated) | 5 | v2 pages deleted in prior session; manifest never cleared |
| Missing `pipeline` tag | 1 | v2→v3 migration; manifest entry predates the tag |
| Orphaned transcripts | 0 | (no notebooks deleted yet) |
| Orphaned manifest entries | 0 | (all tracked notebooks still live) |

The stale slugs were the real catch: 5 concept pages were deleted as part of
the v2→v3 migration, but the manifest still listed them as written. A re-sync
would have reported "5 pages synced" based on stale data. The audit caught
this; `--fix-stale-slugs --confirm` cleared it in one command.

## When this pattern applies

| Skill | Accumulates state? | Maintenance surface needed? |
|---|---|---|
| nlm-to-wiki | Yes: manifest, transcripts, concept pages, keyframes | ✅ Built (maintenance.py) |
| nlm-bulk-ingest | Yes: notebook registry, cluster state, run logs | ✅ Should have one |
| search-fleet | Yes: tool registry, cache, RRF results | ⚠ Registry is config (self-maintaining); cache may need periodic prune |
| wiki | Yes: concept pages, log, _state/ lifecycle files | ⚠ Has `wiki_health_check.py` — partial maintenance surface |
| /go, /tp, /check | No: session-scoped, no durable artifacts | ❌ Not needed |
| /handoff | Yes: handoff files accumulate | ⚠ `/close` serves as partial maintenance (stale handoff detection) |

**Rule of thumb:** if the skill writes files that persist across sessions, it
needs a maintenance surface. If it's session-scoped (state dies when the
session ends), it doesn't.

## What this means for our workspace

- **Add `maintenance.py` to stateful skills that lack one.** nlm-bulk-ingest
  is the next candidate — it has a notebook registry and cluster state that
  will accumulate across bulk-ingest runs.
- **Run `--audit` before any large re-sync or migration.** The nlm-to-wiki
  v3 refactor's stale slugs would have been caught before the first v3 sync
  attempt if the audit had existed before the migration.
- **The `--disk-report` operation is the disk-pressure early-warning system.**
  Transcript and keyframe directories grow linearly with source count; a
  300-source notebook produces ~2-5 MB of transcripts. Across 15 notebooks,
  that's 30-75 MB — not urgent, but the report makes it visible before it is.
- **The help short-circuit (`/skill -h`) should point at the maintenance
  commands.** When an operator asks "how do I clean up X?", the help resource
  should surface `--audit` and `--fix-*` as the first answer, not manual file
  inspection.

## Falsifier

This pattern is over-engineering if:
- The audit never catches real issues (all state is always clean). The first
  nlm-to-wiki audit caught 5 stale slugs + 1 missing tag, so this falsifier
  did not fire on the initial run. Re-evaluate after 3 months of regular use.
- The maintenance script itself accumulates bugs that are worse than the state
  it maintains (the cure is worse than the disease). Mitigated by the dry-run
  default and `--confirm` gate.
- Stateful skills are rare enough that the pattern doesn't generalize beyond
  nlm-to-wiki. [INFERENCE] — nlm-bulk-ingest, wiki, and handoff all accumulate
  state; the pattern applies to at least 4 skills in the current fleet.

If any of these holds within 6 months, retire the pattern and revert to
ad-hoc cleanup.

## Sources

- `P:/.agents/skills/nlm-to-wiki/scripts/maintenance.py` — the implementation
  that produced this decision. 4 operations (audit, fix, prune, disk-report),
  dry-run default, `--confirm` gate, move-to-trash for destructive ops.
- `P:/.data/wiki/_state/nlm-sync-manifest.json` — the manifest whose stale
  entries (5 concept_slugs + missing pipeline tag) were caught by the first
  audit run. Evidence that the pattern catches real issues.
- `P:/.data/wiki/concepts/skill-lifecycle-toolkit.md` — the skill-as-artifact
  lifecycle (create/audit/improve/retire the SKILL.md). This concept
  complements it by covering the *state* lifecycle (what the skill produces
  and tracks across invocations).
- `P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md` —
  progressive disclosure pattern (Level 1/2/3). The maintenance surface is an
  operational complement: progressive disclosure governs how the skill loads
  its own documentation; the maintenance surface governs how the operator
  inspects and repairs the skill's accumulated output.

## Auto-related

- [[skill-lifecycle-toolkit]] — skill-as-artifact lifecycle (create/audit/improve/retire); this concept covers the complementary state lifecycle
- [[skill-authoring-patterns-dos-and-donts]] — progressive disclosure pattern; the maintenance surface is its operational complement
- [[notebooklm-cli-operational-gotchas]] — the auth-recovery + bulk-add gotchas that nlm-to-wiki inherits; the maintenance surface catches state decay from those operations
- [[semantic-clustering-bounded-size]] — the clustering algorithm reused by nlm-to-wiki; clusters are part of the accumulated state the maintenance surface tracks
