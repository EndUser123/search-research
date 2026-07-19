# Canonical `/research` extraction — 2026-07-14

Verdict: `PASS_RESEARCH_EXTRACTED_NEEDS_USAGE`

## Workspace and source authority

- Repository: `P:/packages/.claude-marketplace/plugins/search-research`
- Branch: `main`
- Plugin HEAD before edit: `03f8b6dfd58f20f687aad1dc9af4ab4cd9be1b84`
- Workspace HEAD: `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`
- The plugin was clean before this extraction; the parent workspace was already
  heavily dirty with unrelated work.
- Active plugin worktree: `P:/.claude/worktrees/chs-chain-export`.
- Canonical Python: `C:\Python314\python.exe` for tests; plugin runtime uses
  the plugin `.venv` Python.
- Canonical research test command:
  `C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider`
- Pre-edit narrow source audit:
  `P:\tmp\source-discovery-research-narrow-pre.json`
- Post-edit source audit:
  `P:\tmp\source-discovery-research-canonical-post.json`
- Final source audit after compatibility-symbol repair:
  `P:\tmp\source-discovery-research-canonical-final.json`

The post-edit audit reported two `orchestration.py` candidates. Manual source
inspection resolves this intentional overlap: `skills/research/orchestration.py`
contains the implementation; `skills/all/orchestration.py` is a delegation
wrapper and contains no Phase 1/provider/artifact logic. No duplicate execution
implementation remains.

## Runtime ownership

Before:

```text
/all -> skills.all.orchestration -> skills.all.search_executor
     -> tools.research_run_v1.phase1.run_phase1
```

After:

```text
/research -> skills.research.orchestration -> skills.research.search_executor
          -> tools.research_run_v1.phase1.run_phase1

/all -> skills.all.orchestration compatibility wrapper
     -> skills.research.orchestration
     -> the same research executor and Phase 1 engine
```

The implementation modules moved to `skills/research`. The old `skills/all`
modules now re-export or delegate to the canonical modules. The caller is
explicitly carried into Phase 1 so artifact identity and telemetry distinguish
canonical research from compatibility invocation:

- `/research`: `search-research:/research`
- `/all`: `search-research:/all`

## Research contract

The existing artifact remains the source of truth and now serves the future
research boundary:

```text
research question
evidence requirements / quality plan
selected capabilities and executed lanes
opened source identities and provenance
assessments and claims
uncertainty / unresolved evidence
stop reason and authorization boundary
```

No `/design` behavior was added. Authority rules, claim handling, immutable
artifacts, evidence assessment, and completion gates were preserved.

## Live validation

Live matrix artifact:

[research-canonicalization-live-20260714.json](P:/tmp/research-canonicalization-live-20260714.json)

| Case | Entrypoint | Caller | Observed lanes | Result |
|---|---|---|---|---|
| local-only | `/research` | `search-research:/research` | QMD | success |
| conceptual | `/research` | `search-research:/research` | MMX | success |
| implementation | `/research` | `search-research:/research` | Brave | success |
| mixed | `/research` | `search-research:/research` | Brave + MMX + QMD | all success |
| compatibility | `/all -> /research` | `search-research:/all` | Brave | success |

Direct same-question local comparison:

[research-compatibility-comparison-20260714.json](P:/tmp/research-compatibility-comparison-20260714.json)

The direct `/research` and compatibility `/all` artifacts had equivalent
question, lane, source, claim, assessment, and quality payloads. The only
intentional difference was caller identity; `equivalent_payload: true`.

The live run produced these representative immutable artifacts:

- `/research` local:
  `P:\tmp\.codex\state\research-run-v1\3000848d-a60a-4cb2-b607-badeecd3fe2b\research-run.json`
- `/research` mixed:
  `P:\tmp\.codex\state\research-run-v1\907590b9-4082-4e20-92e2-608cda2eb6ad\research-run.json`
- `/all` compatibility:
  `P:\tmp\.codex\state\research-run-v1\85c1b999-ff6e-44bb-97b2-0e70ce590c19\research-run.json`

## Tests and limitations

- Canonicalization regression tests: `3 passed`.
- The full research suite after extraction: `75 passed, 3 failed`; the three
  failures are the previously independently attributed router-policy/corpus
  failures, not extraction failures.
- The plugin's legacy `skills/all/tests` run reached 17 passing tests before
  timing out in existing background/indexing threads; this is recorded as a
  plugin-test harness limitation, not silently counted as a pass.
- Claude installed the updated local plugin from `0.1.113` to `0.1.115`; the
  generated cache at
  `C:\Users\brsth\.claude\plugins\cache\local\search-research\0.1.115`
  contains both `/research` and the `/all` wrapper. Help-mode validation passed
  from the installed cache for both entrypoints.
- The Codex cachebuster helper was not applicable because this is a Claude
  plugin with `.claude-plugin/plugin.json`, not a Codex `.codex-plugin` manifest.

## Authorization

Authorized now:

- use `/research` as the canonical research capability;
- retain `/all` as a compatibility caller delegating to `/research`;
- use the existing QMD/MMX/Brave Phase 1 lanes and artifact substrate;
- continue manual/experimental runtime usage while adoption telemetry grows.

Still deferred:

- `/design` integration;
- `/go` and `/search` integration;
- new providers, Exa, DDG, or `agy`;
- automatic Phase 2A;
- routing redesign or model-based routing;
- changes to evidence authority, claim, or completion rules.
