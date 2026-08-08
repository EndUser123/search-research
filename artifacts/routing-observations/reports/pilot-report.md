# Skill-Load Observation Pilot Report

Generated: 2026-07-31T23:15:07.879577+00:00

> Tier 1.5 evidence: proves only that a registered skill instruction file
> was successfully read during a wrapper-owned Grok run.
> Does not prove route selection, correctness, abstention, or causal impact.

## Summary

| Metric | Value |
|--------|-------|
| Runs observed | 51 |
| Successful Grok runs | 49 |
| Failed Grok runs | 2 |
| Skill-load observations | 20 |
| Unique skills loaded | 9 |
| No-load runs | 32 |

## Skills loaded by name

- **help**: 8 loads
- **handoff**: 3 loads
- **check**: 2 loads
- **tp**: 2 loads
- **wiki**: 1 loads
- **go**: 1 loads
- **design**: 1 loads
- **review**: 1 loads
- **aar**: 1 loads

## Skills loaded by scope

- **user**: 18 loads
- **workspace**: 2 loads

## Co-loaded skills (multiple skills in one run)

- Run b0e0fd5f: help, check

## Limitations

- Observations prove instruction-file reads, not route selection.
- Grok can use skills from system-prompt-cached descriptions without reading SKILL.md.
- Absence of an observation does not prove abstention.
- Operational use cannot be distinguished from object-of-edit without adjudication.

## Review contract

First review at: 50 runs or 30 days, whichever occurs first.
- **Retain**: if mechanical integrity is clean and >=10 useful observations exist.
- **Modify**: if coverage or adjudication usefulness is weak.
- **Retire**: if <5 useful observations in 50 runs or integrity failures occur.
