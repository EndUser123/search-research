"""
TDD Validator Module

Contains TestFileValidator, GraduatedTDDEnforcer, and related classes for
Test-Driven Development enforcement in the PreToolUse hook.

Extracted from pre_tool_use.py for better modularity and maintainability.
"""

import datetime
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class EnforcementTier(Enum):
    """TDD enforcement tiers for graduated enforcement"""

    TIER0 = "tier0"  # Critical system components - require smoke tests
    TIER1 = "tier1"  # Production application code - require Tier 1 tests
    TIER2 = "tier2"  # Experimental code - advisory mode
    TIER3 = "tier3"  # Configuration and documentation - no TDD required


class FileCategory(Enum):
    """File categories for graduated TDD enforcement"""

    CRITICAL = "critical"  # Production code - strict TDD enforcement
    EXPERIMENTAL = "experimental"  # Experimental code - warning mode
    TEST = "test"  # Test files - no TDD enforcement
    CONFIG = "config"  # Configuration files - no TDD enforcement
    DOC = "doc"  # Documentation files - no TDD enforcement
    BUILD = "build"  # Build artifacts - no TDD enforcement
    UNKNOWN = "unknown"  # Unknown file type - conservative enforcement


class TDDViolationType(Enum):
    """Types of TDD violations"""

    MISSING_TEST_FILE = "missing_test_file"
    TEST_OUT_OF_DATE = "test_out_of_date"
    PRODUCTION_WITHOUT_TESTS = "production_without_tests"
    CRITICAL_FILE_NO_TESTS = "critical_file_no_tests"


class TDDEnforcementAction(Enum):
    """TDD enforcement actions"""

    BLOCK = "block"  # Block the operation
    WARN = "warn"  # Allow with warning
    SUGGEST = "suggest"  # Allow with suggestions
    LOG_ONLY = "log_only"  # Log but don't interfere


@dataclass
class TDDValidationResult:
    """Result of TDD validation"""

    def __init__(
        self,
        allowed: bool,
        reason: str,
        violation_type: TDDViolationType | None = None,
        action: TDDEnforcementAction = TDDEnforcementAction.LOG_ONLY,
        suggestions: list[str] = None,
        test_file_paths: list[str] = None,
    ):
        self.allowed = allowed
        self.reason = reason
        self.violation_type = violation_type
        self.action = action
        self.suggestions = suggestions or []
        self.test_file_paths = test_file_paths or []
        self.timestamp = datetime.datetime.now().isoformat()


class TestFileValidator:
    """
    Smart test file validation engine with pattern recognition and graduated enforcement.
    """

    def __init__(self):
        self.source_patterns = self._init_source_patterns()
        self.test_patterns = self._init_test_patterns()
        self.category_patterns = self._init_category_patterns()
        self.exclusion_patterns = self._init_exclusion_patterns()

    def _init_source_patterns(self) -> list[dict[str, Any]]:
        """Initialize source file patterns for different languages"""
        return [
            # Python
            {
                "pattern": r"^.*\.py$",
                "language": "python",
                "test_correspondence": [
                    r"^test_(.*).py$",
                    r"^(.*)_test\.py$",
                    r"^tests/(.*).py$",
                    r"^tests/test_(.*).py$",
                    r"^test/(.*).py$",
                ],
            },
            # JavaScript/TypeScript
            {
                "pattern": r"^.*\.(js|ts)$",
                "language": "javascript",
                "test_correspondence": [
                    r"^.*\.test\.(js|ts)$",
                    r"^.*\.spec\.(js|ts)$",
                    r"^test/.*\.(js|ts)$",
                    r"^tests/.*\.(js|ts)$",
                ],
            },
            # TypeScript
            {
                "pattern": r"^.*\.tsx?$",
                "language": "typescript",
                "test_correspondence": [
                    r"^.*\.test\.tsx?$",
                    r"^.*\.spec\.tsx?$",
                    r"^test/.*\.tsx?$",
                    r"^tests/.*\.tsx?$",
                ],
            },
            # Java
            {
                "pattern": r"^.*\.java$",
                "language": "java",
                "test_correspondence": [
                    r"^.*Test\.java$",
                    r"^.*Tests\.java$",
                    r"^test/.*\.java$",
                    r"^src/test/.*\.java$",
                ],
            },
            # C/C++
            {
                "pattern": r"^.*\.(c|cpp|cc|cxx|h|hpp)$",
                "language": "cpp",
                "test_correspondence": [
                    r"^.*_test\.(c|cpp|cc|cxx)$",
                    r"^test_.*\.(c|cpp|cc|cxx)$",
                    r"^test/.*\.(c|cpp|cc|cxx)$",
                ],
            },
            # Rust
            {
                "pattern": r"^.*\.rs$",
                "language": "rust",
                "test_correspondence": [r"^.*_test\.rs$", r"^tests/.*\.rs$"],
            },
            # Go
            {
                "pattern": r"^.*\.go$",
                "language": "go",
                "test_correspondence": [r"^.*_test\.go$"],
            },
        ]

    def _init_test_patterns(self) -> list[str]:
        """Patterns that identify test files"""
        return [
            r"^test_.*\.py$",
            r"^.*_test\.py$",
            r"^tests/.*\.py$",
            r"^tests/test_.*\.py$",
            r"^test/.*\.py$",
            r"^.*\.test\.(js|ts|tsx)$",
            r"^.*\.spec\.(js|ts|tsx)$",
            r"^test/.*\.(js|ts|tsx)$",
            r"^tests/.*\.(js|ts|tsx)$",
            r"^.*Test\.java$",
            r"^.*Tests\.java$",
            r"^src/test/.*\.java$",
            r"^.*_test\.(c|cpp|cc|cxx)$",
            r"^test_.*\.(c|cpp|cc|cxx)$",
            r"^test/.*\.(c|cpp|cc|cxx)$",
            r"^.*_test\.rs$",
            r"^tests/.*\.rs$",
            r"^.*_test\.go$",
        ]

    def _init_category_patterns(self) -> dict[FileCategory, list[dict[str, Any]]]:
        """Initialize file category patterns for graduated enforcement"""
        return {
            FileCategory.CRITICAL: [
                # Core application code
                {
                    "pattern": r"^src/.*\.(py|js|ts|java|cpp|c|rs|go)$",
                    "description": "Source code",
                },
                {
                    "pattern": r"^lib/.*\.(py|js|ts|java|cpp|c|rs|go)$",
                    "description": "Library code",
                },
                {
                    "pattern": r"^app/.*\.(py|js|ts|java|cpp|c|rs|go)$",
                    "description": "Application code",
                },
                # Core configuration files
                {
                    "pattern": r"^.*(main|index|app|core)\.(py|js|ts|java)$",
                    "description": "Main application files",
                },
                # Production API files
                {"pattern": r"^.*api/.*\.(py|js|ts)$", "description": "API code"},
                {"pattern": r"^.*server\.(py|js|ts)$", "description": "Server code"},
                {
                    "pattern": r"^.*service/.*\.(py|js|ts)$",
                    "description": "Service code",
                },
            ],
            FileCategory.EXPERIMENTAL: [
                # Experimental and prototype code
                {
                    "pattern": r"^.*experimental.*\.(py|js|ts)$",
                    "description": "Experimental code",
                },
                {
                    "pattern": r"^.*prototype.*\.(py|js|ts)$",
                    "description": "Prototype code",
                },
                {
                    "pattern": r"^.*sandbox.*\.(py|js|ts)$",
                    "description": "Sandbox code",
                },
                {"pattern": r"^.*demo.*\.(py|js|ts)$", "description": "Demo code"},
                {"pattern": r"^temp/.*\.(py|js|ts)$", "description": "Temporary code"},
                {"pattern": r"^tmp/.*\.(py|js|ts)$", "description": "Temporary code"},
            ],
            FileCategory.TEST: [
                # Test files (excluded from TDD enforcement)
                {"pattern": r"^test_.*\.py$", "description": "Python test file"},
                {"pattern": r"^.*_test\.py$", "description": "Python test file"},
                {"pattern": r"^tests/.*\.py$", "description": "Python test file"},
                {
                    "pattern": r"^.*\.test\.(js|ts|tsx)$",
                    "description": "JavaScript/TypeScript test",
                },
                {
                    "pattern": r"^.*\.spec\.(js|ts|tsx)$",
                    "description": "JavaScript/TypeScript spec",
                },
                {
                    "pattern": r"^test/.*\.(js|ts|tsx)$",
                    "description": "JavaScript/TypeScript test directory",
                },
                {"pattern": r"^conftest\.py$", "description": "Pytest configuration"},
            ],
            FileCategory.CONFIG: [
                # Configuration files (excluded from TDD enforcement)
                {
                    "pattern": r"^.*\.(json|yaml|yml|toml|ini|cfg|conf)$",
                    "description": "Configuration file",
                },
                {
                    "pattern": r"^.*\.(env|env\.local|env\.prod)$",
                    "description": "Environment configuration",
                },
                {"pattern": r"^.*Dockerfile$", "description": "Docker configuration"},
                {
                    "pattern": r"^docker-compose.*\.ya?ml$",
                    "description": "Docker Compose configuration",
                },
                {
                    "pattern": r"^.*requirements.*\.txt$",
                    "description": "Python requirements",
                },
                {
                    "pattern": r"^pyproject\.toml$",
                    "description": "Python project configuration",
                },
                {
                    "pattern": r"^package\.json$",
                    "description": "Node.js package configuration",
                },
            ],
            FileCategory.DOC: [
                # Documentation files (excluded from TDD enforcement)
                {
                    "pattern": r"^.*\.(md|rst|txt|adoc)$",
                    "description": "Documentation file",
                },
                {"pattern": r"^README.*", "description": "README file"},
                {"pattern": r"^CHANGELOG.*", "description": "Changelog file"},
                {"pattern": r"^LICENSE.*", "description": "License file"},
            ],
            FileCategory.BUILD: [
                # Build artifacts (excluded from TDD enforcement)
                {"pattern": r"^.*\.(lock|sum)$", "description": "Lock file"},
                {"pattern": r"^package-lock\.json$", "description": "NPM lock file"},
                {"pattern": r"^yarn\.lock$", "description": "Yarn lock file"},
                {"pattern": r"^Pipfile\.lock$", "description": "Pipenv lock file"},
                {"pattern": r"^poetry\.lock$", "description": "Poetry lock file"},
            ],
        }

    def _init_exclusion_patterns(self) -> list[str]:
        """Patterns for files excluded from TDD enforcement"""
        return [
            r"^__pycache__/.*",
            r"^.*\.pyc$",
            r"^.*\.pyo$",
            r"^.*\.pyd$",
            r"^\.git/.*",
            r"^node_modules/.*",
            r"^\.venv/.*",
            r"^venv/.*",
            r"^env/.*",
            r"^\.env$",
            r"^\.DS_Store$",
            r"^Thumbs\.db$",
            r"^.*\.swp$",
            r"^.*\.swo$",
            r"^.*~$",
            r"^.*\.bak$",
            r"^.*\.tmp$",
        ]

    def is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file based on patterns"""
        file_path = file_path.replace("\\", "/").lower()
        for pattern in self.test_patterns:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def is_excluded_file(self, file_path: str) -> bool:
        """Check if file should be excluded from TDD enforcement"""
        file_path = file_path.replace("\\", "/").lower()
        for pattern in self.exclusion_patterns:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def categorize_file(self, file_path: str) -> FileCategory:
        """Categorize file for graduated enforcement"""
        if self.is_test_file(file_path):
            return FileCategory.TEST
        if self.is_excluded_file(file_path):
            return FileCategory.UNKNOWN  # Will be handled conservatively

        file_path = file_path.replace("\\", "/").lower()

        for category, patterns in self.category_patterns.items():
            for pattern_info in patterns:
                if re.match(pattern_info["pattern"], file_path, re.IGNORECASE):
                    return category

        return FileCategory.UNKNOWN

    def find_corresponding_test_files(self, source_file_path: str) -> list[str]:
        """Find test files that correspond to a source file"""
        source_file_path = source_file_path.replace("\\", "/")
        source_dir = Path(source_file_path).parent
        source_name = Path(source_file_path).stem

        test_files = []

        # Find matching source pattern
        for source_pattern_info in self.source_patterns:
            if re.match(
                source_pattern_info["pattern"], source_file_path, re.IGNORECASE
            ):
                # Generate possible test file paths
                for test_pattern in source_pattern_info["test_correspondence"]:
                    # For each test pattern, try to generate test file paths
                    if "{1}" in test_pattern:  # Back reference pattern
                        test_path = re.sub(
                            r"^.*\/([^\/]+)\.([^\.]+)$", test_pattern, source_file_path
                        )
                        if os.path.exists(test_path):
                            test_files.append(test_path)
                    else:
                        # Try to find test files by searching directories
                        for test_file in self._search_test_files(
                            source_dir, source_name, source_pattern_info["language"]
                        ):
                            if test_file not in test_files:
                                test_files.append(test_file)

        return test_files

    def _search_test_files(
        self, source_dir: Path, source_name: str, language: str
    ) -> list[str]:
        """Search for test files in common test directories"""
        test_dirs = ["test", "tests", "spec", "specs", "__tests__"]
        test_files = []

        # Search in source directory
        for test_dir in test_dirs:
            test_dir_path = source_dir / test_dir
            if test_dir_path.exists():
                # Search for files with test-related names
                for pattern in [
                    f"test_{source_name}.*",
                    f"{source_name}_test.*",
                    f"{source_name}.test.*",
                    f"{source_name}.spec.*",
                ]:
                    for test_file in test_dir_path.glob(pattern):
                        if test_file.is_file():
                            test_files.append(str(test_file))

        # Search in parent directories
        current_dir = source_dir
        for _ in range(3):  # Search up to 3 levels up
            parent_dir = current_dir.parent
            for test_dir in test_dirs:
                test_dir_path = parent_dir / test_dir
                if test_dir_path.exists():
                    for pattern in [
                        f"test_{source_name}.*",
                        f"{source_name}_test.*",
                        f"{source_name}.test.*",
                        f"{source_name}.spec.*",
                    ]:
                        for test_file in test_dir_path.glob(f"**/{pattern}"):
                            if test_file.is_file():
                                test_files.append(str(test_file))
            current_dir = parent_dir

        return test_files

    def validate_tdd_compliance(
        self, file_path: str, operation: str
    ) -> TDDValidationResult:
        """
        Validate TDD compliance for a file operation.

        Args:
            file_path: Path to the file being operated on
            operation: Type of operation (Edit, Write, Read)

        Returns:
            TDDValidationResult with enforcement decision and guidance
        """
        # Read operations don't need TDD enforcement
        if operation == "Read":
            return TDDValidationResult(
                allowed=True,
                reason="Read operation - no TDD enforcement required",
                action=TDDEnforcementAction.LOG_ONLY,
            )

        # Check if file is excluded
        if self.is_excluded_file(file_path):
            return TDDValidationResult(
                allowed=True,
                reason="File excluded from TDD enforcement",
                action=TDDEnforcementAction.LOG_ONLY,
            )

        # Categorize the file
        category = self.categorize_file(file_path)

        # Test files don't need TDD enforcement
        if category == FileCategory.TEST:
            return TDDValidationResult(
                allowed=True,
                reason="Test file - no TDD enforcement required",
                action=TDDEnforcementAction.LOG_ONLY,
            )

        # Config, doc, and build files don't need TDD enforcement
        if category in [FileCategory.CONFIG, FileCategory.DOC, FileCategory.BUILD]:
            return TDDValidationResult(
                allowed=True,
                reason=f"{category.value} file - no TDD enforcement required",
                action=TDDEnforcementAction.LOG_ONLY,
            )

        # Find corresponding test files
        test_files = self.find_corresponding_test_files(file_path)

        # Check TDD compliance based on category
        if category == FileCategory.CRITICAL:
            return self._validate_critical_file(file_path, test_files)
        elif category == FileCategory.EXPERIMENTAL:
            return self._validate_experimental_file(file_path, test_files)
        else:
            return self._validate_unknown_file(file_path, test_files)

    def _validate_critical_file(
        self, file_path: str, test_files: list[str]
    ) -> TDDValidationResult:
        """Validate critical production files with strict TDD enforcement"""
        if not test_files:
            return TDDValidationResult(
                allowed=False,
                reason=f"Critical production file '{Path(file_path).name}' has no corresponding test files",
                violation_type=TDDViolationType.CRITICAL_FILE_NO_TESTS,
                action=TDDEnforcementAction.BLOCK,
                suggestions=self._generate_test_creation_suggestions(file_path),
                test_file_paths=[],
            )

        # Check if test files are recent (simple heuristic)
        if self._are_tests_out_of_date(file_path, test_files):
            return TDDValidationResult(
                allowed=False,
                reason=f"Test files for '{Path(file_path).name}' appear to be out of date",
                violation_type=TDDViolationType.TEST_OUT_OF_DATE,
                action=TDDEnforcementAction.BLOCK,
                suggestions=[
                    "Update existing test files to reflect recent code changes",
                    "Run existing tests to ensure they pass",
                    "Add new tests for any new functionality",
                ],
                test_file_paths=test_files,
            )

        return TDDValidationResult(
            allowed=True,
            reason=f"Critical file '{Path(file_path).name}' has corresponding test files: {[Path(f).name for f in test_files]}",
            action=TDDEnforcementAction.LOG_ONLY,
            test_file_paths=test_files,
        )

    def _validate_experimental_file(
        self, file_path: str, test_files: list[str]
    ) -> TDDValidationResult:
        """Validate experimental files with warning mode"""
        suggestions = []

        if not test_files:
            suggestions.extend(self._generate_test_creation_suggestions(file_path))
            suggestions.append(
                "Consider using spike and stabilize pattern: prototype first, then add tests"
            )

            return TDDValidationResult(
                allowed=True,
                reason=f"Experimental file '{Path(file_path).name}' has no tests (allowed in experimental mode)",
                action=TDDEnforcementAction.WARN,
                suggestions=suggestions,
                test_file_paths=[],
            )

        return TDDValidationResult(
            allowed=True,
            reason=f"Experimental file '{Path(file_path).name}' has test files (good practice)",
            action=TDDEnforcementAction.SUGGEST,
            suggestions=[
                "Consider stabilizing this code and moving to production directory"
            ],
            test_file_paths=test_files,
        )

    def _validate_unknown_file(
        self, file_path: str, test_files: list[str]
    ) -> TDDValidationResult:
        """Validate unknown files with conservative enforcement"""
        if not test_files:
            return TDDValidationResult(
                allowed=True,
                reason=f"File '{Path(file_path).name}' of unknown category has no tests (conservative allowance)",
                action=TDDEnforcementAction.SUGGEST,
                suggestions=self._generate_test_creation_suggestions(file_path)
                + [
                    "Consider moving this file to an appropriate directory structure",
                    "Add test files to ensure code quality and reliability",
                ],
                test_file_paths=[],
            )

        return TDDValidationResult(
            allowed=True,
            reason=f"File '{Path(file_path).name}' has corresponding test files",
            action=TDDEnforcementAction.LOG_ONLY,
            test_file_paths=test_files,
        )

    def _generate_test_creation_suggestions(self, source_file_path: str) -> list[str]:
        """Generate helpful suggestions for test file creation"""
        source_name = Path(source_file_path).stem
        source_ext = Path(source_file_path).suffix
        source_dir = Path(source_file_path).parent

        suggestions = []

        # Language-specific suggestions
        if source_ext == ".py":
            suggestions.extend(
                [
                    f"Create test file: test_{source_name}.py",
                    f"Create test file: {source_name}_test.py",
                    f"Create test in tests/test_{source_name}.py",
                    "Use pytest framework for testing",
                    "Include unit tests for all public methods",
                    "Add integration tests for external dependencies",
                ]
            )
        elif source_ext in [".js", ".ts", ".tsx"]:
            suggestions.extend(
                [
                    f"Create test file: {source_name}.test{source_ext}",
                    f"Create test file: {source_name}.spec{source_ext}",
                    "Use Jest or Mocha for testing",
                    "Include tests for all exported functions/classes",
                    "Add mock tests for external API calls",
                ]
            )
        elif source_ext == ".java":
            suggestions.extend(
                [
                    f"Create test file: {source_name}Test.java",
                    f"Create test file: {source_name}Tests.java",
                    "Use JUnit or TestNG for testing",
                    "Add tests in src/test/java directory",
                    "Include tests for all public methods",
                ]
            )
        else:
            suggestions.extend(
                [
                    f"Create test file: test_{source_name}{source_ext}",
                    f"Create test file: {source_name}_test{source_ext}",
                    "Include unit tests for core functionality",
                    "Add integration tests for system interactions",
                ]
            )

        # Directory structure suggestions
        try:
            relative_source = str(
                Path(source_file_path).relative_to(Path.cwd())
            ).replace("\\", "/")
            suggestions.append(
                f"Recommended test directory structure: tests/{relative_source}"
            )
        except ValueError:
            pass
        return suggestions

    def _are_tests_out_of_date(
        self, source_file_path: str, test_files: list[str]
    ) -> bool:
        """Simple heuristic to check if test files might be out of date"""
        try:
            source_mtime = os.path.getmtime(source_file_path)
            for test_file in test_files:
                if os.path.exists(test_file):
                    test_mtime = os.path.getmtime(test_file)
                    # If source is significantly newer than test, consider it out of date
                    if source_mtime - test_mtime > 3600:  # 1 hour difference
                        return True
            return False
        except OSError:
            # If we can't check modification times, assume tests are not out of date
            return False


class GraduatedTDDEnforcer:
    """
    Graduated TDD enforcement with environment variable toggles and tier-based blocking.
    """

    def __init__(self):
        self.config = self._load_tdd_config()
        self.env_config = self._load_environment_config()
        self.enforcement_tiers = self.config.get("enforcement_tiers", {})
        self.classification_rules = self.config.get("classification_rules", {})

    def _load_tdd_config(self) -> dict[str, Any]:
        """Load TDD configuration from tier1_tests.yaml using SystemConfig"""
        try:
            from pathlib import Path

            # Try to load from various possible locations
            possible_paths = [
                Path("__csf/config/tier1_tests.yaml"),
                Path(".claude/config/tier1_tests.yaml"),
                Path.cwd() / "tier1_tests.yaml",
            ]

            for config_path in possible_paths:
                if config_path.exists():
                    import yaml

                    with open(config_path) as f:
                        return yaml.safe_load(f)
        except Exception:
            pass

        # Fallback default configuration
        return {
            "enforcement_tiers": {
                "tier0": {
                    "name": "Critical System Components",
                    "required_test_level": "tier0",
                    "enforcement_mode": "block",
                    "directory_patterns": [
                        "src/features/core_utils/",
                        "src/features/modules/standardization/",
                        ".claude/hooks/",
                        "src/core/",
                    ],
                },
                "tier1": {
                    "name": "Production Application Code",
                    "required_test_level": "tier1",
                    "enforcement_mode": "block",
                    "directory_patterns": [
                        "src/",
                        "lib/",
                        "app/",
                        "api/",
                        "services/",
                        "server/",
                    ],
                },
            }
        }

    def _load_environment_config(self) -> dict[str, Any]:
        """Load environment variable configuration"""
        return {
            "CSF_STRICT_MODE": False,
            "CSF_TIER1_BLOCKING": True,
            "CSF_NEW_FIREWALL_RULES": True,
            "CSF_DEBUG_MODE": False,
            "CSF_PERFORMANCE_MODE": False,
            "CSF_TDD_LEVEL": "auto",
            "CSF_TDD_EVIDENCE": True,
        }

    def determine_enforcement_tier(
        self, file_path: str
    ) -> tuple[EnforcementTier, dict[str, Any]]:
        """
        Determine enforcement tier for a file path.

        Returns:
            Tuple of (EnforcementTier, tier_config)
        """
        normalized_path = file_path.replace("\\", "/").lower()

        # Check if TDD enforcement is disabled
        if not self.env_config["CSF_NEW_FIREWALL_RULES"]:
            return EnforcementTier.TIER3, {"enforcement_mode": "log_only"}

        # Strict mode upgrades all to block
        if self.env_config["CSF_STRICT_MODE"]:
            return EnforcementTier.TIER1, {"enforcement_mode": "block"}

        # Check tiers in order of precedence (Tier 0 first, then Tier 1, etc.)
        for tier_key in ["tier0", "tier1", "tier2"]:
            tier_config = self.enforcement_tiers.get(tier_key, {})
            patterns = tier_config.get("directory_patterns", [])

            for pattern in patterns:
                if self._path_matches_pattern(normalized_path, pattern):
                    tier = EnforcementTier(tier_key)
                    return tier, tier_config

        # Default to Tier 3 (no TDD required)
        return EnforcementTier.TIER3, {"enforcement_mode": "log_only"}

    def _path_matches_pattern(self, normalized_path: str, pattern: str) -> bool:
        """Check if a path matches a directory pattern"""
        normalized_pattern = pattern.replace("\\", "/").lower()
        regex_pattern = normalized_pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}"
        return bool(re.match(regex_pattern, normalized_path))

    def validate_tdd_requirements(
        self,
        file_path: str,
        enforcement_tier: EnforcementTier,
        tier_config: dict[str, Any],
        test_validator: TestFileValidator,
    ) -> dict[str, Any]:
        """
        Validate TDD requirements based on enforcement tier.

        Returns:
            Dict with validation result and enforcement decision
        """
        result = {
            "allowed": True,
            "reason": "TDD validation passed",
            "enforcement_tier": enforcement_tier.value,
            "enforcement_mode": tier_config.get("enforcement_mode", "log_only"),
            "violations": [],
            "suggestions": [],
            "test_files_found": [],
        }

        # No validation needed for Tier 3 or log_only mode
        if (
            enforcement_tier == EnforcementTier.TIER3
            or tier_config.get("enforcement_mode") == "log_only"
        ):
            return result

        # Find test files using the existing test validator
        test_files = test_validator.find_corresponding_test_files(file_path)
        result["test_files_found"] = test_files

        # Tier 0: Require smoke tests
        if enforcement_tier == EnforcementTier.TIER0:
            has_smoke_tests = self._check_smoke_tests(file_path, [])
            if not has_smoke_tests:
                result["violations"].append(
                    {
                        "type": "missing_smoke_tests",
                        "severity": "critical",
                        "message": "Critical system component requires smoke tests",
                    }
                )
                result["suggestions"].extend(
                    [
                        "Create smoke test in tests/test_smoke_*.py",
                        "Ensure smoke tests execute in <2 seconds",
                        "Focus on basic system health validation",
                    ]
                )

        # Tier 1: Require Tier 1 tests
        elif enforcement_tier == EnforcementTier.TIER1:
            if not test_files:
                result["violations"].append(
                    {
                        "type": "missing_tier1_tests",
                        "severity": "high",
                        "message": "Production code requires Tier 1 tests",
                    }
                )
                result["suggestions"].extend(
                    [
                        "Create comprehensive test file in tests/test_*.py",
                        "Ensure test coverage meets requirements (>=80%)",
                        "Include integration tests for external dependencies",
                    ]
                )

        # Tier 2: Advisory mode
        elif enforcement_tier == EnforcementTier.TIER2:
            if not test_files:
                result["violations"].append(
                    {
                        "type": "advisory_no_tests",
                        "severity": "low",
                        "message": "Experimental code has no tests (advisory)",
                    }
                )
                result["suggestions"].extend(
                    [
                        "Consider adding tests for experimental code",
                        "Use spike and stabilize pattern",
                        "Document experimental approach",
                    ]
                )

        # Determine if operation should be blocked
        enforcement_mode = tier_config.get("enforcement_mode", "log_only")
        critical_violations = [
            v for v in result["violations"] if v["severity"] in ["critical", "high"]
        ]

        if enforcement_mode == "block" and critical_violations:
            result["allowed"] = False
            result["reason"] = (
                f"TDD violation in {enforcement_tier.value}: {critical_violations[0]['message']}"
            )

        return result

    def _check_smoke_tests(self, file_path: str, smoke_patterns: list[str]) -> bool:
        """Check if smoke tests exist for the critical component"""
        base_name = Path(file_path).stem
        smoke_test_names = [
            f"test_smoke_{base_name}.py",
            f"test_{base_name}_smoke.py",
            f"smoke_test_{base_name}.py",
        ]
        for smoke_name in smoke_test_names:
            if Path(smoke_name).exists():
                return True
        return False
