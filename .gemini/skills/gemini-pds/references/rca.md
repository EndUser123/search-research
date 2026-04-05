# Root Cause Analysis (RCA)

When investigating bugs or system failures, you must prioritize understanding over fixing.

## 1. Reproduce
- Find the exact command or state that triggers the error.
- Do not speculate until reproduction is achieved.

## 2. Hypothesis Ledger (Graph of Thoughts)
- Map out the potential causes as a graph.
- **Evidence-First:** Disprove or confirm each hypothesis using tool outputs (logs, grep).

## 3. The 5 Whys
- Drill down to the fundamental system flaw. 
- Ask "Why" 5 times until the architectural root cause is exposed.

## 4. Evidence-Bound Claims
- **Prohibited:** Claims like "the path changed" or "it worked before" without paired evidence in the ledger.
- **Required:** If you claim a state transition (was X, now Y), show the tool outputs for BOTH states.
