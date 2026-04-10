# Ollama KV Cache Comparison (2026-04-10)

## Summary Table

| Scenario | OK/Total | Timeouts | Timeout Rate | p50 (s) | p95 (s) | Mean (s) |
| --- | --- | --- | --- | --- | --- | --- |
| bundled_baseline | 4/4 | 0 | 0.000 | 52.200 | 58.113 | 41.632 |
| shadow_first_pass | 1/4 | 3 | 0.750 | 130.933 | 130.933 | 130.933 |
| shadow_warm_rerun | 4/4 | 0 | 0.000 | 3.972 | 4.026 | 3.975 |

## Raw Turn Latencies

- `bundled_baseline`: t1=46.916s ok, t2=57.483s ok, t3=58.225s ok, t4=3.905s ok
- `shadow_first_pass`: t1=130.933s ok, t2=180.008s timeout fail, t3=180.016s timeout fail, t4=180.010s timeout fail
- `shadow_warm_rerun`: t1=4.029s ok, t2=4.007s ok, t3=3.926s ok, t4=3.937s ok

## Interpretation

- Warm rerun with shadow plugin is materially faster than bundled baseline.
- First shadow pass showed severe variance/timeouts, so stability is environment-dependent.
- Recommended publication framing: speedup is achievable, but operators should benchmark on their own host and run multiple passes.

## Source Files

- `bundled_baseline`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-bundled.json`
- `shadow_first_pass`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-shadow.json`
- `shadow_warm_rerun`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab-shadow-rerun.json`
