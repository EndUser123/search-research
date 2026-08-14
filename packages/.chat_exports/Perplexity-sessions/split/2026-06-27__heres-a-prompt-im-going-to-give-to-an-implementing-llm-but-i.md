---
title: "Here's a prompt I'm going to give to an implementing LLM.  But I need to know if the opencode-go and opencode-zen models"
date: "2026-06-27"
mode: "COPILOT"
uuid: "f9113bbf-e0d6-4cfb-83fd-b519cc42a510"
entry_count: 1
---

## Human

Here's a prompt I'm going to give to an implementing LLM.  But I need to know if the opencode-go and opencode-zen models, and other models, can support 1M context.
"TASK: Replace config.json with the authoritative routing config
RULES (read before doing anything)
Do NOT ask clarifying questions. Every value you need is in this document.
Do NOT improvise, add, or "improve" anything not listed here.
Do NOT preserve any existing fallback content. REPLACE the file's Router and fallback sections entirely with what is specified below.
Make ALL changes, then verify. Do not stop partway to report progress.
When done, output ONLY the verification results from STEP 3. No prose summary.
STEP 1 — Overwrite these exact sections in config.json
Router (exact values)
"Router": {
  "think":                 "zai,glm-5.2",
  "default":               "minimax,MiniMax-M3[1m]",
  "background":            "minimax,MiniMax-M2.7",
  "longContext":           "minimax,MiniMax-M3[1m]",
  "longContextThreshold":  180000
}

Note: the "webSearch" Router key is REMOVED. Search is handled by the MCP, not routing.
fallback (exact arrays, exact order)
"fallback": {
  "think": [
    "opencode-go,glm-5.2",
    "minimax,MiniMax-M3[1m]",
    "opencode-zen-free,opencode/minimax-m3-free"
  ],
  "default": [
    "zai,glm-4.7",
    "opencode-go,deepseek-v4-pro",
    "opencode-zen-free,opencode/deepseek-v4-flash-free",
    "opencode-zen-free,opencode/minimax-m3-free"
  ],
  "background": [
    "opencode-go,minimax-m2.7",
    "opencode-zen-free,opencode/big-pickle",
    "zai,glm-4.7",
    "lmstudio,local-mimo"
  ],
  "longContext": [
    "zai,glm-5.2[1m]",
    "opencode-go,deepseek-v4-flash",
    "opencode-zen-free,opencode/minimax-m3-free",
    "nvidia-free,nvidia/nemotron-3-ultra-550b-a55b"
  ]
}

Note: "webSearch" fallback key is also REMOVED.
STEP 2 — Confirm Providers section contains these (add any that are missing, change nothing else)
The Providers array must define ALL of these provider names with these model ids:
minimax -> MiniMax-M3[1m], MiniMax-M2.7
zai -> glm-5.2, glm-5.2[1m], glm-4.7
opencode-go -> glm-5.2, deepseek-v4-pro, deepseek-v4-flash, minimax-m2.7
opencode-zen-free -> opencode/minimax-m3-free, opencode/deepseek-v4-flash-free, opencode/big-pickle
lmstudio -> local-mimo
nvidia-free -> nvidia/nemotron-3-ultra-550b-a55b
Do NOT add "[1m]" to any opencode-go model. Go does not honor the suffix. The ONLY models carrying "[1m]" are: minimax MiniMax-M3[1m], and zai glm-5.2[1m].
STEP 3 — Verify (run this, paste the output, do nothing else after)
python3 - <<'EOF'
import json
c = json.load(open("config.json"))
R, F = c["Router"], c["fallback"]

# A. webSearch fully removed
assert "webSearch" not in R, "FAIL: webSearch still in Router"
assert "webSearch" not in F, "FAIL: webSearch still in fallback"

# B. threshold is 180000
assert R["longContextThreshold"] == 180000, "FAIL: threshold wrong"

# C. every longContext step is a 1M-capable model (no 200k models allowed)
allowed_1m = {"MiniMax-M3[1m]","glm-5.2[1m]","deepseek-v4-flash",
              "opencode/minimax-m3-free","nvidia/nemotron-3-ultra-550b-a55b"}
for step in [R["longContext"]] + F["longContext"]:
    model = step.split(",",1)[1]
    assert model in allowed_1m, f"FAIL: non-1M model in longContext: {step}"

# D. opencode-go appears at most ONCE per fallback chain
for role, chain in F.items():
    go = [s for s in chain if s.startswith("opencode-go,")]
    assert len(go) <= 1, f"FAIL: {role} has {len(go)} opencode-go steps"

# E. no [1m] suffix on any opencode-go model
for role, chain in F.items():
    for s in chain:
        if s.startswith("opencode-go,"):
            assert "[1m]" not in s, f"FAIL: [1m] on Go model: {s}"

# F. background does NOT hit the expensive Z.ai plan before the cheap pools
assert F["background"][0] == "opencode-go,minimax-m2.7", "FAIL: background fb1 wrong"

print("ALL CHECKS PASSED")
for k in ["think","default","background","longContext"]:
    print(k, "->", R[k], "| fb:", F[k])
EOF

DONE CRITERIA
The task is complete ONLY when STEP 3 prints "ALL CHECKS PASSED". If any assertion fails, fix the config and re-run STEP 3. Do not report success until the script passes. Output only the script's final output."

## Assistant

You can safely treat all the models referenced in your long‑context chains as 1M‑capable, and your prompt’s constraints about which ones carry the “[1m]” suffix in your own config are consistent with how those providers expose them.[1][2][3][4][5]

## GLM‑5.2 via opencode‑go

- Zhipu’s GLM‑5.2 itself is a 1M‑context model; multiple sources describe it explicitly as moving from 200k to 1M context.[6][7]
- In the OpenCode/Go ecosystem, GLM‑5.2 is advertised as “1M context” with the same pricing as 5.1, and OpenClaw’s opencode‑go provider docs confirm “GLM‑5.2 uses a 1M‑token context window.”[4][1]
- Your prompt rule “Do NOT add ‘[1m]’ to any opencode‑go model. Go does not honor the suffix.” is therefore about *your routing schema*, not the underlying capability; using `opencode-go,glm-5.2` in longContext is still 1M‑capable even without the suffix.[1][4]

FACT: GLM‑5.2 is 1M‑context; opencode‑go exposes GLM‑5.2 with a 1M window.[6][4][1]
CONSENSUS: Tools built around opencode (videos, guides, third‑party tools) treat GLM‑5.2 as a frontier 1M‑context coding model.[8][9]
SPECULATION (high confidence): omitting “[1m]” in your config is purely a naming/selector convention and does not reduce context in Go; Go forwards the full model. This matches your own note about the suffix not being honored by Go.

## DeepSeek V4 Flash (and Pro) via opencode‑go

- DeepSeek V4 Flash is documented by providers like OpenRouter as supporting a 1M‑token context window.[5]
- Third‑party integration guides (e.g., Kilo Code) describe both DeepSeek V4 Pro and V4 Flash as “1M context by default” for coding.[10]
- OpenCode integrations route directly to these DeepSeek endpoints (via BYOK or aggregators) and marketing around OpenCode + DeepSeek explicitly emphasizes “handles entire codebases in one shot,” which aligns with the 1M‑context claim.[11][10]

FACT: DeepSeek V4 Flash supports a 1M‑token context window.[10][5]
SPECULATION (high confidence): `opencode-go,deepseek-v4-flash` in your longContext chain correctly hits a 1M‑context endpoint; like GLM‑5.2, Go’s lack of a “[1m]” suffix does not imply a smaller context.[5][10]

## MiniMax M3 and the “[1m]” suffix

- MiniMax’s own material describes M3 as “supports up to 1M tokens context window.”[2][3]
- Some hosts (e.g., Fireworks) initially support 500k context while working toward the full 1M, but that’s clearly called out as an implementation detail and not a limit of the base model.[12]
- Your config is explicitly marking `MiniMax-M3[1m]` as the 1M‑tier variant, and you are using that same string both for direct minimax and opencode/minimax‑m3‑free.[3][2][12]

FACT: MiniMax M3 is designed and marketed as a 1M‑context model; your use of `MiniMax-M3[1m]` is consistent with that.[2][3]
SPECULATION (medium confidence): Some third‑party hosts may temporarily cap context below 1M (e.g., 500k on Fireworks at launch), but your check is about *model class* (1M‑capable) rather than “exact deployed limit on every host,” so treating M3 as 1M‑capable for routing is reasonable.[12]

## Z.ai GLM‑5.2[1m] (non‑Go)

- Z.ai/GLM documentation and community posts are very explicit that GLM‑5.2 is the “1M‑Context Coding Model,” with context jumping from 200k to 1M relative to GLM‑5.1.[7][6]
- Cloudflare Workers AI and other platforms integrating GLM‑5.2 in coding tools also present it as a 1M‑context model.[8][4]
- Your use of `glm-5.2[1m]` as a distinct string in the zai provider block is just an internal naming convention to distinguish 1M routing paths.[4][7][6]

FACT: GLM‑5.2 from Z.ai is a 1M‑context model.[7][6][4]
CONSENSUS: Tools and content around GLM‑5.2 treat 1M context as the defining property.[9][6][8]

## Nemotron‑3 Ultra 550B

- NVIDIA’s Nemotron‑3 Ultra 550B “A55B” variant is an enormous MoE‑style LLM exported through several free/demo endpoints as a long‑context, high‑capability model.[5]
- Providers hosting it (through “nvidia/nemotron‑3‑ultra‑550b‑a55b” style IDs) advertise it for large‑context workloads; some platforms co‑market DeepSeek V4 Flash and Nemotron as 1M‑context options.[5]

SPECULATION (medium confidence): Direct, official NVIDIA docs spelling out the exact maximum context length for this free tier are thinner than for DeepSeek or GLM‑5.2, but given how it is packaged and co‑positioned with 1M‑context models on aggregators, treating it as “1M‑capable” for routing is defensible.[5]

## Does your STEP 3 check make sense?

Your verification script treats the 1M‑capable set as:

```python
allowed_1m = {
  "MiniMax-M3[1m]",
  "glm-5.2[1m]",
  "deepseek-v4-flash",
  "opencode/minimax-m3-free",
  "nvidia/nemotron-3-ultra-550b-a55b"
}
```

Mapping this to reality:

- `MiniMax-M3[1m]` → MiniMax M3, designed for 1M context.[3][2]
- `glm-5.2[1m]` → GLM‑5.2 1M‑context coding model.[6][4][7]
- `deepseek-v4-flash` → DeepSeek V4 Flash, documented as 1M context.[10][5]
- `opencode/minimax-m3-free` → a free M3‑family endpoint; underlying model is 1M‑context class even if a host caps it lower.[2][3][12]
- `nvidia/nemotron-3-ultra-550b-a55b` → large NVIDIA model used as a long‑context option; evidence suggests it is treated as a 1M‑class or comparable long‑context model.[5]

On that basis, your STEP 3 assertion “every longContext step is a 1M‑capable model (no 200k models allowed)” matches current public claims from MiniMax, Z.ai, DeepSeek, and the aggregates.[3][4][6][2][10][5]

## How I’d phrase this back into your prompt assumptions

You can safely keep these assumptions in the task prompt for the implementing LLM:

- Treat `minimax MiniMax-M3[1m]` and `zai glm-5.2[1m]` as the only models that carry the “[1m]” suffix in your *config* schema, even though GLM‑5.2 via opencode‑go is also 1M‑context; Go just doesn’t use the suffix.[1][4][7][6][2][3]
- Assume `deepseek-v4-flash` (including through opencode‑go) is 1M‑context and belongs in longContext.[10][5]
- Assume `opencode/minimax-m3-free` and `nvidia/nemotron-3-ultra-550b-a55b` are long‑context, 1M‑class models for your routing constraints.[2][3][5]

Overall confidence:  
- GLM‑5.2 (all providers) 1M‑context: high.[4][7][1][6]
- MiniMax M3 1M‑context: high (with caveat that some hosts may temporarily cap lower).[12][3][2]
- DeepSeek V4 Flash 1M‑context: high.[10][5]
- Nemotron‑3 Ultra 550B as “1M‑class” in your specific free endpoint: medium.

One thing I would still explicitly verify in your own stack is the *effective* max input tokens each provider lets you send today (vs. advertised maximum), but that’s an operational concern separate from whether your routing prompt’s logical assumptions are correct.

To tune this further for your system: do you want the verification script to treat “1M‑capable” as “model family supports 1M” (current behavior) or “this specific endpoint is actually configured at 1M right now”?
