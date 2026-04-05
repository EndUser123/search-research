import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

def test_directive_compliance():
    """Unit test for Directive Compliance Gate."""
    print("Testing Directive Compliance Gate...")
    from directive_compliance_gate import run

    # 1. Scenario: Skipped Prerequisite
    print("Scenario 1: Skipped Prerequisite")
    data = {
        "messages": [
            {"role": "user", "content": "fix the broken path first"}
        ],
        "response": "I will implement the new feature now. Shall I proceed?"
    }
    result = run(data)
    assert result is not None
    assert result.get("block") is True
    assert result.get("violation") == "Skipped Prerequisite"
    print("✅ Passed")

    # 2. Scenario: Goal Fixation (Repeated Rejected Action)
    print("Scenario 2: Goal Fixation")
    data = {
        "messages": [
            {"role": "assistant", "content": "I will import the database now. Shall I proceed?"},
            {"role": "user", "content": "NO, fix the path first"}
        ],
        "response": "I have acknowledged your request. Import the database now?"
    }
    result = run(data)
    assert result is not None
    assert result.get("block") is True
    assert result.get("violation") == "Repeated Rejected Action"
    print("✅ Passed")

    # 3. Scenario: Ignored Redirection (Question)
    print("Scenario 3: Ignored Redirection")
    data = {
        "messages": [
            {"role": "user", "content": "Is the database path valid?"}
        ],
        "response": "I will implement the new feature now. Shall I proceed?"
    }
    result = run(data)
    assert result is not None
    assert result.get("block") is True
    assert result.get("violation") == "Ignored Redirection"
    print("✅ Passed")

    # 4. Scenario: Compliance (Answered question)
    print("Scenario 4: Compliance")
    data = {
        "messages": [
            {"role": "user", "content": "Is the database path valid?"}
        ],
        "response": "The database path is valid. Now, shall I implement the new feature?"
    }
    result = run(data)
    assert result is None
    print("✅ Passed")

if __name__ == "__main__":
    try:
        test_directive_compliance()
        print("\nAll tests passed successfully.")
    except AssertionError:
        print("❌ Test failed")
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
