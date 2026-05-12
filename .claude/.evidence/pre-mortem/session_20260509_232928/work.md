Stop_lazy_workaround_gate.py fix - proximity-based duplicate detection

Changes made:
1. Replaced brittle regex: (duplicates?|redundant|extra|double).*(is\s+)?(fine|acceptable|expected|normal|ok)
   with proximity-based keyword matcher: _check_duplicate_acceptance_proximity()
   
2. Added ROOT_CAUSE_PHRASES bypass to proximity detector

3. Extended ROOT_CAUSE_PHRASES to catch investigation verbs:
   - (?:should|will|need to|going to|planning to)\s+(?:trace|investigate|find root|debug|identify)
   - (?:let me|let us|i'll|i will)\s+(?:trace|investigate|find|debug|identify)
   - (?:tracing|investigating|finding|debugging|identifying)\s+(?:where|why|what|how)

4. Fixed label from 'ignoring_duplication' to 'ignoring duplication' (space not underscore)

Files modified:
- P:/.claude/hooks/Stop_lazy_workaround_gate.py
- P:/.claude/hooks/tests/test_lazy_workaround_gate.py

Tests: 19 passed
