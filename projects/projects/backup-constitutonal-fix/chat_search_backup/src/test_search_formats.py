#!/usr/bin/env python3
"""Test script to verify search result format consistency."""

import sys
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_search import ChatHistorySearcher


def test_search_result_formats():
    """Test that all search methods return consistent result formats."""
    print("🧪 Testing Search Result Format Consistency")
    print("=" * 60)

    # Initialize search system
    searcher = ChatHistorySearcher()

    # Test queries
    test_queries = [
        "GPU memory optimization",
        "SQLite database",
        "real-time monitoring",
        "batch sizing"
    ]

    all_results = []

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = searcher.search(query, limit=2)
        all_results.extend(results)

        print(f"📊 Results: {len(results)} found")

        for i, result in enumerate(results, 1):
            # Test all possible content field names
            content_fields = ['text', 'content', 'display']
            found_content = None

            for field in content_fields:
                if field in result and result[field]:
                    found_content = result[field]
                    break

            # Test role extraction
            role = result.get('metadata', {}).get('role', result.get('role', 'unknown'))

            # Test score extraction
            score = result.get('relevance_score', result.get('score', 'N/A'))

            # Test method
            method = result.get('search_method', 'unknown')

            print(f"  {i}. ✅ Content found: {bool(found_content)}")
            print(f"     📝 Length: {len(found_content) if found_content else 0}")
            print(f"     👤 Role: {role}")
            print(f"     📊 Score: {score}")
            print(f"     🔧 Method: {method}")

            # Verify result structure
            required_fields = ['text', 'display', 'content', 'metadata']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                print(f"     ⚠️  Missing fields: {missing_fields}")
            else:
                print("     ✅ All required fields present")

    # Summary
    print("\n📈 Test Summary:")
    print(f"   Total queries tested: {len(test_queries)}")
    print(f"   Total results processed: {len(all_results)}")
    print(f"   Average results per query: {len(all_results) / len(test_queries):.1f}")

    # Validate consistency
    print("\n🔍 Format Consistency Check:")
    field_counts = {}
    for result in all_results:
        for field in result.keys():
            field_counts[field] = field_counts.get(field, 0) + 1

    expected_fields = ['text', 'display', 'content', 'timestamp', 'metadata', 'search_method']
    print("   Expected fields present in all results:")
    for field in expected_fields:
        count = field_counts.get(field, 0)
        percentage = (count / len(all_results)) * 100 if all_results else 0
        status = "✅" if percentage == 100 else "⚠️"
        print(f"   {status} {field}: {count}/{len(all_results)} ({percentage:.0f}%)")

    print("\n🎉 Search result format test completed!")
    return True


if __name__ == "__main__":
    test_search_result_formats()
