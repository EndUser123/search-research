---
description: Produce a concise risk-policy review block before claiming a task complete
---

Before claiming this task complete, produce a risk review. Call `get_active_risk_policy` and report the following block, filling each value from the tool output:

```
Risk Tier:   <tier>
Policy:      <policy label>

Reasons:
<reasons>

Verification:
  planned:    <true|false>
  ran:        <true|false>
  passed:     <true|false>
  diff:       <true|false>
  approved:   <true|false>

Open requirements:
<missing items, or "none">
```

If "Open requirements" is non-empty, the task is not yet done — list exactly what's missing and do not claim completion.