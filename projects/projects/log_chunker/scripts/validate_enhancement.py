#!/usr/bin/env python3
"""
Enhancement Validation Script for Log Chunker

This script validates that enhancement implementations follow the established patterns
and maintain consistency across different LLM developers.

Usage:
    python scripts/validate_enhancement.py <file_path>
    python scripts/validate_enhancement.py src/log_chunker/plugins/enhanced/semantic_clustering.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any


class EnhancementValidator:
    """Validates enhancement implementations against established patterns"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []

    def validate_plugin_file(self, file_path: Path) -> dict[str, Any]:
        """Validate a plugin file follows required patterns"""

        if not file_path.exists():
            self.errors.append(f"File not found: {file_path}")
            return self._get_results()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except Exception as e:
            self.errors.append(f"Failed to parse Python file: {e}")
            return self._get_results()

        # Run all validation checks
        self._validate_plugin_structure(tree, content)
        self._validate_optional_dependencies(tree, content)
        self._validate_error_handling(tree, content)
        self._validate_documentation(content)
        self._validate_rich_integration(content)

        return self._get_results()

    def _validate_plugin_structure(self, tree: ast.AST, content: str):
        """Validate plugin follows required class structure"""

        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        plugin_classes = [cls for cls in classes if cls.name.endswith("Plugin")]

        if not plugin_classes:
            self.errors.append(
                "No plugin class found (class name must end with 'Plugin')"
            )
            return

        plugin_class = plugin_classes[0]

        # Check inheritance
        if not plugin_class.bases:
            self.errors.append("Plugin class must inherit from base plugin class")
        else:
            base_names = [
                base.attr if isinstance(base, ast.Attribute) else base.id
                for base in plugin_class.bases
                if hasattr(base, "attr") or hasattr(base, "id")
            ]
            if not any("Plugin" in name for name in base_names):
                self.errors.append(
                    "Plugin class must inherit from ChunkingPlugin or AnalysisPlugin"
                )
            else:
                self.successes.append(
                    "✅ Plugin class inherits from correct base class"
                )

        # Check required methods
        methods = [
            node.name for node in plugin_class.body if isinstance(node, ast.FunctionDef)
        ]
        required_methods = ["__init__", "find_boundaries", "score_chunk"]

        for method in required_methods:
            if method in methods:
                self.successes.append(f"✅ Required method '{method}' found")
            else:
                self.errors.append(f"Missing required method: {method}")

        # Check for fallback implementation
        fallback_methods = [m for m in methods if "fallback" in m.lower()]
        if fallback_methods:
            self.successes.append("✅ Fallback implementation methods found")
        else:
            self.warnings.append("⚠️  No fallback implementation methods found")

    def _validate_optional_dependencies(self, tree: ast.AST, content: str):
        """Validate optional dependency handling pattern"""

        # Check for try/except import pattern
        has_try_except_import = False
        has_dependency_flag = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check if this is an import try/except
                import_nodes = [
                    n for n in node.body if isinstance(n, (ast.Import, ast.ImportFrom))
                ]
                if import_nodes:
                    has_try_except_import = True
                    self.successes.append("✅ Try/except import pattern found")
                    break

        # Check for HAS_*_DEPS flag
        if re.search(r"HAS_\w+_DEPS\s*=\s*(True|False)", content):
            has_dependency_flag = True
            self.successes.append("✅ Dependency availability flag found")

        if not has_try_except_import:
            self.errors.append("Missing try/except pattern for optional imports")

        if not has_dependency_flag:
            self.errors.append("Missing HAS_*_DEPS dependency availability flag")

        # Check for use_fallback attribute
        if "self.use_fallback" in content:
            self.successes.append("✅ Fallback mechanism implemented")
        else:
            self.errors.append("Missing fallback mechanism (self.use_fallback)")

    def _validate_error_handling(self, tree: ast.AST, content: str):
        """Validate error handling follows established patterns"""

        # Check for proper exception imports
        exception_imports = ["PluginError", "LogChunkerError"]

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "exceptions" in node.module:
                    imported_names = [alias.name for alias in node.names]
                    for exc in exception_imports:
                        if exc in imported_names:
                            self.successes.append(f"✅ {exc} import found")

        # Check for try/except blocks in methods
        try_except_count = len(
            [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
        )
        if try_except_count > 1:  # More than just the import try/except
            self.successes.append("✅ Error handling try/except blocks found")
        else:
            self.warnings.append("⚠️  Limited error handling found")

        # Check for logging
        if "logger." in content:
            self.successes.append("✅ Logging implementation found")
        else:
            self.warnings.append("⚠️  No logging implementation found")

    def _validate_documentation(self, content: str):
        """Validate documentation follows standards"""

        # Check for module docstring
        if '"""' in content[:500]:  # Check first 500 chars for module docstring
            self.successes.append("✅ Module docstring found")
        else:
            self.warnings.append("⚠️  Module docstring missing")

        # Check for class docstring
        if "class " in content and '"""' in content:
            self.successes.append("✅ Class docstring found")

        # Check for method docstrings
        method_docstring_count = content.count("def ") - content.count('"""')
        if method_docstring_count <= 0:
            self.successes.append("✅ Method docstrings appear to be present")
        else:
            self.warnings.append("⚠️  Some methods may be missing docstrings")

        # Check for type hints
        if "->" in content and ":" in content:
            self.successes.append("✅ Type hints found")
        else:
            self.warnings.append("⚠️  Limited type hints found")

    def _validate_rich_integration(self, content: str):
        """Validate Rich console integration patterns"""

        # Check for console usage
        if "self.console" in content:
            self.successes.append("✅ Console integration found")
        else:
            self.warnings.append("⚠️  No console integration found")

        # Check for Rich markup patterns
        rich_patterns = ["[green]", "[red]", "[yellow]", "[cyan]", "[bold]"]
        found_patterns = [pattern for pattern in rich_patterns if pattern in content]

        if found_patterns:
            self.successes.append(
                f"✅ Rich markup patterns found: {', '.join(found_patterns)}"
            )
        else:
            self.warnings.append("⚠️  No Rich markup patterns found")

    def _get_results(self) -> dict[str, Any]:
        """Get validation results"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "successes": self.successes,
            "passed": len(self.errors) == 0,
        }


def validate_configuration_file(file_path: Path) -> dict[str, Any]:
    """Validate configuration file changes"""

    validator = EnhancementValidator()

    if not file_path.exists():
        validator.errors.append(f"Configuration file not found: {file_path}")
        return validator._get_results()

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        validator.errors.append(f"Failed to read configuration file: {e}")
        return validator._get_results()

    # Check for Pydantic imports
    if "from pydantic import" in content:
        validator.successes.append("✅ Pydantic imports found")
    else:
        validator.errors.append("Missing Pydantic imports")

    # Check for Field usage
    if "Field(" in content:
        validator.successes.append("✅ Pydantic Field usage found")
    else:
        validator.warnings.append("⚠️  Limited Pydantic Field usage")

    # Check for new config classes
    if "Config(BaseModel)" in content.replace(" ", ""):
        validator.successes.append("✅ New configuration class found")

    return validator._get_results()


def main():
    """Main validation function"""

    if len(sys.argv) < 2:
        print("Usage: python validate_enhancement.py <file_path>")
        print("\nExamples:")
        print(
            "  python validate_enhancement.py src/log_chunker/plugins/enhanced/semantic_clustering.py"
        )
        print("  python validate_enhancement.py src/log_chunker/config.py")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    print(f"🔍 Validating enhancement: {file_path}")
    print("=" * 50)

    # Determine validation type based on file
    if "plugin" in str(file_path) and file_path.suffix == ".py":
        validator = EnhancementValidator()
        results = validator.validate_plugin_file(file_path)
    elif file_path.name == "config.py":
        results = validate_configuration_file(file_path)
    else:
        print(f"❌ Unsupported file type for validation: {file_path}")
        sys.exit(1)

    # Display results
    print("\n📊 VALIDATION RESULTS:")
    print("-" * 30)

    if results["successes"]:
        print("\n✅ SUCCESSES:")
        for success in results["successes"]:
            print(f"  {success}")

    if results["warnings"]:
        print("\n⚠️  WARNINGS:")
        for warning in results["warnings"]:
            print(f"  {warning}")

    if results["errors"]:
        print("\n❌ ERRORS:")
        for error in results["errors"]:
            print(f"  {error}")

    print("\n" + "=" * 50)

    if results["passed"]:
        print("🎉 VALIDATION PASSED! Enhancement follows established patterns.")
        sys.exit(0)
    else:
        print("💥 VALIDATION FAILED! Please fix the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
