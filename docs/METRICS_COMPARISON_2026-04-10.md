# Ollama KV Cache Comparison (2026-04-10, 10 Turns)

Test setup: `Reply with exactly OK`, same agent/model/session strategy as prior runs, 10 measured turns per scenario.

## Summary Table

| Scenario | OK/Total | Timeouts | Timeout Rate | Warmup p50 (s) | p50 (s) | p95 (s) | Mean (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bundled_baseline | 10/10 | 0 | 0.000 | 27.813 | 56.947 | 77.624 | 57.413 |
| shadow_first_pass | 10/10 | 0 | 0.000 | 118.708 | 3.920 | 4.030 | 3.941 |
| shadow_warm_rerun | 9/10 | 1 | 0.100 | n/a | 4.352 | 113.879 | 25.191 |

## Speedup vs Bundled Baseline

| Scenario | p50 Speedup | p95 Speedup |
| --- | --- | --- |
| shadow_first_pass | 14.526x | 19.262x |
| shadow_warm_rerun | 13.084x | 0.682x |

## Raw Turn Latencies

- `bundled_baseline`: t1=36.645s ok, t2=42.510s ok, t3=51.791s ok, t4=84.973s ok, t5=62.292s ok, t6=68.641s ok, t7=54.635s ok, t8=58.749s ok, t9=55.671s ok, t10=58.223s ok
- `shadow_first_pass`: t1=3.986s ok, t2=3.908s ok, t3=4.065s ok, t4=3.871s ok, t5=3.919s ok, t6=3.901s ok, t7=3.880s ok, t8=3.921s ok, t9=3.977s ok, t10=3.987s ok
- `shadow_warm_rerun`: t1=4.352s ok, t2=177.710s ok, t3=180.007s timeout fail, t4=18.133s ok, t5=4.620s ok, t6=4.220s ok, t7=5.560s ok, t8=4.013s ok, t9=4.046s ok, t10=4.060s ok

## Interpretation

- Steady-state shadow performance is substantially faster than bundled baseline (~14x by p50).
- Shadow first pass pays a large cold-start cost (warmup ~118.7s), then stabilizes near ~4s in measured turns.
- Warm rerun shows tail-risk variance (1 timeout and one very slow turn), so p95 can regress despite strong p50.
- Recommended framing: large steady-state win is achievable, but production rollout should monitor long-tail latency and timeout rate.

## Source Files

- `bundled_baseline`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-bundled.json`
- `shadow_first_pass`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-shadow.json`
- `shadow_warm_rerun`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-shadow-rerun.json`
