#!/usr/bin/env python
"""Rollback script for TDD escalation pipeline migration.

This script rolls back migration 001, removing all escalation pipeline
tables from the database.

Usage:
    python rollback_escalation_pipeline.py <db_path>

Example:
    python rollback_escalation_pipeline.py .csf_nip_tdd_evidence.db
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def confirm_rollback(db_path: str | Path) -> bool:
    """Ask user to confirm rollback.

    Args:
        db_path: Path to the database

    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n⚠️  WARNING: This will rollback migration 001 on:")
    print(f"   {db_path}")
    print(f"\nThis will DELETE the following tables:")
    print("   - mutation_results")
    print("   - property_test_results")
    print("   - bdd_scenario_results")
    print("   - integration_test_results")
    print("   - pipeline_signals")
    print("\nThis action CANNOT be undone without reapplying the migration.\n")

    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    return response in ("yes", "y")


def main():
    """Main rollback function."""
    if len(sys.argv) < 2:
        print("Usage: python rollback_escalation_pipeline.py <db_path>")
        sys.exit(1)

    db_path = sys.argv[1]

    # Check if database exists
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    # Confirm rollback
    if not confirm_rollback(db_path):
        print("Rollback cancelled.")
        sys.exit(0)

    # Import and run rollback
    try:
        from src.core.tdd_hooks.migration_001_escalation_pipeline import rollback

        success = rollback(db_path)

        if success:
            print("\n✓ Rollback completed successfully")
            print("  All escalation pipeline tables have been removed.")
        else:
            print("\nℹ Rollback not needed or not applicable")
            print("  The migration may not have been applied.")

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
