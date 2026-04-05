"""Integration tests for modified ask_cli execution flow.

Tests the complete flow: query → task classification → prompt engineering → execution → performance logging.
"""

from ai_cli import _PERFORMANCE_LOGGER
from prompt_templates import build_prompt
from task_classifier import TaskType, classify_task


class TestTaskClassificationIntegration:
    """Test task classification is applied to queries."""

    def test_code_review_query_classification(self):
        """Test code review queries are classified correctly."""
        result = classify_task("review this code for bugs")
        assert result.task_type == TaskType.CODE_REVIEW
        assert result.confidence > 0
        assert "review" in result.matched_keywords

    def test_planning_query_classification(self):
        """Test planning queries are classified correctly."""
        result = classify_task("create a plan for implementing feature X")
        assert result.task_type == TaskType.PLANNING
        assert result.confidence > 0

    def test_debug_query_classification(self):
        """Test debug queries are classified correctly."""
        result = classify_task("debug this error in module.py")
        assert result.task_type == TaskType.DEBUG
        assert result.confidence > 0

    def test_general_query_defaults_to_general(self):
        """Test queries without keywords default to general."""
        result = classify_task("hello world")
        assert result.task_type == TaskType.GENERAL
        assert result.confidence == 0.0


class TestPromptEngineeringIntegration:
    """Test prompt engineering enhances queries correctly."""

    def test_code_review_prompt_enhancement(self):
        """Test code review prompt adds security focus."""
        query = "review this code"
        classification = classify_task(query)
        enhanced_query = build_prompt(query, classification.task_type)

        # Should add code review template
        assert "CODE REVIEW" in enhanced_query
        assert "Security vulnerabilities" in enhanced_query
        assert query in enhanced_query  # Original query preserved

    def test_planning_prompt_enhancement(self):
        """Test planning prompt adds phased approach."""
        query = "create a plan"
        classification = classify_task(query)
        enhanced_query = build_prompt(query, classification.task_type)

        # Should add planning template
        assert "IMPLEMENTATION PLAN" in enhanced_query
        assert "Phase 1:" in enhanced_query
        assert query in enhanced_query

    def test_debug_prompt_enhancement(self):
        """Test debug prompt adds diagnostic focus."""
        query = "debug this"
        classification = classify_task(query)
        enhanced_query = build_prompt(query, classification.task_type)

        # Should add debug template
        assert "DEBUGGING" in enhanced_query
        assert "Diagnosis" in enhanced_query
        assert query in enhanced_query

    def test_solo_dev_constraints_applied(self):
        """Test solo-dev constraints are applied to all prompts."""
        for query, task_type in [
            ("review", TaskType.CODE_REVIEW),
            ("plan", TaskType.PLANNING),
            ("debug", TaskType.DEBUG),
            ("general", TaskType.GENERAL),
        ]:
            enhanced_query = build_prompt(query, task_type)
            assert "Solo Development Environment" in enhanced_query
            assert "NO team assignments" in enhanced_query
            assert "JSON > databases" in enhanced_query

    def test_context_injection(self):
        """Test context is injected into prompts."""
        query = "explain this"
        context = "This is file content"

        enhanced_query = build_prompt(query, TaskType.GENERAL, context=context)

        assert "--- Context ---" in enhanced_query
        assert context in enhanced_query
        assert query in enhanced_query


class TestPerformanceLoggingIntegration:
    """Test performance logging captures execution metrics."""

    def test_logger_records_all_required_fields(self, tmp_path):
        """Test logger records all required execution fields."""
        log_path = tmp_path / "test_integration_perf.jsonl"
        logger = _PERFORMANCE_LOGGER

        # Override log path for test
        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            logger.log_execution(
                cli_name="qwen",
                task_type=TaskType.CODE_REVIEW,
                query="review this code",
                duration_seconds=63.5,
                outcome="success",
                output_length=1500,
                error_message=None,
            )

            records = logger.get_all_records()
            assert len(records) == 1

            record = records[0]
            assert record.cli_name == "qwen"
            assert record.task_type == "code_review"
            assert record.duration_seconds == 63.5
            assert record.outcome == "success"
            assert record.output_length == 1500
        finally:
            logger.log_path = original_log_path

    def test_logger_tracks_all_supported_clis(self, tmp_path):
        """Test logger can track all supported CLI models."""
        log_path = tmp_path / "test_all_clis.jsonl"
        logger = _PERFORMANCE_LOGGER

        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            supported_clis = [
                "qwen",
                "gemini",
                "codex",
                "vibe",
                "opencode",
                "glm-4.7-flash",
            ]

            for cli in supported_clis:
                logger.log_execution(
                    cli_name=cli,
                    task_type=TaskType.GENERAL,
                    query="test query",
                    duration_seconds=1.0,
                    outcome="success",
                    output_length=100,
                )

            records = logger.get_all_records()
            logged_clis = {r.cli_name for r in records}
            assert logged_clis == set(supported_clis)
        finally:
            logger.log_path = original_log_path

    def test_logger_records_all_outcome_types(self, tmp_path):
        """Test logger records all outcome types."""
        log_path = tmp_path / "test_outcomes.jsonl"
        logger = _PERFORMANCE_LOGGER

        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            outcomes = ["success", "timeout", "error", "empty_output"]

            for outcome in outcomes:
                logger.log_execution(
                    cli_name="test_cli",
                    task_type=TaskType.GENERAL,
                    query="test",
                    duration_seconds=1.0,
                    outcome=outcome,
                    output_length=100 if outcome == "success" else 0,
                    error_message="Test error" if outcome == "error" else None,
                )

            records = logger.get_all_records()
            logged_outcomes = {r.outcome for r in records}
            assert logged_outcomes == set(outcomes)
        finally:
            logger.log_path = original_log_path


class TestExecutionFlow:
    """Test end-to-end execution flow components."""

    def test_classification_to_prompt_flow(self):
        """Test flow from classification to prompt building."""
        query = "review this code for security issues"

        # Step 1: Classify
        classification = classify_task(query)
        assert classification.task_type == TaskType.CODE_REVIEW

        # Step 2: Build prompt
        enhanced_prompt = build_prompt(query, classification.task_type)

        # Verify flow完整性
        assert "CODE REVIEW" in enhanced_prompt
        assert "Security vulnerabilities" in enhanced_prompt
        assert query in enhanced_prompt
        assert "Solo Development Environment" in enhanced_prompt

    def test_all_task_types_generate_valid_prompts(self):
        """Test all task types generate valid prompts."""
        test_queries = {
            TaskType.CODE_REVIEW: "review this code",
            TaskType.PLANNING: "create a plan",
            TaskType.BRAINSTORM: "brainstorm ideas",
            TaskType.RESEARCH: "research best practices",
            TaskType.DEBUG: "debug this error",
            TaskType.REFACTOR: "refactor this function",
            TaskType.GENERAL: "explain this",
        }

        for task_type, query in test_queries.items():
            prompt = build_prompt(query, task_type)

            # All prompts should include:
            assert query in prompt, f"Query missing in {task_type} prompt"
            assert (
                "Solo Development Environment" in prompt
            ), f"Constraints missing in {task_type} prompt"
            assert len(prompt) > 100, f"{task_type} prompt too short"

    def test_performance_stats_calculation(self, tmp_path):
        """Test performance statistics are calculated correctly."""
        log_path = tmp_path / "test_stats.jsonl"
        logger = _PERFORMANCE_LOGGER

        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            # Log some test data
            logger.log_execution(
                cli_name="qwen",
                task_type=TaskType.CODE_REVIEW,
                query="review 1",
                duration_seconds=60.0,
                outcome="success",
                output_length=1000,
            )

            logger.log_execution(
                cli_name="qwen",
                task_type=TaskType.CODE_REVIEW,
                query="review 2",
                duration_seconds=70.0,
                outcome="success",
                output_length=1500,
            )

            logger.log_execution(
                cli_name="gemini",
                task_type=TaskType.PLANNING,
                query="plan",
                duration_seconds=120.0,
                outcome="success",
                output_length=2000,
            )

            # Calculate stats
            stats = logger.get_performance_stats(task_type=TaskType.CODE_REVIEW)

            assert "qwen" in stats
            assert stats["qwen"]["total_executions"] == 2
            assert stats["qwen"]["success_rate"] == 1.0
            assert stats["qwen"]["avg_duration"] == 65.0  # (60 + 70) / 2
            assert stats["qwen"]["avg_output_length"] == 1250  # (1000 + 1500) / 2

            # Gemini should not be in code_review stats
            assert "gemini" not in stats
        finally:
            logger.log_path = original_log_path


class TestEdgeCasesIntegration:
    """Test edge cases in integrated flow."""

    def test_empty_query_handling(self):
        """Test empty query is handled gracefully."""
        result = classify_task("")
        assert result.task_type == TaskType.GENERAL
        assert result.confidence == 0.0

        prompt = build_prompt("", TaskType.GENERAL)
        assert len(prompt) > 0  # Should still build a prompt

    def test_very_long_query_truncation(self, tmp_path):
        """Test long queries are truncated in performance logs."""
        log_path = tmp_path / "test_truncation.jsonl"
        logger = _PERFORMANCE_LOGGER

        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            long_query = "x" * 200

            logger.log_execution(
                cli_name="qwen",
                task_type=TaskType.GENERAL,
                query=long_query,
                duration_seconds=1.0,
                outcome="success",
                output_length=100,
            )

            records = logger.get_all_records()
            assert len(records) == 1
            assert len(records[0].query_preview) == 100  # Truncated to 100 chars
        finally:
            logger.log_path = original_log_path

    def test_special_characters_in_query(self):
        """Test queries with special characters are handled."""
        special_query = "debug: error?! @#$% test <html> & 'quotes'"

        result = classify_task(special_query)
        assert result.task_type == TaskType.DEBUG  # "debug" keyword detected

        prompt = build_prompt(special_query, result.task_type)
        assert special_query in prompt  # Special chars preserved

    def test_concurrent_logging_safety(self, tmp_path):
        """Test concurrent logging doesn't corrupt data (multi-terminal safety)."""
        from threading import Thread

        log_path = tmp_path / "test_concurrent.jsonl"
        logger = _PERFORMANCE_LOGGER

        original_log_path = logger.log_path
        logger.log_path = log_path

        try:
            num_threads = 5
            writes_per_thread = 20
            errors = []

            def write_records(thread_id):
                try:
                    for i in range(writes_per_thread):
                        logger.log_execution(
                            cli_name=f"cli_{thread_id}",
                            task_type=TaskType.GENERAL,
                            query=f"query {thread_id} {i}",
                            duration_seconds=1.0,
                            outcome="success",
                            output_length=100,
                        )
                except Exception as e:
                    errors.append((thread_id, e))

            threads = []
            for i in range(num_threads):
                t = Thread(target=write_records, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # Verify no errors and all records written
            assert len(errors) == 0, f"Errors occurred: {errors}"
            records = logger.get_all_records()
            assert len(records) == num_threads * writes_per_thread

        finally:
            logger.log_path = original_log_path
