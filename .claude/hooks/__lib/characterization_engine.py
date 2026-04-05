#!/usr/bin/env python3
"""
Characterization Engine for Library Code Protection

Captures complete behavior characterization before edits to enable API breakage detection.

This module provides:
- AST-based signature extraction (functions, classes, methods)
- Import dependency mapping
- Call graph building (reuses static_call_graph.py)
- SHA256 checksum for change detection
- Behavior snapshots (execute with sample inputs)

Data Structure:
    CharacterizationData:
        - module_path: Path to the module
        - captured_at: Timestamp of capture
        - checksum: SHA256 of source code
        - function_signatures: Dict of function signatures
        - class_definitions: Dict of class definitions
        - import_dependencies: Import mapping
        - external_dependencies: External package list
        - call_graph: Function call relationships
        - caller_map: Reverse call graph
        - complexity_scores: Cyclomatic complexity

TDD-RED Phase: Tests will verify signature extraction.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add CSF paths for call graph builder
# NOTE: Scoped path mutation - restored after import via context manager pattern
# The import happens at module load time, but the path is only needed briefly
_csf_path_added = False
_original_path = sys.path.copy()
current_dir = Path(__file__).resolve().parent
csf_src = current_dir.parent.parent.parent / "__csf" / "src"
if csf_src.exists():
    sys.path.insert(0, str(csf_src))
    _csf_path_added = True

try:
    from modules.discover.static_call_graph import CallGraph, StaticCallGraphBuilder
    CALL_GRAPH_AVAILABLE = True
except ImportError:
    CALL_GRAPH_AVAILABLE = False
    import warnings
    warnings.warn(
        "Call graph feature unavailable: static_call_graph module not found. "
        "API breakage detection will have reduced accuracy. "
        "Install __csf/src/modules/discover/ to enable this feature.",
        ImportWarning,
        stacklevel=2
    )
finally:
    # Restore original path after import (scope control for sys.path mutation)
    if _csf_path_added:
        sys.path = _original_path


# Maximum safe length for unparsed AST strings (prevents DoS from malicious code)
MAX_UNPARSE_LENGTH = 10000

# Default module prefixes considered "local" for external import detection
# Task: #184 - Make local_prefixes configurable instead of hardcoded
DEFAULT_LOCAL_PREFIXES = ("csf_", "__csf", "claude_hooks")


def safe_unparse(node: ast.AST) -> str:
    """
    Safely convert AST node to string with length limiting.

    This prevents potential DoS attacks via extremely long expressions
    and ensures output is safe for storage/display only.

    Args:
        node: AST node to unparsed

    Returns:
        String representation of the AST node, truncated if too long

    Task: #174 - Safe AST unparse with length limits
    """
    if not hasattr(ast, "unparse"):
        return str(node)

    try:
        result = ast.unparse(node)
        # Truncate to prevent DoS from malicious code with huge expressions
        if len(result) > MAX_UNPARSE_LENGTH:
            result = result[:MAX_UNPARSE_LENGTH] + "... [truncated]"
        return result
    except Exception:
        # Fallback to string representation if unparse fails
        return str(node)[:MAX_UNPARSE_LENGTH]


@dataclass
class FunctionSignature:
    """Represents a function signature for API comparison."""
    name: str
    parameters: list[dict[str, Any]]  # name, type, default, kind
    return_type: str | None
    is_async: bool
    decorators: list[str]
    lineno: int
    docstring: str | None

    def to_comparable_key(self) -> str:
        """Generate comparable key for signature change detection."""
        params_key = ",".join(
            f"{p['name']}:{p.get('type', 'Any')}" for p in self.parameters
        )
        return f"{self.name}:{params_key}:{self.return_type or 'None'}:{self.is_async}"

    def is_compatible_with(self, other: FunctionSignature) -> bool:
        """Check if another signature is backward compatible."""
        # Name must match
        if self.name != other.name:
            return False

        # Async/sync mismatch is breaking (task #168)
        if self.is_async != other.is_async:
            return False

        # Positional parameter count must be compatible
        my_positional = [p for p in self.parameters if p.get("kind") in ("positional", "pos_or_kw")]
        other_positional = [p for p in other.parameters if p.get("kind") in ("positional", "pos_or_kw")]

        # Check required parameters (no 'default' key indicates required)
        # Note: Use 'default' not in p to detect required params, not 'not p.get("default")'
        # This is because default=None is a valid default value (task #168 bug fix)
        my_required = [p for p in my_positional if "default" not in p]
        other_required = [p for p in other_positional if "default" not in p]

        # Adding new required parameters is breaking
        # Removing required parameters is also breaking (handled by position check below)
        if len(other_required) > len(my_required):
            return False

        # All of my positional parameters must exist in the same order in other
        for i, mine in enumerate(my_positional):
            if i >= len(other_positional):
                return False  # Parameter removed

            theirs = other_positional[i]
            # Parameter type changes are potentially breaking
            if mine.get("type") and theirs.get("type") and mine["type"] != theirs["type"]:
                return False

        return True

    def get_compatibility_issues(
        self, other: FunctionSignature
    ) -> list[dict[str, Any]]:
        """
        Get detailed compatibility issues between signatures.

        Returns a list of issues with severity levels:
        - "critical": Breaking changes (would make is_compatible_with return False)
        - "warning": Potentially breaking changes (default value changes, etc.)

        Task #169: Add default value change detection.
        """
        issues = []

        # First check if incompatible (critical issues)
        if not self.is_compatible_with(other):
            issues.append({
                "severity": "critical",
                "type": "incompatible_signature",
                "description": f"Function '{self.name}' has incompatible signature changes",
            })
            return issues  # Critical issues take precedence

        # Check for default value changes (WARNING level)
        # Map params by name for comparison
        my_params_by_name = {p["name"]: p for p in self.parameters}
        other_params_by_name = {p["name"]: p for p in other.parameters}

        for param_name, my_param in my_params_by_name.items():
            if param_name not in other_params_by_name:
                continue  # Parameter removed - already caught by is_compatible_with

            other_param = other_params_by_name[param_name]

            # Compare default values
            my_default = my_param.get("default")
            other_default = other_param.get("default")

            # If one has default and other doesn't, that's a required/optional change
            # This is already handled by is_compatible_with, so skip here
            has_my_default = "default" in my_param
            has_other_default = "default" in other_param

            if has_my_default and has_other_default:
                # Both have defaults - check if values differ
                if my_default != other_default:
                    issues.append({
                        "severity": "warning",
                        "type": "default_value_changed",
                        "parameter": param_name,
                        "before": my_default,
                        "after": other_default,
                        "description": (
                            f"Parameter '{param_name}' default value changed "
                            f"from {repr(my_default)} to {repr(other_default)}"
                        ),
                    })

        return issues


@dataclass
class ClassDefinition:
    """Represents a class definition for API comparison."""
    name: str
    bases: list[str]
    methods: list[str]
    properties: list[str]
    lineno: int
    docstring: str | None

    def has_method(self, method_name: str) -> bool:
        """Check if class has a specific method."""
        return method_name in self.methods


@dataclass
class ImportInfo:
    """Represents an import dependency."""
    module: str
    alias: str | None
    is_external: bool
    lineno: int
    import_type: str  # "import" or "from_import"


@dataclass
class CharacterizationData:
    """Complete characterization of a library module."""
    module_path: str
    captured_at: str
    checksum: str

    # AST-based analysis
    function_signatures: dict[str, FunctionSignature] = field(default_factory=dict)
    class_definitions: dict[str, ClassDefinition] = field(default_factory=dict)

    # Dependency analysis
    import_dependencies: dict[str, list[ImportInfo]] = field(default_factory=dict)
    external_dependencies: list[str] = field(default_factory=list)

    # Call graph
    call_graph: dict[str, list[str]] = field(default_factory=dict)
    caller_map: dict[str, list[str]] = field(default_factory=dict)

    # Complexity metrics
    complexity_scores: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            "module_path": self.module_path,
            "captured_at": self.captured_at,
            "checksum": self.checksum,
            "function_signatures": {
                name: self._serialize_function_sig(sig)
                for name, sig in self.function_signatures.items()
            },
            "class_definitions": {
                name: asdict(cls_def) for name, cls_def in self.class_definitions.items()
            },
            "import_dependencies": {
                file: [asdict(imp) for imp in imports]
                for file, imports in self.import_dependencies.items()
            },
            "external_dependencies": self.external_dependencies,
            "call_graph": self.call_graph,
            "caller_map": self.caller_map,
            "complexity_scores": self.complexity_scores,
        }
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def _serialize_function_sig(sig: FunctionSignature) -> dict:
        """Serialize FunctionSignature to dict."""
        return asdict(sig)

    @staticmethod
    def _validate_schema(data: dict) -> None:
        """
        Validate JSON schema before deserialization.

        Raises:
            ValueError: If required fields are missing or have invalid types.
            TypeError: If field types don't match expected types.

        Task: #164, #180 - Schema validation for security
        """
        # Required fields
        required_fields = ["module_path", "captured_at", "checksum"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Type validation for required fields
        if not isinstance(data["module_path"], str):
            raise TypeError(f"module_path must be str, got {type(data['module_path']).__name__}")
        if not isinstance(data["captured_at"], str):
            raise TypeError(f"captured_at must be str, got {type(data['captured_at']).__name__}")
        if not isinstance(data["checksum"], str):
            raise TypeError(f"checksum must be str, got {type(data['checksum']).__name__}")

        # Validate checksum format (SHA256 = 64 hex chars)
        if len(data["checksum"]) != 64:
            raise ValueError(f"checksum must be 64 characters (SHA256), got {len(data['checksum'])}")

        # Validate optional field types if present
        optional_fields = {
            "external_dependencies": list,
            "call_graph": dict,
            "caller_map": dict,
            "complexity_scores": dict,
        }
        for field, expected_type in optional_fields.items():
            if field in data and not isinstance(data[field], expected_type):
                raise TypeError(f"{field} must be {expected_type.__name__}, got {type(data[field]).__name__}")

    @staticmethod
    def _safe_create_nested_object(
        cls: type,
        data: dict,
        context: str
    ) -> Any:
        """
        Safely create nested objects with error handling.

        Args:
            cls: The class to instantiate
            data: Raw dict from JSON
            context: Description for error messages

        Returns:
            Instance of cls

        Raises:
            ValueError: If data structure is invalid
            TypeError: If types don't match expected schema
        """
        try:
            return cls(**data)
        except TypeError as e:
            raise TypeError(f"Invalid {context} structure: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to create {context}: {e}") from e

    @staticmethod
    def from_json(json_str: str) -> CharacterizationData:
        """
        Deserialize from JSON with schema validation.

        Args:
            json_str: JSON string to deserialize

        Returns:
            CharacterizationData instance

        Raises:
            json.JSONDecodeError: If JSON is malformed
            ValueError: If required fields missing or invalid values
            TypeError: If field types don't match expected schema

        Task: #164, #180 - Safe deserialization with validation
        """
        # Parse JSON (may raise json.JSONDecodeError)
        data = json.loads(json_str)

        # Validate schema before creating objects
        CharacterizationData._validate_schema(data)

        # Safely create nested objects with error handling
        function_sigs = {}
        for name, sig_data in data.get("function_signatures", {}).items():
            function_sigs[name] = CharacterizationData._safe_create_nested_object(
                FunctionSignature, sig_data, f"function_signature[{name}]"
            )

        class_defs = {}
        for name, cls_data in data.get("class_definitions", {}).items():
            class_defs[name] = CharacterizationData._safe_create_nested_object(
                ClassDefinition, cls_data, f"class_definition[{name}]"
            )

        import_deps = {}
        for file, imports in data.get("import_dependencies", {}).items():
            import_deps[file] = [
                CharacterizationData._safe_create_nested_object(ImportInfo, imp, f"import_info[{file}]")
                for imp in imports
            ]

        return CharacterizationData(
            module_path=data["module_path"],
            captured_at=data["captured_at"],
            checksum=data["checksum"],
            function_signatures=function_sigs,
            class_definitions=class_defs,
            import_dependencies=import_deps,
            external_dependencies=data.get("external_dependencies", []),
            call_graph=data.get("call_graph", {}),
            caller_map=data.get("caller_map", {}),
            complexity_scores=data.get("complexity_scores", {}),
        )


class SinglePassASTVisitor(ast.NodeVisitor):
    """
    Single-pass AST visitor that collects all characterization data.

    Replaces multiple ast.walk() calls with a single traversal.
    Collects: function signatures, class definitions, imports, complexity.

    Task: #229 - Consolidate AST walks into single pass (PERF-008 CRITICAL)
    """

    def __init__(self, module_path: str, local_prefixes: tuple[str, ...] = DEFAULT_LOCAL_PREFIXES):
        """
        Initialize the visitor with result containers.

        Args:
            module_path: Path to the module being analyzed
            local_prefixes: Tuple of module name prefixes considered "local"
                           (Task: #184 - configurable instead of hardcoded)
        """
        self.module_path = module_path
        self.local_prefixes = local_prefixes
        self.function_signatures: dict[str, FunctionSignature] = {}
        self.class_definitions: dict[str, ClassDefinition] = {}
        self.import_dependencies: dict[str, list[ImportInfo]] = {module_path: []}
        self.external_dependencies: set[str] = set()
        self.complexity_scores: dict[str, int] = {}

        # Parent tracking for proper method qualification
        self._parent_stack: list[ast.AST] = []
        self._current_class: ast.ClassDef | None = None

    def visit(self, node: ast.AST) -> None:
        """Visit a node with parent tracking."""
        self._parent_stack.append(node)
        try:
            super().visit(node)
        finally:
            self._parent_stack.pop()

    def _get_parent(self, node_type: type) -> ast.AST | None:
        """Get the first parent of the given type."""
        for parent in reversed(self._parent_stack):
            if isinstance(parent, node_type):
                return parent
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class definition."""
        # Save and update current class context
        parent_class = self._current_class
        self._current_class = node

        # Parse class definition
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(safe_unparse(base))

        methods = []
        properties = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
                # Check for @property decorator
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "property":
                        properties.append(item.name)

        self.class_definitions[node.name] = ClassDefinition(
            name=node.name,
            bases=bases,
            methods=methods,
            properties=properties,
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
        )

        # Visit class body (for methods)
        self.generic_visit(node)

        # Restore previous class context
        self._current_class = parent_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function signature and complexity."""
        self._process_function(node)
        # Don't recurse into function body for complexity (handled separately)
        # But we need to visit nested functions
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(child)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Extract async function signature and complexity."""
        self._process_function(node)
        # Don't recurse into function body for complexity (handled separately)
        # But we need to visit nested functions
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(child)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Process a function node for signature and complexity."""
        # Determine qualified name
        if self._current_class is not None:
            qualified_name = f"{self._current_class.name}.{node.name}"
        else:
            qualified_name = node.name

        # Parse parameters
        parameters = []
        for arg in node.args.posonlyargs:
            param = {
                "name": arg.arg,
                "type": self._get_type_annotation(arg.annotation),
                "kind": "positional_only",
            }
            parameters.append(param)
        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "type": self._get_type_annotation(arg.annotation),
                "kind": "pos_or_kw",
            }
            parameters.append(param)
        for arg in node.args.kwonlyargs:
            param = {
                "name": arg.arg,
                "type": self._get_type_annotation(arg.annotation),
                "kind": "keyword_only",
            }
            parameters.append(param)

        # Handle defaults - only add 'default' key for parameters with defaults
        # This allows is_compatible_with to detect required params using "default" not in p
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            param_idx = defaults_offset + i
            if param_idx < len(parameters):
                parameters[param_idx]["default"] = safe_unparse(default)

        # Add defaults for keyword-only args (they have their own defaults list)
        for i, default in enumerate(node.args.kw_defaults):
            if default is not None:
                # Find the keyword-only arg (after positional args)
                kw_param_idx = len(node.args.posonlyargs) + len(node.args.args) + i
                if kw_param_idx < len(parameters):
                    parameters[kw_param_idx]["default"] = safe_unparse(default)

        return_type = self._get_type_annotation(node.returns)
        decorators = [d.id if isinstance(d, ast.Name) else safe_unparse(d) for d in node.decorator_list]

        sig = FunctionSignature(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
        )
        self.function_signatures[qualified_name] = sig

        # Calculate complexity for this function
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        self.complexity_scores[qualified_name] = complexity

    def _get_type_annotation(self, annotation: ast.AST | None) -> str | None:
        """Get type annotation as string."""
        if annotation is None:
            return None
        return safe_unparse(annotation)

    def visit_Import(self, node: ast.Import) -> None:
        """Extract import dependencies."""
        for alias in node.names:
            is_external = self._is_external_import(alias.name)
            if is_external:
                self.external_dependencies.add(alias.name.split(".")[0])

            self.import_dependencies[self.module_path].append(ImportInfo(
                module=alias.name,
                alias=alias.asname,
                is_external=is_external,
                lineno=node.lineno,
                import_type="import",
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract from-import dependencies."""
        module = node.module or ""
        is_external = self._is_external_import(module)
        if is_external and module:
            self.external_dependencies.add(module.split(".")[0])

        for alias in node.names:
            self.import_dependencies[self.module_path].append(ImportInfo(
                module=f"{module}.{alias.name}" if module else alias.name,
                alias=alias.asname,
                is_external=is_external,
                lineno=node.lineno,
                import_type="from_import",
            ))

    def _is_external_import(self, module_name: str) -> bool:
        """Check if import is from external package."""
        if not module_name:
            return False
        # Local modules start with .
        if module_name.startswith("."):
            return False
        # Check against configured local prefixes (Task: #184)
        return not module_name.startswith(self.local_prefixes)


class CharacterizationEngine:
    """
    Captures complete behavior characterization for library code.

    Usage:
        engine = CharacterizationEngine()
        data = engine.capture_characterization("path/to/module.py")

        # With custom local prefixes
        engine = CharacterizationEngine(local_prefixes=("myapp_", "internal"))
    """

    def __init__(self, local_prefixes: tuple[str, ...] = DEFAULT_LOCAL_PREFIXES):
        """
        Initialize the characterization engine.

        Args:
            local_prefixes: Module name prefixes considered "local" for external
                           import detection. (Task: #184 - configurable)
        """
        self.local_prefixes = local_prefixes
        self.call_graph_builder = StaticCallGraphBuilder(language="python") if CALL_GRAPH_AVAILABLE else None

    def capture_characterization(self, module_path: str) -> CharacterizationData:
        """
        Capture complete characterization of a module.

        Args:
            module_path: Path to the Python module

        Returns:
            CharacterizationData with complete analysis

        Task: #229 - Single-pass AST traversal for performance
        """
        # Capture original path string BEFORE any Path operations
        # This is needed to check for '..' before resolution (task #165)
        original_path_str = str(module_path)

        # Check for '..' in original path BEFORE resolution
        if '..' in original_path_str or '..' in module_path:
            raise ValueError(f"Path traversal not allowed: {module_path}")

        module_path = Path(module_path).resolve()

        # Path traversal protection: only allow hooks directory and project root
        original_path = Path(module_path)

        # Define strictly allowed base directories
        allowed_bases = [
            Path(__file__).parent.resolve(),  # hooks directory
            Path(__file__).resolve().parent.parent.parent.parent.resolve(),  # project root (P:\) - 4 levels up from __lib
        ]

        # Verify path is within allowed directories (no temp dirs allowed)
        is_allowed = any(
            module_path == base or module_path.is_relative_to(base)
            for base in allowed_bases
        )

        if not is_allowed:
            raise ValueError(f"Path outside allowed directories: {module_path}")

        if not module_path.exists():
            raise FileNotFoundError(f"Module not found: {module_path}")

        source_code = module_path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(source_code.encode()).hexdigest()

        # Parse AST
        try:
            tree = ast.parse(source_code, filename=str(module_path))
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {module_path}: {e}")

        # Single-pass extraction using NodeVisitor
        visitor = SinglePassASTVisitor(str(module_path), local_prefixes=self.local_prefixes)
        visitor.visit(tree)

        # Build call graph (still uses separate library)
        call_graph, caller_map = self._build_call_graph(source_code, str(module_path))

        return CharacterizationData(
            module_path=str(module_path),
            captured_at=datetime.now().isoformat(),
            checksum=checksum,
            function_signatures=visitor.function_signatures,
            class_definitions=visitor.class_definitions,
            import_dependencies=visitor.import_dependencies,
            external_dependencies=sorted(visitor.external_dependencies),  # Convert set to sorted list
            call_graph=call_graph,
            caller_map=caller_map,
            complexity_scores=visitor.complexity_scores,
        )

    def _build_call_graph(
        self, source_code: str, module_path: str
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """Build call graph and reverse caller map.

        Note: This still uses the separate StaticCallGraphBuilder library.
        The single-pass optimization applies to AST walking only.
        """
        if not self.call_graph_builder:
            return {}, {}

        graph = self.call_graph_builder.build(source_code, filename=module_path)

        call_graph = {}
        caller_map = {}

        for func_name in graph.functions:
            callees = graph.get_callees(func_name)
            callers = graph.get_callers(func_name)

            if callees:
                call_graph[func_name] = callees
            if callers:
                caller_map[func_name] = callers

        return call_graph, caller_map


def capture_characterization(module_path: str) -> CharacterizationData:
    """
    Convenience function to capture module characterization.

    Args:
        module_path: Path to the Python module

    Returns:
        CharacterizationData with complete analysis
    """
    engine = CharacterizationEngine()
    return engine.capture_characterization(module_path)


__all__ = [
    "CharacterizationData",
    "CharacterizationEngine",
    "FunctionSignature",
    "ClassDefinition",
    "ImportInfo",
    "capture_characterization",
]
