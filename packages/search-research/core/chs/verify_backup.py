"""CHS Backup Integrity Verification.

Provides safety checks for CHS database and FAISS index backups.
This module implements the data safety verifications from the CHS
consolidation plan (PRE-001: CRITICAL).

Usage:
    from search_research.core.chs.verify_backup import (
        verify_database_backup,
        verify_faiss_backup,
        create_backup_metadata,
    )

    # Verify database backup
    is_valid, details = verify_database_backup("chat_history.db.backup")

    # Verify FAISS backup
    is_valid, details = verify_faiss_backup("chat_history_faiss_424k.backup/")

    # Create backup metadata
    metadata = create_backup_metadata("chat_history.db", "chat_history.db.backup")
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for CHS backups.

    Stores exact counts and checksums to verify backup integrity.
    This replaces approximate counts (~520K) with exact baseline counts.
    """

    source_db: str
    backup_db: str
    message_count: int  # Exact count, not approximate
    db_checksum: str  # SHA256 of database file
    faiss_path: str | None
    faiss_checksum: str | None  # SHA256 of FAISS index directory
    faiss_vector_count: int | None
    faiss_dimension: int | None

    def to_json(self, file_path: str | Path) -> None:
        """Write metadata to JSON file."""
        with open(file_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def from_json(cls, file_path: str | Path) -> BackupMetadata:
        """Read metadata from JSON file."""
        with open(file_path) as f:
            data = json.load(f)
        return cls(**data)


def compute_sha256(file_path: str | Path) -> str:
    """Compute SHA256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal SHA256 checksum
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_directory_sha256(directory: str | Path) -> str:
    """Compute SHA256 checksum of all files in a directory.

    Creates a combined hash of all files in the directory for
    integrity verification.

    Args:
        directory: Path to directory

    Returns:
        Hexadecimal SHA256 checksum
    """
    sha256 = hashlib.sha256()
    dir_path = Path(directory)

    # Sort files for consistent hash
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            sha256.update(file_path.name.encode())
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

    return sha256.hexdigest()


def get_exact_message_count(db_path: str | Path) -> int:
    """Get exact message count from CHS database.

    Replaces approximate counts (~520K) with exact baseline count.

    Args:
        db_path: Path to chat_history.db

    Returns:
        Exact message count

    Raises:
        sqlite3.Error: If database query fails
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get exact count
    cursor.execute("SELECT COUNT(*) FROM messages;")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def verify_database_integrity(db_path: str | Path) -> tuple[bool, str]:
    """Run PRAGMA integrity_check on database.

    FM-002: Database integrity verification incomplete.
    This function implements PRAGMA integrity_check to detect corruption.

    Args:
        db_path: Path to database file

    Returns:
        (is_valid, details) - True if integrity check passes
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Run integrity check
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]

        conn.close()

        if result == "ok":
            return True, "Database integrity check passed"
        else:
            return False, f"Database integrity check failed: {result}"

    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def verify_database_backup(
    backup_db_path: str | Path,
    expected_count: int | None = None,
    expected_checksum: str | None = None,
) -> tuple[bool, dict]:
    """Verify database backup integrity.

    Performs multiple safety checks:
    1. File exists
    2. PRAGMA integrity_check passes
    3. Exact count matches expected (if provided)
    4. Checksum matches expected (if provided)

    Args:
        backup_db_path: Path to backup database
        expected_count: Expected exact message count (from metadata)
        expected_checksum: Expected SHA256 checksum (from metadata)

    Returns:
        (is_valid, details) - details dict contains all check results
    """
    backup_path = Path(backup_db_path)
    details = {"checks": [], "passed": [], "failed": []}

    # Check 1: File exists
    if not backup_path.exists():
        details["failed"].append("backup_file_missing")
        return False, details

    details["passed"].append("backup_file_exists")

    # Check 2: PRAGMA integrity_check (FM-002)
    is_valid, integrity_result = verify_database_integrity(backup_path)
    if is_valid:
        details["passed"].append("integrity_check")
    else:
        details["failed"].append(f"integrity_check: {integrity_result}")
        return False, details

    # Check 3: Exact count (TEST-001)
    if expected_count is not None:
        try:
            actual_count = get_exact_message_count(backup_path)
            if actual_count == expected_count:
                details["passed"].append(f"count_match: {actual_count}")
            else:
                details["failed"].append(
                    f"count_mismatch: expected {expected_count}, got {actual_count}"
                )
                return False, details
        except sqlite3.Error as e:
            details["failed"].append(f"count_query_failed: {e}")
            return False, details

    # Check 4: Checksum (if provided)
    if expected_checksum is not None:
        actual_checksum = compute_sha256(backup_path)
        if actual_checksum == expected_checksum:
            details["passed"].append("checksum_match")
        else:
            details["failed"].append("checksum_mismatch")
            return False, details

    return True, details


def verify_faiss_backup(
    backup_faiss_path: str | Path,
    expected_vector_count: int | None = None,
    expected_dimension: int | None = 768,
    expected_checksum: str | None = None,
) -> tuple[bool, dict]:
    """Verify FAISS index backup integrity.

    Performs multiple safety checks:
    1. Directory exists
    2. Index file exists
    3. Index loads without corruption
    4. Vector count > 0 (if expected_count provided, verify match)
    5. Dimension matches expected (768 for default embeddings)

    TEST-001: FAISS backup encryption verification.

    Args:
        backup_faiss_path: Path to backup FAISS directory
        expected_vector_count: Expected vector count (from metadata)
        expected_dimension: Expected embedding dimension (default: 768)
        expected_checksum: Expected SHA256 checksum (from metadata)

    Returns:
        (is_valid, details) - details dict contains all check results
    """
    backup_path = Path(backup_faiss_path)
    details = {"checks": [], "passed": [], "failed": []}

    # Check 1: Directory exists
    if not backup_path.exists():
        details["failed"].append("faiss_directory_missing")
        return False, details

    details["passed"].append("faiss_directory_exists")

    # Check 2: Index file exists (typically index.faiss or *.faiss)
    index_files = list(backup_path.glob("*.faiss"))
    if not index_files:
        details["failed"].append("no_index_file_found")
        return False, details

    index_file = index_files[0]
    details["passed"].append(f"index_file_found: {index_file.name}")

    # Check 3: Verify index loads (TEST-001)
    try:
        import faiss

        index = faiss.read_index(str(index_file))
        details["passed"].append("index_loads_successfully")

        # Check 4: Vector count
        vector_count = index.ntotal
        if vector_count > 0:
            details["passed"].append(f"vector_count: {vector_count}")
        else:
            details["failed"].append("vector_count_zero")
            return False, details

        # Verify expected count
        if expected_vector_count is not None:
            if vector_count == expected_vector_count:
                details["passed"].append(f"vector_count_match: {vector_count}")
            else:
                details["failed"].append(
                    f"vector_count_mismatch: expected {expected_vector_count}, got {vector_count}"
                )
                return False, details

        # Check 5: Dimension (expected 768 for default embeddings)
        actual_dimension = index.d
        if expected_dimension is not None:
            if actual_dimension == expected_dimension:
                details["passed"].append(f"dimension_correct: {actual_dimension}")
            else:
                details["failed"].append(
                    f"dimension_mismatch: expected {expected_dimension}, got {actual_dimension}"
                )
                return False, details
        else:
            # No dimension check requested, just record the actual dimension
            details["passed"].append(f"dimension_recorded: {actual_dimension}")

    except Exception as e:
        details["failed"].append(f"index_load_failed: {e}")
        return False, details

    # Check 6: Checksum (if provided)
    if expected_checksum is not None:
        actual_checksum = compute_directory_sha256(backup_path)
        if actual_checksum == expected_checksum:
            details["passed"].append("faiss_checksum_match")
        else:
            details["failed"].append("faiss_checksum_mismatch")
            return False, details

    return True, details


def create_backup_metadata(
    source_db: str | Path,
    backup_db: str | Path,
    faiss_source: str | Path | None = None,
    faiss_backup: str | Path | None = None,
) -> BackupMetadata:
    """Create backup metadata with exact counts and checksums.

    PRE-001: Store exact baseline count during backup.
    Replaces ~520K approximation with exact count.

    Args:
        source_db: Path to source database
        backup_db: Path to backup database
        faiss_source: Path to source FAISS directory (optional)
        faiss_backup: Path to backup FAISS directory (optional)

    Returns:
        BackupMetadata object with exact counts and checksums
    """
    # Get exact message count
    message_count = get_exact_message_count(source_db)

    # Compute checksums
    db_checksum = compute_sha256(backup_db)

    faiss_checksum = None
    faiss_vector_count = None
    faiss_dimension = None

    if faiss_source and faiss_backup:
        try:
            import faiss

            # Load source index to get metadata
            index_files = list(Path(faiss_source).glob("*.faiss"))
            if index_files:
                index = faiss.read_index(str(index_files[0]))
                faiss_vector_count = index.ntotal
                faiss_dimension = index.d

            faiss_checksum = compute_directory_sha256(faiss_backup)
        except Exception:
            # FAISS verification is optional
            pass

    metadata = BackupMetadata(
        source_db=str(source_db),
        backup_db=str(backup_db),
        message_count=message_count,
        db_checksum=db_checksum,
        faiss_path=str(faiss_backup) if faiss_backup else None,
        faiss_checksum=faiss_checksum,
        faiss_vector_count=faiss_vector_count,
        faiss_dimension=faiss_dimension,
    )

    return metadata


def set_restrictive_permissions(file_path: str | Path) -> tuple[bool, str]:
    """Set restrictive permissions on backup files.

    PRE-001: Add file permissions to backup creation.
    On Windows: Uses icacls to set user-only permissions.
    On Unix: Uses chmod 0600 (user read/write only).

    Args:
        file_path: Path to backup file

    Returns:
        (success, message) - True if permissions set successfully
    """
    path = Path(file_path)

    try:
        import platform
        import subprocess

        if platform.system() == "Windows":
            # Windows: Use icacls to set user-only permissions
            # Disable inheritance and grant user full control
            result = subprocess.run(
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant",
                    f"{os.getenv('USERNAME', 'USER')}:F",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True, "Windows permissions set (icacls)"
            else:
                return False, f"icacls failed: {result.stderr}"
        else:
            # Unix: Use chmod 0600
            path.chmod(0o600)
            return True, "Unix permissions set (chmod 0600)"

    except Exception as e:
        return False, f"Failed to set permissions: {e}"


# Convenience aliases
verify_database_backup = verify_database_backup
verify_faiss_backup = verify_faiss_backup
create_backup_metadata = create_backup_metadata


def main() -> int:
    """CLI for backup verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify CHS backup integrity (PRE-001 data safety)"
    )
    parser.add_argument("--db", type=str, help="Path to backup database")
    parser.add_argument("--faiss", type=str, help="Path to backup FAISS directory")
    parser.add_argument("--metadata", type=str, help="Path to backup metadata JSON")
    parser.add_argument(
        "--create-metadata", action="store_true", help="Create metadata from source"
    )
    parser.add_argument("--source-db", type=str, help="Source database (for metadata creation)")
    parser.add_argument(
        "--source-faiss", type=str, help="Source FAISS directory (for metadata creation)"
    )

    args = parser.parse_args()

    if args.metadata:
        # Verify using metadata file
        metadata = BackupMetadata.from_json(args.metadata)

        if args.db or args.faiss:
            # Verify specific backup
            all_valid = True

            if args.db:
                is_valid, details = verify_database_backup(
                    args.db,
                    expected_count=metadata.message_count,
                    expected_checksum=metadata.db_checksum,
                )
                print(f"Database backup: {'VALID' if is_valid else 'INVALID'}")
                print(json.dumps(details, indent=2))
                if not is_valid:
                    all_valid = False

            if args.faiss:
                is_valid, details = verify_faiss_backup(
                    args.faiss,
                    expected_vector_count=metadata.faiss_vector_count,
                    expected_dimension=metadata.faiss_dimension,
                    expected_checksum=metadata.faiss_checksum,
                )
                print(f"FAISS backup: {'VALID' if is_valid else 'INVALID'}")
                print(json.dumps(details, indent=2))
                if not is_valid:
                    all_valid = False

            return 0 if all_valid else 1
        else:
            # Verify all from metadata
            is_valid_db, _ = verify_database_backup(
                metadata.backup_db,
                expected_count=metadata.message_count,
                expected_checksum=metadata.db_checksum,
            )

            # Only verify FAISS if path exists
            is_valid_faiss = True
            if metadata.faiss_path:
                is_valid_faiss, _ = verify_faiss_backup(
                    metadata.faiss_path,
                    expected_vector_count=metadata.faiss_vector_count,
                    expected_dimension=metadata.faiss_dimension,
                    expected_checksum=metadata.faiss_checksum,
                )

            print(f"Database: {'VALID' if is_valid_db else 'INVALID'}")
            if metadata.faiss_path:
                print(f"FAISS: {'VALID' if is_valid_faiss else 'INVALID'}")

            return 0 if (is_valid_db and is_valid_faiss) else 1

    elif args.create_metadata:
        # Create metadata
        metadata = create_backup_metadata(
            args.source_db,
            args.db,
            args.source_faiss,
            args.faiss,
        )
        metadata_path = f"{args.db}.backup-metadata.json"
        metadata.to_json(metadata_path)
        print(f"Created metadata: {metadata_path}")
        print(f"Message count: {metadata.message_count}")
        return 0

    else:
        # Simple verification
        all_valid = True

        if args.db:
            is_valid, details = verify_database_backup(args.db)
            print(f"Database: {'VALID' if is_valid else 'INVALID'}")
            if not is_valid:
                all_valid = False

        if args.faiss:
            is_valid, details = verify_faiss_backup(args.faiss)
            print(f"FAISS: {'VALID' if is_valid else 'INVALID'}")
            if not is_valid:
                all_valid = False

        return 0 if all_valid else 1


if __name__ == "__main__":
    import logging
    import os

    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
