# Ollama KV Cache Token Usage Comparison (2026-04-10)

## Summary Table

| Scenario | OK/Total | Usage Parsed | Input Sum | Output Sum | Total Sum | Avg Total/OK Turn | Mean Tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bundled_baseline | 4/4 | 4/4 | 67620 | 24 | 67644 | 16911.00 | 1321.99 |
| shadow_first_pass | 1/4 | 1/4 | 17259 | 6 | 17265 | 17265.00 | 131.86 |
| shadow_warm_rerun | 4/4 | 4/4 | 68978 | 26 | 69004 | 17251.00 | 4340.97 |

## Distribution (Total Tokens Per Successful Turn)

| Scenario | p50 Total | p95 Total | p50 Tokens/s | p95 Tokens/s |
| --- | --- | --- | --- | --- |
| bundled_baseline | 16911.00 | 16959.60 | 326.59 | 3746.33 |
| shadow_first_pass | 17265.00 | 17265.00 | 131.86 | 131.86 |
| shadow_warm_rerun | 17251.00 | 17300.60 | 4348.55 | 4398.58 |

## Per-turn Parsed Usage

### bundled_baseline
- t1: ok=True timeout=False input=16851 output=6 total=16857 cacheRead=0 cacheWrite=0 latency=46.916s
- t2: ok=True timeout=False input=16887 output=6 total=16893 cacheRead=0 cacheWrite=0 latency=57.483s
- t3: ok=True timeout=False input=16923 output=6 total=16929 cacheRead=0 cacheWrite=0 latency=58.225s
- t4: ok=True timeout=False input=16959 output=6 total=16965 cacheRead=0 cacheWrite=0 latency=3.905s

### shadow_first_pass
- t1: ok=True timeout=False input=17259 output=6 total=17265 cacheRead=0 cacheWrite=0 latency=130.933s
- t2: ok=False timeout=True usage=missing latency=180.008s
- t3: ok=False timeout=True usage=missing latency=180.016s
- t4: ok=False timeout=True usage=missing latency=180.010s

### shadow_warm_rerun
- t1: ok=True timeout=False input=17190 output=6 total=17196 cacheRead=0 cacheWrite=0 latency=4.029s
- t2: ok=True timeout=False input=17226 output=6 total=17232 cacheRead=0 cacheWrite=0 latency=4.007s
- t3: ok=True timeout=False input=17262 output=8 total=17270 cacheRead=0 cacheWrite=0 latency=3.926s
- t4: ok=True timeout=False input=17300 output=6 total=17306 cacheRead=0 cacheWrite=0 latency=3.937s

## Notes

- Token counts are similar across bundled and shadow warm scenarios.
- Latency improvements therefore come from faster execution path, not fewer prompt tokens.
- `cacheRead/cacheWrite` are reported as zero in these artifacts.

## Source Files

- `bundled_baseline`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-bundled.json`
- `shadow_first_pass`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-shadow.json`
- `shadow_warm_rerun`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-shadow-rerun.json`
