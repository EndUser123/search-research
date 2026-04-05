"""
BugJail Pattern Library

Comprehensive collection of bug detection patterns for multiple languages.
"""

import json
import os

from ..core.types import BugCategory, BugSeverity, DetectionPattern, VulnerabilityType


class PatternLibrary:
    """
    Library of bug detection patterns.

    Maintains patterns for multiple languages and bug categories,
    with support for custom patterns and updates.
    """

    def __init__(self):
        """Initialize pattern library."""
        self._patterns: dict[str, list[DetectionPattern]] = {
            "python": [],
            "javascript": [],
            "typescript": [],
            "java": [],
            "cpp": [],
            "c": [],
            "csharp": [],
            "go": [],
            "rust": []
        }
        self._loaded_builtin = False

    def load_builtin_patterns(self):
        """Load built-in detection patterns."""
        if self._loaded_builtin:
            return

        # Python patterns
        self._patterns["python"].extend([
            DetectionPattern(
                id="py_null_pointer_001",
                name="Potential None dereference",
                category=BugCategory.NULL_POINTER,
                severity=BugSeverity.HIGH,
                pattern=r"(\w+)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
                language="python",
                description="Method call on variable that could be None",
                tags={"null-check", "dereference"},
                references=["https://docs.python.org/3/library/exceptions.html#NoneType"],
                confidence_threshold=0.7
            ),
            DetectionPattern(
                id="py_resource_leak_001",
                name="File without context manager",
                category=BugCategory.RESOURCE_LEAK,
                severity=BugSeverity.HIGH,
                pattern=r"open\s*\([^)]+\)(?!\s*\.close\(\))(?!\s*with)",
                language="python",
                description="File opened without context manager or explicit close",
                tags={"resource-leak", "file-handle"},
                confidence_threshold=0.9
            ),
            DetectionPattern(
                id="py_division_by_zero_001",
                name="Division by zero",
                category=BugCategory.DIVISION_BY_ZERO,
                severity=BugSeverity.CRITICAL,
                pattern=r"/\s*0\b",
                language="python",
                description="Division operation with literal zero",
                tags={"division", "zero", "runtime-error"},
                confidence_threshold=1.0
            ),
            DetectionPattern(
                id="py_logic_error_001",
                name="Assignment in condition",
                category=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.HIGH,
                pattern=r"if\s*\([^)]*=[^)]*\)",
                language="python",
                description="Assignment operator used in conditional statement",
                tags={"logic-error", "assignment"},
                confidence_threshold=0.8
            ),
            DetectionPattern(
                id="py_race_condition_001",
                name="Non-atomic increment",
                category=BugCategory.RACE_CONDITION,
                severity=BugSeverity.MEDIUM,
                pattern=r"(\w+)\s*=\s*(\w+)\s*\+\s*1",
                language="python",
                description="Non-atomic increment operation",
                tags={"race-condition", "thread-safety"},
                confidence_threshold=0.6
            ),
            DetectionPattern(
                id="py_eval_usage_001",
                name="Use of eval() function",
                category=BugCategory.API_MISUSE,
                severity=BugSeverity.CRITICAL,
                pattern=r"eval\s*\(",
                language="python",
                description="Use of eval() function poses security risk",
                tags={"security", "code-injection"},
                confidence_threshold=0.9
            ),
            DetectionPattern(
                id="py_exec_usage_001",
                name="Use of exec() function",
                category=BugCategory.API_MISUSE,
                severity=BugSeverity.CRITICAL,
                pattern=r"exec\s*\(",
                language="python",
                description="Use of exec() function poses security risk",
                tags={"security", "code-injection"},
                confidence_threshold=0.9
            ),
            DetectionPattern(
                id="py_assert_in_production_001",
                name="Assert in production code",
                category=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.MEDIUM,
                pattern=r"assert\s+",
                language="python",
                description="Assert statements should not be used in production",
                tags={"assert", "production"},
                confidence_threshold=0.5
            )
        ])

        # JavaScript patterns
        self._patterns["javascript"].extend([
            DetectionPattern(
                id="js_null_pointer_001",
                name="Potential null dereference",
                category=BugCategory.NULL_POINTER,
                severity=BugSeverity.HIGH,
                pattern=r"(\w+)\.([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(",
                language="javascript",
                description="Method call on variable that could be null",
                tags={"null-check", "dereference"},
                confidence_threshold=0.6
            ),
            DetectionPattern(
                id="js_equality_001",
                name="Use of == instead of ===",
                category=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.MEDIUM,
                pattern=r"==\s*[^=]",
                language="javascript",
                description="Use strict equality (===) instead of loose equality (==)",
                tags={"equality", "type-coercion"},
                confidence_threshold=0.7
            ),
            DetectionPattern(
                id="js_global_leak_001",
                name="Undeclared variable assignment",
                category=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.LOW,
                pattern=r"(\w+)\s*=",
                language="javascript",
                description="Assignment to undeclared variable creates global",
                tags={"global-leak", "scope"},
                confidence_threshold=0.5
            ),
            DetectionPattern(
                id="js_eval_usage_001",
                name="Use of eval()",
                category=BugCategory.API_MISUSE,
                severity=BugSeverity.CRITICAL,
                pattern=r"eval\s*\(",
                language="javascript",
                description="Use of eval() function poses security risk",
                tags={"security", "code-injection"},
                confidence_threshold=0.9
            )
        ])

        # TypeScript patterns (inherit JavaScript patterns)
        self._patterns["typescript"].extend(self._patterns["javascript"].copy())

        # Java patterns
        self._patterns["java"].extend([
            DetectionPattern(
                id="java_null_pointer_001",
                name="Potential null dereference",
                category=BugCategory.NULL_POINTER,
                severity=BugSeverity.HIGH,
                pattern=r"(\w+)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
                language="java",
                description="Method call on variable that could be null",
                tags={"null-check", "dereference"},
                confidence_threshold=0.6
            ),
            DetectionPattern(
                id="java_resource_leak_001",
                name="Resource without try-with-resources",
                category=BugCategory.RESOURCE_LEAK,
                severity=BugSeverity.HIGH,
                pattern=r"new\s+(FileInputStream|FileOutputStream|BufferedReader|Connection)\s*\(",
                language="java",
                description="Resource created without try-with-resources",
                tags={"resource-leak", "io-resource"},
                confidence_threshold=0.7
            ),
            DetectionPattern(
                id="java_equals_hashcode_001",
                name="equals() without hashCode()",
                category=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.HIGH,
                pattern=r"public\s+boolean\s+equals\s*\(",
                language="java",
                description="equals() implemented without hashCode()",
                tags={"equals-hashcode", "contract"},
                confidence_threshold=0.8
            )
        ])

        self._loaded_builtin = True

    def get_patterns_for_language(self, language: str) -> list[DetectionPattern]:
        """Get all patterns for a specific language."""
        return self._patterns.get(language.lower(), [])

    def add_pattern(self, pattern: DetectionPattern):
        """Add a new pattern to the library."""
        language = pattern.language.lower()
        if language not in self._patterns:
            self._patterns[language] = []
        self._patterns[language].append(pattern)

    def add_patterns(self, patterns: list[DetectionPattern]):
        """Add multiple patterns to the library."""
        for pattern in patterns:
            self.add_pattern(pattern)

    def load_patterns_from_file(self, file_path: str):
        """Load patterns from JSON file."""
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, encoding='utf-8') as f:
                patterns_data = json.load(f)

            for pattern_data in patterns_data.get("patterns", []):
                pattern = self._deserialize_pattern(pattern_data)
                if pattern:
                    self.add_pattern(pattern)

        except Exception as e:
            print(f"Error loading patterns from {file_path}: {e}")

    def save_patterns_to_file(self, file_path: str, language: str = None):
        """Save patterns to JSON file."""
        patterns_to_save = []

        if language:
            patterns_to_save = self.get_patterns_for_language(language)
        else:
            for lang_patterns in self._patterns.values():
                patterns_to_save.extend(lang_patterns)

        patterns_data = {
            "patterns": [self._serialize_pattern(p) for p in patterns_to_save]
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving patterns to {file_path}: {e}")

    def get_pattern_by_id(self, pattern_id: str) -> DetectionPattern:
        """Get pattern by ID across all languages."""
        for patterns in self._patterns.values():
            for pattern in patterns:
                if pattern.id == pattern_id:
                    return pattern
        return None

    def get_patterns_by_category(self, category: BugCategory) -> list[DetectionPattern]:
        """Get all patterns matching a category."""
        matching_patterns = []
        for patterns in self._patterns.values():
            matching_patterns.extend([p for p in patterns if p.category == category])
        return matching_patterns

    def get_patterns_by_severity(self, severity: BugSeverity) -> list[DetectionPattern]:
        """Get all patterns matching a severity level."""
        matching_patterns = []
        for patterns in self._patterns.values():
            matching_patterns.extend([p for p in patterns if p.severity == severity])
        return matching_patterns

    def enable_pattern(self, pattern_id: str):
        """Enable a pattern by ID."""
        pattern = self.get_pattern_by_id(pattern_id)
        if pattern:
            pattern.enabled = True

    def disable_pattern(self, pattern_id: str):
        """Disable a pattern by ID."""
        pattern = self.get_pattern_by_id(pattern_id)
        if pattern:
            pattern.enabled = False

    def get_statistics(self) -> dict:
        """Get library statistics."""
        stats = {
            "total_patterns": 0,
            "patterns_by_language": {},
            "patterns_by_category": {},
            "patterns_by_severity": {},
            "enabled_patterns": 0
        }

        for language, patterns in self._patterns.items():
            stats["patterns_by_language"][language] = len(patterns)
            stats["total_patterns"] += len(patterns)

            for pattern in patterns:
                # Category stats
                cat = pattern.category.value
                stats["patterns_by_category"][cat] = stats["patterns_by_category"].get(cat, 0) + 1

                # Severity stats
                sev = pattern.severity.value
                stats["patterns_by_severity"][sev] = stats["patterns_by_severity"].get(sev, 0) + 1

                # Enabled stats
                if pattern.enabled:
                    stats["enabled_patterns"] += 1

        return stats

    def _serialize_pattern(self, pattern: DetectionPattern) -> dict:
        """Serialize pattern to dictionary."""
        return {
            "id": pattern.id,
            "name": pattern.name,
            "category": pattern.category.value,
            "severity": pattern.severity.value,
            "pattern": pattern.pattern,
            "language": pattern.language,
            "pattern_type": pattern.pattern_type,
            "description": pattern.description,
            "tags": list(pattern.tags),
            "references": pattern.references,
            "enabled": pattern.enabled,
            "confidence_threshold": pattern.confidence_threshold,
            "owasp_category": pattern.owasp_category.value if pattern.owasp_category else None,
            "cwe_id": pattern.cwe_id
        }

    def _deserialize_pattern(self, data: dict) -> DetectionPattern:
        """Deserialize pattern from dictionary."""
        try:
            category = BugCategory(data.get("category"))
            severity = BugSeverity(data.get("severity"))
            owasp_category = VulnerabilityType(data.get("owasp_category")) if data.get("owasp_category") else None

            return DetectionPattern(
                id=data["id"],
                name=data["name"],
                category=category,
                severity=severity,
                pattern=data["pattern"],
                language=data["language"],
                pattern_type=data.get("pattern_type", "regex"),
                description=data["description"],
                tags=set(data.get("tags", [])),
                references=data.get("references", []),
                enabled=data.get("enabled", True),
                confidence_threshold=data.get("confidence_threshold", 0.5),
                owasp_category=owasp_category,
                cwe_id=data.get("cwe_id")
            )
        except Exception as e:
            print(f"Error deserializing pattern: {e}")
            return None

    def clear_patterns(self, language: str = None):
        """Clear patterns for a language or all patterns."""
        if language:
            self._patterns[language.lower()] = []
        else:
            for lang in self._patterns:
                self._patterns[lang] = []
