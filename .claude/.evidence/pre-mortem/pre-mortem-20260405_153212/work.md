Mechanism Fabrication Hook Fix

Target: P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py + Stop_hypothesis_as_fact_gate.py

What was done:
- Added MECHANISM claim type to hypothesis_as_fact_detector.py (ClaimType enum + 5 regex patterns)
- Added _strip_non_assertion_contexts() preprocessor to Stop_hypothesis_as_fact_gate.py
- The preprocessor strips markdown contexts (fenced blocks, table rows, blockquotes) before claim extraction
- Fixed 3 test functions in test_stop_hypothesis_as_fact_refactor.py that returned bool instead of None
- Added Pattern 5 to lazy_patterns.md

Why:
- LLM was fabricating internal mechanism details (timeout windows, function names) to explain observed symptoms
- New MECHANISM patterns were matching quoted incident examples in the LLM's own response (false positive)
- _strip_non_assertion_contexts prevents false positives when response documents/quotes bad behavior

Files modified:
- P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py
- P:/.claude/hooks/Stop_hypothesis_as_fact_gate.py
- P:/.claude/hooks/tests/test_stop_hypothesis_as_fact_refactor.py
- P:/.claude/memory/lazy_patterns.md

Tests: 47 passed, 0 warnings
