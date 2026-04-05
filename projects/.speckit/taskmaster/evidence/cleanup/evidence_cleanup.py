#!/usr/bin/env python3
"""
Evidence Cleanup Manager
Automated cleanup of old evidence files with comprehensive logging and validation.

Provides:
- 3-day default retention with configurable periods
- Safe file deletion with validation
- Comprehensive cleanup statistics and logging
- Integration with TaskMaster task cleanup
"""

import asyncio
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EvidenceCleanupManager:
    """Manages automated cleanup of explore evidence files"""

    def __init__(self, evidence_path: str = "P:\\.speckit\\taskmaster\\evidence\\explore_findings", retention_days: int = 3):
        self.evidence_path = Path(evidence_path)
        self.retention_days = retention_days
        self.cleanup_log = self.evidence_path.parent / "cleanup" / "cleanup_{}.log".format(datetime.now().strftime("%Y-%m-%d"))

    async def cleanup_old_evidence(self, dry_run: bool = False) -> dict[str, Any]:
        """Automated cleanup of old evidence files"""

        cleanup_stats = {
            "start_time": datetime.now().isoformat(),
            "dry_run": dry_run,
            "retention_days": self.retention_days,
            "cutoff_date": (datetime.now() - timedelta(days=self.retention_days)).isoformat(),
            "files_removed": 0,
            "folders_removed": 0,
            "bytes_freed": 0,
            "errors": [],
            "warnings": [],
            "details": []
        }

        try:
            logger.info(f"Starting evidence cleanup (dry_run={dry_run}, retention_days={self.retention_days})")

            # Ensure evidence path exists
            if not self.evidence_path.exists():
                cleanup_stats["warnings"].append(f"Evidence path does not exist: {self.evidence_path}")
                return cleanup_stats

            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Process daily folders
            for item in self.evidence_path.iterdir():
                if item.is_dir():
                    await self._process_daily_folder(item, cutoff_date, cleanup_stats, dry_run)

            # Log cleanup summary
            await self._log_cleanup_summary(cleanup_stats)

            logger.info(f"Cleanup completed successfully: {cleanup_stats['files_removed']} files, {cleanup_stats['folders_removed']} folders removed")
            return cleanup_stats

        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            logger.error(error_msg)
            cleanup_stats["errors"].append(error_msg)
            return cleanup_stats

    async def _process_daily_folder(self, folder_path: Path, cutoff_date: datetime, stats: dict[str, Any], dry_run: bool):
        """Process a single daily evidence folder"""

        try:
            # Extract date from folder name
            folder_name = folder_path.name
            try:
                folder_date = datetime.strptime(folder_name, "%Y-%m-%d")
            except ValueError:
                # Skip folders that don't match date format
                stats["warnings"].append(f"Skipping non-date folder: {folder_name}")
                return

            # Check if folder is older than retention period
            if folder_date >= cutoff_date:
                return

            # Calculate folder size before deletion
            folder_size = 0
            file_count = 0
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    folder_size += file_path.stat().st_size
                    file_count += 1

            # Validate folder contents before deletion
            validation_result = await self._validate_folder_contents(folder_path)
            if not validation_result["valid"]:
                stats["warnings"].append(f"Skipping folder due to validation errors: {folder_name} - {validation_result['errors']}")
                return

            if dry_run:
                stats["details"].append(f"DRY RUN: Would remove folder {folder_name} ({file_count} files, {self._format_bytes(folder_size)})")
            else:
                # Actually delete the folder
                await self._safe_delete_folder(folder_path)
                stats["folders_removed"] += 1
                stats["files_removed"] += file_count
                stats["bytes_freed"] += folder_size
                stats["details"].append(f"Removed folder {folder_name} ({file_count} files, {self._format_bytes(folder_size)})")

        except Exception as e:
            error_msg = f"Error processing folder {folder_path}: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

    async def _validate_folder_contents(self, folder_path: Path) -> dict[str, Any]:
        """Validate folder contents before deletion"""

        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # Check for lock files (indicating active use)
            lock_files = list(folder_path.glob("*.lock"))
            if lock_files:
                validation["valid"] = False
                validation["errors"].append(f"Lock files found: {[f.name for f in lock_files]}")

            # Check for very recent files (might indicate active use)
            recent_threshold = datetime.now() - timedelta(hours=1)
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime > recent_threshold:
                        validation["warnings"].append(f"Recent file found: {file_path.name} (modified {file_mtime})")

            # Validate file integrity for evidence files
            for evidence_file in folder_path.glob("*.json.gz"):
                try:
                    # Quick validation - try to read file header
                    import gzip
                    with gzip.open(evidence_file, 'rb') as f:
                        f.read(100)  # Read first 100 bytes to validate
                except Exception as e:
                    validation["errors"].append(f"Corrupted evidence file: {evidence_file.name} - {str(e)}")

        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Validation error: {str(e)}")

        return validation

    async def _safe_delete_folder(self, folder_path: Path):
        """Safely delete a folder with comprehensive checks"""

        try:
            # Double-check folder is within evidence path
            if not str(folder_path).startswith(str(self.evidence_path)):
                raise ValueError(f"Folder path outside evidence directory: {folder_path}")

            # Check folder isn't empty root directory
            if folder_path == self.evidence_path:
                raise ValueError("Cannot delete root evidence directory")

            # Create backup record before deletion
            backup_record = {
                "deleted_at": datetime.now().isoformat(),
                "folder_path": str(folder_path),
                "original_contents": await self._create_folder_manifest(folder_path)
            }

            backup_file = self.evidence_path.parent / "cleanup" / f"deleted_backup_{folder_path.name}.json"
            backup_file.parent.mkdir(exist_ok=True)
            with open(backup_file, 'w') as f:
                json.dump(backup_record, f, indent=2, default=str)

            # Perform deletion
            shutil.rmtree(folder_path)

            logger.info(f"Safely deleted folder: {folder_path}")

        except Exception as e:
            logger.error(f"Failed to safely delete folder {folder_path}: {str(e)}")
            raise

    async def _create_folder_manifest(self, folder_path: Path) -> list[dict[str, Any]]:
        """Create manifest of folder contents before deletion"""

        manifest = []
        try:
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(folder_path)
                    stat = file_path.stat()
                    manifest.append({
                        "path": str(relative_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "checksum": await self._calculate_file_checksum(file_path)
                    })
        except Exception as e:
            logger.warning(f"Failed to create manifest for {folder_path}: {str(e)}")

        return manifest

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""

        try:
            import hashlib
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "checksum_failed"

    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes count for human readable output"""

        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024
        return f"{bytes_count:.1f} TB"

    async def _log_cleanup_summary(self, stats: dict[str, Any]):
        """Log comprehensive cleanup summary"""

        summary = f"""
=== EVIDENCE CLEANUP SUMMARY ===
Execution Time: {stats['start_time']}
Dry Run: {stats['dry_run']}
Retention Period: {stats['retention_days']} days
Cutoff Date: {stats['cutoff_date']}

RESULTS:
- Files Removed: {stats['files_removed']}
- Folders Removed: {stats['folders_removed']}
- Space Freed: {self._format_bytes(stats['bytes_freed'])}

ISSUES:
- Errors: {len(stats['errors'])}
- Warnings: {len(stats['warnings'])}
"""

        if stats["errors"]:
            summary += "\nERRORS:\n"
            for error in stats["errors"]:
                summary += f"  - {error}\n"

        if stats["warnings"]:
            summary += "\nWARNINGS:\n"
            for warning in stats["warnings"]:
                summary += f"  - {warning}\n"

        # Write to cleanup log
        with open(self.cleanup_log, 'a') as f:
            f.write(summary + "\n" + "="*50 + "\n\n")

        logger.info("Cleanup summary logged to " + str(self.cleanup_log))

# Global cleanup manager instance
cleanup_manager = EvidenceCleanupManager()

# Main execution function
async def main():
    """Main cleanup execution function"""

    import argparse

    parser = argparse.ArgumentParser(description="Evidence Cleanup Manager")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--retention-days", type=int, default=3, help="Retention period in days")
    parser.add_argument("--evidence-path", default="P:\\.speckit\\taskmaster\\evidence\\explore_findings", help="Path to evidence directory")

    args = parser.parse_args()

    # Initialize cleanup manager
    manager = EvidenceCleanupManager(args.evidence_path, args.retention_days)

    # Run cleanup
    stats = await manager.cleanup_old_evidence(dry_run=args.dry_run)

    # Print results
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
