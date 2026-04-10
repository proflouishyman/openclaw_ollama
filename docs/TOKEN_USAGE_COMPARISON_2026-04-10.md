# Ollama KV Cache Token Usage Comparison (2026-04-10, 10 Turns)

Token counts are derived from the same 10-turn latency experiment artifacts.

## Summary Table

| Scenario | OK/Total | Usage Parsed | Input Sum | Output Sum | Total Sum | Avg Total/OK Turn | Mean Tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bundled_baseline | 10/10 | 10/10 | 176060 | 44 | 176104 | 17610.40 | 322.00 |
| shadow_first_pass | 10/10 | 10/10 | 180020 | 33 | 180053 | 18005.30 | 4569.18 |
| shadow_warm_rerun | 9/10 | 8/10 | 146937 | 46 | 146983 | 18372.88 | 3419.82 |

## Distribution (Total Tokens Per Successful Turn)

| Scenario | p50 Total | p95 Total | p50 Tokens/s | p95 Tokens/s |
| --- | --- | --- | --- | --- |
| bundled_baseline | 17610.50 | 17756.45 | 311.92 | 446.97 |
| shadow_first_pass | 18004.50 | 18150.80 | 4582.34 | 4646.61 |
| shadow_warm_rerun | 18370.00 | 18518.40 | 4269.78 | 4589.60 |

## Throughput Speedup vs Bundled Baseline

| Scenario | Mean Tokens/s Speedup | p50 Tokens/s Speedup |
| --- | --- | --- |
| shadow_first_pass | 14.19x | 14.69x |
| shadow_warm_rerun | 10.62x | 13.69x |

## Per-turn Parsed Usage

### bundled_baseline
- t1: ok=True timeout=False input=17444 output=6 total=17450 cacheRead=0 cacheWrite=0 latency=36.645s
- t2: ok=True timeout=False input=17480 output=3 total=17483 cacheRead=0 cacheWrite=0 latency=42.510s
- t3: ok=True timeout=False input=17516 output=2 total=17518 cacheRead=0 cacheWrite=0 latency=51.791s
- t4: ok=True timeout=False input=17552 output=6 total=17558 cacheRead=0 cacheWrite=0 latency=84.973s
- t5: ok=True timeout=False input=17588 output=3 total=17591 cacheRead=0 cacheWrite=0 latency=62.292s
- t6: ok=True timeout=False input=17624 output=6 total=17630 cacheRead=0 cacheWrite=0 latency=68.641s
- t7: ok=True timeout=False input=17660 output=6 total=17666 cacheRead=0 cacheWrite=0 latency=54.635s
- t8: ok=True timeout=False input=17696 output=3 total=17699 cacheRead=0 cacheWrite=0 latency=58.749s
- t9: ok=True timeout=False input=17732 output=3 total=17735 cacheRead=0 cacheWrite=0 latency=55.671s
- t10: ok=True timeout=False input=17768 output=6 total=17774 cacheRead=0 cacheWrite=0 latency=58.223s

### shadow_first_pass
- t1: ok=True timeout=False input=17840 output=6 total=17846 cacheRead=0 cacheWrite=0 latency=3.986s
- t2: ok=True timeout=False input=17876 output=3 total=17879 cacheRead=0 cacheWrite=0 latency=3.908s
- t3: ok=True timeout=False input=17912 output=6 total=17918 cacheRead=0 cacheWrite=0 latency=4.065s
- t4: ok=True timeout=False input=17948 output=3 total=17951 cacheRead=0 cacheWrite=0 latency=3.871s
- t5: ok=True timeout=False input=17984 output=2 total=17986 cacheRead=0 cacheWrite=0 latency=3.919s
- t6: ok=True timeout=False input=18020 output=3 total=18023 cacheRead=0 cacheWrite=0 latency=3.901s
- t7: ok=True timeout=False input=18056 output=2 total=18058 cacheRead=0 cacheWrite=0 latency=3.880s
- t8: ok=True timeout=False input=18092 output=2 total=18094 cacheRead=0 cacheWrite=0 latency=3.921s
- t9: ok=True timeout=False input=18128 output=3 total=18131 cacheRead=0 cacheWrite=0 latency=3.977s
- t10: ok=True timeout=False input=18164 output=3 total=18167 cacheRead=0 cacheWrite=0 latency=3.987s

### shadow_warm_rerun
- t1: ok=True timeout=False input=18200 output=2 total=18202 cacheRead=0 cacheWrite=0 latency=4.352s
- t2: ok=True timeout=False input=18236 output=6 total=18242 cacheRead=0 cacheWrite=0 latency=177.710s
- t3: ok=False timeout=True usage=missing latency=180.007s
- t4: ok=True timeout=False input=18308 output=6 total=18314 cacheRead=0 cacheWrite=0 latency=18.133s
- t5: ok=True timeout=False input=18344 output=8 total=18352 cacheRead=0 cacheWrite=0 latency=4.620s
- t6: ok=True timeout=False input=18382 output=6 total=18388 cacheRead=0 cacheWrite=0 latency=4.220s
- t7: ok=True timeout=False usage=missing latency=5.560s
- t8: ok=True timeout=False input=18453 output=6 total=18459 cacheRead=0 cacheWrite=0 latency=4.013s
- t9: ok=True timeout=False input=18489 output=6 total=18495 cacheRead=0 cacheWrite=0 latency=4.046s
- t10: ok=True timeout=False input=18525 output=6 total=18531 cacheRead=0 cacheWrite=0 latency=4.060s

## Notes

- Token counts are similar across bundled and shadow warm scenarios.
- Latency improvements therefore come from faster execution path, not fewer prompt tokens.
- `cacheRead/cacheWrite` are reported as zero in these artifacts.

## Source Files

- `bundled_baseline`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-bundled.json`
- `shadow_first_pass`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-shadow.json`
- `shadow_warm_rerun`: `/Users/louishyman/openclaw/runtime_metrics/ollama-kv-ab10-shadow-rerun.json`
