import sys
sys.path.insert(0, r'P:\.claude\hooks')
from epistemic_validator import _classify_response_type, _has_citation_markers, _is_locally_grounded_summary, _has_local_tool_link, _has_substantive_overlap

# Test 1
text1 = "The behavior of external service X is proven by the pytest output above."
transcript1 = "38 passed in 0.60s\nTestSelfTriggerRegression: 7 passed"
print("=== Test 1: external claim ===")
print("response_type:", _classify_response_type(text1))
print("has_citation:", _has_citation_markers(text1))
print("has_link:", _has_local_tool_link(text1))
print("overlap:", _has_substantive_overlap(text1, transcript1))
print()

# Test 2
text2 = "38 passed. Based on the pytest run above, the structural fix for the self-trigger issue appears to be working."
transcript2 = "=============================\n38 passed in 0.60s\n============================="
print("=== Test 2: local tool summary ===")
print("response_type:", _classify_response_type(text2))
print("has_citation:", _has_citation_markers(text2))
print("has_link:", _has_local_tool_link(text2))
print("overlap:", _has_substantive_overlap(text2, transcript2))
print()

# Test 3
text3 = "From the pytest run above: 38 passed."
transcript3 = "38 passed in 0.60s\nTestSelfTriggerRegression: 7 passed"
print("=== Test 3: short summary ===")
print("response_type:", _classify_response_type(text3))
print("has_citation:", _has_citation_markers(text3))
print("has_link:", _has_local_tool_link(text3))
print("overlap:", _has_substantive_overlap(text3, transcript3))