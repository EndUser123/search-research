#!/usr/bin/env python3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from posttooluse.effects.logging_effect import LoggingEffectVerifier
from posttooluse.observable_effect_verifier import ObservableEffectVerifier


class TestObservableEffectVerifier:
    def test_extends_post_tool_use_hook(self):
        from posttooluse.base import PostToolUseHook
        verifier = ObservableEffectVerifier()
        assert isinstance(verifier, PostToolUseHook)

    def test_env_var_configuration(self):
        verifier = ObservableEffectVerifier()
        assert verifier.env_var == "SEV_ENABLED"
        assert verifier.default_enabled is True

    def test_tool_matcher_configuration(self):
        verifier = ObservableEffectVerifier()
        assert verifier.tool_matcher == {"Edit", "Write"}

    def test_registers_logging_effect_verifier(self):
        verifier = ObservableEffectVerifier()
        assert len(verifier.verifiers) > 0

    def test_process_returns_expected_structure(self):
        verifier = ObservableEffectVerifier()
        tool_input = {"file_path": "test.py"}
        result = verifier.process("Write", tool_input, {})
        assert "passed" in result

    def test_skips_non_edit_write_tools(self):
        verifier = ObservableEffectVerifier()
        result = verifier.process("Read", {}, {})
        assert result.get("passed") is True

    def test_env_var_disables_hook(self):
        with patch.dict("os.environ", {"SEV_ENABLED": "false"}):
            verifier = ObservableEffectVerifier()
            assert not verifier.enabled


class TestEffectVerifierInterface:
    def test_logging_verifier_has_detect_method(self):
        verifier = LoggingEffectVerifier()
        assert callable(verifier.detect)

    def test_logging_verifier_enable_disable(self):
        verifier = LoggingEffectVerifier()
        verifier.disable()
        assert not verifier.is_enabled()
        verifier.enable()
        assert verifier.is_enabled()


class TestSkipPatterns:
    def test_conditional_logging_skip(self):
        content = "if DEBUG:" + chr(10) + "    handler = logging.FileHandler('debug.log')"
        result = LoggingEffectVerifier.detect_config(content, "test.py")
        assert result is None

    def test_env_based_path_skip(self):
        content = "os.getenv('LOG_PATH')"
        result = LoggingEffectVerifier.detect_config(content, "test.py")
        assert result is None


class TestEffectVerificationScenarios:
    def test_verification_fail_when_log_missing(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import logging" + chr(10) + "handler = logging.FileHandler('missing.log')")
            py_file = f.name
        try:
            config = LoggingEffectVerifier.detect_config(Path(py_file).read_text(), py_file)
            result = LoggingEffectVerifier.verify_config(config, py_file)
            assert not result.is_valid()
        finally:
            Path(py_file).unlink(missing_ok=True)


class TestPositiveNegativeCases:
    def test_positive_simple_filehandler(self):
        content = "handler = logging.FileHandler('app.log')"
        result = LoggingEffectVerifier.detect_config(content, "test.py")
        assert result is not None
        assert result["log_path"] == "app.log"

    def test_negative_no_logging(self):
        content = "print('hello')"
        result = LoggingEffectVerifier.detect_config(content, "test.py")
        assert result is None

    def test_negative_non_python_file(self):
        content = "handler = logging.FileHandler('app.log')"
        result = LoggingEffectVerifier.detect_config(content, "test.js")
        assert result is None


class TestPerformanceBaseline:
    def test_baseline_latency_no_effects(self):
        import time
        verifier = ObservableEffectVerifier()
        tool_input = {"file_path": __file__}
        start = time.perf_counter()
        result = verifier.process("Write", tool_input, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
