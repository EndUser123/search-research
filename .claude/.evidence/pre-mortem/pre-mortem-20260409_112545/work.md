Context-aware filtering for overconfidence detector hook

Location: P:/.claude/hooks/anti_sycophancy/overconfidence_detector.py
Changes implemented:
1. Added _is_explanatory_prose() function to detect explanatory prose answering user's 'why' questions
2. Modified detect_overconfidence() to accept optional user_prompt parameter
3. Added explanatory prose check in causal assertion detection (allows explanatory prose, flags technical assertions)
4. Updated StopHook_overconfidence_detector.py to pass user_prompt to detector
5. Updated test to verify fix works correctly

Test results: All 16 tests pass
- Explanatory prose with data indicators: Allowed (no note)
- Technical causal assertions without evidence: Still blocked
- No regressions in existing tests
