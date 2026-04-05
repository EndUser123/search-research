#!/usr/bin/env python3
"""
Test script to verify progress bar display without commas
"""

import asyncio
import time

import pytest
from dnld_telegram.src.ui.displays.tqdm_display import TQDMDisplay


@pytest.mark.asyncio
async def test_progress_bars():
    """Test the progress bars to ensure no commas appear"""
    print("Testing TQDM progress display...")

    display = TQDMDisplay()

    # Initialize display
    await display.initialize()

    # Test main task with file counts
    display.add_main_task("test", "Testing file downloads", total=3)
    display.start_main_task("test")

    # Test individual file downloads
    files = [
        ("BJ智贤3月 (9).mp4", 1200000000),  # 1.2GB file
        ("BJ智贤3月 (10).mp4", 310900000),  # 310MB file
        ("test_file.jpg", 50000000),  # 50MB file
    ]

    task_ids = []
    for filename, size in files:
        task_id = display.add_download_task(filename, size)
        task_ids.append((task_id, size))
        display.start_download_task(task_id)

    # Simulate downloads with progress updates
    for i in range(20):
        # Update each file's progress
        for j, (task_id, total_size) in enumerate(task_ids):
            if i * 5 < 100:  # Simulate different download speeds
                advance = max(1, int(total_size * 0.05))  # 5% per update
                display.update_download_task(task_id, advance)

        # Update main task
        if i % 7 == 0:  # Complete a file every 7 iterations
            file_num = i // 7
            if file_num < len(files):
                display.update_main_task(
                    "test", advance=1, status=f"Downloaded {files[file_num][0]}"
                )

        time.sleep(0.5)  # Brief pause to see updates

        # Complete some files
        if i == 6:
            display.complete_download_task(
                task_ids[2][0]
            )  # Complete smallest file first
        elif i == 12:
            display.complete_download_task(task_ids[1][0])  # Complete medium file
        elif i == 18:
            display.complete_download_task(task_ids[0][0])  # Complete largest file

    # Complete main task
    display.complete_main_task("test", "All downloads complete")

    # Cleanup
    await display.cleanup()

    print("\nTest completed! Check the progress bars above for:")
    print("1. No commas in any progress displays")
    print("2. File counts (X/Y) in overall progress bar")
    print("3. Proper file size formatting (e.g., '40.5M' not '40,500,000')")


if __name__ == "__main__":
    asyncio.run(test_progress_bars())
