#!/usr/bin/env python3
"""
Comprehensive Backup and Recovery Automation Script
For Task Execution Enhancements Project

This script handles:
- Automated backup procedures
- Disaster recovery testing automation
- System restoration procedures
- Data integrity validation
- Recovery time objective (RTO) automation
"""

import hashlib
import json
import logging
import shutil
import sqlite3
import sys
import tarfile
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import schedule


@dataclass
class BackupConfig:
    """Configuration for backup and recovery"""
    # Backup locations
    backup_root_dir: str = "deployment-automation/backups"
    local_backup_dir: str = "deployment-automation/backups/local"
    remote_backup_dir: str = "/remote/backups/task-execution-enhancements"
    s3_backup_bucket: str = "task-execution-enhancements-backups"

    # Backup schedules
    database_backup_interval: str = "hourly"  # hourly, daily, weekly
    config_backup_interval: str = "daily"
    log_backup_interval: str = "weekly"
    full_backup_interval: str = "monthly"

    # Retention policies
    daily_retention_days: int = 7
    weekly_retention_weeks: int = 4
    monthly_retention_months: int = 12
    yearly_retention_years: int = 3

    # Backup types
    backup_database: bool = True
    backup_configurations: bool = True
    backup_logs: bool = True
    backup_artifacts: bool = True
    backup_dependencies: bool = True

    # Compression and encryption
    compression_enabled: bool = True
    compression_level: int = 6
    encryption_enabled: bool = False
    encryption_key: str | None = None

    # Performance settings
    max_parallel_backups: int = 3
    backup_timeout_minutes: int = 60

    # Verification settings
    verify_backups: bool = True
    test_restores: bool = True
    integrity_check_enabled: bool = True

@dataclass
class BackupMetadata:
    """Metadata for backup files"""
    backup_id: str
    timestamp: str
    backup_type: str  # database, config, logs, full
    size_bytes: int
    checksum: str
    compressed: bool
    encrypted: bool
    file_path: str
    description: str
    source_directories: list[str]
    retention_period: str

class BackupRecoveryError(Exception):
    """Custom exception for backup and recovery failures"""
    pass

class BackupRecoveryManager:
    """Comprehensive backup and recovery automation"""

    def __init__(self, config: BackupConfig | None = None):
        self.config = config or BackupConfig()
        self.logger = self._setup_logging()
        self.base_path = Path.cwd()
        self.backup_root = Path(self.config.backup_root_dir)
        self.active_backups = {}
        self.backup_history = []

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    f'backup_recovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                )
            ]
        )
        return logging.getLogger(__name__)

    def log_step(self, step: str, status: str, details: str = ""):
        """Log backup/recovery step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.backup_history.append(log_entry)

        if status == 'SUCCESS':
            self.logger.info(f"✅ {step}: {details}")
        elif status == 'WARNING':
            self.logger.warning(f"⚠️  {step}: {details}")
        else:
            self.logger.error(f"❌ {step}: {details}")

    def initialize_backup_structure(self) -> bool:
        """Initialize backup directory structure"""
        self.log_step("Initializing Backup Structure", "STARTED")

        try:
            directories = [
                self.backup_root,
                Path(self.config.local_backup_dir),
                self.backup_root / "database",
                self.backup_root / "config",
                self.backup_root / "logs",
                self.backup_root / "artifacts",
                self.backup_root / "metadata",
                self.backup_root / "temp",
                self.backup_root / "recovery-test"
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.log_step(f"Creating Directory {directory.name}", "SUCCESS")

            # Create backup configuration
            backup_config_file = self.backup_root / "backup_config.json"
            with open(backup_config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)

            self.log_step("Initializing Backup Structure", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Initializing Backup Structure", "FAILED", str(e))
            return False

    def backup_database(self, backup_type: str = "incremental") -> BackupMetadata | None:
        """Backup SQLite databases"""
        if not self.config.backup_database:
            self.log_step("Database Backup", "SKIPPED", "Database backup disabled")
            return None

        self.log_step("Database Backup", "STARTED", f"Type: {backup_type}")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"database_backup_{backup_type}_{timestamp}.sql"
            backup_path = self.backup_root / "database" / backup_filename

            # Find all SQLite databases
            database_paths = [
                self.base_path / "__csf/data/evidence.db",
                self.base_path / "P:/taskmaster_db.get_db_path()",
                self.base_path / ".claude/session_storage/sessions.db"
            ]

            existing_databases = [p for p in database_paths if p.exists()]
            if not existing_databases:
                self.log_step("Database Backup", "WARNING", "No databases found to backup")
                return None

            # Create backup script
            with open(backup_path, 'w') as backup_file:
                backup_file.write(f"-- Database Backup - {timestamp}\n")
                backup_file.write(f"-- Backup Type: {backup_type}\n\n")

                for db_path in existing_databases:
                    backup_file.write(f"-- Database: {db_path.name}\n")

                    conn = sqlite3.connect(db_path)
                    try:
                        # Dump database schema and data
                        with backup_file:
                            for line in conn.iterdump():
                                backup_file.write(f"{line}\n")
                        backup_file.write("\n")
                    finally:
                        conn.close()

            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)

            # Compress if enabled
            if self.config.compression_enabled:
                compressed_path = backup_path.with_suffix('.sql.gz')
                with open(backup_path, 'rb') as f_in:
                    import gzip
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path.unlink()  # Remove uncompressed file
                backup_path = compressed_path
                is_compressed = True
            else:
                is_compressed = False

            # Create metadata
            metadata = BackupMetadata(
                backup_id=f"db_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}",
                timestamp=timestamp,
                backup_type=f"database_{backup_type}",
                size_bytes=backup_path.stat().st_size,
                checksum=checksum,
                compressed=is_compressed,
                encrypted=False,
                file_path=str(backup_path),
                description=f"Database backup - {backup_type}",
                source_directories=[str(p.parent) for p in existing_databases],
                retention_period=self._get_retention_period("database")
            )

            # Save metadata
            self._save_backup_metadata(metadata)

            self.log_step("Database Backup", "SUCCESS", f"Backed up {len(existing_databases)} databases")
            return metadata

        except Exception as e:
            self.log_step("Database Backup", "FAILED", str(e))
            return None

    def backup_configurations(self) -> BackupMetadata | None:
        """Backup configuration files"""
        if not self.config.backup_configurations:
            self.log_step("Configuration Backup", "SKIPPED", "Configuration backup disabled")
            return None

        self.log_step("Configuration Backup", "STARTED")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.tar.gz"
            backup_path = self.backup_root / "config" / backup_filename

            # Configuration directories to backup
            config_sources = [
                (self.base_path / ".claude", ".claude"),
                (self.base_path / "__csf/config", "csf_nip_config"),
                (self.base_path / "deployment-automation/config", "deployment_config"),
                (self.base_path / ".gittree", "gittree")
            ]

            # Create archive
            with tarfile.open(backup_path, "w:gz") as tar:
                for source_dir, arcname in config_sources:
                    if source_dir.exists():
                        tar.add(source_dir, arcname=arcname)
                        self.log_step("Adding to backup", "SUCCESS", f"{source_dir}")

            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)

            # Create metadata
            metadata = BackupMetadata(
                backup_id=f"config_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}",
                timestamp=timestamp,
                backup_type="config",
                size_bytes=backup_path.stat().st_size,
                checksum=checksum,
                compressed=True,
                encrypted=False,
                file_path=str(backup_path),
                description="Configuration files backup",
                source_directories=[str(p[0]) for p in config_sources if p[0].exists()],
                retention_period=self._get_retention_period("config")
            )

            # Save metadata
            self._save_backup_metadata(metadata)

            self.log_step("Configuration Backup", "SUCCESS", f"Configuration backed up to {backup_filename}")
            return metadata

        except Exception as e:
            self.log_step("Configuration Backup", "FAILED", str(e))
            return None

    def backup_logs(self) -> BackupMetadata | None:
        """Backup log files"""
        if not self.config.backup_logs:
            self.log_step("Log Backup", "SKIPPED", "Log backup disabled")
            return None

        self.log_step("Log Backup", "STARTED")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"logs_backup_{timestamp}.tar.gz"
            backup_path = self.backup_root / "logs" / backup_filename

            # Log directories to backup
            log_sources = [
                (self.base_path / "__csf/logs", "csf_nip_logs"),
                (self.base_path / ".claude/logs", "claude_logs"),
                (self.base_path / "deployment-automation/logs", "deployment_logs"),
                (self.base_path / "logs", "application_logs")
            ]

            # Create archive with only recent logs (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            with tarfile.open(backup_path, "w:gz") as tar:
                for source_dir, arcname in log_sources:
                    if source_dir.exists():
                        for log_file in source_dir.rglob("*"):
                            if log_file.is_file():
                                # Check file modification time
                                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                                if mod_time > cutoff_date:
                                    tar.add(log_file, arcname=f"{arcname}/{log_file.relative_to(source_dir)}")

            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)

            # Create metadata
            metadata = BackupMetadata(
                backup_id=f"logs_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}",
                timestamp=timestamp,
                backup_type="logs",
                size_bytes=backup_path.stat().st_size,
                checksum=checksum,
                compressed=True,
                encrypted=False,
                file_path=str(backup_path),
                description="Log files backup (last 30 days)",
                source_directories=[str(p[0]) for p in log_sources if p[0].exists()],
                retention_period=self._get_retention_period("logs")
            )

            # Save metadata
            self._save_backup_metadata(metadata)

            self.log_step("Log Backup", "SUCCESS", f"Logs backed up to {backup_filename}")
            return metadata

        except Exception as e:
            self.log_step("Log Backup", "FAILED", str(e))
            return None

    def backup_artifacts(self) -> BackupMetadata | None:
        """Backup deployment artifacts and build outputs"""
        if not self.config.backup_artifacts:
            self.log_step("Artifacts Backup", "SKIPPED", "Artifacts backup disabled")
            return None

        self.log_step("Artifacts Backup", "STARTED")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"artifacts_backup_{timestamp}.tar.gz"
            backup_path = self.backup_root / "artifacts" / backup_filename

            # Artifact directories to backup
            artifact_sources = [
                (self.base_path / "dist", "distribution"),
                (self.base_path / "build", "build"),
                (self.base_path / ".pytest_cache", "pytest_cache"),
                (self.base_path / ".coverage", "coverage"),
                (self.base_path / "htmlcov", "html_coverage"),
                (self.base_path / "deployment-automation/packages", "packages")
            ]

            # Create archive
            with tarfile.open(backup_path, "w:gz") as tar:
                for source_dir, arcname in artifact_sources:
                    if source_dir.exists():
                        tar.add(source_dir, arcname=arcname)

            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)

            # Create metadata
            metadata = BackupMetadata(
                backup_id=f"artifacts_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}",
                timestamp=timestamp,
                backup_type="artifacts",
                size_bytes=backup_path.stat().st_size,
                checksum=checksum,
                compressed=True,
                encrypted=False,
                file_path=str(backup_path),
                description="Build artifacts and deployment packages",
                source_directories=[str(p[0]) for p in artifact_sources if p[0].exists()],
                retention_period=self._get_retention_period("artifacts")
            )

            # Save metadata
            self._save_backup_metadata(metadata)

            self.log_step("Artifacts Backup", "SUCCESS", f"Artifacts backed up to {backup_filename}")
            return metadata

        except Exception as e:
            self.log_step("Artifacts Backup", "FAILED", str(e))
            return None

    def create_full_backup(self) -> list[BackupMetadata]:
        """Create a complete full backup"""
        self.log_step("Full Backup", "STARTED")

        backup_results = []

        try:
            # Backup all components
            backups = [
                self.backup_database("full"),
                self.backup_configurations(),
                self.backup_logs(),
                self.backup_artifacts()
            ]

            backup_results = [b for b in backups if b is not None]

            # Create backup manifest
            manifest = {
                'backup_id': f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'full',
                'components': [asdict(b) for b in backup_results],
                'total_size': sum(b.size_bytes for b in backup_results),
                'description': 'Complete system backup'
            }

            manifest_path = self.backup_root / "metadata" / f"full_backup_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            self.log_step("Full Backup", "SUCCESS", f"Created full backup with {len(backup_results)} components")
            return backup_results

        except Exception as e:
            self.log_step("Full Backup", "FAILED", str(e))
            return backup_results

    def restore_database(self, backup_id: str, target_path: Path | None = None) -> bool:
        """Restore database from backup"""
        self.log_step("Database Restore", "STARTED", f"Backup ID: {backup_id}")

        try:
            # Find backup metadata
            metadata = self._find_backup_metadata(backup_id)
            if not metadata or not metadata.backup_type.startswith("database"):
                raise BackupRecoveryError(f"Database backup {backup_id} not found")

            backup_path = Path(metadata.file_path)
            if not backup_path.exists():
                raise BackupRecoveryError(f"Backup file not found: {backup_path}")

            # Extract if compressed
            temp_path = self.backup_root / "temp" / f"restore_{backup_id}"
            temp_path.mkdir(parents=True, exist_ok=True)

            if metadata.compressed:
                import gzip
                with gzip.open(backup_path, 'rt') as f_in:
                    with open(temp_path / "restore.sql", 'w') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = temp_path / "restore.sql"
            else:
                sql_file = backup_path

            # Determine restore target
            if target_path is None:
                target_path = self.base_path / "__csf/data"

            # Restore databases
            restored_dbs = []
            with open(sql_file) as f:
                sql_content = f.read()

            # Split SQL content by database (assuming comments indicate database boundaries)
            db_statements = sql_content.split('-- Database:')

            for i, db_statement in enumerate(db_statements[1:], 1):  # Skip first empty split
                lines = db_statement.split('\n')
                db_name = lines[0].strip() if lines else f"database_{i}"

                # Create database file
                db_file = target_path / f"{db_name}.db"

                conn = sqlite3.connect(db_file)
                try:
                    # Extract and execute SQL for this database
                    db_sql = '-- Database: ' + db_statement
                    conn.executescript(db_sql)
                    restored_dbs.append(str(db_file))
                finally:
                    conn.close()

            # Cleanup temp files
            if temp_path.exists():
                shutil.rmtree(temp_path)

            self.log_step("Database Restore", "SUCCESS", f"Restored {len(restored_dbs)} databases")
            return True

        except Exception as e:
            self.log_step("Database Restore", "FAILED", str(e))
            return False

    def restore_configurations(self, backup_id: str) -> bool:
        """Restore configuration files from backup"""
        self.log_step("Configuration Restore", "STARTED", f"Backup ID: {backup_id}")

        try:
            metadata = self._find_backup_metadata(backup_id)
            if not metadata or metadata.backup_type != "config":
                raise BackupRecoveryError(f"Configuration backup {backup_id} not found")

            backup_path = Path(metadata.file_path)
            if not backup_path.exists():
                raise BackupRecoveryError(f"Backup file not found: {backup_path}")

            # Extract configuration backup
            temp_path = self.backup_root / "temp" / f"config_restore_{backup_id}"
            temp_path.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(temp_path)

            # Restore configurations to original locations
            restore_mappings = {
                "claude": self.base_path / ".claude",
                "csf_nip_config": self.base_path / "__csf/config",
                "deployment_config": self.base_path / "deployment-automation/config",
                "gittree": self.base_path / ".gittree"
            }

            restored_configs = []
            for source_name, target_path in restore_mappings.items():
                source_path = temp_path / source_name
                if source_path.exists():
                    # Backup current configuration first
                    if target_path.exists():
                        backup_current = target_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.move(target_path, backup_current)

                    # Restore from backup
                    shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                    restored_configs.append(str(target_path))

            # Cleanup temp files
            if temp_path.exists():
                shutil.rmtree(temp_path)

            self.log_step("Configuration Restore", "SUCCESS", f"Restored {len(restored_configs)} configuration sets")
            return True

        except Exception as e:
            self.log_step("Configuration Restore", "FAILED", str(e))
            return False

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify backup file integrity"""
        self.log_step("Backup Integrity Verification", "STARTED", f"Backup ID: {backup_id}")

        try:
            metadata = self._find_backup_metadata(backup_id)
            if not metadata:
                raise BackupRecoveryError(f"Backup {backup_id} not found")

            backup_path = Path(metadata.file_path)
            if not backup_path.exists():
                raise BackupRecoveryError(f"Backup file not found: {backup_path}")

            # Verify file exists and has expected size
            if backup_path.stat().st_size != metadata.size_bytes:
                self.log_step("Backup Integrity Verification", "FAILED", "Size mismatch")
                return False

            # Verify checksum
            current_checksum = self._calculate_file_checksum(backup_path)
            if current_checksum != metadata.checksum:
                self.log_step("Backup Integrity Verification", "FAILED", "Checksum mismatch")
                return False

            # Test archive integrity for compressed files
            if backup_path.suffix in ['.gz', '.zip', '.tar.gz']:
                try:
                    if backup_path.suffix == '.gz' and backup_path.suffixes[-2] == '.tar':
                        # Test tar.gz file
                        with tarfile.open(backup_path, "r:gz") as tar:
                            tar.testzip()
                    elif backup_path.suffix == '.gz':
                        # Test gzip file
                        import gzip
                        with gzip.open(backup_path, 'rt') as f:
                            f.read(1024)  # Read a small portion to test
                    elif backup_path.suffix == '.zip':
                        # Test zip file
                        with zipfile.ZipFile(backup_path, 'r') as zip_file:
                            zip_file.testzip()
                except Exception as e:
                    self.log_step("Backup Integrity Verification", "FAILED", f"Archive test failed: {str(e)}")
                    return False

            self.log_step("Backup Integrity Verification", "SUCCESS", "Backup integrity verified")
            return True

        except Exception as e:
            self.log_step("Backup Integrity Verification", "FAILED", str(e))
            return False

    def test_disaster_recovery(self) -> bool:
        """Test disaster recovery procedures"""
        self.log_step("Disaster Recovery Test", "STARTED")

        try:
            test_results = []

            # Test 1: Create test backup
            self.log_step("Creating Test Backup", "STARTED")
            test_backups = self.create_full_backup()
            if not test_backups:
                raise BackupRecoveryError("Failed to create test backup")

            test_backup_id = test_backups[0].backup_id
            test_results.append(("backup_creation", True, "Test backup created successfully"))

            # Test 2: Verify backup integrity
            integrity_ok = self.verify_backup_integrity(test_backup_id)
            test_results.append(("backup_integrity", integrity_ok, "Backup integrity verified" if integrity_ok else "Backup integrity failed"))

            # Test 3: Test configuration restore
            config_restore_ok = self.restore_configurations(test_backup_id)
            test_results.append(("config_restore", config_restore_ok, "Configuration restore successful" if config_restore_ok else "Configuration restore failed"))

            # Test 4: Test database restore
            db_restore_path = self.backup_root / "recovery-test" / "database"
            db_restore_path.mkdir(parents=True, exist_ok=True)
            db_restore_ok = self.restore_database(test_backup_id, db_restore_path)
            test_results.append(("database_restore", db_restore_ok, "Database restore successful" if db_restore_ok else "Database restore failed"))

            # Calculate success rate
            successful_tests = sum(1 for _, success, _ in test_results if success)
            total_tests = len(test_results)
            success_rate = (successful_tests / total_tests) * 100

            # Generate test report
            test_report = {
                'test_timestamp': datetime.now().isoformat(),
                'backup_id': test_backup_id,
                'test_results': [
                    {
                        'test_name': name,
                        'success': success,
                        'message': message
                    } for name, success, message in test_results
                ],
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'success_rate': success_rate
                }
            }

            report_path = self.backup_root / "recovery-test" / f"disaster_recovery_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(test_report, f, indent=2)

            if success_rate >= 75:  # At least 75% of tests should pass
                self.log_step("Disaster Recovery Test", "SUCCESS", f"Success rate: {success_rate:.1f}%")
                return True
            else:
                self.log_step("Disaster Recovery Test", "FAILED", f"Low success rate: {success_rate:.1f}%")
                return False

        except Exception as e:
            self.log_step("Disaster Recovery Test", "FAILED", str(e))
            return False

    def cleanup_old_backups(self) -> bool:
        """Clean up old backups based on retention policy"""
        self.log_step("Backup Cleanup", "STARTED")

        try:
            # Load all backup metadata
            metadata_dir = self.backup_root / "metadata"
            if not metadata_dir.exists():
                self.log_step("Backup Cleanup", "SUCCESS", "No metadata directory found")
                return True

            all_metadata = []
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file) as f:
                        data = json.load(f)
                        if 'backup_id' in data:
                            all_metadata.append(data)
                except Exception:
                    continue

            if not all_metadata:
                self.log_step("Backup Cleanup", "SUCCESS", "No backup metadata found")
                return True

            # Calculate cutoff dates
            now = datetime.now()
            daily_cutoff = now - timedelta(days=self.config.daily_retention_days)
            weekly_cutoff = now - timedelta(weeks=self.config.weekly_retention_weeks)
            monthly_cutoff = now - timedelta(days=self.config.monthly_retention_months * 30)
            yearly_cutoff = now - timedelta(days=self.config.yearly_retention_years * 365)

            deleted_backups = 0
            for metadata in all_metadata:
                try:
                    backup_timestamp = datetime.fromisoformat(metadata['timestamp'])
                    backup_path = Path(metadata['file_path'])

                    should_delete = False
                    delete_reason = ""

                    # Check retention based on backup type and age
                    if backup_timestamp < yearly_cutoff:
                        should_delete = True
                        delete_reason = "Yearly retention exceeded"
                    elif backup_timestamp < monthly_cutoff and metadata['backup_type'] != 'database_full':
                        should_delete = True
                        delete_reason = "Monthly retention exceeded"
                    elif backup_timestamp < weekly_cutoff and metadata['backup_type'] not in ['database_full', 'database_incremental']:
                        should_delete = True
                        delete_reason = "Weekly retention exceeded"
                    elif backup_timestamp < daily_cutoff and metadata['backup_type'] not in ['database_full', 'database_incremental', 'config']:
                        should_delete = True
                        delete_reason = "Daily retention exceeded"

                    if should_delete and backup_path.exists():
                        backup_path.unlink()
                        # Also delete metadata file
                        metadata_file = metadata_dir / f"backup_metadata_{metadata['backup_id']}.json"
                        if metadata_file.exists():
                            metadata_file.unlink()

                        deleted_backups += 1
                        self.log_step("Deleting Backup", "SUCCESS", f"Deleted {metadata['backup_id']} - {delete_reason}")

                except Exception as e:
                    self.log_step("Backup Cleanup Error", "WARNING", f"Error processing backup: {str(e)}")
                    continue

            self.log_step("Backup Cleanup", "SUCCESS", f"Deleted {deleted_backups} old backups")
            return True

        except Exception as e:
            self.log_step("Backup Cleanup", "FAILED", str(e))
            return False

    def schedule_backups(self) -> bool:
        """Setup scheduled backup jobs"""
        self.log_step("Scheduling Backups", "STARTED")

        try:
            # Schedule database backups
            if self.config.backup_database:
                if self.config.database_backup_interval == "hourly":
                    schedule.every().hour.do(self.backup_database, "incremental")
                elif self.config.database_backup_interval == "daily":
                    schedule.every().day.at("02:00").do(self.backup_database, "incremental")
                elif self.config.database_backup_interval == "weekly":
                    schedule.every().sunday.at("02:00").do(self.backup_database, "full")

            # Schedule configuration backups
            if self.config.backup_configurations:
                if self.config.config_backup_interval == "daily":
                    schedule.every().day.at("03:00").do(self.backup_configurations)
                elif self.config.config_backup_interval == "weekly":
                    schedule.every().sunday.at("03:00").do(self.backup_configurations)

            # Schedule log backups
            if self.config.backup_logs:
                if self.config.log_backup_interval == "weekly":
                    schedule.every().sunday.at("04:00").do(self.backup_logs)

            # Schedule full backups
            if self.config.full_backup_interval == "monthly":
                schedule.every().month.do(self.create_full_backup)

            # Schedule cleanup
            schedule.every().day.at("05:00").do(self.cleanup_old_backups)

            # Schedule disaster recovery tests
            if self.config.test_restores:
                schedule.every().week.at("06:00").do(self.test_disaster_recovery)

            self.log_step("Scheduling Backups", "SUCCESS", "Backup schedules configured")
            return True

        except Exception as e:
            self.log_step("Scheduling Backups", "FAILED", str(e))
            return False

    def start_backup_scheduler(self):
        """Start the backup scheduler daemon"""
        self.log_step("Starting Backup Scheduler", "STARTED")

        if not self.schedule_backups():
            self.logger.error("Failed to setup backup schedules")
            return

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log_step("Backup Scheduler", "STOPPED", "Scheduler stopped by user")
        except Exception as e:
            self.log_step("Backup Scheduler", "FAILED", f"Scheduler error: {str(e)}")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file"""
        metadata_file = self.backup_root / "metadata" / f"backup_metadata_{metadata.backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)

    def _find_backup_metadata(self, backup_id: str) -> BackupMetadata | None:
        """Find backup metadata by ID"""
        metadata_file = self.backup_root / "metadata" / f"backup_metadata_{backup_id}.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                return BackupMetadata(**data)
        return None

    def _get_retention_period(self, backup_type: str) -> str:
        """Get retention period for backup type"""
        retention_map = {
            "database": f"{self.config.daily_retention_days} days",
            "config": f"{self.config.weekly_retention_weeks} weeks",
            "logs": f"{self.config.monthly_retention_months} months",
            "artifacts": f"{self.config.monthly_retention_months} months"
        }
        return retention_map.get(backup_type, "30 days")

    def generate_backup_report(self) -> dict:
        """Generate comprehensive backup report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'configuration': asdict(self.config),
            'backup_history': self.backup_history[-20:],  # Last 20 operations
            'summary': {
                'total_operations': len(self.backup_history),
                'successful_operations': len([log for log in self.backup_history if log['status'] == 'SUCCESS']),
                'failed_operations': len([log for log in self.backup_history if log['status'] == 'FAILED']),
                'warnings': len([log for log in self.backup_history if log['status'] == 'WARNING'])
            },
            'storage_info': self._get_storage_info(),
            'last_backup_status': self.backup_history[-1]['status'] if self.backup_history else None
        }

        # Save report
        report_path = self.backup_root / f"backup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Backup report saved to: {report_path}")
        return report

    def _get_storage_info(self) -> dict:
        """Get storage information"""
        try:
            backup_size = sum(f.stat().st_size for f in self.backup_root.rglob('*') if f.is_file())
            backup_files = len(list(self.backup_root.rglob('*')))

            return {
                'total_size_bytes': backup_size,
                'total_size_mb': round(backup_size / (1024 * 1024), 2),
                'total_files': backup_files,
                'backup_root': str(self.backup_root)
            }
        except Exception:
            return {'error': 'Unable to calculate storage info'}

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Execution Enhancements Backup and Recovery")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--action', choices=[
        'init', 'backup-db', 'backup-config', 'backup-logs', 'backup-full',
        'restore-db', 'restore-config', 'verify', 'test-dr', 'cleanup',
        'schedule', 'report'
    ], required=True, help='Action to perform')
    parser.add_argument('--backup-id', help='Backup ID for restore/verify operations')
    parser.add_argument('--target-path', help='Target path for restore operations')
    parser.add_argument('--start-scheduler', action='store_true', help='Start backup scheduler daemon')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Load configuration if provided
    config = BackupConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize backup manager
    manager = BackupRecoveryManager(config)

    try:
        # Initialize backup structure
        if not manager.initialize_backup_structure():
            sys.exit(1)

        # Execute requested action
        success = False
        if args.action == 'init':
            success = manager.initialize_backup_structure()
        elif args.action == 'backup-db':
            result = manager.backup_database()
            success = result is not None
        elif args.action == 'backup-config':
            result = manager.backup_configurations()
            success = result is not None
        elif args.action == 'backup-logs':
            result = manager.backup_logs()
            success = result is not None
        elif args.action == 'backup-full':
            results = manager.create_full_backup()
            success = len(results) > 0
        elif args.action == 'restore-db':
            if not args.backup_id:
                parser.error("--backup-id required for database restore")
            target_path = Path(args.target_path) if args.target_path else None
            success = manager.restore_database(args.backup_id, target_path)
        elif args.action == 'restore-config':
            if not args.backup_id:
                parser.error("--backup-id required for configuration restore")
            success = manager.restore_configurations(args.backup_id)
        elif args.action == 'verify':
            if not args.backup_id:
                parser.error("--backup-id required for verification")
            success = manager.verify_backup_integrity(args.backup_id)
        elif args.action == 'test-dr':
            success = manager.test_disaster_recovery()
        elif args.action == 'cleanup':
            success = manager.cleanup_old_backups()
        elif args.action == 'schedule':
            success = manager.schedule_backups()
        elif args.action == 'report':
            report = manager.generate_backup_report()
            print(json.dumps(report, indent=2))
            success = True

        # Start scheduler if requested
        if args.start_scheduler:
            manager.start_backup_scheduler()
        else:
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        manager.logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        manager.logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
