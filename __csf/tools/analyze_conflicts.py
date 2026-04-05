#!/usr/bin/env python3
"""
Analyze merge conflicts before they happen.
Detects incompatibilities and suggests resolutions.

Usage:
  python analyze_conflicts.py <source-branch> <target-branch>

Output:
  - Lists overlapping files
  - Analyzes compatibility (SAFE/RISKY/BLOCKED)
  - Extracts intent from commit messages
  - Suggests resolution strategies
"""

import subprocess
import sys
from pathlib import Path


def run(cmd: list, cwd=None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result


def get_commit_intent(commit_hash: str, repo: Path) -> str:
    """Extract intent from commit message."""
    result = run(
        ["git", "log", "-1", "--format=%B", commit_hash],
        cwd=repo
    )
    lines = result.stdout.strip().split('\n')

    # Extract WHY section if present
    intent = ""
    in_why = False
    for line in lines:
        if line.startswith("## WHY"):
            in_why = True
            continue
        if line.startswith("##") and in_why:
            break
        if in_why and line.strip():
            intent += line.strip() + " "

    if not intent:
        # Fallback to first line (subject)
        intent = lines[0] if lines and lines[0] else "No intent documented"

    return intent.strip()


def analyze_file(file: str, source: str, target: str, repo: Path) -> tuple[str, str, str]:
    """Analyze a single file's changes."""

    # Get merge base
    base = run(
        ["git", "merge-base", target, source],
        cwd=repo
    ).stdout.strip()

    # Get changes in target
    target_diff = run(
        ["git", "diff", f"{base}..{target}", "--", file],
        cwd=repo
    ).stdout.strip()

    # Get changes in source
    source_diff = run(
        ["git", "diff", f"{base}..{source}", "--", file],
        cwd=repo
    ).stdout.strip()

    # Count additions/deletions
    target_adds = len([line for line in target_diff.split('\n') if line.startswith('+')])
    source_adds = len([line for line in source_diff.split('\n') if line.startswith('+')])
    target_dels = len([line for line in target_diff.split('\n') if line.startswith('-')])
    source_dels = len([line for line in source_diff.split('\n') if line.startswith('-')])

    # Get intents from recent commits
    target_intent = ""
    source_intent = ""

    for branch in [target, source]:
        # Get most recent commit for this branch
        commit = run(
            ["git", "log", "-1", "--format=%H", branch],
            cwd=repo
        ).stdout.strip()

        if commit:
            intent = get_commit_intent(commit, repo)
            if branch == target:
                target_intent = intent
            else:
                source_intent = intent

    # Analyze compatibility based on changes and intents
    if target_adds > 0 and source_adds > 0:
        target_lower = target_intent.lower()
        source_lower = source_intent.lower()

        if "refactor" in target_lower and ("add" in source_lower or "feat" in source_lower):
            compat = "SAFE"
            reason = "One refactors, other adds. Can adapt new code to refactored structure."
            resolution = "Apply both changes. New feature added to refactored code."
        elif ("add" in source_lower or "feat" in source_lower) and ("add" in target_lower or "feat" in target_lower):
            compat = "SAFE"
            reason = "Both add independent features."
            resolution = "Include both features."
        elif "fix" in source_lower and "fix" in target_lower:
            compat = "RISKY"
            reason = "Both fix the same area differently. Need to verify both fixes are compatible."
            resolution = "Review both fixes. May need combined approach or one may supersede the other."
        else:
            compat = "RISKY"
            reason = "Both modify same logic. Need careful analysis."
            resolution = "Review both intents. May need hybrid approach or refactoring."
    elif target_dels > 0 and source_adds > 0:
        compat = "BLOCKED"
        reason = "Target deletes what source adds. Likely incompatible."
        resolution = "Determine if deletions are intentional or conflict with new features."
    elif source_dels > 0 and target_adds > 0:
        compat = "BLOCKED"
        reason = "Source deletes what target adds. Likely incompatible."
        resolution = "Determine if deletions are intentional or conflict with new features."
    else:
        compat = "SAFE"
        reason = "Changes in different areas or one-sided changes."
        resolution = "Apply both changes."

    return compat, reason, resolution


def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze_conflicts.py <source-branch> <target-branch>")
        sys.exit(1)

    source = sys.argv[1]
    target = sys.argv[2]
    repo = Path.cwd()

    # Get overlapping files
    result = run(
        ["git", "diff", "--name-only", f"{target}...{source}"],
        cwd=repo
    )

    overlapping = [f for f in result.stdout.strip().split('\n') if f]

    print(f"\n{'='*70}")
    print(f"CONFLICT ANALYSIS: {source} → {target}")
    print(f"{'='*70}\n")

    if not overlapping:
        print("No overlapping files. Merge is SAFE ✓\n")
        return

    verdicts = []
    for file in overlapping:
        compat, reason, resolution = analyze_file(file, source, target, repo)
        verdicts.append(compat)

        status_icon = "✓" if compat == "SAFE" else "⚠" if compat == "RISKY" else "✗"
        print(f"{status_icon} {file}")
        print(f"  Compatibility: {compat}")
        print(f"  Reason: {reason}")
        print(f"  Resolution: {resolution}\n")

    # Overall verdict
    overall = "BLOCKED" if "BLOCKED" in verdicts else \
              "RISKY" if "RISKY" in verdicts else \
              "SAFE"

    print(f"{'='*70}")
    print(f"OVERALL: {overall}")
    if overall == "SAFE":
        print("✓ Merge is safe to proceed")
    elif overall == "RISKY":
        print("⚠ Merge is possible but requires careful review")
    else:
        print("✗ Merge is blocked. Manual resolution required.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
