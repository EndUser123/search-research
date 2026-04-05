#!/usr/bin/env python3
"""
Comprehensive Environment Setup Automation Script
For Task Execution Enhancements Project

This script handles:
- Environment provisioning and validation
- Dependency installation and verification
- Configuration setup and validation
- Database initialization and migration
- Health check and validation automation
"""

import json
import logging
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class EnvironmentConfig:
    """Configuration for environment setup"""
    python_version: str = "3.10+"
    required_packages: list[str] = None
    optional_packages: list[str] = None
    git_worktree_path: str = ".gittree/task-execution-enhancements"
    session_management_path: str = ".claude"
    csf_nip_path: str = "__csf"

    def __post_init__(self):
        if self.required_packages is None:
            self.required_packages = [
                "uv", "ruff", "mypy", "pytest", "psutil", "pyyaml",
                "watchdog", "bandit", "coverage", "pre-commit"
            ]
        if self.optional_packages is None:
            self.optional_packages = [
                "py-spy", "memory-profiler", "sphinx", "black", "isort"
            ]

class EnvironmentSetupError(Exception):
    """Custom exception for environment setup failures"""
    pass

class EnvironmentSetup:
    """Comprehensive environment setup automation"""

    def __init__(self, config: EnvironmentConfig | None = None):
        self.config = config or EnvironmentConfig()
        self.logger = self._setup_logging()
        self.base_path = Path.cwd()
        self.deployment_path = Path(__file__).parent.parent
        self.setup_log = []

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    f'environment_setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                )
            ]
        )
        return logging.getLogger(__name__)

    def log_step(self, step: str, status: str, details: str = ""):
        """Log setup step with status"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.setup_log.append(log_entry)

        if status == 'SUCCESS':
            self.logger.info(f"✅ {step}: {details}")
        elif status == 'WARNING':
            self.logger.warning(f"⚠️  {step}: {details}")
        else:
            self.logger.error(f"❌ {step}: {details}")

    def validate_system_requirements(self) -> bool:
        """Validate system requirements"""
        self.log_step("System Requirements Check", "STARTED")

        try:
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 8):
                raise EnvironmentSetupError(f"Python 3.8+ required, found {python_version}")

            self.log_step(
                "Python Version Check",
                "SUCCESS",
                f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
            )

            # Check platform
            current_platform = platform.system()
            supported_platforms = ["Windows", "Darwin", "Linux"]
            if current_platform not in supported_platforms:
                self.log_step(
                    "Platform Check",
                    "WARNING",
                    f"Platform {current_platform} not officially supported"
                )
            else:
                self.log_step("Platform Check", "SUCCESS", f"Platform: {current_platform}")

            # Check available memory
            try:
                import psutil
                memory_gb = psutil.virtual_memory().total / (1024**3)
                if memory_gb < 1:
                    self.log_step("Memory Check", "WARNING", f"Low memory: {memory_gb:.1f}GB")
                else:
                    self.log_step("Memory Check", "SUCCESS", f"Memory: {memory_gb:.1f}GB")
            except ImportError:
                self.log_step("Memory Check", "WARNING", "psutil not available for memory check")

            # Check disk space
            disk_usage = shutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            if free_gb < 1:
                raise EnvironmentSetupError(f"Insufficient disk space: {free_gb:.1f}GB available")

            self.log_step("Disk Space Check", "SUCCESS", f"Free space: {free_gb:.1f}GB")

            self.log_step("System Requirements Check", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("System Requirements Check", "FAILED", str(e))
            return False

    def setup_python_environment(self) -> bool:
        """Setup Python environment with uv"""
        self.log_step("Python Environment Setup", "STARTED")

        try:
            # Check if uv is installed
            try:
                subprocess.run(['uv', '--version'], check=True, capture_output=True)
                self.log_step("UV Check", "SUCCESS", "uv package manager found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.log_step("UV Installation", "STARTED", "Installing uv package manager")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'uv'
                ], check=True)
                self.log_step("UV Installation", "SUCCESS", "uv installed successfully")

            # Initialize uv project if needed
            if not (self.base_path / 'pyproject.toml').exists():
                self.log_step("UV Project Init", "STARTED", "Initializing uv project")
                subprocess.run(['uv', 'init'], check=True, cwd=self.base_path)
                self.log_step("UV Project Init", "SUCCESS", "uv project initialized")

            # Install required packages
            for package in self.config.required_packages:
                try:
                    self.log_step(f"Installing {package}", "STARTED")
                    subprocess.run(['uv', 'add', package], check=True, cwd=self.base_path)
                    self.log_step(f"Installing {package}", "SUCCESS")
                except subprocess.CalledProcessError as e:
                    self.log_step(f"Installing {package}", "FAILED", str(e))
                    return False

            # Install optional packages
            for package in self.config.optional_packages:
                try:
                    self.log_step(f"Installing {package} (optional)", "STARTED")
                    subprocess.run(['uv', 'add', '--optional', package], check=True, cwd=self.base_path)
                    self.log_step(f"Installing {package} (optional)", "SUCCESS")
                except subprocess.CalledProcessError:
                    self.log_step(f"Installing {package} (optional)", "WARNING", "Optional package failed")

            self.log_step("Python Environment Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Python Environment Setup", "FAILED", str(e))
            return False

    def setup_directory_structure(self) -> bool:
        """Create required directory structure"""
        self.log_step("Directory Structure Setup", "STARTED")

        required_dirs = [
            self.config.git_worktree_path,
            self.config.session_management_path,
            self.config.csf_nip_path,
            f"{self.config.csf_nip_path}/config",
            f"{self.config.csf_nip_path}/logs",
            f"{self.config.csf_nip_path}/data",
            f"{self.config.session_management_path}/hooks",
            f"{self.config.session_management_path}/backups",
            "deployment-automation/logs",
            "deployment-automation/config",
            "deployment-automation/scripts"
        ]

        try:
            for dir_path in required_dirs:
                full_path = self.base_path / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.log_step(f"Creating Directory {dir_path}", "SUCCESS")
                else:
                    self.log_step(f"Creating Directory {dir_path}", "SUCCESS", "Already exists")

            self.log_step("Directory Structure Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Directory Structure Setup", "FAILED", str(e))
            return False

    def setup_git_worktree(self) -> bool:
        """Setup git worktree for task-execution-enhancements"""
        self.log_step("Git Worktree Setup", "STARTED")

        try:
            # Check if we're in a git repository
            git_dir = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True, text=True
            )

            if git_dir.returncode != 0:
                raise EnvironmentSetupError("Not in a git repository")

            worktree_path = self.base_path / self.config.git_worktree_path

            # Create worktree if it doesn't exist
            if not worktree_path.exists():
                self.log_step("Creating Worktree", "STARTED")
                subprocess.run([
                    'git', 'worktree', 'add',
                    str(worktree_path), '-b', 'task-execution-enhancements'
                ], check=True)
                self.log_step("Creating Worktree", "SUCCESS")
            else:
                self.log_step("Worktree Check", "SUCCESS", "Worktree already exists")

            self.log_step("Git Worktree Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Git Worktree Setup", "FAILED", str(e))
            return False

    def setup_configuration(self) -> bool:
        """Setup configuration files"""
        self.log_step("Configuration Setup", "STARTED")

        try:
            config_templates = {
                'anti_deception_config.json': {
                    "system": {
                        "enabled": True,
                        "mode": "deterministic",
                        "strict_mode": False
                    },
                    "enforcement": {
                        "block_dangerous": False,
                        "warnings_only_mode": True
                    },
                    "layers": {
                        "context_injection": {"enabled": True},
                        "execution_firewall": {"enabled": True},
                        "quality_gates": {"enabled": True},
                        "semantic_supervision": {"enabled": True}
                    }
                },
                'claude_settings.json': {
                    "hooks": {
                        "UserPromptSubmit": [{
                            "matcher": ".*",
                            "hooks": [{
                                "type": "command",
                                "command": "python .claude/hooks/session_start_hook.py",
                                "timeout": 5
                            }]
                        }],
                        "PreToolUse": [{
                            "hooks": [{
                                "type": "command",
                                "command": "python .claude/hooks/pre_tool_use.py",
                                "timeout": 10
                            }]
                        }],
                        "Stop": [{
                            "hooks": [{
                                "type": "command",
                                "command": "python .claude/hooks/session_management_integration.py",
                                "timeout": 30
                            }]
                        }]
                    }
                }
            }

            # Write configuration files
            for config_file, config_content in config_templates.items():
                config_path = self.base_path / self.config.session_management_path / config_file
                with open(config_path, 'w') as f:
                    json.dump(config_content, f, indent=2)
                self.log_step(f"Config File {config_file}", "SUCCESS", "Created successfully")

            self.log_step("Configuration Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Configuration Setup", "FAILED", str(e))
            return False

    def initialize_database(self) -> bool:
        """Initialize database for evidence collection"""
        self.log_step("Database Initialization", "STARTED")

        try:
            # Import database setup from CSF NIP
            sys.path.append(str(self.base_path / self.config.csf_nip_path))

            # Create SQLite database for evidence collection
            db_path = self.base_path / self.config.csf_nip_path / "data" / "evidence.db"

            if not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize database schema
            import sqlite3

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Create evidence table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evidence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        evidence_type TEXT NOT NULL,
                        content TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_path TEXT
                    )
                ''')

                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        metadata TEXT
                    )
                ''')

                # Create task_master table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_master (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tsk_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                ''')

                conn.commit()

            self.log_step("Database Initialization", "SUCCESS", "SQLite database created")
            return True

        except Exception as e:
            self.log_step("Database Initialization", "FAILED", str(e))
            return False

    def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        self.log_step("Health Checks", "STARTED")

        health_checks = [
            self._check_python_environment,
            self._check_dependencies,
            self._check_configuration,
            self._check_database,
            self._check_session_management,
            self._check_git_worktree
        ]

        all_passed = True
        for check in health_checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_step("Health Check", "FAILED", f"Exception: {str(e)}")
                all_passed = False

        if all_passed:
            self.log_step("Health Checks", "SUCCESS", "All health checks passed")
        else:
            self.log_step("Health Checks", "FAILED", "Some health checks failed")

        return all_passed

    def _check_python_environment(self) -> bool:
        """Check Python environment health"""
        try:
            import sys
            version = sys.version_info
            if version >= (3, 8):
                self.log_step("Python Health", "SUCCESS", f"Python {version.major}.{version.minor}")
                return True
            else:
                self.log_step("Python Health", "FAILED", "Python version too low")
                return False
        except Exception as e:
            self.log_step("Python Health", "FAILED", str(e))
            return False

    def _check_dependencies(self) -> bool:
        """Check required dependencies"""
        try:
            missing_deps = []
            for package in self.config.required_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    missing_deps.append(package)

            if missing_deps:
                self.log_step("Dependencies Health", "FAILED", f"Missing: {missing_deps}")
                return False
            else:
                self.log_step("Dependencies Health", "SUCCESS", "All dependencies available")
                return True
        except Exception as e:
            self.log_step("Dependencies Health", "FAILED", str(e))
            return False

    def _check_configuration(self) -> bool:
        """Check configuration files"""
        try:
            config_files = [
                f"{self.config.session_management_path}/anti_deception_config.json",
                f"{self.config.session_management_path}/claude_settings.json"
            ]

            for config_file in config_files:
                config_path = self.base_path / config_file
                if not config_path.exists():
                    self.log_step("Configuration Health", "FAILED", f"Missing {config_file}")
                    return False

                # Validate JSON syntax
                with open(config_path) as f:
                    json.load(f)

            self.log_step("Configuration Health", "SUCCESS", "All configuration files valid")
            return True
        except Exception as e:
            self.log_step("Configuration Health", "FAILED", str(e))
            return False

    def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            db_path = self.base_path / self.config.csf_nip_path / "data" / "evidence.db"
            if not db_path.exists():
                self.log_step("Database Health", "FAILED", "Database file not found")
                return False

            import sqlite3
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                required_tables = ['evidence', 'sessions', 'task_master']
                missing_tables = [t for t in required_tables if t not in tables]

                if missing_tables:
                    self.log_step("Database Health", "FAILED", f"Missing tables: {missing_tables}")
                    return False

            self.log_step("Database Health", "SUCCESS", "Database is accessible")
            return True
        except Exception as e:
            self.log_step("Database Health", "FAILED", str(e))
            return False

    def _check_session_management(self) -> bool:
        """Check session management system"""
        try:
            hooks_dir = self.base_path / self.config.session_management_path / "hooks"
            if not hooks_dir.exists():
                self.log_step("Session Management Health", "FAILED", "Hooks directory not found")
                return False

            # Check for essential hook files
            essential_hooks = [
                "session_start_hook.py",
                "pre_tool_use.py",
                "session_management_integration.py"
            ]

            missing_hooks = []
            for hook in essential_hooks:
                hook_path = hooks_dir / hook
                if not hook_path.exists():
                    missing_hooks.append(hook)

            if missing_hooks:
                self.log_step("Session Management Health", "WARNING", f"Missing hooks: {missing_hooks}")
            else:
                self.log_step("Session Management Health", "SUCCESS", "Session management ready")

            return True
        except Exception as e:
            self.log_step("Session Management Health", "FAILED", str(e))
            return False

    def _check_git_worktree(self) -> bool:
        """Check git worktree status"""
        try:
            worktree_path = self.base_path / self.config.git_worktree_path
            if not worktree_path.exists():
                self.log_step("Git Worktree Health", "FAILED", "Worktree directory not found")
                return False

            # Check if worktree is properly initialized
            result = subprocess.run(
                ['git', 'worktree', 'list'],
                capture_output=True, text=True
            )

            if str(worktree_path) in result.stdout:
                self.log_step("Git Worktree Health", "SUCCESS", "Worktree properly configured")
                return True
            else:
                self.log_step("Git Worktree Health", "FAILED", "Worktree not in git worktree list")
                return False
        except Exception as e:
            self.log_step("Git Worktree Health", "FAILED", str(e))
            return False

    def generate_setup_report(self) -> dict:
        """Generate comprehensive setup report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'environment': {
                'platform': platform.system(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'working_directory': str(self.base_path)
            },
            'setup_log': self.setup_log,
            'summary': {
                'total_steps': len(self.setup_log),
                'successful_steps': len([log for log in self.setup_log if log['status'] == 'SUCCESS']),
                'failed_steps': len([log for log in self.setup_log if log['status'] == 'FAILED']),
                'warnings': len([log for log in self.setup_log if log['status'] == 'WARNING'])
            },
            'status': 'SUCCESS' if all(log['status'] in ['SUCCESS', 'WARNING'] for log in self.setup_log) else 'FAILED'
        }

        # Save report to file
        report_path = self.deployment_path / 'logs' / f'environment_setup_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Setup report saved to: {report_path}")
        return report

    def run_full_setup(self) -> bool:
        """Run complete environment setup"""
        self.logger.info("Starting comprehensive environment setup...")

        setup_steps = [
            self.validate_system_requirements,
            self.setup_python_environment,
            self.setup_directory_structure,
            self.setup_git_worktree,
            self.setup_configuration,
            self.initialize_database,
            self.run_health_checks
        ]

        for step in setup_steps:
            try:
                if not step():
                    self.logger.error("Environment setup failed. Check logs for details.")
                    return False
            except Exception as e:
                self.logger.error(f"Setup step failed with exception: {str(e)}")
                return False

        # Generate final report
        report = self.generate_setup_report()

        if report['status'] == 'SUCCESS':
            self.logger.info("🎉 Environment setup completed successfully!")
            return True
        else:
            self.logger.error("❌ Environment setup completed with errors.")
            return False

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Execution Enhancements Environment Setup")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation')

    args = parser.parse_args()

    # Load configuration if provided
    config = EnvironmentConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run environment setup
    setup = EnvironmentSetup(config)

    try:
        success = setup.run_full_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        setup.logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        setup.logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
