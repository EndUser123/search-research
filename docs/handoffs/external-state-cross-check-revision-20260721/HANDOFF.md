---
thread_id: external-state-cross-check-revision-20260721
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console_019f819a
produced_at: 2026-07-22T03:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
source_transcript: C:/Users/brsth/.grok/sessions/P%3A%5C/019f819a-7619-7cb3-a6a4-480ff1c916ce/chat_history.jsonl
---

# HANDOFF — Revise external-state-cross-check wiki concept per /tp findings

## Objective

Revise the local-only wiki concept `P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md` to address 7 findings from a fresh-subagent /tp critique, then force-add to git.

## Status

READY_FOR_REVIEW — revision scope identified; not yet implemented.

## Producing context

- Date: 2026-07-21
- Session: 019f819a-7619-7cb3-a6a4-480ff1c916ce
- Parent concept: `plausible-narratives-substitute-for-verification.md` (committed e6ddee6) has a dangling cross-reference to this concept at line 144

## Read-first list

1. `P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md` — the concept page to revise
2. `P:/tmp/head-drift-falsification-2026-07-21.md` — falsification findings (PARTIAL verdict)
3. `/tp` critique output (in session transcript, not yet written to file) — 8 findings with evidence tags

## Verified facts

- [FACT] Falsification tested 4 of 6 drifted handoffs; 1 had genuinely stale refs (entire /aar skill gone), 2 had valid refs despite drift, 1 was moot
- [FACT] HEAD-drift is a necessary condition for staleness but not sufficient (HEAD can move without invalidating cited paths)
- [FACT] `/handoff verify` and `/handoff migrate` shipped as v0.1.1 commands after the concept was drafted — they are more precise per-citation external-state checks
- [FACT] `plausible-narratives-substitute-for-verification.md:144` has a dangling cross-reference to this concept

## Task packets

### ESC-01: Revise the concept per /tp findings

- goal: address all 7 content findings from the /tp critique
- in scope: `P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md`
- out of scope: changing the HEAD-drift column code; revising other wiki concepts
- files / anchors: the concept page (local-only)
- acceptance: all 7 findings addressed; concept reflects the PARTIAL falsification result honestly
- falsifier: if the revised concept still claims HEAD-drift is a sufficient condition, the revision didn't land
- verification level required: STATIC_INSPECTION

The 7 findings to address:
1. Add "Signal precision" section: necessary-condition detector, not sufficient
2. Rewrite falsifier: failure mode is "signal too noisy, triagers stop using --head," not "triagers ignore signal"
3. Update worked example: HEAD-drift is first instance; /handoff verify is the more precise second instance
4. Update Sources: cite the falsification file; upgrade verification tag to multi-source-verified
5. Add "external state too coarse" to "doesn't apply" section
6. Make design heuristic gradient, not binary
7. Soften implicit sufficiency claim in the core claim text

### ESC-02: Force-add and commit

- goal: commit the revised concept to git, closing the dangling cross-reference
- in scope: `git add -f` + commit
- acceptance: concept in HEAD; plausible-narratives cross-reference resolves
- falsifier: if the cross-reference still dangles after commit, the slug is wrong
- verification level required: STATIC_INSPECTION

## Open decisions

None — the /tp critique already converged on REVISE-then-COMMIT.

## Hard constraints

- Do NOT commit the concept before revision (option B discipline)
- Match the wiki SCHEMA.md frontmatter conventions
- The revision must honestly reflect the PARTIAL falsification verdict

## Cross-reference couplings

- `plausible-narratives-substitute-for-verification.md:144` → dangling cross-reference to this concept; commit closes it
- `P:/tmp/head-drift-falsification-2026-07-21.md` → source evidence for the revision
- `list_handoffs.py --head` → the worked example; code is shipped and stable

## Explicit non-goals

- Do NOT re-run the falsification (it's done; PARTIAL is the verdict)
- Do NOT revise the HEAD-drift column code (it works as designed; the concept's claims about it need revision, not the code)
- Do NOT start version-split cleanup (separate workstream, cancelled at scope guard)

## Resumption protocol

1. Read this handoff
2. Read the concept page at `P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md`
3. Read the falsification at `P:/tmp/head-drift-falsification-2026-07-21.md`
4. Implement ESC-01 (revise per 7 findings)
5. Implement ESC-02 (force-add + commit)

## Suggested next invocation

```
/go Revise the external-state-cross-check wiki concept per the /tp findings.
Read P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md
and P:/tmp/head-drift-falsification-2026-07-21.md. Address the 7 findings
documented in P:/docs/handoffs/external-state-cross-check-revision-20260721/HANDOFF.md.
Then git add -f the revised concept and commit. Run wiki_after_write.py after
the revision.
```

## Last user message (verbatim)

> /handoff audit -y

## Epistemic labels

- [FACT] falsification results verified against real handoff queue
- [FACT] /tp critique produced 8 findings, 0 hallucinations (all verified against session evidence)
- [FACT] dangling cross-reference confirmed at plausible-narratives line 144
- [INFERENCE] the revision is bounded content work, not architectural — ~30 min