import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

def test_agreement_consistency():
    """Unit test for Agreement Consistency Scanner."""
    print("Testing Agreement Consistency Scanner...")
    from constitutional_enforcer import ConstitutionalEnforcer

    enforcer = ConstitutionalEnforcer()

    # Scenario: Agree then contradict
    print("Scenario: Agree then contradict")
    data = {
        "messages": [
            {"role": "user", "content": "the path P:/bad/path is invalid"}
        ],
        "response": "You're right, P:/bad/path is invalid. Looking at the data, P:/bad/path contains 5 files."
    }
    is_valid, violations = enforcer.validate(data["response"], data)
    v_ids = [v.get('rule_id') if isinstance(v, dict) else v.rule_id for v in violations]
    assert is_valid is False
    assert 'SCANNER-AgreementConsistency' in v_ids
    print("✅ Passed")

    # Scenario: Consistency
    print("Scenario: Consistency")
    data = {
        "messages": [
            {"role": "user", "content": "the path P:/bad/path is invalid"}
        ],
        "response": "Agreed, P:/bad/path is bad. I will migrate data from P:/bad/path to P:/good/path."
    }
    is_valid, violations = enforcer.validate(data["response"], data)
    v_ids = [v.get('rule_id') if isinstance(v, dict) else v.rule_id for v in violations]
    assert is_valid is True
    assert 'SCANNER-AgreementConsistency' not in v_ids
    print("✅ Passed")

if __name__ == "__main__":
    try:
        test_agreement_consistency()
        print("\nAll tests passed successfully.")
    except AssertionError:
        print("❌ Test failed")
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
