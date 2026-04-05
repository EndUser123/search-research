"""
Entity Extraction Strategies

Three strategies with different confidence levels:
1. StructuralStrategy - Extracts from code blocks, backticks, file paths (95% confidence)
2. HeuristicStrategy - Pattern-based with extensive blocklist (70% confidence)  
3. SemanticStrategy - Embedding-based validation (85% confidence)

Blocklist derived from empirical analysis of false positives in assumption_audit logs.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Set

# =============================================================================
# BLOCKLIST - Derived from log analysis of false positive entities
# =============================================================================

# Words that appear as "uncovered entities" but are actually prose
# Organized by category for maintainability
BLOCKLIST_GENERIC_PROGRAMMING = frozenset({
    # Status/state words
    "status", "state", "current", "next", "previous", "before", "after",
    "complete", "completed", "pending", "done", "ready", "active", "inactive",
    "valid", "invalid", "enabled", "disabled", "available", "unavailable",

    # Action words
    "action", "fix", "fixed", "update", "updated", "create", "created",
    "delete", "deleted", "add", "added", "remove", "removed", "edit", "edited",
    "change", "changed", "changes", "modify", "modified", "write", "read",
    "start", "stop", "restart", "run", "running", "execute", "executed",

    # Analysis words
    "analysis", "verification", "validation", "check", "checked", "verify",
    "verified", "evidence", "finding", "findings", "result", "results",
    "summary", "recommendation", "conclusion", "assessment", "evaluation",

    # Structure words
    "step", "phase", "stage", "level", "layer", "component", "module",
    "section", "part", "block", "item", "element", "entry", "record",

    # Quality words
    "issue", "issues", "problem", "problems", "bug", "bugs", "error", "errors",
    "warning", "warnings", "critical", "high", "medium", "low", "severity",

    # Process words
    "implementation", "integration", "configuration", "setup", "install",
    "build", "deploy", "test", "testing", "debug", "debugging",

    # Documentation words
    "description", "documentation", "comment", "note", "notes", "reference",
    "example", "examples", "template", "pattern", "patterns", "design",
})

BLOCKLIST_GENERIC_NOUNS = frozenset({
    # Common objects
    "file", "files", "directory", "directories", "folder", "folders",
    "path", "paths", "name", "names", "value", "values", "key", "keys",
    "data", "content", "text", "string", "number", "list", "array",
    "object", "objects", "type", "types", "class", "classes", "function",
    "method", "methods", "variable", "variables", "parameter", "parameters",

    # System concepts
    "system", "service", "server", "client", "process", "thread", "task",
    "job", "queue", "cache", "memory", "storage", "database", "table",

    # Abstract concepts
    "logic", "behavior", "flow", "sequence", "order", "format", "structure",
    "context", "scope", "range", "limit", "threshold", "timeout", "interval",
})

BLOCKLIST_VERBS_ADJECTIVES = frozenset({
    # Common verbs (often caught by pattern matching)
    "get", "set", "put", "post", "fetch", "load", "save", "store",
    "find", "search", "filter", "sort", "map", "reduce", "transform",
    "parse", "format", "convert", "encode", "decode", "serialize",
    "init", "initialize", "setup", "cleanup", "reset", "clear",
    "open", "close", "connect", "disconnect", "send", "receive",
    "handle", "process", "validate", "sanitize", "normalize",

    # Adjectives
    "new", "old", "first", "last", "final", "initial", "default",
    "required", "optional", "mandatory", "specific", "general",
    "actual", "expected", "original", "modified", "custom",
    "manual", "auto", "automatic", "dynamic", "static",
    "local", "remote", "internal", "external", "public", "private",
})

BLOCKLIST_DISCOURSE = frozenset({
    # Pronouns and articles (should be filtered but double-check)
    "the", "a", "an", "this", "that", "these", "those", "it", "its",
    "you", "your", "we", "our", "they", "their", "i", "my",

    # Conjunctions and prepositions
    "and", "or", "but", "if", "then", "else", "when", "where", "how",
    "what", "which", "who", "why", "for", "from", "to", "in", "on",
    "at", "by", "with", "about", "into", "through", "during", "after",

    # Discourse markers
    "also", "already", "both", "each", "every", "all", "any", "some",
    "none", "other", "another", "same", "different", "various",
    "however", "therefore", "because", "since", "although", "unless",

    # Qualifiers
    "yes", "no", "true", "false", "null", "undefined",
    "maybe", "perhaps", "probably", "possibly", "likely", "unlikely",
})

BLOCKLIST_HOOK_SPECIFIC = frozenset({
    # Terms common in assumption audit context but not entities
    "claim", "claims", "entity", "entities", "coverage", "overlap",
    "scope", "evidence", "tool", "tools", "output", "outputs",
    "response", "request", "message", "prompt", "query",

    # Hook lifecycle terms
    "pretooluse", "posttooluse", "sessionstart", "sessionend", "stop",
    "hook", "hooks", "validator", "validators", "gate", "gates",

    # CSF-specific terms that appear in prose
    "constitutional", "framework", "csf", "cks", "rca", "tdd",
    "tier", "confidence", "reversibility", "decision", "matrix",

    # Additional false positives from log analysis
    "checkpoint", "daemon", "python", "answer", "root", "statement",
    "cause", "pipe", "discovery", "signal", "severity", "critical",
    "component", "protocol", "phase", "execution", "halt", "halted",
    "recommendation", "findings", "variable", "import", "command",
    "json", "pid", "numpy", "sequential", "details",
    "restore", "restoration", "progress", "tracking", "pending",
    "stale", "fallback", "disable", "restart", "precompact",
})

# Combined blocklist
ENTITY_BLOCKLIST = (
    BLOCKLIST_GENERIC_PROGRAMMING |
    BLOCKLIST_GENERIC_NOUNS |
    BLOCKLIST_VERBS_ADJECTIVES |
    BLOCKLIST_DISCOURSE |
    BLOCKLIST_HOOK_SPECIFIC
)

# Minimum entity length (avoid single letters, abbreviations)
MIN_ENTITY_LENGTH = 3

# Maximum entity length (avoid capturing whole sentences)
MAX_ENTITY_LENGTH = 100


# =============================================================================
# STRATEGY BASE CLASS
# =============================================================================

class ExtractionStrategy(ABC):
    """Base class for extraction strategies."""

    @abstractmethod
    def extract(self, text: str) -> Set[str]:
        """Extract entities from text."""
        pass

    def _passes_length_check(self, entity: str) -> bool:
        """Check if entity passes length requirements."""
        return MIN_ENTITY_LENGTH <= len(entity) <= MAX_ENTITY_LENGTH


# =============================================================================
# STRUCTURAL STRATEGY - Highest confidence (95%)
# =============================================================================

class StructuralStrategy(ExtractionStrategy):
    """
    Extract entities from structural code indicators.
    
    High confidence because these are explicitly marked as code:
    - Backtick-wrapped: `entity_name`
    - File paths: /path/to/file.py, C:\\path\\file.py
    - Import statements: from module import entity
    - Explicit code blocks with identifiable entities
    """

    # Patterns for structural extraction
    PATTERNS = {
        # Backtick-wrapped (inline code) - highest signal
        'backtick': re.compile(r'`([^`]+)`'),

        # File paths - Windows and Unix
        'path_windows': re.compile(r'[A-Za-z]:[/\\][\w./\\-]+\.[\w]+'),
        'path_unix': re.compile(r'(?<!\w)/(?:[\w-]+/)+[\w.-]+\.[\w]+'),
        'path_relative': re.compile(r'\.{1,2}/[\w./\\-]+\.[\w]+'),

        # Import statements
        'import_from': re.compile(r'from\s+([\w.]+)\s+import\s+([\w,\s]+)'),
        'import_direct': re.compile(r'^import\s+([\w.]+)', re.MULTILINE),

        # Function definitions
        'def_function': re.compile(r'def\s+(\w+)\s*\('),
        'def_class': re.compile(r'class\s+(\w+)\s*[:\(]'),
    }

    def extract(self, text: str) -> Set[str]:
        """Extract structurally-indicated entities."""
        entities = set()

        if not text:
            return entities

        # Backtick content (most reliable)
        for match in self.PATTERNS['backtick'].finditer(text):
            content = match.group(1).strip()
            # Filter out prose in backticks (sentences, long text)
            if self._is_code_content(content):
                entities.add(content)

        # File paths
        for pattern_name in ['path_windows', 'path_unix', 'path_relative']:
            for match in self.PATTERNS[pattern_name].finditer(text):
                path = match.group(0)
                entities.add(path)
                # Also add just filename
                filename = path.replace('\\', '/').rsplit('/', 1)[-1]
                if self._passes_length_check(filename):
                    entities.add(filename)

        # Imports (only from code blocks)
        code_blocks = self._extract_code_blocks(text)
        for block in code_blocks:
            for match in self.PATTERNS['import_from'].finditer(block):
                module = match.group(1)
                imports = match.group(2)
                entities.add(module)
                for imp in imports.split(','):
                    imp = imp.strip()
                    if self._passes_length_check(imp):
                        entities.add(imp)

            for match in self.PATTERNS['import_direct'].finditer(block):
                entities.add(match.group(1))

            # Function/class definitions
            for match in self.PATTERNS['def_function'].finditer(block):
                entities.add(match.group(1))
            for match in self.PATTERNS['def_class'].finditer(block):
                entities.add(match.group(1))

        return {e for e in entities if self._passes_length_check(e)}

    def _is_code_content(self, content: str) -> bool:
        """Check if backtick content looks like code vs prose."""
        # Too long = probably prose
        if len(content) > 60:
            return False

        # Contains spaces but no code indicators = probably prose
        if ' ' in content:
            code_indicators = ['.', '_', '(', ')', '/', '\\', '=', '->', '::', '[', ']']
            if not any(ind in content for ind in code_indicators):
                return False

        return True

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract fenced code blocks from text."""
        pattern = re.compile(r'```[\w]*\n(.*?)```', re.DOTALL)
        return pattern.findall(text)


# =============================================================================
# HEURISTIC STRATEGY - Medium confidence (70%)
# =============================================================================

class HeuristicStrategy(ExtractionStrategy):
    """
    Pattern-based entity extraction with context validation.
    
    Extracts:
    - snake_case identifiers (with context validation)
    - PascalCase identifiers (with context validation)  
    - CONSTANT_CASE identifiers
    - Filenames with extensions
    
    Filters:
    - Extensive blocklist of common prose words
    - Context validation (must appear in code-like context)
    - Length requirements
    """

    # Patterns with word boundaries
    PATTERNS = {
        # snake_case: must have underscore, not just lowercase
        'snake_case': re.compile(r'\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b'),

        # PascalCase: capital followed by mixed case, min 2 capitals
        'pascal_case': re.compile(r'\b([A-Z][a-z]+(?:[A-Z][a-z0-9]*)+)\b'),

        # CONSTANT_CASE: all caps with underscores
        'constant_case': re.compile(r'\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b'),

        # Filenames with common extensions
        'filename': re.compile(r'\b([\w-]+\.(?:py|js|ts|json|yaml|yml|md|txt|sh|ps1|sql|html|css|jsx|tsx|toml|cfg|ini|env))\b', re.IGNORECASE),

        # Module paths: module.submodule.item
        'module_path': re.compile(r'\b([\w]+(?:\.[\w]+){2,})\b'),
    }

    # Context patterns that indicate code context (increases confidence)
    CODE_CONTEXT_PATTERNS = [
        r'`[^`]*{entity}[^`]*`',           # In backticks
        r'```[^`]*{entity}[^`]*```',       # In code block
        r'\b(?:import|from)\s+.*{entity}', # Import context
        r'{entity}\s*\(',                   # Function call
        r'{entity}\s*=',                    # Assignment
        r'def\s+{entity}',                  # Function definition
        r'class\s+{entity}',                # Class definition
        r'\[\s*["\']?{entity}["\']?\s*\]', # Dict/array access
    ]

    def __init__(self):
        self._blocklist = ENTITY_BLOCKLIST

    def extract(self, text: str) -> Set[str]:
        """Extract entities using heuristic patterns."""
        candidates = set()

        if not text:
            return candidates

        # Extract using each pattern
        for pattern_name, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                entity = match.group(1)
                if self._passes_length_check(entity):
                    candidates.add(entity)

        # Filter by context (optional boost, not requirement)
        # For now, just return candidates - filtering done in extractor
        return candidates

    def is_blocked(self, entity: str) -> bool:
        """Check if entity is in blocklist."""
        normalized = entity.lower().strip()

        # Direct blocklist check
        if normalized in self._blocklist:
            return True

        # Check if it's a common word with suffix
        # e.g., "testing" -> "test" in blocklist
        if normalized.endswith('ing') and normalized[:-3] in self._blocklist:
            return True
        if normalized.endswith('ed') and normalized[:-2] in self._blocklist:
            return True
        if normalized.endswith('s') and normalized[:-1] in self._blocklist:
            return True

        return False

    def has_code_context(self, entity: str, text: str) -> bool:
        """Check if entity appears in a code-like context."""
        for pattern_template in self.CODE_CONTEXT_PATTERNS:
            pattern = pattern_template.format(entity=re.escape(entity))
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True
        return False


# =============================================================================
# SEMANTIC STRATEGY - Validated confidence (85%)
# =============================================================================

class SemanticStrategy(ExtractionStrategy):
    """
    Embedding-based entity validation.
    
    Uses sentence-transformers to:
    1. Embed candidate entities
    2. Compare to code-entity vs prose-word centroids
    3. Classify based on similarity threshold
    
    Optional: Falls back gracefully if sentence-transformers unavailable.
    
    Model: all-MiniLM-L6-v2 (22M params, fast inference)
    """

    # Reference examples for centroid calculation
    CODE_ENTITY_EXAMPLES = [
        "process_data", "UserController", "API_KEY", "config.yaml",
        "test_authentication", "DatabaseConnection", "MAX_RETRIES",
        "utils.py", "handle_request", "ValidationError", "HTTP_STATUS",
        "parse_json", "EventHandler", "DEFAULT_TIMEOUT", "schema.sql",
        "calculate_total", "RequestManager", "ENV_PRODUCTION",
    ]

    PROSE_WORD_EXAMPLES = [
        "current", "status", "evidence", "verification", "summary",
        "problem", "issue", "action", "step", "phase", "complete",
        "fixed", "updated", "created", "result", "finding", "next",
        "implementation", "integration", "recommendation", "assessment",
        "analysis", "conclusion", "component", "section", "level",
    ]

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.1):
        """
        Initialize semantic strategy.
        
        Args:
            model_name: Sentence-transformers model
            threshold: Similarity difference threshold for classification
                       Lower = more permissive (catches more code entities)
                       0.1 = balanced, catches PascalCase and filenames
                       0.3 = strict, mainly snake_case functions
        """
        self._model_name = model_name
        self._threshold = threshold
        self._model = None
        self._code_centroid = None
        self._prose_centroid = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of model and centroids."""
        if self._initialized:
            return

        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)

            # Calculate centroids
            code_embeddings = self._model.encode(self.CODE_ENTITY_EXAMPLES)
            prose_embeddings = self._model.encode(self.PROSE_WORD_EXAMPLES)

            self._code_centroid = np.mean(code_embeddings, axis=0)
            self._prose_centroid = np.mean(prose_embeddings, axis=0)

            self._initialized = True

        except ImportError:
            raise ImportError(
                "sentence-transformers required for semantic validation. "
                "Install with: pip install sentence-transformers"
            )

    def extract(self, text: str) -> Set[str]:
        """
        Semantic strategy doesn't extract - it validates.
        
        Use validate() instead.
        """
        return set()

    def validate(self, candidates: List[str], context: str = "") -> Set[str]:
        """
        Validate candidate entities using semantic similarity.
        
        Args:
            candidates: List of candidate entity strings
            context: Original text context (unused currently, for future)
            
        Returns:
            Set of validated entities (likely code entities)
        """
        if not candidates:
            return set()

        self._initialize()


        validated = set()

        # Embed candidates
        candidate_embeddings = self._model.encode(candidates)

        for i, candidate in enumerate(candidates):
            embedding = candidate_embeddings[i]

            # Calculate cosine similarity to centroids
            code_sim = self._cosine_similarity(embedding, self._code_centroid)
            prose_sim = self._cosine_similarity(embedding, self._prose_centroid)

            # Classify based on relative similarity
            # Positive difference = more like code entity
            diff = code_sim - prose_sim

            if diff > self._threshold:
                validated.add(candidate)

        return validated

    def _cosine_similarity(self, a, b) -> float:
        """Calculate cosine similarity between vectors."""
        import numpy as np
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def classify_single(self, entity: str) -> dict:
        """
        Classify a single entity with detailed scores.
        
        Returns dict with code_sim, prose_sim, diff, is_code_entity.
        Useful for debugging and threshold tuning.
        """
        self._initialize()

        embedding = self._model.encode([entity])[0]
        code_sim = self._cosine_similarity(embedding, self._code_centroid)
        prose_sim = self._cosine_similarity(embedding, self._prose_centroid)
        diff = code_sim - prose_sim

        return {
            'entity': entity,
            'code_similarity': float(code_sim),
            'prose_similarity': float(prose_sim),
            'difference': float(diff),
            'is_code_entity': diff > self._threshold,
            'threshold': self._threshold,
        }
