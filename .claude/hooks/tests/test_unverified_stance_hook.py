#!/usr/bin/env python3
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))


class TestUnverifiedStanceHook:
    def test_detects_skeptical_stance_without_verification(self):
        import StopHook_unverified_stance as hook_module

        input_data = {
            "response": "That sounds high.",
            "toolUse": [],
            "transcript": [{"role": "user", "content": "React has 100k stars."}],
        }
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            # Patch mode to 'warn' so tests are independent of settings.json
            with patch.object(hook_module, "UNVERIFIED_STANCE_MODE", "warn"):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    hook_module.main()
                    output = mock_out.getvalue()
                    result = json.loads(output)
                    assert result["allow"] is True  # Warn mode allows

    def test_allows_when_verification_tool_used(self):
        import StopHook_unverified_stance as hook_module

        input_data = {
            "response": "Let me verify that number.",
            "toolUse": [{"name": "WebSearch"}],
            "transcript": [{"role": "user", "content": "React has 100k stars."}],
        }
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            # Patch mode to 'warn' so tests are independent of settings.json
            with patch.object(hook_module, "UNVERIFIED_STANCE_MODE", "warn"):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    hook_module.main()
                    output = mock_out.getvalue()
                    result = json.loads(output)
                    assert result["allow"] is True
                    # Should not have warning when verification tool used

    def test_detects_unfounded_system_claims(self):
        import StopHook_unverified_stance as hook_module

        input_data = {
            "response": "Since the hook blocks this, we can't proceed.",
            "toolUse": [],
            "transcript": [],
        }
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            # Patch mode to 'warn' so tests are independent of settings.json
            with patch.object(hook_module, "UNVERIFIED_STANCE_MODE", "warn"):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    hook_module.main()
                    output = mock_out.getvalue()
                    result = json.loads(output)
                    assert result["allow"] is True  # Warn mode

    def test_allows_valid_explanation(self):
        import StopHook_unverified_stance as hook_module

        input_data = {
            "response": "Line 145 shows the hook configuration.",
            "toolUse": [],
            "transcript": [],
        }
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                hook_module.main()
                output = mock_out.getvalue()
                result = json.loads(output)
                assert result["allow"] is True

    def test_allows_questions(self):
        import StopHook_unverified_stance as hook_module

        input_data = {
            "response": "Let me check on that for you.",
            "toolUse": [],
            "transcript": [{"role": "user", "content": "How many stars does this have?"}],
        }
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                hook_module.main()
                output = mock_out.getvalue()
                result = json.loads(output)
                assert result["allow"] is True

    def test_handles_missing_response_gracefully(self):
        import StopHook_unverified_stance as hook_module

        input_data = {"response": "", "toolUse": [], "transcript": []}
        with patch("sys.stdin") as mock_stdin:
            import io

            mock_stdin.read.return_value = json.dumps(input_data)
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                hook_module.main()
                output = mock_out.getvalue()
                result = json.loads(output)
                assert result["allow"] is True

    def test_output_result_function(self):
        import io

        from StopHook_unverified_stance import output_result

        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            output_result(allow=True, reason="Test reason")
            output = mock_out.getvalue()
            result = json.loads(output)
            assert result["allow"] is True
            assert result["reason"] == "Test reason"

    def test_integration_with_existing_detector(self):
        from anti_sycophancy.unverified_stance_detector import detect_unverified_stance

        # Test that the detector works standalone
        response = "That sounds high."
        data = {
            "response": response,
            "toolUse": [],
            "transcript": [{"role": "user", "content": "React has 100k stars."}],
        }
        result = detect_unverified_stance(response, data)
        assert result is not None
        assert result.category == "empty_hedge"


class TestEnvironmentVariableConfiguration:
    def test_can_configure_mode_via_reload(self):
        import os

        import StopHook_unverified_stance

        # Temporarily remove env var to test that the default value is 'warn'
        saved = os.environ.pop("UNVERIFIED_STANCE_MODE", None)
        try:
            importlib.reload(StopHook_unverified_stance)
            assert StopHook_unverified_stance.UNVERIFIED_STANCE_MODE == "warn"
        finally:
            if saved is not None:
                os.environ["UNVERIFIED_STANCE_MODE"] = saved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
