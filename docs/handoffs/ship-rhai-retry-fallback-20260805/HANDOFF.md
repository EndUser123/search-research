# Handoff — ship-rhai retry-with-fallback + remaining fixes

## Status
OPEN — design agreed, implementation deferred to fresh session.

## Objective

Add bounded retry-with-fallback-model to the ship-rhai workflow, plus fix
remaining items from this session.

## Retry design (agreed)

```
agent fails → retry once with different model → retry fails → log warning + continue
                                                         ↓
                                             if ALL agents in a phase failed → BLOCKED
                                             if SOME succeeded → proceed with gap noted
```

Rules:
- Cap at 1 retry per agent
- Retry MUST use a different model from the pool
- Don't block entire workflow on single agent failure
- Only retry load-bearing agents (review, verify) — not detect/report
- On retry failure: write details to scratch file for handoff/investigation

## Implementation targets

### 1. Retry-with-fallback in ship-rhai.rhai

Current state: review agents have no retry. The review-success gate (finding #8)
blocks if both fail. Add retry before blocking.

File: `~/.grok/workflows/ship-rhai.rhai`

Pattern to add after each `parallel()` call:

```rhai
// Retry failed agents with fallback model
let retry_jobs = [];
let retry_indices = [];
let i = 0;
for r in review_results {
    if r == () || !r.success {
        // This agent failed — retry with different model
        let fallback_model = "cohere-north-mini-code";  // different from originals
        let original_job = review_jobs[i];
        retry_jobs.push(#{
            prompt: original_job.prompt,
            label: original_job.label + "-retry",
            capability_mode: original_job.capability_mode,
            output_schema: original_job.output_schema,
            model: fallback_model,
        });
        retry_indices.push(i);
    }
    i += 1;
}
if retry_jobs.len() > 0 {
    log(retry_jobs.len().to_string() + " review agents failed — retrying with fallback model");
    let retry_results = parallel(retry_jobs);
    // Merge retry results back into review_results
    let j = 0;
    for idx in retry_indices {
        if retry_results[j] != () && retry_results[j].success {
            review_results[idx] = retry_results[j];
            log("Retry succeeded for agent " + idx.to_string());
        } else {
            log("Retry also failed for agent " + idx.to_string());
        }
        j += 1;
    }
}
```

Note: Rhai maps are `#{ ... }` — the above uses pseudocode. The implementer
needs to verify that Rhai supports accessing `original_job.prompt` etc. from
a map stored in an array. The `review_jobs` array already contains option
maps, so field access should work.

### 2. Remaining session items

- **ship-rhai-3 is still running** — it will complete or fail. Check its
  output for real-world findings when it finishes.
- **Skill pre-check hook** — see `P:/docs/handoffs/skill-precheck-hook-20260805/HANDOFF.md`
- **Self-improving patterns research** — see handoff at same path
- **Push both repos** — significant unpushed work:
  ```powershell
  git -C P:/ push origin main
  git -C C:/Users/brsth/.grok push origin main
  ```
- **ship-py needs the same fixes** (hardcoded session_id, verdict matching,
  health-check flag, review-failure gate, merge-base detection, retry-with-fallback)
- **Scanner Check 11 (NO-WIKI-PERSISTENCE)** flagged both ship skills — add
  wiki-write steps

## Key files

- `~/.grok/workflows/ship-rhai.rhai` — the workflow to enhance
- `~/.grok/skills/ship-rhai/SKILL.md` — skill entry point
- `~/.grok/skills/ship-rhai/__lib/ship_receipt.py` — mechanical verification
- `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — Python variant (needs same fixes)
- `P:/docs/handoffs/skill-precheck-hook-20260805/HANDOFF.md` — other open items
- `P:/.data/wiki/concepts/skill-step-enforcement-architecture-grok-build.md` — architecture decisions

## Handoff is wrong if

- The retry logic adds too much latency (>2x the original run time)
- The retry uses the same model (defeats the purpose — same blind spots)
- The retry blocks the workflow instead of continuing with partial results
