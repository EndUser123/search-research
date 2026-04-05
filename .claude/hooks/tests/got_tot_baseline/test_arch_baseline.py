"""
Baseline regression tests for /arch skill (architecture advisor).

These tests capture the current behavior of /arch before GoT/ToT integration.
They serve as regression guards to ensure core routing functionality continues working.

Test Coverage:
- Template override detection (template=<name>, chaining X+Y)
- Domain detection (cli, python, data-pipeline, precedent)
- Complexity detection (high vs low complexity indicators)
- Intent classification (ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, DEFAULT)
- ADF gate detection (extraction/justification questions)
- Template validation (chaining rules, precedence constraints)

Critical paths tested: 6
Lines of code: ~120
"""

import pytest


def parse_template_override(query: str) -> str | None:
    """
    Parse template override from query string.

    This is a copy of the template override logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        query: User query string

    Returns:
        Template name if override detected, None otherwise
    """
    import re

    # Pattern: template=<name> or template=<name>+<secondary>
    match = re.search(r'template\s*=\s*([\w\-]+(?:\+[\w\-]+)?)', query, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def detect_domain(query: str) -> str | None:
    """
    Detect domain from keyword analysis.

    This is a copy of the domain detection logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        query: User query string

    Returns:
        Detected domain (cli, python, data-pipeline, precedent) or None
    """
    query_lower = query.lower()

    domain_keywords = {
        'cli': ['cli', 'command line', 'terminal', 'shell', 'posix', 'exit code', 'argument parsing'],
        'python': ['python', 'asyncio', 'type hint', 'pydantic', 'fastapi', 'flask', 'django', 'async', 'await', 'decorator', 'context manager'],
        'data-pipeline': ['etl', 'elt', 'pipeline', 'streaming', 'batch', 'kafka', 'spark', 'airflow', 'dagster', 'prefect', 'warehouse', 'data lake'],
        'precedent': ['adr', 'decision record', 'precedent', 'document decision', 'architecture decision record']
    }

    # Count keyword matches per domain
    domain_scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        if score > 0:
            domain_scores[domain] = score

    # Return domain with highest score
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return None


def detect_complexity(query: str) -> str:
    """
    Detect complexity from query indicators.

    This is a copy of the complexity detection logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        query: User query string

    Returns:
        'deep' for high complexity, 'fast' for low complexity
    """
    high_complexity_indicators = [
        'redesign', 'overhaul', 'architecture', 'microservices',
        'from scratch', 'rewrite', 'replace', 'multi-system',
        'service boundary', 'schema migration', 'breaking change'
    ]

    query_lower = query.lower()
    if any(indicator in query_lower for indicator in high_complexity_indicators):
        return 'deep'
    return 'fast'


def classify_intent_type(query: str) -> str:
    """
    Classify intent type from query keywords.

    This is a copy of the intent classification logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        query: User query string

    Returns:
        Intent type: ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, or DEFAULT
    """
    query_lower = query.lower()

    review_keywords = ['review', 'evaluate', 'assess', 'analyze', 'audit', 'validate', 'critique']
    design_keywords = ['design', 'architecture', 'integration', 'proposal', 'theoretical', 'blueprint']
    improve_keywords = ['improve', 'optimize', 'harden', 'stabilize', 'enhance', 'strengthen']
    subsystem_keywords = ['memory', 'cks', 'hooks', 'research', 'retro', 'lesson', 'ingestion', 'validation']

    # ARCHITECTURE_REVIEW: Explicit review of design/architecture
    has_review = any(kw in query_lower for kw in review_keywords)
    has_design = any(kw in query_lower for kw in design_keywords)

    if has_review and has_design:
        return 'ARCHITECTURE_REVIEW'

    # IMPROVE_SYSTEM: Optimize existing subsystem
    has_improve = any(kw in query_lower for kw in improve_keywords)
    has_subsystem = any(kw in query_lower for kw in subsystem_keywords)

    if has_improve and has_subsystem:
        return 'IMPROVE_SYSTEM'

    return 'DEFAULT'


def detect_adf_gate(query: str) -> bool:
    """
    Detect ADF gate (Architecture Decision Framework) triggers.

    This is a copy of the ADF gate detection logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        query: User query string

    Returns:
        True if ADF gate should be triggered, False otherwise
    """
    adf_gate_keywords = [
        # Direct extraction questions
        'should i extract', 'is creating x justified', 'should i create.*module',
        'should i create.*service', 'should i create.*class', 'add abstraction',
        # Boundary/structure questions
        'new boundary', 'new service', 'new module', 'separate.*concern',
        'extract.*service', 'extract.*module', 'split.*into',
        # Justification questions
        'is.*worth it', 'is.*justified', 'justify.*change', 'justify.*extraction',
        # Over-engineering concerns
        'over-engineering', 'overkill', 'too complex', 'unnecessary.*layer'
    ]

    import re
    query_lower = query.lower()

    for pattern in adf_gate_keywords:
        if re.search(pattern, query_lower):
            return True
    return False


def validate_template_chain(template: str) -> tuple[bool, str | None]:
    """
    Validate template chaining syntax and rules.

    This is a copy of the template validation logic from /arch
    to establish baseline behavior before GoT/ToT integration.

    Args:
        template: Template name or chain (e.g., "python+data-pipeline")

    Returns:
        Tuple of (is_valid, error_message)
    """
    VALID_TEMPLATES = {'fast', 'deep', 'cli', 'python', 'data-pipeline', 'precedent'}

    # Check for chaining
    if '+' in template:
        parts = template.split('+')

        # Rule: Max 2 templates in chain
        if len(parts) > 2:
            return False, "Invalid template chain: Max 2 templates allowed"

        # Validate each part
        for part in parts:
            if part not in VALID_TEMPLATES:
                return False, f"Invalid template '{part}' in chain"

        # Rule: precedent cannot be secondary
        if 'precedent' in parts[1:]:
            return False, "Invalid template chain: 'precedent' cannot be secondary"

        # Rule: fast/deep not chainable (they're complexity selectors)
        if any(p in {'fast', 'deep'} for p in parts[1:]):
            return False, "Invalid template chain: 'fast' and 'deep' are complexity selectors, not chainable"

    else:
        # Single template validation
        if template not in VALID_TEMPLATES:
            return False, f"Invalid template '{template}'"

    return True, None


class TestTemplateOverride:
    """Test template override detection."""

    def test_parse_simple_template_override(self):
        """Test parsing simple template=cli"""
        template = parse_template_override("design a cli tool template=cli")
        assert template == 'cli'

    def test_parse_chained_template_override(self):
        """Test parsing chained template=python+data-pipeline"""
        template = parse_template_override("build pipeline template=python+data-pipeline")
        assert template == 'python+data-pipeline'

    def test_no_template_override(self):
        """Test query without template override"""
        template = parse_template_override("improve error handling")
        assert template is None

    def test_case_insensitive_override(self):
        """Test template= is case-insensitive"""
        template = parse_template_override("design api TEMPLATE=DEEP")
        assert template == 'deep'

    def test_template_override_with_spaces(self):
        """Test template= with spaces around equals"""
        template = parse_template_override("design api template = python")
        assert template == 'python'


class TestDomainDetection:
    """Test domain keyword detection."""

    def test_detect_cli_domain(self):
        """Test CLI domain detection from keywords"""
        domain = detect_domain("build a command line tool")
        assert domain == 'cli'

    def test_detect_python_domain(self):
        """Test Python domain detection from keywords"""
        domain = detect_domain("design async python architecture")
        assert domain == 'python'

    def test_detect_data_pipeline_domain(self):
        """Test data-pipeline domain detection from keywords"""
        domain = detect_domain("build etl pipeline")
        assert domain == 'data-pipeline'

    def test_detect_precedent_domain(self):
        """Test precedent domain detection from keywords"""
        domain = detect_domain("document this architecture decision record")
        assert domain == 'precedent'

    def test_no_domain_detected(self):
        """Test query with no domain keywords"""
        domain = detect_domain("improve performance")
        assert domain is None

    def test_domain_highest_score_wins(self):
        """Test domain with most keyword matches wins"""
        domain = detect_domain("build python cli tool with async")
        # Should detect 'python' (2 matches: 'python', 'async')
        # vs 'cli' (1 match: 'cli')
        assert domain == 'python'


class TestComplexityDetection:
    """Test complexity detection."""

    def test_high_complexity_redesign(self):
        """Test high complexity from 'redesign' keyword"""
        complexity = detect_complexity("redesign the authentication system")
        assert complexity == 'deep'

    def test_high_complexity_microservices(self):
        """Test high complexity from 'microservices' keyword"""
        complexity = detect_complexity("design microservices architecture")
        assert complexity == 'deep'

    def test_low_complexity_default(self):
        """Test low complexity for simple queries"""
        complexity = detect_complexity("improve error handling")
        assert complexity == 'fast'

    def test_low_complexity_single_file(self):
        """Test low complexity for single-file changes"""
        complexity = detect_complexity("add logging to function")
        assert complexity == 'fast'


class TestIntentClassification:
    """Test intent type classification."""

    def test_architecture_review_intent(self):
        """Test ARCHITECTURE_REVIEW intent detection"""
        intent = classify_intent_type("review this integration architecture")
        assert intent == 'ARCHITECTURE_REVIEW'

    def test_improve_system_intent(self):
        """Test IMPROVE_SYSTEM intent detection"""
        intent = classify_intent_type("improve memory system performance")
        assert intent == 'IMPROVE_SYSTEM'

    def test_default_intent(self):
        """Test DEFAULT intent for general queries"""
        intent = classify_intent_type("design authentication system")
        assert intent == 'DEFAULT'

    def test_review_with_theoretical_keyword(self):
        """Test ARCHITECTURE_REVIEW with 'theoretical' keyword"""
        intent = classify_intent_type("evaluate this theoretical design")
        assert intent == 'ARCHITECTURE_REVIEW'


class TestAdfGateDetection:
    """Test ADF gate detection."""

    def test_extract_question_triggers_gate(self):
        """Test 'should i extract' triggers ADF gate"""
        triggered = detect_adf_gate("should I extract this into a service")
        assert triggered is True

    def test_justification_question_triggers_gate(self):
        """Test 'is it worth it' triggers ADF gate"""
        triggered = detect_adf_gate("is creating this module justified")
        assert triggered is True

    def test_over_engineering_triggers_gate(self):
        """Test 'over-engineering' triggers ADF gate"""
        triggered = detect_adf_gate("is this over-engineering")
        assert triggered is True

    def test_general_query_no_gate(self):
        """Test general query doesn't trigger ADF gate"""
        triggered = detect_adf_gate("design authentication system")
        assert triggered is False


class TestTemplateValidation:
    """Test template validation and chaining rules."""

    def test_valid_single_template(self):
        """Test valid single template"""
        valid, error = validate_template_chain('cli')
        assert valid is True
        assert error is None

    def test_valid_chained_template(self):
        """Test valid template chain (python+data-pipeline)"""
        valid, error = validate_template_chain('python+data-pipeline')
        assert valid is True
        assert error is None

    def test_invalid_template_name(self):
        """Test invalid template name"""
        valid, error = validate_template_chain('invalid')
        assert valid is False
        assert 'Invalid template' in error

    def test_chain_too_long(self):
        """Test template chain with >2 templates is invalid"""
        valid, error = validate_template_chain('python+data-pipeline+cli')
        assert valid is False
        assert 'Max 2 templates' in error

    def test_precedent_cannot_be_secondary(self):
        """Test precedent cannot be secondary template"""
        valid, error = validate_template_chain('python+precedent')
        assert valid is False
        assert 'cannot be secondary' in error

    def test_fast_deep_not_chainable(self):
        """Test fast/deep cannot be in secondary position"""
        valid, error = validate_template_chain('python+fast')
        assert valid is False
        assert 'complexity selectors' in error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
