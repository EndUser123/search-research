"""
Guidance Generator - Investigation suggestions based on evidence depth
Uses existing investigation-ledger infrastructure
"""

import sys
from pathlib import Path
from typing import List

# Import existing ledger functions
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import calculate_confidence_ceiling, get_investigation_stats


def generate_guidance(error_type: str = None) -> List[str]:
    """
    Generate next-step suggestions based on current investigation depth.

    Uses existing calculate_confidence_ceiling() to determine gap.

    Returns:
        List of guidance strings
    """
    stats = get_investigation_stats()
    ceiling_info = calculate_confidence_ceiling()
    current_confidence = ceiling_info["ceiling"]

    guidance = []

    # Determine gap to target (75% for Tier 3)
    target_confidence = 75
    gap = target_confidence - current_confidence

    if gap <= 0:
        guidance.append("✅ Confidence sufficient for /rca analysis")
        return guidance

    # Generate guidance based on what'''s been investigated
    files_read = stats["files_read"]
    searches = stats["searches"]
    executions = stats["executions"]

    if files_read == 0:
        if error_type == "python_exception":
            guidance.append(f"🔍 Read the file mentioned in the traceback (gap: {gap}%)")
            guidance.append("   Look for the line number in the error message")
        elif error_type == "import_error":
            guidance.append(f"🔍 Check requirements.txt or pyproject.toml (gap: {gap}%)")
            guidance.append("   Verify the module is listed as a dependency")
        elif error_type == "file_concurrency_error":
            guidance.append(f"🔍 Read the file operation code (gap: {gap}%)")
            guidance.append("   Check for atomic_write usage")
        else:
            guidance.append(f"🔍 Read the source file involved in the error (gap: {gap}%)")

    elif files_read == 1:
        guidance.append(f"🔍 Trace the function call chain (gap: {gap}%)")
        guidance.append("   Check where the problematic value originated")
        if error_type == "python_exception":
            guidance.append("   Look for the variable assignment before the error")

    elif searches == 0:
        guidance.append(f"🔍 Search for similar error patterns (gap: {gap}%)")
        guidance.append("   Use /grep to find similar error handling")

    elif executions == 0:
        guidance.append(f"🔍 Reproduce the error to verify conditions (gap: {gap}%)")
        guidance.append("   Run the command again to observe consistent behavior")

    else:
        guidance.append(f"🔍 Cross-reference findings (gap: {gap}%)")
        guidance.append("   Use /search to check CKS for similar incidents")

    # Add tier-based guidance
    if current_confidence == 0:
        guidance.insert(0, "⚠️ No investigation performed. Start by reading error context.")
    elif current_confidence == 50:
        guidance.append("📊 Current: Tier 4 (minimal evidence). Need 2+ sources.")
    elif current_confidence == 75:
        guidance.append("📊 Current: Tier 3 (moderate evidence). Ready for /rca.")

    return guidance


def format_guidance_for_display(guidance: List[str]) -> str:
    """Format guidance list for console display"""
    if not guidance:
        return "No specific guidance available. Proceed with investigation."

    return "\n".join(guidance)
