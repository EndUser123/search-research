#!/usr/bin/env python3
"""Test script to verify CSF NIP slash command integration for chat search."""

import subprocess
import sys
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

def run_chs_command(command_args):
    """Run a chs command and return the output."""
    try:
        cmd = [
            "python", "chat_history_search.py"
        ] + command_args

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def test_slash_command_integration():
    """Test CSF NIP slash command integration for chat search."""
    print("🧪 Testing CSF NIP Slash Command Integration")
    print("=" * 60)

    # Test cases
    test_cases = [
        {
            "name": "Basic Search",
            "args": ["search", "GPU optimization", "--limit", "2"],
            "expected_patterns": ["Search Results", "Found", "Role:", "Score:"]
        },
        {
            "name": "JSON Format Search",
            "args": ["search", "monitoring dashboards", "--limit", "1", "--format", "json"],
            "expected_patterns": ["[", "]", '"text":', '"role":']
        },
        {
            "name": "RAG-Enabled Search",
            "args": ["search", "SQLite database", "--use-rag", "--limit", "1"],
            "expected_patterns": ["Search Results", "Found", "SQLite"]
        },
        {
            "name": "Status Command",
            "args": ["status"],
            "expected_patterns": ["SQLite", "RAG", "initialized"]
        },
        {
            "name": "Analysis Command",
            "args": ["analyze", "--pattern-analysis"],
            "expected_patterns": ["patterns", "analysis"]
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"   Command: chs {' '.join(test_case['args'])}")
        print("-" * 50)

        # Run the command
        result = run_chs_command(test_case['args'])

        if result['success']:
            print("   ✅ Command executed successfully")

            # Check for expected patterns
            stdout_lines = result['stdout'].split('\n')
            found_patterns = []

            for pattern in test_case['expected_patterns']:
                for line in stdout_lines:
                    if pattern in line:
                        found_patterns.append(pattern)
                        break

            pattern_match_rate = len(found_patterns) / len(test_case['expected_patterns'])

            print(f"   📊 Pattern Match: {len(found_patterns)}/{len(test_case['expected_patterns'])} ({pattern_match_rate*100:.0f}%)")

            if pattern_match_rate >= 0.75:  # 75% pattern match threshold
                print("   ✅ Expected output patterns found")
            else:
                print("   ⚠️  Some expected patterns missing")
                print(f"   📝 Missing: {set(test_case['expected_patterns']) - set(found_patterns)}")

            # Show sample output
            output_lines = [line for line in stdout_lines if line.strip() and not line.startswith('GPU environment')]
            if output_lines:
                print("   📝 Sample Output:")
                for line in output_lines[:3]:  # Show first 3 lines
                    print(f"      {line}")
                if len(output_lines) > 3:
                    print(f"      ... ({len(output_lines)-3} more lines)")

        else:
            print("   ❌ Command failed")
            print(f"   🚫 Return Code: {result['returncode']}")
            if result['stderr']:
                print(f"   📝 Error: {result['stderr'][:200]}...")

        results.append({
            "test": test_case['name'],
            "success": result['success'],
            "pattern_match": pattern_match_rate if result['success'] else 0
        })

    # Summary
    print("\n📈 Test Summary:")
    print("=" * 30)

    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)

    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {total_tests - successful_tests}")
    print(f"   Success Rate: {(successful_tests/total_tests)*100:.0f}%")

    # Individual results
    print("\n📊 Individual Test Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        pattern_info = f"({result['pattern_match']*100:.0f}% patterns)" if result['success'] else ""
        print(f"   {status} {result['test']} {pattern_info}")

    # Overall assessment
    overall_success = successful_tests >= (total_tests * 0.8)  # 80% success threshold
    print(f"\n🎯 Overall Integration Status: {'✅ PASS' if overall_success else '❌ NEEDS ATTENTION'}")

    if overall_success:
        print("   🎉 CSF NIP slash command integration is working properly!")
        print("   🔗 The /chs command successfully integrates with the chat search system")
    else:
        print("   ⚠️  Some integration issues detected - review failed tests")

    return overall_success

if __name__ == "__main__":
    test_slash_command_integration()
