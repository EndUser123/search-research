#!/usr/bin/env python3
"""
Measure verify-before-claiming protocol effectiveness.

Tracks:
- Skill compliance rate (how many skills reference protocol)
- Tool usage patterns (are Read/Grep/Bash used before absence claims)
- StopHook block rate (how many blocks per week)

Baseline: 2026-03-14 (protocol implementation date)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def count_skills_with_protocol():
    """Count how many skills reference verification_tiers.md protocol."""
    skills_dir = Path("P:/.claude/skills")
    packages_dir = Path("P:/packages")

    compliant_skills = []
    total_skills = 0

    # Check .claude/skills
    if skills_dir.exists():
        for skill_file in skills_dir.glob("*/SKILL.md"):
            total_skills += 1
            content = skill_file.read_text()
            if "verification_tiers.md" in content.lower():
                compliant_skills.append(skill_file.parent.name)

    # Check packages/*/
    if packages_dir.exists():
        for skill_file in packages_dir.glob("*/skill/SKILL.md"):
            total_skills += 1
            content = skill_file.read_text()
            if "verification_tiers.md" in content.lower():
                compliant_skills.append(skill_file.parent.parent.name)

    compliance_rate = (len(compliant_skills) / total_skills * 100) if total_skills > 0 else 0

    return {
        "total_skills": total_skills,
        "compliant_skills": len(compliant_skills),
        "compliance_rate": round(compliance_rate, 1),
        "compliant_skill_names": compliant_skills
    }


def count_absence_claim_checks():
    """Count how many skills have explicit absence claim verification steps."""
    keywords = [
        "verify.*absence",
        "check.*before.*claim",
        "search.*before.*stat",
        "Grep.*before.*claim",
        "Read.*before.*missing",
    ]

    skills_dir = Path("P:/.claude/skills")
    packages_dir = Path("P:/packages")

    skills_with_checks = 0
    total_skills = 0

    import re

    # Check .claude/skills
    if skills_dir.exists():
        for skill_file in skills_dir.glob("*/SKILL.md"):
            total_skills += 1
            content = skill_file.read_text()
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in keywords):
                skills_with_checks += 1

    # Check packages/*/
    if packages_dir.exists():
        for skill_file in packages_dir.glob("*/skill/SKILL.md"):
            total_skills += 1
            content = skill_file.read_text()
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in keywords):
                skills_with_checks += 1

    check_rate = (skills_with_checks / total_skills * 100) if total_skills > 0 else 0

    return {
        "total_skills": total_skills,
        "skills_with_checks": skills_with_checks,
        "check_rate": round(check_rate, 1)
    }


def analyze_recent_sessions(days=7):
    """Analyze recent sessions for absence claim patterns."""
    sessions_dir = Path("P:/.claude/sessions")

    if not sessions_dir.exists():
        return {"error": "Sessions directory not found"}

    cutoff_date = datetime.now() - timedelta(days=days)
    absence_claims = 0
    verified_claims = 0
    total_sessions = 0

    for session_file in sessions_dir.glob("*.json"):
        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            if mtime < cutoff_date:
                continue

            total_sessions += 1
            content = session_file.read_text()

            # Count absence claim patterns
            content_lower = content.lower()
            absence_patterns = [
                "doesn't exist",
                "does not exist",
                "no hook for",
                "missing",
                "lacks",
                "not implemented"
            ]

            for pattern in absence_patterns:
                if pattern in content_lower:
                    absence_claims += 1

                    # Check if preceded by tool usage indicators
                    # (simplified check - actual implementation would need conversation parsing)
                    if "grep" in content_lower[:content_lower.find(pattern)+500] or \
                       "read" in content_lower[:content_lower.find(pattern)+500]:
                        verified_claims += 1
                    break

        except Exception:
            pass

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "absence_claims": absence_claims,
        "verified_claims": verified_claims,
        "verification_rate": round((verified_claims / absence_claims * 100) if absence_claims > 0 else 0, 1)
    }


def generate_report():
    """Generate effectiveness report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "baseline_date": "2026-03-14",
        "metrics": {}
    }

    # Skill compliance
    print("Measuring skill compliance...")
    report["metrics"]["skill_compliance"] = count_skills_with_protocol()

    # Absence claim checks
    print("Measuring absence claim checks...")
    report["metrics"]["absence_claim_checks"] = count_absence_claim_checks()

    # Recent session analysis
    print("Analyzing recent sessions...")
    report["metrics"]["recent_sessions"] = analyze_recent_sessions(days=7)

    # Save report
    report_file = Path("P:/.claude/state/protocol_effectiveness_report.json")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("BASELINE REPORT: 2026-03-14")
    print("=" * 60)

    print("\nSkill Compliance:")
    print(f"  Total Skills: {report['metrics']['skill_compliance']['total_skills']}")
    print(f"  Compliant: {report['metrics']['skill_compliance']['compliant_skills']}")
    print(f"  Compliance Rate: {report['metrics']['skill_compliance']['compliance_rate']}%")

    print("\nAbsence Claim Checks:")
    print(f"  Total Skills: {report['metrics']['absence_claim_checks']['total_skills']}")
    print(f"  With Checks: {report['metrics']['absence_claim_checks']['skills_with_checks']}")
    print(f"  Check Rate: {report['metrics']['absence_claim_checks']['check_rate']}%")

    print("\nRecent Sessions (7 days):")
    if "error" not in report['metrics']['recent_sessions']:
        print(f"  Sessions Analyzed: {report['metrics']['recent_sessions']['total_sessions']}")
        print(f"  Absence Claims: {report['metrics']['recent_sessions']['absence_claims']}")
        print(f"  Verified Claims: {report['metrics']['recent_sessions']['verified_claims']}")
        print(f"  Verification Rate: {report['metrics']['recent_sessions']['verification_rate']}%")
    else:
        print(f"  {report['metrics']['recent_sessions']['error']}")

    print("\n" + "=" * 60)
    print(f"Report saved to: {report_file}")
    print("=" * 60)

    return report


if __name__ == "__main__":
    print("Generating Protocol Effectiveness Report...")
    print("=" * 60)

    report = generate_report()

    print("\n" + "=" * 60)
    print("BASELINE REPORT: 2026-03-14")
    print("=" * 60)

    print("\nSkill Compliance:")
    print(f"  Total Skills: {report['metrics']['skill_compliance']['total_skills']}")
    print(f"  Compliant: {report['metrics']['skill_compliance']['compliant_skills']}")
    print(f"  Compliance Rate: {report['metrics']['skill_compliance']['compliance_rate']}%")

    print("\nAbsence Claim Checks:")
    print(f"  Total Skills: {report['metrics']['absence_claim_checks']['total_skills']}")
    print(f"  With Checks: {report['metrics']['absence_claim_checks']['skills_with_checks']}")
    print(f"  Check Rate: {report['metrics']['absence_claim_checks']['check_rate']}%")

    print("\nRecent Sessions (7 days):")
    if "error" not in report['metrics']['recent_sessions']:
        print(f"  Sessions Analyzed: {report['metrics']['recent_sessions']['total_sessions']}")
        print(f"  Absence Claims: {report['metrics']['recent_sessions']['absence_claims']}")
        print(f"  Verified Claims: {report['metrics']['recent_sessions']['verified_claims']}")
        print(f"  Verification Rate: {report['metrics']['recent_sessions']['verification_rate']}%")
    else:
        print(f"  {report['metrics']['recent_sessions']['error']}")

    print("\n" + "=" * 60)
    print(f"Report saved to: {report_file}")
    print("=" * 60)
