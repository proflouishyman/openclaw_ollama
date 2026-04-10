# OpenClaw Ollama KV Cache Plugin

Shadow `ollama` provider plugin for OpenClaw that injects Ollama cache controls
for static prompt reuse (for example large `SOUL.md` prefixes).

## What it does

- Overrides bundled `ollama` provider via plugin id `ollama`.
- Preserves bundled provider behavior.
- Injects request fields from model params:
  - `params.ollama.keepAlive` -> top-level `keep_alive` (if absent)
  - `params.ollama.options` -> merged into payload `options`
- Keeps OpenClaw core-managed options authoritative when already set:
  - `num_ctx`
  - `temperature`
  - `num_predict`

## Why this exists

As of 2026-04-10, bundled OpenClaw Ollama request building does not expose
request-level `keep_alive` and custom Ollama options in a controlled way.

This plugin is a maintainable bridge until/if upstream exposes first-class
params for these fields.

## Quickstart

1. Generate the bundled-entry shim (machine-specific path resolution):

```bash
python3 scripts/generate_bundled_shim.py
```

2. Apply OpenClaw config changes:

```bash
python3 scripts/apply_openclaw_config.py
```

3. Verify active plugin source:

```bash
openclaw plugins inspect ollama --json
```

Expected source:

`<this-repo>/index.js`

4. Optional: make this persistent at gateway startup (launchd on macOS):

```bash
python3 scripts/setup_launchagent.py
openclaw gateway restart
```

## Config contract

Example in `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "models": {
        "ollama/gemma4:26b": {
          "params": {
            "ollama": {
              "keepAlive": "45m",
              "options": {
                "num_batch": 16
              }
            }
          }
        }
      }
    }
  }
}
```

## Rollback

1. Remove this plugin path from `plugins.load.paths`.
2. Restart gateway.
3. If launchd startup hook was installed, restore your LaunchAgent backup.

Details: [docs/ROLLBACK.md](docs/ROLLBACK.md)

## Tests

```bash
node --test test/cache-controls.test.mjs
```

## Measured results (2026-04-10, 10-turn rerun)

Test setup:

- prompt: `Reply with exactly OK`
- model: `ollama/gemma4:26b`
- 10 measured turns per scenario
- warmup: `1` for bundled baseline and shadow first pass, `0` for shadow warm rerun

Latency summary:

| Scenario | OK/Total | Timeout Rate | Warmup p50 (s) | p50 (s) | p95 (s) |
| --- | --- | --- | --- | --- | --- |
| Bundled OpenClaw Ollama provider | 10/10 | 0% | 27.81 | 56.95 | 77.62 |
| Shadow provider (first pass) | 10/10 | 0% | 118.71 | 3.92 | 4.03 |
| Shadow provider (warm rerun) | 9/10 | 10% | n/a | 4.35 | 113.88 |

Speedup vs bundled baseline:

- Shadow first pass: `14.53x` faster on p50, `19.26x` faster on p95
- Shadow warm rerun: `13.08x` faster on p50, but p95 regressed due long-tail outliers/timeouts

Token usage summary (same 10-turn experiment):

| Scenario | Usage Parsed | Avg Total Tokens/OK Turn | Mean Tokens/s | p50 Tokens/s |
| --- | --- | --- | --- | --- |
| Bundled OpenClaw Ollama provider | 10/10 | 17610.40 | 322.00 | 311.92 |
| Shadow provider (first pass) | 10/10 | 18005.30 | 4569.18 | 4582.34 |
| Shadow provider (warm rerun) | 8/10 | 18372.88 | 3419.82 | 4269.78 |

Integrated interpretation:

- Token volume per turn stays in the same range; caching does not meaningfully reduce reported prompt token counts.
- The speedup comes from avoiding repeated prefix compute, so tokens/sec increases sharply in steady state.
- This host shows a clear steady-state win (~14x p50), plus a meaningful cold-start cost (~119s warmup) and occasional long-tail failures.
- Production rollout should treat this as a latency optimization with separate reliability guardrails (timeouts/retries/monitoring).

Details and shareable artifacts:

- `docs/METRICS_COMPARISON_2026-04-10.md`
- `docs/metrics-comparison-2026-04-10.json`
- `docs/TOKEN_USAGE_COMPARISON_2026-04-10.md`
- `docs/token-usage-comparison-2026-04-10.json`

Regenerate reports:

```bash
python3 scripts/build_metrics_comparison.py
python3 scripts/build_token_usage_comparison.py
```

## Upgrade notes

After OpenClaw updates, rerun:

```bash
python3 scripts/generate_bundled_shim.py
```

That refreshes the absolute bundled import target used by the plugin.
