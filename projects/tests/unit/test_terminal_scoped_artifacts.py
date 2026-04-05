#!/usr/bin/env python3
"""
Test terminal-scoped artifact isolation.

Verifies:
1. Artifacts created in one terminal only show in that terminal
2. Clearing artifacts in one terminal doesn't affect other terminals
3. The query logic matches statusline.ps1 behavior

Usage:
    python tests/test_terminal_scoped_artifacts.py
    python tests/test_terminal_scoped_artifacts.py --cleanup=false  # Keep test data
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "__csf" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))

DB_PATH = Path("P:/.claude/artifacts.db")
PROJECT_ROOT = "P:/projects/test-terminal-scoping"

# Test terminal IDs (simulated)
TERM_1 = "test_terminal_abc123"
TERM_2 = "test_terminal_xyz789"


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}")


def print_test(name: str, passed: bool, detail: str = "") -> bool:
    """Print a test result and return the pass status."""
    status = (
        f"{Colors.GREEN}✓ PASS{Colors.RESET}"
        if passed
        else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    )
    print(f"{status}: {name}")
    if detail:
        print(f"      {Colors.YELLOW}{detail}{Colors.RESET}")
    return passed


def init_database() -> bool:
    """Ensure database exists with terminal_id column."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if terminal_id column exists
        cursor.execute("PRAGMA table_info(artifact_status)")
        columns = cursor.fetchall()
        has_terminal_id = any(col[1] == "terminal_id" for col in columns)

        conn.close()

        if has_terminal_id:
            print("✓ terminal_id column exists")
            return True
        else:
            print("✗ terminal_id column missing from artifact_status table")
            return False

    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False


def create_test_artifact(
    terminal_id: str, item_id: str, severity: str = "standard"
) -> bool:
    """Create a test artifact with specified terminal_id."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create pending item
        cursor.execute(
            """
            INSERT OR REPLACE INTO pending_items
            (item_id, project_root, summary, change_type, severity, files_changed, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item_id,
                PROJECT_ROOT,
                f"Test artifact for {terminal_id}",
                "feature",
                severity,
                '["test_file.py"]',
                "test",
            ),
        )

        pending_item_id = cursor.lastrowid

        # Create artifact_status with terminal_id
        cursor.execute(
            """
            INSERT OR REPLACE INTO artifact_status
            (pending_item_id, artifact_type, status, terminal_id)
            VALUES (?, ?, ?, ?)
        """,
            (pending_item_id, "prd", "pending", terminal_id),
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"✗ Error creating artifact {item_id}: {e}")
        return False


def count_visible_artifacts(terminal_id: str | None = None) -> int:
    """
    Count artifacts visible to a specific terminal.

    This matches the EXACT query logic from statusline.ps1:
    WHERE (a.terminal_id IS NULL OR a.terminal_id = 'global' OR a.terminal_id = ?)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if terminal_id:
            # Statusline query logic: terminal_id matches, is NULL, or is 'global'
            cursor.execute(
                """
                SELECT COUNT(DISTINCT p.id)
                FROM pending_items p
                WHERE EXISTS (
                    SELECT 1 FROM artifact_status a
                    WHERE a.pending_item_id = p.id
                    AND a.status IN ('pending', 'confirm')
                    AND (a.terminal_id IS NULL OR a.terminal_id = 'global' OR a.terminal_id = ?)
                )
            """,
                (terminal_id,),
            )
        else:
            # Count all pending artifacts regardless of terminal
            cursor.execute(
                """
                SELECT COUNT(DISTINCT p.id)
                FROM pending_items p
                WHERE EXISTS (
                    SELECT 1 FROM artifact_status a
                    WHERE a.pending_item_id = p.id
                    AND a.status IN ('pending', 'confirm')
                )
            """
            )

        count = cursor.fetchone()[0]
        conn.close()
        return count

    except Exception as e:
        print(f"✗ Error querying artifacts: {e}")
        return -1


def clear_artifacts_for_terminal(terminal_id: str) -> int:
    """Clear artifacts for a specific terminal (mimics clear-artifacts.py)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE artifact_status
            SET status = 'done'
            WHERE terminal_id = ?
            AND status IN ('pending', 'confirm')
        """,
            (terminal_id,),
        )

        cleared = cursor.rowcount
        conn.commit()
        conn.close()

        return cleared

    except Exception as e:
        print(f"✗ Error clearing artifacts: {e}")
        return -1


def cleanup_test_artifacts() -> None:
    """Remove all test artifacts from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete artifact_status entries for test terminals
        cursor.execute(
            """
            DELETE FROM artifact_status
            WHERE terminal_id IN (?, ?)
        """,
            (TERM_1, TERM_2),
        )

        # Delete pending_items entries for test items
        cursor.execute(
            """
            DELETE FROM pending_items
            WHERE item_id LIKE 'TSK-TEST-%'
        """
        )

        conn.commit()
        conn.close()
        print(f"\n{Colors.CYAN}Cleaned up test artifacts{Colors.RESET}")

    except Exception as e:
        print(f"✗ Error cleaning up: {e}")


def run_tests(cleanup: bool = True) -> bool:
    """Run all terminal-scoping tests."""
    print_header("Terminal-Scoped Artifact Isolation Test")

    # Initialize
    print_header("Phase 1: Database Check")
    if not init_database():
        print(
            f"{Colors.RED}✗ Cannot proceed without proper database schema{Colors.RESET}"
        )
        return False

    # Cleanup any leftover test artifacts first
    cleanup_test_artifacts()

    # Create test artifacts
    print_header("Phase 2: Create Test Artifacts")
    created = []
    created.append(create_test_artifact(TERM_1, "TSK-TEST-001", "critical"))
    created.append(create_test_artifact(TERM_1, "TSK-TEST-002", "standard"))
    created.append(create_test_artifact(TERM_2, "TSK-TEST-003", "critical"))
    created.append(create_test_artifact(TERM_2, "TSK-TEST-004", "low"))

    if not all(created):
        print(f"{Colors.RED}✗ Failed to create test artifacts{Colors.RESET}")
        return False

    # Verify creation
    total = count_visible_artifacts(None)
    term1_count = count_visible_artifacts(TERM_1)
    term2_count = count_visible_artifacts(TERM_2)

    # Test terminal isolation (query phase)
    print_header("Phase 3: Verify Terminal Isolation")
    all_passed = True

    all_passed &= print_test(
        "Total artifacts created", total == 4, f"Expected 4, got {total}"
    )

    all_passed &= print_test(
        f"Terminal 1 ({TERM_1}) sees 2 artifacts",
        term1_count == 2,
        f"Expected 2, got {term1_count}",
    )

    all_passed &= print_test(
        f"Terminal 2 ({TERM_2}) sees 2 artifacts",
        term2_count == 2,
        f"Expected 2, got {term2_count}",
    )

    # Cross-verify isolation
    # Each terminal should NOT see the other's artifacts
    all_passed &= print_test(
        "Terminals don't see each other's artifacts",
        term1_count == 2 and term2_count == 2 and total == 4,
        "Each terminal isolated",
    )

    # Clear Terminal 1 artifacts
    print_header("Phase 4: Clear Terminal 1 Artifacts")
    cleared = clear_artifacts_for_terminal(TERM_1)
    all_passed &= print_test(
        "Cleared Terminal 1 artifacts",
        cleared == 2,
        f"Expected 2 cleared, got {cleared}",
    )

    # Verify isolation after clear
    print_header("Phase 5: Verify Isolation After Clear")
    term1_after = count_visible_artifacts(TERM_1)
    term2_after = count_visible_artifacts(TERM_2)
    total_after = count_visible_artifacts(None)

    all_passed &= print_test(
        "Terminal 1 now sees 0 artifacts",
        term1_after == 0,
        f"Expected 0, got {term1_after}",
    )

    all_passed &= print_test(
        "Terminal 2 still sees 2 artifacts",
        term2_after == 2,
        f"Expected 2, got {term2_after}",
    )

    all_passed &= print_test(
        "Total remaining: 2 artifacts",
        total_after == 2,
        f"Expected 2, got {total_after}",
    )

    all_passed &= print_test(
        "Clear Terminal 1 didn't affect Terminal 2",
        term1_after == 0 and term2_after == 2,
        "Isolation maintained",
    )

    # Clear Terminal 2 artifacts
    print_header("Phase 6: Clear Terminal 2 Artifacts")
    cleared2 = clear_artifacts_for_terminal(TERM_2)
    all_passed &= print_test(
        "Cleared Terminal 2 artifacts",
        cleared2 == 2,
        f"Expected 2 cleared, got {cleared2}",
    )

    # Final verification
    print_header("Phase 7: Final Verification")
    final_count = count_visible_artifacts(None)
    final_term1 = count_visible_artifacts(TERM_1)
    final_term2 = count_visible_artifacts(TERM_2)

    all_passed &= print_test(
        "All terminals see 0 artifacts",
        final_count == 0 and final_term1 == 0 and final_term2 == 0,
        f"All: {final_count}, Term1: {final_term1}, Term2: {final_term2}",
    )

    # Summary
    print_header("Test Summary")
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}")

    # Cleanup
    if cleanup:
        cleanup_test_artifacts()
    else:
        print(
            f"\n{Colors.YELLOW}Test artifacts left in database for inspection{Colors.RESET}"
        )
        print(f"Terminal 1: {TERM_1}")
        print(f"Terminal 2: {TERM_2}")

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Test terminal-scoped artifact isolation"
    )
    parser.add_argument(
        "--cleanup",
        choices=["true", "false"],
        default="true",
        help="Whether to remove test artifacts after completion (default: true)",
    )
    args = parser.parse_args()

    cleanup = args.cleanup.lower() == "true"
    success = run_tests(cleanup=cleanup)

    return 0 if success else 1


@pytest.mark.unit
def test_terminal_scoping():
    """Pytest wrapper for terminal scoping tests."""
    assert run_tests(cleanup=True) is True


if __name__ == "__main__":
    sys.exit(main())
