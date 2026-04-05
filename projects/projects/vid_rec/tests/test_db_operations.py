import sys
from pathlib import Path

from src.state_manager import JobStatus, StateManager


def main():
    db_path = Path("test_state.db")
    if db_path.exists():
        db_path.unlink()  # Remove existing test DB

    sm = StateManager(db_path=db_path)
    test_file = Path("test_video.mp4")
    test_file.touch()  # Create empty test file

    # Test upsert
    print("Testing upsert operation...")
    sm.upsert_job(test_file, JobStatus.FULLY_COMPLETED)
    print("Upsert successful!")

    # Verify the job was inserted
    print("\nVerifying job status...")
    status = sm.get_job_status(test_file)
    print(f"Job status: {status['status'].value}")
    print(f"Signature match: {not status['signature_mismatch']}")

    # Test reset
    print("\nTesting reset operation...")
    sm.reset_job(test_file)
    status_after_reset = sm.get_job_status(test_file)
    print(f"Status after reset: {status_after_reset['status'].value}")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)
