## Triage Classification
wiki — Claude Code skill for wiki knowledge management with YouTube URL auto-detection and yt-is pipeline with Gemini CLI failover

## Dispatched Specialists
- adversarial-critic: reasoning quality, phase logic, trigger matching, meta-consensus between specialists
- adversarial-compliance: YAML frontmatter, hook registration, schema completeness, contract gaps
- adversarial-quality: maintainability, skill structure, error handling, test coverage

## Specialist Findings Summary

### adversarial-critic
Three meta-findings were produced. Two represent cross-specialist consensus (both adversarial-critic and adversarial-compliance independently flagged the same issues):
1. **Consensus on EVIDENCE_GAP schema gap** (adversarial-critic + adversarial-compliance): EVIDENCE_GAP flag annotations appear in body text (SKILL.md lines 131-136) but not in YAML frontmatter schema (lines 109-125), making the classification non-machine-readable.
2. **Consensus on transcripts.sqlite schema gap** (adversarial-critic + adversarial-compliance): The `failure_reason: no_transcript` trigger condition is documented at line 220, but the full transcripts.sqlite schema (table name, column names) is not documented.
3. **Blind spot identified**: `cognitive_load: <1-5>` notation in frontmatter (line 121) is advisory only — no enforcement bounds are specified, so values outside 1-5 would be silently accepted. The compliance specialist did not flag this as a separate concern, suggesting a detection分工 gap (specialists partition coverage and miss each other's gaps).

### adversarial-compliance
Three findings:
- **COMP-001 [HIGH]**: The `failure_reason: no_transcript` failover trigger references transcripts.sqlite but SKILL.md never documents its schema (table name, columns, semantics). Pipeline maintainers cannot verify whether the manifest correctly records failure states.
- **COMP-002 [MEDIUM]**: `EVIDENCE_GAP` annotations appear inline in body text (lines 131-136) but are absent from the frontmatter schema (lines 109-125). Pages cannot be filtered or ranked by EVIDENCE_GAP status via frontmatter queries.
- **COMP-003 [LOW]**: The "one wiki page per video" Option A decision is implemented but not recorded as a deliberate architectural choice in SKILL.md — only in work.md. Future maintainers may inadvertently refactor to multi-video pages.

### adversarial-quality
Six findings across testing, portability, robustness:
- **QUAL-001 [LOW]**: Two near-identical embedded Python HEREDOC manifest-generation scripts (lines 32 and 176) have no pytest coverage and risk drift on future refactors.
- **QUAL-002 [LOW]**: Three hardcoded paths (`P:/`, `C:/Users/brsth/Downloads`, `/tmp/`) have no env-var fallback, reducing portability.
- **QUAL-003 [LOW]**: Tier-classification boundary logic (200KB, 500KB) has no test coverage; wrong tier causes incorrect skip/warn behavior.
- **QUAL-004 [LOW]**: The Gemini CLI fallback (`gemini -p`, line 158) has no try/except and no timeout — a failed call crashes the subagent without writing `status=failed` to the manifest.
- **QUAL-005 [LOW]**: YouTube URL pattern matching (line 152) uses simple substring checks (`youtube.com/watch`) without regex validation for video ID presence; malformed URLs pass the check and fail downstream.
- **QUAL-006 [MEDIUM]**: Ingest dispatch updates manifest entries to `status: done` or `status: failed` but has no resume flag or idempotency key — crash mid-dispatch leaves partial state that re-dispatches on retry.

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (adversarial-compliance / COMP-001) — transcripts.sqlite schema is referenced by the failover contract (`failure_reason: no_transcript`, SKILL.md line 220) but never documented. The table name, column names, and exact semantics of the `no_transcript` value are absent from the skill's stated contract. Pipeline maintainer cannot verify whether the manifest correctly records failure states.

1.2. [MEDIUM] (adversarial-compliance / COMP-002) — EVIDENCE_GAP annotations exist in body text (SKILL.md lines 131-136: "For each item, annotate with cognitive load (1-5) and flag any EVIDENCE_GAP") but are not a frontmatter field. This means EVIDENCE_GAP classification is not machine-readable from frontmatter and cannot be used for wiki page filtering or ranking. Work.md explicitly requires EVIDENCE_GAP as part of the enhanced subagent output schema.

1.3. [LOW] (adversarial-compliance / COMP-003) — "One wiki page per video" Option A decision is implemented in SKILL.md v1.3.0 but the decision rationale exists only in work.md, not in the skill's own documentation. Future maintainers cannot determine whether the single-page-per-video structure is intentional or accidental.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (adversarial-critic blind_spot) — Frontmatter schema declares `cognitive_load: <1-5>` (line 121) using advisory angle-bracket notation. There is no enforcement — a value of 6 or higher would be silently accepted by YAML parsing. Ingest subagent could emit out-of-range `cognitive_load` values without validation error.

2.2. [LOW] (adversarial-quality / QUAL-002) — VAULT_DIR path `P:/.data/wiki`, Downloads path `C:/Users/brsth/Downloads`, and temp path `/tmp/` are all hardcoded. No environment variable fallback is configured. Path changes require manual search-replace across SKILL.md.

2.3. [LOW] (adversarial-quality / QUAL-005) — YouTube URL validation uses simple substring matching (`youtube.com/watch`, `youtube.com/@`, etc., line 152). The assumption that any URL containing these substrings is valid is fragile — malformed URLs (e.g., missing video ID) pass this check and fail downstream in the yt-is pipeline.

### Missing Obvious Actions / Best Practices
3.1. [LOW] (adversarial-quality / QUAL-001) — Two identical embedded Python HEREDOC scripts for manifest generation (lines 32 and 176) have no unit tests. The obvious action is to extract to `scripts/wiki_manifest.py` with pytest coverage.

3.2. [LOW] (adversarial-quality / QUAL-003) — Tier-classification boundary values (200KB, 500KB) are hardcoded with no boundary tests. The obvious action is to add pytest parameterized tests for the safe/large_warn/large_skip thresholds.

3.3. [LOW] (adversarial-quality / QUAL-004) — The Gemini CLI fallback invocation has no error handling and no timeout. The obvious action is to wrap in `try/except` with a 60-second timeout and write `status=failed` to the manifest on error.

3.4. [LOW] (adversarial-compliance / COMP-003) — The Option A "one wiki page per video" decision should be recorded in SKILL.md as a one-line architectural note to prevent future refactorers from inadvertently changing the structure.

### Risks and Edge Cases
4.1. [MEDIUM] (adversarial-quality / QUAL-006) — Ingest dispatch has no atomicity or resume mechanism. A crash mid-dispatch leaves the manifest in a partial state (some entries `pending`, some `done`, some `failed`). On retry, all `pending` entries are re-dispatched, potentially causing duplicate wiki pages or duplicate yt-is calls. No idempotency key exists.

4.2. [LOW] (adversarial-quality / QUAL-004) — Gemini CLI subprocess call with no error handling means a network failure, timeout, or non-zero exit code from `gemini -p` crashes the subagent without any manifest update. The failure is invisible to orchestrator until the subagent completes with an error.

4.3. [LOW] (adversarial-quality / QUAL-005) — A YouTube URL that passes the substring check but is malformed (e.g., `youtube.com/watch?v=` with empty video ID, or `youtube.com/watch?v=DEADBEEF` where the video does not exist) will reach the yt-is pipeline, which will fail at the yt-is level. The error surface is downstream rather than at the skill entry point.

4.4. [LOW] (adversarial-critic consensus) — Both specialists confirmed the transcripts.sqlite schema is undocumented. If the yt-is pipeline changes its schema (renames `failure_reason` column, uses a different table name), the SKILL.md failover trigger would silently stop working with no validation error.

### Concrete Recommendations
5.1. [HIGH] Document transcripts.sqlite schema in SKILL.md: table name (`transcripts`), column names (`video_id`, `failure_reason`, `fetched_at`, and any others), and the exact semantics of `failure_reason='no_transcript'` as the failover trigger. Add a schema section to the yt-is pipeline documentation. (Source: COMP-001, confirmed by adversarial-critic consensus)

5.2. [MEDIUM] Add `evidence_gaps: [<list of EVIDENCE_GAP descriptions>]` to the YAML frontmatter schema alongside `cognitive_load` and `pillar_scores`, OR explicitly document that EVIDENCE_GAP is intentionally body-only annotation with rationale. (Source: COMP-002, confirmed by adversarial-critic consensus)

5.3. [MEDIUM] Add a `--resume` flag to ingest dispatch that filters to `status: pending` entries only, preventing re-dispatch of already-processed items after a crash. (Source: QUAL-006)

5.4. [LOW] Wrap the Gemini CLI subprocess call in `try/except` with a 60-second timeout, and ensure `status=failed` is written to the manifest entry on any exception or non-zero exit. (Source: QUAL-004)

5.5. [LOW] Add frontmatter validation rule for `cognitive_load` range enforcement, or clarify that values outside 1-5 are silently clamped. Document the enforcement behavior. (Source: adversarial-critic blind_spot)

5.6. [LOW] Extract the two manifest-generation HEREDOCs to `scripts/wiki_manifest.py` with pytest coverage including boundary tests for tier classification (199999 → safe, 200000 → safe, 200001 → large_skip). (Source: QUAL-001, QUAL-003)

5.7. [LOW] Replace hardcoded paths with `pathlib.Path(os.getenv("WIKI_VAULT_DIR", "P:/.data/wiki"))` pattern. (Source: QUAL-002)

5.8. [LOW] Add a one-line architectural note in the ingest section of SKILL.md: `# Option A: one wiki page per video (per user decision, 2026-05-11)`. (Source: COMP-003)

5.9. [LOW] Add regex validation for YouTube video ID (e.g., `^[a-zA-Z0-9_-]{11}$`) after the substring URL check, before dispatching to yt-is. (Source: QUAL-005)

### Open Questions / Unknowns
6.1. What is the exact schema of transcripts.sqlite (table name, all column names, types)? The SKILL.md references it but does not define it. Verification needed against the actual yt-is pipeline implementation.

6.2. Does the yt-is pipeline write `failure_reason` to transcripts.sqlite for all failure modes, or only for `no_transcript`? The failover triggers on `failure_reason: no_transcript` for all methods exhausted, but the boundary condition (which methods, how "exhausted" is defined) is not documented.

6.3. Is there a live test corpus for the tier-classification boundary values? No test file exists according to QUAL-003, so the boundary behavior at exactly 200KB and 500KB is currently unverified.

6.4. What happens when the Gemini CLI is unavailable or returns a non-zero exit code under the current implementation? The error handling gap (QUAL-004) means this scenario has not been systematically tested.

6.5. Are the two HEREDOC manifest-generation scripts at lines 32 and 176 truly identical, or do they differ in subtle ways? If identical, one is a duplicate that should be eliminated; if different, each needs its own test coverage.