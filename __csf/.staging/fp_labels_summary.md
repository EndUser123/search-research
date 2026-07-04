# False Positive Analysis Summary

## Per-Gate Statistics

| Gate | TP | FP | UNCLEAR | FP-rate (excl UNCLEAR) |
|------|-----|----|--------|-----------------------|
| Stop_lazy_workaround_gate.py | 20 | 9 | 0 | 31.0% |
| epistemic_contract | 5 | 4 | 8 | 44.4% |
| perf_attribution | 10 | 8 | 0 | 44.4% |
| unverified_stance | 3 | 12 | 0 | 80.0% |

## Representative False Positive Examples

### Stop_lazy_workaround_gate.py

**ID 4:** Response explicitly identifies the gate trigger as a known false positive pattern

**ID 19:** Response explicitly identifies the gate trigger as a known false positive pattern

### epistemic_contract

**ID 57:** Response has proper epistemic section structure, gate flags formatting nit

**ID 68:** Response includes proper epistemic sections ([FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION]) with explicit (source:) citations

### perf_attribution

**ID 0:** Response does not contain actual performance/bottleneck/timing claims

**ID 32:** Response includes explicit measurement evidence or timing data

### unverified_stance

**ID 11:** Response does not assert confident verdict (fixed/works/root cause)

**ID 12:** Response includes verification evidence (grep output, file line numbers, exit codes)

