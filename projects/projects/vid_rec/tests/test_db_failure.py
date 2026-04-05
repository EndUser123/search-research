from pathlib import Path

from src.state_manager import JobStatus, StateManager


def main():
    db_path = Path("test_failure.db")
    if db_path.exists():
        db_path.unlink()

    sm = StateManager(db_path=db_path)
    test_file = Path("test_video_fail.mp4")
    test_file.touch()

    # Intentionally cause an error by passing invalid data
    print("Testing error handling...")
    # Pass an invalid status that's not part of JobStatus enum
    invalid_status = "INVALID_STATUS"
    try:
        sm.upsert_job(test_file, JobStatus(invalid_status), "Test error")
        print("Upsert should have failed but didn't")
    except Exception as e:
        print(f"Upsert failed as expected: {str(e)}")


if __name__ == "__main__":
    main()
