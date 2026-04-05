"""
Tests for the main processing functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config import AppConfig, SettingsConfig
from src.main_processor import run_subtitle_phase
from src.processing_job import ProcessingJob
from src.state_manager import JobStatus
from src.ui_dashboard import Dashboard


@pytest.fixture
def mock_config():
    """Fixture to create a mock AppConfig."""
    config = MagicMock(spec=AppConfig)
    config.settings = MagicMock(spec=SettingsConfig)
    config.settings.create_subtitles = True
    config.paths.temp_dir = Path("/tmp/test_temp")
    return config


@pytest.fixture
def mock_state_manager():
    """Fixture to create a mock StateManager."""
    return MagicMock()


@pytest.fixture
def mock_dashboard():
    """Fixture to create a mock Dashboard."""
    dashboard = MagicMock(spec=Dashboard)
    dashboard.summary_data = {
        "queued": 1,
        "in_progress": 0,
        "completed": 0,
        "failed": 0,
        "failures": [],
    }
    dashboard.overall_progress = MagicMock()
    dashboard.overall_task = MagicMock()
    dashboard.current_task_text = MagicMock()
    dashboard.clear_subtitle_subtasks = MagicMock()
    dashboard.active_subtask_progress = []
    return dashboard


@patch("src.main_processor.load_model")
@patch("src.main_processor.generate_subtitles_for_file")
def test_run_subtitle_phase(
    mock_generate_subtitles,
    mock_load_model,
    mock_config,
    mock_state_manager,
    mock_dashboard,
):
    """Test the subtitle generation phase."""
    # Arrange
    mock_job = MagicMock(spec=ProcessingJob)
    mock_job.source_path = Path("/test/video.mp4")
    mock_job.file_name = "video.mp4"
    mock_job.temp_destination_dir = Path("/tmp/test_temp/video")
    jobs = [mock_job]

    ui_state = {"stop_event": MagicMock()}
    ui_state["stop_event"].is_set.return_value = False

    # Act
    run_subtitle_phase(
        jobs,
        mock_state_manager,
        ui_state,
        mock_dashboard,
    )

    # Assert
    mock_load_model.assert_called_once()
    mock_generate_subtitles.assert_called_once_with(
        str(mock_job.source_path),
        str(mock_job.temp_destination_dir),
        mock_dashboard.add_subtitle_subtask.return_value,  # This will be the progress callback
    )
    mock_state_manager.upsert_job.assert_called_once_with(
        mock_job.source_path, JobStatus.SUBTITLES_COMPLETED
    )
    assert mock_dashboard.summary_data["completed"] == 1
    assert (
        mock_dashboard.summary_data["in_progress"] == 0
    )  # Should be 0 after completion
    assert (
        mock_dashboard.summary_data["queued"] == 0
    )  # Should be 0 after processing the job
    mock_dashboard.overall_progress.advance.assert_called_once_with(
        mock_dashboard.overall_task
    )
    mock_dashboard.current_task_text.plain = (
        f"Current Task: Subtitles for {mock_job.file_name}"
    )
    mock_dashboard.clear_subtitle_subtasks.assert_called_once()
