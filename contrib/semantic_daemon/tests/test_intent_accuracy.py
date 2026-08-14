"""Tests for intent classification accuracy against golden corpus.

Feature: Intent classification via semantic daemon
- SemanticClient.classify_intent(prompt) returns expected intent
- Golden corpus with 30 prompts covering all 11 intent categories
- Tests accuracy of classification against expected labels

Run with: pytest tests/daemons/test_intent_accuracy.py -v

RED Phase: This test is EXPECTED TO FAIL until classify_intent() is implemented
on SemanticClient.
"""

from __future__ import annotations

# Add src to path for imports
import sys
from pathlib import Path
from typing import Literal

import pytest

_csf_root = Path(__file__).parent.parent.parent
if str(_csf_root) not in sys.path:
    sys.path.insert(0, str(_csf_root))


IntentCategory = Literal[
    "search",
    "read",
    "write",
    "analyze",
    "research",
    "code",
    "test",
    "git",
    "web",
    "existence_claim",
    "other",
]


# Golden corpus with 30 representative prompts covering all 11 intent categories
GOLDEN_CORPUS = [
    # search - Finding, locating, querying
    ("search for memory about async patterns", "search"),
    ("find the bug in this function", "search"),
    ("where is the config file", "search"),
    ("locate the test module", "search"),
    # read - Viewing, inspecting, examining
    ("read the file at src/main.py", "read"),
    ("show me the authentication code", "read"),
    ("display the current git branch", "read"),
    ("view the error logs", "read"),
    ("open the project settings", "read"),
    # write - Creating, generating, producing
    ("create a new function to parse JSON", "write"),
    ("write a test for the auth module", "write"),
    ("add error handling to this code", "write"),
    ("generate a new class for user management", "write"),
    ("implement a retry mechanism", "write"),
    # analyze - Examining, investigating, auditing
    ("analyze the performance bottleneck", "analyze"),
    ("examine the code structure", "analyze"),
    ("investigate the memory leak", "analyze"),
    ("review the pull request", "analyze"),
    # research - Looking up documentation, investigating online
    ("research best practices for API design", "research"),
    ("look up documentation for pytest fixtures", "research"),
    ("find information about docker compose", "research"),
    ("search the web for python async patterns", "research"),
    # code - Implementation, programming, refactoring
    ("refactor this function to use async/await", "code"),
    ("optimize the database query", "code"),
    ("fix the null pointer exception", "code"),
    ("program a new endpoint for user registration", "code"),
    # test - Testing, verifying, validating
    ("test the authentication module", "test"),
    ("verify the input validation logic", "test"),
    ("validate the JSON schema", "test"),
    ("check if the function handles edge cases", "test"),
    # git - Version control operations
    ("commit the changes with message", "git"),
    ("push the branch to remote", "git"),
    ("merge the feature branch", "git"),
    ("checkout to main branch", "git"),
    # web - Online resources, external APIs
    ("fetch data from the external API", "web"),
    ("scrape the website for content", "web"),
    ("download the file from the URL", "web"),
    # existence_claim - Missing/unavailable assertions
    ("the skill is missing from the system", "existence_claim"),
    ("file not found in the expected location", "existence_claim"),
    ("command not found on this system", "existence_claim"),
    ("the required dependency is not installed", "existence_claim"),
    # other - General, miscellaneous, unclear intent
    ("hello there", "other"),
    ("what's the weather like", "other"),
    ("tell me a joke", "other"),
]


class TestIntentAccuracy:
    """Test suite for intent classification accuracy against golden corpus.

    These tests CAPTURE CURRENT BEHAVIOR before implementing the classify_intent
    feature on SemanticClient. All tests are expected to FAIL initially.
    """

    @pytest.fixture
    def semantic_client(self):
        """Create a SemanticClient instance for testing.

        Note: classify_intent() method does not exist yet - tests will fail.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import SemanticClient

        # Create client without connecting to daemon
        # We're testing the classify_intent method, not daemon communication
        client = SemanticClient.__new__(SemanticClient)
        client.pipe_name = r"\\.\pipe\test_intent_classification"
        client.auto_start = False
        client._handle = None
        client._connected = False

        yield client

    @pytest.mark.parametrize("prompt,expected_intent", GOLDEN_CORPUS)
    def test_classify_intent_accuracy(self, semantic_client, prompt, expected_intent):
        """Test that classify_intent returns expected intent for golden corpus prompts.

        This is a parametrized test that runs against all 30+ prompts in the golden corpus.

        Given: A prompt from the golden corpus
        When: SemanticClient.classify_intent(prompt) is called
        Then: The returned intent matches the expected intent

        Args:
            semantic_client: The SemanticClient instance
            prompt: The test prompt
            expected_intent: The expected intent category
        """
        # Act
        result = semantic_client.classify_intent(prompt)

        # Assert
        assert (
            result == expected_intent
        ), f"Expected intent '{expected_intent}' for prompt: '{prompt}', but got '{result}'"

    def test_all_intents_covered(self):
        """Verify: Golden corpus covers all 11 intent categories.

        This is a meta-test to ensure test completeness.
        """
        # Extract unique intents from golden corpus
        covered_intents = {intent for _, intent in GOLDEN_CORPUS}

        # Define all expected intents
        all_intents = {
            "search",
            "read",
            "write",
            "analyze",
            "research",
            "code",
            "test",
            "git",
            "web",
            "existence_claim",
            "other",
        }

        # Assert coverage
        assert (
            covered_intents == all_intents
        ), f"Golden corpus missing intents: {all_intents - covered_intents}"

    def test_golden_corpus_size(self):
        """Verify: Golden corpus has at least 30 test cases.

        This is a meta-test to ensure adequate test coverage.
        """
        assert (
            len(GOLDEN_CORPUS) >= 30
        ), f"Golden corpus should have at least 30 test cases, got {len(GOLDEN_CORPUS)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
