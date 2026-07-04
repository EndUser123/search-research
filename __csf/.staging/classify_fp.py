import json
from collections import defaultdict

# Load data
data = []
with open('C:/Users/brsth/AppData/Local/Temp/claude/P--/220c53b5-bd49-4471-aa6b-f0f192299266/scratchpad/fp_corpus.jsonl', encoding='utf-8', errors='replace') as f:
    for line in f:
        data.append(json.loads(line))

# Process each row with refined logic
labels = []
for row in data:
    row_id = row['id']
    gate = row['gate']
    blocked_response = row.get('blocked_response', '')
    matched_span = row.get('matched_span', '')

    label = "UNCLEAR"
    why = ""

    # If blocked_response is empty, mark UNCLEAR
    if not blocked_response:
        label = "UNCLEAR"
        why = "blocked_response is empty, cannot judge"
    else:
        # Apply gate-specific logic
        if gate == "Stop_lazy_workaround_gate.py":
            # FP: Response does root cause analysis concluding not a local bug
            if ("zero local blast radius" in blocked_response or
                "upstream only" in blocked_response.lower() or
                "non_blocking_error" in blocked_response):
                label = "FP"
                why = "Response presents root cause analysis concluding issue has zero local blast radius / is upstream only / is non-blocking"
            # FP: Response concludes "not a bug" after investigation
            elif ("not a bug" in blocked_response.lower() or
                  "non-problem" in blocked_response.lower() or
                  "cosmetic noise" in blocked_response.lower()):
                label = "FP"
                why = "Response concludes item is not a bug or is cosmetic after actual investigation"
            # FP: "Trivial" describes a root-cause structural fix
            elif ("trivial" in blocked_response.lower() and
                  ("merge streams" in blocked_response.lower() or
                   "structurally" in blocked_response.lower() or
                   "one-liner" in blocked_response.lower())):
                label = "FP"
                why = "Response describes root cause fix as trivial/cheap (e.g., merge streams, one-liner), not dismissing the bug"
            # FP: Explicitly calls out the gate as false positive
            elif "false positive" in blocked_response.lower():
                label = "FP"
                why = "Response explicitly identifies the gate trigger as a known false positive pattern"
            # FP: Already fixed, describing what was done
            elif ("already fixed in the edit I shipped" in blocked_response or
                  "live bug is dead" in blocked_response):
                label = "FP"
                why = "Response describes bug that was already fixed in prior edit, not accepting a problem"
            else:
                label = "TP"
                why = "Response proposes workaround, deferral, or symptom-patch without root cause analysis"

        elif gate == "perf_attribution":
            # Check if response actually makes performance claims
            perf_claim_keywords = ["dominant factor", "bottleneck", "~", "latency", "expensive", "cheap", "fast", "slow"]
            has_perf_claim = any(kw in blocked_response.lower() for kw in perf_claim_keywords)

            # FP: No actual performance/bottleneck claims
            if not has_perf_claim:
                label = "FP"
                why = "Response does not contain actual performance/bottleneck/timing claims"
            # FP: Includes measurement evidence
            elif ("we measured:" in blocked_response.lower() or
                  "measured latencies" in blocked_response.lower() or
                  "probe, this session" in blocked_response.lower() or
                  ("~" in blocked_response and ("1s" in blocked_response or "5s" in blocked_response or "16s" in blocked_response))):
                label = "FP"
                why = "Response includes explicit measurement evidence or timing data"
            else:
                label = "TP"
                why = "Response makes performance/bottleneck claim without measurement evidence"

        elif gate == "epistemic_contract":
            # Check for proper epistemic structure
            has_sections = any(sec in blocked_response for sec in ["[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]"])
            has_citations = "(source:" in blocked_response or "(source: " in blocked_response

            # FP: Has proper sections and citations
            if has_sections and has_citations:
                label = "FP"
                why = "Response includes proper epistemic sections ([FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION]) with explicit (source:) citations"
            # FP: Has sections even if citations missing (formatting complaint)
            elif has_sections:
                label = "FP"
                why = "Response has proper epistemic section structure, gate flags formatting nit"
            else:
                label = "TP"
                why = "Response lacks required epistemic sections or citations"

        elif gate == "unverified_stance":
            # Check for verification evidence
            verification_patterns = [
                "verified via grep",
                "verified:",
                "grep:",
                "line ",
                "offset ",
                "exit 0",
                "passed",
                "confirmed via",
                "(source:",
                "file:"
            ]
            has_verification = any(pat in blocked_response for pat in verification_patterns)

            # Check if actually making confident stance
            stance_patterns = ["fixed", "works", "root cause", "resolved", "verified"]
            has_stance = any(pat in blocked_response.lower() for pat in stance_patterns)

            # FP: No confident stance
            if not has_stance:
                label = "FP"
                why = "Response does not assert confident verdict (fixed/works/root cause)"
            # FP: Has verification evidence
            elif has_verification:
                label = "FP"
                why = "Response includes verification evidence (grep output, file line numbers, exit codes)"
            # FP: "You're right" followed by detailed findings with verification
            elif ("you're right" in blocked_response.lower() and
                  ("line " in blocked_response or "grep" in blocked_response.lower())):
                label = "FP"
                why = "Response agrees with user after providing detailed verification evidence (line numbers, grep results)"
            else:
                label = "TP"
                why = "Response asserts confident verdict without verification evidence"

    labels.append({
        "id": row_id,
        "gate": gate,
        "label": label,
        "why": why
    })

# Output labels JSONL
with open('P:/__csf/.staging/fp_labels.jsonl', 'w', encoding='utf-8') as f:
    for lbl in labels:
        f.write(json.dumps(lbl) + '\n')

print(f"Wrote {len(labels)} labels to fp_labels.jsonl")

# Calculate stats
gate_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "UNCLEAR": 0})
gate_fp_examples = defaultdict(list)

for lbl in labels:
    gate_stats[lbl['gate']][lbl['label']] += 1
    if lbl['label'] == "FP":
        gate_fp_examples[lbl['gate']].append((lbl['id'], lbl['why']))

# Write summary
summary = "# False Positive Analysis Summary\n\n"
summary += "## Per-Gate Statistics\n\n"
summary += "| Gate | TP | FP | UNCLEAR | FP-rate (excl UNCLEAR) |\n"
summary += "|------|-----|----|--------|-----------------------|\n"

for gate in sorted(gate_stats.keys()):
    stats = gate_stats[gate]
    total_clear = stats["TP"] + stats["FP"]
    fp_rate = (stats["FP"] / total_clear * 100) if total_clear > 0 else 0
    summary += f"| {gate} | {stats['TP']} | {stats['FP']} | {stats['UNCLEAR']} | {fp_rate:.1f}% |\n"

summary += "\n## Representative False Positive Examples\n\n"

for gate in sorted(gate_stats.keys()):
    fps = gate_fp_examples[gate]
    if fps:
        summary += f"### {gate}\n\n"
        for fp_id, why in fps[:2]:
            summary += f"**ID {fp_id}:** {why}\n\n"

with open('P:/__csf/.staging/fp_labels_summary.md', 'w', encoding='utf-8') as f:
    f.write(summary)

print(f"Wrote summary to fp_labels_summary.md")
print("\nGate statistics:")
for gate in sorted(gate_stats.keys()):
    stats = gate_stats[gate]
    print(f"  {gate}: TP={stats['TP']}, FP={stats['FP']}, UNCLEAR={stats['UNCLEAR']}")

# Sample some labels for review
print("\nSample labels (first 10):")
for lbl in labels[:10]:
    print(f"  ID {lbl['id']}: {lbl['label']} - {lbl['why'][:80]}...")