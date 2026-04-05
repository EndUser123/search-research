## Triage Classification
**code** — Python source code module with batch detection logic for GTO RSN output

## Dispatched Specialists
- **adversarial-logic**: Batch grouping strategy correctness, truncation collisions
- **adversarial-quality**: Batch routing, severity normalization, path parsing
- **adversarial-testing**: Test coverage, severity case mismatch, edge cases
- **adversarial-io-validation**: Path handling, type safety, import mutations

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pure logic correctness in batch grouping strategies
**Key findings:**
- LOGIC-001 [MEDIUM]: Double-truncation in Strategy 2 batch ID creation causes reason collisions
- LOGIC-002 [MEDIUM]: Strategy 2 hardcodes domain="import" regardless of actual keyword matched
- Open questions: 50% effort multiplier is arbitrary; Strategy 1/2 priority is undocumented

### adversarial-quality
**Domain:** Maintainability, batch routing correctness, domain mapping
**Key findings:**
- QUAL-001 [HIGH]: Location key ('', None) vs (None, None) don't batch together — same-location gaps missed
- QUAL-002 [HIGH]: Strategy 2 reason split on '.' loses attribute name context from [attr-defined]
- QUAL-003 [MEDIUM]: Strategy 3 passes severity through without uppercase normalization
- QUAL-004 [MEDIUM]: Windows drive letter colon in batch ID makes id unparseable (BATCH-LOC-C:\file.py:10)
- QUAL-005 [LOW]: Domain hardcoded for batched findings vs derived for individual

### adversarial-testing
**Domain:** Test coverage, regression detection
**Key findings:**
- TEST-001 [HIGH]: severity_order uses UPPERCASE keys but Gap dataclass produces lowercase — ALL batches report LOW severity
- TEST-002 [HIGH]: Zero test coverage for _detect_batch_groups() and format_rsn_from_gaps()
- TEST-003 [MEDIUM]: Batch ID produces BATCH-LOC-foo.py:None when line_number is None
- TEST-004 [MEDIUM]: Partial location overlap skips entire group — silently drops gaps
- TEST-005 [LOW]: Domain routing inconsistency between batched and non-batched findings
- TEST-006 [LOW]: GapFinding missing effort_estimate_minutes — all subagent gaps get 5-min default

### adversarial-io-validation
**Domain:** Type safety, path handling, import hygiene
**Key findings:**
- IO-001 [BLOCKER]: .lower() called on msg without string type guard — AttributeError on None/non-string
- IO-002 [BLOCKER]: dict.fromkeys() on generator with unhashable message values — TypeError
- IO-003 [BLOCKER]: Effort multipliers 0.7/0.5 arbitrary with no upper-bound validation
- IO-004 [LOW]: sys.path.insert(0, ...) mutates global import path at import time — multi-terminal hazard
- IO-005 [LOW]: msg.find('# type: ignore') returning -1 causes msg[-1:] (last char) as grouping key

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-testing/TEST-001) — severity case mismatch: severity_order={"CRITICAL":0,"HIGH":1...} but Gap produces lowercase — all batches get LOW (next_steps_formatter.py:388,445)
1.2. [HIGH] (source: adversarial-quality/QUAL-001) — location key collision: ('',None) vs (None,None) don't batch together — same-file gaps missed (next_steps_formatter.py:369-374)
1.3. [HIGH] (source: adversarial-quality/QUAL-002) — reason split('.') truncates at first dot, discarding attribute name from [attr-defined] (next_steps_formatter.py:433)
1.4. [MEDIUM] (source: adversarial-logic/LOGIC-001) — double-truncation ([:40] then [:20]) creates BATCH-IGNORE collisions for distinct attr errors (next_steps_formatter.py:432-434)
1.5. [MEDIUM] (source: adversarial-logic/LOGIC-002) — domain hardcoded "import" for all # type: ignore batches regardless of keyword — misroutes "no attribute" findings (next_steps_formatter.py:460)
1.6. [MEDIUM] (source: adversarial-quality/QUAL-003) — Strategy 3 severity passes through unnormalized while Strategy 1/2 normalize — mixed-case causes KeyError (next_steps_formatter.py:482)
1.7. [MEDIUM] (source: adversarial-testing/TEST-004) — used_indices overlap skips entire location group, silently drops unused indices (next_steps_formatter.py:379-380)

### Hidden Assumptions & Fragile Dependencies
2.1. [BLOCKER] (source: adversarial-io-validation/IO-001) — assumes all gap['message'] values are strings — None causes AttributeError (next_steps_formatter.py:428-429)
2.2. [BLOCKER] (source: adversarial-io-validation/IO-002) — assumes message values are hashable for dict.fromkeys() — list/dict causes TypeError (next_steps_formatter.py:393)
2.3. [HIGH] (source: adversarial-io-validation/IO-003) — effort multipliers 0.7/0.5 are arbitrary with no empirical basis; no upper-bound validation (next_steps_formatter.py:402,450)
2.4. [LOW] (source: adversarial-io-validation/IO-004) — sys.path.insert(0,_claude_dir) at import time creates multi-terminal TOCTOU import hazard (next_steps_formatter.py:312-322)
2.5. [LOW] (source: adversarial-quality/QUAL-004) — Windows path colon ambiguous in BATCH-LOC-{path}:{line} format (next_steps_formatter.py:407)
2.6. [LOW] (source: adversarial-io-validation/IO-005) — find('# type: ignore') returning -1 produces msg[-1:] as grouping key (next_steps_formatter.py:428-434)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-testing/TEST-002) — zero test coverage for _detect_batch_groups() or format_rsn_from_gaps() — 3 strategies completely untested
3.2. [MEDIUM] (source: adversarial-quality/QUAL-004) — batch ID separator ':' conflicts with Windows drive letter — use '|' or hash instead (next_steps_formatter.py:407)
3.3. [LOW] (source: adversarial-testing/TEST-005) — domain hardcoded for batched gaps vs derived for individual — section routing inconsistent (next_steps_formatter.py:413,460)
3.4. [LOW] (source: adversarial-testing/TEST-006) — GapFinding missing effort_estimate_minutes field; all subagent gaps default to 5 minutes (gap_finder_subagent.py:23)

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-testing/TEST-003) — BATCH-LOC-foo.py:None when line_number=None — malformed IDs in output (next_steps_formatter.py:407)
4.2. [LOW] — 50% effort multiplier has no stated justification; may mislead on actual effort (next_steps_formatter.py:450)
4.3. [LOW] — Strategy 1/2 mutual exclusivity (used_indices) priority not documented — may conflate future cases

### Concrete Recommendations
5.1. [HIGH] — Normalize severity: severities = [g.get("severity","LOW").upper() for g in batch_gaps] at lines 389 and 446 (source: adversarial-testing/TEST-001)
5.2. [HIGH] — Add type guard: if not isinstance(msg, str): continue before .lower() call at line 428 (source: adversarial-io-validation/IO-001)
5.3. [HIGH] — Add test coverage for _detect_batch_groups() with all 3 strategies and format_rsn_from_gaps() end-to-end (source: adversarial-testing/TEST-002)
5.4. [HIGH] — Normalize file_path in location key: fp = gap.get('file_path') or '' then None→'' consistently (source: adversarial-quality/QUAL-001)
5.5. [HIGH] — Sanitize message before dict.fromkeys: str_msgs = [str(m) if isinstance(m,str) else repr(m) for m in msgs] (source: adversarial-io-validation/IO-002)
5.6. [MEDIUM] — Use '|' separator instead of ':' in batch IDs to avoid Windows path collision (source: adversarial-quality/QUAL-004)
5.7. [MEDIUM] — Guard against -1 from find(): if reason_start == -1: continue (source: adversarial-io-validation/IO-005)
5.8. [MEDIUM] — Emit unused indices as individual findings instead of skipping entire group on overlap (source: adversarial-testing/TEST-004)
5.9. [MEDIUM] — Derive domain from matched keyword or original gap type, not hardcoded (source: adversarial-logic/LOGIC-002)
5.10. [MEDIUM] — Add effort upper-bound validation and comment justifying 0.7/0.5 multipliers (source: adversarial-io-validation/IO-003)

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-logic) — Is 50% effort multiplier based on empirical data? Document source or make configurable
6.2. [LOW] (source: adversarial-logic) — Is Strategy 1 priority over Strategy 2 intentional for gaps matching both? Document priority
6.3. [LOW] (source: adversarial-io-validation) — Is sys.path.insert() fallback actually reachable in production, or is rsn_formatter properly importable via package path?
6.4. [LOW] (source: adversarial-testing/TEST-006) — Does GapFinderSubagent ever produce gaps without effort_estimate_minutes in practice?
