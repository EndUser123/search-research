# Phase 2A targeted-disconfirmation stabilization

Observed: 2026-07-13. This increment stabilizes Phase 2A only. It does not integrate Phase 2A into `/go`, `/search`, or any primary workflow; it adds no provider and does not invoke `agy`.

## Environment and authority

The repository is `P:\`, branch `main`, HEAD `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`. The worktree was already materially dirty with unrelated hook, provider-config, plugin, and delegation changes; those changes were preserved. Active worktrees were recorded with `git worktree list` and were not modified.

No root Python manifest or canonical project virtual environment exists for `tools/research_run_v1`. The existing installed test executable was verified as:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe
pytest 9.0.2
```

Canonical command used:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `58 passed`. No package was installed or shared environment modified.

## Stabilization changes

`phase2a.py` now has deterministic admission checks for claim binding, decision-changing relevance, external testability, generic ceremonial risks, already-resolved hypotheses, duplicates, and explicit corpus rejection reasons. The corpus retains all original 16 hypotheses for same-case comparison, but five are rejected before provider invocation.

`build_bounded_query()` rejects keyword-only queries and appends a missing claim anchor to preserve the concrete failure mode. It does not add generic `problem`, `failure`, `issue`, or `bad` stuffing.

Contradiction evidence remains conservative: only opened, claim-bound evidence with an anchor, sufficient evidence terms, compatible scope, and a contradiction relationship can affect reconciliation. Search snippets remain discovery-only. Rejected or unresolved falsifiers cannot reject a conclusion or reduce authorization.

## Original noise and false-hit analysis

The original Phase 2A run had five noisy falsifiers and eight false-contradiction hits:

| Falsifier | Classification | Evidence pattern |
|---|---|---|
| `osc-2` | `different_claim_scope`, `keyword_overlap_only` | GitHub reusable-workflow documentation lacked the agentic-workflow claim anchor. |
| `abl-1` | `targets_the_wrong_claim`, `reported_issue_not_current_fact` | Results discussed agentic workflows but did not identify the allegedly abandoned repository. |
| `abl-2` | `source_identity_mismatch`, `different_claim_scope` | General repo-of-repos and AGENTS.md articles did not establish a mirror relationship for one library. |
| `ise-1` | `authority_requirement_not_encoded`, `secondary_source_overstatement` | Academic/secondary material matched terms but did not directly resolve the implementation question authoritatively. |
| `inc-2` | `different_claim_scope`, `keyword_overlap_only` | SourceGraph’s general agentic-coding article did not prove that the specific result was a toy implementation. |

The eight false hits were the two `osc-2` sources, one `abl-1` source, two `abl-2` sources, two `ise-1` sources, and one `inc-2` source. They were not treated as factual contradictions after stabilization.

The original three source-open failures were one MMX `HTTPError` for `wld-1` and two Brave `URLError` failures for `ise-2`. The stabilized rerun had two failures, both Brave `URLError` failures for `ise-2`; no opener replacement was added.

## Same-corpus comparison

| Case | Original action | Stabilized action | Admitted/rejected | Opens before/after | Noise before/after | Reconciliation |
|---|---|---|---:|---:|---:|---|
| maintained-agentic-repositories | continue targeted use | continue targeted use | 2/0 | 2/2 | 0/0 | survived |
| feature-implementation-evidence | continue targeted use | continue targeted use | 2/0 | 4/4 | 0/0 | survived |
| windows-lifecycle-defects | explicit guardrail | explicit guardrail | 2/0 | 3/4 | 0/0 | guardrail retained |
| official-source-comparison | no broader authorization | no broader authorization | 1/1 | 4/2 | 1/0 | authorization reduction retained |
| abandoned-library | gather more evidence | gather more evidence | 0/2 | 4/0 | 2/0 | conservative unresolved result retained |
| authoritative-missed-source | primary verification | gather more evidence | 0/2 | 4/0 | 0/0 | more-evidence requirement retained, conservatively strengthened |
| insufficient-evidence | gather more evidence | gather more evidence | 1/1 | 2/0 | 1/0 | more-evidence requirement retained |
| implementation-not-concept | continue targeted use | continue targeted use | 1/1 | 4/2 | 1/0 | survival retained |

Five original material action changes were retained. The stabilized run had 3 survived, 1 added guardrail, 1 reduced authorization, and 3 required more evidence; it rejected no conclusion. It produced no false authorization reduction and no false rejection. One remaining false-contradiction hit (`osc-1`) was retained as a non-material lexical hit and did not change the action.

## Measured burden

| Metric | Original | Stabilized | Change |
|---|---:|---:|---:|
| Total wall time | 109.5 s | 98.0 s | -10.5 s |
| Additional opened sources | 27 | 14 | -13 |
| Source-open failures | 3 | 2 | -1 |
| Noisy falsifiers | 5 | 0 | -5 |
| False-contradiction hits | 8 | 1 | -7 |

The stabilized run issued only admitted provider searches, retained role routing (MMX conceptual/alternative discovery; Brave implementation/authority/maintenance), and used QMD once per case. MMX readiness was `ready` before and after; quota attribution remained indeterminate under shared concurrent use.

## Deterministic future recommendation policy (not integrated)

Recommend targeted disconfirmation only when a provisional claim supports a consequential decision and at least one trigger is true: adopting a repository/framework/provider/dependency; introducing a mechanism or architectural layer; claiming production readiness or compatibility; claiming runtime activation from presence/documentation; making a hard-to-reverse or authority-bearing decision; relying on maintenance, containment, lifecycle, or security claims; deciding a native capability is insufficient; or when omission risk is explicitly material.

Skip it for simple factual lookups, locating an official page, low-impact reversible questions, claims already resolved by direct current authoritative evidence, or questions without a provisional decision-bearing claim.

Depth is deterministic: light = 1–2 admitted falsifiers for a consequential but reversible decision; standard = 2–3 for adoption, compatibility, lifecycle, or production claims; rigorous = 3–5 for authority-bearing, hard-to-reverse, security, containment, or explicitly high-omission-risk decisions. These are internal policy thresholds only; no user-facing mode or automatic workflow was added.

## Authorization and verdict

Authorized by this increment: manual/offline evaluation and bounded targeted disconfirmation using the existing MMX, Brave, QMD, source-opening, assessment, and claim-status paths. Not authorized: `/go` or `/search` integration, automatic routing, provider fallback, `agy`, adaptive learning, production configuration, or generic disconfirmation.

Verdict: `PASS_PHASE2A_STABILIZED`. Canonical tests pass; the same-case live rerun retained all five material prior action changes, eliminated noisy falsifiers, reduced false hits and source-opening burden, and did not create an unsafe authorization reduction or false rejection.

Intentionally deferred: primary-workflow integration, opener improvements, further corpus expansion, adaptive falsifier generation, and Phase 2B disconfirmation. The next step is targeted workflow integration only after an explicit human checkpoint; no integration was performed here.

## Provider-provenance audit correction

The implemented Phase 2A path is provider-traceable: `evaluate_phase2a.py` calls the existing MMX executor, Brave lane, and QMD/local lane; the final artifact records MMX, Brave, and QMD only. Every opened source records its provider and source identity. Exa and DuckDuckGo do not appear in the artifact or implemented Phase 2A invocation path. The separate OpenCode terminal summary mentioning Exa/Brave/DDG/MMX is external tool telemetry and is not evidence that those tools supplied Phase 2A results.

The original raw Phase 2A artifact is no longer retained separately from the stabilized run, so exact original query/result equivalence cannot be reconstructed. The reported before/after metrics are therefore only partially comparable: corpus and assessment/reconciliation rules are comparable, while original raw provider telemetry, exact query text after stabilization's anchor construction, and source selection are not fully reconstructible. The correct milestone wording is:

> Stabilization retained useful decision effects and reduced observed noise under the available MMX+Brave+QMD execution path. Because the original raw artifact is unavailable for byte-level provider/result comparison, exact quantitative before/after attribution is partial.

Two fresh bounded MMX+Brave confirmation cases (`windows-lifecycle-defects` and `official-source-comparison`) reproduced their stabilized actions: explicit guardrail and reduced authorization respectively. MMX and Brave were both ready; the run was stored at `P:\tmp\.codex\state\phase2a-provenance-confirmation-20260714\confirmation.json`. This confirms no material regression in those two cases, but does not upgrade the full-corpus comparison to provider-equivalent.

The provenance-corrected full artifact was regenerated after this audit. It records 5 MMX calls and 4 Brave calls (the Brave empty-result attempt is included), 8 QMD calls, 14 opened sources, 2 source-open failures, 0 noisy falsifiers, and 0 false contradictions. Its current reconciliations are 4 survived, 1 guardrail added, and 3 requiring more evidence; the official-source case returned `continue_targeted_use` in this later run. This variability is why the earlier exact “five action changes retained” wording is historical evidence from the preceding run, not a stable provider-equivalent metric.
