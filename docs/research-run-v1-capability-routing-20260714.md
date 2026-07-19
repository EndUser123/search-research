# `/all` Phase 1 capability-composition routing

Date: 2026-07-14  
Workspace: `P:/`  
Branch: `main`  
HEAD: `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`  
Consumed caller: `P:/packages/.claude-marketplace/plugins/search-research/skills/all/orchestration.py`  
Canonical Phase 1 runtime: `P:/tools/research_run_v1/phase1.py`

## Verdict

`PASS_CAPABILITY_ROUTING`

The smallest capability-composition increment is implemented and exercised through the real `/all` entrypoint. `/all` can now select QMD, MMX, and Brave as the minimum sufficient bounded set when the existing parallel policy is explicitly triggered. Authority-sensitive work reaches Brave discovery and source opening; authority remains an evidence-assessment result, not a provider capability gate.

This does not authorize `/go`, `/search`, Phase 2A automation, `agy`, unrestricted parallelism, or authority claims without claim-specific evidence.

## Existing limitation and change

The previous router required every selected lane to satisfy every task capability. That blocked mixed tasks and incorrectly treated `primary_source_verification` as a prerequisite of Brave discovery.

The router now:

1. derives execution requirements from task signals;
2. maps provider roles to evidence capabilities;
3. selects a minimum sufficient lane set by bounded capability coverage;
4. returns multiple lanes only when the existing parallel trigger is active;
5. records required capabilities, satisfaction mapping, rejected lanes, and execution wave;
6. leaves authority verification to source opening and evidence assessment.

Provider roles remain unchanged:

| Lane | Capabilities |
|---|---|
| QMD | `local_context` |
| MMX | external, broad, conceptual, candidate discovery |
| Brave | external, implementation, repository, maintenance, compatibility, authority-candidate discovery |

`source_opening` and `evidence_assessment` are represented as Phase 1 post-selection capabilities. `primary_source_verification` is recorded as required evidence but is not claimed as satisfied merely because Brave returned a result.

## Static and synthetic evidence

- Router corpus and existing policy tests remain green.
- Authority synthetic case selects Brave and leaves `primary_source_verification` unsatisfied until assessment.
- Mixed synthetic case selects exactly `{local, brave, mmx}` under `distinct_complementary_roles`.
- Without a parallel trigger, the selector retains single-lane behavior and avoids extra provider calls.
- Existing immutable artifact and multi-terminal isolation tests remain in the canonical suite.

## Live `/all` evidence

| Case | Artifact | Selection | Evidence |
|---|---|---|---|
| Local-only | `22fb15d1-ac97-499f-be83-1a9f8432296b` | QMD | 2 opened sources; QMD only; validated |
| Conceptual | `96b1c5c0-ad87-4ad5-ad07-a001819028f5` | MMX | MMX success; 2 opened sources |
| Implementation | `2b27dcd6-eb50-44ff-ae23-75af04161593` | Brave | Brave success; 2 opened sources |
| Authority-sensitive | `1a7bd3fd-45b8-4ecf-8e84-f1fde2643fd8` | Brave | Brave success; 2 opened sources; one `unverified` authority-candidate claim and assessment |
| Mixed local + conceptual + implementation | `e93092fb-0196-4655-8278-52a5b3793335` | QMD + MMX + Brave | bounded parallel wave; all three provider outcomes `success`; 16 normalized sources; source IDs unique and artifact validated |

The mixed run initially exposed duplicate source IDs when MMX and Brave returned the same URL. Source IDs are now provider-scoped, preserving distinct provenance while retaining stable identity within each lane.

## Files changed

- `P:/tools/research_run_v1/router.py`
- `P:/tools/research_run_v1/mmx_state.py`
- `P:/tools/research_run_v1/brave_lane.py`
- `P:/tools/research_run_v1/phase1.py`
- `P:/packages/.claude-marketplace/plugins/search-research/skills/all/search_executor.py`
- `P:/tests/research_run_v1/test_router.py`
- `P:/tests/research_run_v1/test_workflow_integration.py`
- `P:/docs/research-run-v1-capability-routing-20260714.md`

No new provider, broker, scheduler, caller, `/go` path, `/search` path, or Phase 2A behavior was added.

## Verification

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
68 passed in 6.63s
```

Focused router/workflow verification: `18 passed`. The live artifacts above passed `P:/tools/research_run_v1/validate_research_run.py`.

The final source-authority audit is retained at `P:/tmp/source-discovery-capability-routing-final-20260714.json`. It reports `needs_review` because evaluator modules and canonical runtime modules share the tokens `phase1` and `router`; direct caller inspection reconciles `phase1.py` and `router.py` as canonical runtime sources, while `evaluate_phase1*.py` and `evaluate_router.py` are evaluator/test consumers.

## Authorization boundary

Authorized: manual/experimental `/all` Phase 1 routing for QMD-only, MMX-only, Brave-only, authority-candidate discovery, and explicitly justified bounded QMD+MMX+Brave composition.

Still unauthorized: automatic production routing, authority-bearing claims from provider output alone, Phase 2A workflow gating, `agy`, `/go`, `/search`, and any additional caller integration.
