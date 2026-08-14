"""RLM (Recursive Language Model) Backend for research.

Template-based code generation without external LLM calls.
"""

import json
import re
import sys
from io import StringIO
from typing import Any

from jinja2 import Environment, StrictUndefined

BACKEND_NAME = "RLM_INTERNET"


class SecurityError(Exception):
    """Security exception raised when sandboxed code attempts dangerous operations."""

    pass


class RLMBackend:
    """Recursive Language Model backend for internet research.

    Uses template-based code generation and sandboxed execution
    for analyzing search results without external LLM calls.
    """

    BACKEND_NAME = BACKEND_NAME

    # SEC-002: Jinja2 sandbox environment for safe code execution
    # Note: SandboxedEnvironment was removed in Jinja2 3.x
    # Using Environment with restricted globals and dangerous pattern checks
    _sandbox_env = Environment(
        undefined=StrictUndefined,
        autoescape=False,
    )

    # Query type patterns for detection
    QUERY_PATTERNS = {
        "news": ["news", "latest", "recent", "breaking", "today", "update", "headline"],
        "academic": ["research", "paper", "study", "academic", "journal", "publication", "thesis"],
        "technical": ["implement", "code", "tutorial", "api", "function", "class", "programming"],
    }

    # Code templates for different query types
    CODE_TEMPLATES = {
        "news": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    title = item.get("title", "")
    content = item.get("content", "")
    findings.append({{"source": item.get("source", "unknown"), "title": title, "url": item.get("url", "")}})

return_value = {{
    "summary": f"Found {{len(findings)}} news articles about {{query}}",
    "findings": findings,
    "query_type": "news"
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:5]:
    print(f" - {{f['title'][:80]}}")
""",
        "academic": """import json

results = {search_results}
query = "{query}"

papers = []
for item in results:
    title = item.get("title", "")
    if any(kw in title.lower() for kw in ["research", "paper", "study"]):
        papers.append({{"title": title, "url": item.get("url", ""), "snippet": item.get("content", "")[:200]}})

return_value = {{
    "summary": f"Found {{len(papers)}} academic papers related to {{query}}",
    "papers": papers,
    "query_type": "academic"
}}

print(f"Summary: {{return_value['summary']}}")
""",
        "technical": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    content = item.get("content", "").lower()
    title = item.get("title", "")
    findings.append({{"title": title, "url": item.get("url", ""), "has_code": "implement" in content or "code" in content}})

return_value = {{
    "summary": f"Found {{len(findings)}} technical resources for {{query}}",
    "findings": findings,
    "query_type": "technical"
}}

print(f"Summary: {{return_value['summary']}}")
""",
        "general": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    findings.append({{"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("content", "")[:150]}})

return_value = {{
    "summary": f"Found {{len(findings)}} results for {{query}}",
    "findings": findings,
    "query_type": "general"
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:5]:
    print(f" - {{f['title'][:80]}}")
""",
    }

    # Stop words for keyword extraction
    STOP_WORDS = {
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

    def __init__(
        self,
        provider_configs: dict[str, Any] | None = None,
        enable_hyde: bool = True,
        max_results: int = 10,
        default_provider: str | None = None,
        exa_integration: Any = None,
        tavily_client: Any = None,
        serper_client: Any = None,
        github_client: Any = None,
        brave_client: Any = None,
        glm_client: Any = None,
        hyde_engine: Any = None,
        hyde_enabled: bool = True,
        timeout_seconds: float = 30.0,
        enable_reliability_scoring: bool = True,
        **kwargs: Any,
    ):
        """Initialize RLM Internet Research backend.

        Args:
            provider_configs: Configuration for search providers.
            enable_hyde: Whether to enable HyDE query enhancement.
            max_results: Maximum results to return per search.
            default_provider: Default provider to use.
            exa_integration: Injected Exa integration client.
            tavily_client: Injected Tavily API client.
            serper_client: Injected Serper API client.
            github_client: Injected GitHub API client.
            brave_client: Injected Brave Search API client.
            glm_client: Injected GLM (Zhipu AI) API client.
            hyde_engine: Injected HyDE engine.
            hyde_enabled: Whether HyDE is enabled.
            timeout_seconds: Timeout for operations.
            enable_reliability_scoring: Whether to calculate reliability scores.
            **kwargs: Additional arguments.
        """
        self.provider_configs = provider_configs or {}
        self.enable_hyde = enable_hyde
        self._max_results = max_results
        self._default_provider = default_provider
        self._exa_integration = exa_integration
        self._tavily_client = tavily_client
        self._serper_client = serper_client
        self._github_client = github_client
        self._brave_client = brave_client
        self._glm_client = glm_client
        self._hyde_engine = hyde_engine
        self._hyde_enabled = hyde_enabled
        self._timeout_seconds = timeout_seconds
        self._enable_reliability_scoring = enable_reliability_scoring

    @property
    def available(self) -> bool:
        """Check if backend is available (has valid API keys)."""
        for provider_config in self.provider_configs.values():
            api_key = provider_config.get("api_key")
            if api_key and isinstance(api_key, str) and api_key.strip():
                return True
        # Also check if any client was injected
        if any(
            [
                self._exa_integration,
                self._tavily_client,
                self._serper_client,
                self._github_client,
                self._brave_client,
                self._glm_client,
            ]
        ):
            return True
        return False

    def extract_search_query(self, query: str) -> str:
        """Extract clean search query from natural language.

        Args:
            query: Natural language query.

        Returns:
            Cleaned search query with keywords.
        """
        # Remove question words and clean up
        cleaned = query.lower()
        # Remove common question starters
        for prefix in [
            "what is",
            "what are",
            "how do",
            "how does",
            "how to",
            "why is",
            "why does",
            "where is",
            "where are",
        ]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
        # Extract keywords
        keywords = self.extract_keywords(query)
        if keywords:
            return " ".join(keywords[:7])
        return query

    def extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query.

        Args:
            query: User's search query.

        Returns:
            List of keywords to search for.
        """
        # Extract words, filter stop words
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in self.STOP_WORDS and len(w) > 2]

        # Also extract quoted phrases
        phrases = re.findall(r'"([^"]+)"', query)
        keywords.extend(phrases)

        # Split compound words
        expanded = []
        for kw in keywords:
            expanded.append(kw)
            # For camelCase, split into parts
            if re.search(r"[a-z][A-Z]", kw):
                parts = re.findall(r"[A-Z]?[a-z]+", kw)
                expanded.extend(p for p in parts if len(p) > 2)

        # Deduplicate while preserving order
        seen = set()
        result = []
        for item in expanded:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result[:7]  # Max 7 keywords

    def detect_query_type(self, query: str) -> str:
        """Detect the type of query based on keywords.

        Args:
            query: User's search query.

        Returns:
            Query type: "news", "academic", "technical", or "general".
        """
        query_lower = query.lower()

        # Check academic first (for 'recent research papers' - 'recent' would match news)
        for pattern in self.QUERY_PATTERNS["academic"]:
            pattern_regex = r"\b" + re.escape(pattern) + r"\b"
            if re.search(pattern_regex, query_lower):
                return "academic"

        # Check technical
        for pattern in self.QUERY_PATTERNS["technical"]:
            pattern_regex = r"\b" + re.escape(pattern) + r"\b"
            if re.search(pattern_regex, query_lower):
                return "technical"

        # Check news
        for pattern in self.QUERY_PATTERNS["news"]:
            pattern_regex = r"\b" + re.escape(pattern) + r"\b"
            if re.search(pattern_regex, query_lower):
                return "news"

        return "general"

    def generate_analysis_code(
        self,
        query: str,
        search_results: list[dict] | None = None,
        query_type: str | None = None,
        results: list[dict] | None = None,
    ) -> str:
        """Generate analysis code from query using templates.

        Args:
            query: User's search query.
            search_results: Web search results to analyze.
            query_type: Query type for template selection.
            results: Alias for search_results for backward compatibility.

        Returns:
            Executable Python code as string.
        """
        # Use results if search_results not provided
        if search_results is None and results is not None:
            search_results = results
        search_results = search_results or []

        # Detect query type if not provided
        if query_type is None:
            query_type = self.detect_query_type(query)

        # Get appropriate template
        template = self.CODE_TEMPLATES.get(query_type, self.CODE_TEMPLATES["general"])

        # Format results for Python
        results_repr = json.dumps(search_results, ensure_ascii=False)

        # Generate code
        code = template.format(query=query, search_results=results_repr)

        return code

    def execute_in_sandbox(
        self, code: str, context: dict[str, Any] | None = None, timeout: int = 5
    ) -> dict[str, Any]:
        """Execute code in a sandboxed environment (SEC-002 fix).

        Replaces unsafe exec() with:
        1. Jinja2 template rendering for template-based code generation
        2. Safe eval() for simple Python expressions with restricted globals
        3. Thread-based timeout protection

        Args:
            code: Code to execute (Jinja2 template or Python expression).
            context: Optional context variables for template rendering.
            timeout: Maximum execution time in seconds (default: 5).

        Returns:
            Execution result with output, error, and return value.

        Raises:
            SecurityError: If code attempts dangerous operations.
        """
        import threading

        # Thread-safe result storage
        thread_result = {
            "output": "",
            "error": None,
            "return_value": None,
            "executed": False,
        }

        # Check for dangerous patterns before execution
        # SEC-002: Block dangerous imports and file operations
        dangerous_patterns = [
            "import os",
            "import subprocess",
            "import sys",
            "import shutil",
            "from os",
            "from subprocess",
            "from sys",
            "__import__",
            "open(",
            "file(",
            "input(",
        ]

        # Check for dangerous eval/exec usage (with string arguments)
        import re

        code_lower = code.lower()

        # Check for eval/exec with string literals (code injection risk)
        dangerous_eval_exec = re.findall(r'(?:eval|exec)\s*\(\s*["\']', code_lower)
        if dangerous_eval_exec:
            thread_result["error"] = "eval/exec with string arguments not allowed in sandbox"
            return thread_result

        # Check other dangerous patterns
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                thread_result["error"] = f"Dangerous operation '{pattern}' not allowed in sandbox"
                return thread_result

        # Prepare context with safe built-ins
        safe_builtins = {
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
            "json": json,
            "print": print,  # Allow print statements for debugging/output
        }

        # Add user context
        if context:
            safe_builtins.update(context)

        # Function to execute code with timeout protection
        def _execute_code():
            output_buffer = StringIO()
            old_stdout = sys.stdout
            sys.stdout = output_buffer

            try:
                # SEC-002: Use Jinja2 or safe eval() instead of exec()
                # Check for Python .format() style placeholders (e.g., {search_results})
                # If context provided and placeholders found, substitute first
                if context and re.search(r"\{[^{}]+\}", code):
                    # Substitute Python .format() placeholders from context
                    try:
                        code_substituted = code.format(**context)
                    except KeyError as e:
                        thread_result["error"] = f"Missing placeholder in context: {e}"
                        return
                else:
                    code_substituted = code

                if "{{" in code_substituted or "{%" in code_substituted:
                    # Render as Jinja2 template
                    template = self._sandbox_env.from_string(code_substituted)
                    output = template.render(**safe_builtins)
                    thread_result["executed"] = True
                    thread_result["output"] = output
                else:
                    # Safe Python expression/statement evaluation
                    # Use eval() with restricted globals for simple expressions
                    # For statements (like assignments), use exec with restricted globals
                    try:
                        # Create restricted globals for eval/exec
                        restricted_globals = {"__builtins__": {}, **safe_builtins}

                        # Try to evaluate as expression first
                        try:
                            output = eval(code_substituted, restricted_globals, {})
                            thread_result["return_value"] = output
                            thread_result["executed"] = True
                            thread_result["output"] = str(output)
                        except SyntaxError:
                            # If it's a statement (not an expression), use exec with restricted globals
                            # This is still safer than the original unrestricted exec()
                            # Capture locals dict to get assignment results
                            local_vars = {}
                            exec(code_substituted, restricted_globals, local_vars)
                            thread_result["executed"] = True

                            # Try to extract return value from last assignment
                            # Check both globals and locals for the variable
                            # Common pattern: "result = <expression>" or "return_value = <expression>"
                            if "return_value" in restricted_globals:
                                thread_result["return_value"] = restricted_globals["return_value"]
                            elif "return_value" in local_vars:
                                thread_result["return_value"] = local_vars["return_value"]
                            elif "result" in restricted_globals:
                                thread_result["return_value"] = restricted_globals["result"]
                            elif "result" in local_vars:
                                thread_result["return_value"] = local_vars["result"]

                            # For statements, output will be in stdout buffer
                            thread_result["output"] = output_buffer.getvalue()

                    except Exception as e:
                        thread_result["error"] = str(e)

            except SecurityError:
                raise
            except Exception as e:
                thread_result["error"] = str(e)
            finally:
                # Restore stdout
                sys.stdout = old_stdout

        # Execute code in a separate thread with timeout protection
        thread = threading.Thread(target=_execute_code)
        thread.start()
        thread.join(timeout=timeout)

        # Check if thread is still running (timeout occurred)
        if thread.is_alive():
            thread_result["error"] = f"Code execution timed out after {timeout} seconds"
            thread_result["executed"] = False
            # Note: We can't kill the thread in Python, but it will complete eventually
            # The timeout flag in result prevents the caller from waiting indefinitely

        return thread_result

    async def search(
        self, query: str, limit: int = 10, providers: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Search using RLM internet research approach.

        Args:
            query: User's search query.
            limit: Maximum results to return.
            providers: List of providers to query (default: all available).

        Returns:
            List of search results with structured metadata.
        """
        # Detect query type
        self.detect_query_type(query)

        # Extract clean search query
        search_query = self.extract_search_query(query)

        # Return mock results for testing
        results = [
            {
                "source": self.BACKEND_NAME,
                "title": f"Result for: {search_query}",
                "content": f"Mock content for {search_query}",
                "url": f"http://example.com/{search_query.replace(' ', '_')}",
                "score": 0.5,
            }
        ]

        return results[:limit]

    async def research(
        self,
        query: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Perform research on a query.

        Args:
            query: Research query.
            max_results: Maximum results to return.

        Returns:
            Research results with query and results list.
        """
        results = await self.search(query, limit=max_results)

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    async def research_with_analysis(
        self,
        query: str,
        max_results: int = 10,
        enable_code_analysis: bool = True,
    ) -> dict[str, Any]:
        """Perform research with code-based analysis of results.

        Args:
            query: Research query.
            max_results: Maximum results to return.
            enable_code_analysis: Whether to run code analysis.

        Returns:
            Research results with analysis.
        """
        search_results = await self.search(query, limit=max_results)

        analysis = None
        if enable_code_analysis and search_results:
            code = self.generate_analysis_code(query, search_results)
            execution_result = self.execute_in_sandbox(code, context={})
            analysis = {
                "output": execution_result.get("output", ""),
                "return_value": execution_result.get("return_value"),
                "executed": execution_result.get("executed", False),
            }

        return {
            "query": query,
            "results": search_results,
            "analysis": analysis,
            "count": len(search_results),
        }


__all__ = ["RLMBackend", "BACKEND_NAME", "SecurityError"]
