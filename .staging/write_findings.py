#!/usr/bin/env python3
"""Write adversarial findings to JSON files."""

import json

security_data = [
    {
        "id": "SEC-007",
        "severity": "MEDIUM",
        "title": "SSRF bypass via URL encoding and obfuscation",
        "description": "The SSRF validation in _validate_url() does not handle URL encoding, IPv6 alternative representations, or DNS rebinding attacks. The code admits this vulnerability in lines 68-71 but treats it as acceptable for solo-dev.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 106},
        "confidence": 85
    },
    {
        "id": "SEC-008",
        "severity": "MEDIUM",
        "title": "Error information disclosure in SSRF validation",
        "description": "The SSRF validation logs specific URLs that are blocked in logger.warning() calls. These logs may be accessible to attackers through log injection or log exposure vulnerabilities.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 122},
        "confidence": 70
    },
    {
        "id": "SEC-009",
        "severity": "LOW",
        "title": "Missing timeout enforcement on asyncio.gather",
        "description": "While individual HTTP requests have a timeout via httpx.AsyncClient, the asyncio.gather() call in search() has no overall timeout.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 315},
        "confidence": 65
    },
    {
        "id": "SEC-010",
        "severity": "LOW",
        "title": "Content-Length header validation bypass via missing header",
        "description": "The response size validation checks Content-Length header but does not handle cases where the header is missing, tampered with, or incorrectly specified.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 232},
        "confidence": 90
    }
]

performance_data = [
    {
        "id": "PERF-001",
        "severity": "MEDIUM",
        "title": "Inefficient IP network containment checks in SSRF validation",
        "description": "The _validate_url method uses ip in ipaddress.ip_network() which is O(n) for each network check. With 8 network checks performed on every URL validation (lines 138-181), this creates unnecessary CPU overhead.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 138},
        "confidence": 95
    },
    {
        "id": "PERF-002",
        "severity": "MEDIUM",
        "title": "Redundant ipaddress.ip_address() parsing for IPv6 comparisons",
        "description": "Multiple calls to ipaddress.ip_address() constructor for the same literal values (lines 164, 169, 174, 179). These should be module-level constants.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 164},
        "confidence": 100
    }
]

quality_data = [
    {
        "id": "QUAL-001",
        "severity": "HIGH",
        "title": "Inconsistent return type annotation for _fetch_single_url",
        "description": "The method _fetch_single_url has a return type annotation SearchResult | None, but line 283 returns SearchResult in the exception handler. The line 269 also returns None when content exceeds max_response_size.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 247},
        "confidence": 85
    },
    {
        "id": "QUAL-002",
        "severity": "MEDIUM",
        "title": "Code duplication in SSRF IP validation blocks",
        "description": "Lines 137-181 contain repetitive code blocks for IP address validation. This violates DRY and makes maintenance error-prone.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 137},
        "confidence": 95
    },
    {
        "id": "QUAL-003",
        "severity": "MEDIUM",
        "title": "Inconsistent error handling in _fetch_single_url",
        "description": "The method returns None when content exceeds max_response_size (line 269), but returns a SearchResult with error metadata when other failures occur (line 285-294).",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 267},
        "confidence": 90
    }
]

testing_data = [
    {
        "id": "TEST-001",
        "severity": "CRITICAL",
        "title": "Missing DNS rebinding integration test coverage",
        "description": "While test_webreader_dns_rebinding.py documents the vulnerability as a characterization test, there is no actual integration test that verifies the DNS rebinding mitigation works end-to-end.",
        "evidence": {"file": "P:/__csf/src/research/providers/test_webreader_dns_rebinding.py", "line": 54},
        "confidence": 95
    },
    {
        "id": "TEST-002",
        "severity": "HIGH",
        "title": "Missing property-based testing for URL validation edge cases",
        "description": "The SSRF validation tests use hardcoded examples but do not test edge cases like malformed URLs, IP address variations, or boundary conditions systematically.",
        "evidence": {"file": "P:/__csf/src/research/providers/test_webreader_ssrf.py", "line": 25},
        "confidence": 90
    },
    {
        "id": "TEST-005",
        "severity": "MEDIUM",
        "title": "Missing test for HTTP redirect chain SSRF bypass",
        "description": "The code uses follow_redirects=True (line 228). Tests do not verify that redirect targets are also validated against SSRF rules.",
        "evidence": {"file": "P:/__csf/src/research/providers/webreader_mcp.py", "line": 228},
        "confidence": 92
    }
]

base_dir = "P:/.claude/state/v_findings/fallback_1"
changed_files = ["P:/__csf/src/research/providers/webreader_mcp.py"]

# Wrap each finding set with metadata
security_wrapper = {"findings": security_data, "changed_files": changed_files}
performance_wrapper = {"findings": performance_data, "changed_files": changed_files}
quality_wrapper = {"findings": quality_data, "changed_files": changed_files}
testing_wrapper = {"findings": testing_data, "changed_files": changed_files}

with open(f"{base_dir}/adversarial-security-fallback_1.json", "w") as f:
    json.dump(security_wrapper, f, indent=2)

with open(f"{base_dir}/adversarial-performance-fallback_1.json", "w") as f:
    json.dump(performance_wrapper, f, indent=2)

with open(f"{base_dir}/adversarial-quality-fallback_1.json", "w") as f:
    json.dump(quality_wrapper, f, indent=2)

with open(f"{base_dir}/adversarial-testing-fallback_1.json", "w") as f:
    json.dump(testing_wrapper, f, indent=2)

print("All adversarial findings written to JSON files with wrapper format")
