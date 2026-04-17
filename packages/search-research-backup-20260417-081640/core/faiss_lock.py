"""
FAISS lock retry wrapper with exponential backoff.

Handles concurrent read access to FAISS index files that may be temporarily
locked by other processes (e.g., during index updates).
"""

import time
from pathlib import Path

import faiss


class FAISSLockTimeoutError(PermissionError):
    """Raised when FAISS index cannot be read after all retries."""

    def __init__(self, path: str | Path, attempts: int, elapsed: float):
        self.path = str(path)
        self.attempts = attempts
        self.elapsed = elapsed
        super().__init__(
            f"FAISS lock timeout: Could not access {path} after {attempts} attempts "
            f"({elapsed:.1f}s). File may be locked by another process."
        )


def faiss_open_read(path: str | Path, timeout: float = 5.0) -> faiss.Index:
    """
    Open a FAISS index file with retry logic for handling temporary locks.

    This function is a drop-in replacement for `faiss.read_index()` that adds
    automatic retry logic with exponential backoff when encountering
    PermissionError from concurrent file access.

    Args:
        path: Path to the FAISS index file
        timeout: Maximum time to spend retrying (default: 5.0 seconds)

    Returns:
        Loaded FAISS index

    Raises:
        FAISSLockTimeoutError: If the file cannot be read after all retries
        FileNotFoundError: If the file doesn't exist
        RuntimeError: For other FAISS read errors

    Example:
        >>> # Instead of: index = faiss.read_index("path/to/index.faiss")
        >>> index = faiss_open_read("path/to/index.faiss")
    """
    path = Path(path)
    start_time = time.time()
    attempt = 0

    # Exponential backoff sequence: 0.2s, 0.4s, 0.8s, 1.6s
    # Total of 4 attempts (initial + 3 retries)
    max_attempts = 4
    backoff_delays = [0.2, 0.4, 0.8, 1.6]

    while attempt < max_attempts:
        attempt += 1
        elapsed = time.time() - start_time

        try:
            return faiss.read_index(str(path))

        except PermissionError as e:
            # Check if we've used all attempts
            if attempt >= max_attempts:
                raise FAISSLockTimeoutError(path, attempt, elapsed) from e

            # Sleep before retry (only after first attempt)
            if attempt < max_attempts:
                delay = backoff_delays[attempt - 1]

                # Don't sleep longer than remaining timeout
                if elapsed + delay > timeout:
                    # Would exceed timeout, raise immediately
                    raise FAISSLockTimeoutError(path, attempt, elapsed) from e

                if attempt > 1:
                    # Only print diagnostic info after second attempt (avoid noise)
                    print(
                        f"FAISS read attempt {attempt} blocked by lock ({path.name}). "
                        f"Retrying in {delay:.1f}s..."
                    )

                time.sleep(delay)

        except FileNotFoundError as e:
            # Don't retry if file doesn't exist
            raise FileNotFoundError(
                f"FAISS index file not found: {path}"
            ) from e

        except Exception as e:
            # For other errors, don't retry - propagate immediately
            raise RuntimeError(
                f"Unexpected error reading FAISS index from {path}: {e}"
            ) from e
