#!/usr/bin/env python3
"""
API Breakage Detector for Library Code Protection

Detects API-breaking changes by comparing pre/post characterizations.

Breakage Types Detected:
- Function removed
- Signature changed (incompatible)
- Parameter removed/changed
- Return type changed
- Import removed
- Class/method removed

Output: Structured report with breaking changes, affected callers, and remediation suggestions.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Add __lib to path for imports
# NOTE: Scoped path mutation - restored after import (AC-003 compliance)
_lib_path_added = False
_original_path = sys.path.copy()
lib_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(lib_dir))
_lib_path_added = True

try:
    from characterization_engine import (
        CharacterizationData,
        FunctionSignature,
    )
finally:
    # Restore original path after import (scope control)
    if _lib_path_added:
        sys.path = _original_path


class Severity(Enum):
    """Severity levels for breaking changes."""
    CRITICAL = "critical"  # Will break existing code
    WARNING = "warning"    # Potentially breaking
    INFO = "info"          # Cosmetic change


@dataclass
class BreakingChange:
    """Represents a single breaking change."""
    change_type: str
    severity: Severity
    description: str
    affected_callers: list[str] = field(default_factory=list)
    remediation: str = ""
    before: str = ""
    after: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "change_type": self.change_type,
            "severity": self.severity.value,
            "description": self.description,
            "affected_callers": self.affected_callers,
            "remediation": self.remediation,
            "before": self.before,
            "after": self.after,
        }


@dataclass
class BreakageReport:
    """Complete report of breaking changes."""
    module_path: str
    has_breaking_changes: bool
    changes: list[BreakingChange] = field(default_factory=list)
    total_callers_affected: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "module_path": self.module_path,
            "has_breaking_changes": self.has_breaking_changes,
            "changes": [c.to_dict() for c in self.changes],
            "total_callers_affected": self.total_callers_affected,
        }

    def format_message(self) -> str:
        """Format as human-readable block message."""
        if not self.has_breaking_changes:
            return f"✅ No breaking changes detected in {self.module_path}"

        lines = [
            "❌ LIBRARY CODE VALIDATION FAILED\n",
            f"File: {self.module_path}\n",
            "BREAKING CHANGES DETECTED:\n",
        ]

        for i, change in enumerate(self.changes, 1):
            severity_icon = {
                Severity.CRITICAL: "[CRITICAL]",
                Severity.WARNING: "[WARNING]",
                Severity.INFO: "[INFO]",
            }[change.severity]

            lines.append(f"{i}. {severity_icon} {change.change_type}")
            lines.append(f"   {change.description}")

            if change.before:
                lines.append(f"   Before: {change.before}")
            if change.after:
                lines.append(f"   After: {change.after}")

            if change.affected_callers:
                lines.append(f"\n   Impact: {len(change.affected_callers)} caller(s) will break")
                for caller in change.affected_callers[:3]:
                    lines.append(f"   - {caller}")
                if len(change.affected_callers) > 3:
                    lines.append(f"   - ... and {len(change.affected_callers) - 3} more")

            if change.remediation:
                lines.append(f"\n   Fix: {change.remediation}")

            lines.append("")

        lines.append("RECOMMENDATION:")
        lines.append("Revert changes and follow safe refactoring pattern:")
        lines.append("1. Add new function with new signature")
        lines.append("2. Update callers incrementally")
        lines.append("3. Deprecate old function")
        lines.append("4. Remove after all callers migrated")

        return "\n".join(lines)


class APIBreakageDetector:
    """
    Detects API-breaking changes by comparing characterizations.

    Usage:
        detector = APIBreakageDetector()
        report = detector.compare_characterizations(before_data, after_data)
    """

    def compare_characterizations(
        self,
        before: CharacterizationData,
        after: CharacterizationData,
    ) -> BreakageReport:
        """
        Compare pre and post characterizations to detect breaking changes.

        Args:
            before: Pre-edit characterization
            after: Post-edit characterization

        Returns:
            BreakageReport with all detected changes
        """
        changes = []

        # Check for function removals
        changes.extend(self._detect_removed_functions(before, after))

        # Check for signature changes
        changes.extend(self._detect_signature_changes(before, after))

        # Check for class/method removals
        changes.extend(self._detect_removed_classes(before, after))

        # Check for import removals
        changes.extend(self._detect_removed_imports(before, after))

        # Calculate total affected callers
        total_affected = sum(len(c.affected_callers) for c in changes)

        return BreakageReport(
            module_path=after.module_path,
            has_breaking_changes=any(c.severity == Severity.CRITICAL for c in changes),
            changes=changes,
            total_callers_affected=total_affected,
        )

    def _detect_removed_functions(
        self,
        before: CharacterizationData,
        after: CharacterizationData,
    ) -> list[BreakingChange]:
        """Detect functions that were removed."""
        changes = []
        before_funcs = set(before.function_signatures.keys())
        after_funcs = set(after.function_signatures.keys())

        removed = before_funcs - after_funcs
        for func_name in removed:
            sig = before.function_signatures[func_name]
            callers = before.caller_map.get(func_name, [])

            changes.append(BreakingChange(
                change_type="Function Removed",
                severity=Severity.CRITICAL,
                description=f"Function '{func_name}' was removed",
                affected_callers=callers,
                remediation=f"Restore {func_name} or ensure all callers are updated",
                before=f"def {func_name}(...)",
                after="(removed)",
            ))

        return changes

    def _detect_signature_changes(
        self,
        before: CharacterizationData,
        after: CharacterizationData,
    ) -> list[BreakingChange]:
        """Detect incompatible signature changes."""
        changes = []
        common_funcs = set(before.function_signatures.keys()) & set(after.function_signatures.keys())

        for func_name in common_funcs:
            before_sig = before.function_signatures[func_name]
            after_sig = after.function_signatures[func_name]

            if not before_sig.is_compatible_with(after_sig):
                callers = before.caller_map.get(func_name, [])
                changes.append(BreakingChange(
                    change_type="Function Signature Changed",
                    severity=Severity.CRITICAL,
                    description=f"Function '{func_name}' signature changed incompatibly",
                    affected_callers=callers,
                    remediation=self._generate_signature_remediation(before_sig, after_sig),
                    before=self._format_signature(before_sig),
                    after=self._format_signature(after_sig),
                ))

        return changes

    def _detect_removed_classes(
        self,
        before: CharacterizationData,
        after: CharacterizationData,
    ) -> list[BreakingChange]:
        """Detect classes or methods that were removed."""
        changes = []
        before_classes = set(before.class_definitions.keys())
        after_classes = set(after.class_definitions.keys())

        # Removed classes
        removed_classes = before_classes - after_classes
        for cls_name in removed_classes:
            cls_def = before.class_definitions[cls_name]
            changes.append(BreakingChange(
                change_type="Class Removed",
                severity=Severity.CRITICAL,
                description=f"Class '{cls_name}' was removed",
                affected_callers=[f"Users of {cls_name}"],
                remediation=f"Restore {cls_name} or migrate all usage",
                before=f"class {cls_name}: ...",
                after="(removed)",
            ))

        # Removed methods
        common_classes = before_classes & after_classes
        for cls_name in common_classes:
            before_cls = before.class_definitions[cls_name]
            after_cls = after.class_definitions[cls_name]

            before_methods = set(before_cls.methods)
            after_methods = set(after_cls.methods)

            removed_methods = before_methods - after_methods
            for method_name in removed_methods:
                changes.append(BreakingChange(
                    change_type="Method Removed",
                    severity=Severity.CRITICAL,
                    description=f"Method '{cls_name}.{method_name}' was removed",
                    affected_callers=[f"Callers of {cls_name}.{method_name}"],
                    remediation=f"Restore {cls_name}.{method_name} or deprecate properly",
                    before=f"def {method_name}(self, ...)",
                    after="(removed)",
                ))

        return changes

    def _detect_removed_imports(
        self,
        before: CharacterizationData,
        after: CharacterizationData,
    ) -> list[BreakingChange]:
        """Detect imports that were removed (may indicate removed dependencies)."""
        changes = []

        # Flatten import dependencies
        before_imports = set()
        for imports in before.import_dependencies.values():
            before_imports.update(imp.module for imp in imports)

        after_imports = set()
        for imports in after.import_dependencies.values():
            after_imports.update(imp.module for imp in imports)

        removed_imports = before_imports - after_imports
        for imp_name in removed_imports:
            # Only flag external imports
            is_external = any(imp.module == imp_name or imp.module.startswith(imp_name + ".")
                             for imports in before.import_dependencies.values()
                             for imp in imports if imp.is_external)

            if is_external:
                changes.append(BreakingChange(
                    change_type="Import Removed",
                    severity=Severity.WARNING,
                    description=f"Import '{imp_name}' was removed (may indicate removed feature)",
                    affected_callers=[],
                    remediation=f"Verify {imp_name} is no longer needed",
                    before=f"import {imp_name}",
                    after="(removed)",
                ))

        return changes

    def _format_signature(self, sig: FunctionSignature) -> str:
        """Format function signature for display."""
        params = ", ".join(
            f"{p['name']}: {p.get('type', 'Any')}" + (f" = {p['default']}" if p.get('default') else "")
            for p in sig.parameters
        )
        return_type = f" -> {sig.return_type}" if sig.return_type else ""
        async_prefix = "async " if sig.is_async else ""
        return f"{async_prefix}def {sig.name}({params}){return_type}"

    def _generate_signature_remediation(
        self,
        before: FunctionSignature,
        after: FunctionSignature,
    ) -> str:
        """Generate remediation suggestion for signature change."""
        before_params = [p["name"] for p in before.parameters]
        after_params = [p["name"] for p in after.parameters]

        if len(after_params) < len(before_params):
            return f"Keep original signature, create new function: {after.name}_v2(...)"

        if len(after_params) > len(before_params):
            new_params = set(after_params) - set(before_params)
            return f"Make new parameters optional with defaults: {', '.join(new_params)}"

        return "Keep backward compatible or use @deprecated decorator"


def compare_characterizations(
    before: CharacterizationData,
    after: CharacterizationData,
) -> BreakageReport:
    """
    Convenience function to compare characterizations.

    Args:
        before: Pre-edit characterization
        after: Post-edit characterization

    Returns:
        BreakageReport with detected changes
    """
    detector = APIBreakageDetector()
    return detector.compare_characterizations(before, after)


__all__ = [
    "APIBreakageDetector",
    "BreakingChange",
    "BreakageReport",
    "Severity",
    "compare_characterizations",
]
