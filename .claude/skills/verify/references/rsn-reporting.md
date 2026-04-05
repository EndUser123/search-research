# RSN Report Generation

## Step 6: Generate RSN Report

Use `RSNFormatter` from `__lib.rsn_formatter` to output findings as Recommended Next Steps:

```python
from __lib.rsn_formatter import RSNFormatter, RSNFinding

formatter = RSNFormatter()
result = formatter.create_result(intent_summary="Verification of <target>")

# Add tier findings as RSNFinding entries
tier_findings = [
    RSNFinding(
        id="VERIFY-001",
        severity="HIGH",  # CRITICAL/HIGH for failures, MEDIUM/LOW for warnings
        message="Tier 1 (component tests) failed: 1/87 tests failing",
        file_ref="packages/search-research/tests/test_mcp_server.py:14",
        action_type="Manual",
        effort_minutes=5,
        domain="test",
    ),
    RSNFinding(
        id="VERIFY-002",
        severity="MEDIUM",
        message="Tier 1 test expectation bug: expects empty results but router falls back to web",
        file_ref="packages/search-research/tests/test_unified_router.py:810",
        action_type="Manual",
        effort_minutes=5,
        domain="test",
    ),
]

formatter.add_findings(result, tier_findings)
formatter.sort_all_sections(result)

# Render as text
print(formatter.render_text(result))
```

## RSN Output Format

```
Recommended Next Steps

1. Logical Gaps & Inconsistencies
   1a. [HIGH] Tier 1 (component tests) failed: 1/87 tests failing (tests/test_mcp_server.py:14)
   1b. [MEDIUM] Tier 1 test expectation bug: expects empty results but router falls back to web (tests/test_unified_router.py:810)

0 — Do ALL Recommended Next Steps
```

## Key Principles

- Only output RSN if issues found; if all tiers pass, simply state "Verification Complete: ALL TIERS PASS"
- Domain `test` routes to "Missing Obvious Actions / Best Practices" section
- Severity CRITICAL/HIGH routes to "Logical Gaps & Inconsistencies" section
- Include `file_ref` for traceability
- Include `effort_minutes` for each finding (default: 5 min for test fixes)
- Do NOT write to package-specific `.claude/analysis/` paths -- RSN is the completion report
