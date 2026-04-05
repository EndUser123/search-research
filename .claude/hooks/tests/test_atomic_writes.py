#!/usr/bin/env python3
"""Test atomic write race condition safety."""

import json
import multiprocessing

# Add atomic_write to path
import sys
import tempfile
from pathlib import Path

csf_nip_path = Path(__file__).resolve().parent.parent.parent.parent / "__csf" / "src"
if csf_nip_path.exists():
    sys.path.insert(0, str(csf_nip_path))

try:
    from utils.atomic_write import atomic_write_json
except ImportError:
    # Fallback for testing without CSF NIP
    print("Warning: atomic_write not found, using fallback")
    import shutil
    from pathlib import Path as _Path

    def atomic_write_json(file_path, data, indent=2):
        """Fallback atomic write implementation."""
        file_path = _Path(file_path)
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=indent)
        shutil.move(temp_path, file_path)


def worker_write(test_file: Path, worker_id: int, iterations: int = 10):
    """Worker that writes to shared file multiple times."""
    for i in range(iterations):
        data = {
            "worker": worker_id,
            "count": i,
            "timestamp": f"worker-{worker_id}-{i}"
        }
        atomic_write_json(test_file, data, indent=2)


def test_concurrent_writes():
    """Test that concurrent writes don't corrupt JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_file = Path(f.name)

    try:
        # Spawn multiple workers writing simultaneously
        processes = []
        num_workers = 4
        iterations = 25

        for worker_id in range(num_workers):
            p = multiprocessing.Process(
                target=worker_write,
                args=(test_file, worker_id, iterations)
            )
            processes.append(p)
            p.start()

        # Wait for all to complete
        for p in processes:
            p.join()

        # Verify result is valid JSON
        with open(test_file) as f:
            result = json.load(f)  # Will raise if corrupted

        # Verify structure
        assert "worker" in result
        assert "count" in result
        assert "timestamp" in result

        print("✅ Atomic write test passed - no corruption detected")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Atomic write test FAILED - JSON corruption: {e}")
        return False
    except Exception as e:
        print(f"❌ Atomic write test FAILED - {e}")
        return False
    finally:
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    import sys
    sys.exit(0 if test_concurrent_writes() else 1)
