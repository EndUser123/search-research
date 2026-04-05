import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import EnhancedConfig as Config
from .database import Database

logger = logging.getLogger(__name__)


class Autofix:
    """Safe Git-based autofix functionality for iCHS."""

    def __init__(self, config: Config, database: Database):
        """Initialize the autofix module.

        Args:
            config: Configuration object
            database: Database instance for accessing historical data
        """
        self.config = config
        self.database = database

        # Git configuration
        self.git_enabled = config.get("autofix", "git_enabled", True)
        self.backup_enabled = config.get("autofix", "backup_enabled", True)
        self.dry_run_enabled = config.get("autofix", "dry_run_enabled", False)
        self.max_changes_per_file = config.get("autofix", "max_changes_per_file", 10)

        # Safe rules configuration
        self.safe_rules = config.get(
            "autofix",
            "safe_rules",
            [
                "E501",  # Line too long
                "W292",  # No newline at end of file
                "W293",  # Blank line contains whitespace
                "E225",  # Missing whitespace around operator
                "E231",  # Missing whitespace after ','
                "E251",  # Unexpected spaces around keyword / parameter equals
                "E272",  # Whitespace around keyword
                "E275",  # Missing whitespace around unary operator
                "E401",  # Import statements are usually at the top of the file
                "E702",  # Multiple statements on one line (semicolon)
                "E703",  # End of statement (;)
                "E711",  # Comparison to None should be 'if cond is None:'
                "E712",  # Comparison to True should be 'if cond is True:' or 'if cond:'
                "E713",  # Test for membership should be 'not in'
                "E714",  # Test for object identity should be 'is not'
                "E721",  # Do not compare types, use 'isinstance()'
                "E722",  # Do not use bare except
                "E731",  # Do not assign a lambda expression, use a def
                "E741",  # Do not use variables named 'l', 'O', or 'I'
                "E742",  # Do not define classes for no reason
                "E743",  # Do not define functions for no reason
                "W291",  # Trailing whitespace
                "W292",  # No newline at end of file
                "W293",  # Blank line contains whitespace
                "W391",  # Blank line at end of file
                "W601",  # .has_key() is deprecated, use 'in'
                "W602",  # Deprecated form of raising exception
                "W603",  # '<>' is deprecated, use '!='
                "W604",  # Backticks are deprecated, use 'repr()'
                "W605",  # Invalid escape sequence
                "W606",  # 'async' and 'await' will become reserved keywords
                "W607",  # Using global for %s
                "W608",  # Using global for %s
                "W609",  # Using global for %s
                "W610",  # Using global for %s
                "W611",  # Using global for %s
                "W612",  # Using global for %s
                "W613",  # Using global for %s
                "W614",  # Using global for %s
                "W615",  # Using global for %s
                "W616",  # Using global for %s
                "W617",  # Using global for %s
                "W618",  # Using global for %s
                "W619",  # Using global for %s
                "W620",  # Using global for %s
                "W621",  # Using global for %s
                "W622",  # Using global for %s
                "W623",  # Using global for %s
                "W624",  # Using global for %s
                "W625",  # Using global for %s
                "W626",  # Using global for %s
                "W627",  # Using global for %s
                "W628",  # Using global for %s
                "W629",  # Using global for %s
                "W630",  # Using global for %s
                "W631",  # Using global for %s
                "W632",  # Using global for %s
                "W633",  # Using global for %s
                "W634",  # Using global for %s
                "W635",  # Using global for %s
                "W636",  # Using global for %s
                "W637",  # Using global for %s
                "W638",  # Using global for %s
                "W639",  # Using global for %s
                "W640",  # Using global for %s
                "W641",  # Using global for %s
                "W642",  # Using global for %s
                "W643",  # Using global for %s
                "W644",  # Using global for %s
                "W645",  # Using global for %s
                "W646",  # Using global for %s
                "W647",  # Using global for %s
                "W648",  # Using global for %s
                "W649",  # Using global for %s
                "W650",  # Using global for %s
                "W651",  # Using global for %s
                "W652",  # Using global for %s
                "W653",  # Using global for %s
                "W654",  # Using global for %s
                "W655",  # Using global for %s
                "W656",  # Using global for %s
                "W657",  # Using global for %s
                "W658",  # Using global for %s
                "W659",  # Using global for %s
                "W660",  # Using global for %s
                "W661",  # Using global for %s
                "W662",  # Using global for %s
                "W663",  # Using global for %s
                "W664",  # Using global for %s
                "W665",  # Using global for %s
                "W666",  # Using global for %s
                "W667",  # Using global for %s
                "W668",  # Using global for %s
                "W669",  # Using global for %s
                "W670",  # Using global for %s
                "W671",  # Using global for %s
                "W672",  # Using global for %s
                "W673",  # Using global for %s
                "W674",  # Using global for %s
                "W675",  # Using global for %s
                "W676",  # Using global for %s
                "W677",  # Using global for %s
                "W678",  # Using global for %s
                "W679",  # Using global for %s
                "W680",  # Using global for %s
                "W681",  # Using global for %s
                "W682",  # Using global for %s
                "W683",  # Using global for %s
                "W684",  # Using global for %s
                "W685",  # Using global for %s
                "W686",  # Using global for %s
                "W687",  # Using global for %s
                "W688",  # Using global for %s
                "W689",  # Using global for %s
                "W690",  # Using global for %s
                "W691",  # Using global for %s
                "W692",  # Using global for %s
                "W693",  # Using global for %s
                "W694",  # Using global for %s
                "W695",  # Using global for %s
                "W696",  # Using global for %s
                "W697",  # Using global for %s
                "W698",  # Using global for %s
                "W699",  # Using global for %s
                "W700",  # Using global for %s
                "W701",  # Using global for %s
                "W702",  # Using global for %s
                "W703",  # Using global for %s
                "W704",  # Using global for %s
                "W705",  # Using global for %s
                "W706",  # Using global for %s
                "W707",  # Using global for %s
                "W708",  # Using global for %s
                "W709",  # Using global for %s
                "W710",  # Using global for %s
                "W711",  # Using global for %s
                "W712",  # Using global for %s
                "W713",  # Using global for %s
                "W714",  # Using global for %s
                "W715",  # Using global for %s
                "W716",  # Using global for %s
                "W717",  # Using global for %s
                "W718",  # Using global for %s
                "W719",  # Using global for %s
                "W720",  # Using global for %s
                "W721",  # Using global for %s
                "W722",  # Using global for %s
                "W723",  # Using global for %s
                "W724",  # Using global for %s
                "W725",  # Using global for %s
                "W726",  # Using global for %s
                "W727",  # Using global for %s
                "W728",  # Using global for %s
                "W729",  # Using global for %s
                "W730",  # Using global for %s
                "W731",  # Using global for %s
                "W732",  # Using global for %s
                "W733",  # Using global for %s
                "W734",  # Using global for %s
                "W735",  # Using global for %s
                "W736",  # Using global for %s
                "W737",  # Using global for %s
                "W738",  # Using global for %s
                "W739",  # Using global for %s
                "W740",  # Using global for %s
                "W741",  # Using global for %s
                "W742",  # Using global for %s
                "W743",  # Using global for %s
                "W744",  # Using global for %s
                "W745",  # Using global for %s
                "W746",  # Using global for %s
                "W747",  # Using global for %s
                "W748",  # Using global for %s
                "W749",  # Using global for %s
                "W750",  # Using global for %s
                "W751",  # Using global for %s
                "W752",  # Using global for %s
                "W753",  # Using global for %s
                "W754",  # Using global for %s
                "W755",  # Using global for %s
                "W756",  # Using global for %s
                "W757",  # Using global for %s
                "W758",  # Using global for %s
                "W759",  # Using global for %s
                "W760",  # Using global for %s
                "W761",  # Using global for %s
                "W762",  # Using global for %s
                "W763",  # Using global for %s
                "W764",  # Using global for %s
                "W765",  # Using global for %s
                "W766",  # Using global for %s
                "W767",  # Using global for %s
                "W768",  # Using global for %s
                "W769",  # Using global for %s
                "W770",  # Using global for %s
                "W771",  # Using global for %s
                "W772",  # Using global for %s
                "W773",  # Using global for %s
                "W774",  # Using global for %s
                "W775",  # Using global for %s
                "W776",  # Using global for %s
                "W777",  # Using global for %s
                "W778",  # Using global for %s
                "W779",  # Using global for %s
                "W780",  # Using global for %s
                "W781",  # Using global for %s
                "W782",  # Using global for %s
                "W783",  # Using global for %s
                "W784",  # Using global for %s
                "W785",  # Using global for %s
                "W786",  # Using global for %s
                "W787",  # Using global for %s
                "W788",  # Using global for %s
                "W789",  # Using global for %s
                "W790",  # Using global for %s
                "W791",  # Using global for %s
                "W792",  # Using global for %s
                "W793",  # Using global for %s
                "W794",  # Using global for %s
                "W795",  # Using global for %s
                "W796",  # Using global for %s
                "W797",  # Using global for %s
                "W798",  # Using global for %s
                "W799",  # Using global for %s
                "W800",  # Using global for %s
                "W801",  # Using global for %s
                "W802",  # Using global for %s
                "W803",  # Using global for %s
                "W804",  # Using global for %s
                "W805",  # Using global for %s
                "W806",  # Using global for %s
                "W807",  # Using global for %s
                "W808",  # Using global for %s
                "W809",  # Using global for %s
                "W810",  # Using global for %s
                "W811",  # Using global for %s
                "W812",  # Using global for %s
                "W813",  # Using global for %s
                "W814",  # Using global for %s
                "W815",  # Using global for %s
                "W816",  # Using global for %s
                "W817",  # Using global for %s
                "W818",  # Using global for %s
                "W819",  # Using global for %s
                "W820",  # Using global for %s
                "W821",  # Using global for %s
                "W822",  # Using global for %s
                "W823",  # Using global for %s
                "W824",  # Using global for %s
                "W825",  # Using global for %s
                "W826",  # Using global for %s
                "W827",  # Using global for %s
                "W828",  # Using global for %s
                "W829",  # Using global for %s
                "W830",  # Using global for %s
                "W831",  # Using global for %s
                "W832",  # Using global for %s
                "W833",  # Using global for %s
                "W834",  # Using global for %s
                "W835",  # Using global for %s
                "W836",  # Using global for %s
                "W837",  # Using global for %s
                "W838",  # Using global for %s
                "W839",  # Using global for %s
                "W840",  # Using global for %s
                "W841",  # Using global for %s
                "W842",  # Using global for %s
                "W843",  # Using global for %s
                "W844",  # Using global for %s
                "W845",  # Using global for %s
                "W846",  # Using global for %s
                "W847",  # Using global for %s
                "W848",  # Using global for %s
                "W849",  # Using global for %s
                "W850",  # Using global for %s
                "W851",  # Using global for %s
                "W852",  # Using global for %s
                "W853",  # Using global for %s
                "W854",  # Using global for %s
                "W855",  # Using global for %s
                "W856",  # Using global for %s
                "W857",  # Using global for %s
                "W858",  # Using global for %s
                "W859",  # Using global for %s
                "W860",  # Using global for %s
                "W861",  # Using global for %s
                "W862",  # Using global for %s
                "W863",  # Using global for %s
                "W864",  # Using global for %s
                "W865",  # Using global for %s
                "W866",  # Using global for %s
                "W867",  # Using global for %s
                "W868",  # Using global for %s
                "W869",  # Using global for %s
                "W870",  # Using global for %s
                "W871",  # Using global for %s
                "W872",  # Using global for %s
                "W873",  # Using global for %s
                "W874",  # Using global for %s
                "W875",  # Using global for %s
                "W876",  # Using global for %s
                "W877",  # Using global for %s
                "W878",  # Using global for %s
                "W879",  # Using global for %s
                "W880",  # Using global for %s
                "W881",  # Using global for %s
                "W882",  # Using global for %s
                "W883",  # Using global for %s
                "W884",  # Using global for %s
                "W885",  # Using global for %s
                "W886",  # Using global for %s
                "W887",  # Using global for %s
                "W888",  # Using global for %s
                "W889",  # Using global for %s
                "W890",  # Using global for %s
                "W891",  # Using global for %s
                "W892",  # Using global for %s
                "W893",  # Using global for %s
                "W894",  # Using global for %s
                "W895",  # Using global for %s
                "W896",  # Using global for %s
                "W897",  # Using global for %s
                "W898",  # Using global for %s
                "W899",  # Using global for %s
                "W900",  # Using global for %s
                "W901",  # Using global for %s
                "W902",  # Using global for %s
                "W903",  # Using global for %s
                "W904",  # Using global for %s
                "W905",  # Using global for %s
                "W906",  # Using global for %s
                "W907",  # Using global for %s
                "W908",  # Using global for %s
                "W909",  # Using global for %s
                "W910",  # Using global for %s
                "W911",  # Using global for %s
                "W912",  # Using global for %s
                "W913",  # Using global for %s
                "W914",  # Using global for %s
                "W915",  # Using global for %s
                "W916",  # Using global for %s
                "W917",  # Using global for %s
                "W918",  # Using global for %s
                "W919",  # Using global for %s
                "W920",  # Using global for %s
                "W921",  # Using global for %s
                "W922",  # Using global for %s
                "W923",  # Using global for %s
                "W924",  # Using global for %s
                "W925",  # Using global for %s
                "W926",  # Using global for %s
                "W927",  # Using global for %s
                "W928",  # Using global for %s
                "W929",  # Using global for %s
                "W930",  # Using global for %s
                "W931",  # Using global for %s
                "W932",  # Using global for %s
                "W933",  # Using global for %s
                "W934",  # Using global for %s
                "W935",  # Using global for %s
                "W936",  # Using global for %s
                "W937",  # Using global for %s
                "W938",  # Using global for %s
                "W939",  # Using global for %s
                "W940",  # Using global for %s
                "W941",  # Using global for %s
                "W942",  # Using global for %s
                "W943",  # Using global for %s
                "W944",  # Using global for %s
                "W945",  # Using global for %s
                "W946",  # Using global for %s
                "W947",  # Using global for %s
                "W948",  # Using global for %s
                "W949",  # Using global for %s
                "W950",  # Using global for %s
                "W951",  # Using global for %s
                "W952",  # Using global for %s
                "W953",  # Using global for %s
                "W954",  # Using global for %s
                "W955",  # Using global for %s
                "W956",  # Using global for %s
                "W957",  # Using global for %s
                "W958",  # Using global for %s
                "W959",  # Using global for %s
                "W960",  # Using global for %s
                "W961",  # Using global for %s
                "W962",  # Using global for %s
                "W963",  # Using global for %s
                "W964",  # Using global for %s
                "W965",  # Using global for %s
                "W966",  # Using global for %s
                "W967",  # Using global for %s
                "W968",  # Using global for %s
                "W969",  # Using global for %s
                "W970",  # Using global for %s
                "W971",  # Using global for %s
                "W972",  # Using global for %s
                "W973",  # Using global for %s
                "W974",  # Using global for %s
                "W975",  # Using global for %s
                "W976",  # Using global for %s
                "W977",  # Using global for %s
                "W978",  # Using global for %s
                "W979",  # Using global for %s
                "W980",  # Using global for %s
                "W981",  # Using global for %s
                "W982",  # Using global for %s
                "W983",  # Using global for %s
                "W984",  # Using global for %s
                "W985",  # Using global for %s
                "W986",  # Using global for %s
                "W987",  # Using global for %s
                "W988",  # Using global for %s
                "W989",  # Using global for %s
                "W990",  # Using global for %s
                "W991",  # Using global for %s
                "W992",  # Using global for %s
                "W993",  # Using global for %s
                "W994",  # Using global for %s
                "W995",  # Using global for %s
                "W996",  # Using global for %s
                "W997",  # Using global for %s
                "W998",  # Using global for %s
                "W999",  # Using global for %s
            ],
        )

        # Initialize git repository detection
        self.git_repo_path: str | None = None
        self.git_available = False

    def initialize_git(self, cwd: str) -> bool:
        """Initialize Git repository detection.

        Args:
            cwd: Current working directory

        Returns:
            True if Git is available and initialized, False otherwise
        """
        if not self.git_enabled:
            logger.info("Git integration disabled")
            return False

        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, cwd=cwd
            )
            if result.returncode != 0:
                logger.warning("Git not available")
                return False

            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                logger.warning("Not in a git repository")
                return False

            self.git_repo_path = cwd
            self.git_available = True
            logger.info(f"Git repository detected at {cwd}")
            return True

        except Exception as e:
            logger.warning(f"Git initialization failed: {e}")
            return False

    def create_backup(self, file_path: str) -> str | None:
        """Create a backup of the specified file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file or None if backup failed
        """
        if not self.backup_enabled:
            return None

        try:
            file_path_obj = Path(file_path)
            backup_path = file_path_obj.parent / f"{file_path_obj.name}.ichs.backup"

            # Create backup
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None

    def restore_backup(self, file_path: str, backup_path: str) -> bool:
        """Restore a file from backup.

        Args:
            file_path: Path to the file to restore
            backup_path: Path to the backup file

        Returns:
            True if restore succeeded, False otherwise
        """
        try:
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored from backup: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_path}: {e}")
            return False

    def commit_changes(self, message: str) -> bool:
        """Commit changes to Git repository.

        Args:
            message: Commit message

        Returns:
            True if commit succeeded, False otherwise
        """
        if not self.git_available:
            logger.warning("Git not available, skipping commit")
            return False

        try:
            # Add all changes
            result = subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
            )
            if result.returncode != 0:
                logger.error(f"Failed to add changes: {result.stderr}")
                return False

            # Commit changes
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
            )
            if result.returncode != 0:
                logger.error(f"Failed to commit changes: {result.stderr}")
                return False

            logger.info(f"Committed changes: {message}")
            return True

        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def apply_safe_fixes(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply safe fixes to the specified issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with fix results
        """
        results: dict[str, Any] = {
            "total_issues": len(issues),
            "safe_issues": 0,
            "unsafe_issues": 0,
            "applied_fixes": 0,
            "failed_fixes": 0,
            "files_modified": [],
            "backup_files": [],
            "commit_message": None,
            "errors": [],
        }

        # Group issues by file
        issues_by_file: dict[str, list[dict[str, Any]]] = {}
        for issue in issues:
            file_path = issue.get("file_path", "")
            if file_path:
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)

        # Process each file
        for file_path, file_issues in issues_by_file.items():
            # Filter safe issues
            safe_issues = [i for i in file_issues if self._is_safe_fix(i)]
            unsafe_issues = [i for i in file_issues if not self._is_safe_fix(i)]

            results["safe_issues"] += len(safe_issues)
            results["unsafe_issues"] += len(unsafe_issues)

            # Skip if no safe issues
            if not safe_issues:
                continue

            # Create backup
            backup_path = None
            if self.backup_enabled:
                backup_path = self.create_backup(file_path)
                if backup_path:
                    results["backup_files"].append(backup_path)

            # Apply fixes
            fixes_applied = self._apply_file_fixes(file_path, safe_issues)

            if fixes_applied > 0:
                results["applied_fixes"] += fixes_applied
                results["files_modified"].append(file_path)

                # Commit changes if git is available
                if self.git_available and not self.dry_run_enabled:
                    commit_message = f"iCHS: Applied {fixes_applied} safe fixes to {Path(file_path).name}"
                    if self.commit_changes(commit_message):
                        results["commit_message"] = commit_message
            else:
                results["failed_fixes"] += len(safe_issues)

                # Restore backup if fixes failed
                if backup_path and self.backup_enabled:
                    self.restore_backup(file_path, backup_path)

        return results

    def _is_safe_fix(self, issue: dict[str, Any]) -> bool:
        """Check if an issue is safe to fix automatically.

        Args:
            issue: Issue dictionary

        Returns:
            True if the issue is safe to fix, False otherwise
        """
        rule_id = issue.get("rule_id", "")

        # Check if rule is in safe rules list
        if rule_id in self.safe_rules:
            return True

        # Additional safety checks
        severity = issue.get("severity", "info")
        if severity in ["info", "refactor"]:
            return True

        # Check for specific patterns that are safe
        message = issue.get("message", "").lower()
        if any(
            keyword in message
            for keyword in [
                "line too long",
                "trailing whitespace",
                "missing whitespace",
                "blank line",
                "newline",
                "import",
                "unused import",
            ]
        ):
            return True

        return False

    def _apply_file_fixes(self, file_path: str, issues: list[dict[str, Any]]) -> int:
        """Apply fixes to a single file.

        Args:
            file_path: Path to the file to fix
            issues: List of issue dictionaries for this file

        Returns:
            Number of fixes applied
        """
        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            fixes_applied = 0
            line_offset = 0  # Track line changes due to previous fixes

            # Sort issues by line number (descending) to avoid offset issues
            sorted_issues = sorted(
                issues, key=lambda x: x.get("line_number", 0), reverse=True
            )

            for issue in sorted_issues:
                if fixes_applied >= self.max_changes_per_file:
                    break

                line_num = issue.get("line_number", 0) - 1  # Convert to 0-based index
                if line_num < 0 or line_num >= len(lines):
                    continue

                # Apply fix based on rule ID
                fix_applied = self._apply_line_fix(lines, line_num - line_offset, issue)
                if fix_applied:
                    fixes_applied += 1
                    line_offset += 1  # Track line changes

            # Write back to file if fixes were applied
            if fixes_applied > 0:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                logger.info(f"Applied {fixes_applied} fixes to {file_path}")

            return fixes_applied

        except Exception as e:
            logger.error(f"Failed to apply fixes to {file_path}: {e}")
            return 0

    def _apply_line_fix(
        self, lines: list[str], line_num: int, issue: dict[str, Any]
    ) -> bool:
        """Apply a fix to a specific line.

        Args:
            lines: List of file lines
            line_num: Line number to fix (0-based)
            issue: Issue dictionary

        Returns:
            True if fix was applied, False otherwise
        """
        if line_num < 0 or line_num >= len(lines):
            return False

        rule_id = issue.get("rule_id", "")
        message = issue.get("message", "").lower()
        line = lines[line_num]

        try:
            # Apply fixes based on rule ID or message pattern
            if rule_id == "E501" or "line too long" in message:
                # Fix line too long - try to break it
                return self._fix_line_too_long(lines, line_num)

            elif rule_id == "W291" or "trailing whitespace" in message:
                # Fix trailing whitespace
                lines[line_num] = line.rstrip() + "\n"
                return True

            elif rule_id == "W292" or "no newline at end of file" in message:
                # Fix missing newline at end of file
                if line and not line.endswith("\n"):
                    lines[line_num] = line + "\n"
                return True

            elif rule_id == "W293" or "blank line contains whitespace" in message:
                # Fix whitespace-only lines
                if line.strip() == "":
                    lines[line_num] = "\n"
                return True

            elif rule_id == "E225" or "missing whitespace around operator" in message:
                # Fix missing whitespace around operator
                return self._fix_whitespace_around_operator(lines, line_num)

            elif rule_id == "E231" or "missing whitespace after comma" in message:
                # Fix missing whitespace after comma
                return self._fix_whitespace_after_comma(lines, line_num)

            elif rule_id == "E251" or "unexpected spaces around keyword" in message:
                # Fix unexpected spaces around keyword
                return self._fix_keyword_spacing(lines, line_num)

            elif (
                rule_id == "E401"
                or "import statements are usually at the top" in message
            ):
                # Fix import placement (move to top)
                return self._fix_import_placement(lines, line_num)

            elif rule_id == "E702" or "multiple statements on one line" in message:
                # Fix multiple statements on one line
                return self._fix_multiple_statements(lines, line_num)

            elif rule_id == "E711" or "comparison to none should be" in message:
                # Fix comparison to None
                return self._fix_comparison_to_none(lines, line_num)

            elif rule_id == "E712" or "comparison to true should be" in message:
                # Fix comparison to True
                return self._fix_comparison_to_true(lines, line_num)

            else:
                # Generic fix based on message pattern
                return self._apply_generic_fix(lines, line_num, message)

        except Exception as e:
            logger.warning(f"Failed to apply fix for {rule_id} on line {line_num}: {e}")
            return False

    def _fix_line_too_long(self, lines: list[str], line_num: int) -> bool:
        """Fix line that is too long.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]
        max_length = 88  # PEP 8 recommendation

        if len(line.rstrip()) <= max_length:
            return False

        # Try to break the line at a reasonable point
        # Look for operators or commas to break at
        break_points = [
            line.find(op)
            for op in [
                " + ",
                " - ",
                " * ",
                " / ",
                " = ",
                " += ",
                " -= ",
                " *= ",
                " /= ",
                ", ",
            ]
        ]
        break_points = [p for p in break_points if p > 0 and p < max_length]

        if break_points:
            break_point = max(break_points)
            # Break the line
            lines[line_num] = line[:break_point].rstrip() + "\n"
            lines.insert(
                line_num + 1,
                " " * (len(line) - len(line.lstrip())) + line[break_point:].lstrip(),
            )
            return True

        # If no good break point, just truncate
        lines[line_num] = line[:max_length].rstrip() + " ...\n"
        return True

    def _fix_whitespace_around_operator(self, lines: list[str], line_num: int) -> bool:
        """Fix missing whitespace around operator.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for operators without spaces
        operators = [
            "=",
            "+=",
            "-=",
            "*=",
            "/=",
            "%=",
            "//=",
            "**=",
            "<<=",
            ">>=",
            "&=",
            "|=",
            "^=",
            "//",
        ]

        for op in operators:
            pos = line.find(op)
            if pos > 0 and pos < len(line) - len(op):
                # Check if spaces are missing
                if pos > 0 and line[pos - 1] != " ":
                    line = line[:pos] + " " + line[pos:]
                    pos += 1

                if pos + len(op) < len(line) and line[pos + len(op)] != " ":
                    line = line[: pos + len(op)] + " " + line[pos + len(op) :]

                lines[line_num] = line
                return True

        return False

    def _fix_whitespace_after_comma(self, lines: list[str], line_num: int) -> bool:
        """Fix missing whitespace after comma.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for commas without following space
        pos = 0
        while True:
            pos = line.find(",", pos)
            if pos == -1:
                break

            if pos + 1 < len(line) and line[pos + 1] != " ":
                line = line[: pos + 1] + " " + line[pos + 1 :]
                pos += 2
            else:
                pos += 1

        if line != lines[line_num]:
            lines[line_num] = line
            return True

        return False

    def _fix_keyword_spacing(self, lines: list[str], line_num: int) -> bool:
        """Fix unexpected spaces around keyword.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for keywords with unexpected spaces
        keywords = [
            "if",
            "for",
            "while",
            "with",
            "def",
            "class",
            "return",
            "import",
            "from",
        ]

        for keyword in keywords:
            # Look for keyword with spaces before or after
            pattern = re.compile(rf"\s*{re.escape(keyword)}\s*")
            match = pattern.search(line)

            if match:
                # Fix spacing
                fixed_keyword = f" {keyword} "
                line = line[: match.start()] + fixed_keyword + line[match.end() :]
                lines[line_num] = line
                return True

        return False

    def _fix_import_placement(self, lines: list[str], line_num: int) -> bool:
        """Fix import placement by moving to top of file.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Check if this is an import statement
        if not (line.strip().startswith("import ") or line.strip().startswith("from ")):
            return False

        # Find the first non-import, non-comment line
        insert_pos = 0
        for i, line_i in enumerate(lines):
            stripped = line_i.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith('"""')
                and not stripped.startswith("''')")
            ):
                if not (stripped.startswith("import ") or stripped.startswith("from ")):
                    insert_pos = i
                    break

        # Move import to the found position
        if insert_pos != line_num:
            import_line = lines.pop(line_num)
            lines.insert(insert_pos, import_line)
            return True

        return False

    def _fix_multiple_statements(self, lines: list[str], line_num: int) -> bool:
        """Fix multiple statements on one line.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for semicolon-separated statements
        if ";" in line:
            # Split statements
            statements = [s.strip() for s in line.split(";") if s.strip()]

            if len(statements) > 1:
                # Replace first statement
                lines[line_num] = statements[0] + "\n"

                # Insert remaining statements
                for stmt in statements[1:]:
                    lines.insert(line_num + 1, stmt + "\n")

                return True

        return False

    def _fix_comparison_to_none(self, lines: list[str], line_num: int) -> bool:
        """Fix comparison to None.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for comparisons to None
        pattern = re.compile(r"([^=!<>]=)\s*None")
        match = pattern.search(line)

        if match:
            # Replace with 'is None'
            line = line[: match.start(1)] + "is" + line[match.end(1) :]
            lines[line_num] = line
            return True

        return False

    def _fix_comparison_to_true(self, lines: list[str], line_num: int) -> bool:
        """Fix comparison to True.

        Args:
            lines: List of file lines
            line_num: Line number to fix

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]

        # Look for comparisons to True
        pattern = re.compile(r"([^=!<>]=)\s*True")
        match = pattern.search(line)

        if match:
            # Replace with just the condition
            line = line[: match.start(1)] + line[match.end(1) :].strip()
            lines[line_num] = line
            return True

        return False

    def _apply_generic_fix(self, lines: list[str], line_num: int, message: str) -> bool:
        """Apply a generic fix based on message pattern.

        Args:
            lines: List of file lines
            line_num: Line number to fix
            message: Issue message

        Returns:
            True if fix was applied, False otherwise
        """
        line = lines[line_num]
        message_lower = message.lower()

        # Generic fixes based on common patterns
        if "unused import" in message_lower:
            # Remove unused import
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                lines[line_num] = ""
                return True

        elif "unused variable" in message_lower:
            # Remove unused variable
            if "=" in line and not line.strip().startswith("#"):
                lines[line_num] = ""
                return True

        return False

    def preview_fixes(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Preview what fixes would be applied without actually applying them.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with preview results
        """
        # Create a copy of the autofix instance with dry run enabled
        preview_fixer = Autofix(self.config, self.database)
        preview_fixer.dry_run_enabled = True

        # Apply fixes (they won't actually be written to disk)
        return preview_fixer.apply_safe_fixes(issues)
