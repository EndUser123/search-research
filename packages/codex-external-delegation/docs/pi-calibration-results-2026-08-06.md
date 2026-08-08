# Pi calibration battery — 2026-08-06

Status: quarantined evidence. These results are not promoted into adaptive
routing.

## Run

- Command: `python C:/Users/brsth/.grok/skills/model-benchmark/scripts/benchmark.py --methods pi --models go-deepseek-v4-flash,nim-deepseek-ai-deepseek-v4-flash,nvidia-nemotron-3-ultra,minimax-m3,glm-5-2,zen-deepseek-v4-flash-free --timeout 60 --max-per-provider 1 --no-telemetry`
- Harness: raw Pi CLI dispatch from Grok's `model-benchmark` implementation,
  not the complete Codex `runner.mjs` path.
- Cohort: six models, six tasks each (`probe`, `reasoning`, `code-gen`,
  `structured`, `multi-step`, `tool-call`), serial per provider group, no
  retries.
- Result: 36 calls across five provider groups; 30 successes and six failures.
- Telemetry: `P:/.artifacts/model-telemetry/usage.db`, with fresh rows tagged
  `caller='model-benchmark --methods'` and `dispatch_method='cli:pi'`.

## Measured Pi results

| Model | Result | Probe (s) | Warm mean, excluding probe (s) | All-task mean (s) |
|---|---:|---:|---:|---:|
| `go-deepseek-v4-flash` | 0/6 | — | — | — |
| `nim-deepseek-ai-deepseek-v4-flash` | 6/6 | 5.3 | 7.22 | 6.9 |
| `nvidia-nemotron-3-ultra` | 6/6 | 36.0 | 6.22 | 11.2 |
| `minimax-m3` | 6/6 | 35.9 | 4.88 | 10.0 |
| `glm-5-2` | 6/6 | 60.9 | 9.72 | 18.2 |
| `zen-deepseek-v4-flash-free` | 6/6 | 39.1 | 8.24 | 13.4 |

The successful task latencies, in task order, were:

- NIM DeepSeek v4 Flash: `5.3, 4.4, 6.9, 4.0, 15.7, 5.1`.
- NVIDIA Nemotron 3 Ultra: `36.0, 6.2, 4.5, 5.6, 6.5, 8.3`.
- MiniMax M3: `35.9, 3.8, 3.4, 4.4, 9.2, 3.6`.
- GLM 5.2: `60.9, 7.2, 10.9, 7.9, 10.5, 12.1`.
- Zen DeepSeek v4 Flash Free: `39.1, 4.9, 10.6, 5.9, 5.4, 14.4`.

OpenCode Go did not fail for lack of quota. All six calls returned the
provider's 403 region error: the latest DeepSeek Flash version requires a
China-hosted endpoint and explicit opt-in. This is a provider/region failure
for this model identity. The result was independently reproduced after the
battery with the authoritative configured paths:

- Pi: `pi -p --provider opencode-go --model deepseek-v4-flash --no-session`
  returned exit 1 with the same 403.
- OpenCode: `opencode run --model opencode-go/deepseek-v4-flash` returned the
  same provider error (OpenCode incorrectly exits 0 for this displayed error).
- Current quota evidence reports OpenCode Go at 100% remaining in both
  `C:/Users/brsth/.cache/opencode/fleet-quota-cache.json` and the provider
  state files.

The configured identity is therefore valid and registered; it is the
provider's current regional eligibility for that model identity that fails.

This conclusion is specific to Go DeepSeek Flash, not to the whole Go
provider. A follow-up smoke test of the configured Go DeepSeek Pro model first
found a separate Pi configuration defect: the provider was marked as
supporting the `developer` role, but Go rejected it. Adding the model-level
`supportsDeveloperRole: false` compatibility override to
`C:/Users/brsth/.pi/agent/models.json` produced `GO_PRO_CONFIG_OK` with exit 0
in 4.856s. Go Pro therefore remains a viable candidate and should be
benchmarked separately; it must not inherit the Flash failure classification.

The corrected Go Pro configuration then passed the full six-task Pi battery
without registry or telemetry write-back: `4.2, 4.9, 4.3, 4.0, 5.6, 3.6`
seconds, 6/6, mean 4.4s. This is raw Pi latency, not complete Codex-runner
latency.

## Interpretation

The first task is probably dominated by Pi/provider cold-start overhead: five
successful models have probe times from 35.9s to 60.9s while their remaining
task means are 4.88–9.72s. That is an inference, not a proven warm-cache
property. A repeated warm battery is the falsifier.

The result is not a direct Codex-runner benchmark. The actual Codex path adds
packet preparation, worktree handling for writes, result-contract parsing, and
verification. It must be measured separately before making production latency
claims.

Historical Grok `spawn` measurements are a different transport and are not
used to rank these Pi results. MiniMax has a historical five-task Grok average
of about 16.0s versus this Pi run's 10.0s overall and 4.88s warm mean; that is
descriptive only, not a causal comparison. The other models do not have a
complete comparable Grok battery in the current registry.

## Registry-integrity finding

The benchmark's write-back path updated the live registry and propagated the
same fresh Pi task battery into every matching role lane and derived view. That
destroyed role-specific historical lane values and changed effective selector
behavior: mechanical/extraction selection moved from Zen to NVIDIA DeepSeek.
This violates the experiment gate that routing remain unchanged.

There is no current registry backup, and the available v3 backup predates the
relevant v4 lane data. Therefore the overwritten role values cannot be safely
reconstructed from authoritative evidence. The fresh measurements remain
valid as telemetry evidence, but the registry write-back is tainted for
routing purposes and must not be treated as a promotion.

## Claim ledger

| Claim | Type | Evidence | Falsifier / next check | Action |
|---|---|---|---|---|
| Five models completed six Pi tasks | verified_fact | benchmark output and SQLite rows | Missing or mismatched telemetry rows | Keep as evidence |
| Go Flash failure was regional, not quota exhaustion | verified_fact | six identical 403 RegionError rows plus direct Pi/OpenCode reproductions | A successful China opt-in run | Do not auto-retry/fallback for Flash |
| Go Pro was initially misconfigured for Pi | verified_fact | direct Pi error naming `developer` role; post-fix smoke success | A later failure with the corrected entry | Benchmark Go Pro separately |
| Probe is cold-start dominated | inference | Probe is 35.9–60.9s; warm tasks are much faster | Repeated warm battery | Do not route on this alone |
| Fresh write-back changed routing | verified_fact | Registry diff/provenance plus selector probes | Exact pre-run snapshot showing no change | Quarantine registry data |
| Pi raw-CLI ranking predicts Codex runner ranking | unsupported | No runner-path battery yet | Actual runner battery | No production decision |

## Next action

Patch the benchmark writer to write transport measurements only to an explicit
canonical transport record (or a separate calibration artifact), preserving
role-specific lane records. Then run a repeated warm battery and a small
actual Codex runner battery. Keep routing unchanged until both pass identity,
provider-error, and result-contract checks.
