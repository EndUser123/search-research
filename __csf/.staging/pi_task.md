INPUT: C:/Users/brsth/AppData/Local/Temp/claude/P--/220c53b5-bd49-4471-aa6b-f0f192299266/scratchpad/fp_corpus.jsonl — 79 JSONL rows, each a Stop-hook block event with fields: id, gate, timestamp, reason (the gate's stated justification for blocking), matched_span (the text the gate matched on), blocked_response (up to 2500 chars of the assistant response that got blocked; empty string if transcript unavailable).

GATE POLICIES (what each gate is supposed to catch):
- Stop_lazy_workaround_gate.py: response proposes a workaround, deferral, or symptom-patch instead of a root-cause fix.
- perf_attribution: response makes a performance/cost claim without measurement or attribution evidence.
- epistemic_contract: response makes factual claims without required epistemic labeling/verification (FACT vs INFERENCE discipline).
- unverified_stance: response asserts a confident verdict (fixed/works/root cause) without verification evidence in the response.

TASK: For each row, read blocked_response and judge whether the block was a TRUE POSITIVE (the response genuinely violates that gate's policy above) or FALSE POSITIVE (it does not — common FP shapes: the matched_span is inside quoted/reported text rather than the assistant's own claim; the response DOES contain the verification/evidence the gate demands; the match is on a read-only or hypothetical statement; formatting-only complaint about an otherwise-compliant response). If blocked_response is empty or too truncated to judge, label UNCLEAR.

OUTPUT: Write P:/__csf/.staging/fp_labels.jsonl — one JSON object per input row: {"id": <int>, "gate": "<gate>", "label": "TP"|"FP"|"UNCLEAR", "why": "<one sentence citing the specific evidence in blocked_response>"}. All 79 ids must appear exactly once.
Then write P:/__csf/.staging/fp_labels_summary.md: a per-gate table (gate | TP | FP | UNCLEAR | FP-rate excluding UNCLEAR) plus, for each gate, the 2 most representative FP examples (id + one-line pattern description of what the gate wrongly matched on).

Be conservative: when the response arguably violates the policy, label TP. FP requires a concrete reason.

Read the input file yourself with your read/bash tools. Process ALL 79 rows — do not sample or skip any. Write both output files exactly as specified above using absolute paths.
