# Adversarial Findings: Marketplace Dashboard Pre-Mortem
# Source: 8-agent adversarial review of premortem_marketplace_dashboard.md
# Date: 2026-03-24

## AGENT RESULTS SUMMARY

| Agent | Findings | Key Issues |
|-------|----------|------------|
| adversarial-security | 4 | SEC-001 live key in config.json, SEC-002 stored XSS in notes, SEC-003 Chart.js SRI missing, SEC-004 GitHub rate limit silent fail |
| adversarial-testing | 12 | TEST-001 zero test coverage, TEST-002 hardcoded [0] index, TEST-003 HTML ID replacement silent fail, TEST-004 DATA block regex silent fail, TEST-005 totals ignores null |
| adversarial-quality | 6 | QUAL-001 data-raw format coupling, QUAL-002 no schema validation, QUAL-003 metric inflation unaddressed, QUAL-004 single timestamp not per-source, QUAL-005 CRIT-001 not enforced |
| adversarial-logic | 6 | LOGIC-001 kill criteria incomplete (malformed data-raw), LOGIC-002 risk table reference error (Risk 9 doesn't exist), LOGIC-003 cascade trace contradiction, LOGIC-004 arbitrary severity thresholds |
| adversarial-compliance | 5 | COMP-001 CRIT-001 never implemented, COMP-002 parseInt mischaracterized, COMP-003 metric inflation unaddressed, COMP-004 hardcoded 94% vs dynamic, COMP-005 success theater not disclosed |
| adversarial-performance | 5 | PERF-001 sequential blocking I/O (135s worst-case), PERF-002 TOCTOU ID mismatch, PERF-003 GitHub rate limiting, PERF-004 NaN from parseInt, PERF-005 N+1 query pattern |
| adversarial-qa | 8 | QA-001 no success acceptance criteria, QA-002 operational checks not automated, QA-003 security grade undefined fallback, QA-004 overlap threshold undefined, QA-005 data-raw format not tested |
| adversarial-critic | 1 | CRIT-001 findings reference wrong doc (plan-adr... vs marketplace), consensus on 0.70 threshold (not relevant here) |

## KEY FINDINGS BY SEVERITY

### CRITICAL (must fix before use)
- SEC-001: Live SkillsMP API key in plaintext config.json → immediate credential exposure risk
- SEC-002: Stored XSS — `notes` field rendered in innerHTML without sanitization → arbitrary JS execution
- TEST-002: Hardcoded `new_data["sources"][0]["listings"]` assumes first position → wrong KPI if order changes
- TEST-003: `html.replace()` silently no-ops on missing ID → dashboard shows NaN with no error
- TEST-004: DATA block regex fails silently → stale DATA persists, no error
- PERF-002: TOCTOU — no verification ID replacement actually occurred → silent failure cascade

### HIGH
- PERF-001: Sequential blocking I/O — 135s worst-case, parallel_get defined but never called
- TEST-005: Totals sum ignores null vs zero distinction → undercount masked as zero
- PERF-003: GitHub rate limit (60 req/hr) silently returns null → stale ecosystem size
- TEST-006: query_official_plugins no error response validation
- QUAL-001: data-raw holds mixed format (numeric + text) → two consumers with incompatible expectations
- QUAL-002: No JSON schema → type errors only caught at browser runtime
- COMP-001: CRIT-001 (ID verification) was in pre-mortem but never implemented
- QA-001: No success acceptance criteria — can't determine if dashboard is working
- QA-002: Step 3.8 operational checks are manual, not automated
- SEC-003: Chart.js CDN without SRI hash → supply chain risk

### MEDIUM
- PERF-004: `parseInt()` NaN case handled by `|| 0` but not explicit
- QUAL-003: Metric inflation (double-counting) acknowledged but no prevention action
- QUAL-004: Single `lastSuccessfulUpdate` timestamp — per-source freshness not tracked
- TEST-007: build_data_js strips totals but no integration test
- TEST-008: initKPIs malformed data-raw → silent 0 fallback
- TEST-009: --dry-run correctness untested
- TEST-010: Full pipeline (JSON→HTML→browser) not integration tested
- LOGIC-001: Kill criteria don't cover malformed data-raw ('N/A' string)
- LOGIC-002: Risk table reference error (Risk 9 in Step 4.5 doesn't exist in table)
- QA-003: Security grade fallback behavior undefined
- QA-004: Overlap threshold undefined — can't detect double-counting
- QA-005: data-raw format not validated by tests
