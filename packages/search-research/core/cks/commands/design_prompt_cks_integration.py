#!/usr/bin/env python3
"""Design for Prompt-Based CKS Integration.

Extends CKS to store and retrieve prompt-based standards alongside executable rules,
enabling LLM-driven enforcement of the full 192 Python 2025 standards.
"""


def create_enhanced_cks_schema() -> str:
    """Create enhanced CKS schema to support prompt-based standards."""
    return """
    -- Add prompt-based standards support
    ALTER TABLE standards ADD COLUMN prompt_template TEXT;
    ALTER TABLE standards ADD COLUMN enforcement_type TEXT DEFAULT 'executable';
    ALTER TABLE standards ADD COLUMN context_keywords TEXT;
    ALTER TABLE standards ADD COLUMN severity_weights TEXT;

    -- Create new table for prompt contexts
    CREATE TABLE IF NOT EXISTS prompt_contexts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id TEXT NOT NULL,
        context_type TEXT NOT NULL,  -- 'function', 'class', 'module', 'import', etc.
        pattern TEXT NOT NULL,        -- regex or keyword pattern
        application_logic TEXT,       -- how to apply in this context
        FOREIGN KEY (rule_id) REFERENCES standards(rule_id)
    );

    -- Create index for prompt retrieval
    CREATE INDEX IF NOT EXISTS idx_standards_prompt ON standards(enforcement_type);
    CREATE INDEX IF NOT EXISTS idx_prompt_contexts_type ON prompt_contexts(context_type);
    """


def store_prompt_standards_in_cks():
    """Store the 192 Python 2025 prompt-based standards in CKS."""
    return [
        # Dependency Management Prompts
        {
            "rule_id": "PY2025_PROMPT_UV001",
            "title": "Use uv for dependency management",
            "prompt_template": """
When reviewing Python code for dependency management:
1. Check if the project uses uv instead of pip/poetry
2. Look for pyproject.toml with [tool.uv] configuration
3. Verify uv.lock file exists and is committed
4. Ensure dependencies are managed via uv add/remove commands
5. Check for legacy requirements.txt usage and recommend migration
Guidance: "Modern Python projects should use uv for lightning-fast dependency resolution and unified Python version management."
            """,
            "enforcement_type": "prompt",
            "context_keywords": "dependency,package,install,import,requirements",
            "severity_weights": "high",
        },
        # Code Quality Prompts
        {
            "rule_id": "PY2025_PROMPT_RUFF001",
            "title": "Use ruff for linting and formatting",
            "prompt_template": """
When reviewing Python code quality:
1. Check if ruff is configured in pyproject.toml [tool.ruff] section
2. Verify ruff format is used instead of black/isort
3. Look for comprehensive ruff rule selection (E, F, W, B, C, etc.)
4. Check for ruff integration in CI/CD pipelines
5. Ensure no overlapping linting tools (flake8, pylint, etc.)
Guidance: "Ruff provides 10-100x faster linting and replaces multiple legacy tools in a single pass."
            """,
            "enforcement_type": "prompt",
            "context_keywords": "format,style,lint,quality,code",
            "severity_weights": "high",
        },
        # Async Programming Prompts
        {
            "rule_id": "PY2025_PROMPT_ASYNC001",
            "title": "Modern async programming patterns",
            "prompt_template": """
When reviewing async Python code:
1. Use asyncio.run() instead of manual event loop management
2. Prefer asyncio.create_task() for concurrent execution
3. Use async with for resource management
4. Avoid blocking operations (time.sleep, requests.get) in async functions
5. Use asyncio.gather() for concurrent independent operations
6. Implement proper timeouts with asyncio.wait_for()
Guidance: "Modern async patterns prevent race conditions, improve performance, and ensure proper resource cleanup."
            """,
            "enforcement_type": "prompt",
            "context_keywords": "async,await,coroutine,concurrency",
            "severity_weights": "medium",
        },
        # Type Safety Prompts
        {
            "rule_id": "PY2025_PROMPT_TYPE001",
            "title": "Modern Python type annotations",
            "prompt_template": """
When reviewing Python type annotations:
1. Use modern syntax (list[int] vs List[int]) for Python 3.9+
2. Type all public functions and methods with proper return types
3. Use Union[str, None] over Optional[str] for clarity
4. Apply Protocol for structural typing when appropriate
5. Use TypedDict for structured dictionaries instead of dict[str, Any]
6. Type async functions with Coroutine return types
7. Use cast() for complex type assertions, not type comments
Guidance: "Comprehensive typing improves code documentation, IDE support, and runtime safety."
            """,
            "enforcement_type": "prompt",
            "context_keywords": "type,annotation,typing,hint",
            "severity_weights": "medium",
        },
    ]


def create_cks_prompt_retrieval_system() -> str:
    """Design CKS integration for LLM prompt-based enforcement."""
    return """
    class CKSPromptRetriever:
        def __init__(self, db_path):
            self.db_path = db_path

        def get_prompt_standards(self, code_context: Dict[str, Any]) -> List[Dict]:
            '''Retrieve relevant prompt standards based on code context.'''

            # Analyze code context
            context_type = self.analyze_code_context(code_context)
            keywords = self.extract_keywords(code_context)

            # Query CKS for relevant prompt standards
            standards = self.query_prompt_standards(context_type, keywords)

            # Sort by relevance and severity
            return self.rank_standards(standards, code_context)

        def analyze_code_context(self, code_context: Dict[str, Any]) -> str:
            '''Analyze what type of code is being reviewed.'''
            # Function definition
            if code_context.get('is_function'):
                return 'function'
            # Class definition
            elif code_context.get('is_class'):
                return 'class'
            # Import statements
            elif code_context.get('has_imports'):
                return 'import'
            # Module level
            else:
                return 'module'

        def extract_keywords(self, code_context: Dict[str, Any]) -> List[str]:
            '''Extract relevant keywords from code context.'''
            return code_context.get('keywords', [])

        def query_prompt_standards(self, context_type: str, keywords: List[str]) -> List[Dict]:
            '''Query CKS database for relevant prompt standards.'''

            query = '''
            SELECT s.rule_id, s.title, s.prompt_template, s.context_keywords, s.severity_weights
            FROM standards s
            WHERE s.enforcement_type = 'prompt'
            AND s.language = 'python'
            ORDER BY CASE
                WHEN s.context_keywords LIKE ? THEN 1
                WHEN s.context_keywords LIKE ? THEN 2
                ELSE 3
            END
            '''

            # Search for matching keywords
            results = []
            for keyword in keywords[:3]:  # Limit search
                # Database query implementation here
                pass

            return results

        def rank_standards(self, standards: List[Dict], code_context: Dict[str, Any]) -> List[Dict]:
            '''Rank standards by relevance and severity.'''

            def relevance_score(standard: Dict, context: Dict) -> float:
                score = 0.0

                # Context matching
                if standard['context_type'] == context.get('type'):
                    score += 2.0

                # Keyword matching
                keywords = context.get('keywords', [])
                for keyword in keywords:
                    if keyword in standard['context_keywords']:
                        score += 1.0

                # Severity weighting
                if standard['severity_weights'] == 'high':
                    score += 1.5
                elif standard['severity_weights'] == 'medium':
                    score += 1.0

                return score

            # Sort by relevance score
            return sorted(standards, key=lambda s: relevance_score(s, code_context), reverse=True)
    """


def design_llm_integration_pattern() -> str:
    """Design how LLM integrates with CKS prompt standards."""
    return """
    # LLM Code Review with CKS Prompt Integration

    def review_python_code_with_cks(code_content: str, file_path: str):

        # 1. Analyze code context
        code_context = analyze_code_context(code_content, file_path)

        # 2. Retrieve relevant prompt standards from CKS
        prompt_retriever = CKSPromptRetriever(standards_knowledge.db)
        relevant_standards = prompt_retriever.get_prompt_standards(code_context)

        # 3. Build comprehensive review prompt
        review_prompt = build_review_prompt(code_content, relevant_standards)

        # 4. LLM analysis with retrieved standards
        analysis = llm_analyze_code(review_prompt)

        # 5. Apply executable rules where available
        executable_violations = run_executable_rules(code_content, relevant_standards)

        # 6. Combine results
        return combine_analysis_results(analysis, executable_violations, relevant_standards)

    def build_review_prompt(code_content: str, standards: List[Dict]) -> str:

        prompt = f\"\"\"
        Please review this Python code based on the following Python 2025 standards:

        CODE TO REVIEW:
        ```python
        {code_content}
        ```

        STANDARDS TO APPLY:
        \"\"\"

        for standard in standards[:10]:  # Limit to prevent prompt overflow
            prompt += f\"\"\"

        ### {standard['title']} ({standard['rule_id']})
        {standard['prompt_template']}

        \"\"\"

        prompt += \"\"\"

        Review Instructions:
        1. Apply each standard systematically to the code
        2. Identify violations and suggest improvements
        3. Prioritize issues by severity (high > medium > low)
        4. Provide specific code examples for fixes
        5. Focus on Python 2025 modern practices

        Format your response as:
        ## Violations Found
        - [HIGH/MEDIUM/LOW] Standard: [Standard ID]
          Issue: [description]
          Fix: [specific code change]

        ## Recommendations
        [improvement suggestions]
        \"\"\"

        return prompt
    """


def main() -> None:
    """Main design documentation."""
    print("=" * 60)
    print("CKS Prompt-Based Standards Integration Design")
    print("=" * 60)

    print("\n1. ENHANCED CKS SCHEMA:")
    print(schema_sql := create_enhanced_cks_schema())

    print("\n2. PROMPT STANDARDS SAMPLE:")
    standards = store_prompt_standards_in_cks()
    for i, standard in enumerate(standards[:2], 1):
        print(f"\nStandard {i}: {standard['rule_id']}")
        print(f"Title: {standard['title']}")
        print(f"Enforcement: {standard['enforcement_type']}")
        print(f"Keywords: {standard['context_keywords']}")
        print(f"Preview: {standard['prompt_template'][:100]}...")

    print("\n3. RETRIEVAL SYSTEM:")
    print(retrieval_system := create_cks_prompt_retrieval_system())

    print("\n4. LLM INTEGRATION PATTERN:")
    print(integration_pattern := design_llm_integration_pattern())

    print("\n" + "=" * 60)
    print("Design Complete - Ready for Implementation")
    print("=" * 60)


if __name__ == "__main__":
    main()
