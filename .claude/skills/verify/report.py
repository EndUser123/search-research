#!/usr/bin/env python3
"""
Verification report generator.

Generates markdown and JSON reports from verification results.
"""

import json
from datetime import datetime
from typing import Any, Dict


class VerificationReport:
    """Generate verification reports in multiple formats."""

    def generate_markdown(self, report_data: Dict[str, Any]) -> str:
        """
        Generate markdown report.

        Args:
            report_data: Verification report data from Verifier.verify()

        Returns:
            Markdown formatted report
        """
        lines = [
            "[VERIFY] Verification Report",
            "",
            f"**Target**: {report_data.get('target', 'unknown')}",
            f"**Date**: {datetime.now().isoformat()}",
            f"**Verification ID**: {report_data.get('verification_id', 'unknown')}",
            "",
            "## Overall Status",
            "",
        ]

        overall_status = report_data.get("overall_status", "unknown")
        if overall_status == "verified":
            lines.append("**Overall Status**: ✅ VERIFIED")
        else:
            lines.append("**Overall Status**: ❌ FAILED")

        lines.append("")

        # Tier results
        for tier_num in ["tier1", "tier2", "tier3"]:
            tier = report_data.get(tier_num, {})
            status = tier.get("status", "unknown")

            if status == "pass":
                lines.append(f"**{tier_num.upper()}**: ✅ PASS")
            elif status == "fail":
                lines.append(f"**{tier_num.upper()}**: ❌ FAIL")
            elif status == "skip":
                lines.append(f"**{tier_num.upper()}**: ⏭️  SKIP")
            else:
                lines.append(f"**{tier_num.upper()}**: ❓ {status.upper()}")

            lines.append("")

        # Evidence section
        lines.extend(["## Tier Evidence", ""])

        for tier_num in ["tier1", "tier2", "tier3"]:
            tier = report_data.get(tier_num, {})
            lines.append(f"### {tier_num.upper()}")
            lines.append("")

            status = tier.get("status", "unknown")
            evidence = tier.get("evidence", "")

            lines.append(f"**Status**: {status}")
            lines.append("**Evidence**:")
            lines.append("```")
            lines.append(evidence[:500])  # Truncate long evidence
            lines.append("```")
            lines.append("")

            # Include command if available (Tier 1)
            if tier_num == "tier1" and "command" in tier:
                lines.append(f"**Command**: `{tier['command']}`")
                lines.append("")

        # Issues found
        if "tier_mismatch" in report_data:
            lines.extend(
                [
                    "## Issues Found",
                    "",
                    "### Tier Mismatch Detected",
                    "",
                    f"Component tests pass but integration fails: {', '.join(report_data['tier_mismatch'])}",
                    "",
                    "**Recommendation**: Check hook registration and router configuration",
                    "",
                ]
            )

        # Recommended Next Steps (GTO format)
        lines.extend(["", "**Recommended Next Steps**", ""])

        if overall_status == "verified":
            lines.extend(
                [
                    "No next steps required - all verification tiers passed.",
                    "",
                    "0 - Verification complete",
                ]
            )
        else:
            # Generate recommended next steps based on failures
            step_num = 1

            # Tier 1 failures - component tests
            if report_data.get("tier1", {}).get("status") == "fail":
                lines.extend(
                    [
                        f"{step_num} (Testing) - Fix component test failures",
                        f"  {step_num}a: Review test output → Manual check - Analyze failing tests in report above",
                        f"  {step_num}b: Run tests with verbose output → Manual check - pytest tests/ -v for details",
                        "",
                    ]
                )
                step_num += 1

            # Tier 2 failures - integration issues
            if report_data.get("tier2", {}).get("status") == "fail":
                lines.extend(
                    [
                        f"{step_num} (Integration) - Fix integration issues",
                        f"  {step_num}a: Check hook registration → Manual check - Verify hooks are registered in router",
                        f"  {step_num}b: Test hook chain → Manual check - Verify hook chain executes",
                        "",
                    ]
                )
                step_num += 1

            # Always suggest /uci for deeper analysis
            lines.extend(
                [
                    f"{step_num} (Code Quality) - Multi-dimensional code analysis",
                    f"  {step_num}a: Run unified code inspection → Use `/uci` - Multi-dimensional code analysis",
                    "",
                ]
            )
            step_num += 1

            lines.extend(["0 - Do ALL Recommended Next Steps", ""])

        return "\n".join(lines)

    def generate_json(self, report_data: Dict[str, Any]) -> str:
        """
        Generate JSON report.

        Args:
            report_data: Verification report data from Verifier.verify()

        Returns:
            JSON formatted report
        """
        return json.dumps(report_data, indent=2)
