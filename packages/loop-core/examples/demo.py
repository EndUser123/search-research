#!/usr/bin/env python3
"""Quick demo of loop-core functionality."""

from pathlib import Path

from core import TerminalStateManager, parse_plan_tasks


def main():
    print("=" * 60)
    print("loop-core Package Demo")
    print("=" * 60)

    # 1. Show terminal detection
    print("\n📍 Terminal Detection:")
    manager = TerminalStateManager()
    print(f"   Terminal ID: {manager.terminal_id}")
    print(f"   State Dir: {manager.state_dir}")
    print(f"   Directory exists: {manager.state_dir.exists()}")

    # 2. Write and read state
    print("\n📝 State Management:")
    manager.write_state("demo_state", {
        "message": "Hello from loop-core!",
        "timestamp": "2026-03-14",
        "counter": 42
    })
    print("   ✓ Wrote state to file")

    state = manager.read_state("demo_state")
    print(f"   ✓ Read state: {state}")

    # 3. Show lock file behavior
    print("\n🔒 Lock Management:")
    if manager.acquire_lock("demo_lock"):
        print("   ✓ Acquired lock 'demo_lock'")

        # Try to acquire same lock (should fail)
        if not manager.acquire_lock("demo_lock"):
            print("   ✓ Second acquire blocked (lock already held)")

        manager.release_lock("demo_lock")
        print("   ✓ Released lock")

        # Now acquire should succeed
        if manager.acquire_lock("demo_lock"):
            print("   ✓ Re-acquired lock after release")
            manager.release_lock("demo_lock")

    # 4. Parse plan file (create example if missing)
    print("\n📋 Plan Parsing:")
    example_plan = Path("example_plan.md")

    if not example_plan.exists():
        example_plan.write_text("""# Example Plan

- [ ] TASK-001 Implement state manager
- [x] TASK-002 Write tests
- [ ] TASK-003 Add documentation [tag:docs]
- [ ] TASK-004 Add error handling after:TASK-001
""")
        print("   ✓ Created example_plan.md")

    tasks = parse_plan_tasks(example_plan)
    print(f"   ✓ Parsed {len(tasks)} tasks")

    incomplete = [t for t in tasks if not t["complete"]]
    print(f"   - Incomplete: {len(incomplete)}")
    for task in incomplete:
        print(f"     [{task['id']}] {task['text']}")

    complete = [t for t in tasks if t["complete"]]
    print(f"   - Complete: {len(complete)}")
    for task in complete:
        print(f"     [{task['id']}] {task['text']}")

    # 5. Show file structure
    print("\n📁 State Directory Structure:")
    if manager.state_dir.exists():
        files = list(manager.state_dir.glob("*.json")) + list(manager.state_dir.glob("*.lock"))
        for file in files:
            size = file.stat().st_size
            print(f"   - {file.name} ({size} bytes)")

    # 6. Show multi-terminal isolation
    print("\n🔀 Multi-Terminal Isolation:")
    manager_a = TerminalStateManager(terminal_id="terminal_a")
    manager_b = TerminalStateManager(terminal_id="terminal_b")

    manager_a.write_state("test", {"terminal": "A"})
    manager_b.write_state("test", {"terminal": "B"})

    state_a = manager_a.read_state("test")
    state_b = manager_b.read_state("test")

    print(f"   Terminal A state: {state_a}")
    print(f"   Terminal B state: {state_b}")
    print(f"   States isolated: {state_a != state_b}")

    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
