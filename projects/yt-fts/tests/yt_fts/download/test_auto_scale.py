"""
Comprehensive unit tests for auto_scale.py module.

Tests cover all pure functions in the module:
- get_optimal_workers: Worker calculation based on mode, CPU, and quota
- get_jobs_per_worker: Jobs-per-worker calculation for threadpool sizing
- apply_preset: Preset configuration with overrides
- PRESETS: Preset dictionary validation
"""

from unittest.mock import patch

from yt_fts.download.auto_scale import (
    PRESETS,
    apply_preset,
    get_jobs_per_worker,
    get_optimal_workers,
)


class TestGetOptimalWorkers:
    """Test worker calculation logic for different modes and constraints."""

    def test_max_workers_override_bypasses_all_logic(self):
        """
        Test that max_workers parameter bypasses all calculation logic.

        Given: max_workers is set to a specific value
        When: get_optimal_workers is called with any mode/cpu_cores/quota
        Then: The max_workers value is returned directly
        """
        # Should return 10 regardless of mode, CPU, or quota
        assert get_optimal_workers("metadata", max_workers=10) == 10
        assert get_optimal_workers("subtitles", max_workers=10) == 10
        assert get_optimal_workers("mixed", max_workers=10) == 10

        # Even with extreme CPU values, override wins
        assert get_optimal_workers("metadata", max_workers=10, cpu_cores=1) == 10
        assert get_optimal_workers("metadata", max_workers=10, cpu_cores=100) == 10

    @patch("yt_fts.download.auto_scale.multiprocessing.cpu_count")
    def test_cpu_cores_none_triggers_auto_detection(self, mock_cpu_count):
        """
        Test that cpu_cores=None triggers auto-detection via multiprocessing.

        Given: cpu_cores parameter is None
        When: get_optimal_workers is called
        Then: multiprocessing.cpu_count() is called for auto-detection
        """
        mock_cpu_count.return_value = 8

        # Metadata mode should use detected CPU count
        result = get_optimal_workers("metadata", cpu_cores=None)
        assert result == min(8 * 2, 16)  # min(cpu_cores * 2, 16)

        # Verify cpu_count was called
        mock_cpu_count.assert_called_once()

    def test_low_quota_reduces_metadata_workers(self):
        """
        Test that low API quota (< 5000) reduces workers in metadata mode.

        Given: quota_remaining is less than 5000
        When: get_optimal_workers is called with mode="metadata"
        Then: Workers are capped at 4 (conservative mode)
        """
        # High CPU but low quota -> should cap at 4
        result = get_optimal_workers(
            "metadata",
            cpu_cores=16,
            quota_remaining=1000
        )
        assert result == 4  # min(min(16 * 2, 16), 4) = 4

        # Exactly at threshold -> should cap at 4
        result = get_optimal_workers(
            "metadata",
            cpu_cores=16,
            quota_remaining=4999
        )
        assert result == 4

        # Just above threshold -> should use normal calculation
        result = get_optimal_workers(
            "metadata",
            cpu_cores=16,
            quota_remaining=5000
        )
        assert result == min(16 * 2, 16)  # 16, not capped

    def test_metadata_mode_calculation(self):
        """
        Test metadata mode worker calculation.

        Given: mode="metadata"
        When: get_optimal_workers is called with various CPU counts
        Then: Returns min(cpu_cores * 2, 16), respecting quota limits
        """
        # Low CPU: cpu_cores * 2 is less than 16
        assert get_optimal_workers("metadata", cpu_cores=2) == 4  # 2 * 2 = 4
        assert get_optimal_workers("metadata", cpu_cores=4) == 8  # 4 * 2 = 8

        # High CPU: capped at 16
        assert get_optimal_workers("metadata", cpu_cores=8) == 16  # 8 * 2 = 16, cap
        assert get_optimal_workers("metadata", cpu_cores=16) == 16  # 16 * 2 = 32, cap at 16
        assert get_optimal_workers("metadata", cpu_cores=32) == 16  # cap at 16

    def test_subtitles_mode_calculation(self):
        """
        Test subtitles mode worker calculation.

        Given: mode="subtitles"
        When: get_optimal_workers is called with various CPU counts
        Then: Returns min(cpu_cores, 4) - SQLite write contention limits
        """
        # Low CPU: CPU count is the limit
        assert get_optimal_workers("subtitles", cpu_cores=1) == 1
        assert get_optimal_workers("subtitles", cpu_cores=2) == 2

        # Medium CPU: still under cap
        assert get_optimal_workers("subtitles", cpu_cores=3) == 3
        assert get_optimal_workers("subtitles", cpu_cores=4) == 4

        # High CPU: capped at 4
        assert get_optimal_workers("subtitles", cpu_cores=8) == 4
        assert get_optimal_workers("subtitles", cpu_cores=16) == 4

    def test_mixed_mode_calculation(self):
        """
        Test mixed mode worker calculation.

        Given: mode="mixed"
        When: get_optimal_workers is called with various CPU counts
        Then: Returns min(cpu_cores, 6) - balance between API and downloads
        """
        # Low CPU: CPU count is the limit
        assert get_optimal_workers("mixed", cpu_cores=1) == 1
        assert get_optimal_workers("mixed", cpu_cores=2) == 2

        # Medium CPU: still under cap
        assert get_optimal_workers("mixed", cpu_cores=4) == 4
        assert get_optimal_workers("mixed", cpu_cores=6) == 6

        # High CPU: capped at 6
        assert get_optimal_workers("mixed", cpu_cores=8) == 6
        assert get_optimal_workers("mixed", cpu_cores=16) == 6

    def test_minimum_1_worker_guarantee(self):
        """
        Test that get_optimal_workers always returns at least 1.

        Given: Any combination of mode and parameters
        When: get_optimal_workers is called
        Then: Result is always >= 1 (even with edge cases)
        """
        # Even with 0 CPU cores (edge case), should return 1
        assert get_optimal_workers("metadata", cpu_cores=0) == 1
        assert get_optimal_workers("subtitles", cpu_cores=0) == 1
        assert get_optimal_workers("mixed", cpu_cores=0) == 1

        # Negative max_workers should still work (user override)
        # This is an edge case - the function allows it
        assert get_optimal_workers("metadata", max_workers=-5) == -5

    def test_quota_none_uses_normal_calculation(self):
        """
        Test that quota_remaining=None uses normal calculation without quota limit.

        Given: quota_remaining is None
        When: get_optimal_workers is called in metadata mode
        Then: Normal CPU-based calculation is used (no quota cap)
        """
        result = get_optimal_workers("metadata", cpu_cores=16, quota_remaining=None)
        assert result == min(16 * 2, 16)  # Should be 16, not capped at 4


class TestGetJobsPerWorker:
    """Test jobs-per-worker calculation for threadpool sizing."""

    def test_metadata_mode_returns_1(self):
        """
        Test that metadata mode always returns 1 job per worker.

        Given: mode="metadata"
        When: get_jobs_per_worker is called with any worker count
        Then: Returns 1 (API calls are serial, parallelism is across workers)
        """
        assert get_jobs_per_worker(workers=1, mode="metadata") == 1
        assert get_jobs_per_worker(workers=4, mode="metadata") == 1
        assert get_jobs_per_worker(workers=16, mode="metadata") == 1
        assert get_jobs_per_worker(workers=100, mode="metadata") == 1

    def test_subtitles_mode_threshold_at_workers_gt_2(self):
        """
        Test that subtitles mode returns 1 job when workers > 2.

        Given: mode="subtitles" and workers > 2
        When: get_jobs_per_worker is called
        Then: Returns 1 (reduce jobs with more workers to limit SQLite contention)
        """
        assert get_jobs_per_worker(workers=3, mode="subtitles") == 1
        assert get_jobs_per_worker(workers=4, mode="subtitles") == 1
        assert get_jobs_per_worker(workers=8, mode="subtitles") == 1
        assert get_jobs_per_worker(workers=16, mode="subtitles") == 1

    def test_subtitles_mode_boundary_workers_2_vs_3(self):
        """
        Test the boundary condition at workers=2 vs workers=3 for subtitles mode.

        Given: mode="subtitles"
        When: get_jobs_per_worker is called with workers=2 and workers=3
        Then: workers=2 returns 2, workers=3 returns 1 (threshold behavior)
        """
        # At boundary: workers=2 returns 2 jobs
        assert get_jobs_per_worker(workers=2, mode="subtitles") == 2

        # Just over boundary: workers=3 returns 1 job
        assert get_jobs_per_worker(workers=3, mode="subtitles") == 1

    def test_subtitles_mode_single_worker_returns_2(self):
        """
        Test that subtitles mode with 1 worker returns 2 jobs.

        Given: mode="subtitles" and workers=1
        When: get_jobs_per_worker is called
        Then: Returns 2 (single worker can handle multiple download jobs)
        """
        assert get_jobs_per_worker(workers=1, mode="subtitles") == 2

    def test_mixed_mode_returns_1(self):
        """
        Test that mixed mode always returns 1 job per worker.

        Given: mode="mixed"
        When: get_jobs_per_worker is called with any worker count
        Then: Returns 1
        """
        assert get_jobs_per_worker(workers=1, mode="mixed") == 1
        assert get_jobs_per_worker(workers=4, mode="mixed") == 1
        assert get_jobs_per_worker(workers=16, mode="mixed") == 1


class TestApplyPreset:
    """Test preset configuration application with overrides."""

    def test_valid_preset_names(self):
        """
        Test that all valid preset names return correct configurations.

        Given: A valid preset name from PRESETS
        When: apply_preset is called
        Then: Returns a copy of the preset configuration
        """
        # metadata-fast preset
        result = apply_preset("metadata-fast")
        assert result == {"workers": 8, "jobs": 1, "delay": 0}

        # metadata-balanced preset
        result = apply_preset("metadata-balanced")
        assert result == {"workers": 4, "jobs": 1, "delay": 0}

        # subtitles-safe preset
        result = apply_preset("subtitles-safe")
        assert result == {"workers": 2, "jobs": 1, "delay": 1}

        # subtitles-max preset
        result = apply_preset("subtitles-max")
        assert result == {"workers": 3, "jobs": 2, "delay": 0}

        # mixed preset
        result = apply_preset("mixed")
        assert result == {"workers": 4, "jobs": 1, "delay": 0.5}

    def test_invalid_preset_name_falls_back_to_mixed(self):
        """
        Test that invalid preset names fall back to "mixed" preset.

        Given: An invalid preset name
        When: apply_preset is called
        Then: Returns the "mixed" preset configuration
        """
        # Totally invalid name
        result = apply_preset("invalid-preset-name")
        assert result == {"workers": 4, "jobs": 1, "delay": 0.5}

        # Empty string
        result = apply_preset("")
        assert result == {"workers": 4, "jobs": 1, "delay": 0.5}

        # Case sensitivity (should not match)
        result = apply_preset("Metadata-Fast")
        assert result == {"workers": 4, "jobs": 1, "delay": 0.5}

    def test_overrides_with_valid_keys(self):
        """
        Test that overrides are applied to the preset configuration.

        Given: A preset name and override dictionary
        When: apply_preset is called with overrides
        Then: Returns preset config with overrides applied
        """
        # Single override
        result = apply_preset("metadata-fast", overrides={"workers": 16})
        assert result == {"workers": 16, "jobs": 1, "delay": 0}

        # Multiple overrides
        result = apply_preset("metadata-fast", overrides={"workers": 12, "delay": 0.5})
        assert result == {"workers": 12, "jobs": 1, "delay": 0.5}

        # Override all values
        result = apply_preset("metadata-fast", overrides={"workers": 1, "jobs": 2, "delay": 5})
        assert result == {"workers": 1, "jobs": 2, "delay": 5}

    def test_overrides_with_invalid_preset(self):
        """
        Test that overrides work even with invalid preset names.

        Given: An invalid preset name and override dictionary
        When: apply_preset is called
        Then: Returns "mixed" preset with overrides applied
        """
        result = apply_preset("invalid", overrides={"workers": 8})
        assert result == {"workers": 8, "jobs": 1, "delay": 0.5}

    def test_immutability_changing_result_doesnt_affect_presets(self):
        """
        Test that modifying the returned config doesn't affect PRESETS.

        Given: A preset configuration is returned
        When: The returned dictionary is modified
        Then: The original PRESETS dictionary remains unchanged
        """
        # Get a preset
        result = apply_preset("metadata-fast")

        # Store original expected value
        original_preset = PRESETS["metadata-fast"].copy()

        # Modify the returned result
        result["workers"] = 999
        result["new_key"] = "new_value"

        # Original PRESETS should be unchanged
        assert PRESETS["metadata-fast"] == original_preset
        assert "new_key" not in PRESETS["metadata-fast"]

    def test_none_overrides_returns_preset_unchanged(self):
        """
        Test that overrides=None returns the preset unchanged.

        Given: A preset name and overrides=None
        When: apply_preset is called
        Then: Returns a copy of the preset without modifications
        """
        result = apply_preset("subtitles-max", overrides=None)
        assert result == {"workers": 3, "jobs": 2, "delay": 0}


class TestPresets:
    """Test the PRESETS dictionary structure and values."""

    def test_all_expected_presets_exist(self):
        """
        Test that all expected preset keys exist in PRESETS.

        Given: The PRESETS dictionary
        When: Checking for expected preset names
        Then: All expected presets are present
        """
        expected_presets = [
            "metadata-fast",
            "metadata-balanced",
            "subtitles-safe",
            "subtitles-max",
            "mixed",
        ]

        for preset_name in expected_presets:
            assert preset_name in PRESETS, f"Preset '{preset_name}' not found"

    def test_preset_values_have_correct_structure(self):
        """
        Test that all preset values have the required keys.

        Given: Any preset in PRESETS
        When: Checking its structure
        Then: Contains 'workers', 'jobs', and 'delay' keys
        """
        required_keys = {"workers", "jobs", "delay"}

        for preset_name, config in PRESETS.items():
            assert required_keys.issubset(config.keys()), (
                f"Preset '{preset_name}' missing required keys. "
                f"Has {config.keys()}, needs {required_keys}"
            )

    def test_preset_workers_are_positive(self):
        """
        Test that all preset 'workers' values are greater than 0.

        Given: Any preset in PRESETS
        When: Checking the 'workers' value
        Then: workers > 0
        """
        for preset_name, config in PRESETS.items():
            assert config["workers"] > 0, (
                f"Preset '{preset_name}' has invalid workers: {config['workers']}"
            )

    def test_preset_jobs_are_at_least_1(self):
        """
        Test that all preset 'jobs' values are at least 1.

        Given: Any preset in PRESETS
        When: Checking the 'jobs' value
        Then: jobs >= 1
        """
        for preset_name, config in PRESETS.items():
            assert config["jobs"] >= 1, (
                f"Preset '{preset_name}' has invalid jobs: {config['jobs']}"
            )

    def test_preset_delay_are_non_negative(self):
        """
        Test that all preset 'delay' values are non-negative.

        Given: Any preset in PRESETS
        When: Checking the 'delay' value
        Then: delay >= 0
        """
        for preset_name, config in PRESETS.items():
            assert config["delay"] >= 0, (
                f"Preset '{preset_name}' has invalid delay: {config['delay']}"
            )

    def test_preset_values_are_reasonable(self):
        """
        Test that preset values fall within reasonable ranges.

        Given: Any preset in PRESETS
        When: Checking value ranges
        Then: Values are within expected practical limits
        """
        for preset_name, config in PRESETS.items():
            # Workers should be reasonably sized (1-32)
            assert 1 <= config["workers"] <= 32, (
                f"Preset '{preset_name}' workers out of range: {config['workers']}"
            )

            # Jobs should be reasonably sized (1-10)
            assert 1 <= config["jobs"] <= 10, (
                f"Preset '{preset_name}' jobs out of range: {config['jobs']}"
            )

            # Delay should be reasonable (0-60 seconds)
            assert 0 <= config["delay"] <= 60, (
                f"Preset '{preset_name}' delay out of range: {config['delay']}"
            )
