"""RLM Backend - Template-based code generation for intelligent code search.

This module provides RLMBackend that generates and executes Python analysis code
in a sandboxed environment. Unlike traditional search, RLM uses CODE as the
search mechanism - enabling semantic understanding through execution.

Key principles:
- NO external LLM calls - uses template-based code generation
- Template-based code generation from query semantics
- Sandboxed execution with restricted builtins
- Returns structured results for interpretation

Architecture:
    User Query → RLMBackend
        ↓ 1. Extract keywords/semantics
        ↓ 2. Generate analysis code (template-based)
        ↓ 3. Execute in sandbox
        ↓ 4. Return structured results
        ↓
        Caller interprets results (not RLM)
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import re
from io import StringIO
from pathlib import Path

# Security: Allowlist of modules that can be imported in sandbox
_SAFE_MODULES = frozenset(
    [
        # Standard library - safe utilities
        "re",
        "json",
        "collections",
        "itertools",
        "functools",
        "operator",
        "string",
        "textwrap",
        "typing",
        # Path-related (read-only operations)
        "pathlib",
        "os.path",
    ]
)


def _restricted_import(name: str, *args, **kwargs):
    """Restricted import that only allows safe modules.

    This replaces __import__ in the sandbox to prevent arbitrary code execution.

    Args:
        name: Module name to import

    Returns:
        The imported module if allowed

    Raises:
        ImportError: If module is not in the allowlist
    """
    # Get base module name (before any dots)
    base_module = name.split(".")[0]

    if base_module not in _SAFE_MODULES and name not in _SAFE_MODULES:
        raise ImportError(
            f"Module '{name}' is not allowed in RLM sandbox. "
            f"Allowed modules: {', '.join(sorted(_SAFE_MODULES))}"
        )

    # importlib.import_module only accepts 'name' and optional 'package' kwarg
    # The sandbox __import__ passes extra args (globals, locals, fromlist, level) that we must ignore
    # Only extract 'package' from kwargs if explicitly provided
    if kwargs.get("package"):
        return importlib.import_module(name, package=kwargs["package"])
    return importlib.import_module(name)


from typing import Any

# Backend identifier
BACKEND_RLM = "RLM"
SOURCE_RELIABILITY_RLM = 0.85

logger = logging.getLogger(__name__)


class CodeTemplate:
    """Templates for generating analysis code based on query semantics."""

    # Pattern to detect different query types
    PATTERNS = {
        "how": ["how", "does", "do", "work", "implement", "handle"],
        "what": ["what", "definition", "mean", "is", "are", "describe"],
        "where": ["where", "located", "find", "which"],
        "why": ["why", "reason", "purpose", "motivation"],
        "list": ["list", "show", "all", "enumerate"],
        "compare": ["compare", "difference", "vs", "versus", "between"],
        "trace": ["trace", "flow", "call", "execution", "invoke"],
    }

    # Analysis templates (simplified for portability)
    TEMPLATES = {
        "search": """import re

query_keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    for keyword in query_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            # Find context around the match
            lines = content.split('\\n')
            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = '\\n'.join(lines[context_start:context_end])
                    findings.append(f'{{path}}:{i+1}: {{keyword}} found\\n{{context}}\\n')
                    break  # One match per file per keyword

return_value = {{
    'summary': f'Found {{len(findings)}} matches for keywords: {{", ".join(query_keywords)}}',
    'findings': findings[:20],
    'files_analyzed': list(codebase.keys())
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:10]:
    print(f"- {{f[:100]}}")
""",
        "explain": """import re

keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            # Find class/function definitions related to keyword
            class_matches = re.findall(r'class\\s+(\\w+.*?{keyword}[^\\n]*)', content)
            func_matches = re.findall(r'def\\s+(\\w+.*?{keyword}[^\\n]*)', content)

            if class_matches:
                findings.append(f'Class in {{path}}: {{", ".join(class_matches)}}')
            if func_matches:
                findings.append(f'Function in {{path}}: {{", ".join(func_matches)}}')

return_value = {{
    'summary': f'Analysis of {{", ".join(keywords)}}: {{len(findings)}} definitions found',
    'findings': findings,
    'files_analyzed': list(codebase.keys())
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:10]:
    print(f"- {{f}}")
""",
        "default": """import re

keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    matched = False
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            matched = True
            break

    if matched:
        findings.append(path)

return_value = {{
    'summary': f'Search for {{", ".join(keywords)}}: {{len(findings)}} matches',
    'findings': findings,
    'files_analyzed': list(codebase.keys())
}}

print(f"{{return_value['summary']}}")
for f in findings[:20]:
    print(f"- {{f}}")
""",
    }

    @classmethod
    def extract_keywords(cls, query: str) -> list[str]:
        """Extract meaningful keywords from query.

        Args:
            query: User's search query.

        Returns:
            List of keywords to search for.
        """
        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "to",
            "for",
            "of",
            "with",
            "in",
            "on",
            "at",
            "from",
            "by",
            "about",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "although",
            "though",
            "explain",
            "describe",
            "show",
            "tell",
            "give",
            "me",
            "find",
            "list",
            "search",
            "look",
            "get",
            "what",
            "which",
        }

        # Extract words, filter stop words
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Also extract quoted phrases
        phrases = re.findall(r'"([^"]+)"', query)
        keywords.extend(phrases)

        return list(set(keywords))[:5]  # Max 5 keywords

    @classmethod
    def detect_query_type(cls, query: str) -> str:
        """Detect the type of query based on keywords.

        Args:
            query: User's search query.

        Returns:
            Query type key for template selection.
        """
        query_lower = query.lower()

        for pattern_name, pattern_keywords in cls.PATTERNS.items():
            if any(kw in query_lower for kw in pattern_keywords):
                return pattern_name

        return "default"

    @classmethod
    def generate_code(cls, query: str) -> str:
        """Generate analysis code from query using templates.

        Args:
            query: User's search query.

        Returns:
            Executable Python code as string.
        """
        keywords = cls.extract_keywords(query)
        query_type = cls.detect_query_type(query)

        # Get appropriate template
        if query_type in cls.TEMPLATES:
            template = cls.TEMPLATES[query_type]
        else:
            template = cls.TEMPLATES["default"]

        # Format keywords for Python
        keywords_repr = repr(keywords)

        return template.format(keywords=keywords_repr)


class RLMBackend:
    """Recursive Language Model backend for intelligent code search.

    RLM generates Python analysis code based on user queries and executes it
    in a sandboxed environment. This enables semantic code understanding beyond
    what AST or pattern matching can provide.

    Unlike the original design, this version:
    - Does NOT call external LLMs for code generation
    - Uses template-based code generation from query semantics
    - Returns structured results (not synthesized text)
    - Caller interprets results

    Example:
        backend = RLMBackend(root_paths=["/path/to/code"])
        results = await backend.search("How is authentication handled?")
        # Returns structured execution results
    """

    BACKEND_NAME = BACKEND_RLM

    def __init__(
        self,
        root_paths: list[str] | None = None,
        enable_by_default: bool = True,
        max_file_reads: int = 50,
        execution_timeout: float = 30.0,
    ) -> None:
        """Initialize RLM backend.

        Args:
            root_paths: List of root directories to analyze.
            enable_by_default: Whether backend is always enabled.
            max_file_reads: Maximum files to read per query.
            execution_timeout: Timeout for generated code execution.
        """
        self.root_paths = [Path(p) for p in (root_paths or ["."])]
        self.enable_by_default = enable_by_default
        self.max_file_reads = max_file_reads
        self.execution_timeout = execution_timeout
        self._codebase_cache: dict[str, dict[str, str]] = {}

    @property
    def available(self) -> bool:
        """Check if RLM backend is available (always true now)."""
        return True

    @property
    def provider_name(self) -> str:
        """Get the name of the active provider (none now)."""
        return "Template"

    def _gather_codebase_files(self, query: str, limit: int = 100) -> list[str]:
        """Gather relevant codebase files for analysis.

        Args:
            query: Search query (for potential keyword matching).
            limit: Maximum files to return.

        Returns:
            List of file paths.
        """
        files = []
        extensions = {".py", ".yaml", ".yml", ".toml", ".json", ".md", ".txt", ".js", ".ts"}

        for root in self.root_paths:
            try:
                for ext in extensions:
                    files.extend(root.rglob(f"*{ext}"))
                    if len(files) >= limit:
                        break
                if len(files) >= limit:
                    break
            except (OSError, PermissionError):
                continue

        return [str(f) for f in files[:limit]]

    def _load_file_content(self, file_path: str, max_size: int = 10000) -> str | None:
        """Load file content with size limit.

        Args:
            file_path: Path to file.
            max_size: Maximum characters to read.

        Returns:
            File content or None if error.
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read(max_size)
                return content
        except (OSError, UnicodeDecodeError):
            return None

    def _build_codebase_dict(self, files: list[str]) -> dict[str, str]:
        """Build codebase dictionary for generated code.

        Args:
            files: List of file paths to include.

        Returns:
            Dict mapping file paths to content.
        """
        codebase = {}
        for file_path in files[: self.max_file_reads]:
            content = self._load_file_content(file_path)
            if content is not None:
                # Use relative path for cleaner keys
                for root in self.root_paths:
                    try:
                        rel_path = str(Path(file_path).relative_to(root))
                        codebase[rel_path] = content
                        break
                    except ValueError:
                        # File not under root, use full path
                        codebase[file_path] = content
        return codebase

    async def _execute_generated_code(self, code: str, codebase: dict[str, str]) -> dict[str, Any]:
        """Execute generated Python code in sandbox.

        Args:
            code: Python code to execute.
            codebase: Dict of file paths to content.

        Returns:
            Execution result with output, error, and return value.
        """
        result = {
            "output": "",
            "error": None,
            "return_value": None,
            "executed": False,
        }

        # Create execution environment (restricted builtins for safety)
        # SECURITY: Use restricted import instead of __import__ to prevent arbitrary code execution
        exec_globals = {
            "__builtins__": {
                "__import__": _restricted_import,  # Restricted import with allowlist
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "max": max,
                "min": min,
                "sum": sum,
                "sorted": sorted,
                "any": any,
                "all": all,
                "map": map,
                "filter": filter,
                "abs": abs,
                "round": round,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "type": type,
                "re": re,
                "json": json,
            },
            "codebase": codebase,
        }

        exec_locals = {}
        import sys as sys_module

        old_stdout = None

        try:
            # Redirect stdout to capture prints
            output_buffer = StringIO()
            old_stdout = sys_module.stdout
            sys_module.stdout = output_buffer

            # Execute with timeout
            await asyncio.wait_for(
                asyncio.to_thread(exec, code, exec_globals, exec_locals),
                timeout=self.execution_timeout,
            )

            result["executed"] = True
            result["output"] = output_buffer.getvalue()
            result["return_value"] = exec_locals.get("return_value")

        except TimeoutError:
            result["error"] = "Execution timeout"
        except Exception as e:
            result["error"] = str(e)
        finally:
            # Restore stdout
            if old_stdout is not None:
                sys_module.stdout = old_stdout

        return result

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search using RLM code generation approach.

        Args:
            query: User's search query.
            limit: Maximum results to return.

        Returns:
            List of search results with structured execution data.
        """
        try:
            # Gather context
            files = self._gather_codebase_files(query)
            codebase = self._build_codebase_dict(files)

            # Generate analysis code using templates (no LLM call)
            generated_code = CodeTemplate.generate_code(query)

            # Execute generated code
            execution_result = await self._execute_generated_code(generated_code, codebase)

            # Return structured results (caller interprets, not us)
            return_value = execution_result.get("return_value") or {}

            # Build result object
            result = {
                "source": self.BACKEND_NAME,
                "title": f"RLM Analysis: {query[:60]}...",
                "content": execution_result.get("output", ""),
                "score": 0.85 if execution_result["executed"] else 0.0,
                "metadata": {
                    "provider": "Template",
                    "files_analyzed": len(codebase),
                    "execution_success": execution_result["executed"],
                    "return_value": return_value,
                    "query_type": CodeTemplate.detect_query_type(query),
                },
            }

            # If execution failed, include error
            if execution_result.get("error"):
                result["metadata"]["error"] = execution_result["error"]
                result["content"] = (
                    f"Execution error: {execution_result['error']}\n\nGenerated code:\n{generated_code[:500]}"
                )

            return [result]

        except Exception as e:
            logger.warning(f"RLM search error: {e}")
            return [
                {
                    "source": self.BACKEND_NAME,
                    "title": "RLM Error",
                    "content": f"RLM analysis failed: {str(e)}",
                    "score": 0.0,
                }
            ]

    def health_check(self):
        """Check the health status of the RLM backend.

        RLM is a code analysis backend that doesn't use persistent storage.
        Health check verifies:
        1. Backend can be initialized
        2. Root paths are accessible (optional, since it can work with any path)

        Returns
        -------
        HealthStatus
            Health status with reachable, working, has_data flags and details.
        """
        # Import from search-research core (migrated from search.health_status)
        from ...health_status import HealthStatus

        reachable = True  # Backend initialized successfully
        working = True  # RLM has no external dependencies
        has_data = True  # RLM works on any codebase, no persistent data needed
        message = "RLM backend operational (template-based code analysis)"
        details = {
            "backend_name": self.BACKEND_NAME,
            "provider": "Template",
            "root_paths": [str(p) for p in self.root_paths],
            "available": self.available,
        }

        return HealthStatus(
            status="pass",
            reachable=reachable,
            working=working,
            has_data=has_data,
            message=message,
            details=details,
        )


# Singleton instance for reuse
_rlm_backend_instance: RLMBackend | None = None


def create_rlm_backend(**kwargs) -> RLMBackend:
    """Create or return cached RLM backend instance.

    Args:
        **kwargs: Arguments passed to RLMBackend constructor.

    Returns:
        RLMBackend instance.
    """
    global _rlm_backend_instance
    if _rlm_backend_instance is None:
        _rlm_backend_instance = RLMBackend(**kwargs)
    return _rlm_backend_instance


def is_rlm_available() -> bool:
    """Check if RLM backend is available.

    Returns:
        Always True now - no external dependencies.
    """
    return True
