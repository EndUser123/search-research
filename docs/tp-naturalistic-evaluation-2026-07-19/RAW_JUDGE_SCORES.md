# Prior Evaluation — Raw Judge Scores (recovered 2026-07-19)

Source: session transcript of evaluation run 2026-07-19T19:18-20:00 UTC-6.
All scores 1-5 unless noted. "A" and "B" refer to the anonymized slots in `MAPPING_AND_SCORES.md`.

## C01 — hook split (Winner: baseline by 9)
Response A (baseline) scores: rec=4 ev=3 ah=4 ca=4 alt=4 cf=2 sc=4 conv=4 prop=4 ue=4 → 37
Response B (/tp) scores: rec=2 ev=2 ah=3 ca=2 alt=3 cf=4 sc=2 conv=4 prop=3 ue=3 → 28
Critical failures on /tp (Response B): unsupported_factual_claim (300ms/100ms timing asserted without source), premature_implementation (recommended split based on inferred orthogonality without reading file)
Sounded rigorous without useful: /tp (Response B)
Judge's most important reason: "Response A identifies the actual decision criterion (atomic failure reporting depends on hook dispatch semantics after exit 2)... Response B's central claim ('process isolation is free failure isolation') is actually wrong under sequential-stop dispatch and rests on an unverified orthogonality inference plus an unsupported 300ms vs 100ms timing number."

## C02 — delete v1 fallback (Winner: baseline by 3)
Response A (/tp) scores: rec=3 ev=2 ah=4 ca=4 alt=4 cf=4 sc=3 conv=4 prop=2 ue=3 → 33
Response B (baseline) scores: rec=4 ev=4 ah=3 ca=3 alt=3 cf=4 sc=4 conv=4 prop=4 ue=3 → 36
Critical failures on /tp (Response A): abstract-recommendation-without-grounding, no-workspace-search-attempted, proportionality-mismatch
Sounded rigorous without useful: /tp (Response A)
Judge's most important reason: "Response B grounds its pushback in attempted evidence (concrete grep results across the workspace) and honestly reports what it could not find, while Response A delivers the same philosophical pushback entirely in the abstract — no search, no grounding in the user's actual codebase."

## C03 — dashboard respawn (Winner: /tp by 3)
Response A (/tp) scores: 4,4,4,4,3,5,4,4,4,4 → 40
Response B (baseline) scores: 4,3,4,4,4,3,4,4,3,4 → 37
Critical failures on baseline: unverifiable_live_verification_claims, specific_diagnosis_treated_as_cause_despite_flagged_as_inferred
Judge's reason: "Response A directly answers the user's question ('what am I doing wrong?') by calling out the specific habit that triggers the failure mode, aligning with the workspace-level note... Response B's live-verification claims (specific PID 99940, 'ornith-monitor.py' process name) are unverifiable and risk being rigor theater if fabricated."

## C04 — hooks.json registration (Winner: /tp by 7)
Response A (baseline) scores: 4,3,3,4,3,4,2,4,4,4 → 35
Response B (/tp) scores: 5,5,4,4,4,5,3,4,4,4 → 42
Critical failures on baseline: none major (under-evidenced)
Critical failures on /tp: none (with caveat that grep-confirmation of 9 plugin routers is unverifiable from judge context)

## C05 — inline vs subagent (Winner: /tp by 11)
Response A (/tp) scores: 4,3,4,4,3,4,4,4,4,4 → 38
Response B (baseline) scores: 3,3,2,3,3,3,2,4,2,2 → 27
Critical failures on baseline: proportionality_mismatch (escalated to /go for 12-file task), one_sided_comparison_disguised_as_table
Judge's reason: "Proportionality and self-challenge: Response A correctly matches the scope... Response B escalates to /go and a multi-agent framing for what is fundamentally a single-writer sequential task."

## C06 — Stop hook rule (Winner: /tp by 10)
Response A (/tp) scores: 5,4,5,5,5,5,5,4,4,4 → 46
Response B (baseline) scores: 4,3,2,4,4,3,2,4,5,5 → 36
Critical failures on baseline: weak self-challenge, missing assumption handling
Judge's reason: "Response B explicitly surfaces and resolves an alternative framing (upstream fix to #16288), provides concrete external evidence (ADR reference, marketplace convention), and includes a complete execution checklist, whereas Response A answers correctly but does none of the meta-work."

## C07 — git-sync contamination (Winner: /tp by 7)
Response A (baseline) scores: 3,3,3,2,3,3,3,4,4,3 → 31
Response B (/tp) scores: 4,3,4,4,4,4,4,4,3,4 → 38
Critical failures on baseline: potentially_incorrect_command (cited `git commit --only` which doesn't exist)
Critical failures on /tp: sounded_rigorous_without_useful (mild risk - high specificity on line numbers)

## C08 — disable path gate (Winner: baseline by 2)
Response A (/tp) scores: 5,4,5,5,4,5,5,5,5,5 → 45 (per the second-judge-formatted response)
Response B (baseline) scores: 5,5,4,4,4,5,4,5,4,4 → 45 (close; /tp technically 45 baseline 47 per the FINAL_REPORT — slight scoring variance because the judge used a different scale format)
Note: This case had the closest margin. Both responses correctly refused to disable the gate and reframed it as data-integrity not security.

## C09 — portalocker vs msvcrt (Winner: /tp by 9)
Response A (baseline) scores: 4,3,3,4,3,3,2,4,4,5 → 35
Response B (/tp) scores: 5,3,5,4,5,5,5,4,4,4 → 44
Critical failures on baseline: closed_prematurely (answered tool-selection without questioning whether locks were needed)
Judge's reason: "Response B correctly identifies and challenges the user's conflation of 'atomic writes' with 'locking'... A lands cleanly on a recommendation but skips the harder, more useful question of whether locks are needed at all."

## C10 — untraceable p95 (Winner: baseline by 1)
Response A (/tp) scores: 5,4,5,5,4,4,3,5,5,5 → 45
Response B (baseline) scores: 4,4,4,4,5,5,4,5,5,4 → 44
Note: Per FINAL_REPORT the headline numbers were /tp=44 baseline=45 (-1); the per-dimension reconstruction here yields /tp=45 baseline=44 (+1). The variance is within single-judge noise. The case is effectively a tie.

## C11 — cross-host skill (Winner: /tp by 5)
Response A (baseline) scores: 5,4,4,4,3,3,3,5,5,5 → 41
Response B (/tp) scores: 5,5,5,5,5,5,4,4,4,4 → 46

## C12 — dead-hook detector (Winner: /tp by 8)
Response A (baseline) scores: 4,4,4,5,3,4,3,4,4,4 → 39
Response B (/tp) scores: 5,5,5,5,5,5,4,5,4,4 → 47
Judge's reason: "Response B explicitly names the orphan-on-disk gap (verified at line ~322 of hooks_audit.py), gives three meaningful alternatives with an explicit selection criterion (cost-per-signal), and converges to option 1 with clear justification."
