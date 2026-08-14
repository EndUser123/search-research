#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path

# Platform-specific file locking
try:
    import fcntl

    HAVE_FCNTL = True
except ImportError:
    HAVE_FCNTL = False

try:
    import msvcrt

    HAVE_MSVCRT = True
except ImportError:
    HAVE_MSVCRT = False

logger = logging.getLogger(__name__)


class _FileLock:
    """Cross-platform file locking context manager with retry logic.

    Falls back gracefully if file locking is not available on the platform.
    Uses non-blocking locks with retries to handle concurrent access.
    """

    MAX_RETRIES = 5
    RETRY_DELAY = 0.1  # seconds

    def __init__(self, file_obj) -> None:
        self.file_obj = file_obj
        self.is_windows = sys.platform == "win32"
        self.has_lock = HAVE_MSVCRT if self.is_windows else HAVE_FCNTL
        self.lock_acquired = False

    def __enter__(self):
        if not self.has_lock:
            # File locking not available, proceed without lock
            return self

        # Retry logic for acquiring lock
        import time

        for attempt in range(self.MAX_RETRIES):
            try:
                if self.is_windows:
                    # Windows: Non-blocking lock, raises exception if locked
                    msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # Unix: Non-blocking lock
                    fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.lock_acquired = True
                return self
            except (OSError, PermissionError) as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2**attempt))
                else:
                    # Failed after retries, log and continue without lock
                    logger.warning(
                        f"Could not acquire file lock after {self.MAX_RETRIES} attempts: {e}"
                    )
                    return self

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.has_lock or not self.lock_acquired:
            return
        try:
            if self.is_windows:
                # Windows: Unlock the region
                msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                # Unix: Release the lock
                fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_UN)
        except (OSError, PermissionError):
            # Suppress unlock errors - file may be closed by another process
            pass
        self.lock_acquired = False


class AutoLearningQueryExpander:
    ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")
    DEFAULT_SIMILARITY_THRESHOLD = 0.3
    DEFAULT_MIN_RESULTS = 2

    def __init__(self, dry_run: bool = False, cks_path: Path | None = None) -> None:
        self.dry_run = dry_run
        self.cks_path = cks_path
        self._query_expander = None
        self._existing_abbreviations: set[str] = set()
        self._existing_synonyms: set[str] = set()
        self._load_existing_mappings()
        self._learned_mappings: dict[str, dict] = {}

    def _load_existing_mappings(self) -> None:
        try:
            from ..query_expansion import QueryExpander

            self._query_expander = QueryExpander()
            self._existing_abbreviations = set(self._query_expander.abbreviations.keys())
            self._existing_synonyms = set(self._query_expander.synonyms.keys())
        except ImportError:
            logger.warning("QueryExpander not available")

    @property
    def query_expander(self):
        return self._query_expander

    def detect_unknown_terms(
        self,
        query: str,
        results: list[dict],
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[str]:
        unknown_terms = []
        if not self._is_poor_search(results, similarity_threshold):
            return unknown_terms

        # Build a map of lowercase terms to their original forms in the query
        original_terms_map = {}
        for word in self.ACRONYM_PATTERN.findall(query):
            original_terms_map[word.lower()] = word
        for word in re.findall(r"\b[a-z]{2,6}\b", query):
            if word.lower() not in original_terms_map:
                original_terms_map[word.lower()] = word

        for word in self._extract_terms(query):
            word_lower = word.lower()
            if (
                word_lower not in self._existing_abbreviations
                and word_lower not in self._existing_synonyms
            ):
                original_casing = original_terms_map.get(word_lower, word)
                if self._is_unknown_term(word_lower, original_casing):
                    unknown_terms.append(word_lower)
        return unknown_terms

    def _is_poor_search(self, results: list[dict], threshold: float) -> bool:
        if not results or len(results) < self.DEFAULT_MIN_RESULTS:
            return True
        similarities = [r.get("similarity") or r.get("score") or 0 for r in results]
        return sum(similarities) / len(similarities) < threshold if similarities else True

    def _extract_terms(self, query: str) -> list[str]:
        terms = list(self.ACRONYM_PATTERN.findall(query))
        stop_words = {"the", "for", "and", "with", "from", "search", "find", "get"}
        for word in re.findall(r"\b[a-z]{2,6}\b", query.lower()):
            if word not in stop_words:
                terms.append(word)
        return terms

    def _is_unknown_term(self, term: str, original_term: str | None = None) -> bool:
        """Check if term is unknown (not in abbreviations/synonyms).

        Args:
            term: The lowercase version of the term
            original_term: The original cased term from query. If provided and ALL CAPS,
                         common word filtering is bypassed (likely an acronym).

        """
        term_lower = term.lower() if isinstance(term, str) else term
        if term_lower in self._existing_abbreviations or term_lower in self._existing_synonyms:
            return False

        common_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "has",
            "have",
            "been",
            "will",
            "with",
            "from",
            "this",
            "that",
            "search",
            "find",
            "get",
            "show",
        }

        # If original term is ALL CAPS, it's likely an acronym - bypass common word check
        if original_term and original_term.isupper() and len(original_term) <= 6:
            return 2 <= len(term) <= 10

        return term_lower not in common_words and 2 <= len(term) <= 10

    def _is_valid_definition(self, text: str) -> bool:
        """Check if extracted text looks like a valid definition.

        Quality heuristics:
        - Not a question (no "is/are/what/how/why" at start)
        - Not an imperative (no "learn/discover/find" at start)
        - Proper length (2-8 words)
        - Not a markdown heading
        - Not a URL or HTML
        - Starts with capital letter (for proper definitions)
        """
        if not text:
            return False

        text = text.strip()
        words = text.split()
        word_count = len(words)

        # Length check
        if word_count < 2 or word_count > 8:
            return False

        first_word = words[0].lower()

        # Question patterns - reject
        question_starters = {
            "is",
            "are",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "does",
            "do",
            "can",
        }
        if first_word in question_starters:
            return False

        # Imperative/heading patterns - reject
        imperative_starters = {
            "learn",
            "discover",
            "find",
            "explore",
            "understand",
            "see",
            "get",
            "using",
            "with",
            "from",
        }
        if first_word in imperative_starters:
            return False

        # Markdown headings
        if text.startswith(("#", "##")):
            return False

        # Contains URLs or HTML
        if "http://" in text or "https://" in text or "<" in text:
            return False

        # Contains common non-definition markers (aggressive patterns only)
        non_def_markers = ["###", "##"]
        if any(marker in text for marker in non_def_markers):
            return False

        # Should start with capital letter (proper noun/definition)
        if not text[0].isupper():
            return False

        # Contains too many special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and c not in " -") / len(text)
        return not special_char_ratio > 0.3

    def _is_valid_definition_stands_for(self, text: str) -> bool:
        """Check if text from 'stands for' format is a valid definition.

        Similar to _is_valid_definition but allows common phrases that appear
        after 'stands for' like 'the', 'a', 'an'.
        """
        if not text:
            return False

        text = text.strip()
        words = text.split()
        word_count = len(words)

        # Length check (slightly more lenient for 'stands for' format)
        if word_count < 2 or word_count > 10:
            return False

        # Remove leading articles for validation
        first_word = words[0].lower()
        if first_word in {"a", "an", "the"} and len(words) > 2:
            first_word = words[1].lower()

        # Question patterns - reject
        question_starters = {
            "is",
            "are",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "does",
            "do",
            "can",
        }
        if first_word in question_starters:
            return False

        # Markdown headings
        if text.startswith(("#", "##")):
            return False

        # Contains URLs or HTML
        if "http://" in text or "https://" in text or "<" in text:
            return False

        # Should start with capital letter
        return text[0].isupper()

    def extract_definition(self, content: str, term: str) -> str:
        if not content:
            return ""

        # Pattern 1: **HyDE (Hypothetical Document Embeddings)** - bold term with parenthetical definition
        pattern1 = re.compile(rf"\*\*{re.escape(term)}\s*\(\s*([^)]+?)\s*\)\*\*", re.IGNORECASE)
        match = pattern1.search(content)
        if match:
            definition = match.group(1).strip()
            if self._is_valid_definition(definition):
                return definition

        # Pattern 2: HyDE (Hypothetical Document Embeddings) - term with parenthetical definition
        # Use word boundary to avoid matching substrings
        pattern2 = re.compile(rf"\b{re.escape(term)}\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE)
        match = pattern2.search(content)
        if match:
            definition = match.group(1).strip()
            if self._is_valid_definition(definition):
                return definition

        # Pattern 3: HyDE - Hypothetical Document Embeddings - term followed by dash/colon
        # Use word boundary and limit to reasonable length
        pattern3 = re.compile(
            r"\b" + re.escape(term) + r"\s*[-:]\s*([A-Z][^\n\r]{10,100}?(?=\n|[.!?]|$))",
            re.IGNORECASE,
        )
        match = pattern3.search(content)
        if match:
            definition = match.group(1).strip()
            if self._is_valid_definition(definition):
                return definition

        # Pattern 4: Application Programming Interfaces (APIs) - definition before term in parentheses
        # More specific: match capitalized phrase ending before (term)
        pattern4 = re.compile(
            rf"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{0,4}})\s*\(\s*{re.escape(term)}s?\s*\)",
            re.IGNORECASE,
        )
        match = pattern4.search(content)
        if match:
            definition = match.group(1).strip()
            # Only remove trailing 's' if the original term was plural
            # Check if the matched pattern had plural form (term with 's')
            full_match = match.group(0)
            # Extract the term from the match to see if it had trailing 's'
            term_pattern = rf"\({re.escape(term)}s?\)"
            term_in_match = re.search(term_pattern, full_match)
            if term_in_match and term_in_match.group(1).endswith("s"):
                definition = definition.rstrip("s")
            # Clean up common prefix words
            for prefix in ["These", "The", "Those", "Some", "Various", "By using", "Using", "In"]:
                if definition.startswith(prefix + " "):
                    definition = definition[len(prefix) + 1 :]
            if self._is_valid_definition(definition):
                return definition

        # Pattern 5: **root cause analysis** (**RCA**) - bold definition before bold term
        pattern5 = re.compile(
            rf"\*\*([A-Z][a-zA-Z\s\-]{2,40}?)\*\*\s*\(\s*\*\*{re.escape(term)}\*\*\s*\)",
            re.IGNORECASE,
        )
        match = pattern5.search(content)
        if match:
            definition = match.group(1).strip()
            if self._is_valid_definition(definition):
                return definition

        # Pattern 6: CAN stands for Controller Area Network - "term stands for definition" format
        pattern6 = re.compile(
            r"\b" + re.escape(term) + r"\s+stands\s+for\s+([A-Z][^\.\r\n]{10,100}?)(?:\.|,|;|$)",
            re.IGNORECASE,
        )
        match = pattern6.search(content)
        if match:
            definition = match.group(1).strip()
            # Clean up trailing punctuation
            definition = definition.rstrip(".,;:")
            if self._is_valid_definition_stands_for(definition):
                return definition
        # Pattern 7: TERM, aka Definition / TERM, also known as Definition
        pattern7 = re.compile(
            r"\b"
            + re.escape(term)
            + r",\s+(?:aka|also\s+known\s+as)\s+([A-Z][^.,;:]{10,100}?)(?:[.,;:?]|$)",
            re.IGNORECASE,
        )
        match = pattern7.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:")
            if self._is_valid_definition(definition):
                return definition

        # Pattern 8: TERM, short for Definition
        pattern8 = re.compile(
            r"\b" + re.escape(term) + r",\s+short\s+for\s+([A-Z][^.,;:]{10,100}?)(?:[.,;:?]|$)",
            re.IGNORECASE,
        )
        match = pattern8.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:")
            if self._is_valid_definition(definition):
                return definition

        # Pattern 9: TERM refers to Definition
        pattern9 = re.compile(
            r"\b"
            + re.escape(term)
            + r"\s+refers\s+to\s+(?:the\s+)?([A-Z][^.,;:]{10,100}?)(?:[.,;:?]|$)",
            re.IGNORECASE,
        )
        match = pattern9.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:")
            if self._is_valid_definition(definition):
                return definition
        # Pattern 10: TERM is an abbreviation for Definition
        pattern10 = re.compile(
            r"\b"
            + re.escape(term)
            + r"\s+is\s+an\s+abbreviation\s+for\s+([A-Z][^.,;:?]{10,100}?)(?:[.,;:?]|$)",
            re.IGNORECASE,
        )
        match = pattern10.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:?")
            if self._is_valid_definition(definition):
                return definition

        # Pattern 11: TERM = Definition
        pattern11 = re.compile(
            r"\b" + re.escape(term) + r"\s=\s*([A-Z][^.,;:?\n\r]{10,100}?)(?:[.,;:?]|$|\n)",
            re.IGNORECASE,
        )
        match = pattern11.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:?")
            if self._is_valid_definition(definition):
                return definition

        # Pattern 12: Definition, abbreviated as TERM
        pattern12 = re.compile(
            r"([A-Z][a-zA-Z\s\-]{10,80}?),\s*abbreviated\s+as\s+" + re.escape(term) + r"\b",
            re.IGNORECASE,
        )
        match = pattern12.search(content)
        if match:
            definition = match.group(1).strip().rstrip(".,;:?")
            if self._is_valid_definition(definition):
                return definition

        return ""

    async def _extract_definition_with_llm(self, term: str, contents: list[str]) -> str:
        """Extract definition using LLM for better accuracy.

        Args:
            term: The term to define (e.g., "rca", "hyde")
            contents: List of content snippets from search results

        Returns:
            Extracted definition or empty string

        """
        if not contents:
            return ""

        # Prepare context from search results (limit to avoid token limits)
        context = "\n\n".join([c[:1000] for c in contents[:3]])

        prompt = f"""Extract the definition of the term "{term}" from the following search results.
Return ONLY the definition (2-8 words), nothing else. If no clear definition exists, return "UNKNOWN".

Search results:
{context}

Definition:"""

        try:
            import subprocess

            from cli.subprocess_helper import run_subprocess

            result = run_subprocess(
                ["python", "-m", "claude", "ask", prompt, "--max-tokens", "50"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent,
            )

            if result.returncode == 0:
                definition = result.stdout.strip()
                # Clean up the response
                definition = definition.replace("Definition:", "").strip()
                if definition and definition.upper() != "UNKNOWN" and len(definition.split()) <= 10:
                    return definition

        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"LLM extraction via subprocess failed: {e}")

        # Fallback: Try importing brainstorm LLM client
        try:
            from brainstorm.llm.llm_client import DGATELLMClient, LLMConfig

            config = LLMConfig(mock_mode=False, temperature=0.3, max_tokens=100)
            client = DGATELLMClient(config)

            response = await client.generate(
                prompt=prompt,
                system_prompt="You are a precise definition extractor. Return only the definition, nothing else.",
                temperature=0.3,
                max_tokens=50,
            )

            if response.content:
                definition = response.content.strip()
                if definition and definition.upper() != "UNKNOWN" and len(definition.split()) <= 10:
                    return definition

        except ImportError:
            logger.debug("brainstorm.llm.LLMClient not available")
        except Exception as e:
            logger.debug(f"LLM extraction failed: {e}")

        return ""

    def _extract_definition_with_llm_sync(self, term: str, contents: list[str]) -> str:
        """Synchronous wrapper for LLM definition extraction.

        Uses asyncio.run() to execute the async method. If called from an
        async context, this will gracefully fall back to empty string.
        """
        try:
            # Check if we're already in an async context
            try:
                asyncio.get_running_loop()
                # Already in async context - can't use asyncio.run()
                # The caller should await _extract_definition_with_llm() directly
                logger.debug(
                    "LLM extraction: Called from async context. "
                    "Use await _extract_definition_with_llm() directly for LLM fallback.",
                )
                return ""
            except RuntimeError:
                # No running loop - safe to use asyncio.run()
                pass

            # asyncio.run() creates a new loop, runs the coroutine, and closes it
            return asyncio.run(self._extract_definition_with_llm(term, contents))
        except Exception as e:
            logger.debug(f"LLM extraction error: {e}")
            return ""

    def _persist_mapping_ast(self, term: str, expansion: str) -> bool:
        """Persist a new abbreviation mapping using AST parsing.

        More robust than regex - handles formatting changes gracefully.

        Args:
            term: The abbreviation term (e.g., "hyde")
            expansion: The full expansion (e.g., "hypothetical document embeddings")

        Returns:
            True if successfully persisted, False otherwise

        """
        if self.dry_run:
            return False

        # Determine the path to query_expansion.py
        if self.cks_path:
            expansion_file = self.cks_path / "query_expansion.py"
        else:
            try:
                import CKS

                expansion_file = Path(cks.__file__).parent / "query_expansion.py"
            except (ImportError, AttributeError):
                expansion_file = Path(__file__).parent.parent / "query_expansion.py"

        if not expansion_file.exists():
            logger.warning(f"query_expansion.py not found at {expansion_file}")
            return False

        try:
            import ast

            # Parse the file as AST
            source_code = expansion_file.read_text(encoding="utf-8")
            tree = ast.parse(source_code)

            # Find the QueryExpander class and _load_abbreviations method
            term_lower = term.lower()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "QueryExpander":
                    for method in node.body:
                        if (
                            isinstance(method, ast.FunctionDef)
                            and method.name == "_load_abbreviations"
                        ):
                            # Find the return statement with the dict
                            for stmt in ast.walk(method):
                                if isinstance(stmt, ast.Return) and isinstance(
                                    stmt.value, ast.Dict
                                ):
                                    # Check if term already exists
                                    existing = False
                                    for key in stmt.value.keys:
                                        key_value = None
                                        if isinstance(key, ast.Constant):
                                            key_value = key.value
                                        elif isinstance(key, ast.Str):  # Python < 3.8
                                            key_value = key.s

                                        if key_value == term_lower:
                                            existing = True
                                            break

                                    # Only add if not already present
                                    if not existing:
                                        new_key = ast.Constant(value=term_lower)
                                        new_value = ast.Constant(value=expansion)
                                        stmt.value.keys.append(new_key)
                                        stmt.value.values.append(new_value)
                                    break
                            break

            # Write back with consistent formatting
            new_code = ast.unparse(tree)

            with open(expansion_file, "w", encoding="utf-8") as f, _FileLock(f):
                f.write(new_code)

            logger.info(f"AST persisted mapping: {term} -> {expansion}")
            return True

        except Exception as e:
            logger.debug(f"AST persistence failed, falling back to regex: {e}")
            # Fall back to regex method
            return self._persist_mapping(term, expansion)

    def _remove_persisted_mapping_ast(self, term: str) -> bool:
        """Remove a persisted mapping using AST parsing.

        Args:
            term: The term to remove (case-insensitive)

        Returns:
            True if successfully removed, False otherwise

        """
        if self.dry_run:
            return False

        # Determine the path to query_expansion.py
        if self.cks_path:
            expansion_file = self.cks_path / "query_expansion.py"
        else:
            try:
                import CKS

                expansion_file = Path(cks.__file__).parent / "query_expansion.py"
            except (ImportError, AttributeError):
                expansion_file = Path(__file__).parent.parent / "query_expansion.py"

        if not expansion_file.exists():
            logger.warning(f"query_expansion.py not found at {expansion_file}")
            return False

        try:
            import ast

            # Parse the file as AST
            source_code = expansion_file.read_text(encoding="utf-8")
            tree = ast.parse(source_code)

            removed = False
            term_lower = term.lower()

            # Find the QueryExpander class and _load_abbreviations method
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "QueryExpander":
                    for method in node.body:
                        if (
                            isinstance(method, ast.FunctionDef)
                            and method.name == "_load_abbreviations"
                        ):
                            # Find the return statement with the dict
                            for stmt in ast.walk(method):
                                if isinstance(stmt, ast.Return) and isinstance(
                                    stmt.value, ast.Dict
                                ):
                                    # Find and remove the matching key
                                    keys_to_keep = []
                                    values_to_keep = []
                                    for key, value in zip(
                                        stmt.value.keys, stmt.value.values, strict=False
                                    ):
                                        # Check if this is the term to remove
                                        key_value = None
                                        if isinstance(key, ast.Constant):
                                            key_value = key.value
                                        elif isinstance(key, ast.Str):  # Python < 3.8
                                            key_value = key.s

                                        if key_value != term_lower:
                                            keys_to_keep.append(key)
                                            values_to_keep.append(value)
                                        else:
                                            removed = True

                                    stmt.value.keys = keys_to_keep
                                    stmt.value.values = values_to_keep
                                    break
                            break

            if not removed:
                logger.debug(f"Term '{term}' not found in query_expansion.py")
                return False

            # Write back
            new_code = ast.unparse(tree)

            with open(expansion_file, "w", encoding="utf-8") as f, _FileLock(f):
                f.write(new_code)

            logger.info(f"AST removed persisted mapping: {term}")
            return True

        except Exception as e:
            logger.debug(f"AST removal failed, falling back to regex: {e}")
            # Fall back to regex method
            return self._remove_persisted_mapping(term)

    def _persist_mapping(self, term: str, expansion: str) -> bool:
        """Persist a new abbreviation mapping to query_expansion.py.

        Args:
            term: The abbreviation term (e.g., "hyde")
            expansion: The full expansion (e.g., "hypothetical document embeddings")

        Returns:
            True if successfully persisted, False otherwise

        """
        if self.dry_run:
            return False

        # Determine the path to query_expansion.py
        if self.cks_path:
            expansion_file = self.cks_path / "query_expansion.py"
        else:
            # Try to find it relative to this module
            try:
                import CKS

                expansion_file = Path(cks.__file__).parent / "query_expansion.py"
            except (ImportError, AttributeError):
                expansion_file = Path(__file__).parent.parent / "query_expansion.py"

        if not expansion_file.exists():
            logger.warning(f"query_expansion.py not found at {expansion_file}")
            return False

        try:
            with open(expansion_file, "r+", encoding="utf-8") as f, _FileLock(f):
                f.seek(0)
                content = f.read()

                # Check if already exists
                if f'"{term}":' in content or f"'{term}':" in content:
                    logger.info(f"Term '{term}' already exists in query_expansion.py")
                    return True

                # Find the _load_abbreviations method and the return statement
                # Pattern: find the closing "}" of _load_abbreviations (before _load_entity_terms)
                # Use negative lookahead to stop at next method definition
                abbrev_pattern = re.compile(
                    r"(_load_abbreviations\(self\).*?return\s*\{.*?)(\n\s{8}\})(?=\n\s{0,4}def\s)",
                    re.DOTALL,
                )
                match = abbrev_pattern.search(content)

                if match:
                    # Insert new abbreviation before the closing brace
                    indent = "            "  # 12 spaces
                    new_entry = f'{indent}"{term}": "{expansion}",\n'
                    new_content = (
                        content[: match.end(1)]
                        + new_entry
                        + match.group(2)
                        + content[match.end(2) :]
                    )
                    # Write with file locking already active above
                    f.seek(0)
                    f.write(new_content)
                    f.truncate()
                    logger.info(f"Persisted mapping: {term} -> {expansion}")
                    return True
                logger.warning("Could not find _load_abbreviations return statement")
                return False

        except Exception as e:
            logger.exception(f"Failed to persist mapping: {e}")
            return False

    def add_mapping(
        self, term: str, expansion: str, source: str = "auto_learned", confidence: float = 0.5
    ) -> dict:
        result = {
            "success": False,
            "term": term.lower(),
            "expansion": expansion,
            "source": source,
            "confidence": confidence,
            "persisted": False,
            "message": "",
        }
        if not term or not expansion:
            result["message"] = "Required"
            return result
        term_lower = term.lower()
        if term_lower in self._existing_abbreviations:
            result["success"] = True
            result["message"] = "Exists"
            return result
        self._learned_mappings[term_lower] = {"expansion": expansion}
        if self.dry_run:
            result["success"] = True
            result["message"] = "DRY RUN"
            return result
        # Try to persist to query_expansion.py
        persisted = self._persist_mapping(term_lower, expansion)
        result["persisted"] = persisted
        result["success"] = True
        result["message"] = "Persisted" if persisted else "In memory only"
        self._existing_abbreviations.add(term_lower)
        return result

    def search_and_learn(self, query: str, results: list[dict], cks_client=None) -> dict:
        response = {
            "query": query,
            "unknown_terms": [],
            "learned_mappings": [],
            "suggestions": [],
            "improved_query": query,
        }
        unknown_terms = self.detect_unknown_terms(query, results)
        response["unknown_terms"] = unknown_terms

        if unknown_terms:
            # Try to extract definitions from results and persist mappings
            for term in unknown_terms:
                definition = ""
                extraction_method = "regex"

                # Step 1: Try regex patterns first (fast)
                for result in results[:5]:
                    content = result.get("content", "")
                    if content:
                        definition = self.extract_definition(content, term)
                        if definition:
                            break

                # Step 2: Fallback to LLM extraction if regex didn't work
                if not definition:
                    contents = [r.get("content", "") for r in results[:5] if r.get("content")]
                    definition = self._extract_definition_with_llm_sync(term, contents)
                    extraction_method = "llm" if definition else "none"

                if definition:
                    # Add the mapping (will persist if not in dry_run mode)
                    confidence = 0.9 if extraction_method == "llm" else 0.7
                    add_result = self.add_mapping(
                        term,
                        definition,
                        source=f"auto_learned_{extraction_method}",
                        confidence=confidence,
                    )
                    response["learned_mappings"].append(
                        {
                            "term": term,
                            "definition": definition,
                            "persisted": add_result.get("persisted", False),
                            "message": add_result.get("message", ""),
                            "extraction_method": extraction_method,
                        }
                    )
                    response["suggestions"].append(f"Learned: {term} -> {definition}")
                else:
                    response["suggestions"].append(f"Unknown: {term} (no definition found)")
        else:
            response["suggestions"].append("No learning needed")

        return response

    def get_learned_mappings(self) -> dict[str, dict]:
        return self._learned_mappings.copy()

    def list_learned_terms(self) -> list[dict]:
        """List all learned terms with metadata.

        Returns:
            List of dicts with keys: term, expansion, confidence, source

        """
        return [
            {
                "term": term,
                "expansion": data.get("expansion", ""),
                "confidence": data.get("confidence", 0.5),
                "source": data.get("source", "unknown"),
            }
            for term, data in self._learned_mappings.items()
        ]

    def _remove_persisted_mapping(self, term: str) -> bool:
        """Remove a persisted mapping from query_expansion.py.

        Args:
            term: The term to remove (case-insensitive)

        Returns:
            True if successfully removed, False otherwise

        """
        if self.dry_run:
            return False

        # Determine the path to query_expansion.py
        if self.cks_path:
            expansion_file = self.cks_path / "query_expansion.py"
        else:
            try:
                import CKS

                expansion_file = Path(cks.__file__).parent / "query_expansion.py"
            except (ImportError, AttributeError):
                expansion_file = Path(__file__).parent.parent / "query_expansion.py"

        if not expansion_file.exists():
            logger.warning(f"query_expansion.py not found at {expansion_file}")
            return False

        try:
            with open(expansion_file, "r+", encoding="utf-8") as f, _FileLock(f):
                f.seek(0)
                content = f.read()

            # Pattern to match the term line: handles both "term": and 'term':
            # Matches lines like:        "hyde": "hypothetical document embeddings",
            term_pattern = re.compile(
                rf'(\s{{8,12}}["\']({re.escape(term)})["\']:\s*["\'][^"\']*["\'],?\s*\n)',
                re.IGNORECASE,
            )

            new_content = term_pattern.sub("", content)

            # Check if anything was actually removed
            if new_content == content:
                logger.debug(f"Term '{term}' not found in query_expansion.py")
                return False

            expansion_file.write_text(new_content, encoding="utf-8")
            logger.info(f"Removed persisted mapping: {term}")
            return True

        except Exception as e:
            logger.exception(f"Failed to remove persisted mapping: {e}")
            return False

    def remove_learned_term(self, term: str) -> bool:
        """Remove a learned term by its term name.

        Args:
            term: The term to remove (case-insensitive)

        Returns:
            True if term was found and removed, False otherwise

        """
        term_lower = term.lower()
        if term_lower in self._learned_mappings:
            del self._learned_mappings[term_lower]
            # Also remove from existing abbreviations if present
            if term_lower in self._existing_abbreviations:
                self._existing_abbreviations.remove(term_lower)
            # Remove from persisted storage if not in dry_run mode
            self._remove_persisted_mapping_ast(term_lower)
            return True
        return False

    def suggest_expansion(self, query: str) -> list[str]:
        return [query]


def auto_learn_from_search(
    query: str, results: list[dict], cks_client=None, dry_run: bool = False
) -> dict:
    expander = AutoLearningQueryExpander(dry_run=dry_run)
    return expander.search_and_learn(query, results, cks_client)
